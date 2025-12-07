import asyncio
import threading
import time
import json
from pathlib import Path
import uvicorn

from .config import (
    API_PORT,
    BLOCK_INTERVAL,
    NODE_NAME,
    P2P_PORT,
    MAX_ROLLBACK,
    BLOCK_REWARD,
)
from .ledger import Ledger
from .mempool import Mempool
from .consensus import Consensus
from .network_ws import P2PNode
from .validator import Validator
from .block import Block
from .validator_set import load_validators
from .snapshot_manager import load_snapshot
from .state import State
from .utils import verify_signature_raw


class FRENode:
    """
    Nœud principal FRE :
    - API REST
    - boucle consensus
    - P2P WS (messages signés)
    """

    def __init__(self):
        print(f"[FRE_NODE] Initialisation du node '{NODE_NAME}'...")

        self.ledger = Ledger()
        self.mempool = Mempool()
        self.consensus = Consensus(self.ledger, self.mempool)
        self.validator = Validator()
        self.p2p = P2PNode(handler_callback=self.handle_network_message)
        self.p2p_loop = None
        self.validators = load_validators()
        self.state = State()

    # ======================================
    #             DEMARRAGE API
    # ======================================

    def start_api(self):
        print(f"[API] API REST démarrée sur http://0.0.0.0:{API_PORT}")
        uvicorn.run(
            "fre_node.api:app",
            host="0.0.0.0",
            port=API_PORT,
            reload=False
        )

    # ======================================
    #              DEMARRAGE P2P
    # ======================================

    def start_p2p(self):
        print(f"[P2P] Démarrage du serveur WS sur {P2P_PORT}...")
        loop = asyncio.new_event_loop()
        self.p2p_loop = loop

        async def runner():
            await asyncio.gather(
                self.p2p.start_server(),
                self.p2p.connect_peers(),
            )

        threading.Thread(target=lambda: loop.run_until_complete(runner()), daemon=True).start()

    # ======================================
    #             MESSAGE P2P
    # ======================================

    def handle_network_message(self, msg: dict):
        mtype = msg.get("type")
        payload = msg.get("payload", {})

        if mtype == "HELLO":
            host = payload.get("host")
            if host:
                self.p2p.add_peer(host)
        elif mtype == "TX":
            tx = payload
            if self.validator.validate_transaction(tx):
                if self.mempool.add_transaction(tx):
                    self._broadcast_async("TX", tx)
        elif mtype == "BLOCK":
            blk = payload
            self._handle_block(blk)
        elif mtype == "REQUEST_BLOCKS":
            start = payload.get("from", 0)
            end = payload.get("to", start + 10)
            blocks = self.ledger.get_chain()[start:end]
            host = payload.get("reply_to")
            if host:
                self._send_async(host, "BLOCKS", {"blocks": blocks})
        elif mtype == "BLOCKS":
            for blk in payload.get("blocks", []):
                self._handle_block(blk)
        elif mtype == "REQUEST_HEADERS":
            start = payload.get("from", 0)
            end = payload.get("to", start + 50)
            headers = [self._block_to_header(b) for b in self.ledger.get_chain()[start:end]]
            host = payload.get("reply_to")
            if host:
                self._send_async(host, "HEADERS", {"headers": headers})
        elif mtype == "HEADERS":
            headers = payload.get("headers", [])
            self._handle_headers(headers)

    def _handle_block(self, blk: dict):
        latest = self.ledger.get_latest_block()
        if latest and blk.get("index") <= latest.get("index", -1):
            return
        prev_block = self.ledger.get_block(blk["index"] - 1) if blk.get("index", 0) > 0 else None
        if blk.get("index", 0) > 0 and not prev_block:
            # demander les blocs manquants
            self._broadcast_async("REQUEST_BLOCKS", {"from": 0, "to": blk["index"], "reply_to": ""})
            return
        if not self.consensus.validate_block(blk, prev_block):
            print("[P2P] Bloc invalide reçu")
            return
        if not self._apply_remote_block(blk):
            print("[P2P] Echec application bloc")
            return
        try:
            block_obj = Block(
                index=blk["index"],
                timestamp=blk["timestamp"],
                txs=blk["txs"],
                prev_hash=blk["prev_hash"],
                validator=blk["validator"],
                state_root=blk.get("state_root", ""),
                merkle_root=blk.get("merkle_root"),
                block_signature=blk.get("block_signature"),
            )
            added = self.ledger.add_block(block_obj)
            if added:
                self._broadcast_async("BLOCK", blk)  # propager
            else:
                # rollback si rejet
                self._rollback_state(blk.get("index", 0))
        except Exception:
            return

    def _broadcast_async(self, msg_type: str, payload: dict):
        if self.p2p_loop:
            asyncio.run_coroutine_threadsafe(self.p2p.broadcast(msg_type, payload), self.p2p_loop)

    def _send_async(self, peer: str, msg_type: str, payload: dict):
        if self.p2p_loop and peer:
            asyncio.run_coroutine_threadsafe(self.p2p.send_to(peer, msg_type, payload), self.p2p_loop)

    def _get_stake(self, name: str) -> int:
        for v in self.validators:
            if v.get("name") == name:
                return max(1, int(v.get("stake", 1)))
        return 1

    def _block_to_header(self, blk: dict):
        return {
            "height": blk["index"],
            "prev_hash": blk["prev_hash"],
            "block_hash": blk["hash"],
            "merkle_root": blk.get("merkle_root", ""),
            "state_root": blk.get("state_root", ""),
            "producer": blk.get("validator", ""),
            "timestamp": blk.get("timestamp", ""),
            "signature": blk.get("block_signature", ""),
        }

    def _validate_header(self, header: dict, prev_header: dict = None) -> bool:
        required = ["height", "prev_hash", "block_hash", "merkle_root", "state_root", "producer", "signature", "timestamp"]
        if not all(k in header for k in required):
            return False
        if prev_header:
            if header["prev_hash"] != prev_header["block_hash"]:
                return False
            if header["height"] != prev_header["height"] + 1:
                return False
        payload = {
            "height": header["height"],
            "prev_hash": header["prev_hash"],
            "block_hash": header["block_hash"],
            "merkle_root": header["merkle_root"],
            "state_root": header["state_root"],
            "producer": header["producer"],
            "timestamp": header["timestamp"],
        }
        try:
            raw = json.dumps(payload, sort_keys=True).encode()
            return verify_signature_raw(header["producer"], raw, header["signature"])
        except Exception:
            return False

    def _handle_headers(self, headers: list):
        if not headers:
            return
        # validation basique de la chaîne de headers
        prev = None
        for h in headers:
            if not self._validate_header(h, prev):
                return
            prev = h

        remote_tip = headers[-1]["height"]
        local_tip = (self.ledger.get_latest_block() or {"index": -1})["index"]
        if remote_tip <= local_tip:
            return
        if remote_tip - local_tip > MAX_ROLLBACK:
            return

        # poids stake sur la fenêtre comparée
        remote_weight = sum(self._get_stake(h.get("producer", "")) for h in headers)
        # local weight pour même fenêtre
        chain = self.ledger.get_chain()
        window = chain[max(0, len(chain) - len(headers)) :]
        local_weight = sum(self._get_stake(b.get("validator", "")) for b in window)

        if remote_tip > local_tip or (remote_tip == local_tip and remote_weight > local_weight):
            # demander les blocs manquants
            self._broadcast_async("REQUEST_BLOCKS", {"from": local_tip + 1, "to": remote_tip, "reply_to": ""})

    def _apply_remote_block(self, blk: dict) -> bool:
        # sauvegarde état avant application
        balances_backup = dict(self.state.balances)
        nonces_backup = dict(self.state.nonces)
        total_fees = 0
        for tx in blk.get("txs", []):
            if not self.validator.validate_transaction(tx):
                self.state.restore(balances_backup, nonces_backup)
                return False
            if not self.state.apply_transaction(tx):
                self.state.restore(balances_backup, nonces_backup)
                return False
            total_fees += tx.get("fee", 0)

        reward_total = total_fees + (BLOCK_REWARD if BLOCK_REWARD else 0)
        if reward_total > 0:
            self.state.credit(blk.get("validator", ""), reward_total)

        computed_root = self.state.compute_state_root()
        if blk.get("state_root") and blk.get("state_root") != computed_root:
            self.state.restore(balances_backup, nonces_backup)
            return False

        return True

    def _rollback_state(self, target_height: int):
        # rollback using latest snapshot not deeper than MAX_ROLLBACK
        snap_height = None
        for h in range(target_height, max(-1, target_height - MAX_ROLLBACK - 1), -1):
            path = f"db/snapshots/snap-{h}.json"
            if Path(path).exists():
                snap_height = h
                break
        if snap_height is None:
            return
        snap = load_snapshot(snap_height)
        if snap:
            self.state.restore(snap.get("balances", {}), snap.get("nonces", {}))
            self.ledger.truncate(snap_height)

    # ======================================
    #           BOUCLE VALIDATEUR
    # ======================================

    def block_loop(self):
        print(f"[CONSENSUS] Boucle de production de blocs → intervalle {BLOCK_INTERVAL}s")

        while True:
            time.sleep(BLOCK_INTERVAL)

            if self.mempool.count() == 0:
                continue

            new_block = self.consensus.produce_block()
            if new_block:
                print(f"[BLOCK] Nouveau bloc #{new_block['index']} → hash={new_block['hash'][:12]}...")
                self._broadcast_async("BLOCK", new_block)

    # ======================================
    #            LANCEMENT GLOBAL
    # ======================================

    def start(self):
        print("[FRE_NODE] Démarrage complet du nœud...")

        threading.Thread(target=self.start_p2p, daemon=True).start()
        threading.Thread(target=self.block_loop, daemon=True).start()

        # API REST (bloquante)
        self.start_api()


if __name__ == "__main__":
    node = FRENode()
    node.start()

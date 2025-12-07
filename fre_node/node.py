import asyncio
import threading
import time
import uvicorn

from .config import API_PORT, BLOCK_INTERVAL, NODE_NAME, P2P_PORT
from .ledger import Ledger
from .mempool import Mempool
from .consensus import Consensus
from .network_ws import P2PNode
from .validator import Validator
from .block import Block


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
        except Exception:
            return

    def _broadcast_async(self, msg_type: str, payload: dict):
        if self.p2p_loop:
            asyncio.run_coroutine_threadsafe(self.p2p.broadcast(msg_type, payload), self.p2p_loop)

    def _send_async(self, peer: str, msg_type: str, payload: dict):
        if self.p2p_loop and peer:
            asyncio.run_coroutine_threadsafe(self.p2p.send_to(peer, msg_type, payload), self.p2p_loop)

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

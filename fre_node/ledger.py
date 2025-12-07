import json
import os
from .config import CHAIN_FILE
from .block import Block
from .validator_set import load_validators, select_producer, get_pubkey
from .utils import verify_signature_raw


class Ledger:
    """
    JSON ledger with basic validation and atomic writes.
    """

    def __init__(self):
        if not os.path.exists(CHAIN_FILE):
            print("[LEDGER] Creating chain.json")
            self._write_chain([])
        self.chain = self._read_chain()
        self.validators = load_validators()
        self._validate_chain_on_load()

    # =====================================
    # READ / WRITE
    # =====================================

    def _read_chain(self):
        with open(CHAIN_FILE, "r") as f:
            raw_chain = json.load(f)
        return [self._normalize_block(blk) for blk in raw_chain]

    def _write_chain(self, chain):
        """Atomic write with backup chain.json.bak"""
        tmp_path = CHAIN_FILE + ".tmp"
        bak_path = CHAIN_FILE + ".bak"

        if os.path.exists(CHAIN_FILE):
            try:
                if os.path.exists(bak_path):
                    os.remove(bak_path)
                os.replace(CHAIN_FILE, bak_path)
            except Exception:
                pass

        with open(tmp_path, "w") as f:
            json.dump(chain, f, indent=4)
        os.replace(tmp_path, CHAIN_FILE)

    def _normalize_block(self, blk: dict) -> dict:
        txs = blk.get("txs", blk.get("transactions", []))
        prev_hash = blk.get("prev_hash", blk.get("previous_hash", "0" * 64))
        validator = blk.get("validator", blk.get("node", "genesis"))
        state_root = blk.get("state_root", blk.get("stateRoot", ""))
        merkle_root = blk.get("merkle_root")

        normalized = {
            "index": blk.get("index", 0),
            "timestamp": blk.get("timestamp", 0),
            "txs": txs,
            "prev_hash": prev_hash,
            "validator": validator,
            "state_root": state_root,
            "merkle_root": merkle_root,
            "block_signature": blk.get("block_signature"),
        }

        try:
            block_obj = Block(**normalized)
            normalized["merkle_root"] = block_obj.merkle_root
            normalized["hash"] = blk.get("hash", block_obj.hash)
        except Exception:
            normalized["hash"] = blk.get("hash", "0" * 64)

        return normalized

    # =====================================
    # GETTERS
    # =====================================

    def get_latest_block(self):
        if len(self.chain) == 0:
            return None
        return self.chain[-1]

    def get_block(self, index: int):
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def get_chain(self):
        return self.chain

    def count_blocks(self):
        return len(self.chain)

    def truncate(self, height: int):
        """
        Coupe la chaîne au height indiqué (conservé), rewrite chain.json
        """
        if height < 0:
            self.chain = []
        else:
            self.chain = self.chain[: height + 1]
        self._write_chain(self.chain)

    # =====================================
    # ADD BLOCK
    # =====================================

    def add_block(self, block):
        blk_dict = block.to_dict()

        if not self._validate_new_block(blk_dict):
            print("[LEDGER] Block rejected (validation)")
            return False

        self.chain.append(blk_dict)
        self._write_chain(self.chain)
        print(f"[LEDGER] Block #{blk_dict['index']} added.")
        return True

    # =====================================
    # VALIDATION
    # =====================================

    def _validate_new_block(self, blk: dict) -> bool:
        latest = self.get_latest_block()

        if latest:
            if blk.get("index") != latest["index"] + 1:
                print("[LEDGER] Invalid index")
                return False
            if blk.get("prev_hash") != latest["hash"]:
                print("[LEDGER] Invalid prev_hash")
                return False
        else:
            if blk.get("index") != 0:
                print("[LEDGER] Invalid genesis index")
                return False

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
        except Exception:
            print("[LEDGER] Malformed block")
            return False

        if blk.get("merkle_root") and blk.get("merkle_root") != block_obj.merkle_root:
            print("[LEDGER] Invalid merkle_root")
            return False

        if blk.get("hash") != block_obj.hash:
            print("[LEDGER] Invalid hash")
            return False

        # producer check + signature (skip genesis)
        if blk.get("index", 0) > 0:
            expected_producer = select_producer(blk["index"], self.validators)
            if blk.get("validator") != expected_producer:
                print("[LEDGER] Invalid producer")
                return False

            pubkey = get_pubkey(self.validators, blk.get("validator"))
            if not pubkey or not blk.get("block_signature"):
                print("[LEDGER] Missing pubkey or signature")
                return False
            if not verify_signature_raw(pubkey, block_obj.hash.encode(), blk["block_signature"]):
                print("[LEDGER] Invalid block signature")
                return False

        return True

    def _validate_chain_on_load(self):
        for i, blk in enumerate(self.chain):
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

            if blk.get("merkle_root") and blk.get("merkle_root") != block_obj.merkle_root:
                raise ValueError(f"Block #{i} invalid merkle_root")

            if blk.get("hash") != block_obj.hash:
                raise ValueError(f"Block #{i} invalid hash")

            if i > 0 and blk.get("prev_hash") != self.chain[i - 1]["hash"]:
                raise ValueError(f"Block #{i} invalid chain link")

            if blk.get("index", 0) > 0:
                expected_producer = select_producer(blk["index"], self.validators)
                if blk.get("validator") != expected_producer:
                    raise ValueError(f"Block #{i} invalid producer")

                pubkey = get_pubkey(self.validators, blk.get("validator"))
                if not pubkey or not blk.get("block_signature"):
                    raise ValueError(f"Block #{i} missing pubkey or signature")
                if not verify_signature_raw(pubkey, block_obj.hash.encode(), blk["block_signature"]):
                    raise ValueError(f"Block #{i} invalid block signature")

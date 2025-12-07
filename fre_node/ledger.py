import json
import os
from .config import CHAIN_FILE
from .block import Block


class Ledger:
    """
    Ledger de la blockchain FRE_NODE.
    Stockage simple JSON :
    - liste de blocs
    - persistance totale
    ""

    def __init__(self):
        if not os.path.exists(CHAIN_FILE):
            print("[LEDGER] Cr?ation d'un nouveau fichier chain.json")
            self._write_chain([])
        self.chain = self._read_chain()
        self._validate_chain_on_load()

    # =====================================
    # LECTURE / ECRITURE BASIQUE DU LEDGER
    # =====================================

    def _read_chain(self):
        with open(CHAIN_FILE, "r") as f:
            raw_chain = json.load(f)
        normalized = []
        for blk in raw_chain:
            normalized.append(self._normalize_block(blk))
        return normalized

    def _write_chain(self, chain):
        """
        Ecriture atomique + backup simple (chain.json.bak) pour recovery basique.
        """
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

        normalized = {
            "index": blk.get("index", 0),
            "timestamp": blk.get("timestamp", 0),
            "txs": txs,
            "prev_hash": prev_hash,
            "validator": validator,
            "state_root": state_root,
        }

        try:
            block_obj = Block(**normalized)
            normalized["hash"] = blk.get("hash", block_obj.hash)
        except Exception:
            normalized["hash"] = blk.get("hash", "0" * 64)

        return normalized

    # =====================================
    # RECUPERATION DE BLOCS
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

    # =====================================
    # AJOUT D'UN BLOC
    # =====================================

    def add_block(self, block):
        blk_dict = block.to_dict()

        if not self._validate_new_block(blk_dict):
            print("[LEDGER] Bloc rejet? (validation)")
            return False

        self.chain.append(blk_dict)
        self._write_chain(self.chain)
        print(f"[LEDGER] Bloc #{blk_dict['index']} ajout?.")
        return True

    # =====================================
    # VALIDATION DE LA CHAINE / BLOCS
    # =====================================

    def _validate_new_block(self, blk: dict) -> bool:
        latest = self.get_latest_block()

        if latest:
            if blk.get("index") != latest["index"] + 1:
                print("[LEDGER] Index invalide.")
                return False
            if blk.get("prev_hash") != latest["hash"]:
                print("[LEDGER] prev_hash invalide.")
                return False
        else:
            if blk.get("index") != 0:
                print("[LEDGER] Genesis invalide.")
                return False

        try:
            computed = Block(
                index=blk["index"],
                timestamp=blk["timestamp"],
                txs=blk["txs"],
                prev_hash=blk["prev_hash"],
                validator=blk["validator"],
                state_root=blk.get("state_root", ""),
            ).hash
        except Exception:
            print("[LEDGER] Bloc mal form?.")
            return False

        if blk.get("hash") != computed:
            print("[LEDGER] Hash invalide.")
            return False

        return True

    def _validate_chain_on_load(self):
        for i, blk in enumerate(self.chain):
            try:
                computed = Block(
                    index=blk["index"],
                    timestamp=blk["timestamp"],
                    txs=blk["txs"],
                    prev_hash=blk["prev_hash"],
                    validator=blk["validator"],
                    state_root=blk.get("state_root", ""),
                ).hash
            except Exception:
                raise ValueError(f"Bloc #{i} mal form?")

            if blk.get("hash") != computed:
                raise ValueError(f"Bloc #{i} hash invalide")

            if i > 0 and blk.get("prev_hash") != self.chain[i - 1]["hash"]:
                raise ValueError(f"Bloc #{i} cha?nage invalide")


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
    """

    def __init__(self):
        if not os.path.exists(CHAIN_FILE):
            print("[LEDGER] Création d'un nouveau fichier chain.json")
            self._write_chain([])
        self.chain = self._read_chain()

    # =====================================
    # LECTURE / ECRITURE BASIQUE DU LEDGER
    # =====================================

    def _read_chain(self):
        with open(CHAIN_FILE, "r") as f:
            raw_chain = json.load(f)
        # Normalisation du schéma (compatibilité anciennes clés)
        normalized = []
        for blk in raw_chain:
            normalized.append(self._normalize_block(blk))
        return normalized

    def _write_chain(self, chain):
        with open(CHAIN_FILE, "w") as f:
            json.dump(chain, f, indent=4)

    def _normalize_block(self, blk: dict) -> dict:
        """
        Convertit d'anciennes clés (transactions/previous_hash)
        vers le schéma courant (txs/prev_hash) et recalcule le hash
        si nécessaire.
        """
        txs = blk.get("txs", blk.get("transactions", []))
        prev_hash = blk.get("prev_hash", blk.get("previous_hash", "0" * 64))

        # Certains anciens blocs n'avaient pas validator/state_root
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

        # Recalcul du hash si absent ou invalide
        try:
            block_obj = Block(**normalized)
            normalized["hash"] = blk.get("hash", block_obj.hash)
        except Exception:
            # fallback : on garde l'ancien hash si présent
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
        """
        block : Block object (appel à block.to_dict() dans consensus)
        """
        blk_dict = block.to_dict()
        self.chain.append(blk_dict)
        self._write_chain(self.chain)
        print(f"[LEDGER] Bloc #{blk_dict['index']} ajouté.")

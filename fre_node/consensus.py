from datetime import datetime
import json
from .block import Block
from .config import MAX_TX_PER_BLOCK, NODE_NAME, BLOCK_REWARD
from .state import get_global_state

class Consensus:
    """
    Consensus PoA simplifié :
    - Le node valideur unique produit les blocs.
    - Chaque bloc contient max MAX_TX_PER_BLOCK transactions.
    - On applique les transactions une par une au state.
    - On génère un state_root final.
    """

    def __init__(self, ledger, mempool):
        self.ledger = ledger
        self.mempool = mempool
        self.state = get_global_state()

    # ======================================
    # PRODUCTION D’UN NOUVEAU BLOC
    # ======================================

    def produce_block(self):
        """
        1. Récupère les transactions du mempool
        2. Applique les transactions au state
        3. Calcule state_root
        4. Crée un bloc
        """

        prev_block = self.ledger.get_latest_block()
        prev_hash = prev_block["hash"] if prev_block else "0" * 64

        txs = self.mempool.pop_transactions(MAX_TX_PER_BLOCK)

        applied_txs = []
        total_fees = 0

        for tx in txs:
            ok = self.state.apply_transaction(tx)
            if ok:
                applied_txs.append(tx)
                total_fees += tx.get("fee", 0)
            # les transactions invalides sont ignorées, non rejouées

        reward_total = total_fees + (BLOCK_REWARD if BLOCK_REWARD else 0)
        if reward_total > 0:
            self.state.credit(NODE_NAME, reward_total)

        state_root = self.state.compute_state_root()

        new_block = Block(
            index=(prev_block["index"] + 1 if prev_block else 0),
            timestamp=datetime.utcnow().isoformat(),
            txs=applied_txs,
            prev_hash=prev_hash,
            validator=NODE_NAME,
            state_root=state_root
        )

        # Sauvegarde dans ledger
        self.ledger.add_block(new_block)

        return new_block.to_dict()

    # ======================================
    # VALIDATION D’UN BLOC EXISTANT
    # (utile si un jour multi-noeuds)
    # ======================================

    @staticmethod
    def validate_block(block: dict, prev_block: dict) -> bool:
        """
        V?rifie :
        - index correct
        - prev_hash correct
        - hash correct (inclut merkle_root)
        """
        if prev_block and block["prev_hash"] != prev_block["hash"]:
            return False

        block_obj = Block(
            index=block["index"],
            timestamp=block["timestamp"],
            txs=block["txs"],
            prev_hash=block["prev_hash"],
            validator=block["validator"],
            state_root=block["state_root"],
            merkle_root=block.get("merkle_root")
        )

        if block_obj.hash != block["hash"]:
            return False

        return True

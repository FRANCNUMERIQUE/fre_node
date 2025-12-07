from datetime import datetime
import json
from .block import Block
import os
from .config import MAX_TX_PER_BLOCK, NODE_NAME, BLOCK_REWARD, VALIDATOR_PRIVKEY_ENV
from .utils import load_signing_key, sign_message
from .validators import load_validators, select_producer
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
        self.validators = load_validators()
        self.signing_key = None
        if VALIDATOR_PRIVKEY_ENV:
            try:
                self.signing_key = load_signing_key(VALIDATOR_PRIVKEY_ENV)
            except Exception:
                self.signing_key = None

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

        height = prev_block["index"] + 1 if prev_block else 0
        expected_producer = select_producer(height, self.validators)
        if expected_producer != NODE_NAME:
            return None  # ce node n'est pas producteur pour ce slot

        new_block = Block(
            index=(prev_block["index"] + 1 if prev_block else 0),
            timestamp=datetime.utcnow().isoformat(),
            txs=applied_txs,
            prev_hash=prev_hash,
            validator=NODE_NAME,
            state_root=state_root
        )

        # Signature du bloc par le producteur
        if self.signing_key:
            new_block.block_signature = sign_message(self.signing_key, new_block.hash.encode())

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

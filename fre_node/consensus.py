import time
from datetime import datetime
from .block import Block
from .config import MAX_TX_PER_BLOCK, NODE_NAME, BLOCK_REWARD, VALIDATOR_PRIVKEY_ENV, ANCHOR_FREQUENCY_BLOCKS, SNAPSHOT_INTERVAL, VALIDATOR
from .utils import load_signing_key, sign_message, verify_signature_raw
from .validator_set import load_validators, select_producer, get_pubkey
from .ton_anchor import anchor_client
from .snapshot_manager import save_snapshot
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
        producer_name = VALIDATOR.get("name", NODE_NAME)
        if reward_total > 0:
            self.state.credit(producer_name, reward_total)

        state_root = self.state.compute_state_root()

        height = prev_block["index"] + 1 if prev_block else 0
        expected_producer = select_producer(height, self.validators, weighted=True)
        if expected_producer != producer_name:
            return None  # ce node n'est pas producteur pour ce slot

        new_block = Block(
            index=height,
            timestamp=int(time.time()),
            txs=applied_txs,
            prev_hash=prev_hash,
            validator=producer_name,
            state_root=state_root
        )

        # Signature du bloc par le producteur
        if self.signing_key:
            new_block.block_signature = sign_message(self.signing_key, new_block.hash.encode())

        # Sauvegarde dans ledger
        added = self.ledger.add_block(new_block)

        # Ancrage TON (tous les N blocs)
        if added and (new_block.index % ANCHOR_FREQUENCY_BLOCKS == 0):
            anchor_client.anchor_block(new_block.to_dict())

        # Snapshot périodique
        if added and (new_block.index % SNAPSHOT_INTERVAL == 0):
            save_snapshot(
                {
                    "balances": self.state.balances,
                    "nonces": self.state.nonces,
                    "state_root": state_root,
                },
                new_block.index,
                producer_pub=self.signing_key.verify_key.encode().hex() if self.signing_key else "",
                privkey_b64=VALIDATOR_PRIVKEY_ENV,
            )

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

        # Producer selection + signature (skip genesis)
        if block_obj.index > 0:
            validators = load_validators()
            expected = select_producer(block_obj.index, validators)
            if block_obj.validator != expected:
                return False

            pubkey = get_pubkey(validators, block_obj.validator)
            sig = block.get("block_signature")
            if not pubkey or not sig:
                return False
            if not verify_signature_raw(pubkey, block_obj.hash.encode(), sig):
                return False

        return True

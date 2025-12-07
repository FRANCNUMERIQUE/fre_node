import base64
import hashlib
import time

from .config import (
    INITIAL_BALANCE,
    DEV_MODE,
    MIN_FEE,
    TX_VERSION,
    CHAIN_ID,
)
from .utils import ton_decode, verify_signature, canonical_tx_message
from .state import get_global_state


class Validator:
    """
    Validation stricte des transactions.
    """

    ALLOWED_TYPES = {"transfer"}
    MAX_CLOCK_SKEW_SEC = 300  # +/- 5 min

    def __init__(self):
        self.state = get_global_state()

    def _decode_pubkey(self, pubkey_b64: str):
        padded = pubkey_b64 + "=" * ((4 - len(pubkey_b64) % 4) % 4)
        return base64.urlsafe_b64decode(padded)

    def validate_transaction(self, tx: dict) -> bool:
        required = [
            "version",
            "type",
            "chain_id",
            "timestamp",
            "from",
            "to",
            "amount",
            "fee",
            "nonce",
            "signature",
            "pubkey",
        ]
        if not all(k in tx for k in required):
            print("[VALIDATOR] Champs manquants.")
            return False

        if tx["version"] != TX_VERSION:
            print("[VALIDATOR] Version invalide.")
            return False
        if tx["type"] not in self.ALLOWED_TYPES:
            print("[VALIDATOR] Type invalide.")
            return False
        if tx["chain_id"] != CHAIN_ID:
            print("[VALIDATOR] Mauvais chain_id.")
            return False

        try:
            ts = int(tx["timestamp"])
        except Exception:
            print("[VALIDATOR] Timestamp invalide.")
            return False
        now = int(time.time())
        if abs(now - ts) > self.MAX_CLOCK_SKEW_SEC:
            print("[VALIDATOR] Timestamp trop eloigne.")
            return False

        try:
            sender_pubkey_hash = ton_decode(tx["from"])
            ton_decode(tx["to"])
        except Exception:
            if DEV_MODE:
                sender_pubkey_hash = b""
            else:
                print("[VALIDATOR] Adresse TON invalide.")
                return False

        if not isinstance(tx["amount"], int) or tx["amount"] <= 0:
            print("[VALIDATOR] Montant invalide.")
            return False
        if not isinstance(tx["fee"], int) or tx["fee"] < MIN_FEE:
            print("[VALIDATOR] Fee invalide.")
            return False

        expected_nonce = self.state.get_nonce(tx["from"])
        if tx["nonce"] != expected_nonce:
            print(f"[VALIDATOR] Nonce incorrect. Attendu : {expected_nonce}")
            return False

        if DEV_MODE:
            self.state.create_wallet_if_needed(tx["from"], INITIAL_BALANCE)
            self.state.create_wallet_if_needed(tx["to"], 0)
            if self.state.get_balance(tx["from"]) < tx["amount"] + tx["fee"]:
                print("[VALIDATOR][DEV] Balance insuffisante.")
                return False
            return True

        try:
            pubkey_raw = self._decode_pubkey(tx["pubkey"])
        except Exception:
            print("[VALIDATOR] Pubkey invalide.")
            return False

        if self.state.get_balance(tx["from"]) < tx["amount"] + tx["fee"]:
            print("[VALIDATOR] Balance insuffisante.")
            return False

        message = canonical_tx_message(tx)
        if not verify_signature(sender_pubkey_hash, message, tx["signature"], pubkey_raw):
            print("[VALIDATOR] Signature invalide.")
            return False

        return True

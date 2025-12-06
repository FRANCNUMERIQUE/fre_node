import hashlib
import base64
from .utils import ton_decode, verify_signature
from .state import get_global_state

class Validator:
    """
    Valide une transaction avant ajout dans le mempool.
    Vérifie :
    - format TON strict
    - nonce correct
    - signature ed25519 (simplifiée)
    - balance suffisante
    """

    def __init__(self):
        self.state = get_global_state()

    # ============================
    # VALIDATION PRINCIPALE
    # ============================

    def validate_transaction(self, tx: dict) -> bool:
        """
        tx attendu :
        {
            "from": str,
            "to": str,
            "amount": int,
            "nonce": int,
            "signature": str
        }
        """

        required = ["from", "to", "amount", "nonce", "signature"]
        if not all(k in tx for k in required):
            return False

        # ---------------------------
        # 1) VALIDATION ADRESSES TON
        # ---------------------------

        try:
            sender_pubkey_hash = ton_decode(tx["from"])
            receiver_pubkey_hash = ton_decode(tx["to"])
        except:
            print("[VALIDATOR] Adresse TON invalide.")
            return False

        # ---------------------------
        # 2) VALIDATION MONTANT
        # ---------------------------

        if not isinstance(tx["amount"], int) or tx["amount"] <= 0:
            print("[VALIDATOR] Montant invalide.")
            return False

        # ---------------------------
        # 3) NONCE & DOUBLE SPEND
        # ---------------------------

        expected_nonce = self.state.get_nonce(tx["from"])
        if tx["nonce"] != expected_nonce:
            print(f"[VALIDATOR] Nonce incorrect. Attendu : {expected_nonce}")
            return False

        # ---------------------------
        # 4) BALANCE SUFFISANTE
        # ---------------------------

        if self.state.get_balance(tx["from"]) < tx["amount"]:
            print("[VALIDATOR] Balance insuffisante.")
            return False

        # ---------------------------
        # 5) SIGNATURE ED25519 (simplifiée)
        # ---------------------------

        message = f"{tx['from']}{tx['to']}{tx['amount']}{tx['nonce']}".encode()

        # Optionnel : pubkey (base64) pour vérification stricte Ed25519
        pubkey_raw = None
        if "pubkey" in tx and tx["pubkey"]:
            try:
                padded_pk = tx["pubkey"] + "=" * ((4 - len(tx["pubkey"]) % 4) % 4)
                pubkey_raw = base64.urlsafe_b64decode(padded_pk)
            except Exception:
                print("[VALIDATOR] Pubkey invalide.")
                return False

        if not verify_signature(sender_pubkey_hash, message, tx["signature"], pubkey_raw):
            print("[VALIDATOR] Signature invalide.")
            return False

        # ---------------------------
        # 6) TOUT EST OK
        # ---------------------------

        return True

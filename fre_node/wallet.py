import base64
import json
import time
from pathlib import Path
from typing import Dict, Any

from nacl.signing import SigningKey, VerifyKey

from .config import TX_VERSION, CHAIN_ID, MIN_FEE
from .utils import (
    generate_keys,
    ton_address_from_pubkey,
    sign_message,
    canonical_tx_message,
)


def _b64url(data: bytes) -> str:
    """Base64 URL sans padding."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded)


class Wallet:
    """
    Gestion minimale d'un wallet :
    - génération clé privée/publique
    - adresse TON-like
    - signature de transactions
    - export/import JSON
    """

    def __init__(self, signing_key: SigningKey, verify_key: VerifyKey):
        self.signing_key = signing_key
        self.verify_key = verify_key
        self.address = ton_address_from_pubkey(bytes(self.verify_key))

    @classmethod
    def create(cls) -> "Wallet":
        sk, vk = generate_keys()
        return cls(sk, vk)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Wallet":
        if "privkey" not in data or "pubkey" not in data:
            raise ValueError("Missing keys to load wallet")
        sk_raw = _b64url_decode(data["privkey"])
        vk_raw = _b64url_decode(data["pubkey"])
        sk = SigningKey(sk_raw)
        vk = VerifyKey(vk_raw)
        return cls(sk, vk)

    def to_dict(self) -> Dict[str, str]:
        return {
            "address": self.address,
            "privkey": _b64url(bytes(self.signing_key)),
            "pubkey": _b64url(bytes(self.verify_key)),
        }

    def save(self, path: str | Path):
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Wallet":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def sign_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Signe une transaction (ajoute la signature et la pubkey).
        Le message signé est le canonical_tx_message utilisé par le validator.
        """
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
        ]
        if not all(k in tx for k in required):
            raise ValueError(f"Transaction incomplete, champs requis: {required}")

        tx = dict(tx)
        tx["pubkey"] = _b64url(bytes(self.verify_key))
        message = canonical_tx_message(tx)
        tx["signature"] = sign_message(self.signing_key, message)
        return tx

    def create_tx(
        self,
        to: str,
        amount: int,
        nonce: int,
        tx_type: str = "transfer",
        fee: int = None,
        timestamp: int = None,
        chain_id: str = None,
        version: str = None,
    ) -> Dict[str, Any]:
        base_tx = {
            "version": version or TX_VERSION,
            "type": tx_type,
            "chain_id": chain_id or CHAIN_ID,
            "timestamp": timestamp or int(time.time()),
            "from": self.address,
            "to": to,
            "amount": amount,
            "fee": fee if fee is not None else MIN_FEE,
            "nonce": nonce,
            "signature": "",
            "pubkey": "",
        }
        return self.sign_transaction(base_tx)

import base64
import hashlib
import os
from nacl.signing import SigningKey, VerifyKey

# ===========================
# CANONICAL TX MESSAGE
# ===========================

def canonical_tx_message(tx: dict) -> bytes:
    """
    Canonical string for signing/verifying tx_v1.
    Order is fixed to avoid ambiguity.
    """
    parts = [
        str(tx.get("version", "")),
        str(tx.get("type", "")),
        str(tx.get("chain_id", "")),
        str(tx.get("timestamp", "")),
        str(tx.get("from", "")),
        str(tx.get("to", "")),
        str(tx.get("amount", "")),
        str(tx.get("fee", "")),
        str(tx.get("nonce", "")),
    ]
    return "|".join(parts).encode()


# ===========================
# BASE64URL UTIL
# ===========================

def b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded)


# ===========================
# TX ID
# ===========================

def compute_tx_id(tx: dict) -> str:
    """Identifiant de transaction : sha256(message canonique + signature brute)."""
    sig_bytes = b""
    if "signature" in tx and tx["signature"]:
        try:
            sig_bytes = b64url_decode(tx["signature"])
        except Exception:
            sig_bytes = b""
    msg = canonical_tx_message(tx)
    return hashlib.sha256(msg + sig_bytes).hexdigest()

# ===========================
# TON STRICT – CRC16
# ===========================

def crc16_ton(data: bytes) -> bytes:
    poly = 0x1021
    reg = 0xFFFF
    for byte in data:
        reg ^= (byte << 8)
        for _ in range(8):
            if reg & 0x8000:
                reg = ((reg << 1) ^ poly) & 0xFFFF
            else:
                reg = (reg << 1) & 0xFFFF
    return reg.to_bytes(2, "big")

# ===========================
# TON ADDRESS ENCODE
# ===========================

def ton_address_from_pubkey(pubkey: bytes, workchain: int = 0) -> str:
    """
    Génère une adresse TON-like strict :
    tag(0x51) + workchain + hash(pubkey) + CRC16 → base64url
    """
    tag = bytes([0x51])
    wc = bytes([workchain & 0xFF])
    pub_hash = hashlib.sha256(pubkey).digest()

    addr_bytes = tag + wc + pub_hash
    checksum = crc16_ton(addr_bytes)
    full = addr_bytes + checksum

    return base64.urlsafe_b64encode(full).decode().rstrip("=")

# ===========================
# BASE64URL DECODE STRICT TON
# ===========================

def ton_decode(address: str) -> bytes:
    padded = address + "=" * ((4 - len(address) % 4) % 4)
    raw = base64.urlsafe_b64decode(padded)

    data, checksum = raw[:-2], raw[-2:]
    if crc16_ton(data) != checksum:
        raise ValueError("Checksum TON invalide")

    return data[2:]  # Hash pubkey uniquement

# ===========================
# GÉNÉRATION DE CLÉS ED25519
# ===========================

def generate_keys():
    key = SigningKey.generate()
    return key, key.verify_key

# ===========================
# SIGNATURE ED25519
# ===========================

def sign_message(private: SigningKey, message: bytes) -> str:
    sig = private.sign(message).signature
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")

# ===========================
# VÉRIFICATION SIGNATURE
# ===========================

def verify_signature(pubkey_hash: bytes, message: bytes, signature: str, pubkey: bytes = None) -> bool:
    padded = signature + "=" * ((4 - len(signature) % 4) % 4)
    sig_bytes = base64.urlsafe_b64decode(padded)

    # Chemin privilégié : pubkey fourni dans la transaction
    if pubkey:
        # Vérifie la correspondance adresse <-> pubkey
        if hashlib.sha256(pubkey).digest() != pubkey_hash:
            return False
        try:
            VerifyKey(pubkey).verify(message, sig_bytes)
            return True
        except Exception:
            return False

    # Sans pubkey fournie : refuser (pas de fallback faible)
    return False


def verify_signature_raw(pubkey_b64: str, message: bytes, signature_b64: str) -> bool:
    try:
        vk = VerifyKey(b64url_decode(pubkey_b64))
        sig = b64url_decode(signature_b64)
        vk.verify(message, sig)
        return True
    except Exception:
        return False


# ===========================
# CHARGE SIGNING KEY (P2P/VALIDATOR)
# ===========================

def load_signing_key(priv_b64: str) -> SigningKey:
    padded = priv_b64 + "=" * ((4 - len(priv_b64) % 4) % 4)
    return SigningKey(base64.urlsafe_b64decode(padded))

# ===========================
# P2P SIGN/VERIFY
# ===========================

def sign_message_raw(priv_b64: str, message: bytes) -> str:
    return sign_message(load_signing_key(priv_b64), message)


def verify_signature_p2p(pubkey_b64: str, message: bytes, signature_b64: str) -> bool:
    return verify_signature_raw(pubkey_b64, message, signature_b64)


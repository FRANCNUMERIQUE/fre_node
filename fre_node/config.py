import os
import json

# ===========================
# CONFIGURATION PRINCIPALE
# ===========================

NODE_NAME = "fre_node"

DATA_DIR = os.path.join(os.path.dirname(__file__), "db")

CHAIN_FILE = os.path.join(DATA_DIR, "chain.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
ADMIN_TOKEN_FILE = os.path.join(DATA_DIR, "admin_token.json")

# ===========================
# RÉSEAU
# ===========================

API_PORT = 8500          # API FastAPI
DASHBOARD_PORT = 8080    # Dashboard web
P2P_PORT = 9000

# ===========================
# CONSENSUS & VALIDATION
# ===========================

BLOCK_INTERVAL = 5          # secondes
MAX_TX_PER_BLOCK = 100
INITIAL_BALANCE = 1000      # pour les nouveaux wallets

# Rewards / fees
BLOCK_REWARD = 0            # inflation optionnelle par bloc (0 = désactivé)

# Mempool
MEMPOOL_FILE = os.path.join(DATA_DIR, "mempool.json")
MEMPOOL_TTL_SEC = 600       # expire après 10 minutes
MEMPOOL_MAX_SIZE = 10000

# ===========================
# VALIDATEUR PRINCIPAL (PoA / identité locale)
# ===========================
# Configure via env pour éviter de commit une clé privée.

VALIDATOR_SECRET_FILE = os.path.join(DATA_DIR, "validator_secret.json")

VALIDATOR = {
    "name": os.getenv("FRE_VALIDATOR_NAME", NODE_NAME),
    "public_key": os.getenv("FRE_VALIDATOR_PUBKEY", ""),  # base64url
}
VALIDATOR_PRIVATE_KEY = os.getenv("FRE_VALIDATOR_PRIVKEY", "")  # base64url ed25519

# Charger une config locale facultative si les variables d'environnement ne sont pas définies
if os.path.exists(VALIDATOR_SECRET_FILE):
    try:
        import json

        with open(VALIDATOR_SECRET_FILE, "r") as f:
            secret = json.load(f)
        if not VALIDATOR.get("name") and secret.get("name"):
            VALIDATOR["name"] = secret.get("name")
        if not VALIDATOR.get("public_key") and secret.get("public_key"):
            VALIDATOR["public_key"] = secret.get("public_key")
        if not VALIDATOR_PRIVATE_KEY and secret.get("private_key"):
            VALIDATOR_PRIVATE_KEY = secret.get("private_key")
    except Exception:
        pass

# ===========================
# VALIDATEURS (mPoS light)
# ===========================
VALIDATORS_FILE = os.path.join(DATA_DIR, "validators.json")
# Liste statique par défaut (un seul validateur). Sera écrasée par validators.json si présent.
VALIDATORS_DEFAULT = [
    {
        "name": VALIDATOR.get("name") or os.getenv("FRE_VALIDATOR_NAME", "fre-node-01"),
        "public_key": VALIDATOR.get("public_key") or os.getenv("FRE_VALIDATOR_PUBKEY", ""),
        "stake": 1
    }
]
VALIDATOR_PRIVKEY_ENV = VALIDATOR_PRIVATE_KEY or os.getenv("FRE_VALIDATOR_PRIVKEY")

# ===========================
# TRANSACTIONS (FORMAT STRICT)
# ===========================
TX_VERSION = "tx_v1"
CHAIN_ID = "fre-local"
MIN_FEE = 1

# ===========================
# MODE DEV (validation souple)
# ===========================
# En mode DEV, les transactions de test peuvent passer sans adresse TON ni signature
# stricte (utile pour les démos et tests manuels).
DEV_MODE = os.getenv("FRE_DEV_MODE", "true").lower() in ("1", "true", "yes")


# ===========================
# ANCRAGE TON (placeholder)
# ===========================
ANCHOR_ENABLED = os.getenv("FRE_ANCHOR_ENABLED", "false").lower() in ("1", "true", "yes")
ANCHOR_FREQUENCY_BLOCKS = int(os.getenv("FRE_ANCHOR_FREQ", "20"))
ANCHOR_LOG_FILE = os.path.join(DATA_DIR, "anchor_log.json")
TON_API_ENDPOINT = os.getenv("FRE_TON_API", "https://testnet.toncenter.com/api/v2/")
TON_API_KEY = os.getenv("FRE_TON_API_KEY", "")
ANCHOR_CONTRACT = os.getenv("FRE_ANCHOR_CONTRACT", "")
VALIDATOR_TON_WALLET = os.getenv("FRE_TON_WALLET", "")
VALIDATOR_TON_PRIVATE_KEY = os.getenv("FRE_TON_PRIVKEY", "")


# ===========================
# SNAPSHOTS
# ===========================
SNAPSHOT_INTERVAL = int(os.getenv("FRE_SNAPSHOT_INTERVAL", "50"))
MAX_ROLLBACK = int(os.getenv("FRE_MAX_ROLLBACK", "200"))
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")

# ===========================
# P2P (WS)
# ===========================
PEERS_FILE = os.path.join(DATA_DIR, "peers.json")
P2P_PRIVKEY_ENV = os.getenv("FRE_P2P_PRIVKEY", os.getenv("FRE_VALIDATOR_PRIVKEY", ""))
P2P_BAN_THRESHOLD = 5

# ===========================
# ADMIN API (broadcast update)
# ===========================
def load_admin_token():
    """
    Charge le token admin à partir de l'env ou d'un fichier local.
    Si absent, retourne une chaîne vide (l'UI devra déclencher la génération).
    """
    env_tok = os.getenv("FRE_ADMIN_TOKEN", "").strip()
    if env_tok:
        return env_tok
    if os.path.exists(ADMIN_TOKEN_FILE):
        try:
            data = json.loads(open(ADMIN_TOKEN_FILE, "r").read())
            tok = data.get("token", "").strip()
            if tok:
                return tok
        except Exception:
            pass
    return ""


def save_admin_token(token: str):
    """Enregistre un token généré (setup) et le conserve en mémoire."""
    global ADMIN_TOKEN
    ADMIN_TOKEN = token
    try:
        os.makedirs(os.path.dirname(ADMIN_TOKEN_FILE), exist_ok=True)
        with open(ADMIN_TOKEN_FILE, "w") as f:
            f.write(json.dumps({"token": token}, indent=2))
    except Exception:
        pass


ADMIN_TOKEN = load_admin_token()

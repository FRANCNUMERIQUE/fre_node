import os

# ===========================
# CONFIGURATION PRINCIPALE
# ===========================

NODE_NAME = "fre_node"

DATA_DIR = os.path.join(os.path.dirname(__file__), "db")

CHAIN_FILE = os.path.join(DATA_DIR, "chain.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

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

# ===========================
# VALIDATEUR PRINCIPAL (PoA)
# ===========================

VALIDATOR_PUBLIC_KEY = None   # sera rempli au lancement
VALIDATOR_PRIVATE_KEY = None  # idem

# ===========================
# MODE DEV (validation souple)
# ===========================
# En mode DEV, les transactions de test peuvent passer sans adresse TON ni signature
# stricte (utile pour les démos et tests manuels).
DEV_MODE = os.getenv("FRE_DEV_MODE", "true").lower() in ("1", "true", "yes")

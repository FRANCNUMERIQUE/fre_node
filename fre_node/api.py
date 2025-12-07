from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fre_node.config import API_PORT
from .validator import Validator
from .mempool import Mempool
from .ledger import Ledger
from .state import State
from .config import NODE_NAME

import psutil
import platform
import time
import uvicorn


# Instance FastAPI unique
app = FastAPI(title="FRE_NODE API", version="1.0.0")

# Autoriser le dashboard à appeler l'API (peut être restreint au LAN)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def start_api():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


validator = Validator()
mempool = Mempool()
ledger = Ledger()
state = State()

# ===============================
#         ENDPOINTS STATUS
# ===============================

@app.get("/status")
def status():
    return {
        "node": NODE_NAME,
        "blocks": ledger.count_blocks(),
        "mempool": mempool.count(),
        "latest_block": ledger.get_latest_block(),
        "system": {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "os": platform.platform(),
            "uptime_sec": time.time() - psutil.boot_time()
        }
    }

# ===============================
#         BLOCKCHAIN
# ===============================

@app.get("/block/latest")
def latest_block():
    return ledger.get_latest_block() or {}

@app.get("/block/{index}")
def get_block(index: int):
    blk = ledger.get_block(index)
    return blk if blk else JSONResponse({"error": "Block not found"}, status_code=404)

@app.get("/blockchain")
def blockchain():
    return ledger.get_chain()

# ===============================
#          STATE (LEDGER)
# ===============================

@app.get("/state")
def get_state():
    return {
        "balances": state.balances,
        "nonces": state.nonces
    }

@app.get("/balance/{address}")
def balance(address: str):
    return {"address": address, "balance": state.get_balance(address)}

# ===============================
#          MEMPOOL
# ===============================

@app.get("/mempool")
def mempool_content():
    return mempool.list_transactions()

# ===============================
#         TRANSACTIONS (POST)
# ===============================

@app.post("/tx")
def submit_transaction(tx: dict):
    """
    Envoie une transaction (tx_v1) :
    {
        "version": "tx_v1",
        "type": "transfer",
        "chain_id": "fre-local",
        "timestamp": 1234567890,
        "from": "...",
        "to": "...",
        "amount": 10,
        "fee": 1,
        "nonce": 0,
        "pubkey": "base64url...",
        "signature": "base64url..."
    }
    """

    if not validator.validate_transaction(tx):
        return JSONResponse({"error": "Invalid transaction"}, status_code=400)

    ok = mempool.add_transaction(tx)
    if not ok:
        return JSONResponse({"error": "Duplicate TX"}, status_code=409)

    return {"status": "accepted", "mempool": mempool.count()}

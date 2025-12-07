from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fre_node.config import API_PORT
from .validator import Validator
from .mempool import Mempool
from .ledger import Ledger
from .state import State
from .config import NODE_NAME
from .validator_set import load_validators
from .ton_anchor import anchor_client

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
validators_list = load_validators()

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
#         API v1 (versionnée)
# ===============================

@app.post("/v1/tx/submit")
def v1_tx_submit(tx: dict):
    if not validator.validate_transaction(tx):
        return JSONResponse({"error": "Invalid transaction"}, status_code=400)
    ok = mempool.add_transaction(tx)
    if not ok:
        return JSONResponse({"error": "Duplicate TX"}, status_code=409)
    return {"status": "accepted", "mempool": mempool.count()}


@app.get("/v1/tx/{tx_hash}")
def v1_tx_get(tx_hash: str):
    # recherche dans la mempool et dans la chaîne
    for entry in mempool.transactions:
        if entry.get("id") == tx_hash:
            return {"status": "pending", "tx": entry.get("tx")}
    chain = ledger.get_chain()
    for blk in chain:
        for tx in blk.get("txs", []):
            # tx_id recalculable côté client si besoin ; ici on renvoie l'inclusion
            if tx.get("hash") == tx_hash or tx.get("tx_id") == tx_hash:
                return {"status": "included", "block": blk.get("index"), "tx": tx}
    return JSONResponse({"error": "Transaction not found"}, status_code=404)


@app.get("/v1/block/{height}")
def v1_block(height: int):
    blk = ledger.get_block(height)
    return blk if blk else JSONResponse({"error": "Block not found"}, status_code=404)


@app.get("/v1/address/{addr}")
def v1_address(addr: str):
    return {
        "address": addr,
        "balance": state.get_balance(addr),
        "nonce": state.get_nonce(addr)
    }


@app.get("/v1/validators")
def v1_validators():
    return validators_list


@app.get("/v1/anchor/status")
def v1_anchor_status():
    return anchor_client.status()


@app.get("/v1/mempool")
def v1_mempool():
    return mempool.list_transactions()

# ===============================
#          LEGACY ROUTES
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

@app.get("/state")
def get_state():
    return {
        "balances": state.balances,
        "nonces": state.nonces
    }

@app.get("/balance/{address}")
def balance(address: str):
    return {"address": address, "balance": state.get_balance(address)}

@app.get("/mempool")
def mempool_content():
    return mempool.list_transactions()

# ===============================
#          HEALTH / METRICS
# ===============================

@app.get("/health")
def health():
    latest = ledger.get_latest_block() or {}
    return {"status": "ok", "height": latest.get("index", 0), "hash": latest.get("hash", ""), "mempool": mempool.count()}

@app.get("/metrics")
def metrics():
    latest = ledger.get_latest_block() or {}
    return {
        "node": NODE_NAME,
        "height": latest.get("index", 0),
        "latest_hash": latest.get("hash", ""),
        "mempool": mempool.count(),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "uptime_sec": time.time() - psutil.boot_time(),
        },
    }

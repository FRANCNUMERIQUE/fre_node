from fastapi import FastAPI, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fre_node.config import API_PORT
from .validator import Validator
from .mempool import Mempool
from .ledger import Ledger
from .state import State
from .config import NODE_NAME, ADMIN_TOKEN, VALIDATORS_FILE, VALIDATOR_SECRET_FILE
from .validator_set import load_validators
from .ton_anchor import anchor_client
import subprocess
from pathlib import Path
import json
import os
from typing import Optional
import base64
from nacl.signing import SigningKey

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
#          ADMIN (LOCAL)
# ===============================

REPO_ROOT = Path(__file__).resolve().parent.parent
UPDATE_SCRIPT = REPO_ROOT / "update" / "update_node.sh"


@app.post("/admin/update")
def admin_update(x_admin_token: str = Header(default="")):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if not UPDATE_SCRIPT.exists():
        return JSONResponse({"error": "update script not found"}, status_code=500)
    try:
        res = subprocess.run(
            ["bash", str(UPDATE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "status": "ok" if res.returncode == 0 else "failed",
            "returncode": res.returncode,
            "stdout": res.stdout[-1000:],  # tail
            "stderr": res.stderr[-1000:],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def _systemctl(cmd: list):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


@app.get("/admin/status")
def admin_status(x_admin_token: str = Header(default="")):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    services = {}
    for svc in ["fre_node", "fre_dashboard"]:
        code, out, err = _systemctl(["systemctl", "is-active", f"{svc}.service"])
        services[svc] = {"status": out or "unknown", "error": err}

    return {
        "services": services,
        "node": {
            "height": ledger.count_blocks(),
            "mempool": mempool.count(),
            "latest": ledger.get_latest_block(),
        },
        "mempool": mempool.count(),
        "validators": validators_list,
    }


@app.post("/admin/service/restart")
def admin_service_restart(
    payload: dict = Body(...),
    x_admin_token: str = Header(default="")
):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    service = payload.get("service")
    if service not in ("fre_node", "fre_dashboard"):
        return JSONResponse({"error": "invalid service"}, status_code=400)
    code, out, err = _systemctl(["systemctl", "restart", f"{service}.service"])
    return {"status": "ok" if code == 0 else "failed", "stdout": out, "stderr": err, "returncode": code}


@app.post("/admin/validator")
def admin_set_validator(
    payload: dict = Body(...),
    x_admin_token: str = Header(default="")
):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    name = payload.get("name")
    public_key = payload.get("public_key")
    private_key = payload.get("private_key", "")
    stake = payload.get("stake", 1)
    if not name or not public_key:
        return JSONResponse({"error": "name and public_key required"}, status_code=400)
    try:
        stake_int = int(stake)
    except Exception:
        stake_int = 1

    # Sauvegarde validators.json
    validators_data = [{"name": name, "pubkey": public_key, "stake": stake_int}]
    Path(VALIDATORS_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(VALIDATORS_FILE).write_text(json.dumps(validators_data, indent=2))
    global validators_list
    validators_list = validators_data

    # Sauvegarde facultative de la clé privée (utilisée si env absent)
    secret = {
        "name": name,
        "public_key": public_key,
        "private_key": private_key or "",
    }
    Path(VALIDATOR_SECRET_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(VALIDATOR_SECRET_FILE).write_text(json.dumps(secret, indent=2))

    return {"status": "ok", "validators": validators_data}


@app.get("/admin/validator/info")
def admin_validator_info(x_admin_token: str = Header(default="")):
    """
    Retourne les informations du validateur (nom, pubkey, stake) et l'état local (balance, nonce).
    Utilise le token d'accès (ADMIN_TOKEN) pour protéger l'appel.
    """
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    validators = load_validators()
    validator: Optional[dict] = validators[0] if validators else None

    secret = {}
    if Path(VALIDATOR_SECRET_FILE).exists():
        try:
            secret = json.loads(Path(VALIDATOR_SECRET_FILE).read_text())
        except Exception:
            secret = {}

    name = validator.get("name") if validator else ""
    info = {
        "validator": validator,
        "private_key": secret.get("private_key", ""),
        "balance": state.get_balance(name) if name else 0,
        "nonce": state.get_nonce(name) if name else 0,
        "rewards": {
            "fees_total": state.get_balance(name) if name else 0  # placeholder: même champ balance pour l'instant
        }
    }
    return info


@app.get("/admin/validator/generate")
def admin_validator_generate(x_admin_token: str = Header(default="")):
    """
    Génère une paire de clés Ed25519 côté nœud.
    Retourne public_key / private_key en base64url.
    """
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    key = SigningKey.generate()
    pub_b64 = base64.urlsafe_b64encode(key.verify_key.encode()).decode().rstrip("=")
    priv_b64 = base64.urlsafe_b64encode(key.encode()).decode().rstrip("=")
    return {"public_key": pub_b64, "private_key": priv_b64}


@app.post("/admin/wifi")
def admin_wifi(
    payload: dict = Body(...),
    x_admin_token: str = Header(default="")
):
    """
    Configure le Wi‑Fi client (wpa_supplicant) puis bascule wlan0 en mode client.
    Attention : peut couper le hotspot et l'accès actuel.
    """
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    ssid = payload.get("ssid", "").strip()
    password = payload.get("password", "").strip()
    country = payload.get("country", "FR").strip() or "FR"

    if not ssid or not password:
        return JSONResponse({"error": "ssid and password required"}, status_code=400)

    wpa_conf = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country={country}
network={{
    ssid="{ssid}"
    psk="{password}"
}}
"""
    WPA_PATH = "/etc/wpa_supplicant/wpa_supplicant.conf"
    try:
        # sauvegarde
        subprocess.run(["sudo", "cp", WPA_PATH, WPA_PATH + ".bak"], check=False)
        # écriture
        subprocess.run(["sudo", "bash", "-c", f'cat > {WPA_PATH} <<\"EOF\"\n{wpa_conf}\nEOF'], check=True)
        # bascule mode client : arrêter hostapd/dnsmasq, activer wpa_supplicant
        subprocess.run(["sudo", "systemctl", "stop", "hostapd", "dnsmasq"], check=False)
        subprocess.run(["sudo", "systemctl", "disable", "hostapd", "dnsmasq"], check=False)
        subprocess.run(["sudo", "systemctl", "enable", "--now", "wpa_supplicant@wlan0.service"], check=False)
        # relancer le réseau
        subprocess.run(["sudo", "systemctl", "restart", "systemd-networkd"], check=False)
        return {"status": "ok", "message": "Wi-Fi appliqué, wlan0 bascule en client"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

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

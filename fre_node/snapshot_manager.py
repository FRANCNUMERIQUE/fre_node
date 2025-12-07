import json
import time
from pathlib import Path
from typing import Dict, Any

from .config import SNAPSHOT_DIR
from .utils import load_signing_key, sign_message
from .config import P2P_PRIVKEY_ENV


def snapshot_path(height: int) -> Path:
    return Path(SNAPSHOT_DIR) / f"snap-{height}.json"


def save_snapshot(state: Dict[str, Any], height: int, producer_pub: str, privkey_b64: str = None):
    """
    state : dict {"balances":..., "nonces":..., "state_root":...}
    """
    snap = {
        "height": height,
        "timestamp": int(time.time()),
        "state_root": state.get("state_root", ""),
        "producer": producer_pub,
        "balances": state.get("balances", {}),
        "nonces": state.get("nonces", {}),
    }

    sig = None
    key_src = privkey_b64 or P2P_PRIVKEY_ENV
    if key_src:
        try:
            sk = load_signing_key(key_src)
            snap["signature"] = sign_message(sk, json.dumps(snap, sort_keys=True).encode())
        except Exception:
            snap["signature"] = None

    path = snapshot_path(height)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(snap, indent=2))
    tmp.replace(path)


def load_snapshot(height: int) -> Dict[str, Any]:
    path = snapshot_path(height)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

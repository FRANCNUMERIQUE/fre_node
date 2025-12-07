import json
from pathlib import Path
from typing import List, Dict

from .config import VALIDATORS_FILE, NODE_NAME, VALIDATORS_DEFAULT


def _normalize_entry(raw: Dict):
    """
    Normalize validator entry keys and ensure minimal fields.
    Accepts both `pubkey` and `public_key` for backward compatibility.
    """
    if not raw:
        return None
    name = raw.get("name")
    pubkey = raw.get("pubkey") or raw.get("public_key")
    stake_raw = raw.get("stake", 1)
    try:
        stake = int(stake_raw)
    except Exception:
        stake = 1
    if not name or stake <= 0:
        return None
    return {"name": name, "pubkey": pubkey, "stake": stake}


def load_validators() -> List[Dict]:
    """
    Charge la liste des validateurs depuis validators.json.
    Format attendu : [{"name": "...", "pubkey": "base64url", "stake": 1}, ...]
    Fallback : VALIDATORS_DEFAULT (config.py).
    """
    path = Path(VALIDATORS_FILE)
    if not path.exists():
        return [v for v in (_normalize_entry(v) for v in VALIDATORS_DEFAULT) if v]
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            normalized = []
            for v in data:
                norm = _normalize_entry(v)
                if norm:
                    normalized.append(norm)
            if normalized:
                return normalized
    except Exception:
        pass
    return [{"name": NODE_NAME, "pubkey": None, "stake": 1}]


def total_stake(validators: List[Dict]) -> int:
    return sum(max(1, int(v.get("stake", 1))) for v in validators)


def select_producer(height: int, validators: List[Dict]) -> str:
    """
    Round-robin simple (ordre de la liste).
    """
    if not validators:
        return NODE_NAME
    return validators[height % len(validators)]["name"]


def get_pubkey(validators: List[Dict], name: str):
    for v in validators:
        if v.get("name") == name:
            return v.get("pubkey")
    return None

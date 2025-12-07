import json
from pathlib import Path
from typing import List, Dict

from .config import VALIDATORS_FILE, NODE_NAME, VALIDATORS_DEFAULT


def load_validators() -> List[Dict]:
    """
    Charge la liste des validateurs depuis validators.json.
    Format attendu : [{"name": "...", "pubkey": "base64url", "stake": 1}, ...]
    Fallback : VALIDATORS_DEFAULT (config.py).
    """
    path = Path(VALIDATORS_FILE)
    if not path.exists():
        return VALIDATORS_DEFAULT
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            normalized = []
            for v in data:
                name = v.get("name")
                pubkey = v.get("pubkey")
                stake = int(v.get("stake", 1))
                if name and stake > 0:
                    normalized.append({"name": name, "pubkey": pubkey, "stake": stake})
            if normalized:
                return normalized
    except Exception:
        pass
    return [{"name": NODE_NAME, "pubkey": None, "stake": 1}]


def total_stake(validators: List[Dict]) -> int:
    return sum(max(1, int(v.get("stake", 1))) for v in validators)


def select_producer(height: int, validators: List[Dict]) -> str:
    """
    Round-robin pondéré par stake, déterministe.
    """
    if not validators:
        return NODE_NAME
    weights = []
    for v in validators:
        w = max(1, int(v.get("stake", 1)))
        weights.append((v["name"], w))
    total = sum(w for _, w in weights)
    if total == 0:
        return validators[0]["name"]
    slot = height % total
    acc = 0
    for name, w in weights:
        acc += w
        if slot < acc:
            return name
    return validators[-1]["name"]


def get_pubkey(validators: List[Dict], name: str):
    for v in validators:
        if v.get("name") == name:
            return v.get("pubkey")
    return None

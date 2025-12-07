import json
import time
from pathlib import Path
from typing import Dict, Any

from .config import (
    ANCHOR_LOG_FILE,
    ANCHOR_ENABLED,
    ANCHOR_CONTRACT,
    TON_API_ENDPOINT,
    TON_API_KEY,
    VALIDATOR_TON_WALLET,
)


class TonAnchor:
    """
    Client d'ancrage TON (toncenter). Version placeholder : enregistre localement et
    simule le succès si la config est absente. À compléter avec l'appel réel toncenter.
    """

    def __init__(self):
        self.log_path = Path(ANCHOR_LOG_FILE)
        self.log = self._load_log()

    def _load_log(self) -> Dict[str, Any]:
        if not self.log_path.exists():
            return {"last_success": None, "last_attempt": None, "pending": []}
        try:
            return json.loads(self.log_path.read_text())
        except Exception:
            return {"last_success": None, "last_attempt": None, "pending": []}

    def _save_log(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(self.log_path) + ".tmp")
        tmp.write_text(json.dumps(self.log, indent=2))
        tmp.replace(self.log_path)

    def _record_attempt(self, entry):
        self.log["last_attempt"] = entry["height"]
        # supprime doublon pending même height
        self.log["pending"] = [p for p in self.log["pending"] if p.get("height") != entry["height"]]
        self.log["pending"].append(entry)
        self._save_log()

    def _record_success(self, height):
        self.log["last_success"] = height
        self.log["pending"] = [p for p in self.log["pending"] if p.get("height") != height]
        self._save_log()

    def status(self):
        return self.log

    def anchor_block(self, blk: dict):
        if not ANCHOR_ENABLED:
            return

        entry = {
            "height": blk["index"],
            "block_hash": blk.get("hash"),
            "state_root": blk.get("state_root"),
            "timestamp": int(time.time()),
        }
        self._record_attempt(entry)

        # Config minimale requise
        if not ANCHOR_CONTRACT or not TON_API_ENDPOINT or not TON_API_KEY:
            return  # laissé en pending pour retry futur

        # TODO: appeler toncenter avec la méthode publish_root/publish_checkpoint
        # Pour l'instant, on simule un succès immédiat.
        self._record_success(blk["index"])


anchor_client = TonAnchor()

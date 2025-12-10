import json
import os
import time
from pathlib import Path
from typing import List, Dict

from .config import MEMPOOL_FILE, MEMPOOL_TTL_SEC, MEMPOOL_MAX_SIZE
from .utils import compute_tx_id


class Mempool:
    """
    Persistent mempool with fee priority, dedup, TTL, and disk storage.
    Stored as a JSON list of entries: {id, tx, received_at}.
    """

    def __init__(self):
        self.transactions: List[Dict] = []  # entries: {id, tx, received_at}
        self.tx_index = set()
        self._load()
        self._purge_expired()

    # ============================
    # PERSISTENCE
    # ============================

    def _load(self):
        if not os.path.exists(MEMPOOL_FILE):
            return
        try:
            data = json.loads(Path(MEMPOOL_FILE).read_text())
            if isinstance(data, list):
                self.transactions = [e for e in data if isinstance(e, dict) and "tx" in e]
                self.tx_index = {e.get("id") for e in self.transactions if e.get("id")}
        except Exception:
            # corrupt file -> start empty
            self.transactions = []
            self.tx_index = set()

    def _save(self):
        Path(MEMPOOL_FILE).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(MEMPOOL_FILE) + '.tmp')
        Path(tmp).write_text(json.dumps(self.transactions, indent=2))
        os.replace(tmp, MEMPOOL_FILE)

    # ============================
    # MAINTENANCE
    # ============================

    def _purge_expired(self):
        cutoff = time.time() - MEMPOOL_TTL_SEC
        before = len(self.transactions)
        self.transactions = [e for e in self.transactions if e.get('received_at', 0) >= cutoff]
        self.tx_index = {e.get('id') for e in self.transactions if e.get('id')}
        if len(self.transactions) != before:
            self._save()

    def _sorted_entries(self):
        # sort by fee desc, then oldest first
        return sorted(
            self.transactions,
            key=lambda e: (
                -int(e.get('tx', {}).get('fee', 0)),
                e.get('received_at', 0)
            )
        )

    # ============================
    # ADD TRANSACTION
    # ============================

    def add_transaction(self, tx: dict) -> bool:
        self._purge_expired()

        tx_id = compute_tx_id(tx)
        if tx_id in self.tx_index:
            return False
        if len(self.transactions) >= MEMPOOL_MAX_SIZE:
            return False

        entry = {
            "id": tx_id,
            "tx": tx,
            "received_at": time.time(),
        }
        self.transactions.append(entry)
        self.tx_index.add(tx_id)
        self._save()
        return True

    # ============================
    # POP FOR BLOCKS
    # ============================

    def pop_transactions(self, max_count: int):
        self._purge_expired()
        entries = self._sorted_entries()
        selected = entries[:max_count]
        selected_ids = {e["id"] for e in selected}

        self.transactions = [e for e in self.transactions if e.get("id") not in selected_ids]
        self.tx_index = {e.get("id") for e in self.transactions if e.get("id")}
        if selected:
            self._save()

        return [e["tx"] for e in selected]

    # ============================
    # UTILITIES
    # ============================

    def count(self) -> int:
        self._purge_expired()
        return len(self.transactions)

    def stats(self) -> dict:
        """Retourne des stats basiques sur la mempool."""
        self._purge_expired()
        count = len(self.transactions)
        ts_list = [e.get("received_at", 0) for e in self.transactions]
        fees = [e.get("tx", {}).get("fee", 0) for e in self.transactions if isinstance(e.get("tx", {}).get("fee", 0), (int, float))]
        return {
            "count": count,
            "max_size": MEMPOOL_MAX_SIZE,
            "ttl_sec": MEMPOOL_TTL_SEC,
            "oldest_ts": min(ts_list) if ts_list else None,
            "newest_ts": max(ts_list) if ts_list else None,
            "fee": {
                "max": max(fees) if fees else 0,
                "min": min(fees) if fees else 0,
                "avg": (sum(fees) / len(fees)) if fees else 0,
            },
        }

    def clear(self):
        self.transactions = []
        self.tx_index = set()
        self._save()

    def list_transactions(self):
        """Return transactions sorted by priority (fee desc, oldest first)."""
        self._purge_expired()
        return [e["tx"] for e in self._sorted_entries()]

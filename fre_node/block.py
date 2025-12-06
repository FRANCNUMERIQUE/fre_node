import hashlib
import json
from datetime import datetime

class Block:
    def __init__(self, index, timestamp, txs, prev_hash, validator, state_root):
        self.index = index
        self.timestamp = timestamp
        self.txs = txs
        self.prev_hash = prev_hash
        self.validator = validator
        self.state_root = state_root
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "prev_hash": self.prev_hash,
            "validator": self.validator,
            "state_root": self.state_root
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "txs": self.txs,
            "prev_hash": self.prev_hash,
            "validator": self.validator,
            "state_root": self.state_root,
            "hash": self.hash
        }

import hashlib
import json

from .utils import compute_tx_id


class Block:
    def __init__(self, index, timestamp, txs, prev_hash, validator, state_root, merkle_root=None):
        self.index = index
        self.timestamp = timestamp
        self.txs = txs
        self.prev_hash = prev_hash
        self.validator = validator
        self.state_root = state_root
        self.merkle_root = merkle_root or self.compute_merkle_root(txs)
        self.hash = self.compute_hash()

    @staticmethod
    def compute_merkle_root(txs):
        """
        Merkle root sur les tx_id (compute_tx_id), ordre préservé.
        """
        if not txs:
            return hashlib.sha256(b"").hexdigest()

        layer = [compute_tx_id(tx) for tx in txs]

        while len(layer) > 1:
            next_layer = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i + 1] if i + 1 < len(layer) else layer[i]
                combined = (left + right).encode()
                next_layer.append(hashlib.sha256(combined).hexdigest())
            layer = next_layer
        return layer[0]

    def compute_hash(self):
        """
        Hash déterministe du bloc (métadonnées uniquement, pas la liste TX brute).
        """
        block_string = json.dumps({
            "index": self.index,
            "prev_hash": self.prev_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
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
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

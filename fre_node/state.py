import json
import os
import hashlib
from .config import STATE_FILE, INITIAL_BALANCE

class State:
    """
    Gère l'état global du réseau :
    - balances
    - nonces
    - state_root
    """

    def __init__(self):
        self.balances = {}
        self.nonces = {}

        if not os.path.exists(STATE_FILE):
            self._create_initial_state()
        else:
            self._load_state()

    # ============================
    # INITIALISATION
    # ============================

    def _create_initial_state(self):
        self.balances = {}
        self.nonces = {}
        self._save()
        print("[STATE] Nouveau state.json généré.")

    def _load_state(self):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            self.balances = data.get("balances", {})
            self.nonces = data.get("nonces", {})

    def _save(self):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "balances": self.balances,
                "nonces": self.nonces
            }, f, indent=4)

    # ============================
    # BALANCES
    # ============================

    def get_balance(self, addr: str) -> int:
        return self.balances.get(addr, 0)

    def create_wallet_if_needed(self, addr: str, initial_balance: int = 0):
        """
        Initialise un wallet si absent.
        En mode normal on ne cr?dite pas par d?faut pour ?viter la cr?ation mon?taire
        implicite. initial_balance est utile en mode dev/tests.
        """
        if addr not in self.balances:
            self.balances[addr] = max(initial_balance, 0)
            self.nonces[addr] = 0
            self._save()

    # ============================
    # NONCE MANAGEMENT
    # ============================

    def get_nonce(self, addr: str) -> int:
        return self.nonces.get(addr, 0)

    def increment_nonce(self, addr: str):
        if addr not in self.nonces:
            self.nonces[addr] = 1
        else:
            self.nonces[addr] += 1
        self._save()

    # ============================
    # STATE ROOT
    # ============================

    def compute_state_root(self) -> str:
        """Retourne un hash unique de l'état (comme un Merkle simplifié)."""

        data_string = json.dumps({
            "balances": self.balances,
            "nonces": self.nonces
        }, sort_keys=True).encode()

        return hashlib.sha256(data_string).hexdigest()

    # ============================
    # APPLY TRANSACTION (après consensus)
    # ============================

    def apply_transaction(self, tx: dict) -> bool:
        sender = tx["from"]
        receiver = tx["to"]
        amount = tx["amount"]

        if sender not in self.balances:
            return False

        if self.balances[sender] < amount:
            return False

        # Débit
        self.balances[sender] -= amount

        # Crédit
        if receiver not in self.balances:
            self.create_wallet_if_needed(receiver)

        self.balances[receiver] += amount

        # Mise à jour du nonce
        self.increment_nonce(sender)

        self._save()
        return True


# Singleton léger pour partager l'état entre validator/consensus/API
_GLOBAL_STATE = None


def get_global_state() -> State:
    global _GLOBAL_STATE
    if _GLOBAL_STATE is None:
        _GLOBAL_STATE = State()
    return _GLOBAL_STATE

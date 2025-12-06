import time

class Mempool:
    """
    Mempool : stocke les transactions valides en attente d'être intégrées
    dans le prochain bloc. Pas de persistance, mémoire volatile.
    """

    def __init__(self):
        self.transactions = []

    # ============================
    # AJOUT DE TRANSACTION
    # ============================

    def add_transaction(self, tx: dict) -> bool:
        """
        tx = {
            "from": "...",
            "to": "...",
            "amount": int,
            "nonce": int,
            "signature": "..."
        }
        """

        # Pas de doublon exact
        if tx in self.transactions:
            return False

        self.transactions.append(tx)
        return True

    # ============================
    # RÉCUPÉRATION DES TX POUR BLOCS
    # ============================

    def pop_transactions(self, max_count: int):
        """
        Retourne les max_count premières transactions.
        Les supprime ensuite de la mempool.
        """

        tx_to_process = self.transactions[:max_count]
        self.transactions = self.transactions[max_count:]
        return tx_to_process

    # ============================
    # COMPTEUR
    # ============================

    def count(self) -> int:
        return len(self.transactions)

    # ============================
    # NETTOYAGE
    # ============================

    def clear(self):
        self.transactions = []

import threading
import time
import uvicorn

from .config import API_PORT, BLOCK_INTERVAL, NODE_NAME
from .ledger import Ledger
from .mempool import Mempool
from .consensus import Consensus
from .network import NetworkNode
from fre_node.config import API_PORT


class FRENode:
    """
    Nœud principal FRE :
    - lance l'API REST
    - lance la boucle de consensus (PoA)
    - lance le module réseau
    """

    def __init__(self):
        print(f"[FRE_NODE] Initialisation du node '{NODE_NAME}'...")
        
        self.ledger = Ledger()
        self.mempool = Mempool()
        self.consensus = Consensus(self.ledger, self.mempool)
        self.network = NetworkNode(handler_callback=self.handle_network_message)

    # ======================================
    #             DEMARRAGE API
    # ======================================

    def start_api(self):
        print(f"[API] API REST démarrée sur http://0.0.0.0:{API_PORT}")

        # IMPORTANT : référence explicite du module → systemd supporte mieux
        uvicorn.run(
            "fre_node.api:app",
            host="0.0.0.0",
            port=API_PORT,
            reload=False
        )

    # ======================================
    #              DEMARRAGE P2P
    # ======================================

    def start_network(self):
        print("[NETWORK] Démarrage du serveur P2P...")
        self.network.start_server()

    # ======================================
    #             MESSAGE P2P
    # ======================================

    def handle_network_message(self, msg: dict):
        print(f"[P2P] Message reçu : {msg}")
        # futur : sync blockchain, propagation TX, propagation blocs

    # ======================================
    #           BOUCLE VALIDATEUR
    # ======================================

    def block_loop(self):
        print(f"[CONSENSUS] Boucle de production de blocs → intervalle {BLOCK_INTERVAL}s")

        while True:
            time.sleep(BLOCK_INTERVAL)

            if self.mempool.count() == 0:
                continue  # pas de TX → pas de bloc

            new_block = self.consensus.produce_block()
            print(f"[BLOCK] Nouveau bloc #{new_block['index']} → hash={new_block['hash'][:12]}...")

    # ======================================
    #            LANCEMENT GLOBAL
    # ======================================

    def start(self):
        print("[FRE_NODE] Démarrage complet du nœud...")

        threading.Thread(target=self.start_network, daemon=True).start()
        threading.Thread(target=self.block_loop, daemon=True).start()

        # API REST (bloquante)
        self.start_api()


# ======================================
#             MAIN
# ======================================

if __name__ == "__main__":
    node = FRENode()
    node.start()

import json
import socket
import threading
from .config import P2P_PORT

class NetworkNode:
    """
    Gestion réseau simplifiée pour FRE_NODE.
    
    Aujourd'hui :
    - écoute sur un port TCP
    - reçoit des messages JSON
    - envoie à un "handler" les messages reçus
    - permet un broadcast simple
    
    Futur :
    - découverte de pairs
    - synchronisation blockchain
    - propagation mempool
    """

    def __init__(self, handler_callback):
        self.handler_callback = handler_callback
        self.peers = []  # liste d'IP pour broadcast
        self.running = False

    # ============================
    # SERVEUR TCP
    # ============================

    def start_server(self):
        self.running = True

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", P2P_PORT))
        server.listen(5)

        print(f"[NETWORK] Serveur P2P en écoute sur port {P2P_PORT}")

        # Thread serveur
        threading.Thread(target=self._accept_loop, args=(server,), daemon=True).start()

    def _accept_loop(self, server):
        while self.running:
            conn, addr = server.accept()
            threading.Thread(target=self._client_handler, args=(conn, addr), daemon=True).start()

    def _client_handler(self, conn, addr):
        try:
            data = conn.recv(4096)
            if not data:
                return

            try:
                msg = json.loads(data.decode())
                self.handler_callback(msg)
            except:
                print("[NETWORK] Message JSON invalide.")
        finally:
            conn.close()

    # ============================
    # ENVOI / BROADCAST
    # ============================

    def send(self, ip: str, message: dict):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, P2P_PORT))
            sock.send(json.dumps(message).encode())
            sock.close()
        except:
            print(f"[NETWORK] Échec envoi → {ip}")

    def broadcast(self, message: dict):
        for peer in self.peers:
            self.send(peer, message)

    # ============================
    # GESTION DES PEERS
    # ============================

    def add_peer(self, ip: str):
        if ip not in self.peers:
            self.peers.append(ip)
            print(f"[NETWORK] Nouveau peer : {ip}")

    def remove_peer(self, ip: str):
        if ip in self.peers:
            self.peers.remove(ip)

FRE Node
========

Node FRE minimal pour démo/dev : API FastAPI, boucle consensus PoA simplifiée, dashboard FastAPI/Jinja2.

Prérequis
---------
- Python 3.10+
- systemd (fre_node.service, fre_dashboard.service)
- git

Installation rapide (Linux)
---------------------------
1) Cloner et lancer l’install :
   - `git clone https://github.com/FRANCNUMERIQUE/fre_node.git`
   - `cd fre_node`
   - `bash install.sh`

`install.sh` crée le venv, installe les dépendances, écrit/active/démarre `fre_node.service` et `fre_dashboard.service`.

Variables utiles (avant `bash install.sh`) :
- `NODE_DIR`    : chemin du dépôt (défaut = courant)
- `PYTHON_BIN`  : binaire python (défaut = python3)
- `VENV_DIR`    : venv (défaut = $NODE_DIR/venv)
- `SERVICE_USER`: utilisateur systemd (défaut = user courant / sudo)

Services systemd
----------------
- Statut : `sudo systemctl status fre_node.service` et `sudo systemctl status fre_dashboard.service`
- API : http://<ip>:8500
- Dashboard : http://<ip>:8080

Diagnostic
----------
- `bash diagnose.sh`
  - Vérifie services, API, blockchain, ledger, mempool, port, dashboard (codes HTTP).

Transactions de test (mode dev)
-------------------------------
- Le validator accepte des TX de test si `FRE_DEV_MODE=true` (défaut). Nonce initial = 0.
- Format `tx_v1` attendu :
  ```json
  {
    "version": "tx_v1",
    "type": "transfer",
    "chain_id": "fre-local",
    "timestamp": 1234567890,
    "from": "<address>",
    "to": "<address>",
    "amount": 10,
    "fee": 1,
    "nonce": 0,
    "pubkey": "<base64url ed25519>",
    "signature": "<base64url>"
  }
  ```
- Exemple rapide (dev, signature factice) :
  - `curl -X POST http://127.0.0.1:8500/tx -H "Content-Type: application/json" -d '{"version":"tx_v1","type":"transfer","chain_id":"fre-local","timestamp":1700000000,"from":"alice","to":"bob","amount":10,"fee":1,"nonce":0,"pubkey":"test","signature":"test"}'`
- La boucle produit un bloc toutes les 5 s si la mempool n’est pas vide ; le nonce de l’émetteur passe alors à 1.

Wallet helper
-------------
- `fre_node/wallet.py` permet de générer et signer une transaction.
- Exemple (Python) :
  - `from fre_node.wallet import Wallet`
  - `w = Wallet.create(); w.save("wallet.json")`
  - `tx = w.create_tx(to="dest_address", amount=10, nonce=0)`

Mises à jour automatiques (cron)
--------------------------------
- `update/install_update.sh` installe un cron (toutes les 10 min) qui appelle `update/update_node.sh` (git pull, pip install, restart, backup).

FRE Node
========

Ce dépôt contient un nœud FRE minimal (API FastAPI + boucle consensus PoA simplifiée) et un dashboard FastAPI/Jinja2.

Pré-requis
----------
- Python 3.10+ (recommandé)
- systemd (pour les services fre_node.service et fre_dashboard.service)
- git

Installation rapide (Linux)
---------------------------
```bash
git clone https://github.com/FRANCNUMERIQUE/fre_node.git
cd fre_node
bash install.sh
```
`install.sh` crée un venv, installe les dépendances, génère/installe les unités systemd, active et démarre les services `fre_node.service` et `fre_dashboard.service`.

Variables utiles (env) avant `bash install.sh` :
- `NODE_DIR` : chemin du dépôt (défaut = dossier courant)
- `PYTHON_BIN` : binaire python à utiliser (défaut = python3)
- `VENV_DIR` : chemin du venv (défaut = $NODE_DIR/venv)
- `SERVICE_USER` : utilisateur systemd (défaut = utilisateur courant ou sudo)

Services systemd
----------------
```
sudo systemctl status fre_node.service
sudo systemctl status fre_dashboard.service
```
API : http://<ip>:8500
Dashboard : http://<ip>:8080

Diagnostic
----------
```
bash diagnose.sh
```
Vérifie services, API, blockchain, ledger, mempool, port et dashboard (codes HTTP).

Transactions de test (mode dev)
-------------------------------
Le validator accepte des TX de test en mode dev (par défaut `FRE_DEV_MODE=true`). Nonce initial = 0. Exemple :
```bash
curl -X POST http://127.0.0.1:8500/tx \
  -H "Content-Type: application/json" \
  -d '{"from":"alice","to":"bob","amount":10,"nonce":0,"signature":"test"}'
```
Après minage (boucle toutes les 5s si mempool non vide), le nonce de l’émetteur passe à 1.

Wallet helper
-------------
`fre_node/wallet.py` permet de générer un wallet et signer une transaction :
```python
from fre_node.wallet import Wallet
w = Wallet.create()
w.save("wallet.json")
tx = w.create_tx(to="dest_address", amount=10, nonce=0)
print(tx)
```

Mises à jour automatiques (cron)
--------------------------------
`update/install_update.sh` installe un cron (toutes les 10 minutes) qui appelle `update/update_node.sh` pour pull/pip install/restart avec sauvegarde.

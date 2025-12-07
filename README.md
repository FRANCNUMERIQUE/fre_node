FRE Node
========

Minimal FRE node: FastAPI API + simple PoA loop + FastAPI/Jinja2 dashboard.

Prerequisites
-------------
- Python 3.10+
- systemd (for fre_node.service and fre_dashboard.service)
- git

Quick install (Linux)
---------------------
```bash
git clone https://github.com/FRANCNUMERIQUE/fre_node.git
cd fre_node
bash install.sh
```
`install.sh` creates a venv, installs deps, writes systemd units, enables and starts `fre_node.service` and `fre_dashboard.service`.

Environment vars (before `bash install.sh`):
- `NODE_DIR`    : repo path (default = current dir)
- `PYTHON_BIN`  : python binary (default = python3)
- `VENV_DIR`    : venv path (default = $NODE_DIR/venv)
- `SERVICE_USER`: systemd user (default = current/sudo user)

Systemd services
----------------
```bash
sudo systemctl status fre_node.service
sudo systemctl status fre_dashboard.service
```
API: http://<ip>:8500  
Dashboard: http://<ip>:8080

Diagnostic
----------
```bash
bash diagnose.sh
```
Checks services, API, blockchain, ledger, mempool, port, dashboard (HTTP codes).

Test transactions (dev mode)
----------------------------
Validator accepts test TX when `FRE_DEV_MODE=true` (default). Initial nonce = 0.
```bash
curl -X POST http://127.0.0.1:8500/tx \
  -H "Content-Type: application/json" \
  -d '{"from":"alice","to":"bob","amount":10,"nonce":0,"signature":"test"}'
```
After a block is mined (every 5s if mempool not empty), sender nonce moves to 1.

Wallet helper
-------------
`fre_node/wallet.py` to generate a wallet and sign a transaction:
```python
from fre_node.wallet import Wallet
w = Wallet.create()
w.save("wallet.json")
tx = w.create_tx(to="dest_address", amount=10, nonce=0)
print(tx)
```

Automatic updates (cron)
------------------------
`update/install_update.sh` installs a cron (every 10 minutes) calling `update/update_node.sh` to fetch/pip install/restart with backup.

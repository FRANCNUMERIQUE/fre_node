#!/bin/bash
set -euo pipefail

# Simple installer for FRE node + dashboard on a systemd host.
# You can override defaults with env vars: NODE_DIR, PYTHON_BIN, VENV_DIR.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_DIR="${NODE_DIR:-$SCRIPT_DIR}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$NODE_DIR/venv}"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(whoami)}}"

echo "[INFO] Install FRE node in $NODE_DIR"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "[ERROR] $PYTHON_BIN not found"; exit 1; }

if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating venv at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "[INFO] Installing Python dependencies"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$NODE_DIR/requirements.txt"

echo "[INFO] Writing systemd units"
sudo tee /etc/systemd/system/fre_node.service >/dev/null <<EOF
[Unit]
Description=FRE Layer 2 Node
After=network-online.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$NODE_DIR
Environment=PYTHONPATH=$NODE_DIR
ExecStart=$VENV_DIR/bin/python3 $NODE_DIR/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/fre_dashboard.service >/dev/null <<EOF
[Unit]
Description=FRE Node Dashboard
After=network-online.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$NODE_DIR
Environment=PYTHONPATH=$NODE_DIR
ExecStart=$VENV_DIR/bin/python3 $NODE_DIR/dashboard/dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "[INFO] Enabling and starting services"
sudo systemctl daemon-reload
sudo systemctl enable fre_node.service
sudo systemctl enable fre_dashboard.service
sudo systemctl restart fre_node.service
sudo systemctl restart fre_dashboard.service

echo "[DONE] FRE node and dashboard installed and started."

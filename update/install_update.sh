#!/bin/bash

echo "[UPDATE] Installation du gestionnaire de mises à jour..."

SCRIPT_DIR="$(dirname $(realpath $0))"

crontab -l > mycron 2>/dev/null

# toutes les 10 minutes : mise à jour automatique
echo "*/10 * * * * bash $SCRIPT_DIR/update_node.sh >> $SCRIPT_DIR/update.log 2>&1" >> mycron

crontab mycron
rm mycron

echo "[UPDATE] Mise à jour automatique activée."

echo "[INSTALL] Installation / Mise à jour des services FRE..."

# Installation du service du node
sudo cp $SCRIPT_DIR/../system/fre_node.service /etc/systemd/system/fre_node.service

# Installation du service du dashboard
sudo cp $SCRIPT_DIR/../system/fre_dashboard.service /etc/systemd/system/fre_dashboard.service

# Rechargement de systemd
sudo systemctl daemon-reload

# Activation des services
sudo systemctl enable fre_node.service
sudo systemctl enable fre_dashboard.service

# Redémarrage des services
sudo systemctl restart fre_node.service
sudo systemctl restart fre_dashboard.service

echo "[INSTALL] Services FRE installés et démarrés."
echo "[DONE] Installation complète terminée."

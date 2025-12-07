#!/bin/bash
LOG_FILE="/home/aliasvava/fre_node/update/update.log"
NODE_DIR="/home/aliasvava/fre_node"
BACKUP_DIR="$NODE_DIR/backup"
PYTHON="$NODE_DIR/venv/bin/python3"

echo "=================================================" | tee -a $LOG_FILE
echo "[UPDATE] Vérification des mises à jour..." | tee -a $LOG_FILE
date | tee -a $LOG_FILE
echo "=================================================" | tee -a $LOG_FILE

cd "$NODE_DIR"

echo "[CHECK] Vérification GitHub..." | tee -a $LOG_FILE

git fetch origin >> $LOG_FILE 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" == "$REMOTE" ]; then
    echo "[INFO] Aucune mise à jour disponible." | tee -a $LOG_FILE
    exit 0
fi

echo "[UPDATE] Nouvelle version détectée !" | tee -a $LOG_FILE

echo "[BACKUP] Sauvegarde de la version actuelle..." | tee -a $LOG_FILE
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp -r "$NODE_DIR"/* "$BACKUP_DIR"/ 2>>$LOG_FILE

echo "[GIT] Application du git pull..." | tee -a $LOG_FILE
if ! git pull --rebase >> $LOG_FILE 2>&1; then
    echo "[ERROR] Le git pull a échoué ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

echo "[PIP] Mise à jour des dépendances..." | tee -a $LOG_FILE
source "$NODE_DIR/venv/bin/activate"
if ! pip install -r requirements.txt >> $LOG_FILE 2>&1; then
    echo "[ERROR] Échec pip install ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

echo "[TEST] Test de lancement..." | tee -a $LOG_FILE
timeout 5 $PYTHON "$NODE_DIR/main.py" --check-only >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    echo "[ERROR] Le node ne démarre pas ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

echo "[SUCCESS] Mise à jour appliquée correctement !" | tee -a $LOG_FILE

echo "[SYSTEMD] Redémarrage des services..." | tee -a $LOG_FILE
sudo systemctl restart fre_node.service
sudo systemctl restart fre_dashboard.service
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart avahi-daemon
[ -f /etc/systemd/system/fre_portal.service ] && sudo systemctl restart fre_portal.service

echo "[DONE] Mise à jour terminée." | tee -a $LOG_FILE
exit 0

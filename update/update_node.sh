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

# Récupération de l’état du dépôt
git fetch origin >> $LOG_FILE 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" == "$REMOTE" ]; then
    echo "[INFO] Aucune mise à jour disponible." | tee -a $LOG_FILE
    exit 0
fi

echo "[UPDATE] Nouvelle version détectée !" | tee -a $LOG_FILE

# Sauvegarde
echo "[BACKUP] Sauvegarde de la version actuelle..." | tee -a $LOG_FILE
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

cp -r "$NODE_DIR"/* "$BACKUP_DIR"/ 2>>$LOG_FILE

# Mise à jour
echo "[GIT] Application du git pull..." | tee -a $LOG_FILE
if ! git pull --rebase >> $LOG_FILE 2>&1; then
    echo "[ERROR] Le git pull a échoué ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

# Dépendances
echo "[PIP] Mise à jour des dépendances..." | tee -a $LOG_FILE
source "$NODE_DIR/venv/bin/activate"

if ! pip install -r requirements.txt >> $LOG_FILE 2>&1; then
    echo "[ERROR] Échec pip install ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

# Test du node avant redémarrage réel
echo "[TEST] Test de lancement..." | tee -a $LOG_FILE
timeout 5 $PYTHON "$NODE_DIR/main.py" --check-only >> $LOG_FILE 2>&1

if [ $? -ne 0 ]; then
    echo "[ERROR] Le node ne démarre pas ! Restauration..." | tee -a $LOG_FILE
    cp -r "$BACKUP_DIR"/* "$NODE_DIR"/
    exit 1
fi

echo "[SUCCESS] Mise à jour appliquée correctement !" | tee -a $LOG_FILE

echo "[SYSTEMD] Redémarrage du service..." | tee -a $LOG_FILE
sudo systemctl restart fre-node

echo "[DONE] Mise à jour terminée." | tee -a $LOG_FILE
exit 0

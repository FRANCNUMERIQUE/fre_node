#!/bin/bash

GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
RESET="\e[0m"

API_PORT=8500
DASHBOARD_PORT=8080

IP=$(hostname -I | awk '{print $1}')

echo -e "${YELLOW}=============================================="
echo -e "        FRE NODE – DIAGNOSTIC COMPLET"
echo -e "==============================================${RESET}"
echo ""
echo -e "Adresse IP détectée : ${GREEN}$IP${RESET}"
echo ""

# ----------------------------------------------------
# 1) Vérifier services systemd
# ----------------------------------------------------

check_service() {
    SERVICE=$1
    echo -e "${YELLOW}[SERVICE] Vérification : $SERVICE${RESET}"

    if systemctl is-active --quiet "$SERVICE" 2>/dev/null || sudo systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
        echo -e " → ${GREEN}OK : Service actif${RESET}"
    else
        STATE=$(systemctl is-active "$SERVICE" 2>/dev/null || sudo systemctl is-active "$SERVICE" 2>/dev/null || echo "indéterminé")
        echo -e " → ${RED}ERREUR : Service inactif (${STATE})${RESET}"
    fi
    echo ""
}

check_service "fre_node.service"
check_service "fre_dashboard.service"

# ----------------------------------------------------
# 2) Tester l’API backend FRE
# ----------------------------------------------------

echo -e "${YELLOW}[API] Test de connexion à l’API FRE...${RESET}"

STATUS=$(curl -s http://$IP:$API_PORT/status)

if [[ -z "$STATUS" ]]; then
    echo -e " → ${RED}ERREUR : Impossible d'accéder à /status${RESET}"
else
    echo -e " → ${GREEN}OK : API accessible${RESET}"
    echo "$STATUS"
fi
echo ""

# ----------------------------------------------------
# 3) Tester le dernier bloc
# ----------------------------------------------------

echo -e "${YELLOW}[BLOCKCHAIN] Lecture du dernier bloc...${RESET}"

BLOCK=$(curl -s http://$IP:$API_PORT/block/latest)

if [[ -z "$BLOCK" ]]; then
    echo -e " → ${RED}ERREUR : Aucun bloc retourné${RESET}"
else
    echo -e " → ${GREEN}OK${RESET}\n$BLOCK"
fi
echo ""

# ----------------------------------------------------
# 4) Tester le ledger
# ----------------------------------------------------

echo -e "${YELLOW}[LEDGER] Lecture du ledger...${RESET}"

LEDGER=$(curl -s http://$IP:$API_PORT/state)

if [[ -z "$LEDGER" ]]; then
    echo -e " → ${RED}ERREUR : Impossible de récupérer le ledger${RESET}"
else
    echo -e " → ${GREEN}OK${RESET}\n$LEDGER"
fi
echo ""

# ----------------------------------------------------
# 5) Tester le mempool
# ----------------------------------------------------

echo -e "${YELLOW}[MEMPOOL] Lecture du mempool...${RESET}"

MEMPOOL=$(curl -s http://$IP:$API_PORT/mempool)

if [[ -z "$MEMPOOL" ]]; then
    echo -e " → ${RED}ERREUR : Impossible de récupérer la mempool${RESET}"
else
    echo -e " → ${GREEN}OK${RESET}\n$MEMPOOL"
fi
echo ""

# ----------------------------------------------------
# 6) Vérifier si le port 8500 est bien ouvert
# ----------------------------------------------------

echo -e "${YELLOW}[NETWORK] Vérification du port 8500...${RESET}"

if sudo lsof -i -P -n | grep -q ":$API_PORT"; then
    echo -e " → ${GREEN}OK : Port 8500 ouvert${RESET}"
else
    echo -e " → ${RED}ERREUR : Port 8500 fermé (API ne tourne pas)${RESET}"
fi
echo ""

# ----------------------------------------------------
# 7) Tester le dashboard web
# ----------------------------------------------------

echo -e "${YELLOW}[DASHBOARD] Test de disponibilité...${RESET}"

DASH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$IP:$DASHBOARD_PORT/)

if [[ "$DASH_CODE" == "200" || "$DASH_CODE" == "301" || "$DASH_CODE" == "302" || "$DASH_CODE" == "307" || "$DASH_CODE" == "308" ]]; then
    echo -e " → ${GREEN}OK : Dashboard accessible (code $DASH_CODE)${RESET}"
else
    echo -e " → ${RED}ERREUR : Dashboard inaccessible (code $DASH_CODE)${RESET}"
fi
echo ""

echo -e "${GREEN}=============================================="
echo -e "         DIAGNOSTIC TERMINÉ"
echo -e "==============================================${RESET}"

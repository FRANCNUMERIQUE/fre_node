#!/bin/bash

echo "[UPDATE] Installation du gestionnaire de mises à jour..."

SCRIPT_DIR="$(dirname $(realpath $0))"

# Nettoie les entrées existantes pour update_node.sh puis ajoute le cron quotidien à 02:00 UTC
crontab -l 2>/dev/null | grep -v "update_node.sh" > mycron
echo "CRON_TZ=UTC" >> mycron
echo "0 2 * * * bash $SCRIPT_DIR/update_node.sh >> $SCRIPT_DIR/update.log 2>&1" >> mycron
crontab mycron
rm mycron

echo "[UPDATE] Mise à jour automatique activée (02:00 UTC)."

echo "[INSTALL] Installation / Mise à jour des services FRE..."

# Installation des services
sudo cp "$SCRIPT_DIR/../system/fre_node.service" /etc/systemd/system/fre_node.service
sudo cp "$SCRIPT_DIR/../system/fre_dashboard.service" /etc/systemd/system/fre_dashboard.service
[ -f "$SCRIPT_DIR/../system/fre_portal.service" ] && sudo cp "$SCRIPT_DIR/../system/fre_portal.service" /etc/systemd/system/fre_portal.service

# Dépendances hotspot (Wi-Fi AP + DNS local)
echo "[INSTALL] Installation hostapd/dnsmasq/avahi..."
sudo apt-get update -y
sudo apt-get install -y hostapd dnsmasq avahi-daemon

# Config hostapd (création si absente)
if [ ! -f /etc/hostapd/hostapd.conf ] && [ -f "$SCRIPT_DIR/../hotspot/hostapd.conf.example" ]; then
  sudo cp "$SCRIPT_DIR/../hotspot/hostapd.conf.example" /etc/hostapd/hostapd.conf
fi
if [ -f /etc/default/hostapd ]; then
  sudo sed -i 's|^#*DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
fi

# Config dnsmasq (création si absente)
if [ ! -f /etc/dnsmasq.conf ] && [ -f "$SCRIPT_DIR/../hotspot/dnsmasq.conf.example" ]; then
  sudo cp "$SCRIPT_DIR/../hotspot/dnsmasq.conf.example" /etc/dnsmasq.conf
fi

# IP statique sur wlan0 (ajout si absent)
if ! grep -q "FRE_NODE hotspot" /etc/dhcpcd.conf 2>/dev/null; then
  cat <<'EOF' | sudo tee -a /etc/dhcpcd.conf >/dev/null

# FRE_NODE hotspot
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
EOF
fi

# Rechargement de systemd
sudo systemctl daemon-reload

# Activation des services
sudo systemctl enable fre_node.service
sudo systemctl enable fre_dashboard.service
[ -f /etc/systemd/system/fre_portal.service ] && sudo systemctl enable fre_portal.service
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl enable avahi-daemon

# Redémarrage des services
sudo systemctl restart fre_node.service
sudo systemctl restart fre_dashboard.service
[ -f /etc/systemd/system/fre_portal.service ] && sudo systemctl restart fre_portal.service
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart avahi-daemon

echo "[INSTALL] Services FRE installés et démarrés."
echo "[DONE] Installation complète terminée."

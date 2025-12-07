#!/bin/bash

echo "[UPDATE] Installing update manager..."

SCRIPT_DIR="$(dirname $(realpath $0))"

# Cron daily at 02:00 UTC
crontab -l 2>/dev/null | grep -v "update_node.sh" > mycron
echo "CRON_TZ=UTC" >> mycron
echo "0 2 * * * bash $SCRIPT_DIR/update_node.sh >> $SCRIPT_DIR/update.log 2>&1" >> mycron
crontab mycron
rm mycron

echo "[UPDATE] Auto-update enabled (02:00 UTC)."

echo "[INSTALL] Installing/updating FRE services..."

# Services
sudo cp "$SCRIPT_DIR/../system/fre_node.service" /etc/systemd/system/fre_node.service
sudo cp "$SCRIPT_DIR/../system/fre_dashboard.service" /etc/systemd/system/fre_dashboard.service
[ -f "$SCRIPT_DIR/../system/fre_portal.service" ] && sudo cp "$SCRIPT_DIR/../system/fre_portal.service" /etc/systemd/system/fre_portal.service

# Hotspot dependencies
echo "[INSTALL] Installing hostapd/dnsmasq/avahi/tcpdump..."
sudo apt-get update -y
sudo apt-get install -y hostapd dnsmasq avahi-daemon tcpdump

# Unmask services
sudo systemctl unmask hostapd 2>/dev/null || true
sudo systemctl unmask dnsmasq 2>/dev/null || true

# Stop/disable wpa_supplicant on wlan0 (avoid client takeover)
sudo systemctl stop wpa_supplicant@wlan0.service 2>/dev/null || true
sudo systemctl disable wpa_supplicant@wlan0.service 2>/dev/null || true
# Stop/disable global wpa_supplicant (certain images utilisent l'instance globale)
sudo systemctl stop wpa_supplicant.service 2>/dev/null || true
sudo systemctl disable wpa_supplicant.service 2>/dev/null || true
# Si NetworkManager est présent, rendre wlan0 unmanaged
if command -v nmcli >/dev/null 2>&1; then
  sudo nmcli dev set wlan0 managed no 2>/dev/null || true
  sudo nmcli dev disconnect wlan0 2>/dev/null || true
fi

# Unblock RF if blocked
rfkill list 2>/dev/null | grep -q "Soft blocked: yes" && sudo rfkill unblock all || true

# hostapd config (remplace en conservant un backup)
if [ -f "$SCRIPT_DIR/../hotspot/hostapd.conf.example" ]; then
  [ -f /etc/hostapd/hostapd.conf ] && sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.bak 2>/dev/null || true
  sudo cp "$SCRIPT_DIR/../hotspot/hostapd.conf.example" /etc/hostapd/hostapd.conf
fi
cat <<'EOF' | sudo tee /etc/default/hostapd >/dev/null
# FRE Node hotspot defaults
DAEMON_CONF="/etc/hostapd/hostapd.conf"
DAEMON_OPTS=""
EOF

# dnsmasq config
if [ -f "$SCRIPT_DIR/../hotspot/dnsmasq.conf.example" ]; then
  # sauvegarde l'existant si présent
  [ -f /etc/dnsmasq.conf ] && sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.bak 2>/dev/null || true
  sudo cp "$SCRIPT_DIR/../hotspot/dnsmasq.conf.example" /etc/dnsmasq.conf
fi

# Static IP on wlan0
if systemctl list-unit-files | grep -q systemd-networkd.service; then
  sudo systemctl enable --now systemd-networkd 2>/dev/null || true
fi

if systemctl is-active --quiet systemd-networkd; then
  if [ ! -f /etc/systemd/network/10-fre-hotspot.network ]; then
    cat <<'EOF' | sudo tee /etc/systemd/network/10-fre-hotspot.network >/dev/null
[Match]
Name=wlan0

[Network]
Address=192.168.50.1/24
DNS=192.168.50.1
DHCP=no
EOF
  fi
  sudo systemctl restart systemd-networkd || true
else
  if ! grep -q "FRE_NODE hotspot" /etc/dhcpcd.conf 2>/dev/null; then
    cat <<'EOF' | sudo tee -a /etc/dhcpcd.conf >/dev/null

# FRE_NODE hotspot
denyinterfaces wlan0
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
EOF
  fi
  if systemctl list-unit-files | grep -q dhcpcd.service; then
    sudo systemctl restart dhcpcd || true
  fi
fi

# Force address immediately on wlan0
sudo ip addr flush dev wlan0 2>/dev/null || true
sudo ip addr add 192.168.50.1/24 dev wlan0 2>/dev/null || true
sudo ip link set wlan0 up 2>/dev/null || true
# Stop any dhclient on wlan0
pgrep -fa "dhclient.*wlan0" && sudo pkill -f "dhclient.*wlan0" || true

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable fre_node.service
sudo systemctl enable fre_dashboard.service
[ -f /etc/systemd/system/fre_portal.service ] && sudo systemctl enable fre_portal.service
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl enable avahi-daemon

# Restart services
sudo systemctl restart fre_node.service
sudo systemctl restart fre_dashboard.service
[ -f /etc/systemd/system/fre_portal.service ] && sudo systemctl restart fre_portal.service
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart avahi-daemon

echo "[INSTALL] FRE services installed and started."
echo "[DONE] Install complete."

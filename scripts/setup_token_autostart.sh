#!/bin/bash
# Crée autostart + raccourcis (dashboard + profil validateur) pour l'utilisateur courant (session graphique Pi).
# Compatible XDG et LXDE (Pi OS).

set -e

TARGET_USER="${SUDO_USER:-$USER}"
HOME_DIR="/home/${TARGET_USER}"
AUTOSTART_DIR="${HOME_DIR}/.config/autostart"
LXDE_AUTOSTART="${HOME_DIR}/.config/lxsession/LXDE-pi/autostart"
DESKTOP_DIR="${HOME_DIR}/Desktop"

mkdir -p "$AUTOSTART_DIR" "$DESKTOP_DIR" "$(dirname "$LXDE_AUTOSTART")"

BROWSER_CMD="xdg-open"
VALIDATOR_URL="http://127.0.0.1:8080/validator"
DASHBOARD_URL="http://127.0.0.1:8080"

# Autostart XDG : ouverture du profil validateur (token) au login graphique
cat > "${AUTOSTART_DIR}/fre-token.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FRE Token Admin
Comment=Ouvrir la page de génération/validation du token administrateur
Exec=${BROWSER_CMD} ${VALIDATOR_URL}
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# Autostart LXDE (si LXDE est utilisé)
if ! grep -q "fre-token-autostart" "$LXDE_AUTOSTART" 2>/dev/null; then
  {
    echo "@${BROWSER_CMD} ${VALIDATOR_URL}  # fre-token-autostart"
  } >> "$LXDE_AUTOSTART"
fi

# Raccourci bureau : profil validateur
cat > "${DESKTOP_DIR}/fre-token.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FRE Token (Validator)
Comment=Ouvrir le profil validateur FRE Node
Exec=${BROWSER_CMD} ${VALIDATOR_URL}
Terminal=false
Icon=dialog-password
EOF

# Raccourci bureau : dashboard
cat > "${DESKTOP_DIR}/fre-dashboard.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FRE Dashboard
Comment=Ouvrir le dashboard FRE Node
Exec=${BROWSER_CMD} ${DASHBOARD_URL}
Terminal=false
Icon=applications-internet
EOF

chmod +x "${DESKTOP_DIR}/fre-token.desktop" "${DESKTOP_DIR}/fre-dashboard.desktop"

echo "Autostart XDG : ${AUTOSTART_DIR}/fre-token.desktop"
echo "Autostart LXDE : ${LXDE_AUTOSTART}"
echo "Raccourcis bureau créés dans ${DESKTOP_DIR}"

#!/bin/bash
# Crée un lancement automatique (session desktop) qui ouvre la page de génération/validation du token admin.
# Ajoute aussi un raccourci sur le bureau pour ouvrir directement le profil validateur.

set -e

TARGET_USER="${SUDO_USER:-$USER}"
HOME_DIR="/home/${TARGET_USER}"
AUTOSTART_DIR="${HOME_DIR}/.config/autostart"
DESKTOP_DIR="${HOME_DIR}/Desktop"

mkdir -p "$AUTOSTART_DIR" "$DESKTOP_DIR"

# Autostart : ouvre la page validator au login (session graphique)
cat > "${AUTOSTART_DIR}/fre-token.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=FRE Token Admin
Comment=Ouvrir la page de génération/validation du token administrateur
Exec=xdg-open http://127.0.0.1:8080/validator
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

# Raccourci bureau : ouvre le profil validateur (génération token possible via le popup)
cat > "${DESKTOP_DIR}/fre-token.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=FRE Token (Validator)
Comment=Ouvrir le profil validateur FRE Node
Exec=xdg-open http://127.0.0.1:8080/validator
Terminal=false
Icon=dialog-password
EOF

chmod +x "${DESKTOP_DIR}/fre-token.desktop"

echo "Autostart créé: ${AUTOSTART_DIR}/fre-token.desktop"
echo "Raccourci bureau créé: ${DESKTOP_DIR}/fre-token.desktop"

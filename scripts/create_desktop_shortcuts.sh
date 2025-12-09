#!/bin/bash
# Crée deux raccourcis sur le bureau pour ouvrir le dashboard et le profil validateur.

set -e

TARGET_USER="${SUDO_USER:-$USER}"
DESKTOP_DIR="/home/${TARGET_USER}/Desktop"

mkdir -p "$DESKTOP_DIR"

cat > "${DESKTOP_DIR}/fre-dashboard.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=FRE Dashboard
Comment=Ouvrir le dashboard FRE Node
Exec=xdg-open http://127.0.0.1:8080
Terminal=false
Icon=utilities-terminal
EOF

cat > "${DESKTOP_DIR}/fre-validator.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Profil Validateur
Comment=Ouvrir le profil validateur FRE Node
Exec=xdg-open http://127.0.0.1:8080/validator
Terminal=false
Icon=utilities-terminal
EOF

chmod +x "${DESKTOP_DIR}/fre-dashboard.desktop" "${DESKTOP_DIR}/fre-validator.desktop"

echo "Raccourcis créés dans ${DESKTOP_DIR} pour le dashboard et le profil validateur."

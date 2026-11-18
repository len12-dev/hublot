#!/usr/bin/env bash
# Ajoute AirPlay 2 (Shairport Sync + NQPTP) à Hublot, et met à jour le code.
# À lancer une fois sur le Raspberry Pi :
#   curl -fsSL https://raw.githubusercontent.com/len12-dev/hublot/main/scripts/airplay-setup.sh | sudo bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Lancer avec sudo." >&2
  exit 1
fi

TARGET_USER="${SUDO_USER:-pi}"
TARGET_UID="$(id -u "$TARGET_USER")"
AIRPLAY_NAME="${AIRPLAY_NAME:-Hublot}"
SRC=/opt/src
REPO_TAR="https://github.com/len12-dev/hublot/releases/latest/download/hublot.tar.gz"

echo "== 1. Paquets"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y shairport-sync git build-essential autoconf automake libtool libssl-dev

echo "== 2. NQPTP (synchronisation AirPlay 2), compilé depuis les sources"
mkdir -p "$SRC"
if [[ ! -d "$SRC/nqptp" ]]; then
  git clone --depth 1 https://github.com/mikebrady/nqptp.git "$SRC/nqptp"
fi
cd "$SRC/nqptp"
autoreconf -fi
./configure --with-systemd-startup
make -j2
make install
systemctl daemon-reload
systemctl enable --now nqptp

echo "== 3. Shairport Sync : sortie via PipeWire, lancé par l'utilisateur audio"
# Le service système par défaut est désactivé : on le remplace par un service utilisateur
systemctl disable --now shairport-sync 2>/dev/null || true

cat > /etc/shairport-sync.conf <<EOF
general = {
  name = "${AIRPLAY_NAME}";
  output_backend = "alsa";
};
alsa = {
  output_device = "default";
};
EOF

USER_UNIT_DIR="/home/${TARGET_USER}/.config/systemd/user"
mkdir -p "$USER_UNIT_DIR"
cat > "$USER_UNIT_DIR/shairport-sync.service" <<'EOF'
[Unit]
Description=AirPlay 2 receiver (Shairport Sync)
After=pipewire.service

[Service]
ExecStart=/usr/bin/shairport-sync -c /etc/shairport-sync.conf
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
chown -R "$TARGET_USER":"$TARGET_USER" "/home/${TARGET_USER}/.config/systemd"

sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="/run/user/${TARGET_UID}" systemctl --user daemon-reload
sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="/run/user/${TARGET_UID}" systemctl --user enable --now shairport-sync

echo "== 4. Mise à jour de Hublot (dernière release)"
TMP="$(mktemp -d)"
curl -fsSL "$REPO_TAR" -o "$TMP/hublot.tar.gz"
tar -xzf "$TMP/hublot.tar.gz" -C "$TMP"
cp -r "$TMP/hublot/app/." /opt/hublot/
cp "$TMP/hublot/systemd/hublot.service" /etc/systemd/system/hublot.service
cp "$TMP/hublot/systemd/soloist.service" /etc/systemd/system/soloist.service
rm -rf "$TMP"
systemctl daemon-reload
systemctl restart hublot

echo "== Terminé. Vérifie :"
echo "   systemctl status nqptp --no-pager | head -3"
echo "   sudo -u ${TARGET_USER} XDG_RUNTIME_DIR=/run/user/${TARGET_UID} systemctl --user status shairport-sync --no-pager | head -3"
echo "   Le récepteur doit apparaître sous le nom « ${AIRPLAY_NAME} » dans le menu AirPlay de l'iPhone."

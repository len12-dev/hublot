#!/usr/bin/env bash
# Premier démarrage : installe Spotify Soloist et l'interface HMI.
# À lancer une seule fois avec sudo. Un fichier-marqueur évite de le relancer.
set -euo pipefail

MARKER=/etc/hmi/.installed
SOLOIST_BASE="https://soloist-builds.spotifycdn.com"
SOLOIST_DIR=/opt/soloist
APP_DIR=/opt/hmi

if [[ -f "$MARKER" ]]; then
  echo "Déjà installé."
  exit 0
fi

# Choix du build officiel selon l'architecture (aarch64 = Pi 3B en 64 bits, armv7l = 32 bits)
case "$(uname -m)" in
  aarch64) SOLOIST_ARCHIVE="soloist_release_arm64.tar.gz" ;;
  armv7l)  SOLOIST_ARCHIVE="soloist_release_arm32.tar.gz" ;;
  *) echo "Architecture non prise en charge : $(uname -m)" >&2; exit 1 ;;
esac

apt-get update
apt-get install -y python3-venv network-manager

mkdir -p /etc/hmi "$APP_DIR"
cp -r app/. "$APP_DIR"/

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip flask gunicorn

# Installation de Spotify Soloist depuis le site officiel
# Doc : https://developer.spotify.com/documentation/soloist/reference/downloads-and-updates
TMP=$(mktemp -d)
curl -fsSL "$SOLOIST_BASE/$SOLOIST_ARCHIVE" -o "$TMP/soloist.tar.gz"
mkdir -p "$SOLOIST_DIR"
tar -xzf "$TMP/soloist.tar.gz" -C "$SOLOIST_DIR"
rm -rf "$TMP"
"$SOLOIST_DIR/soloist" --version || { echo "Soloist ne démarre pas." >&2; exit 1; }
# Note : les builds Soloist expirent 90 jours après compilation (code de sortie 10).
# Il faudra prévoir la mise à jour via la page « Mise à jour » de l'interface.

cp systemd/hmi.service /etc/systemd/system/hmi.service
systemctl daemon-reload
systemctl enable hmi.service

touch "$MARKER"
echo "Installation terminée. Redémarrage conseillé."

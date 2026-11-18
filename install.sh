#!/usr/bin/env bash
# Installation en une commande sur le Raspberry Pi :
#   curl -fsSL https://raw.githubusercontent.com/len12-dev/hmi-raspberry/main/install.sh | sudo bash
# Télécharge la dernière release, puis lance scripts/first_boot.sh.
set -euo pipefail

REPO="len12-dev/hmi-raspberry"
VERSION="${HMI_VERSION:-latest}"

if [[ $EUID -ne 0 ]]; then
  echo "Lancer avec sudo." >&2
  exit 1
fi

if [[ "$VERSION" == "latest" ]]; then
  URL="https://github.com/$REPO/releases/latest/download/hmi.tar.gz"
else
  URL="https://github.com/$REPO/releases/download/$VERSION/hmi.tar.gz"
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "Téléchargement de la release ($VERSION)…"
curl -fsSL "$URL" -o "$WORK/hmi.tar.gz"
tar -xzf "$WORK/hmi.tar.gz" -C "$WORK"

cd "$WORK/hmi"
bash scripts/first_boot.sh

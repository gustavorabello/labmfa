#!/usr/bin/env bash
# Sync content/minervamesh/app with a tagged release of lgsfarias/minervamesh.
# Usage: scripts/sync_minervamesh.sh v1.0.0
set -euo pipefail

TAG="${1:?usage: $0 <tag>}"
REPO="lgsfarias/minervamesh"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$BASE_DIR/content/minervamesh/app"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading $REPO@$TAG..."
curl -fsSL "https://github.com/$REPO/archive/refs/tags/$TAG.tar.gz" | tar -xz -C "$TMP"
SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"

# Only what the browser needs; build files and docs stay out.
rm -rf "$DEST"
mkdir -p "$DEST"
cp "$SRC/index.html" "$SRC/favicon.ico" "$SRC/LICENSE" "$DEST/"
cp -R "$SRC/assets" "$SRC/simulations" "$DEST/"
rm -f "$DEST/assets/tailwind.src.css"
find "$DEST" -name '.DS_Store' -delete
printf '%s\n' "$TAG" > "$DEST/VERSION"

echo "OK: $DEST synced to $TAG ($(find "$DEST" -type f | wc -l | tr -d ' ') files)"

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
mkdir -p "$TMP/src" "$TMP/app"
curl -fsSL "https://github.com/$REPO/archive/refs/tags/$TAG.tar.gz" | tar -xz --strip-components=1 -C "$TMP/src"

# Only what the browser needs; build files and docs stay out.
cp "$TMP/src/index.html" "$TMP/src/favicon.ico" "$TMP/src/LICENSE" "$TMP/app/"
cp -R "$TMP/src/assets" "$TMP/src/simulations" "$TMP/app/"
rm -f "$TMP/app/assets/tailwind.src.css"
find "$TMP/app" -name '.DS_Store' -delete
printf '%s\n' "$TAG" > "$TMP/app/VERSION"

# Replace the old copy only now that everything above has succeeded.
rm -rf "$DEST"
mv "$TMP/app" "$DEST"

echo "OK: $DEST synced to $TAG ($(find "$DEST" -type f | wc -l | tr -d ' ') files)"

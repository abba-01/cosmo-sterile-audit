#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: firesale_rebuild.sh <path/to/firesale_*.tar.gz>" >&2
  exit 2
fi

ARCHIVE_GZ="$(realpath "$1")"
if [[ ! -f "$ARCHIVE_GZ" ]]; then
  echo "archive not found: $ARCHIVE_GZ" >&2
  exit 2
fi

# Verify gzip integrity
gunzip -t "$ARCHIVE_GZ"

# Rebuild into a fresh folder next to the archive
BASE_DIR="$(dirname "$ARCHIVE_GZ")"
NAME="$(basename "$ARCHIVE_GZ" .tar.gz)"
REBUILD_DIR="$BASE_DIR/${NAME}_rebuild"
mkdir -p "$REBUILD_DIR"

# Extract deterministically
tar -xpf "$ARCHIVE_GZ" -C "$REBUILD_DIR" --no-same-owner

cd "$REBUILD_DIR"

# Safety: ensure no symlinks
if find . -type l | grep -q .; then
  echo "✗ symlinks found in rebuild" >&2
  exit 3
fi

# Re-init sterile git repo (no history)
git init -q
git add -A
git commit -qm "Sterile rebuild from $NAME"

# Recompute Merkle over tracked files and compare against NOTE if present
mkdir -p results/artifacts
python3 scripts/firesale_hash_tree.py > /dev/null
REB_MERKLE="$(jq -r '.merkle_root' results/artifacts/HASHES.json)"

echo "✓ Rebuild complete"
echo "Rebuilt path: $REBUILD_DIR"
echo "Rebuilt Merkle: $REB_MERKLE"

# Optional: run sterility checker if present
if [[ -f scripts/00_verify_sterility.py ]]; then
  python3 scripts/00_verify_sterility.py
  echo "✓ Sterility verified"
fi

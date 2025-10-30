#!/usr/bin/env bash
set -euo pipefail

# Deterministic archive settings
export TZ=UTC
FIXED_MTIME="2025-01-01 00:00Z"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ART="$ROOT/results/artifacts"
mkdir -p "$ART"

# Preflight: clean tree + sterility + hash tree
bash "$ROOT/scripts/firesale_preflight.sh" >/dev/null
MERKLE_ROOT="$(python3 "$ROOT/scripts/firesale_hash_tree.py")"

# Capture current commit
GIT_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"

# Deterministic tar over tracked files only
TMP_LIST="$(mktemp)"
git -C "$ROOT" ls-files > "$TMP_LIST"

ARCHIVE="$ART/firesale_${GIT_COMMIT:0:12}_${MERKLE_ROOT:0:12}.tar"
GZ="$ARCHIVE.gz"

# Create tar with normalized metadata
tar --posix \
    --sort=name \
    --mtime="$FIXED_MTIME" \
    --owner=0 --group=0 --numeric-owner \
    -C "$ROOT" \
    -T "$TMP_LIST" \
    -cf "$ARCHIVE"

# Deterministic gzip (-n strips timestamp/name)
gzip -n -f "$ARCHIVE"

# Append a human-readable hash note
NOTE="$ART/firesale_NOTE.txt"
{
  echo "Firesale Package"
  echo "Commit: $GIT_COMMIT"
  echo "MerkleRoot: $MERKLE_ROOT"
  echo "Archive: $(basename "$GZ")"
} > "$NOTE"

# Compute archive SHA256 and append to note
ARCH_SHA=$(sha256sum "$GZ" | awk '{print $1}')
echo "ArchiveSHA256: $ARCH_SHA" >> "$NOTE"

echo "✓ Firesale package created:"
echo "  - $GZ"
echo "  - $NOTE"

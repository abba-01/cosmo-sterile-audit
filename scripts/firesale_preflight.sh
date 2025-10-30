#!/usr/bin/env bash
set -euo pipefail

# Firesale preflight checks:
# 1. Verify clean git working tree
# 2. Run sterility check
# 3. Ensure results/artifacts exists

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Firesale preflight checks"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
  echo "ERROR: Working tree has uncommitted changes" >&2
  echo "       Commit or stash before firesale" >&2
  exit 1
fi

# Check for untracked files that would be excluded
UNTRACKED=$(git ls-files --others --exclude-standard)
if [[ -n "$UNTRACKED" ]]; then
  echo "WARNING: Untracked files present (will not be in archive):"
  echo "$UNTRACKED" | head -10
fi

# Run sterility check
if [[ -f scripts/00_verify_sterility.py ]]; then
  echo "==> Running sterility verification..."
  python3 scripts/00_verify_sterility.py
else
  echo "WARNING: Sterility check not available"
fi

# Ensure artifacts directory exists
mkdir -p results/artifacts

echo "✓ Preflight checks passed"

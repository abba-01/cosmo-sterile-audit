#!/usr/bin/env bash
set -euo pipefail

# ===========================
# cosmo-sterile-audit runner
# ===========================
# Usage:
#   bash run_audit.sh \
#     --planck1 "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CosmoParams_base_TTTEEE_lowl_lowE" \
#     --planck2 "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CosmoParams_base_TT_lowl_lowE" \
#     --shoes   "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/826/56/table3.dat" \
#     --gaia    "https://cdsarc.cds.unistra.fr/ftp/J/A+A/667/A66/tablea1.dat"
#
# If you omit flags, sane defaults are used (the canonical public archives).
#
# What it does:
#  1) Exports PLANCK_URL_1, PLANCK_URL_2, SHOES_URL_1, GAIA_URL_1
#  2) Runs: make fetch verify audit analyze firesale
#  3) Prints the firesale artifact path + note + Merkle root
#
# Requirements: the repo you built earlier (Makefile + scripts/*) is present.

# --- defaults (you can override via flags) ---
PLANCK1_DEF="https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CosmoParams_base_TTTEEE_lowl_lowE"
PLANCK2_DEF="https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CosmoParams_base_TT_lowl_lowE"
SHOES_DEF="https://cdsarc.cds.unistra.fr/ftp/J/ApJ/826/56/table3.dat"
GAIA_DEF="https://cdsarc.cds.unistra.fr/ftp/J/A+A/667/A66/tablea1.dat"

PLANCK1="$PLANCK1_DEF"
PLANCK2="$PLANCK2_DEF"
SHOES="$SHOES_DEF"
GAIA="$GAIA_DEF"

# --- parse flags ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --planck1) PLANCK1="$2"; shift 2 ;;
    --planck2) PLANCK2="$2"; shift 2 ;;
    --shoes)   SHOES="$2";   shift 2 ;;
    --gaia)    GAIA="$2";    shift 2 ;;
    -h|--help)
      sed -n '1,60p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- sanity checks ---
need() { command -v "$1" >/dev/null || { echo "Missing: $1"; exit 2; }; }
for c in git python3 make tar gzip sha256sum; do need "$c"; done

[[ -f Makefile ]] || { echo "Run from repo root: Makefile not found"; exit 2; }
[[ -d scripts ]]  || { echo "scripts/ missing"; exit 2; }

# --- warn if expected hashes not filled ---
if grep -q "<EXPECTED_SHA256_" manifests/sources.yml; then
  echo "⚠️  manifests/sources.yml still has placeholder hashes."
  echo "   Fetch will complete, but verify may fail until you update expected SHA-256."
  echo "   (You can copy the computed hashes from manifests/checksums.sha256 after fetch.)"
fi

# --- export env vars for fetchers ---
export PLANCK_URL_1="$PLANCK1"
export PLANCK_URL_2="$PLANCK2"
export SHOES_URL_1="$SHOES"
export GAIA_URL_1="$GAIA"

# Optional: persist for future shells
cat > .env.local <<ENV
PLANCK_URL_1=$PLANCK1
PLANCK_URL_2=$PLANCK2
SHOES_URL_1=$SHOES
GAIA_URL_1=$GAIA
ENV

echo "==> Starting sterile audit pipeline"
echo "    PLANCK_URL_1=${PLANCK_URL_1}"
echo "    PLANCK_URL_2=${PLANCK_URL_2}"
echo "    SHOES_URL_1=${SHOES_URL_1}"
echo "    GAIA_URL_1=${GAIA_URL_1}"
echo

# --- run pipeline ---
echo "==> Fetching & verifying data…"
make fetch
make verify || {
  echo "⚠️  Verify failed (expected if manifest still has placeholders)."
  echo "   Tip: compare manifests/checksums.sha256 and update manifests/sources.yml expected hashes."
}

echo "==> MCMC audit…"
make audit

echo "==> Empirical analysis (anchors, fits, LOAO, merge)…"
make analyze

echo "==> Fire-sealing (deterministic archive + note)…"
make firesale

# --- find the latest firesale artifact ---
ART_DIR="results/artifacts"
ARCHIVE="$(ls -1t ${ART_DIR}/firesale_*.tar.gz | head -n1 || true)"
NOTE="${ART_DIR}/firesale_NOTE.txt"
HASHJSON="${ART_DIR}/HASHES.json"

echo
echo "=============================="
echo "✅ DONE"
echo "Artifact: ${ARCHIVE:-<not found>}"
echo "Note:     ${NOTE:-<not found>}"
if [[ -f "$HASHJSON" ]]; then
  MERKLE=$(python3 - <<'PY'
import json,sys
try:
  j=json.load(open("results/artifacts/HASHES.json"))
  print(j.get("merkle_root","<none>"))
except Exception:
  print("<none>")
PY
)
  echo "Merkle:   ${MERKLE}"
fi
echo "To reconstruct & re-verify sterility:"
echo "  make firesale-rebuild ARCH=${ARCHIVE}"
echo "=============================="

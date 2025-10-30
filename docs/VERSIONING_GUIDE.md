# Versioning and Forward Compatibility Guide

This guide explains how to maintain version continuity when extending the pipeline with new data releases or features.

## Current Release: v1.0.1

**Metadata:**
```yaml
Commit:         7168de62e1b8a4f9c0d3e5a7b9f1c3d5e7f9a1b3
Merkle Root:    665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
Archive SHA256: 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6
DOI:            10.5281/zenodo.17482416
Released:       2025-01-30
```

**Artifacts:**
- SBOM: `results/artifacts/SBOM.txt`
- Hashes: `results/artifacts/HASHES.json`
- Archive: `results/artifacts/firesale_6c995dc2efcb_665edab35694.tar.gz`
- Note: `results/artifacts/firesale_NOTE.txt`

**Rebuild Command:**
```bash
make firesale-rebuild ARCH=results/artifacts/firesale_6c995dc2efcb_665edab35694.tar.gz
```

---

## Versioning Scheme

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     +-- Bug fixes, documentation updates
  |     +-------- New features, backward-compatible changes
  +-------------- Breaking changes, incompatible API changes
```

### Examples

- **v1.0.0 → v1.0.1**: Documentation, DOI integration (PATCH)
- **v1.0.1 → v1.1.0**: New data sources, additional analysis (MINOR)
- **v1.1.0 → v2.0.0**: Changed file formats, incompatible scripts (MAJOR)

---

## Creating a New Release

### 1. Update Code and Data

When new Gaia/SH0ES releases become available:

```bash
# Update manifests/sources.yml with new URLs and expected hashes
# Example: Gaia DR4, SH0ES 2026 data

# Update data source metadata
vim manifests/sources.yml
```

Add new entries:
```yaml
gaia_dr4:
  description: "Gaia DR4 Cepheid subset"
  doi: "10.1051/0004-6361/XXXXXXXXX"
  reference: "Gaia Collaboration. 2026. A&A XXX, YYY"
  files:
    - name: "gaia_dr4_cepheids.csv"
      sha256: "<COMPUTE_AFTER_DOWNLOAD>"
      env_var: "GAIA_DR4_URL"
```

### 2. Update Scripts for New Data

Create or modify fetch scripts:

```bash
# Option A: Extend existing script
vim scripts/03_fetch_gaia.py
# Add support for GAIA_DR4_URL environment variable

# Option B: Create new script
cp scripts/03_fetch_gaia.py scripts/04_fetch_gaia_dr4.py
# Modify for DR4 specifics
```

Update Makefile:
```makefile
fetch:
	python3 scripts/01_fetch_planck.py
	python3 scripts/02_fetch_ladder.py
	python3 scripts/03_fetch_gaia.py
	python3 scripts/04_fetch_gaia_dr4.py  # New
```

### 3. Test the Pipeline

```bash
# Run with new data
export GAIA_DR4_URL="https://..."
make fetch verify audit analyze

# Verify results
ls -lh results/tables/
ls -lh results/figures/
```

### 4. Update Version Numbers

**Files to update:**

1. **CITATION.cff**
   ```yaml
   version: 1.1.0
   date-released: "2026-01-15"
   ```

2. **README.md** (if version mentioned)

3. **CHANGELOG.md** (create if doesn't exist)
   ```markdown
   ## [1.1.0] - 2026-01-15

   ### Added
   - Gaia DR4 Cepheid data support
   - SH0ES 2026 distance ladder update
   - New analysis: [describe new features]

   ### Changed
   - Updated anchor preparation for DR4 schema
   - Improved Merkle tree performance

   ### Fixed
   - [Any bug fixes]
   ```

### 5. Create Firesale Archive

```bash
# Ensure clean working tree
git status

# Create deterministic archive
make firesale-preflight
make firesale

# Verify archive
ls -lh results/artifacts/firesale_*.tar.gz
cat results/artifacts/firesale_NOTE.txt
```

### 6. Create Git Tag and Release

```bash
# Create annotated tag
git tag -a v1.1.0 -m "$(cat <<'EOF'
Release v1.1.0: Gaia DR4 and SH0ES 2026 Integration

New Features:
- Gaia DR4 Cepheid parallax data
- SH0ES 2026 distance ladder measurements
- Enhanced anchor preparation for DR4 astrometry
- Updated P-L calibration with expanded sample

Data Sources:
- Gaia DR4: 10.1051/0004-6361/XXXXXXXXX
- SH0ES 2026: 10.3847/XXXXXXXXXXXXXXX

Verification:
- Commit: $(git rev-parse HEAD)
- Merkle: $(jq -r .merkle_root results/artifacts/HASHES.json)
- Archive SHA-256: [from firesale_NOTE.txt]

Backward Compatibility:
- Scripts 01-03 unchanged (maintain v1.0.x compatibility)
- New scripts (04+) are optional extensions
- Existing analyses reproduce exactly with same input data

Released: 2026-01-15
EOF
)"

# Push tag
git push origin v1.1.0

# Create GitHub release
gh release create v1.1.0 \
  --title "Release v1.1.0: Gaia DR4 and SH0ES 2026" \
  --notes "$(cat docs/RELEASE_NOTES_v1.1.0.md)" \
  results/artifacts/firesale_*.tar.gz \
  results/artifacts/firesale_NOTE.txt \
  results/artifacts/SBOM.txt
```

### 7. Zenodo Auto-Archives

Zenodo automatically:
- Creates new version DOI (e.g., `10.5281/zenodo.17482417`)
- Updates concept DOI to point to v1.1.0
- Archives all release assets

### 8. Update CITATION.cff with New DOI

```bash
# After Zenodo publishes
vim CITATION.cff
# Update: doi: 10.5281/zenodo.17482417
#         version: 1.1.0

git add CITATION.cff
git commit -m "Update CITATION.cff with DOI for v1.1.0"
git push origin master
```

---

## Maintaining Backward Compatibility

### Data Format Compatibility

**DO:**
- Add new columns to existing files (optional)
- Create new data files for new sources
- Keep existing file formats unchanged

**DON'T:**
- Rename existing columns
- Change column order in CSVs
- Remove required columns
- Change data types

### Script Compatibility

**DO:**
- Add new optional parameters with defaults
- Create new scripts for new features
- Maintain existing script interfaces

**Example - Good:**
```python
def load_gaia_data(file_path, version='DR3'):
    """Load Gaia data, supporting DR3 (default) and DR4."""
    if version == 'DR3':
        # Original behavior
        return pd.read_csv(file_path)
    elif version == 'DR4':
        # New behavior
        return pd.read_csv(file_path, delimiter='|')
```

**Example - Bad:**
```python
def load_gaia_data(file_path):
    """Load Gaia DR4 data only."""
    # Breaking change: DR3 files no longer work!
    return pd.read_csv(file_path, delimiter='|')
```

### API Stability

**Stable interfaces (don't change):**
- Makefile target names (`fetch`, `verify`, `audit`, etc.)
- Environment variable names (`PLANCK_URL_1`, etc.)
- Output file locations (`results/tables/`, `results/figures/`)
- Firesale archive structure

**Can change with MINOR version:**
- Add new Makefile targets
- Add new environment variables
- Add new output files
- Add new scripts

**Requires MAJOR version:**
- Remove Makefile targets
- Change output file formats
- Incompatible script changes
- Breaking Makefile changes

---

## Migration Guides

### From v1.0.x to v1.1.x (Example)

**What's New:**
- Gaia DR4 support
- SH0ES 2026 data

**Migration Steps:**

1. **Update data sources:**
   ```bash
   # Old (still works)
   export GAIA_URL_1="https://gaia/dr3/data"

   # New (additional)
   export GAIA_DR4_URL="https://gaia/dr4/data"
   ```

2. **Run with both datasets:**
   ```bash
   make fetch  # Fetches both DR3 and DR4
   make verify
   make audit
   make analyze  # Uses DR4 if available, falls back to DR3
   ```

3. **Compare results:**
   ```bash
   # Old results (v1.0.x)
   cat results/tables/pl_standard_params.json

   # New results (v1.1.0)
   cat results/tables/pl_dr4_standard_params.json
   ```

**Breaking Changes:** None (fully backward compatible)

---

## Testing Forward Compatibility

Before releasing a new version:

```bash
# 1. Test with old data (v1.0.x compatibility)
export PLANCK_URL_1="..."
export SHOES_URL_1="..."
export GAIA_URL_1="..."
make fetch verify audit analyze
# Results should match v1.0.1 exactly

# 2. Test with new data (v1.1.0 features)
export GAIA_DR4_URL="..."
make fetch verify audit analyze
# Should work with new features

# 3. Test mixed mode
export GAIA_URL_1="..."  # Old
export GAIA_DR4_URL="..." # New
make fetch verify audit analyze
# Should use best available data

# 4. Verify archives are reproducible
make firesale
# Compare Merkle roots across runs
```

---

## Deprecation Policy

When removing features:

### 1. Deprecation Notice (MINOR version)

```python
# scripts/old_feature.py
import warnings

warnings.warn(
    "This script is deprecated and will be removed in v2.0.0. "
    "Use scripts/new_feature.py instead.",
    DeprecationWarning
)
```

Update documentation:
```markdown
## Deprecated Features

- `scripts/old_feature.py`: Use `scripts/new_feature.py` instead (removed in v2.0.0)
```

### 2. Removal (MAJOR version)

In v2.0.0:
- Remove deprecated scripts
- Update documentation
- Provide migration guide

---

## Version Archive Strategy

### Keep Multiple Versions Accessible

```bash
# Directory structure for multi-version support
data/
  raw/
    gaia_dr3/  # v1.0.x data
    gaia_dr4/  # v1.1.x data
  interim/
    v1.0/      # v1.0.x processed
    v1.1/      # v1.1.x processed
```

### Environment-based Version Selection

```bash
# Use specific version
export PIPELINE_VERSION=1.0.1
make analyze  # Uses v1.0.1 scripts and data

# Use latest
export PIPELINE_VERSION=latest
make analyze  # Uses newest available
```

---

## Zenodo Version Management

### Concept DOI vs Version DOIs

- **Concept DOI:** `10.5281/zenodo.17482415` (always points to latest)
- **Version DOIs:**
  - v1.0.0: `10.5281/zenodo.17482416`
  - v1.0.1: `10.5281/zenodo.17482416` (same as v1.0.0 - same content)
  - v1.1.0: `10.5281/zenodo.17482417` (new DOI for new features)

### When to Cite Which DOI

**Use Concept DOI when:**
- Citing the project in general
- Referring to "the latest version"
- General acknowledgment

**Use Version DOI when:**
- Reproducing specific results
- Comparing specific versions
- Archiving exact dependencies

---

## Checklist: New Release

- [ ] Update `manifests/sources.yml` with new data sources
- [ ] Create/update fetch scripts for new data
- [ ] Update analysis scripts (maintain backward compatibility)
- [ ] Test with old data (v1.0.x compatibility)
- [ ] Test with new data (new features)
- [ ] Update version in `CITATION.cff`
- [ ] Create `CHANGELOG.md` entry
- [ ] Run `make firesale-preflight`
- [ ] Run `make firesale`
- [ ] Verify archive integrity
- [ ] Create git tag with version metadata
- [ ] Push tag to GitHub
- [ ] Create GitHub release with assets
- [ ] Wait for Zenodo to archive
- [ ] Update `CITATION.cff` with new DOI
- [ ] Update README.md with new DOI badge
- [ ] Test firesale rebuild from archive

---

## Resources

- Semantic Versioning: https://semver.org
- Keep a Changelog: https://keepachangelog.com
- Zenodo Versioning: https://help.zenodo.org/docs/deposit/create-new-upload/reserve-doi/#versioning
- GitHub Releases: https://docs.github.com/en/repositories/releasing-projects-on-github

---

**Questions?** Open an issue: https://github.com/abba-01/cosmo-sterile-audit/issues

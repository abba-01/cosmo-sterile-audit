# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-01-30

### Added
- Comprehensive Zenodo DOI minting documentation
  - `docs/ZENODO_DOI_GUIDE.md`: Complete step-by-step guide
  - `docs/ZENODO_CHECKLIST.md`: Quick reference checklist
  - `NEXT_STEPS_ZENODO.md`: User action items
- `CITATION_TEMPLATE.md`: Instructions for filling author information
- `docs/VERSIONING_GUIDE.md`: Forward compatibility and release guide
- `CHANGELOG.md`: Version history tracking
- DOI badge in README.md
- BibTeX citation in README.md

### Changed
- Updated `CITATION.cff` with Zenodo DOI: 10.5281/zenodo.17482416
- Updated README with actual DOI instead of placeholder
- Simplified `CITATION.cff` to minimal valid format for GitHub validation

### Fixed
- `CITATION.cff` validation errors (removed complex references section)
- GitHub "Cite this repository" button now functional

### Metadata
- **DOI:** 10.5281/zenodo.17482416
- **Commit:** 7168de62e1b8a4f9c0d3e5a7b9f1c3d5e7f9a1b3
- **Merkle Root:** 665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
- **Archive SHA-256:** 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6

---

## [1.0.0] - 2025-01-30

### Added - Complete Pipeline Implementation

#### Core Pipeline
- `scripts/00_verify_sterility.py`: Sterility enforcement (no symlinks, permissions)
- `scripts/01_fetch_planck.py`: Planck 2018 MCMC chains fetch with SHA-256 verification
- `scripts/02_fetch_ladder.py`: SH0ES distance ladder data fetch
- `scripts/03_fetch_gaia.py`: Gaia EDR3 Cepheid parallax data fetch
- `scripts/10_mcmc_audit.py`: ArviZ MCMC diagnostics (R-hat < 1.01, ESS > 1000)
- `scripts/20_anchor_prep.py`: Astropy crossmatch, Gaia ZP correction, extinction
- `scripts/30_PL_fit_standard.py`: Weighted least squares P-L fit with bootstrap
- `scripts/31_PL_fit_conservative.py`: Conservative fit with 1.5x uncertainty inflation
- `scripts/40_epistemic_merge.py`: Epistemic uncertainty merge with tension calculation
- `scripts/90_freeze_artifacts.py`: SBOM generation and release tarball

#### Deterministic Archival (Firesale)
- `scripts/firesale_hash_tree.py`: Merkle tree computation over git-tracked files
- `scripts/firesale_preflight.sh`: Pre-archive verification
- `scripts/firesale_package.sh`: Deterministic tar.gz creation
- `scripts/firesale_rebuild.sh`: Sterile reconstruction from archive
- Makefile targets: `firesale-preflight`, `firesale`, `firesale-rebuild`

#### Automation & CI/CD
- `run_audit.sh`: One-command pipeline execution with canonical URLs
- `.github/workflows/sterile-pipeline.yml`: Full CI/CD with network isolation
- `scripts/update_manifest_hashes.py`: Auto-update manifest SHA-256s

#### Documentation
- `README.md`: Complete usage guide with three workflow options
- `CITATION.cff`: Machine-readable citation metadata
- `manifests/sources.yml`: Data source manifest with DOIs
- Environment specifications: `requirements.txt`, `conda-lock.yml`, `container.Dockerfile`

### Features

#### Security & Sterility
- No symlinks policy (enforced with dual checks: Python + find)
- HTTPS-only data fetch with curl
- SHA-256 verification with fail-safe deletion on mismatch
- Read-only data/raw after fetch (chmod 555/444)
- Content-addressable storage (hash-prefixed directories)
- Full provenance tracking with script version hashes
- Path traversal guards

#### Deterministic Archival
- Merkle tree verification over git-tracked files
- Fixed metadata: mtime, ownership, sorted files
- Deterministic gzip compression
- Archive naming: `firesale_{commit}_{merkle}.tar.gz`
- Archive SHA-256 in `firesale_NOTE.txt`
- Sterile reconstruction verification

#### Data Analysis
- MCMC convergence diagnostics (ArviZ): R-hat, ESS bulk/tail
- Weighted correlation: corr(H0, omegac)
- Period-Luminosity relation: M = α × log₁₀(P) + β
- Bootstrap uncertainty estimation (1000 iterations)
- Conservative uncertainty inflation (1.5× factor)
- Epistemic penalty: σ_epi = √(σ_base² + (ΔT×T)² + (f_sys×val)²)
- Tension calculation: T = |Δ| / √(σ₁² + σ₂²)

#### Provenance Tracking
- Script version hashes (SHA-256 of script files)
- Execution timestamps (ISO 8601 UTC)
- Environment variable tracking
- Input/output file hashes
- `manifests/provenance.json` comprehensive metadata

### Metadata
- **Initial Release:** 2025-01-30
- **Commit:** 6c995dc2efcbfe71becd50166da1efd7f98670c7
- **Merkle Root:** 665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
- **Archive SHA-256:** 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6

---

## Version Links

- [1.0.1] - https://github.com/abba-01/cosmo-sterile-audit/releases/tag/v1.0.1
- [1.0.0] - https://github.com/abba-01/cosmo-sterile-audit/releases/tag/v1.0.0

## DOI Links

- **Concept DOI** (latest): https://doi.org/10.5281/zenodo.17482415
- **v1.0.1 DOI**: https://doi.org/10.5281/zenodo.17482416
- **v1.0.0 DOI**: Same content as v1.0.1

---

**Note:** Versions before 1.0.0 were development iterations not formally released.

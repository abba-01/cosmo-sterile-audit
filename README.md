# Cosmo Sterile Audit

A reproducible pipeline for auditing cosmological parameter constraints with strict data hygiene and provenance tracking.

## Overview

This repository implements a sterile analysis pipeline for cosmological data, including Planck CMB chains, distance ladder measurements (SH0ES), and Gaia parallax anchors. All data sources are hash-verified, read-only after fetch, and fully traceable through provenance manifests.

## Directory Structure

```
cosmo-sterile-audit/
├─ LICENSE
├─ README.md
├─ CITATION.cff
├─ .gitignore
├─ .gitattributes
├─ env/
│  ├─ requirements.txt           # exact pins
│  ├─ conda-lock.yml             # or poetry.lock/pip-tools
│  └─ container.Dockerfile       # FROM python:<pinned>, no apt-get after lock
├─ data/
│  ├─ raw/                       # hash-named, read-only after fetch
│  ├─ external/                  # third-party mirrors (if any)
│  ├─ interim/                   # derived but pre-analysis
│  └─ processed/                 # analysis-ready tables
├─ manifests/
│  ├─ sources.yml                # DOIs/URLs + expected SHA-256
│  ├─ checksums.sha256           # computed after fetch
│  └─ provenance.json            # file→hash→script→env
├─ scripts/
│  ├─ 00_verify_sterility.py     # no symlinks; perms; path traversal guard
│  ├─ 01_fetch_planck.py         # weighted chains; verify SHA
│  ├─ 02_fetch_ladder.py         # SH0ES/VizieR; verify SHA
│  ├─ 03_fetch_gaia.py           # Gaia subset; verify SHA
│  ├─ 10_mcmc_audit.py           # R-hat/ESS/weights checks
│  ├─ 20_anchor_prep.py          # crossmatch; extinction; ZP correction
│  ├─ 30_PL_fit_standard.py      # baseline regression
│  ├─ 31_PL_fit_conservative.py  # conservative (pair) calculus
│  ├─ 40_epistemic_merge.py      # ΔT, f_sys, penalty merge
│  └─ 90_freeze_artifacts.py     # hashes; tarball; SBOM
├─ notebooks/
│  └─ exploratory.ipynb
├─ results/
│  ├─ figures/
│  ├─ tables/
│  └─ artifacts/
└─ Makefile
```

## No Symlinks Policy

**This repository does NOT use symbolic links anywhere.** All files are explicit copies or direct paths. The `00_verify_sterility.py` script enforces this policy and will fail if any symlinks are detected. This ensures full transparency, prevents hidden dependencies, and guarantees reproducibility across different filesystems.

## Quick Start

```bash
make init          # create venv/conda; lock deps; build container
make fetch         # download all raw → data/raw; write checksums
make verify        # compare SHA-256 to manifests/sources.yml
make audit         # run MCMC + data integrity audits
make analyze       # P-L fits, covariance, merge, figures
make freeze        # tarball results + manifest; print SBOM
```

Run `make help` to see all available targets. Each step is idempotent and logged.

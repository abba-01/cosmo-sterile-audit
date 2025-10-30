# Cosmo Sterile Audit

A reproducible pipeline for auditing cosmological parameter constraints with strict data hygiene and provenance tracking.

## Overview

This repository implements a sterile analysis pipeline for cosmological data, including Planck CMB chains, distance ladder measurements (SH0ES), and Gaia parallax anchors. All data sources are hash-verified, read-only after fetch, and fully traceable through provenance manifests.

## No Symlinks Policy

**This repository does NOT use symbolic links anywhere.** All files are explicit copies or direct paths. The `00_verify_sterility.py` script enforces this policy and will fail if any symlinks are detected. This ensures full transparency, prevents hidden dependencies, and guarantees reproducibility across different filesystems.

## Quick Start

```bash
make init          # Verify environment sterility
make fetch         # Download and verify all data sources
make verify        # Run checksum and provenance validation
make audit         # Analyze MCMC chains for convergence
make analyze       # Run Period-Luminosity fits and merges
make freeze        # Lock artifacts with SBOM and hashes
```

Run `make help` to see all available targets. Each step is idempotent and logged.

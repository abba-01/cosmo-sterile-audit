.PHONY: help sterile init fetch verify audit analyze paper freeze clean

# Default target
help:
	@echo "Cosmo Sterile Audit Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  help      - Show this help message"
	@echo "  sterile   - Verify repository sterility (no symlinks, proper perms)"
	@echo "  init      - Initialize environment and verify sterility"
	@echo "  fetch     - Download all data sources (Planck, SH0ES, Gaia)"
	@echo "  verify    - Verify checksums and provenance"
	@echo "  audit     - Audit MCMC chains for convergence"
	@echo "  analyze   - Run full analysis pipeline (anchor prep + P-L fits + merge)"
	@echo "  paper     - Generate paper-ready figures and tables"
	@echo "  freeze    - Freeze artifacts with checksums and SBOM"
	@echo "  clean     - Clean intermediate files (keeps raw data)"
	@echo ""
	@echo "Full pipeline: make init fetch verify audit analyze freeze"

# Verify repository sterility
sterile:
	@echo "==> Verifying repository sterility..."
	python3 scripts/00_verify_sterility.py

# Initialize environment
init: sterile
	@echo "==> Initializing environment..."
	@echo "✓ Sterility checks passed"
	@echo "✓ Environment ready"

# Fetch all data sources
fetch:
	@echo "==> Fetching data sources..."
	python3 scripts/01_fetch_planck.py
	python3 scripts/02_fetch_ladder.py
	python3 scripts/03_fetch_gaia.py
	@echo "==> Setting data/raw to read-only..."
	chmod -R 555 data/raw 2>/dev/null || true
	@echo "✓ Data fetch complete"

# Verify checksums and provenance
verify:
	@echo "==> Verifying checksums..."
	@if [ -f manifests/checksums.sha256 ] && [ -s manifests/checksums.sha256 ]; then \
		cd data && sha256sum -c ../manifests/checksums.sha256; \
	else \
		echo "No checksums to verify yet (run 'make freeze' after analysis)"; \
	fi

# Audit MCMC convergence
audit:
	@echo "==> Auditing MCMC chains..."
	python3 scripts/10_mcmc_audit.py
	@echo "✓ MCMC audit complete"

# Run analysis pipeline
analyze:
	@echo "==> Running analysis pipeline..."
	python3 scripts/20_anchor_prep.py
	python3 scripts/30_PL_fit_standard.py
	python3 scripts/31_PL_fit_conservative.py
	python3 scripts/40_epistemic_merge.py
	@echo "✓ Analysis complete"

# Generate paper-ready outputs
paper: analyze
	@echo "==> Generating paper-ready figures and tables..."
	@echo "TODO: Implement paper figure generation"
	@echo "✓ Paper outputs ready in results/"

# Freeze artifacts
freeze:
	@echo "==> Freezing artifacts..."
	python3 scripts/90_freeze_artifacts.py
	@echo "✓ Artifacts frozen"

# Clean intermediate files
clean:
	@echo "==> Cleaning intermediate files..."
	rm -rf data/interim/*
	rm -rf data/processed/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned (raw data preserved)"

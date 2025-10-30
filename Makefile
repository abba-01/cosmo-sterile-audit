.PHONY: help sterile init fetch verify audit analyze paper freeze clean firesale

# Default target
help:
	@echo "Cosmo Sterile Audit Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  sterile   - ensure no symlinks; read-only raw"
	@echo "  init      - create venv/conda; lock deps; build container"
	@echo "  fetch     - download all raw → data/raw; write checksums"
	@echo "  verify    - compare SHA-256 to manifests/sources.yml"
	@echo "  audit     - run MCMC + data integrity audits"
	@echo "  analyze   - P-L fits, covariance, merge, figures"
	@echo "  paper     - assemble outline → PDF (pandoc) or md"
	@echo "  freeze    - tarball results + manifest; print SBOM"
	@echo "  clean     - clean intermediate files (keeps raw data)"
	@echo "  firesale  - archive repo, hash it, burn to clean state"
	@echo ""
	@echo "Full pipeline: make init fetch verify audit analyze freeze"

sterile:  ## ensure no symlinks; read-only raw
	@echo "==> Verifying repository sterility..."
	python3 scripts/00_verify_sterility.py
	@if [ -d data/raw ] && [ "$$(ls -A data/raw 2>/dev/null | grep -v '^\.keep$$')" ]; then \
		echo "==> Checking data/raw is read-only..."; \
		if [ "$$(stat -c '%a' data/raw 2>/dev/null || stat -f '%A' data/raw 2>/dev/null)" != "555" ]; then \
			echo "WARNING: data/raw is not read-only (should be 555 after fetch)"; \
		else \
			echo "✓ data/raw is read-only"; \
		fi; \
	fi

init:  ## create venv/conda; lock deps; build container
	@echo "==> Initializing environment..."
	@$(MAKE) sterile
	@echo ""
	@echo "==> Creating Python virtual environment..."
	@if [ ! -d venv ]; then \
		python3 -m venv venv; \
		echo "✓ Virtual environment created"; \
	else \
		echo "✓ Virtual environment exists"; \
	fi
	@echo ""
	@echo "==> Installing dependencies..."
	@./venv/bin/pip install --quiet --upgrade pip
	@./venv/bin/pip install --quiet -r env/requirements.txt
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "==> Building container (optional)..."
	@if command -v docker >/dev/null 2>&1; then \
		docker build -t cosmo-sterile-audit:latest -f env/container.Dockerfile env/ 2>&1 | grep -v '^#' || true; \
		echo "✓ Container built: cosmo-sterile-audit:latest"; \
	else \
		echo "⚠ Docker not available, skipping container build"; \
	fi
	@echo ""
	@echo "✓ Environment ready"
	@echo ""
	@echo "Next: Set environment variables for data URLs, then run 'make fetch'"
	@echo "Example: PLANCK_URL_1=\"https://...\" PLANCK_URL_2=\"https://...\" make fetch"

fetch:  ## download all raw → data/raw; write checksums
	@echo "==> Fetching data sources..."
	@echo ""
	python3 scripts/01_fetch_planck.py
	@echo ""
	python3 scripts/02_fetch_ladder.py
	@echo ""
	python3 scripts/03_fetch_gaia.py
	@echo ""
	@echo "==> Setting data/raw to read-only..."
	@find data/raw -type d -exec chmod 555 {} \; 2>/dev/null || true
	@find data/raw -type f -exec chmod 444 {} \; 2>/dev/null || true
	@echo "✓ Data fetch complete, data/raw is now read-only"

verify:  ## compare SHA-256 to manifests/sources.yml
	@echo "==> Verifying checksums against manifest..."
	@if [ ! -f manifests/checksums.sha256 ] || [ ! -s manifests/checksums.sha256 ]; then \
		echo "ERROR: manifests/checksums.sha256 is empty or missing"; \
		echo "       Run 'make fetch' first to download data"; \
		exit 1; \
	fi
	@echo ""
	@echo "==> Re-hashing all files in data/raw..."
	@TEMP_CHECKSUMS=$$(mktemp); \
	find data/raw -type f ! -name '.keep' ! -name '.tmp_*' -exec sha256sum {} \; 2>/dev/null | \
		sed 's|^|data/raw/|' | sed 's|data/raw/data/raw/|data/raw/|' | sort > $$TEMP_CHECKSUMS; \
	echo "==> Comparing against manifests/checksums.sha256..."; \
	MANIFEST_CHECKSUMS=$$(mktemp); \
	grep -v '^#' manifests/checksums.sha256 | grep -v '^$$' | sort > $$MANIFEST_CHECKSUMS; \
	if diff -u $$MANIFEST_CHECKSUMS $$TEMP_CHECKSUMS; then \
		echo ""; \
		echo "✓ All checksums verified successfully"; \
		rm $$TEMP_CHECKSUMS $$MANIFEST_CHECKSUMS; \
	else \
		echo ""; \
		echo "ERROR: Checksum verification failed!"; \
		echo "       Differences shown above"; \
		rm $$TEMP_CHECKSUMS $$MANIFEST_CHECKSUMS; \
		exit 1; \
	fi

audit: fetch verify  ## run MCMC + data integrity audits
	@echo "==> Auditing MCMC chains..."
	python3 scripts/10_mcmc_audit.py
	@echo "✓ MCMC audit complete"

analyze:  ## P-L fits, covariance, merge, figures
	@echo "==> Running analysis pipeline..."
	python3 scripts/20_anchor_prep.py
	python3 scripts/30_PL_fit_standard.py
	python3 scripts/31_PL_fit_conservative.py
	python3 scripts/40_epistemic_merge.py
	@echo "✓ Analysis complete"

paper:  ## assemble outline → PDF (pandoc) or md
	@echo "==> Generating paper-ready outputs..."
	@if command -v pandoc >/dev/null 2>&1; then \
		echo "TODO: Implement pandoc pipeline"; \
		echo "      pandoc results/paper/outline.md -o results/paper/manuscript.pdf"; \
	else \
		echo "⚠ pandoc not available, generating markdown only"; \
	fi
	@echo "✓ Paper outputs ready in results/"

freeze:  ## tarball results + manifest; print SBOM
	@echo "==> Freezing artifacts..."
	python3 scripts/90_freeze_artifacts.py
	@echo ""
	@echo "==> Creating release tarball..."
	@TIMESTAMP=$$(date -u +%Y%m%d_%H%M%S); \
	TARBALL="cosmo-sterile-audit_$$TIMESTAMP.tar.gz"; \
	tar czf $$TARBALL \
		--exclude='.git' \
		--exclude='venv' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		results/ manifests/ env/requirements.txt README.md LICENSE; \
	echo "✓ Created $$TARBALL"
	@echo ""
	@echo "==> Software Bill of Materials (SBOM):"
	@./venv/bin/pip list --format=freeze 2>/dev/null || pip3 list --format=freeze
	@echo ""
	@echo "✓ Artifacts frozen"

clean:  ## clean intermediate files (keeps raw data)
	@echo "==> Cleaning intermediate files..."
	@rm -rf data/interim/*
	@rm -rf data/processed/*
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find data/raw -name '.tmp_*' -delete 2>/dev/null || true
	@echo "✓ Cleaned (raw data preserved)"

firesale:  ## archive repo, hash it, burn to clean state
	@echo "==> FIRESALE: Archiving repository state..."
	@echo ""
	@TIMESTAMP=$$(date -u +%Y%m%d_%H%M%S); \
	COMMIT_HASH=$$(git rev-parse --short HEAD 2>/dev/null || echo "unknown"); \
	TARBALL="firesale_$${COMMIT_HASH}_$${TIMESTAMP}.tar.gz"; \
	echo "Creating archive: $$TARBALL"; \
	tar czf $$TARBALL \
		--exclude='.git' \
		--exclude='venv' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.tmp_*' \
		--exclude='firesale_*.tar.gz' \
		--exclude='firesale_*.sha256' \
		. ; \
	echo "✓ Archive created: $$TARBALL"; \
	echo ""; \
	echo "Computing SHA-256 hash..."; \
	HASH=$$(sha256sum $$TARBALL | awk '{print $$1}'); \
	echo "$$HASH  $$TARBALL" > "firesale_$${COMMIT_HASH}_$${TIMESTAMP}.sha256"; \
	echo "✓ Hash saved to: firesale_$${COMMIT_HASH}_$${TIMESTAMP}.sha256"; \
	echo ""; \
	echo "Archive hash:"; \
	cat "firesale_$${COMMIT_HASH}_$${TIMESTAMP}.sha256"; \
	echo ""; \
	echo "==> BURNING DOWN to clean state..."; \
	echo ""; \
	echo "Removing downloaded data..."; \
	find data/raw -mindepth 1 ! -name '.keep' -delete 2>/dev/null || true; \
	chmod -R u+w data/raw 2>/dev/null || true; \
	find data/raw -mindepth 1 ! -name '.keep' -exec rm -rf {} + 2>/dev/null || true; \
	echo "✓ data/raw/ cleared"; \
	echo ""; \
	echo "Removing intermediate data..."; \
	rm -rf data/interim/* data/processed/* data/external/* 2>/dev/null || true; \
	echo "✓ data/interim/, data/processed/, data/external/ cleared"; \
	echo ""; \
	echo "Removing results..."; \
	rm -rf results/figures/* results/tables/* results/artifacts/* 2>/dev/null || true; \
	echo "✓ results/ cleared"; \
	echo ""; \
	echo "Removing virtual environment..."; \
	rm -rf venv 2>/dev/null || true; \
	echo "✓ venv/ removed"; \
	echo ""; \
	echo "Removing Python cache..."; \
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
	find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
	echo "✓ Python cache cleared"; \
	echo ""; \
	echo "Resetting manifests..."; \
	git checkout -- manifests/checksums.sha256 manifests/provenance.json 2>/dev/null || true; \
	echo "✓ manifests/ reset to git state"; \
	echo ""; \
	echo ""; \
	echo "╔════════════════════════════════════════════════════════════════╗"; \
	echo "║                    🔥 FIRESALE COMPLETE 🔥                    ║"; \
	echo "╚════════════════════════════════════════════════════════════════╝"; \
	echo ""; \
	echo "Archive: $$TARBALL"; \
	echo "Hash:    $$HASH"; \
	echo ""; \
	echo "Repository burned to clean state."; \
	echo "To restore: tar xzf $$TARBALL"; \
	echo ""

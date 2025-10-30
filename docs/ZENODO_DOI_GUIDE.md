# Zenodo DOI Minting Guide

This guide walks through the process of minting a permanent DOI (Digital Object Identifier) for the `cosmo-sterile-audit` repository via Zenodo.

## Overview

Zenodo is a free, open-access repository that provides DOIs for research outputs, including software. Once connected, Zenodo automatically creates a new DOI for each GitHub release.

## Prerequisites

- GitHub repository with at least one release (✅ We have v1.0.0)
- Zenodo account (free at https://zenodo.org)
- Repository admin access

## Step-by-Step Workflow

### 1. Create Zenodo Account

1. Go to https://zenodo.org
2. Click **"Sign up"** or **"Log in"**
3. Select **"Log in with GitHub"** (recommended for integration)
4. Authorize Zenodo to access your GitHub account
5. Complete your Zenodo profile

### 2. Enable GitHub-Zenodo Integration

1. Log in to Zenodo: https://zenodo.org/login
2. Navigate to **GitHub settings**: https://zenodo.org/account/settings/github/
3. Click the **"Sync now"** button to fetch your repositories
4. Find `cosmo-sterile-audit` in the repository list
5. Toggle the **ON** switch next to the repository name
6. ✅ The integration is now active!

**What happens:**
- Zenodo creates a webhook on your GitHub repository
- Future releases will automatically trigger DOI creation
- Each release gets a unique DOI (versioned DOIs)
- The repository gets a "concept DOI" (always points to latest version)

### 3. Create a New Release (Already Done!)

We already have v1.0.0, but for future releases:

```bash
# Tag a new release
git tag -a v1.0.1 -m "Release v1.0.1: Bug fixes and improvements"
git push origin v1.0.1

# Create GitHub release
gh release create v1.0.1 \
  --title "Release v1.0.1" \
  --notes "Release notes here" \
  results/artifacts/firesale_*.tar.gz
```

**Important:** Zenodo only captures releases created AFTER enabling the integration.

### 4. Trigger DOI Creation for v1.0.0

Since v1.0.0 was created before Zenodo integration:

**Option A: Create a new release (recommended)**
```bash
# Create v1.0.1 pointing to same commit as v1.0.0
git tag -a v1.0.1 6c995dc -m "Release v1.0.1: Zenodo DOI integration"
git push origin v1.0.1

# Create GitHub release with same artifacts
gh release create v1.0.1 \
  --title "Release v1.0.1: Complete Sterile Audit Pipeline (Zenodo DOI)" \
  --notes "$(cat docs/RELEASE_NOTES_v1.0.1.md)" \
  results/artifacts/firesale_6c995dc2efcb_665edab35694.tar.gz \
  results/artifacts/firesale_NOTE.txt
```

**Option B: Use "Create a new upload" on Zenodo**
1. Go to https://zenodo.org/deposit/new
2. Upload the firesale archive manually
3. Fill in metadata (see Section 5 below)
4. Publish to get DOI

### 5. Fill in Zenodo Metadata

After the first release is archived, edit the metadata on Zenodo:

1. Go to https://zenodo.org/account/settings/github/
2. Click on your repository
3. Click the **release** that was archived
4. Click **"Edit"** to modify metadata

**Required Fields:**

- **Upload type:** Software
- **Title:** `Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline`
- **Authors:** Add your name(s) with ORCID (if available)
  - Format: `Last Name, First Name`
  - Click "Add ORCID" if you have one
- **Description:**
  ```
  A reproducible pipeline for auditing cosmological parameter constraints with
  strict data hygiene and provenance tracking. Includes MCMC convergence
  diagnostics, Period-Luminosity calibration, and deterministic archival with
  Merkle verification.

  Features:
  - HTTPS-only data fetch with SHA-256 verification
  - MCMC audit with ArviZ (R-hat, ESS)
  - Anchor preparation with astropy crossmatch
  - P-L fits (standard + conservative)
  - Epistemic uncertainty merge
  - Deterministic firesale archive system
  - Full GitHub Actions CI/CD
  ```
- **Version:** `1.0.0` (or appropriate version)
- **License:** MIT License (should auto-detect from GitHub)
- **Keywords:** Add relevant terms
  - `cosmology`
  - `reproducibility`
  - `provenance`
  - `MCMC`
  - `distance-ladder`
  - `Hubble-constant`
  - `sterile-pipeline`
  - `merkle-tree`
  - `data-integrity`

**Optional but Recommended:**

- **Related/alternate identifiers:**
  - GitHub repository URL: `https://github.com/abba-01/cosmo-sterile-audit`
  - Documentation URL: (if you have readthedocs or similar)

- **Contributors:** Add anyone who contributed
  - Select role: `Researcher`, `Data Curator`, `Software Developer`, etc.

- **References:** Add any papers this code relates to

- **Subjects:**
  - `Astronomy and Astrophysics`
  - `Computer and Information Science: Scientific computing`

- **Notes:**
  ```
  Archive SHA-256: 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6
  Merkle Root: 665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
  Commit: 6c995dc2efcbfe71becd50166da1efd7f98670c7
  ```

Click **"Save"** and then **"Publish"**

### 6. Obtain Your DOI

After publishing, Zenodo will generate:

1. **Version DOI:** Specific to this release (e.g., `10.5281/zenodo.1234567`)
2. **Concept DOI:** Always points to latest version (e.g., `10.5281/zenodo.1234566`)

The DOI badge will appear on the Zenodo page.

### 7. Add DOI Badge to Repository

Once you have the DOI:

1. Copy the Markdown badge from Zenodo
2. Add to README.md:

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

3. Commit and push:

```bash
git add README.md
git commit -m "Add Zenodo DOI badge"
git push origin master
```

### 8. Update CITATION.cff

Edit `CITATION.cff` with the DOI:

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
type: software
title: "Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline"
version: 1.0.0
doi: 10.5281/zenodo.XXXXXXX  # Add your DOI here
date-released: "2025-01-30"
url: "https://github.com/abba-01/cosmo-sterile-audit"
repository-code: "https://github.com/abba-01/cosmo-sterile-audit"
license: MIT
authors:
  - family-names: "Your Last Name"
    given-names: "Your First Name"
    orcid: "https://orcid.org/0000-0000-0000-0000"  # If you have one
keywords:
  - cosmology
  - reproducibility
  - provenance
  - MCMC
  - distance-ladder
  - Hubble-constant
abstract: >-
  A reproducible pipeline for auditing cosmological parameter constraints
  with strict data hygiene and provenance tracking.
```

Commit:
```bash
git add CITATION.cff
git commit -m "Update CITATION.cff with Zenodo DOI"
git push origin master
```

### 9. Update GitHub Release Notes

Edit the v1.0.0 (or v1.0.1) release on GitHub:

1. Go to https://github.com/abba-01/cosmo-sterile-audit/releases
2. Click **"Edit"** on the release
3. Add DOI information to the release notes:

```markdown
## Citation

📚 **DOI:** [`10.5281/zenodo.XXXXXXX`](https://doi.org/10.5281/zenodo.XXXXXXX)

If you use this software in your research, please cite:

\`\`\`bibtex
@software{cosmo_sterile_audit_2025,
  title = {Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline},
  author = {Your Name},
  year = {2025},
  version = {1.0.0},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/abba-01/cosmo-sterile-audit}
}
\`\`\`
```

4. Click **"Update release"**

### 10. Verify Everything Works

Final checklist:

- [ ] Zenodo integration enabled and synced
- [ ] Release visible on Zenodo: https://zenodo.org/search?q=cosmo-sterile-audit
- [ ] DOI resolves correctly: https://doi.org/10.5281/zenodo.XXXXXXX
- [ ] DOI badge added to README.md
- [ ] CITATION.cff updated with DOI
- [ ] GitHub release notes updated with citation
- [ ] Archive SHA-256 matches firesale_NOTE.txt

## Future Releases

For each new release:

1. Create and push tag:
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0: New features"
   git push origin v1.1.0
   ```

2. Create GitHub release with artifacts:
   ```bash
   make firesale-preflight
   make firesale
   gh release create v1.1.0 \
     --title "Release v1.1.0" \
     --notes "$(cat CHANGELOG.md)" \
     results/artifacts/firesale_*.tar.gz
   ```

3. Zenodo automatically:
   - Creates new version DOI
   - Updates concept DOI to point to latest
   - Archives the release artifacts

4. Update CITATION.cff version number and date

## Troubleshooting

**Problem:** Repository not showing on Zenodo

- **Solution:** Click "Sync now" on https://zenodo.org/account/settings/github/
- Make sure you're logged into the correct GitHub account

**Problem:** Release not archived

- **Solution:**
  - Check webhook: GitHub repo → Settings → Webhooks
  - Verify Zenodo toggle is ON
  - Try creating a new test release

**Problem:** Metadata looks wrong

- **Solution:** Edit directly on Zenodo, changes propagate immediately

**Problem:** Want to delete/hide a release

- **Solution:** Contact Zenodo support - DOIs are permanent, but records can be marked as "hidden"

## Resources

- Zenodo GitHub integration: https://docs.zenodo.org/help/features/github/
- Zenodo FAQs: https://help.zenodo.org
- CITATION.cff format: https://citation-file-format.github.io
- ORCID registration: https://orcid.org/register

## Example Citation

Once you have your DOI, others can cite your work:

**APA:**
```
Your Name. (2025). Cosmo Sterile Audit: Reproducible Cosmological Analysis
Pipeline (Version 1.0.0) [Computer software].
https://doi.org/10.5281/zenodo.XXXXXXX
```

**BibTeX:**
```bibtex
@software{cosmo_sterile_audit_2025,
  title = {Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline},
  author = {Your Name},
  year = {2025},
  version = {1.0.0},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/abba-01/cosmo-sterile-audit}
}
```

**Chicago:**
```
Your Name. 2025. Cosmo Sterile Audit: Reproducible Cosmological Analysis
Pipeline. Version 1.0.0. https://doi.org/10.5281/zenodo.XXXXXXX.
```

---

**Questions?** Open an issue on GitHub or consult Zenodo's help documentation.

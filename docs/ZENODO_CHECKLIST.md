# Zenodo DOI Minting - Quick Checklist

Use this checklist when minting a DOI for a new release.

## Pre-Release Checklist

- [ ] All code committed and pushed to GitHub
- [ ] All tests passing (CI/CD green)
- [ ] Version number updated in relevant files
- [ ] CHANGELOG.md updated with release notes
- [ ] Firesale archive created and verified

## Zenodo Setup (One-Time)

- [ ] Create Zenodo account at https://zenodo.org
- [ ] Connect GitHub account to Zenodo
- [ ] Enable repository at https://zenodo.org/account/settings/github/
- [ ] Click "Sync now" to refresh repository list
- [ ] Toggle ON switch for `cosmo-sterile-audit`

## Release Creation

- [ ] Create annotated git tag
  ```bash
  git tag -a v1.X.X -m "Release v1.X.X: Description"
  git push origin v1.X.X
  ```

- [ ] Create firesale archive
  ```bash
  make firesale-preflight
  make firesale
  ```

- [ ] Create GitHub release
  ```bash
  gh release create v1.X.X \
    --title "Release v1.X.X: Title" \
    --notes "$(cat docs/RELEASE_NOTES_v1.X.X.md)" \
    results/artifacts/firesale_*.tar.gz \
    results/artifacts/firesale_NOTE.txt
  ```

- [ ] Verify release appears on GitHub: https://github.com/abba-01/cosmo-sterile-audit/releases

## Zenodo Metadata

- [ ] Wait for Zenodo webhook to trigger (check https://zenodo.org/deposit)
- [ ] Edit Zenodo metadata:
  - [ ] Title: `Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline`
  - [ ] Authors: Add name(s) with ORCID
  - [ ] Description: Copy from template in ZENODO_DOI_GUIDE.md
  - [ ] Version: Match GitHub release tag
  - [ ] License: MIT License
  - [ ] Keywords: cosmology, reproducibility, provenance, MCMC, distance-ladder, etc.
  - [ ] Related identifiers: Add GitHub URL
  - [ ] Notes: Add archive SHA-256, Merkle root, commit hash
- [ ] Click "Publish" to finalize DOI

## Repository Updates

- [ ] Copy DOI from Zenodo (format: `10.5281/zenodo.XXXXXXX`)

- [ ] Add DOI badge to README.md
  ```markdown
  [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
  ```

- [ ] Update CITATION.cff
  ```yaml
  doi: 10.5281/zenodo.XXXXXXX
  version: 1.X.X
  date-released: "YYYY-MM-DD"
  ```

- [ ] Update GitHub release notes with citation
  - Add DOI
  - Add BibTeX citation block
  - Add APA citation

- [ ] Commit and push changes
  ```bash
  git add README.md CITATION.cff
  git commit -m "Add Zenodo DOI for v1.X.X"
  git push origin master
  ```

## Verification

- [ ] DOI resolves: https://doi.org/10.5281/zenodo.XXXXXXX
- [ ] Zenodo page displays correctly
- [ ] Badge appears in README on GitHub
- [ ] CITATION.cff has correct DOI
- [ ] GitHub release has citation information
- [ ] Archive SHA-256 matches firesale_NOTE.txt

## Archive Verification

- [ ] Download archive from Zenodo
- [ ] Verify SHA-256 checksum
  ```bash
  sha256sum -c <<< "HASH  filename.tar.gz"
  ```
- [ ] Extract and verify Merkle root
  ```bash
  tar -xzf archive.tar.gz
  cd extracted/
  python3 scripts/firesale_hash_tree.py
  # Should match Merkle root in firesale_NOTE.txt
  ```

## Announcement (Optional)

- [ ] Update project website/documentation
- [ ] Announce on social media/mailing lists
- [ ] Add to relevant software registries
- [ ] Update lab/institution records

## Notes

**Concept DOI vs Version DOI:**
- Concept DOI: Always points to latest version (use in general citations)
- Version DOI: Specific to one release (use when exact version matters)

**Important Files:**
- `CITATION.cff` - Machine-readable citation
- `docs/ZENODO_DOI_GUIDE.md` - Full detailed guide
- `firesale_NOTE.txt` - Archive verification metadata

**Contact:**
- Zenodo support: info@zenodo.org
- GitHub issues: https://github.com/abba-01/cosmo-sterile-audit/issues

# Next Steps: Minting Your Zenodo DOI

## What We Just Did

✅ Created release v1.0.0 with deterministic firesale archive
✅ Tagged commit `6c995dc` with annotated tag
✅ Pushed release to GitHub with artifacts
✅ Created comprehensive Zenodo documentation
✅ Added DOI placeholder to README

## What YOU Need to Do Now

Follow these steps to mint your DOI on Zenodo:

### Step 1: Set Up Zenodo (5 minutes)

1. **Go to Zenodo:** https://zenodo.org
2. **Click "Log in with GitHub"** (top right)
3. **Authorize Zenodo** to access your GitHub account
4. **Complete your profile** (optional but recommended)

### Step 2: Enable Repository Integration (2 minutes)

1. **Navigate to GitHub settings on Zenodo:**
   https://zenodo.org/account/settings/github/

2. **Click "Sync now"** button to refresh your repository list

3. **Find `cosmo-sterile-audit`** in the list

4. **Toggle the ON switch** next to the repository name

   ✅ You should see a green checkmark when enabled

### Step 3: Create a New Release to Trigger Zenodo (5 minutes)

Since v1.0.0 was created BEFORE Zenodo integration, create v1.0.1:

```bash
cd /got/cosmo-sterile-audit

# Tag the same commit as v1.0.0 with new version
git tag -a v1.0.1 6c995dc -m "Release v1.0.1: Zenodo DOI integration"
git push origin v1.0.1

# Create GitHub release (reuse same firesale archive)
gh release create v1.0.1 \
  --title "Release v1.0.1: Complete Sterile Audit Pipeline (Zenodo DOI)" \
  --notes "This release is identical to v1.0.0 but includes Zenodo DOI integration.

## Verification Metadata

- **Commit:** 6c995dc2efcbfe71becd50166da1efd7f98670c7
- **Merkle Root:** 665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
- **Archive SHA-256:** 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6

For complete documentation, see [ZENODO_DOI_GUIDE.md](docs/ZENODO_DOI_GUIDE.md)" \
  results/artifacts/firesale_6c995dc2efcb_665edab35694.tar.gz \
  results/artifacts/firesale_NOTE.txt
```

### Step 4: Wait for Zenodo to Archive (1-2 minutes)

1. Check your email - Zenodo sends a notification
2. Or go to: https://zenodo.org/deposit
3. You should see a new upload for `cosmo-sterile-audit v1.0.1`

### Step 5: Edit Metadata on Zenodo (10 minutes)

1. **Click on the deposit** for your repository
2. **Click "Edit"** to modify metadata
3. **Fill in the required fields:**

   - **Upload type:** Software
   - **Title:** `Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline`
   - **Authors:** Add your name
     - Format: `Last Name, First Name`
     - Add ORCID if you have one: https://orcid.org/register

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

   - **Version:** `1.0.1`
   - **License:** MIT License (should auto-detect)

   - **Keywords:** (click "Add keyword" for each)
     - cosmology
     - reproducibility
     - provenance
     - MCMC
     - distance-ladder
     - Hubble-constant
     - sterile-pipeline
     - merkle-tree
     - data-integrity

   - **Related identifiers:**
     - Type: "is supplemented by this upload"
     - Identifier: `https://github.com/abba-01/cosmo-sterile-audit`

   - **Notes:**
     ```
     Archive SHA-256: 5cc50022fed3846dd16f706763e5c0b1bf4275d5cad9bd7d71c7d2ac3ff95dd6
     Merkle Root: 665edab35694d529e838bc4c9c7fe502192ccda3383f83d1a0110279d4ed8c72
     Commit: 6c995dc2efcbfe71becd50166da1efd7f98670c7
     ```

4. **Click "Save"** (bottom of page)
5. **Click "Publish"** (this finalizes the DOI - cannot be undone!)

### Step 6: Get Your DOI (1 minute)

After publishing:

1. **Copy the DOI** from the Zenodo page (format: `10.5281/zenodo.XXXXXXX`)
2. **Copy the badge code** (there's a "DOI" button that gives you markdown)

You'll get TWO DOIs:
- **Version DOI:** Specific to v1.0.1 (e.g., `10.5281/zenodo.1234567`)
- **Concept DOI:** Always points to latest (e.g., `10.5281/zenodo.1234566`)

### Step 7: Update Repository with DOI (5 minutes)

Replace `XXXXXXX` with your actual DOI number:

```bash
cd /got/cosmo-sterile-audit

# 1. Update README.md
# Replace the placeholder line:
#   DOI: 10.5281/zenodo.XXXXXXX (to be added after Zenodo integration)
# With:
#   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

# 2. Update CITATION.cff
# Add this line after "version: 1.0.0":
#   doi: 10.5281/zenodo.XXXXXXX

# 3. Commit changes
git add README.md CITATION.cff
git commit -m "Add Zenodo DOI badge and citation"
git push origin master
```

### Step 8: Verify Everything (5 minutes)

Check all these:

- [ ] DOI resolves: https://doi.org/10.5281/zenodo.XXXXXXX
- [ ] Zenodo page displays correctly
- [ ] Badge appears in README on GitHub: https://github.com/abba-01/cosmo-sterile-audit
- [ ] CITATION.cff has correct DOI
- [ ] GitHub release v1.0.1 visible: https://github.com/abba-01/cosmo-sterile-audit/releases

## You're Done! 🎉

Your repository now has:
- ✅ Permanent DOI from Zenodo
- ✅ Archived on Zenodo's servers (long-term preservation)
- ✅ Citable in academic papers
- ✅ Automatic archiving for future releases

## For Future Releases

Just create a new GitHub release and Zenodo will automatically:
1. Archive it
2. Create a new version DOI
3. Update the concept DOI to point to the latest

No additional setup needed!

## Resources

- **Full Guide:** `docs/ZENODO_DOI_GUIDE.md`
- **Quick Checklist:** `docs/ZENODO_CHECKLIST.md`
- **Zenodo Help:** https://help.zenodo.org
- **GitHub Releases:** https://github.com/abba-01/cosmo-sterile-audit/releases

## Questions?

If you run into issues:
1. Check `docs/ZENODO_DOI_GUIDE.md` troubleshooting section
2. Contact Zenodo support: info@zenodo.org
3. Open a GitHub issue: https://github.com/abba-01/cosmo-sterile-audit/issues

---

**Total Time:** ~30 minutes
**Difficulty:** Easy
**Cost:** Free forever

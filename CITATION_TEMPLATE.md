# CITATION.cff Template Instructions

The `CITATION.cff` file has been updated with comprehensive metadata. You need to replace the placeholder values with your actual information.

## Required Updates

### 1. Author Information (Line 18-23)

**Current placeholders:**
```yaml
authors:
  - family-names: "Your-Last-Name"
    given-names: "Your-First-Name"
    email: "your.email@example.com"
    affiliation: "Your Institution"
    orcid: "https://orcid.org/0000-0000-0000-0000"
```

**Replace with your actual information:**
- `family-names`: Your last name (e.g., "Smith")
- `given-names`: Your first name (and middle name if desired) (e.g., "Jane Marie")
- `email`: Your email address (e.g., "jane.smith@university.edu")
- `affiliation`: Your institution (e.g., "University of California, Berkeley")
- `orcid`: Your ORCID ID if you have one, or remove this line if not
  - Get an ORCID: https://orcid.org/register (free and takes 2 minutes)
  - Format: `https://orcid.org/0000-0001-2345-6789`

### 2. Zenodo DOI (Line 10)

**Current placeholder:**
```yaml
doi: 10.5281/zenodo.XXXXXXX
```

**Replace with your actual DOI after Zenodo minting:**
- Format: `10.5281/zenodo.1234567`
- You'll get this from Zenodo after publishing

## How to Update

### Option 1: Edit Directly on GitHub

1. Go to: https://github.com/abba-01/cosmo-sterile-audit/edit/master/CITATION.cff
2. Edit lines 19-23 with your information
3. Edit line 10 with your DOI (after Zenodo minting)
4. Commit changes with message: "Update CITATION.cff with author info and DOI"

### Option 2: Edit Locally

```bash
cd /got/cosmo-sterile-audit

# Edit CITATION.cff in your text editor
nano CITATION.cff
# or
vim CITATION.cff

# Commit and push
git add CITATION.cff
git commit -m "Update CITATION.cff with author info and DOI"
git push origin master
```

## What's Already Included

The CITATION.cff file now includes:

✅ **Complete Metadata:**
- Software title and abstract
- Version 1.0.1
- Release date (2025-01-30)
- Repository URLs
- License (MIT)
- Comprehensive keywords (14 terms)

✅ **References:**
- Planck 2018 results (doi: 10.1051/0004-6361/201833910)
- SH0ES/Riess et al. 2022 (doi: 10.3847/2041-8213/ac5c5b)
- Gaia EDR3 (doi: 10.1051/0004-6361/202039657)

✅ **CFF Format:**
- Version 1.2.0 specification
- GitHub-compatible
- Zenodo-compatible
- Machine-readable

## How GitHub Uses CITATION.cff

Once updated, GitHub will:
1. Show a "Cite this repository" button on your repo page
2. Generate APA and BibTeX citations automatically
3. Display citation information in the sidebar

## Example Citations

After filling in your information, the file will generate citations like:

**APA:**
```
Your Name. (2025). Cosmo Sterile Audit: Reproducible Cosmological Analysis
Pipeline (Version 1.0.1) [Computer software].
https://doi.org/10.5281/zenodo.XXXXXXX
```

**BibTeX:**
```bibtex
@software{Your_Name_2025,
  author = {Your Name},
  title = {Cosmo Sterile Audit: Reproducible Cosmological Analysis Pipeline},
  year = {2025},
  version = {1.0.1},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/abba-01/cosmo-sterile-audit}
}
```

## Validation

Validate your CITATION.cff file:
- Online validator: https://citation-file-format.github.io/cff-initializer-javascript/
- GitHub will also validate when you commit

## Resources

- CFF format guide: https://citation-file-format.github.io
- GitHub citation docs: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files
- ORCID registration: https://orcid.org/register

---

**Status:**
- [ ] Author information updated
- [ ] ORCID added (optional)
- [ ] Zenodo DOI added (after minting)
- [ ] Changes committed and pushed

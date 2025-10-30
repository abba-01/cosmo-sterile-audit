#!/usr/bin/env python3
"""
Prepare anchor data: crossmatch Gaia+SH0ES, apply extinction, ZP corrections.
Crossmatch tolerance: 0.1 arcsec
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u


def get_repo_root():
    """Get repository root directory."""
    return Path(__file__).parent.parent


def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_script_version_hash():
    """Get hash of this script for provenance tracking."""
    return compute_sha256(__file__)


def find_data_files(repo_root):
    """Find Gaia and SH0ES data files in data/raw."""
    raw_dir = repo_root / "data" / "raw"

    gaia_files = []
    shoes_files = []

    # Search all hash-named directories
    for hash_dir in raw_dir.iterdir():
        if hash_dir.is_dir() and hash_dir.name != '.keep':
            # Look for Gaia files
            for file in hash_dir.glob("gaia*.csv"):
                gaia_files.append(file)

            # Look for SH0ES/VizieR files
            for file in hash_dir.glob("*.csv"):
                if "apj" in file.name.lower() or "shoes" in file.name.lower():
                    shoes_files.append(file)

    return sorted(gaia_files), sorted(shoes_files)


def load_gaia_data(gaia_file):
    """
    Load Gaia Cepheid data.
    Expected columns: source_id, ra, dec, parallax, parallax_error, phot_g_mean_mag, bp_rp
    """
    try:
        df = pd.read_csv(gaia_file)

        required_cols = ['source_id', 'ra', 'dec', 'parallax', 'parallax_error']
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            print(f"WARNING: Gaia file missing columns: {missing}")
            print(f"Available columns: {list(df.columns)}")
            # Try alternate column names
            if 'ra' not in df.columns and 'RA' in df.columns:
                df.rename(columns={'RA': 'ra', 'DEC': 'dec'}, inplace=True)

        return df

    except Exception as e:
        print(f"ERROR: Failed to load Gaia file {gaia_file.name}: {e}", file=sys.stderr)
        return None


def load_shoes_data(shoes_file):
    """
    Load SH0ES distance ladder data.
    Expected columns might include: Name, RA, DEC, Period, E(B-V), distance_modulus, etc.
    """
    try:
        df = pd.read_csv(shoes_file)
        print(f"  SH0ES columns: {list(df.columns)}")
        return df

    except Exception as e:
        print(f"ERROR: Failed to load SH0ES file {shoes_file.name}: {e}", file=sys.stderr)
        return None


def crossmatch_catalogs(gaia_df, shoes_df, tolerance_arcsec=0.1):
    """
    Crossmatch Gaia and SH0ES catalogs by sky coordinates.

    Args:
        gaia_df: Gaia DataFrame with ra, dec columns
        shoes_df: SH0ES DataFrame with ra, dec columns
        tolerance_arcsec: Match tolerance in arcseconds

    Returns:
        Matched DataFrame with combined data
    """
    print(f"\n→ Crossmatching catalogs (tolerance: {tolerance_arcsec} arcsec)...")

    # Create SkyCoord objects
    gaia_coords = SkyCoord(
        ra=gaia_df['ra'].values * u.deg,
        dec=gaia_df['dec'].values * u.deg,
        frame='icrs'
    )

    # Detect RA/DEC column names in SH0ES (might be RA/DEC or ra/dec)
    ra_col = 'RA' if 'RA' in shoes_df.columns else 'ra'
    dec_col = 'DEC' if 'DEC' in shoes_df.columns else 'dec'

    shoes_coords = SkyCoord(
        ra=shoes_df[ra_col].values * u.deg,
        dec=shoes_df[dec_col].values * u.deg,
        frame='icrs'
    )

    # Perform crossmatch
    idx, sep2d, _ = shoes_coords.match_to_catalog_sky(gaia_coords)

    # Apply tolerance
    tolerance = tolerance_arcsec * u.arcsec
    matched_mask = sep2d < tolerance

    n_matched = matched_mask.sum()
    n_total = len(shoes_df)

    print(f"  Matched: {n_matched}/{n_total} sources ({100*n_matched/n_total:.1f}%)")
    print(f"  Median separation: {np.median(sep2d[matched_mask].arcsec):.3f} arcsec")

    # Create matched DataFrame
    matched_shoes = shoes_df[matched_mask].copy()
    matched_gaia_idx = idx[matched_mask]
    matched_gaia = gaia_df.iloc[matched_gaia_idx].copy()

    # Combine (prefix columns to avoid conflicts)
    matched_shoes = matched_shoes.add_prefix('shoes_')
    matched_gaia = matched_gaia.add_prefix('gaia_')

    matched = pd.concat([matched_gaia.reset_index(drop=True),
                        matched_shoes.reset_index(drop=True)], axis=1)

    # Add separation column
    matched['sep_arcsec'] = sep2d[matched_mask].arcsec

    return matched


def apply_gaia_zeropoint_correction(parallax, parallax_error):
    """
    Apply Gaia EDR3 parallax zero-point correction.
    Using Lindegren et al. 2021 (A&A 649, A4) recommended offset.

    For most sources: ZP offset ≈ -0.017 mas (simplified)
    Full correction depends on magnitude, color, position - using simplified version.
    """
    ZP_OFFSET = -0.017  # mas (milliarcseconds)

    parallax_corrected = parallax - ZP_OFFSET
    # Uncertainty unchanged by constant offset

    return parallax_corrected, parallax_error


def compute_distances(parallax_corrected, parallax_error):
    """
    Compute distances from parallax.

    Distance (pc) = 1000 / parallax (mas)
    Propagate uncertainties assuming Gaussian (simplified).
    """
    # Avoid division by zero or negative parallaxes
    valid = (parallax_corrected > 0) & (parallax_error > 0)

    distance_pc = np.full(len(parallax_corrected), np.nan)
    distance_err = np.full(len(parallax_corrected), np.nan)

    distance_pc[valid] = 1000.0 / parallax_corrected[valid]

    # Error propagation: σ_d = d² × σ_π / π
    distance_err[valid] = (
        distance_pc[valid]**2 * parallax_error[valid] / parallax_corrected[valid]
    )

    return distance_pc, distance_err


def apply_extinction_correction(mag_obs, ebv, R_V=3.1):
    """
    Apply Milky Way extinction correction.

    A_V = R_V × E(B-V)
    M_corrected = M_obs - A_V

    Args:
        mag_obs: Observed magnitude
        ebv: E(B-V) reddening
        R_V: Ratio of total to selective extinction (default 3.1)

    Returns:
        Corrected magnitude, extinction A_V
    """
    A_V = R_V * ebv
    mag_corrected = mag_obs - A_V

    return mag_corrected, A_V


def update_provenance(repo_root, n_matched, n_total):
    """Update provenance.json with anchor prep metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["anchor_prep"] = {
        "script": "scripts/20_anchor_prep.py",
        "script_version_hash": get_script_version_hash(),
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "n_matched": n_matched,
        "n_total_shoes": n_total,
        "match_fraction": n_matched / n_total if n_total > 0 else 0.0
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def prepare_anchors():
    """Prepare anchor Cepheids for Period-Luminosity fit."""
    print("==> Preparing Cepheid anchor data...")

    repo_root = get_repo_root()

    # Find data files
    print("\n→ Searching for data files...")
    gaia_files, shoes_files = find_data_files(repo_root)

    if not gaia_files:
        print("ERROR: No Gaia files found in data/raw/", file=sys.stderr)
        return 1

    if not shoes_files:
        print("ERROR: No SH0ES files found in data/raw/", file=sys.stderr)
        return 1

    print(f"  Found {len(gaia_files)} Gaia file(s): {[f.name for f in gaia_files]}")
    print(f"  Found {len(shoes_files)} SH0ES file(s): {[f.name for f in shoes_files]}")

    # Load data (use first file if multiple)
    print("\n→ Loading Gaia data...")
    gaia_df = load_gaia_data(gaia_files[0])
    if gaia_df is None:
        return 1
    print(f"  Loaded {len(gaia_df)} Gaia sources")

    print("\n→ Loading SH0ES data...")
    shoes_df = load_shoes_data(shoes_files[0])
    if shoes_df is None:
        return 1
    print(f"  Loaded {len(shoes_df)} SH0ES sources")

    # Crossmatch
    matched = crossmatch_catalogs(gaia_df, shoes_df, tolerance_arcsec=0.1)

    if len(matched) == 0:
        print("ERROR: No matches found between Gaia and SH0ES catalogs", file=sys.stderr)
        return 1

    # Apply Gaia zero-point correction
    print("\n→ Applying Gaia parallax zero-point correction...")
    parallax_corrected, parallax_error = apply_gaia_zeropoint_correction(
        matched['gaia_parallax'].values,
        matched['gaia_parallax_error'].values
    )
    matched['parallax_corrected'] = parallax_corrected
    matched['parallax_error_corrected'] = parallax_error
    print(f"  Applied ZP offset: -0.017 mas")

    # Compute distances
    print("\n→ Computing distances from parallax...")
    distance_pc, distance_err = compute_distances(parallax_corrected, parallax_error)
    matched['distance_pc'] = distance_pc
    matched['distance_err_pc'] = distance_err

    n_valid_distances = np.sum(~np.isnan(distance_pc))
    print(f"  Computed {n_valid_distances}/{len(matched)} valid distances")
    print(f"  Distance range: {np.nanmin(distance_pc):.1f} - {np.nanmax(distance_pc):.1f} pc")

    # Apply extinction correction (if E(B-V) column exists)
    ebv_col = None
    for col in matched.columns:
        if 'ebv' in col.lower() or 'e(b-v)' in col.lower():
            ebv_col = col
            break

    if ebv_col:
        print(f"\n→ Applying extinction correction using {ebv_col}...")

        # Use Gaia G magnitude if available
        mag_col = 'gaia_phot_g_mean_mag'
        if mag_col in matched.columns:
            mag_corrected, A_V = apply_extinction_correction(
                matched[mag_col].values,
                matched[ebv_col].values
            )
            matched['mag_corrected'] = mag_corrected
            matched['A_V'] = A_V
            print(f"  Applied A_V correction (R_V=3.1)")
            print(f"  A_V range: {np.nanmin(A_V):.3f} - {np.nanmax(A_V):.3f} mag")
    else:
        print(f"\n  WARNING: No E(B-V) column found, skipping extinction correction")

    # Save to interim directory
    print("\n→ Saving prepared anchor data...")
    interim_dir = repo_root / "data" / "interim"
    interim_dir.mkdir(parents=True, exist_ok=True)

    output_file = interim_dir / "anchor_mw_prepared.parquet"
    matched.to_parquet(output_file, index=False)
    print(f"  ✓ Saved to: {output_file}")
    print(f"  ✓ Columns: {list(matched.columns)}")
    print(f"  ✓ Total matched sources: {len(matched)}")

    # Update provenance
    update_provenance(repo_root, len(matched), len(shoes_df))

    print("\n✓ Anchor preparation complete")
    return 0


if __name__ == "__main__":
    sys.exit(prepare_anchors())

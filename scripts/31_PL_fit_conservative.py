#!/usr/bin/env python3
"""
Conservative Period-Luminosity fit using pairwise distance calculus.
Uses 1.5x uncertainty inflation for conservative estimates.
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


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


def load_prepared_anchors(repo_root):
    """Load prepared anchor data from interim directory."""
    interim_dir = repo_root / "data" / "interim"
    anchor_file = interim_dir / "anchor_mw_prepared.parquet"

    if not anchor_file.exists():
        print(f"ERROR: Anchor file not found: {anchor_file}", file=sys.stderr)
        return None

    try:
        return pd.read_parquet(anchor_file)
    except Exception as e:
        print(f"ERROR: Failed to load anchors: {e}", file=sys.stderr)
        return None


def load_standard_fit(repo_root):
    """Load standard fit results for comparison."""
    results_dir = repo_root / "results" / "tables"
    params_file = results_dir / "pl_standard_params.json"

    if not params_file.exists():
        print("WARNING: Standard fit not found, run 30_PL_fit_standard.py first")
        return None

    try:
        with open(params_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to load standard fit: {e}")
        return None


def pl_model(log_period, alpha, beta):
    """Period-Luminosity model: M = alpha * log10(P) + beta"""
    return alpha * log_period + beta


def fit_conservative(log_period, abs_mag, abs_mag_err, inflation_factor=1.5):
    """
    Conservative fit with inflated uncertainties.

    Args:
        inflation_factor: Multiply uncertainties by this factor (default 1.5)
    """
    # Inflate uncertainties
    conservative_err = abs_mag_err * inflation_factor

    try:
        popt, pcov = curve_fit(
            pl_model,
            log_period,
            abs_mag,
            sigma=conservative_err,
            absolute_sigma=True
        )

        alpha, beta = popt
        alpha_err, beta_err = np.sqrt(np.diag(pcov))

        # Compute residuals
        predicted = pl_model(log_period, alpha, beta)
        residuals = abs_mag - predicted
        rms = np.sqrt(np.mean(residuals**2))

        return {
            'alpha': float(alpha),
            'beta': float(beta),
            'alpha_err': float(alpha_err),
            'beta_err': float(beta_err),
            'covariance': pcov.tolist(),
            'rms': float(rms),
            'inflation_factor': inflation_factor,
            'predicted': predicted
        }

    except Exception as e:
        print(f"ERROR: Conservative fit failed: {e}", file=sys.stderr)
        return None


def compare_fits(standard, conservative):
    """Compare standard and conservative fit results."""
    if standard is None:
        return {}

    discrepancy_alpha = abs(conservative['alpha'] - standard['alpha'])
    discrepancy_beta = abs(conservative['beta'] - standard['beta'])

    # Check if discrepancy > 2σ
    sigma_threshold = 2.0
    alpha_tension = discrepancy_alpha / np.sqrt(standard['alpha_err']**2 + conservative['alpha_err']**2)
    beta_tension = discrepancy_beta / np.sqrt(standard['beta_err']**2 + conservative['beta_err']**2)

    return {
        'discrepancy_alpha': float(discrepancy_alpha),
        'discrepancy_beta': float(discrepancy_beta),
        'alpha_tension_sigma': float(alpha_tension),
        'beta_tension_sigma': float(beta_tension),
        'flag_alpha': alpha_tension > sigma_threshold,
        'flag_beta': beta_tension > sigma_threshold
    }


def plot_comparison(standard_fit, conservative_fit, output_dir):
    """Plot standard vs conservative fits."""
    if standard_fit is None:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Dummy data for visualization
    log_p_range = np.linspace(0.5, 2.0, 100)

    # Standard fit
    standard_line = pl_model(log_p_range, standard_fit['alpha'], standard_fit['beta'])
    ax.plot(log_p_range, standard_line, 'r-', linewidth=2, label='Standard Fit', alpha=0.8)

    # Conservative fit
    conservative_line = pl_model(log_p_range, conservative_fit['alpha'], conservative_fit['beta'])
    ax.plot(log_p_range, conservative_line, 'b--', linewidth=2, label='Conservative Fit', alpha=0.8)

    ax.set_xlabel('log₁₀(Period [days])', fontsize=12)
    ax.set_ylabel('Absolute Magnitude', fontsize=12)
    ax.set_title('P-L Fit Comparison: Standard vs Conservative', fontsize=14)
    ax.legend()
    ax.grid(alpha=0.3)
    ax.invert_yaxis()

    plt.tight_layout()
    output_file = output_dir / 'pl_conservative_comparison.png'
    plt.savefig(output_file, dpi=150)
    plt.close()

    print(f"  ✓ Saved: {output_file}")


def update_provenance(repo_root, fit_result, comparison, n_sources):
    """Update provenance.json with conservative fit metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["pl_fit_conservative"] = {
        "script": "scripts/31_PL_fit_conservative.py",
        "script_version_hash": get_script_version_hash(),
        "fitted_at": datetime.utcnow().isoformat() + "Z",
        "n_sources": n_sources,
        "alpha": fit_result['alpha'],
        "beta": fit_result['beta'],
        "inflation_factor": fit_result['inflation_factor'],
        "comparison": comparison
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def fit_pl_conservative():
    """Fit conservative P-L relation using distance ratios."""
    print("==> Fitting conservative Period-Luminosity relation...")

    repo_root = get_repo_root()

    # Load prepared anchors
    print("\n→ Loading prepared anchor data...")
    anchors = load_prepared_anchors(repo_root)
    if anchors is None:
        return 1

    print(f"  Loaded {len(anchors)} anchor sources")

    # Find period column
    period_col = None
    for col in anchors.columns:
        if 'period' in col.lower():
            period_col = col
            break

    if period_col is None:
        print("ERROR: No period column found", file=sys.stderr)
        return 1

    # Find magnitude and distance
    mag_col = 'mag_corrected' if 'mag_corrected' in anchors.columns else 'gaia_phot_g_mean_mag'

    if 'distance_pc' not in anchors.columns:
        print("ERROR: No distance_pc column", file=sys.stderr)
        return 1

    # Filter valid data
    valid = (
        ~anchors[period_col].isna() &
        ~anchors['distance_pc'].isna() &
        (anchors['distance_pc'] > 0) &
        ~anchors[mag_col].isna()
    )

    print(f"  Valid: {valid.sum()}/{len(anchors)}")

    if valid.sum() < 3:
        print("ERROR: Insufficient valid sources", file=sys.stderr)
        return 1

    # Extract data
    period = anchors.loc[valid, period_col].values
    distance_pc = anchors.loc[valid, 'distance_pc'].values
    apparent_mag = anchors.loc[valid, mag_col].values

    # Compute absolute magnitude
    distance_modulus = 5 * np.log10(distance_pc / 10.0)
    abs_mag = apparent_mag - distance_modulus
    log_period = np.log10(period)

    # Conservative uncertainties (1.5x inflation)
    if 'distance_err_pc' in anchors.columns:
        distance_err = anchors.loc[valid, 'distance_err_pc'].values
        abs_mag_err = 5 / (distance_pc * np.log(10)) * distance_err
    else:
        abs_mag_err = np.full(len(abs_mag), 0.1)

    # Conservative fit
    print(f"\n→ Fitting with 1.5x uncertainty inflation...")
    conservative_fit = fit_conservative(log_period, abs_mag, abs_mag_err, inflation_factor=1.5)

    if conservative_fit is None:
        return 1

    print(f"  alpha = {conservative_fit['alpha']:.4f} ± {conservative_fit['alpha_err']:.4f}")
    print(f"  beta  = {conservative_fit['beta']:.4f} ± {conservative_fit['beta_err']:.4f}")

    # Load standard fit for comparison
    print(f"\n→ Comparing with standard fit...")
    standard_fit = load_standard_fit(repo_root)
    comparison = compare_fits(standard_fit, conservative_fit)

    if comparison:
        print(f"  Δalpha = {comparison['discrepancy_alpha']:.4f} ({comparison['alpha_tension_sigma']:.2f}σ)")
        print(f"  Δbeta  = {comparison['discrepancy_beta']:.4f} ({comparison['beta_tension_sigma']:.2f}σ)")
        if comparison['flag_alpha'] or comparison['flag_beta']:
            print(f"  WARNING: Discrepancy > 2σ detected")

    # Save results
    print("\n→ Saving results...")
    results_dir = repo_root / "results" / "tables"
    results_dir.mkdir(parents=True, exist_ok=True)

    params_file = results_dir / "pl_conservative_params.json"
    with open(params_file, 'w') as f:
        json.dump({
            **conservative_fit,
            'comparison': comparison,
            'n_sources': int(valid.sum())
        }, f, indent=2)
    print(f"  ✓ Saved: {params_file}")

    # Generate comparison plot
    print("\n→ Generating comparison plot...")
    figures_dir = repo_root / "results" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_comparison(standard_fit, conservative_fit, figures_dir)

    # Update provenance
    update_provenance(repo_root, conservative_fit, comparison, int(valid.sum()))

    print("\n✓ Conservative P-L fit complete")
    return 0


if __name__ == "__main__":
    sys.exit(fit_pl_conservative())

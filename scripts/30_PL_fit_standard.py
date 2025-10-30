#!/usr/bin/env python3
"""
Standard Period-Luminosity relation fit using weighted least squares.
Model: M = alpha * log10(P) + beta
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
        print("       Run scripts/20_anchor_prep.py first", file=sys.stderr)
        return None

    try:
        df = pd.read_parquet(anchor_file)
        return df
    except Exception as e:
        print(f"ERROR: Failed to load anchors: {e}", file=sys.stderr)
        return None


def pl_model(log_period, alpha, beta):
    """Period-Luminosity model: M = alpha * log10(P) + beta"""
    return alpha * log_period + beta


def fit_pl_relation(log_period, abs_mag, abs_mag_err):
    """
    Fit P-L relation using weighted least squares.

    Args:
        log_period: log10 of period in days
        abs_mag: Absolute magnitude
        abs_mag_err: Uncertainty in absolute magnitude

    Returns:
        dict with alpha, beta, errors, covariance, residuals
    """
    # Use inverse variance weighting
    weights = 1.0 / (abs_mag_err**2)

    # Fit using scipy curve_fit
    try:
        popt, pcov = curve_fit(
            pl_model,
            log_period,
            abs_mag,
            sigma=abs_mag_err,
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
            'residuals': residuals,
            'predicted': predicted
        }

    except Exception as e:
        print(f"ERROR: Fit failed: {e}", file=sys.stderr)
        return None


def bootstrap_uncertainties(log_period, abs_mag, abs_mag_err, n_bootstrap=1000):
    """
    Estimate uncertainties using bootstrap resampling.

    Returns:
        dict with percentile-based confidence intervals
    """
    print(f"\n→ Running bootstrap uncertainty estimation ({n_bootstrap} iterations)...")

    n_samples = len(log_period)
    alpha_samples = []
    beta_samples = []

    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)

        log_p_boot = log_period[indices]
        mag_boot = abs_mag[indices]
        mag_err_boot = abs_mag_err[indices]

        # Fit
        try:
            popt, _ = curve_fit(
                pl_model,
                log_p_boot,
                mag_boot,
                sigma=mag_err_boot,
                absolute_sigma=True
            )
            alpha_samples.append(popt[0])
            beta_samples.append(popt[1])
        except:
            continue

    alpha_samples = np.array(alpha_samples)
    beta_samples = np.array(beta_samples)

    # Compute percentiles (16th, 50th, 84th for ~1σ)
    alpha_ci = np.percentile(alpha_samples, [16, 50, 84])
    beta_ci = np.percentile(beta_samples, [16, 50, 84])

    print(f"  Bootstrap iterations: {len(alpha_samples)}/{n_bootstrap}")
    print(f"  alpha: {alpha_ci[1]:.4f} +{alpha_ci[2]-alpha_ci[1]:.4f} -{alpha_ci[1]-alpha_ci[0]:.4f}")
    print(f"  beta:  {beta_ci[1]:.4f} +{beta_ci[2]-beta_ci[1]:.4f} -{beta_ci[1]-beta_ci[0]:.4f}")

    return {
        'alpha_median': float(alpha_ci[1]),
        'alpha_lower': float(alpha_ci[0]),
        'alpha_upper': float(alpha_ci[2]),
        'beta_median': float(beta_ci[1]),
        'beta_lower': float(beta_ci[0]),
        'beta_upper': float(beta_ci[2]),
        'alpha_samples': alpha_samples.tolist(),
        'beta_samples': beta_samples.tolist()
    }


def plot_pl_fit(log_period, abs_mag, abs_mag_err, fit_result, output_dir):
    """Generate P-L relation plot with fit."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot with error bars
    ax.errorbar(
        log_period, abs_mag, yerr=abs_mag_err,
        fmt='o', color='steelblue', markersize=6,
        ecolor='gray', alpha=0.6, label='Anchor Cepheids'
    )

    # Fit line
    log_p_range = np.linspace(log_period.min(), log_period.max(), 100)
    fit_line = pl_model(log_p_range, fit_result['alpha'], fit_result['beta'])

    ax.plot(log_p_range, fit_line, 'r-', linewidth=2,
            label=f'Fit: M = {fit_result["alpha"]:.3f} log(P) + {fit_result["beta"]:.3f}')

    ax.set_xlabel('log₁₀(Period [days])', fontsize=12)
    ax.set_ylabel('Absolute Magnitude', fontsize=12)
    ax.set_title('Period-Luminosity Relation (Standard Fit)', fontsize=14)
    ax.legend()
    ax.grid(alpha=0.3)
    ax.invert_yaxis()  # Brighter stars at top

    plt.tight_layout()
    output_file = output_dir / 'pl_standard_fit.png'
    plt.savefig(output_file, dpi=150)
    plt.close()

    print(f"  ✓ Saved: {output_file}")


def plot_residuals(residuals, output_dir):
    """Generate residual distribution plot."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    ax1.hist(residuals, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax1.axvline(0, color='red', linestyle='--', linewidth=2)
    ax1.set_xlabel('Residual (mag)', fontsize=12)
    ax1.set_ylabel('Count', fontsize=12)
    ax1.set_title('Residual Distribution', fontsize=14)
    ax1.grid(alpha=0.3)

    # Q-Q plot
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=ax2)
    ax2.set_title('Normal Q-Q Plot', fontsize=14)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / 'pl_standard_residuals.png'
    plt.savefig(output_file, dpi=150)
    plt.close()

    print(f"  ✓ Saved: {output_file}")


def update_provenance(repo_root, fit_result, n_sources):
    """Update provenance.json with fit metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["pl_fit_standard"] = {
        "script": "scripts/30_PL_fit_standard.py",
        "script_version_hash": get_script_version_hash(),
        "fitted_at": datetime.utcnow().isoformat() + "Z",
        "n_sources": n_sources,
        "alpha": fit_result['alpha'],
        "beta": fit_result['beta'],
        "rms": fit_result['rms']
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def fit_pl_standard():
    """Fit baseline P-L relation to anchor Cepheids."""
    print("==> Fitting standard Period-Luminosity relation...")

    repo_root = get_repo_root()

    # Load prepared anchors
    print("\n→ Loading prepared anchor data...")
    anchors = load_prepared_anchors(repo_root)
    if anchors is None:
        return 1

    print(f"  Loaded {len(anchors)} anchor sources")
    print(f"  Columns: {list(anchors.columns)}")

    # Extract Period-Luminosity data
    # Need: log(Period), absolute magnitude, errors
    # First, find period column
    period_col = None
    for col in anchors.columns:
        if 'period' in col.lower():
            period_col = col
            break

    if period_col is None:
        print("ERROR: No period column found in anchor data", file=sys.stderr)
        print(f"Available columns: {list(anchors.columns)}", file=sys.stderr)
        return 1

    # Find magnitude column (corrected if available, otherwise raw)
    mag_col = 'mag_corrected' if 'mag_corrected' in anchors.columns else 'gaia_phot_g_mean_mag'

    # Compute absolute magnitude from distance
    # M = m - 5*log10(d/10)  where d is in parsecs
    if 'distance_pc' not in anchors.columns:
        print("ERROR: No distance_pc column in anchor data", file=sys.stderr)
        return 1

    # Filter valid data
    valid = (
        ~anchors[period_col].isna() &
        ~anchors['distance_pc'].isna() &
        (anchors['distance_pc'] > 0) &
        ~anchors[mag_col].isna()
    )

    print(f"\n→ Filtering valid sources...")
    print(f"  Valid: {valid.sum()}/{len(anchors)}")

    if valid.sum() < 3:
        print("ERROR: Insufficient valid sources for fitting", file=sys.stderr)
        return 1

    # Extract data
    period = anchors.loc[valid, period_col].values
    distance_pc = anchors.loc[valid, 'distance_pc'].values
    apparent_mag = anchors.loc[valid, mag_col].values

    # Compute absolute magnitude
    distance_modulus = 5 * np.log10(distance_pc / 10.0)
    abs_mag = apparent_mag - distance_modulus

    log_period = np.log10(period)

    # Estimate uncertainties (simplified - use distance errors if available)
    if 'distance_err_pc' in anchors.columns:
        distance_err = anchors.loc[valid, 'distance_err_pc'].values
        # Propagate to magnitude error
        abs_mag_err = 5 / (distance_pc * np.log(10)) * distance_err
    else:
        # Use default uncertainty
        abs_mag_err = np.full(len(abs_mag), 0.1)

    print(f"\n→ Data summary:")
    print(f"  Period range: {period.min():.2f} - {period.max():.2f} days")
    print(f"  log(P) range: {log_period.min():.3f} - {log_period.max():.3f}")
    print(f"  Abs mag range: {abs_mag.min():.3f} - {abs_mag.max():.3f}")

    # Fit P-L relation
    print(f"\n→ Fitting P-L relation (M = alpha * log(P) + beta)...")
    fit_result = fit_pl_relation(log_period, abs_mag, abs_mag_err)

    if fit_result is None:
        return 1

    print(f"  alpha = {fit_result['alpha']:.4f} ± {fit_result['alpha_err']:.4f}")
    print(f"  beta  = {fit_result['beta']:.4f} ± {fit_result['beta_err']:.4f}")
    print(f"  RMS   = {fit_result['rms']:.4f} mag")

    # Bootstrap uncertainties
    bootstrap_result = bootstrap_uncertainties(log_period, abs_mag, abs_mag_err, n_bootstrap=1000)

    # Save results
    print("\n→ Saving results...")
    results_dir = repo_root / "results" / "tables"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save parameters
    params_file = results_dir / "pl_standard_params.json"
    with open(params_file, 'w') as f:
        json.dump({
            **fit_result,
            'bootstrap': bootstrap_result,
            'n_sources': int(valid.sum())
        }, f, indent=2)
    print(f"  ✓ Saved: {params_file}")

    # Save residuals table
    residuals_df = pd.DataFrame({
        'log_period': log_period,
        'abs_mag_observed': abs_mag,
        'abs_mag_predicted': fit_result['predicted'],
        'residual': fit_result['residuals']
    })
    residuals_file = results_dir / "pl_standard_residuals.csv"
    residuals_df.to_csv(residuals_file, index=False)
    print(f"  ✓ Saved: {residuals_file}")

    # Generate plots
    print("\n→ Generating diagnostic plots...")
    figures_dir = repo_root / "results" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_pl_fit(log_period, abs_mag, abs_mag_err, fit_result, figures_dir)
    plot_residuals(fit_result['residuals'], figures_dir)

    # Update provenance
    update_provenance(repo_root, fit_result, int(valid.sum()))

    print("\n✓ Standard P-L fit complete")
    return 0


if __name__ == "__main__":
    sys.exit(fit_pl_standard())

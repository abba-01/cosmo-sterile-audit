#!/usr/bin/env python3
"""
Merge standard and conservative fits with epistemic uncertainty (ΔT, f_sys).
Environment variables: DELTA_T (default 0.0), F_SYS (default 0.01)
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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


def load_fit_results(repo_root, fit_type):
    """Load P-L fit results (standard or conservative)."""
    results_dir = repo_root / "results" / "tables"
    params_file = results_dir / f"pl_{fit_type}_params.json"

    if not params_file.exists():
        print(f"ERROR: {fit_type} fit not found: {params_file}", file=sys.stderr)
        return None

    try:
        with open(params_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load {fit_type} fit: {e}", file=sys.stderr)
        return None


def get_env_params():
    """Get ΔT and f_sys from environment variables with defaults."""
    delta_t = float(os.environ.get('DELTA_T', '0.0'))
    f_sys = float(os.environ.get('F_SYS', '0.01'))

    print(f"  Environment parameters:")
    print(f"    DELTA_T = {delta_t} (discrepancy penalty)")
    print(f"    F_SYS   = {f_sys} (systematic fraction)")

    return delta_t, f_sys


def compute_tension(val1, err1, val2, err2):
    """
    Compute tension between two measurements.

    T = |val1 - val2| / sqrt(err1² + err2²)
    """
    tension = abs(val1 - val2) / np.sqrt(err1**2 + err2**2)
    return tension


def apply_epistemic_penalty(value, base_error, tension, delta_t, f_sys):
    """
    Apply epistemic penalty to uncertainty.

    σ_epistemic = sqrt(σ_base² + (ΔT × T)² + (f_sys × value)²)

    Args:
        value: Central value
        base_error: Base statistical uncertainty
        tension: Tension metric
        delta_t: Discrepancy penalty scale
        f_sys: Systematic fraction

    Returns:
        Updated uncertainty with epistemic penalty
    """
    penalty_discrepancy = (delta_t * tension)**2
    penalty_systematic = (f_sys * value)**2

    epistemic_error = np.sqrt(base_error**2 + penalty_discrepancy + penalty_systematic)

    return epistemic_error


def merge_measurements(standard, conservative, delta_t, f_sys):
    """
    Merge standard and conservative measurements.

    Uses conservative estimate as primary, applies epistemic penalties.
    """
    # Use conservative as baseline (wider uncertainties)
    alpha_merged = conservative['alpha']
    beta_merged = conservative['beta']

    # Compute tension
    alpha_tension = compute_tension(
        standard['alpha'], standard['alpha_err'],
        conservative['alpha'], conservative['alpha_err']
    )
    beta_tension = compute_tension(
        standard['beta'], standard['beta_err'],
        conservative['beta'], conservative['beta_err']
    )

    print(f"\n→ Tension metrics:")
    print(f"  alpha tension: {alpha_tension:.2f}σ")
    print(f"  beta tension:  {beta_tension:.2f}σ")

    # Apply epistemic penalties
    alpha_err_merged = apply_epistemic_penalty(
        alpha_merged, conservative['alpha_err'],
        alpha_tension, delta_t, f_sys
    )
    beta_err_merged = apply_epistemic_penalty(
        beta_merged, conservative['beta_err'],
        beta_tension, delta_t, f_sys
    )

    return {
        'alpha': alpha_merged,
        'beta': beta_merged,
        'alpha_err': alpha_err_merged,
        'beta_err': beta_err_merged,
        'alpha_tension': alpha_tension,
        'beta_tension': beta_tension,
        'delta_t_applied': delta_t,
        'f_sys_applied': f_sys
    }


def create_summary_table(standard, conservative, merged, output_dir):
    """Create summary CSV and JSON."""
    summary = {
        'standard_alpha': standard['alpha'],
        'standard_alpha_err': standard['alpha_err'],
        'standard_beta': standard['beta'],
        'standard_beta_err': standard['beta_err'],
        'conservative_alpha': conservative['alpha'],
        'conservative_alpha_err': conservative['alpha_err'],
        'conservative_beta': conservative['beta'],
        'conservative_beta_err': conservative['beta_err'],
        'merged_alpha': merged['alpha'],
        'merged_alpha_err': merged['alpha_err'],
        'merged_beta': merged['beta'],
        'merged_beta_err': merged['beta_err'],
        'alpha_tension_sigma': merged['alpha_tension'],
        'beta_tension_sigma': merged['beta_tension'],
        'delta_t': merged['delta_t_applied'],
        'f_sys': merged['f_sys_applied']
    }

    # Save CSV
    df = pd.DataFrame([summary])
    csv_file = output_dir / "merge_summary.csv"
    df.to_csv(csv_file, index=False)
    print(f"  ✓ Saved: {csv_file}")

    # Save JSON
    json_file = output_dir / "merge_summary.json"
    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  ✓ Saved: {json_file}")


def plot_comparison(standard, conservative, merged, output_dir):
    """Generate comparison plot of all three fits."""
    fig, ax = plt.subplots(figsize=(10, 6))

    log_p_range = np.linspace(0.5, 2.0, 100)

    # Standard
    std_line = standard['alpha'] * log_p_range + standard['beta']
    ax.plot(log_p_range, std_line, 'r-', linewidth=2, label='Standard', alpha=0.7)

    # Conservative
    cons_line = conservative['alpha'] * log_p_range + conservative['beta']
    ax.plot(log_p_range, cons_line, 'b--', linewidth=2, label='Conservative', alpha=0.7)

    # Merged
    merged_line = merged['alpha'] * log_p_range + merged['beta']
    ax.plot(log_p_range, merged_line, 'g-.', linewidth=3, label='Merged (Epistemic)', alpha=0.9)

    ax.set_xlabel('log₁₀(Period [days])', fontsize=12)
    ax.set_ylabel('Absolute Magnitude', fontsize=12)
    ax.set_title('P-L Relation: Epistemic Merge', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    ax.invert_yaxis()

    plt.tight_layout()
    output_file = output_dir / 'merge_comparison.png'
    plt.savefig(output_file, dpi=150)
    plt.close()

    print(f"  ✓ Saved: {output_file}")


def update_provenance(repo_root, merged):
    """Update provenance.json with merge metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["epistemic_merge"] = {
        "script": "scripts/40_epistemic_merge.py",
        "script_version_hash": get_script_version_hash(),
        "merged_at": datetime.utcnow().isoformat() + "Z",
        "alpha": merged['alpha'],
        "alpha_err": merged['alpha_err'],
        "beta": merged['beta'],
        "beta_err": merged['beta_err'],
        "delta_t": merged['delta_t_applied'],
        "f_sys": merged['f_sys_applied']
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def merge_epistemic():
    """Merge P-L fits with epistemic penalty."""
    print("==> Merging P-L fits with epistemic uncertainty...")

    repo_root = get_repo_root()

    # Get environment parameters
    print("\n→ Reading environment parameters...")
    delta_t, f_sys = get_env_params()

    # Load fit results
    print("\n→ Loading fit results...")
    standard = load_fit_results(repo_root, 'standard')
    conservative = load_fit_results(repo_root, 'conservative')

    if standard is None or conservative is None:
        print("ERROR: Cannot merge - missing fit results", file=sys.stderr)
        return 1

    print(f"  ✓ Loaded standard fit")
    print(f"  ✓ Loaded conservative fit")

    # Merge measurements
    print("\n→ Computing epistemic merge...")
    merged = merge_measurements(standard, conservative, delta_t, f_sys)

    print(f"\n→ Merged results:")
    print(f"  alpha = {merged['alpha']:.4f} ± {merged['alpha_err']:.4f}")
    print(f"  beta  = {merged['beta']:.4f} ± {merged['beta_err']:.4f}")

    # Save results
    print("\n→ Saving results...")
    results_dir = repo_root / "results" / "tables"
    results_dir.mkdir(parents=True, exist_ok=True)

    create_summary_table(standard, conservative, merged, results_dir)

    # Generate plots
    print("\n→ Generating comparison plot...")
    figures_dir = repo_root / "results" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_comparison(standard, conservative, merged, figures_dir)

    # Update provenance
    update_provenance(repo_root, merged)

    print("\n✓ Epistemic merge complete")
    return 0


if __name__ == "__main__":
    sys.exit(merge_epistemic())

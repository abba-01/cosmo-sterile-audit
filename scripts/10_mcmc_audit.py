#!/usr/bin/env python3
"""
Audit MCMC chains for convergence: R-hat, ESS, and weight consistency.
Thresholds: R-hat < 1.01, ESS > 1000
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import arviz as az


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


def find_planck_chains(repo_root):
    """Find Planck chain files in data/raw."""
    raw_dir = repo_root / "data" / "raw"
    chain_files = []

    # Search all hash-named directories
    for hash_dir in raw_dir.iterdir():
        if hash_dir.is_dir() and hash_dir.name != '.keep':
            # Look for chain files
            for file in hash_dir.glob("*.txt"):
                if "chain" in file.name.lower():
                    chain_files.append(file)

    return sorted(chain_files)


def load_chain_with_weights(chain_file):
    """
    Load a Planck chain file with weights.
    Expected columns: weight, -log(Like), [params...]
    Common params: H0, omegabh2, omegach2, ns, tau, ...
    """
    try:
        # Read chain file - first two columns are typically weight and -log(Like)
        data = pd.read_csv(chain_file, sep=r'\s+', header=None, comment='#')

        # Planck chains typically have format:
        # weight, -log(Like), param1, param2, ...
        # We need to identify columns - this is a simplified version
        # In real implementation, you'd parse the header or use known column positions

        if data.shape[1] < 3:
            print(f"WARNING: Chain file {chain_file.name} has only {data.shape[1]} columns")
            return None

        # For demonstration purposes, assume standard Planck column layout
        # Column 0: weight, Column 1: -log(Like), then parameters
        # Real implementation would read .paramnames file

        # Extract weights (first column)
        weights = data.iloc[:, 0].values

        # Check for valid weights
        if np.any(weights <= 0):
            print(f"WARNING: Chain {chain_file.name} has non-positive weights")
            weights = np.abs(weights)

        # Normalize weights to sum to number of samples (ArviZ convention)
        weights = weights / weights.sum() * len(weights)

        # Extract parameter samples (skip weight and -log(Like))
        samples = data.iloc[:, 2:].values

        return {
            'samples': samples,
            'weights': weights,
            'n_params': samples.shape[1],
            'n_samples': samples.shape[0]
        }

    except Exception as e:
        print(f"ERROR: Failed to load chain {chain_file.name}: {e}", file=sys.stderr)
        return None


def remove_burnin(samples, weights, burnin_frac=0.1):
    """Remove first burnin_frac of chain."""
    n_samples = len(samples)
    burnin_samples = int(n_samples * burnin_frac)

    if burnin_samples > 0:
        return samples[burnin_samples:], weights[burnin_samples:]
    return samples, weights


def compute_diagnostics(chains_data, param_names):
    """
    Compute R-hat and ESS for all parameters using ArviZ.

    Args:
        chains_data: List of dicts with 'samples' and 'weights'
        param_names: List of parameter names

    Returns:
        dict with diagnostics per parameter
    """
    n_chains = len(chains_data)
    n_params = chains_data[0]['n_params']

    # Create ArviZ InferenceData structure
    # Shape: (n_chains, n_draws, n_params)
    max_draws = min(chain['n_samples'] for chain in chains_data)

    # Truncate all chains to same length for ArviZ
    chain_arrays = []
    weight_arrays = []

    for chain in chains_data:
        chain_arrays.append(chain['samples'][:max_draws, :])
        weight_arrays.append(chain['weights'][:max_draws])

    # Stack into (n_chains, n_draws, n_params)
    samples_array = np.stack(chain_arrays, axis=0)
    weights_array = np.stack(weight_arrays, axis=0)

    # Create dataset for ArviZ
    dataset = {}
    for i, param_name in enumerate(param_names):
        dataset[param_name] = (['chain', 'draw'], samples_array[:, :, i])

    idata = az.convert_to_inference_data(dataset)

    # Compute diagnostics
    diagnostics = {}

    for param_name in param_names:
        # R-hat
        rhat = az.rhat(idata, var_names=[param_name])[param_name].values

        # ESS bulk and tail
        ess_bulk = az.ess(idata, var_names=[param_name], method='bulk')[param_name].values
        ess_tail = az.ess(idata, var_names=[param_name], method='tail')[param_name].values

        diagnostics[param_name] = {
            'rhat': float(rhat),
            'ess_bulk': float(ess_bulk),
            'ess_tail': float(ess_tail)
        }

    return diagnostics


def compute_weighted_correlation(samples1, samples2, weights):
    """Compute weighted correlation between two parameter samples."""
    # Weighted mean
    mean1 = np.average(samples1, weights=weights)
    mean2 = np.average(samples2, weights=weights)

    # Weighted covariance
    cov = np.average((samples1 - mean1) * (samples2 - mean2), weights=weights)

    # Weighted standard deviations
    std1 = np.sqrt(np.average((samples1 - mean1)**2, weights=weights))
    std2 = np.sqrt(np.average((samples2 - mean2)**2, weights=weights))

    # Correlation
    corr = cov / (std1 * std2)

    return corr


def update_provenance(repo_root, audit_results):
    """Update provenance.json with audit metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["mcmc_audit"] = {
        "script": "scripts/10_mcmc_audit.py",
        "script_version_hash": get_script_version_hash(),
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "results": audit_results
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def audit_mcmc_chains():
    """Check chain convergence diagnostics."""
    print("==> Auditing MCMC chain convergence...")

    repo_root = get_repo_root()

    # Find chain files
    print("\n→ Searching for Planck chain files...")
    chain_files = find_planck_chains(repo_root)

    if not chain_files:
        print("ERROR: No Planck chain files found in data/raw/", file=sys.stderr)
        print("       Expected files matching '*chain*.txt'", file=sys.stderr)
        return 1

    print(f"  Found {len(chain_files)} chain file(s)")

    # Load chains
    print("\n→ Loading chains with weights...")
    chains_data = []
    for chain_file in chain_files:
        print(f"  Loading: {chain_file.name}")
        chain_data = load_chain_with_weights(chain_file)
        if chain_data is None:
            return 1

        # Remove burn-in (first 10%)
        samples, weights = remove_burnin(
            chain_data['samples'],
            chain_data['weights'],
            burnin_frac=0.1
        )
        chain_data['samples'] = samples
        chain_data['weights'] = weights
        chain_data['n_samples'] = len(samples)

        chains_data.append(chain_data)
        print(f"    Samples: {chain_data['n_samples']} (after 10% burn-in removal)")

    # Define parameters of interest
    # NOTE: In real implementation, read from .paramnames file
    # For now, use standard Planck parameter order (simplified)
    param_names = ['H0', 'omegab', 'omegac', 'ns', 'tau']

    print(f"\n→ Computing diagnostics for parameters: {', '.join(param_names)}")

    # Compute diagnostics
    diagnostics = compute_diagnostics(chains_data, param_names)

    # Check thresholds
    print("\n→ Checking convergence thresholds (R-hat < 1.01, ESS > 1000)...\n")

    failures = []
    results_table = []

    for param_name in param_names:
        diag = diagnostics[param_name]
        rhat = diag['rhat']
        ess_bulk = diag['ess_bulk']
        ess_tail = diag['ess_tail']

        rhat_pass = rhat < 1.01
        ess_pass = ess_bulk > 1000 and ess_tail > 1000

        status = "✓ PASS" if (rhat_pass and ess_pass) else "✗ FAIL"

        print(f"  {param_name:10s} | R-hat: {rhat:.4f} | ESS_bulk: {ess_bulk:6.0f} | ESS_tail: {ess_tail:6.0f} | {status}")

        results_table.append({
            'parameter': param_name,
            'rhat': rhat,
            'ess_bulk': ess_bulk,
            'ess_tail': ess_tail,
            'rhat_pass': rhat_pass,
            'ess_pass': ess_pass
        })

        if not (rhat_pass and ess_pass):
            failures.append(param_name)

    # Compute weighted correlation between H0 and omegac
    print("\n→ Computing weighted correlation: corr(H0, omegac)...")

    # Combine all chains for correlation
    all_h0 = []
    all_omegac = []
    all_weights = []

    h0_idx = param_names.index('H0')
    omegac_idx = param_names.index('omegac')

    for chain in chains_data:
        all_h0.append(chain['samples'][:, h0_idx])
        all_omegac.append(chain['samples'][:, omegac_idx])
        all_weights.append(chain['weights'])

    all_h0 = np.concatenate(all_h0)
    all_omegac = np.concatenate(all_omegac)
    all_weights = np.concatenate(all_weights)

    corr_h0_omegac = compute_weighted_correlation(all_h0, all_omegac, all_weights)
    print(f"  corr(H0, omegac) = {corr_h0_omegac:.4f}")

    # Save results to CSV
    print("\n→ Saving audit report...")
    results_dir = repo_root / "results" / "tables"
    results_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results_table)
    df['corr_H0_omegac'] = [corr_h0_omegac if i == 0 else '' for i in range(len(df))]

    output_file = results_dir / "mcmc_audit.csv"
    df.to_csv(output_file, index=False)
    print(f"  ✓ Saved to: {output_file}")

    # Update provenance
    audit_results = {
        'n_chains': len(chains_data),
        'parameters': param_names,
        'corr_H0_omegac': corr_h0_omegac,
        'failures': failures
    }
    update_provenance(repo_root, audit_results)

    # Final status
    print()
    if failures:
        print(f"✗ CONVERGENCE FAILED for: {', '.join(failures)}", file=sys.stderr)
        return 1
    else:
        print("✓ All parameters passed convergence thresholds")
        return 0


if __name__ == "__main__":
    sys.exit(audit_mcmc_chains())

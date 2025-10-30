#!/usr/bin/env python3
"""
Fetch SH0ES distance ladder data from VizieR and verify SHA-256 checksum.
URLs MUST be provided via environment variables. No hardcoded URLs.
"""

import sys
import os
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import yaml


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


def download_file(url, output_path):
    """
    Download file using curl (more secure than Python's urllib for large files).
    Enforces HTTPS only.
    """
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        print(f"ERROR: Only HTTPS URLs are allowed. Got: {parsed.scheme}", file=sys.stderr)
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Use curl with fail-on-error, follow redirects, and connection timeout
        cmd = [
            'curl',
            '--fail',           # Fail on HTTP errors
            '--location',       # Follow redirects
            '--max-time', '3600',  # 1 hour timeout
            '--output', str(output_path),
            '--silent',
            '--show-error',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: Download failed: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"ERROR: Download exception: {e}", file=sys.stderr)
        return False


def update_provenance(repo_root, file_info, env_vars_used, actual_hash):
    """Update provenance.json with download metadata."""
    prov_file = repo_root / "manifests" / "provenance.json"

    try:
        with open(prov_file, 'r') as f:
            provenance = json.load(f)
    except Exception:
        provenance = {"version": "1.0.0", "files": {}}

    provenance["generated_at"] = datetime.utcnow().isoformat() + "Z"
    provenance["files"][file_info['name']] = {
        "sha256": actual_hash,
        "source": "shoes_vizier",
        "env_var": file_info['env_var'],
        "env_var_value": env_vars_used.get(file_info['env_var'], ""),
        "downloaded_at": datetime.utcnow().isoformat() + "Z",
        "script": "scripts/02_fetch_ladder.py",
        "script_version_hash": get_script_version_hash()
    }

    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)


def update_checksums(repo_root, filename, file_hash):
    """Append to checksums.sha256 file."""
    checksum_file = repo_root / "manifests" / "checksums.sha256"

    # Read existing checksums
    existing = set()
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    existing.add(line.strip())

    # Add new checksum
    new_entry = f"{file_hash}  data/raw/{file_hash[:16]}/{filename}"
    existing.add(new_entry)

    # Write back sorted
    with open(checksum_file, 'w') as f:
        f.write("# SHA-256 checksums computed after data fetch\n")
        f.write("# Format: <hash>  <filepath>\n")
        f.write(f"# Updated: {datetime.utcnow().isoformat()}Z\n#\n")
        f.write("# Verify with: cd data/raw && sha256sum -c ../../manifests/checksums.sha256\n\n")
        for entry in sorted(existing):
            f.write(entry + "\n")


def fetch_ladder_data():
    """Download SH0ES distance ladder data and verify checksums."""
    print("==> Fetching SH0ES distance ladder data...")

    repo_root = get_repo_root()
    manifest_file = repo_root / "manifests" / "sources.yml"

    # Load manifest
    try:
        with open(manifest_file, 'r') as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to read manifest: {e}", file=sys.stderr)
        return 1

    shoes_config = manifest.get('shoes_vizier', {})
    files = shoes_config.get('files', [])

    if not files:
        print("ERROR: No files defined in manifest for 'shoes_vizier'", file=sys.stderr)
        return 1

    env_vars_used = {}
    downloaded_files = []

    # Process each file
    for file_info in files:
        filename = file_info['name']
        expected_sha256 = file_info['sha256']
        env_var = file_info['env_var']

        print(f"\n→ Processing: {filename}")

        # Check for URL in environment
        url = os.environ.get(env_var)
        if not url:
            print(f"ERROR: Environment variable {env_var} not set", file=sys.stderr)
            print(f"       Set it to the HTTPS URL for {filename}", file=sys.stderr)
            return 1

        env_vars_used[env_var] = url
        print(f"  URL source: ${env_var}")

        # Verify expected hash is not placeholder
        if '<' in expected_sha256 or '>' in expected_sha256 or expected_sha256.startswith('placeholder'):
            print(f"WARNING: Expected SHA-256 is a placeholder: {expected_sha256}")
            print(f"         Will compute and report actual hash")
            expected_sha256 = None

        # Download to temporary location first
        temp_path = repo_root / "data" / "raw" / f".tmp_{filename}"
        print(f"  Downloading...")

        if not download_file(url, temp_path):
            return 1

        # Compute actual hash
        print(f"  Computing SHA-256...")
        actual_hash = compute_sha256(temp_path)
        print(f"  Computed: {actual_hash}")

        # Verify hash if expected is provided
        if expected_sha256:
            if actual_hash != expected_sha256:
                print(f"ERROR: SHA-256 mismatch!", file=sys.stderr)
                print(f"  Expected: {expected_sha256}", file=sys.stderr)
                print(f"  Actual:   {actual_hash}", file=sys.stderr)
                print(f"  Deleting downloaded file...", file=sys.stderr)
                temp_path.unlink()
                return 1
            print(f"  ✓ SHA-256 verified")
        else:
            print(f"  ⚠ No expected hash to verify against")
            print(f"  Please update manifests/sources.yml with:")
            print(f"    sha256: \"{actual_hash}\"")

        # Move to hash-named directory
        hash_prefix = actual_hash[:16]
        final_dir = repo_root / "data" / "raw" / hash_prefix
        final_dir.mkdir(parents=True, exist_ok=True)
        final_path = final_dir / filename

        temp_path.rename(final_path)
        downloaded_files.append(final_path)

        print(f"  ✓ Saved to: data/raw/{hash_prefix}/{filename}")

        # Update manifests
        update_provenance(repo_root, file_info, env_vars_used, actual_hash)
        update_checksums(repo_root, filename, actual_hash)

    print(f"\n✓ Downloaded {len(downloaded_files)} file(s)")

    # Run sterility verification
    print("\n==> Running sterility verification...")
    sterility_script = repo_root / "scripts" / "00_verify_sterility.py"
    result = subprocess.run([sys.executable, str(sterility_script)])

    return result.returncode


if __name__ == "__main__":
    sys.exit(fetch_ladder_data())

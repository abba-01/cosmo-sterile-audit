#!/usr/bin/env python3
"""
Update manifests/sources.yml with actual SHA-256 hashes from checksums.sha256.

After running 'make fetch', this script reads the computed checksums and updates
the YAML manifest to replace placeholder values like <EXPECTED_SHA256_FROM_*>
with the actual hash values.

Usage:
    python3 scripts/update_manifest_hashes.py

This will:
1. Read manifests/checksums.sha256
2. Parse manifests/sources.yml
3. Match filenames and update sha256 fields
4. Write back to manifests/sources.yml with updated hashes
"""

import sys
import re
from pathlib import Path
import yaml


def get_repo_root():
    """Get repository root directory."""
    return Path(__file__).resolve().parents[1]


def load_computed_checksums(checksums_file):
    """
    Load checksums from manifests/checksums.sha256.

    Returns:
        dict: {filename: sha256_hash}
    """
    checksums = {}

    if not checksums_file.exists():
        print(f"ERROR: {checksums_file} not found", file=sys.stderr)
        print("       Run 'make fetch' first to generate checksums", file=sys.stderr)
        return None

    with open(checksums_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse: <hash>  <filepath>
            parts = line.split(None, 1)
            if len(parts) == 2:
                hash_val, filepath = parts
                # Extract just the filename
                filename = Path(filepath).name
                checksums[filename] = hash_val

    print(f"✓ Loaded {len(checksums)} checksums from {checksums_file.name}")
    return checksums


def update_manifest_hashes(manifest_file, checksums):
    """
    Update manifests/sources.yml with actual SHA-256 hashes.

    Args:
        manifest_file: Path to sources.yml
        checksums: dict of {filename: sha256_hash}

    Returns:
        int: Number of hashes updated
    """
    if not manifest_file.exists():
        print(f"ERROR: {manifest_file} not found", file=sys.stderr)
        return 0

    # Load YAML
    with open(manifest_file, 'r') as f:
        manifest = yaml.safe_load(f)

    updated_count = 0

    # Iterate through all sources
    for source_name, source_data in manifest.items():
        if not isinstance(source_data, dict) or 'files' not in source_data:
            continue

        for file_entry in source_data['files']:
            if not isinstance(file_entry, dict):
                continue

            filename = file_entry.get('name')
            current_hash = file_entry.get('sha256', '')

            if not filename:
                continue

            # Check if hash is a placeholder
            if current_hash.startswith('<EXPECTED_SHA256_'):
                # Look up actual hash
                if filename in checksums:
                    actual_hash = checksums[filename]
                    file_entry['sha256'] = actual_hash
                    updated_count += 1
                    print(f"  ✓ Updated {source_name}/{filename}")
                    print(f"    Old: {current_hash}")
                    print(f"    New: {actual_hash}")
                else:
                    print(f"  ⚠ No checksum found for {source_name}/{filename}", file=sys.stderr)

    if updated_count > 0:
        # Write back to file, preserving comments
        # First, read the original file to preserve header comments
        with open(manifest_file, 'r') as f:
            original_lines = f.readlines()

        # Find where the YAML content starts (after header comments)
        yaml_start = 0
        for i, line in enumerate(original_lines):
            if line.strip() and not line.strip().startswith('#'):
                yaml_start = i
                break

        # Preserve header
        header = ''.join(original_lines[:yaml_start])

        # Write back with preserved header
        with open(manifest_file, 'w') as f:
            f.write(header)
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, width=120)

        print(f"\n✓ Updated {updated_count} hash(es) in {manifest_file.name}")
    else:
        print("\n✓ No placeholder hashes found (manifest already up to date)")

    return updated_count


def main():
    """Main entry point."""
    print("==> Updating manifest with computed SHA-256 hashes...")

    repo_root = get_repo_root()
    checksums_file = repo_root / "manifests" / "checksums.sha256"
    manifest_file = repo_root / "manifests" / "sources.yml"

    # Load computed checksums
    checksums = load_computed_checksums(checksums_file)
    if checksums is None:
        return 1

    if not checksums:
        print("WARNING: No checksums found in file", file=sys.stderr)
        return 1

    # Update manifest
    print(f"\n→ Updating {manifest_file.name}...")
    updated = update_manifest_hashes(manifest_file, checksums)

    if updated > 0:
        print("\n→ Next steps:")
        print("  1. Review the changes: git diff manifests/sources.yml")
        print("  2. Commit the updated manifest: git add manifests/sources.yml && git commit")
        print("  3. Future 'make verify' runs will now check against these hashes")

    return 0


if __name__ == "__main__":
    sys.exit(main())

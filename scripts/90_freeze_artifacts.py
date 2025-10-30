#!/usr/bin/env python3
"""
Freeze final artifacts: compute hashes, generate SBOM, create tarball.
"""

import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime


def compute_sha256(filepath):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def freeze_artifacts():
    """Generate checksums, provenance, and archive."""
    print("Freezing artifacts...")

    repo_root = Path(__file__).parent.parent
    checksums = []
    provenance = {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "repository": "cosmo-sterile-audit",
        "files": {}
    }

    # Compute checksums for data files
    for data_dir in ["processed", "interim"]:
        data_path = repo_root / "data" / data_dir
        if data_path.exists():
            for file in data_path.rglob("*"):
                if file.is_file() and file.name != ".keep":
                    hash_val = compute_sha256(file)
                    rel_path = file.relative_to(repo_root)
                    checksums.append(f"{hash_val}  {rel_path}")
                    provenance["files"][str(rel_path)] = {
                        "sha256": hash_val,
                        "size_bytes": file.stat().st_size
                    }

    # Write checksums
    checksum_file = repo_root / "manifests" / "checksums.sha256"
    with open(checksum_file, 'w') as f:
        f.write("# SHA-256 checksums computed after data processing\n")
        f.write("# Format: <hash>  <filepath>\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n#\n")
        f.write("# Verify with: sha256sum -c manifests/checksums.sha256\n\n")
        for line in sorted(checksums):
            f.write(line + "\n")

    # Write provenance
    prov_file = repo_root / "manifests" / "provenance.json"
    with open(prov_file, 'w') as f:
        json.dump(provenance, f, indent=2)

    print(f"✓ Checksums written to {checksum_file}")
    print(f"✓ Provenance written to {prov_file}")
    print("TODO: Generate SBOM (Software Bill of Materials)")
    print("TODO: Create release tarball")

    return 0


if __name__ == "__main__":
    sys.exit(freeze_artifacts())

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

    # Generate SBOM
    print("\n==> Generating Software Bill of Materials...")
    artifacts_dir = repo_root / "results" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    sbom_file = artifacts_dir / "SBOM.txt"
    with open(sbom_file, 'w') as f:
        f.write("# Software Bill of Materials (SBOM)\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"# Repository: cosmo-sterile-audit\n")

        # Get git commit if available
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, cwd=repo_root)
            if result.returncode == 0:
                f.write(f"# Git commit: {result.stdout.strip()}\n")
        except:
            pass

        # Python version
        import sys as sys_module
        import platform
        f.write(f"# Python: {sys_module.version}\n")
        f.write(f"# Platform: {platform.platform()}\n")
        f.write("\n# Dependencies:\n")

        # Get installed packages
        try:
            import subprocess
            result = subprocess.run(['pip', 'list', '--format=freeze'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                f.write(result.stdout)
        except:
            f.write("# (pip list unavailable)\n")

    print(f"✓ SBOM written to {sbom_file}")

    # Create release tarball
    print("\n==> Creating release tarball...")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    tarball_name = f"release_{timestamp}.tar.gz"
    tarball_path = artifacts_dir / tarball_name

    import tarfile
    with tarfile.open(tarball_path, "w:gz") as tar:
        # Add results directory
        tar.add(repo_root / "results", arcname="results")
        # Add manifests
        tar.add(repo_root / "manifests", arcname="manifests")

    # Compute tarball hash
    tarball_hash = compute_sha256(tarball_path)
    hash_file = artifacts_dir / f"{tarball_name}.sha256"
    with open(hash_file, 'w') as f:
        f.write(f"{tarball_hash}  {tarball_name}\n")

    print(f"✓ Release tarball: {tarball_path}")
    print(f"✓ SHA-256: {tarball_hash}")
    print(f"✓ Hash file: {hash_file}")

    return 0


if __name__ == "__main__":
    sys.exit(freeze_artifacts())

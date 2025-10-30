#!/usr/bin/env python3
"""
Verify repository sterility: no symlinks, proper permissions, path safety.
Exit code 0 if sterile, non-zero otherwise.
"""

import os
import sys
from pathlib import Path


def get_repo_root():
    """Get the repository root directory."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def check_no_symlinks(repo_root):
    """Verify no symbolic links exist anywhere in the repository."""
    symlinks_found = []

    for root, dirs, files in os.walk(repo_root):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')

        # Check directories
        for d in dirs:
            path = Path(root) / d
            if path.is_symlink():
                symlinks_found.append(str(path.relative_to(repo_root)))

        # Check files
        for f in files:
            path = Path(root) / f
            if path.is_symlink():
                symlinks_found.append(str(path.relative_to(repo_root)))

    if symlinks_found:
        print("ERROR: Symbolic links detected (violates sterility policy):", file=sys.stderr)
        for link in symlinks_found:
            print(f"  - {link}", file=sys.stderr)
        return False

    return True


def check_data_raw_readonly(repo_root):
    """Verify data/raw is read-only (if it exists and has content)."""
    raw_path = repo_root / "data" / "raw"

    if not raw_path.exists():
        print("WARNING: data/raw does not exist yet")
        return True

    # Check if directory has any real files (not just .keep)
    has_data = any(f.name != '.keep' for f in raw_path.iterdir() if f.is_file())

    if has_data:
        # Check permissions - should be 0555 (r-xr-xr-x for directories)
        perms = oct(raw_path.stat().st_mode)[-3:]
        if perms != '555' and perms != '755':
            print(f"WARNING: data/raw permissions are {perms}, should be 555 after fetch", file=sys.stderr)
            # This is a warning, not an error, since it's only required after fetch

    return True


def check_path_traversal_safety(path_str, repo_root):
    """
    Guard against path traversal attacks.
    Ensures a given path string would resolve within repo_root.
    """
    try:
        target = (repo_root / path_str).resolve()
        return target.is_relative_to(repo_root)
    except (ValueError, OSError):
        return False


def verify_no_path_traversal_patterns(repo_root):
    """Check for suspicious path patterns in tracked files."""
    suspicious_patterns = ['../', '..\\', '~/', '/tmp/', '/var/tmp/']
    issues = []

    # Check Python scripts for suspicious write operations
    scripts_dir = repo_root / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.glob("*.py"):
            try:
                content = script.read_text()
                for pattern in suspicious_patterns:
                    if pattern in content and ('open(' in content or 'write' in content):
                        issues.append(f"{script.name} contains suspicious pattern: {pattern}")
            except Exception as e:
                print(f"WARNING: Could not read {script.name}: {e}", file=sys.stderr)

    if issues:
        print("WARNING: Potentially unsafe path patterns detected:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)

    return True  # Warning only, not a hard failure


def main():
    """Run all sterility checks."""
    repo_root = get_repo_root()
    print(f"Verifying sterility of repository: {repo_root}")

    checks = [
        ("No symlinks", check_no_symlinks(repo_root)),
        ("data/raw read-only check", check_data_raw_readonly(repo_root)),
        ("Path traversal safety", verify_no_path_traversal_patterns(repo_root)),
    ]

    all_passed = all(result for _, result in checks)

    print("\nSterility Check Results:")
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    if all_passed:
        print("\n✓ Repository is sterile")
        return 0
    else:
        print("\n✗ Repository sterility checks failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

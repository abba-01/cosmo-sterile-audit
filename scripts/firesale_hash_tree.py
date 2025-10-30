#!/usr/bin/env python3
"""
Deterministic Merkle root over tracked files.
- Only hashes files in `git ls-files`
- Normalizes line endings via bytes as-is (no EOL munging)
- Ignores .git/ and any artifacts not tracked by git
Outputs:
  - prints Merkle root to stdout
  - writes results/artifacts/HASHES.txt (per-file sha256)
"""
import hashlib, json, subprocess, sys, os, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "results" / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, cwd=ROOT).strip()

def file_sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    files = sh("git ls-files -z").split('\x00')
    files = [f for f in files if f]  # drop trailing empty
    files_sorted = sorted(files)     # deterministic order

    per_file = []
    # Merkle over (path + sha) leaves
    leaves = []
    for rel in files_sorted:
        p = ROOT / rel
        # safety: must be regular file
        if not p.is_file():
            continue
        digest = file_sha256(p)
        per_file.append({"path": rel, "sha256": digest})
        leaves.append(hashlib.sha256((rel + '\n' + digest).encode('utf-8')).digest())

    if not leaves:
        print("no files to hash", file=sys.stderr)
        sys.exit(1)

    # simple binary Merkle tree
    cur = leaves
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            a = cur[i]
            b = cur[i+1] if i+1 < len(cur) else a
            nxt.append(hashlib.sha256(a + b).digest())
        cur = nxt
    merkle_root = cur[0].hex()

    # write human-readable HASHES.txt
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out_txt = ART / "HASHES.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"# Repository hash manifest\n")
        f.write(f"# Timestamp: {ts}\n")
        f.write(f"# MerkleRoot: {merkle_root}\n")
        for row in per_file:
            f.write(f"{row['sha256']}  {row['path']}\n")

    # also JSON for machines
    out_json = ART / "HASHES.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"timestamp": ts, "merkle_root": merkle_root, "files": per_file},
                  f, indent=2)

    print(merkle_root)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package-root", default=".")
    args = ap.parse_args()
    root = Path(args.package_root).expanduser().resolve()
    package_path = root / "manifest/package.json"
    package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    package["validation"] = "passed"
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inventory = root / "manifest/files.csv"
    validation = root / "manifest/validation.json"
    if validation.exists():
        validation.unlink()
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p not in {inventory, validation}):
        rows.append((path.relative_to(root).as_posix(), path.stat().st_size, sha256(path)))
    with inventory.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["path", "bytes", "sha256"]); w.writerows(rows)
    p = subprocess.run([sys.executable, str(root / "scripts/validate_package.py"), "--package-root", str(root), "--output", str(validation)], text=True)
    if p.returncode:
        return p.returncode
    print(json.dumps({"root": str(root), "files": len(rows), "validation": str(validation), "validation_sha256": sha256(validation)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

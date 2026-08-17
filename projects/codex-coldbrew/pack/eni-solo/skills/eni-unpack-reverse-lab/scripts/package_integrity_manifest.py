#!/usr/bin/env python3
"""Create a read-only SHA-256 integrity manifest for a local package."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only package SHA-256 manifest")
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    entries = []
    for path in sorted((item for item in args.root.rglob("*") if item.is_file()), key=lambda item: str(item).lower()):
        entries.append({"relative_path": str(path.relative_to(args.root)), "size": path.stat().st_size, "sha256": sha256(path)})
    result = {"status": "read_only_package_integrity_manifest", "root": str(args.root), "file_count": len(entries), "files": entries}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "files": len(entries)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

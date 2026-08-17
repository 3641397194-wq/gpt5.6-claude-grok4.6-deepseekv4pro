#!/usr/bin/env python3
"""Build and verify a deterministic DeepSeek Harness ColdBrew source archive."""

from __future__ import annotations

import argparse
import hashlib
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
STEM = "DeepSeek Harness ColdBrew".replace(" ", "-") + f"-v{VERSION}-Source"
ARCHIVE = ROOT / f"{STEM}.zip"
SIDECAR = ROOT / f"{STEM}.sha256"
ZIP_TIME = (2026, 8, 17, 0, 0, 0)
IGNORED = {".git", "__pycache__", ".pytest_cache", "build", "dist"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def source_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in IGNORED for part in relative.parts) or path.is_dir():
            continue
        if path.is_symlink():
            raise RuntimeError(f"symlink is not publishable: {relative}")
        if path in (ARCHIVE, SIDECAR) or path.name.endswith("-Source.zip") or path.name.endswith("-Source.sha256"):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def build(path: Path) -> str:
    entries = [(item.relative_to(ROOT).as_posix(), item.read_bytes()) for item in source_files()]
    manifest = "".join(f"{digest(data)}  {name}\n" for name, data in entries).encode("utf-8")
    entries.append(("SHA256SUMS.txt", manifest))
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.create_system = 3
            mode = 0o755 if PurePosixPath(name).suffix in {".py", ".sh"} else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    return digest(path.read_bytes())


def verify() -> str:
    expected = digest(ARCHIVE.read_bytes())
    if SIDECAR.read_text(encoding="ascii") != f"{expected}  {ARCHIVE.name}\n":
        raise RuntimeError("source sidecar mismatch")
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("duplicate ZIP entry")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                raise RuntimeError(f"unsafe ZIP entry: {name}")
        recorded = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            value, name = line.split("  ", 1)
            recorded[name] = value
        if set(recorded) != set(names) - {"SHA256SUMS.txt"}:
            raise RuntimeError("internal manifest paths differ")
        for name, value in recorded.items():
            if digest(archive.read(name)) != value:
                raise RuntimeError(f"internal checksum mismatch: {name}")
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / ARCHIVE.name
        if build(rebuilt) != expected or rebuilt.read_bytes() != ARCHIVE.read_bytes():
            raise RuntimeError("archive is not reproducible")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    if args.command == "build":
        value = build(ARCHIVE)
        SIDECAR.write_text(f"{value}  {ARCHIVE.name}\n", encoding="ascii", newline="\n")
        print(f"ARCHIVE={ARCHIVE}")
    else:
        value = verify()
        print("ARCHIVE_STRUCTURE=PASS")
        print("ARCHIVE_REPRODUCIBLE=PASS")
    print(f"SHA256={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

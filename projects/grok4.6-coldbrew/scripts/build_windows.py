#!/usr/bin/env python3
"""Build the single-file Windows application with PyInstaller."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
STEM = "Grok 4.6 ColdBrew".replace(" ", "-") + f"-v{VERSION}-Windows"
EXE = ROOT / "dist" / f"{STEM}.exe"
SIDECAR = ROOT / "dist" / f"{STEM}.sha256"


def build() -> None:
    if os.name != "nt":
        raise RuntimeError("Windows build requires Windows")
    separator = os.pathsep
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", STEM, "--paths", str(ROOT / "app"),
        "--add-data", f"{ROOT / 'VERSION'}{separator}.",
        "--add-data", f"{ROOT / 'app' / 'profiles.json'}{separator}app",
    ]
    for path in (ROOT / "docs" / "images").glob("*.png"):
        command += ["--add-data", f"{path}{separator}docs/images"]
    command += ["--distpath", str(EXE.parent), "--workpath", str(ROOT / "build"), "--specpath", str(ROOT / "build"), str(ROOT / "app" / "grok_coldbrew.py")]
    subprocess.run(command, check=True)
    value = hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
    SIDECAR.write_text(f"{value}  {EXE.name}\n", encoding="ascii", newline="\n")


def verify() -> str:
    data = EXE.read_bytes()
    if not data.startswith(b"MZ") or len(data) < 4_000_000:
        raise RuntimeError("invalid packaged executable")
    value = hashlib.sha256(data).hexdigest().upper()
    if SIDECAR.read_text(encoding="ascii") != f"{value}  {EXE.name}\n":
        raise RuntimeError("Windows checksum mismatch")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    if args.command == "build":
        build()
    print(f"SHA256={verify()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

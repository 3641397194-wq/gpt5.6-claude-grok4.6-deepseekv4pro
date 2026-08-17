#!/usr/bin/env python3
"""Build and verify the Claude ColdBrew single-file Windows application."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
APP_STEM = f"Claude-ColdBrew-Studio-v{VERSION}-Windows"
EXE_PATH = ROOT / "dist" / f"{APP_STEM}.exe"
HASH_PATH = ROOT / "dist" / f"{APP_STEM}.sha256"
ENTRY_PATH = ROOT / "app" / "claude_pojia.py"
ACTIVATION_PATH = ROOT / "app" / "coldbrew_activation.py"
BRAIN_PATH = ROOT / "app" / "brain_layers.py"
PROFILE_PATH = ROOT / "app" / "profiles.json"
ICON_PATH = ROOT / "assets" / "coldbrew.ico"
BRAND_PATH = ROOT / "assets" / "ishii-brand.png"
COMMUNITY_PATHS = (
    ROOT / "docs" / "images" / "qq-group-codex.png",
    ROOT / "docs" / "images" / "qq-group-codex-claude.png",
    ROOT / "docs" / "images" / "codex-group-qr.png",
)
WORK_PATH = ROOT / "build" / "pyinstaller-claude"
SPEC_PATH = ROOT / "build"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("Windows EXE builds must run on Windows")


def pyinstaller_command() -> list[str]:
    required = (
        ENTRY_PATH,
        ACTIVATION_PATH,
        BRAIN_PATH,
        PROFILE_PATH,
        ROOT / "VERSION",
        ICON_PATH,
        BRAND_PATH,
        *COMMUNITY_PATHS,
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Windows build inputs missing: {missing}")
    data_separator = os.pathsep
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        APP_STEM,
        "--icon",
        str(ICON_PATH),
        "--paths",
        str(ROOT / "app"),
        "--hidden-import",
        "brain_layers",
        "--add-data",
        f"{ROOT / 'VERSION'}{data_separator}.",
        "--add-data",
        f"{PROFILE_PATH}{data_separator}app",
        "--add-data",
        f"{ICON_PATH}{data_separator}assets",
        "--add-data",
        f"{BRAND_PATH}{data_separator}assets",
        "--distpath",
        str(EXE_PATH.parent),
        "--workpath",
        str(WORK_PATH),
        "--specpath",
        str(SPEC_PATH),
        str(ENTRY_PATH),
    ]
    for path in COMMUNITY_PATHS:
        command[command.index("--distpath"):command.index("--distpath")] = [
            "--add-data",
            f"{path}{data_separator}docs/images",
        ]
    return command


def verify() -> tuple[str, int]:
    require_windows()
    if not EXE_PATH.is_file():
        raise RuntimeError(f"Windows application missing: {EXE_PATH}")
    data = EXE_PATH.read_bytes()
    if not data.startswith(b"MZ"):
        raise RuntimeError("Windows application does not have a PE header")
    if len(data) < 5_000_000:
        raise RuntimeError(f"Windows application is unexpectedly small: {len(data)} bytes")
    probes = (
        ([str(EXE_PATH), "activate", "--trigger", "冷咖啡"], 0, "canonical activation"),
        ([str(EXE_PATH), "activate"], 2, "missing activation"),
        ([str(EXE_PATH), "activate", "--trigger", "coldbrew-build-probe"], 2, "invalid activation"),
    )
    for command, expected, label in probes:
        probe = subprocess.run(command, check=False, timeout=45)
        if probe.returncode != expected:
            raise RuntimeError(
                f"Packaged {label} probe returned {probe.returncode}, expected {expected}"
            )
    digest = sha256_file(EXE_PATH)
    expected_line = f"{digest}  {EXE_PATH.name}\n"
    if HASH_PATH.exists() and HASH_PATH.read_text(encoding="ascii") != expected_line:
        raise RuntimeError("Windows application checksum file does not match")
    return digest, len(data)


def build() -> tuple[str, int]:
    require_windows()
    EXE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORK_PATH.mkdir(parents=True, exist_ok=True)
    subprocess.run(pyinstaller_command(), cwd=ROOT, check=True)
    # A rebuild replaces the executable, so discard a sidecar for the previous binary.
    HASH_PATH.unlink(missing_ok=True)
    digest, size = verify()
    HASH_PATH.write_text(f"{digest}  {EXE_PATH.name}\n", encoding="ascii", newline="\n")
    digest, size = verify()
    return digest, size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args(argv)
    digest, size = build() if args.command == "build" else verify()
    print(f"WINDOWS_APP={EXE_PATH}")
    print(f"WINDOWS_APP_BYTES={size}")
    print(f"WINDOWS_APP_SHA256={digest}")
    print(f"WINDOWS_{args.command.upper()}_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

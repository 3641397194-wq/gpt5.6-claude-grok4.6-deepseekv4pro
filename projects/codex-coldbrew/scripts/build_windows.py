#!/usr/bin/env python3
"""Build and verify the Codex ColdBrew single-file Windows application."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
APP_STEM = f"Codex-ColdBrew-Studio-v{VERSION}-Windows"
EXE_PATH = ROOT / "dist" / f"{APP_STEM}.exe"
HASH_PATH = ROOT / "dist" / f"{APP_STEM}.sha256"
ENTRY_PATH = ROOT / "studio" / "coldbrew_studio.py"
ACTIVATION_PATH = ROOT / "studio" / "coldbrew_activation.py"
BRAIN_PATH = ROOT / "studio" / "brain_pack.py"
REVIEW_PATH = ROOT / "studio" / "review_chain.py"
PRESETS_PATH = ROOT / "studio" / "presets.json"
ICON_PATH = ROOT / "assets" / "coldbrew-codex.ico"
BRAND_PATH = ROOT / "assets" / "ishii-brand.png"
COMMUNITY_PATHS = (
    ROOT / "docs" / "images" / "qq-group-codex.png",
    ROOT / "docs" / "images" / "qq-group-codex-claude.png",
    ROOT / "docs" / "images" / "codex-group-qr.png",
)
LICENSE_PATHS = tuple(
    ROOT / name
    for name in ("LICENSE", "LICENSE_POLICY.md", "THIRD_PARTY_NOTICES.md")
)
PROJECT_SOURCE_URL = "https://github.com/茶/codex5.6-coldbrew"
WORK_PATH = ROOT / "build" / "pyinstaller-codex"
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
        REVIEW_PATH,
        PRESETS_PATH,
        ROOT / "VERSION",
        ICON_PATH,
        BRAND_PATH,
        *COMMUNITY_PATHS,
        *LICENSE_PATHS,
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
        str(ROOT / "studio"),
        "--hidden-import",
        "brain_pack",
        "--hidden-import",
        "review_chain",
        "--add-data",
        f"{ROOT / 'VERSION'}{data_separator}.",
        "--add-data",
        f"{PRESETS_PATH}{data_separator}studio",
        "--add-data",
        f"{ICON_PATH}{data_separator}assets",
        "--add-data",
        f"{BRAND_PATH}{data_separator}assets",
    ]
    for path in COMMUNITY_PATHS:
        command.extend(("--add-data", f"{path}{data_separator}docs/images"))
    for path in LICENSE_PATHS:
        command.extend(("--add-data", f"{path}{data_separator}."))
    command.extend([
        "--distpath",
        str(EXE_PATH.parent),
        "--workpath",
        str(WORK_PATH),
        "--specpath",
        str(SPEC_PATH),
        str(ENTRY_PATH),
    ])
    return command


def verify(*, check_sidecar: bool = True) -> tuple[str, int]:
    require_windows()
    if EXE_PATH.is_symlink() or not EXE_PATH.is_file():
        raise RuntimeError(f"Windows application missing: {EXE_PATH}")
    data = EXE_PATH.read_bytes()
    if not data.startswith(b"MZ"):
        raise RuntimeError("Windows application does not have a PE header")
    if len(data) < 5_000_000:
        raise RuntimeError(f"Windows application is unexpectedly small: {len(data)} bytes")
    with tempfile.TemporaryDirectory(prefix="coldbrew-packaged-probe-") as tmp:
        probe_root = Path(tmp)
        review_home = probe_root / "codex-home"
        license_export = probe_root / "licenses"
        probes = (
            (
                [str(EXE_PATH), "activate", "--trigger", "冷咖啡"],
                0,
                "canonical activation",
            ),
            ([str(EXE_PATH), "activate"], 2, "missing activation"),
            (
                [str(EXE_PATH), "activate", "--trigger", "coldbrew-build-probe"],
                2,
                "invalid activation",
            ),
            (
                [str(EXE_PATH), "review-self-test", "--home", str(review_home), "--json"],
                0,
                "review-chain hidden import",
            ),
            (
                [str(EXE_PATH), "license", "--export", str(license_export), "--json"],
                0,
                "bundled license export",
            ),
        )
        for command, expected, label in probes:
            probe = subprocess.run(command, check=False, timeout=60)
            if probe.returncode != expected:
                raise RuntimeError(
                    f"Packaged {label} probe returned {probe.returncode}, expected {expected}"
                )
        for source in LICENSE_PATHS:
            exported = license_export / source.name
            if not exported.is_file() or exported.read_bytes() != source.read_bytes():
                raise RuntimeError(f"Packaged license material did not round-trip: {source.name}")
        source_url_path = license_export / "PUBLIC_SOURCE_URL.txt"
        if source_url_path.read_text(encoding="utf-8") != PROJECT_SOURCE_URL + "\n":
            raise RuntimeError("Packaged public source URL did not round-trip")
    digest = sha256_file(EXE_PATH)
    expected_line = f"{digest}  {EXE_PATH.name}\n"
    if check_sidecar:
        if HASH_PATH.is_symlink() or not HASH_PATH.is_file():
            raise RuntimeError(f"Windows application checksum file missing: {HASH_PATH}")
        if HASH_PATH.read_text(encoding="ascii") != expected_line:
            raise RuntimeError("Windows application checksum file does not match")
    return digest, len(data)


def build() -> tuple[str, int]:
    require_windows()
    EXE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORK_PATH.mkdir(parents=True, exist_ok=True)
    subprocess.run(pyinstaller_command(), cwd=ROOT, check=True)
    digest, size = verify(check_sidecar=False)
    HASH_PATH.write_text(
        f"{digest}  {EXE_PATH.name}\n",
        encoding="ascii",
        newline="\n",
    )
    return verify()


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

#!/usr/bin/env python3
"""Build and verify a deterministic Claude ColdBrew source release archive."""

from __future__ import annotations

import hashlib
import re
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", VERSION):
    raise RuntimeError(f"Invalid VERSION: {VERSION!r}")
ARCHIVE_NAME = f"Claude-ColdBrew-Studio-v{VERSION}-Source.zip"
ARCHIVE_PATH = ROOT / ARCHIVE_NAME
ARCHIVE_SIDECAR_NAME = f"{ARCHIVE_NAME}.sha256"
ARCHIVE_SIDECAR_PATH = ROOT / ARCHIVE_SIDECAR_NAME
MANIFEST_PATH = ROOT / "SHA256SUMS.txt"
ZIP_TIME = (2026, 8, 8, 0, 0, 0)

ROOT_FILES = {
    ".gitattributes", ".gitignore", "CHANGELOG.md", "CONTRIBUTING.md",
    "LICENSE", "LICENSE_POLICY.md", "ORIGINALITY_REPORT.md", "PROVENANCE.md",
    "README.md", "README_EN.md", "SECURITY.md", "requirements-build.txt",
    "THIRD_PARTY_NOTICES.md", "VERSION", "install.ps1", "install.sh",
    "uninstall.ps1", "uninstall.sh", "start-claude-pojia.bat",
    "start-claude-pojia.ps1", "start-claude-pojia.sh", "launch-claude-max.ps1",
    "launch-claude-max.sh",
}
TREE_SUFFIXES = {
    ".github": {".json", ".md", ".yaml", ".yml"},
    "app": {".json", ".py", ".md"},
    "assets": {".ico", ".jpg", ".png"},
    "docs": {".css", ".html", ".jpg", ".jpeg", ".js", ".md", ".png", ".svg", ".yml", ".yaml"},
    "pack": {".md", ".json", ".txt"},
    "scripts": {".py", ".md"},
}
TREE_NAMES = {"docs/.nojekyll"}
IGNORED_PARTS = {".git", ".verify-sandbox", "__pycache__", "backup", "build", "dist", "release", "work"}
HISTORICAL_ARCHIVE_PATTERN = re.compile(
    r"Claude-ColdBrew-Studio-v\d+\.\d+\.\d+-Source\.zip(?:\.sha256)?"
)
RELEASE_NOTE_PATTERN = re.compile(r"RELEASE_NOTES_v\d+\.\d+\.\d+\.md")
ALLOWED_DIRS = set(TREE_SUFFIXES)
REQUIRED = {
    "app/claude_pojia.py", "app/coldbrew_activation.py", "app/brain_layers.py", "app/profiles.json",
    "app/test_claude_pojia.py", "app/test_brain_layers.py", "assets/coldbrew.ico",
    "assets/ishii-brand-source.jpg", "assets/ishii-brand.png",
    "docs/index.html", "docs/styles.css", "docs/claude.css", "docs/app.js", "docs/images/coldbrew-mark.svg",
    "docs/images/claude-coldbrew-start.png", "docs/images/claude-coldbrew-active.png",
    "docs/images/claude-release-board.png",
    "docs/images/claude-brain-hero.png", "docs/images/ishii-coldbrew-avatar.png",
    "docs/images/qq-group-codex.jpg", "docs/images/qq-group-codex-claude.jpg",
    "docs/images/qq-group-codex.png", "docs/images/qq-group-codex-claude.png",
    "LICENSE", "LICENSE_POLICY.md", "scripts/license_audit.py", "scripts/originality_audit.py",
    "scripts/site_audit.py", "scripts/build_windows.py", "requirements-build.txt",
    "scripts/generate_brand_assets.py", f"RELEASE_NOTES_v{VERSION}.md", ".github/repository-metadata.json",
}

PACKAGE_README = f"""# Claude 破甲 · 冷咖啡 / ColdBrew Studio v{VERSION}

This archive contains the complete public source, build configuration,
documentation, tests and visual assets for the independent Claude product.

Ready-to-run Windows application:
    Claude-ColdBrew-Studio-v{VERSION}-Windows.exe

Windows:
    powershell -ExecutionPolicy Bypass -File .\\install.ps1
    start-claude-pojia.bat

macOS / Linux:
    sh ./install.sh
    sh ./start-claude-pojia.sh

Project: https://github.com/茶/claude-coldbrew
Release: https://github.com/茶/claude-coldbrew/releases/tag/v{VERSION}

ColdBrew community:
    WeChat group QR docs/images/codex-group-qr.png
    QQ group 1057540028
    QQ group 1077074552
    Telegram group https://t.me/chachachacha99999
    Official Telegram channel https://t.me/chachacha99999999

License: Claude ColdBrew Community License 1.0 (CBCL-1.0). Source, build,
documentation and assets remain public; closed, commercial, paid-hosted and
fee-gated distribution is prohibited. See LICENSE and LICENSE_POLICY.md.
""".encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def is_allowlisted(relative: str) -> bool:
    if relative in ROOT_FILES or relative in TREE_NAMES or RELEASE_NOTE_PATTERN.fullmatch(relative):
        return True
    path = PurePosixPath(relative)
    if not path.parts or path.parts[0] not in ALLOWED_DIRS:
        return False
    return path.suffix.lower() in TREE_SUFFIXES[path.parts[0]]


def discover_files() -> list[Path]:
    found: list[Path] = []
    for entry in ROOT.iterdir():
        relative = entry.relative_to(ROOT).as_posix()
        if (
            entry.name in IGNORED_PARTS
            or HISTORICAL_ARCHIVE_PATTERN.fullmatch(entry.name)
            or relative in {ARCHIVE_NAME, ARCHIVE_SIDECAR_NAME, "SHA256SUMS.txt"}
        ):
            continue
        if entry.is_symlink():
            raise RuntimeError(f"Symbolic links are not publishable: {relative}")
        if entry.is_dir():
            if entry.name not in ALLOWED_DIRS:
                raise RuntimeError(f"Directory outside release whitelist: {relative}")
            for path in entry.rglob("*"):
                rel = path.relative_to(ROOT).as_posix()
                if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
                    continue
                if path.is_symlink():
                    raise RuntimeError(f"Symbolic links are not publishable: {rel}")
                if path.is_dir():
                    continue
                if not path.is_file() or not is_allowlisted(rel):
                    raise RuntimeError(f"File outside release whitelist: {rel}")
                found.append(path)
            continue
        if not entry.is_file() or not is_allowlisted(relative):
            raise RuntimeError(f"File outside release whitelist: {relative}")
        found.append(entry)
    actual = {path.relative_to(ROOT).as_posix() for path in found}
    missing = sorted(REQUIRED - actual)
    if missing:
        raise RuntimeError(f"Required release files missing: {missing}")
    return sorted(found, key=lambda path: path.relative_to(ROOT).as_posix())


def zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_STORED
    return info


def build_archive(output: Path) -> str:
    entries: list[tuple[str, bytes, bool]] = []
    for path in discover_files():
        name = path.relative_to(ROOT).as_posix()
        entries.append((name, path.read_bytes(), path.suffix.lower() in {".py", ".sh"}))
    entries.append(("PACKAGE_README.md", PACKAGE_README, False))
    entries.sort(key=lambda item: item[0])
    internal = "".join(f"{sha256(data)}  {name}\n" for name, data, _ in entries).encode("utf-8")
    entries.append(("SHA256SUMS.txt", internal, False))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data, executable in entries:
            archive.writestr(zip_info(name, executable), data)
    return sha256(output.read_bytes())


def write_manifest() -> None:
    lines = []
    for path in discover_files() + [ARCHIVE_PATH, ARCHIVE_SIDECAR_PATH]:
        lines.append(f"{sha256(path.read_bytes())}  {path.relative_to(ROOT).as_posix()}\n")
    MANIFEST_PATH.write_text("".join(sorted(lines, key=lambda line: line.split("  ", 1)[1])), encoding="utf-8", newline="\n")


def write_archive_sidecar(archive_hash: str) -> None:
    ARCHIVE_SIDECAR_PATH.write_text(
        f"{archive_hash}  {ARCHIVE_NAME}\n", encoding="ascii", newline="\n"
    )


def parse_manifest(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9A-F]{64})  (.+)", line)
        if not match:
            raise RuntimeError(f"Invalid manifest line: {line!r}")
        digest, name = match.groups()
        if name in result:
            raise RuntimeError(f"Duplicate manifest path: {name}")
        result[name] = digest
    return result


def verify_manifest() -> None:
    expected = {path.relative_to(ROOT).as_posix(): path for path in discover_files()}
    expected[ARCHIVE_NAME] = ARCHIVE_PATH
    expected[ARCHIVE_SIDECAR_NAME] = ARCHIVE_SIDECAR_PATH
    recorded = parse_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if set(expected) != set(recorded):
        raise RuntimeError("Repository manifest path mismatch")
    for name, path in expected.items():
        if sha256(path.read_bytes()) != recorded[name]:
            raise RuntimeError(f"Repository checksum mismatch: {name}")


def verify_archive_sidecar() -> None:
    expected = f"{sha256(ARCHIVE_PATH.read_bytes())}  {ARCHIVE_NAME}\n"
    if ARCHIVE_SIDECAR_PATH.read_text(encoding="ascii") != expected:
        raise RuntimeError("Archive sidecar checksum mismatch")


def verify_archive() -> str:
    archive_hash = sha256(ARCHIVE_PATH.read_bytes())
    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("Duplicate ZIP entry")
        for name in names:
            pure = PurePosixPath(name)
            if "\\" in name or pure.is_absolute() or ".." in pure.parts:
                raise RuntimeError(f"Unsafe ZIP entry: {name}")
        internal = parse_manifest(archive.read("SHA256SUMS.txt").decode("utf-8"))
        if set(internal) != set(names) - {"SHA256SUMS.txt"}:
            raise RuntimeError("Internal archive manifest path mismatch")
        for name, digest in internal.items():
            if sha256(archive.read(name)) != digest:
                raise RuntimeError(f"Internal archive checksum mismatch: {name}")
    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / ARCHIVE_NAME
        if build_archive(rebuilt) != archive_hash or rebuilt.read_bytes() != ARCHIVE_PATH.read_bytes():
            raise RuntimeError("Archive is not reproducible")
    return archive_hash


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    if args.command == "build":
        archive_hash = build_archive(ARCHIVE_PATH)
        write_archive_sidecar(archive_hash)
        write_manifest()
        print(f"ARCHIVE={ARCHIVE_PATH}")
        print(f"ARCHIVE_SIDECAR={ARCHIVE_SIDECAR_PATH}")
        print(f"SHA256={archive_hash}")
        print("BUILD_EXIT=0")
        return 0
    verify_manifest()
    verify_archive_sidecar()
    archive_hash = verify_archive()
    print("REPOSITORY_MANIFEST=PASS")
    print("ARCHIVE_SIDECAR=PASS")
    print("ARCHIVE_STRUCTURE=PASS")
    print("ARCHIVE_REPRODUCIBLE=PASS")
    print(f"ARCHIVE_SHA256={archive_hash}")
    print("VERIFY_RELEASE_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

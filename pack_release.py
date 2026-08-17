#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ColdBrew Hub release packer — deterministic source archives + SHA256SUMS.

Packs one project (or every project) under the hub root into a reproducible
source zip: fixed archive timestamps, sorted entries, UTF-8 metadata, and
build/intermediate noise excluded.

Usage::

    python pack_release.py --all                 # every project under projects/
    python pack_release.py --project codex-coldbrew
    python pack_release.py --project codex-coldbrew --out D:\\release --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HUB_ROOT = Path(__file__).resolve().parent
PROJECTS_ROOT = HUB_ROOT / "projects"
DEFAULT_OUT = HUB_ROOT / "release"

# Directory names (any depth) that never enter a source archive.
EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}
# File suffixes excluded from source archives.
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".exe",
    ".zip",
    ".sha256",
    ".bak",
    ".tmp",
    ".log",
    ".png.bak",
}
# A deterministic timestamp so rebuilds produce identical bytes.
FIXED_MTIME = (2026, 1, 1, 0, 0, 0)


def version_of(project: Path) -> str:
    version_file = project / "VERSION"
    if version_file.is_file():
        text = version_file.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"\d+\.\d+\.\d+", text):
            return text
    return "unversioned"


def collect_files(project: Path) -> list[Path]:
    """Return relative file paths to archive, sorted for determinism."""
    result: list[Path] = []
    for path in sorted(project.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(project)
        parts = relative.parts
        if any(part in EXCLUDED_DIRS for part in parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        result.append(relative)
    return result


def pack_project(project: Path, out_dir: Path) -> dict:
    if not project.is_dir():
        return {"ok": False, "project": project.name, "error": "项目目录缺失"}
    version = version_of(project)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"{project.name}-v{version}-source.zip"
    archive_path = out_dir / archive_name
    checksum_path = out_dir / f"{archive_name}.sha256"

    files = collect_files(project)
    if not files:
        return {"ok": False, "project": project.name, "error": "未收集到任何文件"}

    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as handle:
        for relative in files:
            info = zipfile.ZipInfo(f"{project.name}/{relative.as_posix()}", FIXED_MTIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            handle.writestr(info, (project / relative).read_bytes())

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {archive_name}\n", encoding="utf-8", newline="\n")

    return {
        "ok": True,
        "project": project.name,
        "version": version,
        "files": len(files),
        "archive": str(archive_path),
        "sha256": digest,
        "stamp": stamp,
    }


def write_sums(out_dir: Path, results: list[dict]) -> Path:
    sums = out_dir / f"SHA256SUMS-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    lines = [f"{item['sha256']}  {Path(item['archive']).name}" for item in results if item.get("ok")]
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return sums


def list_projects(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ColdBrew Hub deterministic release packer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Pack every project under projects/")
    group.add_argument("--project", help="Pack a single project directory name")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory")
    parser.add_argument("--root", type=Path, default=HUB_ROOT, help="Hub root override")
    parser.add_argument("--json", action="store_true", help="Emit single-line JSON")
    args = parser.parse_args(argv)

    projects_root = args.root / "projects"
    if args.all:
        targets = list_projects(projects_root)
    else:
        target = projects_root / args.project
        if not target.is_dir():
            targets = [args.root / args.project] if (args.root / args.project).is_dir() else []
        else:
            targets = [target]
    if not targets:
        payload = {"ok": False, "error": f"未在 {projects_root} 下找到任何项目"}
        print(json.dumps(payload, ensure_ascii=False) if args.json else payload["error"])
        return 2

    results = [pack_project(project, args.out) for project in targets]
    sums = write_sums(args.out, results) if any(r.get("ok") for r in results) else None
    payload = {
        "ok": all(r.get("ok") for r in results),
        "out": str(args.out),
        "results": results,
        "sha256sums": str(sums) if sums else None,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for item in results:
            if item.get("ok"):
                print(f"[成功] {item['project']} v{item['version']} "
                      f"（{item['files']} 个文件）→ {item['archive']}")
                print(f"     sha256 {item['sha256']}")
            else:
                print(f"[失败] {item['project']}：{item.get('error')}")
        if sums:
            print(f"[校验汇总] {sums}")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

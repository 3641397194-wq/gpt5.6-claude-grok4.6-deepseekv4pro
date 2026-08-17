#!/usr/bin/env python3
"""Run deterministic governance checks for the Codex ColdBrew release."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PHRASES: dict[str, tuple[str, ...]] = {
    "LICENSE": (
        "ColdBrew Studio Community License v1.0",
        "public-source, non-commercial community license",
        "complete corresponding source",
        "under this same license",
        "must not be sold",
        "sublicensed",
        "paid product",
        "paid access gate",
        "monetized as a hosted service",
        "closed-source binary",
        "any other direct or indirect payment",
        "remove, obscure or replace",
        "does not claim OSI certification",
    ),
    "LICENSE_POLICY.md": (
        "ColdBrew Studio Community License v1.0",
        "完整对应源代码",
        "构建脚本和打包脚本",
        "同一许可证",
        "禁止闭源",
        "禁止出售、转售",
        "禁止付费托管",
        "付费门槛",
        "任何直接、间接方式收费",
        "禁止再许可",
        "禁止去除",
        "不宣称获得 OSI 认证",
    ),
    "CONTRIBUTING.md": ("LICENSE", "source", "provenance"),
    "THIRD_PARTY_NOTICES.md": ("independent", "ColdBrew Studio"),
    "SECURITY.md": ("Security Policy", "private"),
    "scripts/build_windows.py": (
        "LICENSE_PATHS",
        "LICENSE_POLICY.md",
        "THIRD_PARTY_NOTICES.md",
        "--add-data",
        "bundled license export",
        "PUBLIC_SOURCE_URL.txt",
    ),
    "studio/coldbrew_studio.py": (
        "LICENSE_DOCUMENT_NAMES",
        "license_payload",
        "PUBLIC_SOURCE_URL.txt",
        "https://github.com/茶/codex5.6-coldbrew",
        "查看许可证",
        "公开源码",
    ),
}
PUBLIC_PATHS = ("studio/", "skills/", "scripts/", "docs/", "assets/")
BUNDLED_LICENSE_FILES = ("LICENSE", "LICENSE_POLICY.md", "THIRD_PARTY_NOTICES.md")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def audit(root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def record(ok: bool, target: str, detail: str) -> None:
        checks.append({"status": "PASS" if ok else "FAIL", "target": target, "detail": detail})

    for relative, phrases in REQUIRED_PHRASES.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            record(False, relative, "missing-or-linked")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            record(False, relative, f"utf8-read:{exc.__class__.__name__}")
            continue
        folded = re.sub(r"\s+", " ", text.casefold())
        record(True, relative, "present-and-utf8")
        for phrase in phrases:
            expected = re.sub(r"\s+", " ", phrase.casefold())
            record(expected in folded, relative, f"phrase:{phrase}")

    policy = (root / "LICENSE_POLICY.md").read_text(encoding="utf-8") if (root / "LICENSE_POLICY.md").is_file() else ""
    for public_path in PUBLIC_PATHS:
        directory = root / public_path.rstrip("/")
        record(directory.is_dir(), public_path, "public-source-path")
        record(public_path in policy, "LICENSE_POLICY.md", f"covered-path:{public_path}")

    build_script = (root / "scripts" / "build_windows.py").read_text(encoding="utf-8")
    studio_source = (root / "studio" / "coldbrew_studio.py").read_text(encoding="utf-8")
    for name in BUNDLED_LICENSE_FILES:
        record(name in build_script, "scripts/build_windows.py", f"bundled-input:{name}")
        record(name in studio_source, "studio/coldbrew_studio.py", f"runtime-document:{name}")
    record(
        'command.extend(("--add-data"' in build_script,
        "scripts/build_windows.py",
        "license-inputs-added-to-pyinstaller",
    )
    record(
        "PROJECT_SOURCE_URL" in build_script and "PROJECT_SOURCE_URL" in studio_source,
        "public source",
        "embedded-and-visible-source-url",
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = audit(args.root.expanduser().resolve())
    failures = [check for check in checks if check["status"] == "FAIL"]
    if args.json:
        print(json.dumps({"ok": not failures, "checks": checks}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for check in checks:
            print(f"{check['status']} {check['target']}: {check['detail']}")
        print(f"RESULT {'PASS' if not failures else 'FAIL'} ({len(checks)} checks)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

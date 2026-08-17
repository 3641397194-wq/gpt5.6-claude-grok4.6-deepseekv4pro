#!/usr/bin/env python3
"""Deterministic governance checks for the Claude 破甲 / ColdBrew release.

The audit is intentionally dependency-free and read-only. It checks the
project's license contract and public-policy documents; it does not infer or
approve third-party license compatibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = (
    "LICENSE",
    "LICENSE_POLICY.md",
    "THIRD_PARTY_NOTICES.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "scripts/license_audit.py",
)

# These phrases are deliberately explicit: changing them requires a conscious
# review of the project-specific license, not a permissive substring accident.
REQUIRED_PHRASES: dict[str, tuple[str, ...]] = {
    "LICENSE": (
        "ColdBrew Community License 1.0",
        "CBCL-1.0",
        "Claude 破甲",
        "冷咖啡 / ColdBrew",
        "custom source-available",
        "not an OSI-approved open source license",
        "complete corresponding source",
        "closed-source distribution",
        "sale",
        "paid hosting",
        "fee gates",
        "sublicensing",
        "Attribution",
        "Third-Party Material",
        "not made,",
        "endorsed by Anthropic",
    ),
    "LICENSE_POLICY.md": (
        "CBCL-1.0",
        "不是 OSI 批准的开源许可证",
        "完整源代码、构建材料、文档和资产",
        "闭源分发",
        "出售、转售",
        "付费托管",
        "fee gate",
        "再许可",
        "署名",
        "第三方",
        "独立项目",
        "Anthropic",
    ),
    "THIRD_PARTY_NOTICES.md": (
        "Third-Party Notices",
        "independent",
        "CBCL-1.0",
        "Anthropic",
        "complete corresponding source",
    ),
    "CONTRIBUTING.md": (
        "CBCL-1.0",
        "not an OSI-approved open source license",
        "complete source, build/release configuration, documentation",
        "closed-source release",
        "paid hosting",
        "fee gate",
        "sublicense",
        "Attribution",
        "Anthropic",
    ),
    "SECURITY.md": (
        "complete corresponding source",
        "CBCL-1.0",
        "not an OSI-approved open source license",
        "Anthropic",
        "private",
    ),
}

PUBLIC_PATHS = ("app/", "scripts/", "docs/", "pack/", "assets/")


def read_utf8(path: Path) -> tuple[str | None, str | None]:
    """Return text or a stable error code without following symlinks."""

    if path.is_symlink():
        return None, "symlink"
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return None, "not-utf8"
    except OSError as exc:
        return None, f"read-error:{exc.__class__.__name__}"


def normalized(value: str) -> str:
    return value.casefold().replace("\r\n", "\n")


def add_finding(findings: list[dict[str, str]], status: str, path: str, detail: str) -> None:
    findings.append({"status": status, "path": path, "detail": detail})


def audit(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    texts: dict[str, str] = {}

    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.exists():
            add_finding(findings, "FAIL", relative, "missing")
            continue
        if not path.is_file():
            add_finding(findings, "FAIL", relative, "not-a-file")
            continue
        text, error = read_utf8(path)
        if error:
            add_finding(findings, "FAIL", relative, error)
            continue
        assert text is not None
        texts[relative] = text
        add_finding(findings, "PASS", relative, "present and UTF-8")

    for relative, phrases in REQUIRED_PHRASES.items():
        text = texts.get(relative)
        if text is None:
            continue
        haystack = normalized(text)
        for phrase in phrases:
            if normalized(phrase) not in haystack:
                add_finding(findings, "FAIL", relative, f"missing phrase: {phrase}")
            else:
                add_finding(findings, "PASS", relative, f"phrase: {phrase}")

    policy = texts.get("LICENSE_POLICY.md", "")
    policy_normalized = normalized(policy)
    for public_path in PUBLIC_PATHS:
        if public_path.casefold() not in policy_normalized:
            add_finding(findings, "FAIL", "LICENSE_POLICY.md", f"missing covered path: {public_path}")
        else:
            add_finding(findings, "PASS", "LICENSE_POLICY.md", f"covered path: {public_path}")

    # A directory containing a file is evidence that the corresponding public
    # path exists; the policy still names future `assets/` explicitly.
    for public_path in PUBLIC_PATHS:
        directory = root / public_path.rstrip("/")
        if directory.exists() and not directory.is_dir():
            add_finding(findings, "FAIL", public_path, "covered path is not a directory")

    return findings


def iter_failures(findings: Iterable[dict[str, str]]) -> Iterable[dict[str, str]]:
    return (item for item in findings if item["status"] == "FAIL")


def configure_stdio() -> None:
    """Keep human-readable audit output stable on Windows runners."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="emit stable JSON")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    findings = audit(root)
    failures = list(iter_failures(findings))
    if args.json:
        payload = {
            "root": ".",
            "ok": not failures,
            "findings": findings,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for item in findings:
            print(f"{item['status']} {item['path']}: {item['detail']}")
        print(f"RESULT {'PASS' if not failures else 'FAIL'} ({len(findings)} checks)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

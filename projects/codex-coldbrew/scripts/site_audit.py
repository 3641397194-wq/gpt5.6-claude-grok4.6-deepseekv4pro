#!/usr/bin/env python3
"""Verify Codex ColdBrew marketing text, metadata and visual assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "studio"))

from coldbrew_activation import (  # noqa: E402
    BANNER,
    CANONICAL_SHA256,
    CAPABILITY_SECTIONS,
    INTRO,
    TAGLINE,
    TARGET_HEADING,
    TARGET_PROMPT,
    TRIGGER,
    activation_document,
    activation_payload,
    activation_sha256,
    verify_canonical_contract,
)


EXPECTED_DESCRIPTION = (
    "Codex 破甲 · 冷咖啡 / ColdBrew | 原创 Codex 多层指令增强与可逆部署 Studio | "
    "微信群：冷咖啡破甲社区 | QQ：1057540028 / 1077074552 | Telegram 交流群：@chachachacha99999 | 官方频道：@chachacha99999999"
)
GROUP_ASSETS = {
    "docs/images/wechat-group-source.jpg": {
        "group": "",
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1080, 1596),
    },
    "docs/images/qq-group-codex.jpg": {
        "group": "",
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1284, 2283),
    },
    "docs/images/qq-group-codex-claude.jpg": {
        "group": "",
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1284, 2283),
    },
}
PRODUCT_ASSETS = {
    "docs/images/product-matrix.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1600, 650),
    },
    "docs/images/codex-coldbrew-start.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1240, 780),
    },
    "docs/images/codex-coldbrew-active.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1240, 780),
    },
    "docs/images/codex-release-board.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1600, 900),
    },
    "docs/images/codex-group-qr.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1080, 1596),
    },
}
BRAND_ASSETS = {
    "assets/ishii-brand-source.jpg": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (640, 640),
    },
   "assets/ishii-brand.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (62, 62),
    },
   "docs/images/ishii-coldbrew-avatar.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (512, 512),
    },
   "docs/images/codex-brain-hero.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (1600, 720),
    },
    "docs/images/qq-group-codex.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (288, 288),
    },
    "docs/images/qq-group-codex-claude.png": {
        "sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
        "size": (288, 288),
    },
}
TEXT_REQUIREMENTS = {
    "README.md": (
        "Codex ColdBrew Studio v6.1.0",
        "",
        "",
        "",
        "Telegram 交流群",
        "",
        "官方 Telegram 频道",
        "docs/images/codex-release-board.png",
        "docs/images/qq-group-codex.png",
        "docs/images/qq-group-codex-claude.png",
        "docs/images/codex-coldbrew-start.png",
        "docs/images/codex-coldbrew-active.png",
        "docs/images/codex-group-qr.png",
        "",
        "Codex-ColdBrew-Studio-v6.1.0-Windows.exe",
        "Codex-ColdBrew-Studio-v6.1.0-Source.zip",
        CANONICAL_SHA256,
    ),
    "README_EN.md": (
        "Codex Armor Break",
        "v6.1.0",
        "",
        "",
        "",
        "Telegram group",
        "",
        "Official Telegram Channel",
        "docs/images/codex-coldbrew-start.png",
        "docs/images/codex-coldbrew-active.png",
        "docs/images/codex-group-qr.png",
        "WeChat group",
        "Codex-ColdBrew-Studio-v6.1.0-Windows.exe",
    ),
    "docs/PRODUCT.md": (
        "Codex ColdBrew Studio v6",
        "five `skills/coldbrew-*/SKILL.md`",
        "Local PASS",
        "",
        "",
    ),
    "docs/index.html": (
        "Codex 破甲",
        "v6.1.0",
        'id="community"',
        "",
        "",
        "",
        "Telegram 交流群",
        "",
        "官方 Telegram 频道",
        "images/codex-release-board.png",
        "images/ishii-coldbrew-avatar.png",
        "images/qq-group-codex.png",
        "images/qq-group-codex-claude.png",
        "images/codex-coldbrew-start.png",
        "images/codex-coldbrew-active.png",
        "images/codex-group-qr.png",
        "",
        "Codex-ColdBrew-Studio-v6.1.0-Windows.exe",
        "禁止闭源发布、商业售卖、付费托管和收费分发",
    ),
    "LICENSE_POLICY.md": ("禁止闭源", "禁止出售、转售", "禁止付费托管", "禁止再许可"),
    "THIRD_PARTY_NOTICES.md": (
        GROUP_ASSETS["docs/images/qq-group-codex.jpg"]["sha256"],
        GROUP_ASSETS["docs/images/qq-group-codex-claude.jpg"]["sha256"],
        BRAND_ASSETS["assets/ishii-brand-source.jpg"]["sha256"],
        "",
        "",
    ),
    "RELEASE_NOTES_v6.1.0.md": (
        "",
        "Telegram group",
        "",
        "Official Telegram channel",
    ),
    "scripts/build_windows.py": (
        "Codex-ColdBrew-Studio-v",
        "PyInstaller",
        "coldbrew-codex.ico",
        "review_chain",
        "brain_pack",
        "ishii-brand.png",
        "LICENSE_PATHS",
        "bundled license export",
    ),
    "scripts/release.py": ("Codex-ColdBrew-Studio-v", "brain_pack.py", "ishii-brand-source.jpg", "RELEASE_NOTES_v", "WeChat group QR", "Telegram group", "Official Telegram channel"),
    "studio/coldbrew_studio.py": (
        "TELEGRAM_GROUP_URL",
        "TELEGRAM_CHANNEL_URL",
        "activation_payload",
        "CAPABILITY_SECTIONS",
        "review-self-test",
        "license_payload",
        "查看许可证",
        "公开源码",
    ),
    "studio/coldbrew_activation.py": (CANONICAL_SHA256, 'TRIGGER = "冷咖啡"'),
    "studio/brain_pack.py": ("coldbrew-ishii", "skills/coldbrew-core/SKILL.md", "prompts/coldbrew.md"),
}
README_IMAGE_WIDTHS = {
    "README.md": (
        'alt="QQ群 1057540028" width="360"',
        'alt="QQ群 1077074552" width="360"',
        'alt="微信群：冷咖啡破甲社区二维码" width="320"',
    ),
    "README_EN.md": (
        'alt="QQ 1057540028" width="360"',
        'alt="QQ 1077074552" width="360"',
        'alt="ColdBrew community WeChat group QR code" width="320"',
    ),
}
SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    offset = 2
    while offset + 8 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0x01, 0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            return None
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            return None
        if marker in SOF_MARKERS and length >= 7:
            height = int.from_bytes(data[offset + 3:offset + 5], "big")
            width = int.from_bytes(data[offset + 5:offset + 7], "big")
            return width, height
        offset += length
    return None


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def audit(root: Path) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def record(ok: bool, target: str, detail: str) -> None:
        checks.append({"status": "PASS" if ok else "FAIL", "target": target, "detail": detail})

    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        record(False, "VERSION", f"utf8-read:{exc.__class__.__name__}")
    else:
        record(version == "6.1.0", "VERSION", f"release:{version}")

    record(verify_canonical_contract(), "activation contract", "fixed canonical hash")
    record(activation_sha256() == CANONICAL_SHA256, "activation contract", f"sha256:{activation_sha256()}")
    for accepted in ("冷咖啡", " cold coffee ", "[[ENI:PROFILE=MAX]]"):
        record(activation_payload(accepted)["active"], "activation gate", f"accepted:{accepted!r}")
    for non_startup in ("冰美式", "请输入冷咖啡"):
        record(not activation_payload(non_startup)["active"], "activation gate", f"non-startup:{non_startup!r}")

    for relative, required in TEXT_REQUIREMENTS.items():
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            record(False, relative, f"utf8-read:{exc.__class__.__name__}")
            continue
        record("\ufffd" not in text, relative, "no replacement character")
        record(re.search(r"\?{2,}", text) is None, relative, "no repeated ASCII question marks")
        record("锟斤拷" not in text, relative, "no common mojibake marker")
        for token in required:
            record(str(token) in text, relative, f"contains:{token}")
        for presentation in README_IMAGE_WIDTHS.get(relative, ()):
            record(presentation in text, relative, f"image-presentation:{presentation}")

    metadata_path = root / ".github" / "repository-metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        record(False, ".github/repository-metadata.json", f"parse:{exc.__class__.__name__}")
    else:
        record(metadata.get("description") == EXPECTED_DESCRIPTION, "repository description", "exact UTF-8 source")
        record(metadata.get("homepage") == "https://3641397194-wq.github.io/codex5.6-coldbrew/", "repository homepage", "Pages URL")
        topics = metadata.get("topics", [])
        record(isinstance(topics, list) and "codex" in topics and "coldbrew" in topics, "repository topics", "core topics")

    for relative, expected in GROUP_ASSETS.items():
        try:
            data = (root / relative).read_bytes()
        except OSError as exc:
            record(False, relative, f"read:{exc.__class__.__name__}")
            continue
        digest = hashlib.sha256(data).hexdigest().upper()
        record(digest == expected["sha256"], relative, f"sha256:{digest}")
        record(jpeg_dimensions(data) == expected["size"], relative, f"dimensions:{jpeg_dimensions(data)}")

    for relative, expected in PRODUCT_ASSETS.items():
        try:
            data = (root / relative).read_bytes()
        except OSError as exc:
            record(False, relative, f"read:{exc.__class__.__name__}")
            continue
        digest = hashlib.sha256(data).hexdigest().upper()
        record(digest == expected["sha256"], relative, f"sha256:{digest}")
        record(png_dimensions(data) == expected["size"], relative, f"dimensions:{png_dimensions(data)}")

    for relative, expected in BRAND_ASSETS.items():
        try:
            data = (root / relative).read_bytes()
        except OSError as exc:
            record(False, relative, f"read:{exc.__class__.__name__}")
            continue
        digest = hashlib.sha256(data).hexdigest().upper()
        dimensions = jpeg_dimensions(data) or png_dimensions(data)
        record(digest == expected["sha256"], relative, f"sha256:{digest}")
        record(dimensions == expected["size"], relative, f"dimensions:{dimensions}")

    wrong_telegram = "https://t.me/" + "+4JaWWv6zXtRmMTNl"
    residue: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".py", ".json", ".html", ".css", ".js", ".yml", ".yaml"}:
            try:
                if wrong_telegram in path.read_text(encoding="utf-8"):
                    residue.append(path.relative_to(root).as_posix())
            except (OSError, UnicodeError):
                pass
    record(not residue, "Telegram residue", f"files:{residue}")

    markdown_contract = activation_document(markdown=True)
    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        record(False, "README.md", f"activation-read:{exc.__class__.__name__}")
    else:
        record(markdown_contract in readme, "README.md", "contains complete canonical activation contract")

    try:
        site = (root / "docs" / "index.html").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        record(False, "docs/index.html", f"activation-read:{exc.__class__.__name__}")
    else:
        for token in (TRIGGER, BANNER, TAGLINE, INTRO, TARGET_HEADING, TARGET_PROMPT):
            record(token in site, "docs/index.html", f"activation-token:{token[:28]}")
        for title, body in CAPABILITY_SECTIONS:
            record(title in site and body in site, "docs/index.html", f"activation-section:{title}")

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

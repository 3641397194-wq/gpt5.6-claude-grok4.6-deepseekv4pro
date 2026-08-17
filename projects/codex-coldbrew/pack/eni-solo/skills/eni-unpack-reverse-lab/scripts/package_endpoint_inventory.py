#!/usr/bin/env python3
"""Read-only package endpoint inventory for local Windows audit cases."""
from __future__ import annotations

import argparse
import json
import pathlib
import re


URL = re.compile(rb"https?://[^\x00\s\"<>]{4,300}", re.I)
IP = re.compile(rb"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?")
DOMAIN = re.compile(rb"(?<![A-Za-z0-9.-])(?:[A-Za-z0-9-]{1,63}\.)+(?:com|net|org|cn|io|cc|vip|top|xyz)(?::\d{1,5})?(?![A-Za-z0-9.-])", re.I)
SUFFIXES = {".exe", ".dll", ".txt", ".ini", ".cfg", ".json", ".xml", ".dat"}


def decoded_matches(pattern: re.Pattern[bytes], data: bytes, kind: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in pattern.findall(data):
        result.append({"type": kind, "value": item.decode("ascii", "replace")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only local package endpoint inventory")
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    files: list[dict[str, object]] = []
    all_indicators: set[tuple[str, str]] = set()
    for path in args.root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        indicators = decoded_matches(URL, data, "url") + decoded_matches(IP, data, "ipv4") + decoded_matches(DOMAIN, data, "domain")
        unique = list(dict.fromkeys((item["type"], item["value"]) for item in indicators))
        if unique:
            files.append({"file": str(path), "indicators": [{"type": kind, "value": value} for kind, value in unique]})
            all_indicators.update(unique)
    result = {
        "status": "read_only_package_endpoint_inventory",
        "root": str(args.root),
        "files_scanned": sum(1 for path in args.root.rglob("*") if path.is_file() and path.suffix.lower() in SUFFIXES),
        "files_with_indicators": files,
        "unique_indicators": [{"type": kind, "value": value} for kind, value in sorted(all_indicators)],
        "note": "Raw static indicator scan only; values are leads, not evidence of a live connection or protocol security property.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "indicators": len(all_indicators)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

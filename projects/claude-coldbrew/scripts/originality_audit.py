#!/usr/bin/env python3
"""Measure structural similarity against explicitly supplied reference trees."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".json", ".html", ".css", ".js", ".ps1", ".sh", ".bat", ".yml", ".yaml", ".txt"}
IGNORE_PARTS = {".git", "__pycache__", ".verify-sandbox", "work", "dist", "release"}
SCRUB = re.compile(r"(?im)^(?:\s*(?:#|//|<!--|/\*)\s*)?(?:copyright|license|source|brand|version|claude|coldbrew).*$")


def files(root: Path) -> list[Path]:
    result: list[Path] = []
    if not root.exists():
        return result
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in IGNORE_PARTS for part in relative.parts):
            continue
        result.append(path)
    return sorted(result)


def normalized(path: Path) -> str:
    value = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    value = SCRUB.sub("", value)
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def normalized_lines(path: Path) -> set[str]:
    raw = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    result: set[str] = set()
    for line in raw.splitlines():
        line = SCRUB.sub("", line).strip().casefold()
        line = re.sub(r"\s+", " ", line)
        if len(line) >= 24:
            result.add(line)
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(candidate: Path, reference_roots: list[Path]) -> dict[str, object]:
    candidate_files = files(candidate)
    reference_files = [path for root in reference_roots for path in files(root)]
    reference_norm = [(path, normalized(path), normalized_lines(path), digest(path)) for path in reference_files]
    reference_by_name: dict[str, list[tuple[Path, str, set[str], str]]] = {}
    for item in reference_norm:
        reference_by_name.setdefault(item[0].name.casefold(), []).append(item)
    identical: list[str] = []
    max_overlap = 0.0
    max_block = 0
    max_pair = None
    for path in candidate_files:
        candidate_hash = digest(path)
        candidate_norm = normalized(path)
        candidate_lines = normalized_lines(path)
        # Compare line vocabulary against the union for a fast global signal,
        # then run the more expensive block check only on same-name files.
        same_name = reference_by_name.get(path.name.casefold(), [])
        same_name_lines: set[str] = set()
        for _other, _other_norm, other_lines, _other_hash in same_name:
            same_name_lines.update(other_lines)
        if candidate_lines and same_name_lines:
            overlap = len(candidate_lines & same_name_lines) / len(candidate_lines) * 100
            if overlap > max_overlap:
                max_overlap = overlap
                max_pair = [str(path.relative_to(candidate)), "<same-name-reference-union>"]
        for other, other_norm, other_lines, other_hash in same_name:
            if candidate_hash == other_hash:
                identical.append(str(path.relative_to(candidate)))
            if candidate_norm and other_norm and len(candidate_norm) < 200_000 and len(other_norm) < 200_000:
                block = difflib.SequenceMatcher(None, candidate_norm, other_norm, autojunk=False).find_longest_match(0, len(candidate_norm), 0, len(other_norm)).size
                if block > max_block:
                    max_block = block
    return {
        "candidate_files": len(candidate_files),
        "reference_files": len(reference_files),
        "identical_files": sorted(set(identical)),
        "max_normalized_line_overlap_percent": round(max_overlap, 4),
        "max_overlap_pair": max_pair,
        "longest_common_block_chars": max_block,
        "thresholds": {"identical_files": 0, "line_overlap_percent": 8.0, "longest_common_block_chars": 128},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=Path.cwd())
    parser.add_argument("--reference", type=Path, action="append", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.candidate.resolve(), [path.resolve() for path in args.reference])
    result["result"] = "PASS" if not result["identical_files"] and result["max_normalized_line_overlap_percent"] <= 8 and result["longest_common_block_chars"] <= 128 else "REVIEW"
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

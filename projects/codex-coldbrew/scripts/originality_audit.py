#!/usr/bin/env python3
"""Reproducible source-tree originality audit for Codex ColdBrew Studio."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".bat", ".css", ".html", ".js", ".json", ".md", ".ps1",
    ".py", ".sh", ".toml", ".txt", ".yaml", ".yml",
}
IGNORED_PARTS = {
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".verify-sandbox",
    "__pycache__", "backup", "build", "dist", "release", "work",
}
# These files carry declarations, provenance, or generated release metadata rather
# than product implementation. They remain in the release package but are not used
# to dilute or inflate source-code similarity measurements.
CANDIDATE_EXACT_EXCLUDES = {
    "LICENSE", "LICENSE_POLICY.md", "THIRD_PARTY_NOTICES.md", "PROVENANCE.md",
    "ORIGINALITY_REPORT.md", "SHA256SUMS.txt", "docs/SOURCE_MAP.md",
    "docs/originality-evidence-v6.json",
}
INTERFACE_IDENTIFIERS = {"冷咖啡", "cold coffee"}
MAX_LINE_OVERLAP = 0.12
MAX_COMMON_BLOCK = 12
MAX_IDENTICAL_FILES = 0
MAX_FOREIGN_COPYRIGHT_HEADERS = 0
HEADER_RE = re.compile(r"(?im)^\s*(?:#|//|/\*|\*|;|<!--)?\s*(?:copyright\b|©)\s*.*$")


@dataclass(frozen=True)
class TextArtifact:
    path: str
    digest: str
    text: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_utf8(path: Path) -> str:
    # Reference checkouts occasionally contain legacy-encoded scripts. Decode
    # losslessly enough for structural comparison instead of dropping the file.
    data = path.read_bytes()
    return data.decode("utf-8-sig", errors="replace")


def include_candidate(relative: str) -> bool:
    if relative in CANDIDATE_EXACT_EXCLUDES:
        return False
    # Generated source archives and their checksums are evidence, not source.
    if re.fullmatch(r"Codex-ColdBrew-Studio-v\d+\.\d+\.\d+-Source\.(?:zip|sha256)", relative):
        return False
    return True


def collect_tree(root: Path, *, candidate: bool) -> tuple[TextArtifact, ...]:
    root = root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"Tree is missing, linked, or not a directory: {root}")
    artifacts: list[TextArtifact] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise RuntimeError(f"Tree contains a symbolic link: {root / relative}")
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if candidate and not include_candidate(relative):
            continue
        artifacts.append(TextArtifact(relative, sha256_file(path), read_utf8(path)))
    if not artifacts:
        raise RuntimeError(f"No comparable text/code artifacts found in {root}")
    return tuple(artifacts)


def tree_hash(artifacts: tuple[TextArtifact, ...]) -> str:
    manifest = "".join(f"{item.digest}  {item.path}\n" for item in artifacts).encode("utf-8")
    return sha256_bytes(manifest)


def normalized_line_list(text: str) -> list[str]:
    result: list[str] = []
    for raw in text.splitlines():
        value = unicodedata.normalize("NFKC", raw).casefold()
        for identifier in INTERFACE_IDENTIFIERS:
            value = value.replace(identifier, "<interface>")
        value = re.sub(r"\s+", " ", value).strip(" `#*-|:;")
        if len(value) >= 24:
            result.append(value)
    return result


def normalized_lines(text: str) -> set[str]:
    return set(normalized_line_list(text))


def normalized_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).casefold().replace("\x00", " ")
    for identifier in INTERFACE_IDENTIFIERS:
        value = value.replace(identifier, "<interface>")
    return re.sub(r"\s+", " ", value)


def suffix_automaton(text: str) -> tuple[list[dict[str, int]], list[int], list[int]]:
    transitions: list[dict[str, int]] = [{}]
    lengths = [0]
    links = [-1]
    last = 0
    for character in text:
        current = len(transitions)
        transitions.append({})
        lengths.append(lengths[last] + 1)
        links.append(0)
        parent = last
        while parent >= 0 and character not in transitions[parent]:
            transitions[parent][character] = current
            parent = links[parent]
        if parent < 0:
            links[current] = 0
        else:
            target = transitions[parent][character]
            if lengths[parent] + 1 == lengths[target]:
                links[current] = target
            else:
                clone = len(transitions)
                transitions.append(dict(transitions[target]))
                lengths.append(lengths[target])
                links.append(links[target])
                while parent >= 0 and transitions[parent].get(character) == target:
                    transitions[parent][character] = clone
                    parent = links[parent]
                links[target] = links[current] = clone
        last = current
    return transitions, lengths, links


def longest_common_block(reference: tuple[TextArtifact, ...], candidate: tuple[TextArtifact, ...]) -> int:
    """Return the longest contiguous run of equal normalized lines."""
    best = 0
    for source in reference:
        source_lines = normalized_line_list(source.text)
        for target in candidate:
            target_lines = normalized_line_list(target.text)
            positions: dict[str, list[int]] = {}
            for target_index, target_line in enumerate(target_lines):
                positions.setdefault(target_line, []).append(target_index)
            previous: dict[int, int] = {}
            for index, line in enumerate(source_lines):
                current: dict[int, int] = {}
                for target_index in positions.get(line, []):
                    current[target_index] = previous.get(target_index - 1, 0) + 1
                    best = max(best, current[target_index])
                previous = current
    return best


def foreign_copyright_headers(candidate: tuple[TextArtifact, ...]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for artifact in candidate:
        for match in HEADER_RE.finditer(artifact.text):
            header = re.sub(r"\s+", " ", match.group(0)).strip()
            # Project-owned notices are allowed; any other copyright header needs review.
            if "coldbrew" not in header.casefold() and "tingweiy10" not in header.casefold():
                findings.append({"path": artifact.path, "header": header[:240]})
    return findings


def audit(candidate_root: Path, reference_root: Path) -> dict[str, object]:
    candidate = collect_tree(candidate_root, candidate=True)
    reference = collect_tree(reference_root, candidate=False)
    reference_hashes = {item.digest for item in reference}
    identical = sorted(item.path for item in candidate if item.digest in reference_hashes)
    candidate_lines = set().union(*(normalized_lines(item.text) for item in candidate))
    reference_lines = set().union(*(normalized_lines(item.text) for item in reference))
    overlap = len(candidate_lines & reference_lines) / max(1, len(candidate_lines))
    longest = longest_common_block(reference, candidate)
    headers = foreign_copyright_headers(candidate)
    passed = (
        len(identical) <= MAX_IDENTICAL_FILES
        and overlap <= MAX_LINE_OVERLAP
        and longest <= MAX_COMMON_BLOCK
        and len(headers) <= MAX_FOREIGN_COPYRIGHT_HEADERS
    )
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema": "coldbrew-originality-audit/v2",
        "version": version,
        "candidate": {"root": str(candidate_root.resolve()), "files": len(candidate), "tree_sha256": tree_hash(candidate)},
        "reference": {"root": str(reference_root.resolve()), "files": len(reference), "tree_sha256": tree_hash(reference)},
        "metrics": {
            "identical_files": identical,
            "normalized_candidate_line_overlap": overlap,
            "longest_normalized_common_block_lines": longest,
            "foreign_copyright_headers": headers,
        },
        "thresholds": {
            "max_identical_files": MAX_IDENTICAL_FILES,
            "max_normalized_candidate_line_overlap": MAX_LINE_OVERLAP,
            "max_longest_normalized_common_block_lines": MAX_COMMON_BLOCK,
            "max_foreign_copyright_headers": MAX_FOREIGN_COPYRIGHT_HEADERS,
        },
        "result": "PASS" if passed else "FAIL",
    }


def render_report(evidence: dict[str, object]) -> str:
    candidate = evidence["candidate"]
    reference = evidence["reference"]
    metrics = evidence["metrics"]
    thresholds = evidence["thresholds"]
    return f"""# Originality Audit — v{evidence['version']}

This v6 audit compares the current product candidate tree directly with the
current reference tree. It does not depend on a historical ZIP extraction.
Generated archives, backups, Git metadata, licenses, provenance records and
source-map ledgers are excluded as non-product comparison noise; implementation,
tests, Skills, Pages, workflows and product documentation remain in scope.

## Reproducible Evidence

- Candidate tree: `{candidate['root']}`
- Candidate text/code files: `{candidate['files']}`
- Candidate manifest SHA-256: `{candidate['tree_sha256']}`
- Reference tree: `{reference['root']}`
- Reference text/code files: `{reference['files']}`
- Reference manifest SHA-256: `{reference['tree_sha256']}`
- Machine-readable evidence: [`docs/originality-evidence-v6.json`](docs/originality-evidence-v6.json)

## Results

- Byte-identical candidate files: `{len(metrics['identical_files'])}` / threshold `<= {thresholds['max_identical_files']}`
- Normalized candidate-line overlap: `{metrics['normalized_candidate_line_overlap']:.4%}` / threshold `<= {thresholds['max_normalized_candidate_line_overlap']:.0%}`
- Longest normalized common block: `{metrics['longest_normalized_common_block_lines']}` contiguous lines / threshold `<= {thresholds['max_longest_normalized_common_block_lines']}`
- Foreign copyright headers: `{len(metrics['foreign_copyright_headers'])}` / threshold `<= {thresholds['max_foreign_copyright_headers']}`
- Result: `{evidence['result']}`

The audit intentionally removes the exact `冷咖啡` / `cold coffee` interface
identifiers before normalized text comparison. This narrowly prevents a shared
public activation label from creating a false match; no product code, tests,
page content, workflow, or prompt body is blanket-excluded.

Reference repositories are research inputs only. Their source, prompts, Skills,
tests, visual assets, schemas and release artifacts are not shipped in this
repository or its source archive.
"""


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        candidate = base / "candidate"
        reference = base / "reference"
        candidate.mkdir(); reference.mkdir()
        (candidate / "studio.py").write_text("def owned():\n    return 'coldbrew'\n", encoding="utf-8")
        (reference / "source.py").write_text("def external():\n    return 'reference'\n", encoding="utf-8")
        clean = audit(candidate, reference)
        if clean["result"] != "PASS":
            raise AssertionError("Independent fixture should pass")
        (candidate / "copied.py").write_text((reference / "source.py").read_text(encoding="utf-8"), encoding="utf-8")
        copied = audit(candidate, reference)
        if copied["result"] != "FAIL" or not copied["metrics"]["identical_files"]:
            raise AssertionError("Identical file fixture should fail")
    print("SELF_TEST=PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--json", type=Path, dest="json_path", default=ROOT / "docs/originality-evidence-v6.json")
    parser.add_argument("--report", type=Path, default=ROOT / "ORIGINALITY_REPORT.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.reference is None:
        parser.error("--reference is required unless --self-test is used")
    evidence = audit(args.candidate, args.reference)
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(evidence), encoding="utf-8", newline="\n")
    print(f"CANDIDATE_FILES={evidence['candidate']['files']} SHA256={evidence['candidate']['tree_sha256']}")
    print(f"REFERENCE_FILES={evidence['reference']['files']} SHA256={evidence['reference']['tree_sha256']}")
    print(f"ORIGINALITY_IDENTICAL={len(evidence['metrics']['identical_files'])}")
    print(f"ORIGINALITY_LINE_OVERLAP={evidence['metrics']['normalized_candidate_line_overlap']:.6f}")
    print(f"ORIGINALITY_LONGEST_BLOCK_LINES={evidence['metrics']['longest_normalized_common_block_lines']}")
    print(f"ORIGINALITY_FOREIGN_HEADERS={len(evidence['metrics']['foreign_copyright_headers'])}")
    print(f"ORIGINALITY_AUDIT={evidence['result']}")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

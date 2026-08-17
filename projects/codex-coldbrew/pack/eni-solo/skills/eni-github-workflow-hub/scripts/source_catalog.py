#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def roots(explicit: str | None) -> list[Path]:
    package_or_home = Path(__file__).resolve().parents[3]
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    values = []
    if explicit:
        values.append(Path(explicit))
    if os.environ.get("ENI_UNIFIED_MANIFEST_ROOT"):
        values.append(Path(os.environ["ENI_UNIFIED_MANIFEST_ROOT"]))
    values += [package_or_home / "manifest", package_or_home / "eni-unified/manifest", home / "eni-unified/manifest"]
    result, seen = [], set()
    for value in values:
        value = value.expanduser().resolve()
        key = os.path.normcase(str(value))
        if key not in seen:
            seen.add(key); result.append(value)
    return result


def load(values: list[Path]):
    for root in values:
        allow, fallback = root / "github-workflow-allowlist.json", root / "github-workflow-sources.json"
        selected = allow if allow.is_file() else fallback
        if selected.is_file():
            lock = root / "github-revision-lock.json"
            return json.loads(selected.read_text(encoding="utf-8-sig")), selected, lock if lock.is_file() else None
    raise FileNotFoundError("No catalog in: " + ", ".join(map(str, values)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow"); parser.add_argument("--manifest-root"); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(); searched = roots(args.manifest_root)
    try:
        data, manifest, lock_path = load(searched)
        lock = json.loads(lock_path.read_text(encoding="utf-8-sig")) if lock_path else {}
        revisions = lock.get("sources") or {}; output = []
        for source in data.get("sources") or []:
            if args.workflow and args.workflow not in source.get("workflow_lanes", []):
                continue
            item = dict(source); pinned = revisions.get(source.get("id")) or {}
            item["pinned_commit"] = pinned.get("commit") or source.get("commit")
            item["revision_lock"] = str(lock_path) if lock_path else None
            output.append(item)
        if args.json:
            print(json.dumps({"manifest": str(manifest), "revision_lock": str(lock_path) if lock_path else None, "count": len(output), "sources": output}, ensure_ascii=False, indent=2))
        else:
            for item in output:
                print(f"{item.get('id')}\t{item.get('pinned_commit')}\t{','.join(item.get('workflow_lanes', []))}\t{item.get('repository')}")
        return 0
    except Exception as error:
        print(json.dumps({"error": str(error), "searched": list(map(str, searched))}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a local sandbox / CTF reverse-engineering case workspace."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return value.lower() or "case"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-name", required=True, help="Case folder name, e.g. crackme-01")
    parser.add_argument("--goal", default="local sandbox reverse engineering")
    parser.add_argument("--out", required=True, help="Parent output directory")
    args = parser.parse_args()

    case_dir = Path(args.out) / slugify(args.case_name)
    for sub in ["artifacts", "copies", "triage", "notes", "reports", "tools", "logs", "screenshots"]:
        (case_dir / sub).mkdir(parents=True, exist_ok=True)

    state = {
        "case_name": args.case_name,
        "goal": args.goal,
        "assumption": "local sandbox / CTF / authorized lab",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": "intake",
        "artifacts": [],
        "evidence": [],
        "findings": [],
        "next_steps": [
            "triage artifact",
            "audit local reverse tools",
            "start static analysis",
            "start dynamic analysis in sandbox",
            "write report snapshot",
        ],
    }
    (case_dir / "case.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (case_dir / "notes" / "scratch.md").write_text(
        f"# {args.case_name}\n\nGoal: {args.goal}\n\nAssumption: local sandbox / CTF / authorized lab.\n\n## Notes\n\n",
        encoding="utf-8",
    )
    (case_dir / "reports" / "snapshot.md").write_text(
        f"# Case Snapshot: {args.case_name}\n\n## Goal\n{args.goal}\n\n## Current phase\nIntake\n\n## Evidence\nTBD\n",
        encoding="utf-8",
    )
    print(str(case_dir.resolve()))


if __name__ == "__main__":
    main()

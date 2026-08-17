#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

VERSION = "4.0.0"


def find_manifest(name: str) -> Path:
    package = Path(__file__).resolve().parents[3]
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    for candidate in (package / "manifest" / name, home / "eni-solo" / "manifest" / name):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(name)


def hit(term: str, prompt: str) -> bool:
    term = term.casefold()
    prompt = prompt.casefold()
    if re.fullmatch(r"[a-z0-9-]+", term, re.I) and len(term) <= 4:
        return bool(re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", prompt))
    return term in prompt


def route(prompt: str) -> dict:
    rules = json.loads(find_manifest("routing-rules.json").read_text(encoding="utf-8-sig"))
    workflows = json.loads(find_manifest("workflows.json").read_text(encoding="utf-8-sig"))["workflows"]
    matches = []
    for rule in rules["rules"]:
        hits = [term for term in rule["terms"] if hit(term, prompt)]
        if hits:
            matches.append({**rule, "hits": hits})
    matches.sort(key=lambda x: (-int(x["priority"]), -len(x["hits"]), x["id"]))
    if matches:
        selected = matches[0]
        fallback = False
    else:
        selected = {
            "workflow": rules["default_workflow"],
            "primary_skill": rules["default_skill"],
            "hits": [],
        }
        fallback = True
    workflow = selected["workflow"]
    stages = [str(x) for x in workflows[workflow]["stages"]]
    skill = selected["primary_skill"]
    receipt = f"[石井 ROUTE] workflow={workflow} | stages={'→'.join(stages)} | skill={skill}"
    return {
        "router_version": VERSION,
        "runtime": "eni-solo",
        "persona": "石井",
        "workflow": workflow,
        "stages": stages,
        "skill": skill,
        "matched_terms": selected.get("hits", []),
        "all_matches": [{"workflow": x["workflow"], "hits": x["hits"]} for x in matches],
        "fallback": fallback,
        "route_receipt": receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="eni-solo deterministic single-workflow router")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    value = route(args.prompt)
    print(json.dumps(value, ensure_ascii=False, indent=2) if args.json else value["route_receipt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

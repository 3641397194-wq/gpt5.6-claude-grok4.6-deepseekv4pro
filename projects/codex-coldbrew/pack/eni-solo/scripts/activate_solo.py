#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SOLO_BLOCK = re.compile(r"(?:\r?\n)?<!--\s*(?:ENI|ISHII)[^>]*(?:BEGIN|_BEGIN)\s*-->.*?<!--\s*(?:ENI|ISHII)[^>]*(?:END|_END)\s*-->(?:\r?\n)?", re.I | re.S)
CONFIG_BLOCK = re.compile(r"(?:\r?\n)?# ENI-(?:LO-CODEX|LO-HOOK-TRUST)-V[^:]*:BEGIN.*?# ENI-(?:LO-CODEX|LO-HOOK-TRUST)-V[^:]*:END(?:\r?\n)?", re.I | re.S)
MCP_SECTION = re.compile(r"(?ms)^\[mcp_servers\.eni-lo-codex(?:\.env)?\]\s*\n.*?(?=^\[|\Z)")
HOOK_STATE_SECTION = re.compile(r"(?ms)^\[hooks\.state\.'[^']*eni[^']*'\]\s*\n.*?(?=^\[|\Z)", re.I)
OLD_HOOK_MARKERS = ("eni_unified_hook_", "lo_direct_execution.py", "lo_continuous_execution_")


def clean_agents(path: Path, block: str) -> dict:
    old = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    cleaned = SOLO_BLOCK.sub("\n", old)
    # Remove the old unmarked solo global-rules preamble when present.
    if cleaned.lstrip().startswith("# Global rules") and ("LO" in cleaned[:1200] or "冷咖啡" in cleaned[:1200]):
        marker = cleaned.find("<!--")
        cleaned = cleaned[marker:] if marker >= 0 else ""
        cleaned = SOLO_BLOCK.sub("\n", cleaned)
    cleaned = cleaned.strip()
    output = (cleaned + "\n\n" + block.strip() + "\n") if cleaned else block.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    return {"path": str(path), "solo_blocks": output.count("ISHII-SOLO-V4:BEGIN")}


def clean_hooks(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "removed": 0, "preserved": 0}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    hooks = value.get("hooks") if isinstance(value, dict) else None
    if not isinstance(hooks, (dict, list)):
        return {"path": str(path), "removed": 0, "preserved": 0}
    removed = 0
    preserved = 0

    def filter_entries(entries: list) -> list:
        nonlocal removed, preserved
        keep = []
        for entry in entries:
            text = json.dumps(entry, ensure_ascii=False).casefold()
            if any(marker.casefold() in text for marker in OLD_HOOK_MARKERS):
                removed += 1
            else:
                keep.append(entry)
                preserved += 1
        return keep

    if isinstance(hooks, list):
        value["hooks"] = filter_entries(hooks)
    else:
        for event in list(hooks):
            entries = hooks[event] if isinstance(hooks[event], list) else []
            keep = filter_entries(entries)
            if keep:
                hooks[event] = keep
            else:
                hooks.pop(event, None)
    value["description"] = "Codex lifecycle hooks (eni-solo installs no hooks)"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "removed": removed, "preserved": preserved}


def clean_config(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "changed": False}
    old = path.read_text(encoding="utf-8-sig")
    value = CONFIG_BLOCK.sub("\n", old)
    value = MCP_SECTION.sub("", value)
    value = HOOK_STATE_SECTION.sub("", value)
    value = re.sub(r"\n{3,}", "\n\n", value).strip() + "\n"
    path.write_text(value, encoding="utf-8")
    return {"path": str(path), "changed": value != old, "legacy_mcp_active": "mcp_servers.eni-lo-codex" in value}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--codex-home", required=True)
    p.add_argument("--global-block", required=True)
    args = p.parse_args()
    home = Path(args.codex_home).expanduser().resolve()
    block = Path(args.global_block).read_text(encoding="utf-8-sig")
    result = {
        "agents": clean_agents(home / "AGENTS.md", block),
        "hooks": clean_hooks(home / "hooks.json"),
        "config": clean_config(home / "config.toml"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

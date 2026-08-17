#!/usr/bin/env python3
"""石井 v4 — UserPromptSubmit route injector. Clean. No prompt override."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def emit(value: dict) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")


def install(codex_home: Path) -> int:
    home = codex_home.expanduser().resolve()
    target_dir = home / "hooks"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "ishii_auto_route.py"
    source = Path(__file__).resolve()
    if source != target:
        shutil.copy2(source, target)
    hooks_path = home / "hooks.json"
    if hooks_path.is_file():
        data = json.loads(hooks_path.read_text(encoding="utf-8-sig"))
    else:
        data = {"description": "Codex lifecycle hooks", "hooks": {}}
    if not isinstance(data, dict):
        raise RuntimeError("hooks.json root must be an object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise RuntimeError("hooks field must be an object")
    groups = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(groups, list):
        raise RuntimeError("UserPromptSubmit must be an array")
    command = f'python "{target}"'
    exists = any(
        isinstance(group, dict)
        and any(
            isinstance(handler, dict)
            and (handler.get("commandWindows") == command or handler.get("command") == command)
            for handler in group.get("hooks", [])
        )
        for group in groups
    )
    if not exists:
        groups.append({
            "hooks": [{
                "type": "command",
                "command": command,
                "commandWindows": command,
                "timeout": 15,
            }]
        })
    hooks_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    emit({"installed": True, "hook": str(target), "hooks_json": str(hooks_path), "duplicate_skipped": exists})
    return 0


def run_hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        emit({"continue": True})
        return 0
    prompt = str(payload.get("prompt") or "")
    if not prompt.strip():
        emit({"continue": True})
        return 0
    home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).resolve()
    router = home / "skills" / "eni-unified-router" / "scripts" / "router.py"
    if not router.is_file():
        emit({"continue": True})
        return 0
    try:
        proc = subprocess.run(
            [sys.executable, str(router), "--prompt", prompt, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **os.environ,
                "CODEX_HOME": str(home),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8",
            },
            timeout=10,
        )
    except Exception:
        emit({"continue": True})
        return 0
    if proc.returncode != 0:
        emit({"continue": True})
        return 0
    try:
        route = json.loads(proc.stdout)
    except Exception:
        emit({"continue": True})
        return 0
    workflow = str(route.get("workflow") or "universal")
    skill = str(route.get("skill") or "eni-universal-workflow")
    stages = [str(x) for x in (route.get("stages") or [])]
    route_receipt = f"[ROUTE] workflow={workflow} | stages={'→'.join(stages)} | skill={skill}"
    emit({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": route_receipt,
        },
    })
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--codex-home", type=Path)
    args = parser.parse_args()
    if args.install:
        if args.codex_home is None:
            parser.error("--codex-home is required with --install")
        return install(args.codex_home)
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())

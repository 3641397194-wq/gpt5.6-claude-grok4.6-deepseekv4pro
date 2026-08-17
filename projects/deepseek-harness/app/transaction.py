#!/usr/bin/env python3
"""Reversible filesystem transaction for the DeepSeek Harness adapter."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from profile_engine import compose_prompt

STATE_SCHEMA = 1
MANAGED_KEY = "coldbrew"


class TransactionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Layout:
    home: Path
    config: Path
    prompt: Path
    template: Path
    state: Path

    def as_dict(self) -> dict[str, str]:
        return {name: str(getattr(self, name)) for name in ("home", "config", "prompt", "template", "state")}


def default_home() -> Path:
    configured = os.environ.get("DEEPSEEK_COLDBREW_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".deepseek-harness"


def resolve_layout(home: Path | None = None) -> Layout:
    root = (home or default_home()).expanduser().resolve()
    return Layout(root, root / "config.json", root / "coldbrew/system-prompt.md", root / "coldbrew/harness-template.json", root / ".coldbrew" / "state.json")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def snapshot(path: Path) -> str | None:
    return base64.b64encode(path.read_bytes()).decode("ascii") if path.exists() else None


def restore_snapshot(path: Path, value: str | None) -> None:
    if value is None:
        if path.exists():
            path.unlink()
        return
    write_atomic(path, base64.b64decode(value))


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent.exists()):
        raise TransactionError(f"refusing symlink path: {path}")
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError(f"config must be a UTF-8 JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise TransactionError(f"config must contain an object: {path}")
    return value


def preview(home: Path | None = None, profile: str = "max") -> dict:
    layout = resolve_layout(home)
    config = read_config(layout.config)
    return {
        "action": "preview",
        "profile": profile,
        "layout": layout.as_dict(),
        "managed": layout.state.is_file(),
        "config_exists": layout.config.is_file(),
        "prompt_exists": layout.prompt.is_file(),
        "managed_config": config.get(MANAGED_KEY),
        "prompt_sha256": sha256(compose_prompt(profile).encode("utf-8")),
    }


def deploy(home: Path | None = None, profile: str = "max") -> dict:
    layout = resolve_layout(home)
    config = read_config(layout.config)
    if layout.state.exists():
        state = json.loads(layout.state.read_text(encoding="utf-8"))
        if state.get("schema") != STATE_SCHEMA:
            raise TransactionError("unsupported state schema")
    else:
        state = {
            "schema": STATE_SCHEMA,
            "original": {
                "config": snapshot(layout.config),
                "prompt": snapshot(layout.prompt),
                "template": snapshot(layout.template),
            },
        }
    prompt = compose_prompt(profile).encode("utf-8")
    template_data = {
        "schema": 1,
        "platform": "DeepSeek Harness",
        "profile": profile,
        "system_prompt_file": str(layout.prompt),
        "activation_trigger": "冷咖啡",
        "activation_sha256": "F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246",
    }
    config[MANAGED_KEY] = {
        "owner": "deepseek-harness-coldbrew",
        "profile": profile,
        "system_prompt": str(layout.prompt),
        "session_template": str(layout.template),
    }
    write_atomic(layout.prompt, prompt)
    write_atomic(layout.template, (json.dumps(template_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    write_atomic(layout.config, (json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    state["current"] = {
        "profile": profile,
        "prompt_sha256": sha256(prompt),
        "template_sha256": sha256(layout.template.read_bytes()),
        "config_sha256": sha256(layout.config.read_bytes()),
    }
    write_atomic(layout.state, (json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    result = verify(home)
    result["action"] = "deploy"
    return result


def verify(home: Path | None = None) -> dict:
    layout = resolve_layout(home)
    if not layout.state.is_file():
        raise TransactionError("deployment state is missing")
    state = json.loads(layout.state.read_text(encoding="utf-8"))
    current = state.get("current", {})
    config = read_config(layout.config)
    checks = {
        "state_schema": state.get("schema") == STATE_SCHEMA,
        "managed_key": config.get(MANAGED_KEY, {}).get("owner") == "deepseek-harness-coldbrew",
        "prompt_hash": layout.prompt.is_file() and sha256(layout.prompt.read_bytes()) == current.get("prompt_sha256"),
        "template_hash": layout.template.is_file() and sha256(layout.template.read_bytes()) == current.get("template_sha256"),
        "config_hash": layout.config.is_file() and sha256(layout.config.read_bytes()) == current.get("config_sha256"),
    }
    return {"action": "verify", "ok": all(checks.values()), "checks": checks, "layout": layout.as_dict(), "profile": current.get("profile")}


def restore(home: Path | None = None) -> dict:
    layout = resolve_layout(home)
    if not layout.state.is_file():
        return {"action": "restore", "ok": True, "changed": False, "layout": layout.as_dict()}
    state = json.loads(layout.state.read_text(encoding="utf-8"))
    original = state.get("original", {})
    restore_snapshot(layout.config, original.get("config"))
    restore_snapshot(layout.prompt, original.get("prompt"))
    restore_snapshot(layout.template, original.get("template"))
    layout.state.unlink()
    return {"action": "restore", "ok": True, "changed": True, "layout": layout.as_dict()}

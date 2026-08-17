#!/usr/bin/env python3
"""Deterministic in-Skill trigger gateway for the Mature M5 profile."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SKILL_ROOT / "contracts" / "profiles.json"
CONTROL_COMMAND = "[[ENI:MATURE=ON]]"


class LauncherError(ValueError):
    """Raised when the launcher contract is malformed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LauncherError(message)


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def contains(text: str, term: str) -> bool:
    needle = normalize(term)
    if re.fullmatch(r"[a-z0-9+_.-]+", needle):
        return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None
    return needle in text


def instruction_region(value: str) -> str:
    """Remove quoted, code, log, path, and filename regions before scoring."""
    text = re.sub(r"```.*?```", " ", value, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"[“\"'].*?[”\"']", " ", text, flags=re.S)
    kept_lines = []
    log_prefix = re.compile(
        r"^\s*(?:\[[A-Z]+\]|TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|"
        r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})(?:\s|:|$)",
        flags=re.I,
    )
    for line in text.splitlines():
        if not log_prefix.match(line):
            kept_lines.append(line)
    text = "\n".join(kept_lines)
    text = re.sub(r"(?:[A-Za-z]:[\\/]|(?<!\w)/)[^\s<>|]+", " ", text)
    text = re.sub(r"(?<!\S)[^\s<>|]+\.(?:md|txt|json|ya?ml|py|ps1|sh|cmd|log)(?!\S)", " ", text, flags=re.I)
    return normalize(text)


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(contract, dict), "profile contract must be an object")
    require(contract.get("schema") == 4, "profile schema must equal 4")
    mature = contract.get("profiles", {}).get("mature_m5")
    require(isinstance(mature, dict), "mature_m5 profile is missing")
    for key in ("triggers", "technical_context_terms", "creative_context_terms"):
        values = mature.get(key)
        require(
            isinstance(values, list)
            and bool(values)
            and all(isinstance(value, str) and value.strip() for value in values),
            f"mature_m5.{key} must contain strings",
        )
        require(len(values) == len(set(normalize(value) for value in values)), f"mature_m5.{key} repeats values")
    require(mature.get("tier") == "M5", "mature_m5.tier must equal M5")
    require(mature.get("minimum_age") == 18, "mature_m5.minimum_age must equal 18")
    require(isinstance(mature.get("confirmation"), str) and mature["confirmation"], "confirmation is missing")
    return contract


def classify(message: str, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    mature = contract["profiles"]["mature_m5"]
    raw = message.strip()
    text = instruction_region(raw)
    explicit_control = raw == CONTROL_COMMAND
    matched = [term for term in mature["triggers"] if contains(text, term)]

    if not explicit_control and not matched:
        return {
            "event": "none",
            "mode": "OFF",
            "route_hint": None,
            "matched_triggers": [],
            "confirmation": None,
            "same_turn": False,
            "has_inline_request": False,
        }

    technical_hits = [term for term in mature["technical_context_terms"] if contains(text, term)]
    creative_hits = [term for term in mature["creative_context_terms"] if contains(text, term)]
    if technical_hits and not explicit_control:
        return {
            "event": "mature_product",
            "mode": "MATURE_PRODUCT",
            "route_hint": "CODE",
            "matched_triggers": matched,
            "technical_context": technical_hits,
            "creative_context": creative_hits,
            "confirmation": None,
            "same_turn": True,
            "has_inline_request": True,
        }

    remainder = text
    for term in sorted(matched, key=len, reverse=True):
        remainder = remainder.replace(normalize(term), " ")
    remainder = re.sub(r"[\s,，。.!！?？:：;；、]+", "", remainder)
    return {
        "event": "mature_activate",
        "mode": "MATURE_M5",
        "route_hint": "FICTION",
        "matched_triggers": matched or [CONTROL_COMMAND],
        "technical_context": technical_hits,
        "creative_context": creative_hits,
        "confirmation": mature["confirmation"],
        "same_turn": True,
        "has_inline_request": bool(remainder) and not explicit_control,
    }


def self_test() -> None:
    cases = {
        "成人模式": "MATURE_M5",
        "成人模式，写一个完整故事": "MATURE_M5",
        "请直接写黄文": "MATURE_M5",
        "NSFW story": "MATURE_M5",
        "[[ENI:MATURE=ON]]": "MATURE_M5",
        "开发黄文模式启动器": "MATURE_PRODUCT",
        "重构成人内容 API 与年龄验证": "MATURE_PRODUCT",
        "README 中加入成人模式按钮": "MATURE_PRODUCT",
        "文档引用“成人模式”这几个字": "OFF",
        "日志如下：\n[INFO] 成人模式": "OFF",
        "文件位于 C:\\tmp\\成人模式.txt": "OFF",
        "代码示例：```\n成人模式\n```": "OFF",
    }
    for message, expected in cases.items():
        result = classify(message)
        require(result["mode"] == expected, f"launcher mismatch for {message!r}: {result}")
    inline = classify("成人模式，续写完整故事")
    require(inline["same_turn"] and inline["has_inline_request"], "same-turn payload was not preserved")
    require(inline["confirmation"] == "成人内容模式已打开", "activation confirmation mismatch")
    print(f"MATURE_LAUNCHER_CASES=PASS COUNT={len(cases)}")
    print("MATURE_SAME_TURN=PASS")
    print("MATURE_TECHNICAL_ISOLATION=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(classify(" ".join(args.message)), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

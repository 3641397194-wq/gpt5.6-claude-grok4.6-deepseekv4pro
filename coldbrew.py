#!/usr/bin/env python3
"""ColdBrew Zero: an original, explicit-input prompt workbench."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


ACTIVATION_WORD = "冷咖啡"
CONTROL_WORD = "BREAK//OPEN"


@dataclass(frozen=True)
class Profile:
    name: str
    stages: tuple[str, ...]
    tone: str


PROFILES = {
    "MAX": Profile("MAX", ("OBJECTIVE", "CONTEXT", "OUTPUT", "CHECK"), "直接、完整、可继续"),
    "FOCUS": Profile("FOCUS", ("OBJECTIVE", "OUTPUT"), "短链路、少噪声"),
    "RESEARCH": Profile("RESEARCH", ("OBJECTIVE", "SOURCES", "CHECK"), "证据优先、分层表达"),
}


def compose(prompt: str, profile: Profile) -> str:
    clean = prompt.strip()
    if not clean:
        raise ValueError("prompt 为空")
    stages = " -> ".join(profile.stages)
    return (
        f"{CONTROL_WORD} / {profile.name}\n"
        f"工作链：{stages}\n"
        f"语气：{profile.tone}\n"
        "保持用户目标、格式和完成判据；缺失信息用占位符标记；"
        "先给可执行产物，再列出检查点。\n\n"
        f"用户目标：{clean}"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ColdBrew Zero prompt workbench")
    parser.add_argument("--activate", required=True, help="品牌启动词：冷咖啡")
    parser.add_argument("--profile", default="MAX", choices=sorted(PROFILES))
    parser.add_argument("--prompt", help="显式输入文本；省略时从标准输入读取")
    parser.add_argument("--json", action="store_true", help="输出结构化结果")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.activate != ACTIVATION_WORD:
        print("activation rejected: use 冷咖啡", file=sys.stderr)
        return 2
    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    profile = PROFILES[args.profile]
    try:
        output = compose(prompt, profile)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = {
        "ok": True,
        "activation": ACTIVATION_WORD,
        "control": CONTROL_WORD,
        "profile": profile.name,
        "stages": list(profile.stages),
        "prompt": output,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


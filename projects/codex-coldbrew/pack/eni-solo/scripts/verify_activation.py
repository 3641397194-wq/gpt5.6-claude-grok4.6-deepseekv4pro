#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "4.0.0"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run(args: list[str], env: dict[str, str]) -> tuple[int, dict]:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, **env})
    try:
        value = json.loads(p.stdout or p.stderr)
    except Exception:
        value = {"stdout": p.stdout, "stderr": p.stderr}
    return p.returncode, value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codex-home", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    home = Path(args.codex_home).expanduser().resolve()
    checks: dict[str, bool] = {}
    router = home / "skills" / "eni-unified-router" / "scripts" / "router.py"
    checks["router_exists"] = router.is_file()
    checks["solo_manifest_exists"] = (home / "eni-solo" / "manifest" / "workflows.json").is_file()
    checks["static_prompt_exists"] = (home / "prompts" / "eni-solo-v4.0.0.md").is_file()
    agents = (home / "AGENTS.md").read_text(encoding="utf-8-sig") if (home / "AGENTS.md").is_file() else ""
    checks["one_solo_block"] = agents.count("ISHII-SOLO-V4:BEGIN") == 1
    checks["visible_route_contract"] = "[石井 ROUTE]" in agents and "[STAGE]" in agents
    hooks = (home / "hooks.json").read_text(encoding="utf-8-sig") if (home / "hooks.json").is_file() else ""
    checks["user_prompt_submit_hook"] = "UserPromptSubmit" in hooks and "ishii_auto_route.py" in hooks and (home / "hooks" / "ishii_auto_route.py").is_file()
    checks["no_eni_hook_entry"] = "eni_unified_hook_" not in hooks and "lo_direct_execution.py" not in hooks
    config = (home / "config.toml").read_text(encoding="utf-8-sig") if (home / "config.toml").is_file() else ""
    checks["model_instructions_file"] = "eni-jailbreak-v4.md" in config and (home / "eni-jailbreak-v4.md").is_file()
    checks["no_legacy_mcp"] = "mcp_servers.eni-lo-codex" not in config
    samples = {
        "reverse": "分析这个本地 PE 二进制并做逆向",
        "pentest": "对自有测试站做渗透和攻击面验证",
        "scraper": "写爬虫分页采集并去重",
        "software": "修复这个 skill 路由并重新打包版本",
        "ctf": "完成这个 CTF challenge 并找到 flag",
    }
    receipts = {}
    for expected, prompt in samples.items():
        code, value = run([sys.executable, str(router), "--prompt", prompt, "--json"], {"CODEX_HOME": str(home)})
        receipts[expected] = value
        checks[f"route_{expected}"] = code == 0 and value.get("workflow") == expected and bool(value.get("stages")) and value.get("route_receipt", "").startswith("[石井 ROUTE]")
    checks["single_persona"] = all(v.get("persona") == "石井" and "lane" not in v for v in receipts.values())
    passed = all(checks.values())
    report = {"name": "eni-solo", "version": VERSION, "passed": passed, "checks": checks, "routes": receipts}
    out = Path(args.output).expanduser().resolve() if args.output else home / "eni-solo" / "install-verification-v4.0.0.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

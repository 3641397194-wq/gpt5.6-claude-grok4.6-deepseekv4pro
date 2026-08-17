#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
from pathlib import Path

VERSION = "4.0.0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package-root", default=".")
    ap.add_argument("--output")
    args = ap.parse_args()
    root = Path(args.package_root).expanduser().resolve()
    checks: dict[str, bool] = {}
    failures: list[str] = []
    def check(name: str, ok: bool, detail: str = "") -> None:
        checks[name] = bool(ok)
        if not ok:
            failures.append(name + (": " + detail if detail else ""))

    package = json.loads((root / "manifest/package.json").read_text(encoding="utf-8-sig"))
    check("package_identity", package.get("name") == "eni-solo" and package.get("version") == VERSION)
    check("single_persona", "石井" in str(package.get("persona", "")) and package.get("runtime_roles") == 1)
    check("no_hook_directory", not (root / "hooks").exists())
    check("no_plugin_directory", not (root / "plugins").exists() and not (root / ".agents").exists())
    check("no_parallel_runtime", package.get("parallel_dags") is False and package.get("plugins") is False)
    check("user_prompt_submit_hook", package.get("hooks") is True and (root / "scripts/ishii_auto_route.py").is_file() and "UserPromptSubmit" in (root / "scripts/install.ps1").read_text(encoding="utf-8-sig"))
    check("no_automatic_evolution", package.get("automatic_evolution") is False)
    forbidden_manifests = ["dual-lane-runtime.json", "capability-evolution.json", "workflow-evolution.json", "self-upgrade.json", "workflow-quality.json"]
    check("no_meta_manifests", all(not (root / "manifest" / name).exists() for name in forbidden_manifests))

    workflows = json.loads((root / "manifest/workflows.json").read_text(encoding="utf-8-sig"))
    check("workflow_mode", workflows.get("mode") == "single-sequential")
    check("workflow_count", len(workflows.get("workflows", {})) == 20)
    expected_reverse = ["preserve", "fingerprint", "triage", "map", "static-analysis", "dynamic-analysis", "hypotheses", "verify", "deliver"]
    check("reverse_stage_order", workflows["workflows"].get("reverse", {}).get("stages") == expected_reverse)

    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    nested = [p for p in (root / "skills/eni-ctf-orchestrator").rglob("SKILL.md") if p != root / "skills/eni-ctf-orchestrator/SKILL.md"]
    names = []
    yaml_ok = True
    for path in skill_files:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"(?m)^name:\s*([^\n]+)$", text); d = re.search(r"(?m)^description:\s*([^\n]+)$", text)
        yaml_ok = yaml_ok and bool(m) and bool(d)
        if m:
            names.append(m.group(1).strip().strip("\"'"))
    check("skill_frontmatter", yaml_ok)
    check("unique_skill_names", len(names) == len(set(names)))
    check("ctf_single_entry", not nested and (root / "skills/eni-ctf-orchestrator/SKILL.md").is_file())
    skills_manifest = json.loads((root / "manifest/skills.json").read_text(encoding="utf-8-sig"))
    check("skill_count_manifest", skills_manifest.get("root_skill_count") == len(skill_files))
    check("docs_only_labeled", all("[DOCUMENTATION ONLY]" in (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8-sig", errors="replace")[:1200] for name in skills_manifest.get("documentation_only", [])))

    auth = json.loads((root / "manifest/authorization.json").read_text(encoding="utf-8-sig"))
    check("authorization_three_sentences", len(auth.get("text", [])) == 3)
    agents = (root / "AGENTS.md").read_text(encoding="utf-8-sig")
    check("static_route_contract", agents.count("ISHII-SOLO-V4:BEGIN") == 1 and "[石井 ROUTE]" in agents and "[STAGE]" in agents)
    check("no_hook_contract", "生命周期 Hook" in agents and "UserPromptSubmit" not in agents)

    router = root / "skills/eni-unified-router/scripts/router.py"
    samples = {
        "reverse": "分析本地 PE 二进制并做逆向",
        "pentest": "对自有测试站做渗透和攻击面验证",
        "scraper": "写爬虫分页采集并去重",
        "software": "修复 bug，重新打包并测试软件",
        "ctf": "完成 CTF challenge 并找到 flag",
    }
    route_reports = {}
    for expected, prompt in samples.items():
        p = subprocess.run([sys.executable, str(router), "--prompt", prompt, "--json"], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            report = json.loads(p.stdout)
        except Exception:
            report = {"stdout": p.stdout, "stderr": p.stderr}
        route_reports[expected] = report
        check(f"route_{expected}", p.returncode == 0 and report.get("workflow") == expected and bool(report.get("stages")) and report.get("route_receipt", "").startswith("[石井 ROUTE]"))
    check("route_output_single", all("石井" in str(r.get("persona", "")) and "lane_mode" not in r and "workflow" in r for r in route_reports.values()))

    inventory = root / "manifest/files.csv"
    inventory_ok = inventory.is_file()
    if inventory_ok:
        with inventory.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            path = root / row["path"]
            if not path.is_file() or str(path.stat().st_size) != row["bytes"] or sha256(path) != row["sha256"]:
                inventory_ok = False
                break
    check("file_inventory", inventory_ok)
    passed = not failures
    report = {"name": "eni-solo", "version": VERSION, "passed": passed, "checks": checks, "failures": failures, "routes": route_reports}
    out = Path(args.output).expanduser().resolve() if args.output else root / "manifest/validation.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build an initial eni-reverse-workflow report from triage JSON files."""
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path


def risk_hint(item: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    entropy = item.get("prefix_entropy", 0)
    indicators = item.get("indicators", {})
    magic = ", ".join(item.get("magic_hints", []))
    if entropy >= 7.2:
        reasons.append("high prefix entropy suggests compression, encryption, packing, or dense binary data")
    if indicators.get("urls") or indicators.get("ipv4"):
        reasons.append("network indicators present")
    if indicators.get("suspicious_terms"):
        reasons.append("high-signal API/command strings present")
    if any(x in magic.lower() for x in ["executable", "elf", "mach-o", "dex", "apk"]):
        reasons.append("executable or bytecode artifact")
    if len(reasons) >= 3:
        return "Medium", reasons
    if reasons:
        return "Low/Medium", reasons
    return "Unknown/Low", ["limited evidence from offline triage"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create initial Markdown report from triage JSON")
    parser.add_argument("inputs", nargs="+", help="Triage JSON files or glob patterns")
    parser.add_argument("--out", required=True, help="Output Markdown report")
    parser.add_argument("--title", default="Reverse Engineering Initial Report")
    args = parser.parse_args()

    paths: list[Path] = []
    for p in args.inputs:
        matches = glob.glob(p)
        paths.extend(Path(m).resolve() for m in matches) if matches else paths.append(Path(p).resolve())
    items = [json.loads(p.read_text(encoding="utf-8")) for p in paths]

    lines = [
        f"# {args.title}",
        "",
        f"- Generated UTC: {datetime.now(timezone.utc).isoformat()}",
        "- Current phase: Analysis ? Initial report",
        "- Method: Offline triage; artifacts were not executed.",
        "",
        "## Artifact inventory",
        "| Name | Size | SHA-256 | Type hints | Profiles | Entropy | Risk hint |",
        "|---|---:|---|---|---|---:|---|",
    ]
    finding_id = 1
    finding_lines: list[str] = []
    for item in items:
        risk, reasons = risk_hint(item)
        lines.append(f"| {item.get('name','')} | {item.get('size',0)} | `{item['hashes']['sha256']}` | {', '.join(item.get('magic_hints', []))} | {', '.join(item.get('profiles', []))} | {item.get('prefix_entropy', 0):.3f} | {risk} |")
        finding_lines += [
            f"### F{finding_id}: {item.get('name','artifact')} triage observations",
            f"- Path: `{item.get('path','')}`",
            f"- Evidence: magic={', '.join(item.get('magic_hints', []))}; entropy={item.get('prefix_entropy', 0):.3f}; sha256={item['hashes']['sha256']}",
            f"- Interpretation: {'; '.join(reasons)}.",
            f"- Confidence: Medium for file facts; Low/Medium for behavior until reverse/dynamic validation.",
            "",
        ]
        finding_id += 1

    lines += ["", "## Verified facts", ""] + finding_lines
    lines += [
        "## Indicator summary",
        "",
    ]
    for item in items:
        lines.append(f"### {item.get('name','artifact')}")
        inds = item.get("indicators", {})
        if not inds:
            lines.append("- No high-signal indicators found in extracted strings.")
        for name, vals in inds.items():
            preview = ", ".join(f"`{v}`" for v in vals[:10])
            lines.append(f"- {name}: {preview}")
        lines.append("")

    lines += ["## Local tool recommendations", ""]
    all_tools = []
    all_profiles = []
    for item in items:
        all_tools.extend(item.get("recommended_tools", []))
        all_profiles.extend(item.get("profiles", []))
    all_tools = list(dict.fromkeys(all_tools))
    all_profiles = list(dict.fromkeys(all_profiles))
    lines.append(f"- Suggested profiles: {', '.join(all_profiles) if all_profiles else 'generic'}")
    if all_tools:
        for tool in all_tools:
            lines.append(f"- {tool}")
    else:
        lines.append("- No specific tool recommendation yet.")
    lines.append("")

    lines += [
        "## Recommended next steps",
        "1. Continue static reverse engineering of high-signal strings, imports, entry points, and recommended profiles.",
        "2. Run `tool_audit.py --profile <profile>` to check the local sandbox toolchain before deeper work.",
        "3. Build a function/module map and identify trust boundaries.",
        "4. If the user selects dynamic work, run tracing only inside an isolated lab snapshot.",
        "5. Perform vulnerability-focused review of parser, update, authentication, and unsafe memory paths.",
        "6. Produce a deep reverse report or vulnerability advisory from validated evidence.",
        "",
    ]
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

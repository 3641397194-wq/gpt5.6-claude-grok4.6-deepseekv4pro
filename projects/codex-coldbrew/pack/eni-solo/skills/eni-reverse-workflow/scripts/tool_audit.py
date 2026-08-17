#!/usr/bin/env python3
"""Audit local reverse-engineering tooling and recommend next tools by profile."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

CATALOG = [
    {"name":"Ghidra","repo":"https://github.com/NationalSecurityAgency/ghidra","stars":70306,"profile":["native","firmware","vuln"],"commands":["ghidraRun","analyzeHeadless"],"purpose":"decompilation and SRE projects"},
    {"name":"jadx","repo":"https://github.com/skylot/jadx","stars":49250,"profile":["android","mobile"],"commands":["jadx","jadx-gui"],"purpose":"DEX/APK decompilation"},
    {"name":"x64dbg","repo":"https://github.com/x64dbg/x64dbg","stars":48770,"profile":["windows","dynamic","native"],"commands":["x64dbg","x32dbg"],"purpose":"Windows user-mode debugging"},
    {"name":"Apktool","repo":"https://github.com/iBotPeaches/Apktool","stars":24904,"profile":["android","mobile"],"commands":["apktool"],"purpose":"APK resource and smali analysis"},
    {"name":"radare2","repo":"https://github.com/radareorg/radare2","stars":24225,"profile":["native","firmware"],"commands":["r2","rabin2","rahash2"],"purpose":"CLI reverse engineering framework"},
    {"name":"Frida","repo":"https://github.com/frida/frida","stars":21168,"profile":["dynamic","android","mobile","native"],"commands":["frida","frida-trace"],"purpose":"dynamic instrumentation"},
    {"name":"Binwalk","repo":"https://github.com/ReFirmLabs/binwalk","stars":14083,"profile":["firmware"],"commands":["binwalk"],"purpose":"firmware extraction and carving"},
    {"name":"Detect It Easy","repo":"https://github.com/horsicq/Detect-It-Easy","stars":11062,"profile":["native","triage"],"commands":["diec","die"],"purpose":"file/compiler/packer identification"},
    {"name":"pwndbg","repo":"https://github.com/pwndbg/pwndbg","stars":10609,"profile":["native","dynamic","vuln"],"commands":["gdb"],"purpose":"GDB reverse/debug enhancement"},
    {"name":"YARA","repo":"https://github.com/VirusTotal/yara","stars":9721,"profile":["triage","memory","malware"],"commands":["yara"],"purpose":"pattern matching"},
    {"name":"Unicorn","repo":"https://github.com/unicorn-engine/unicorn","stars":9126,"profile":["emulation","firmware","native"],"commands":["python"],"python_modules":["unicorn"],"purpose":"CPU emulation"},
    {"name":"angr","repo":"https://github.com/angr/angr","stars":8921,"profile":["native","vuln"],"commands":["python"],"python_modules":["angr"],"purpose":"symbolic execution and CFG analysis"},
    {"name":"Capstone","repo":"https://github.com/capstone-engine/capstone","stars":8872,"profile":["native","emulation"],"commands":["python"],"python_modules":["capstone"],"purpose":"disassembly library"},
    {"name":"RetDec","repo":"https://github.com/avast/retdec","stars":8566,"profile":["native"],"commands":["retdec-decompiler"],"purpose":"machine-code decompilation"},
    {"name":"GEF","repo":"https://github.com/hugsy/gef","stars":8251,"profile":["native","dynamic","vuln"],"commands":["gdb"],"purpose":"GDB enhancement"},
    {"name":"AFL++","repo":"https://github.com/AFLplusplus/AFLplusplus","stars":6628,"profile":["vuln","fuzzing"],"commands":["afl-fuzz","afl-clang-fast"],"purpose":"coverage-guided fuzzing"},
    {"name":"syzkaller","repo":"https://github.com/google/syzkaller","stars":6249,"profile":["kernel","vuln","fuzzing"],"commands":["syz-manager"],"purpose":"kernel fuzzing"},
    {"name":"capa","repo":"https://github.com/mandiant/capa","stars":6080,"profile":["triage","native","malware"],"commands":["capa"],"purpose":"capability detection"},
    {"name":"Qiling","repo":"https://github.com/qilingframework/qiling","stars":5986,"profile":["emulation","firmware","native"],"commands":["python"],"python_modules":["qiling"],"purpose":"instrumentable binary emulation"},
    {"name":"LIEF","repo":"https://github.com/lief-project/LIEF","stars":5460,"profile":["native","triage"],"commands":["python"],"python_modules":["lief"],"purpose":"executable format parsing"},
    {"name":"Volatility 3","repo":"https://github.com/volatilityfoundation/volatility3","stars":4223,"profile":["memory"],"commands":["vol","vol.py"],"purpose":"memory forensics"},
    {"name":"FLOSS","repo":"https://github.com/mandiant/flare-floss","stars":4066,"profile":["triage","malware","native"],"commands":["floss"],"purpose":"obfuscated string extraction"},
    {"name":"Rizin","repo":"https://github.com/rizinorg/rizin","stars":3693,"profile":["native","firmware"],"commands":["rizin","rz-bin"],"purpose":"CLI reverse engineering framework"},
]


def check_module(module: str) -> bool:
    try:
        subprocess.run(["python", "-c", f"import {module}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return True
    except Exception:
        return False


def audit(profile: str = "auto") -> dict:
    rows = []
    selected = []
    for item in CATALOG:
        if profile != "auto" and profile not in item["profile"]:
            continue
        found_cmds = [cmd for cmd in item.get("commands", []) if shutil.which(cmd)]
        found_mods = [m for m in item.get("python_modules", []) if check_module(m)]
        installed = bool(found_cmds or found_mods)
        row = dict(item)
        row["installed"] = installed
        row["found_commands"] = found_cmds
        row["found_python_modules"] = found_mods
        rows.append(row)
        selected.append(row)
    installed_count = sum(1 for r in selected if r["installed"])
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "installed_count": installed_count,
        "total_checked": len(selected),
        "tools": sorted(selected, key=lambda x: (-int(x["installed"]), -x["stars"], x["name"].lower())),
        "recommended_missing": [r for r in sorted(selected, key=lambda x: -x["stars"]) if not r["installed"]][:10],
    }


def to_markdown(data: dict) -> str:
    lines = [
        "# Reverse Tool Audit",
        "",
        f"- Generated UTC: {data['generated_utc']}",
        f"- Profile: {data['profile']}",
        f"- Installed: {data['installed_count']} / {data['total_checked']}",
        "",
        "## Detected tools",
        "| Status | Tool | Stars | Purpose | Found | Repo |",
        "|---|---|---:|---|---|---|",
    ]
    for r in data["tools"]:
        status = "installed" if r["installed"] else "missing"
        found = ", ".join(r["found_commands"] + r["found_python_modules"]) or "-"
        lines.append(f"| {status} | {r['name']} | {r['stars']} | {r['purpose']} | {found} | {r['repo']} |")
    lines += ["", "## Recommended missing tools", ""]
    for i, r in enumerate(data["recommended_missing"], 1):
        lines.append(f"{i}. **{r['name']}** ({r['stars']} stars): {r['purpose']} ? {r['repo']}")
    lines += ["", "## Next step", "Run artifact triage first, then install only the missing tools needed for the selected profile.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local high-value reverse-engineering tools")
    parser.add_argument("--profile", default="auto", choices=["auto","triage","native","android","mobile","firmware","dynamic","windows","vuln","fuzzing","memory","emulation","kernel","malware"], help="Tool profile to check")
    parser.add_argument("--out", help="Optional output path (.json or .md)")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()
    data = audit(args.profile)
    rendered = json.dumps(data, indent=2, ensure_ascii=False) if args.json else to_markdown(data)
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        print(out)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

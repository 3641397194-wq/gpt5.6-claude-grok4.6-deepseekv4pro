#!/usr/bin/env python3
"""Audit locally available reverse-engineering tools and recommend high-star tools by profile."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

TOOLS: Dict[str, Dict[str, object]] = {
    "ghidra": {"commands": ["ghidraRun", "analyzeHeadless"], "profiles": ["native", "firmware", "all"], "repo": "https://github.com/NationalSecurityAgency/ghidra", "why": "general decompilation and SRE"},
    "jadx": {"commands": ["jadx", "jadx-gui"], "profiles": ["android", "mobile", "all"], "repo": "https://github.com/skylot/jadx", "why": "DEX/APK decompilation"},
    "apktool": {"commands": ["apktool"], "profiles": ["android", "mobile", "all"], "repo": "https://github.com/iBotPeaches/Apktool", "why": "APK resource decode/rebuild for lab copies"},
    "frida": {"commands": ["frida", "frida-trace", "frida-ps"], "profiles": ["dynamic", "android", "mobile", "native", "all"], "repo": "https://github.com/frida/frida", "why": "runtime instrumentation"},
    "radare2": {"commands": ["r2", "rabin2", "rahash2", "rizin", "rz-bin"], "profiles": ["native", "firmware", "all"], "repo": "https://github.com/radareorg/radare2", "why": "CLI reverse engineering and automation"},
    "cutter": {"commands": ["cutter"], "profiles": ["native", "all"], "repo": "https://github.com/rizinorg/cutter", "why": "GUI reverse engineering"},
    "x64dbg": {"commands": ["x64dbg", "x32dbg"], "profiles": ["windows", "debug", "all"], "repo": "https://github.com/x64dbg/x64dbg", "why": "Windows debugging"},
    "gdb": {"commands": ["gdb"], "profiles": ["debug", "native", "all"], "repo": "https://www.sourceware.org/gdb/", "why": "native debugging"},
    "pwndbg": {"commands": ["pwndbg"], "profiles": ["debug", "ctf", "native", "all"], "repo": "https://github.com/pwndbg/pwndbg", "why": "GDB/LLDB RE helpers"},
    "gef": {"commands": ["gef"], "profiles": ["debug", "ctf", "native", "all"], "repo": "https://github.com/hugsy/gef", "why": "GDB exploit/reverse helpers"},
    "pwntools": {"commands": ["pwn", "checksec"], "profiles": ["ctf", "native", "all"], "repo": "https://github.com/Gallopsled/pwntools", "why": "CTF automation and local process harnesses"},
    "angr": {"commands": ["angr-management"], "profiles": ["ctf", "symbolic", "native", "all"], "repo": "https://github.com/angr/angr", "why": "symbolic execution and path solving"},
    "binwalk": {"commands": ["binwalk"], "profiles": ["firmware", "all"], "repo": "https://github.com/ReFirmLabs/binwalk", "why": "firmware extraction"},
    "capa": {"commands": ["capa"], "profiles": ["malware", "native", "all"], "repo": "https://github.com/mandiant/capa", "why": "capability identification"},
    "volatility3": {"commands": ["vol", "volatility3"], "profiles": ["memory", "forensics", "all"], "repo": "https://github.com/volatilityfoundation/volatility3", "why": "memory forensics"},
    "aflplusplus": {"commands": ["afl-fuzz", "afl-clang-fast"], "profiles": ["fuzz", "native", "all"], "repo": "https://github.com/AFLplusplus/AFLplusplus", "why": "coverage-guided fuzzing in local labs"},
    "qiling": {"commands": ["qiling"], "profiles": ["emulation", "ctf", "native", "all"], "repo": "https://github.com/qilingframework/qiling", "why": "binary emulation and API hooks"},
}


INSTALL_HINTS = {
    "ghidra": {"windows": "winget install NSA.Ghidra or download from https://github.com/NationalSecurityAgency/ghidra/releases", "linux": "Use your distro package manager or download a release from the Ghidra repo", "darwin": "brew install --cask ghidra"},
    "jadx": {"windows": "winget install skylot.jadx or download from https://github.com/skylot/jadx/releases", "linux": "Use distro packages or download jadx release zip", "darwin": "brew install jadx"},
    "apktool": {"windows": "Download apktool wrapper and jar from https://apktool.org", "linux": "Use distro package manager or apktool.org", "darwin": "brew install apktool"},
    "frida": {"windows": "python -m pip install frida-tools", "linux": "python3 -m pip install frida-tools", "darwin": "python3 -m pip install frida-tools"},
    "radare2": {"windows": "winget install radare.radare2", "linux": "Use distro packages or build from https://github.com/radareorg/radare2", "darwin": "brew install radare2"},
    "cutter": {"windows": "Download from https://github.com/rizinorg/cutter/releases", "linux": "Use AppImage/release from rizinorg/cutter", "darwin": "brew install --cask cutter"},
    "x64dbg": {"windows": "Download snapshot from https://github.com/x64dbg/x64dbg/releases", "linux": "Windows-only; use wine or a Windows VM", "darwin": "Windows-only; use a Windows VM"},
    "gdb": {"windows": "Install via MSYS2/MinGW or WSL", "linux": "sudo apt install gdb / sudo dnf install gdb", "darwin": "brew install gdb or use lldb"},
    "pwndbg": {"windows": "Use WSL/Linux or see https://github.com/pwndbg/pwndbg", "linux": "git clone https://github.com/pwndbg/pwndbg && ./setup.sh", "darwin": "Use Linux VM/remote target for best results"},
    "gef": {"windows": "Use WSL/Linux or see https://github.com/hugsy/gef", "linux": "bash -c \"$(curl -fsSL https://gef.blah.cat/sh)\"", "darwin": "Use Linux VM/remote target for best results"},
    "pwntools": {"windows": "Use WSL; python3 -m pip install pwntools", "linux": "python3 -m pip install pwntools", "darwin": "python3 -m pip install pwntools"},
    "angr": {"windows": "Use WSL/Linux recommended; python3 -m pip install angr", "linux": "python3 -m pip install angr", "darwin": "python3 -m pip install angr"},
    "binwalk": {"windows": "Use WSL/Linux recommended", "linux": "Use distro package manager or pipx/pip install binwalk", "darwin": "brew install binwalk"},
    "capa": {"windows": "Download release or python -m pip install flare-capa", "linux": "python3 -m pip install flare-capa", "darwin": "python3 -m pip install flare-capa"},
    "volatility3": {"windows": "python -m pip install volatility3", "linux": "python3 -m pip install volatility3", "darwin": "python3 -m pip install volatility3"},
    "aflplusplus": {"windows": "Use WSL/Linux recommended", "linux": "Use distro packages or build AFLplusplus", "darwin": "brew install afl++"},
    "qiling": {"windows": "python -m pip install qiling", "linux": "python3 -m pip install qiling", "darwin": "python3 -m pip install qiling"},
}


def os_key() -> str:
    name = platform.system().lower()
    if name.startswith("win"):
        return "windows"
    if name == "darwin":
        return "darwin"
    return "linux"

VERSION_ARGS = ["--version", "-version", "-v"]


def command_version(cmd: str) -> str:
    path = shutil.which(cmd)
    if not path:
        return ""
    for arg in VERSION_ARGS:
        try:
            out = subprocess.run([cmd, arg], capture_output=True, text=True, timeout=3)
            text = (out.stdout or out.stderr).strip().splitlines()
            if text:
                return text[0][:160]
        except Exception:
            continue
    return "found"


def audit(profile: str) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for name, meta in TOOLS.items():
        profiles = meta["profiles"]  # type: ignore[index]
        if profile != "all" and profile not in profiles:
            continue
        found = []
        versions = {}
        for cmd in meta["commands"]:  # type: ignore[index]
            path = shutil.which(cmd)
            if path:
                found.append({"command": cmd, "path": path})
                versions[cmd] = command_version(cmd)
        rows.append({
            "tool": name,
            "available": bool(found),
            "found": found,
            "versions": versions,
            "repo": meta["repo"],
            "why": meta["why"],
            "profiles": profiles,
            "install_hint": INSTALL_HINTS.get(name, {}).get(os_key(), "See upstream repository install instructions"),
        })
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "profile": profile, "tools": rows}


def render_markdown(data: Dict[str, object]) -> str:
    lines = [f"# Reverse Tool Audit", "", f"Generated: {data['generated_at']}", f"Profile: {data['profile']}", ""]
    lines += ["## Available", ""]
    available = [t for t in data["tools"] if t["available"]]  # type: ignore[index]
    missing = [t for t in data["tools"] if not t["available"]]  # type: ignore[index]
    if available:
        for t in available:
            paths = ", ".join(f"`{f['command']}` -> `{f['path']}`" for f in t["found"])
            versions = "; ".join(f"{k}: {v}" for k, v in t.get("versions", {}).items())
            lines.append(f"- **{t['tool']}**: {paths}. {versions}")
    else:
        lines.append("No matching tools detected on PATH.")
    lines += ["", "## Recommended missing high-value tools", ""]
    if missing:
        for t in missing:
            lines.append(f"- **{t['tool']}** - {t['why']}. Repo: {t['repo']}. Install hint: {t.get('install_hint', 'See upstream docs')}")
    else:
        lines.append("No missing tools in this profile.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="all", choices=["all", "native", "android", "mobile", "dynamic", "debug", "windows", "ctf", "symbolic", "firmware", "malware", "memory", "forensics", "fuzz", "emulation"])
    parser.add_argument("--out", help="Write Markdown audit to this path")
    parser.add_argument("--json", dest="json_out", help="Write JSON audit to this path")
    args = parser.parse_args()
    data = audit(args.profile)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = render_markdown(data)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(args.out)
    else:
        print(md)


if __name__ == "__main__":
    main()

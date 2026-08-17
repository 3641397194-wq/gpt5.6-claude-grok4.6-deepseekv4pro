#!/usr/bin/env python3
"""Inventory local reverse/unpacking tooling without installing or modifying anything."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path


TOOLS = [
    "ghidraRun.bat", "ghidraRun", "ida64.exe", "ida.exe", "x64dbg.exe", "x32dbg.exe",
    "rizin", "rz-bin", "radare2", "r2", "die.exe", "diec.exe", "upx.exe", "7z.exe",
    "frida-ps", "frida-trace", "yara", "yara64.exe", "dumpbin.exe", "sigcheck.exe", "strings.exe",
]
PACKAGES = ["capstone", "pefile", "frida", "psutil", "yara", "lief", "uncompyle6"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only local reverse-tool inventory")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tools = {name: shutil.which(name) for name in TOOLS}
    packages = {name: bool(importlib.util.find_spec(name)) for name in PACKAGES}
    result = {
        "available_tools": {name: path for name, path in tools.items() if path},
        "missing_tools": [name for name, path in tools.items() if not path],
        "python_packages": packages,
        "note": "Inventory only; no tool installation, upgrade, deletion, or configuration change was performed.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "tool_count": len(result["available_tools"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

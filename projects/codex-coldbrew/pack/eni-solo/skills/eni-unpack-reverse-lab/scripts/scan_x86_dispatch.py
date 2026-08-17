#!/usr/bin/env python3
"""Offline scan of captured executable regions for the observed bounded auth dispatcher."""
from __future__ import annotations

import argparse
import json
import pathlib

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


PATTERN = bytes.fromhex("8d480483f9100f870a040000ff248d")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan runtime-captured x86 code for bounded dispatcher signatures")
    parser.add_argument("capture_dir", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    records = []
    for binary in sorted(args.capture_dir.glob("private_exec_*.bin")):
        data = binary.read_bytes()
        cursor = data.find(PATTERN)
        while cursor >= 0:
            start = max(0, cursor - 96)
            code = data[start: min(len(data), cursor + 192)]
            lines = [
                f"{item.address:08x}: {item.bytes.hex(' '):<24} {item.mnemonic:<7} {item.op_str}"
                for item in disassembler.disasm(code, start)
            ]
            records.append({"file": binary.name, "offset": hex(cursor), "disassembly": lines})
            cursor = data.find(PATTERN, cursor + 1)
    result = {
        "status": "offline_captured_code_dispatch_scan",
        "pattern": PATTERN.hex(),
        "match_count": len(records),
        "matches": records,
        "note": "The scanner reads only previously captured copied-process memory files.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "match_count": len(records)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

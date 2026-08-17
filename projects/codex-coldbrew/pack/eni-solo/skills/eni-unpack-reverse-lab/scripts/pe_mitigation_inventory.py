#!/usr/bin/env python3
"""Read-only PE mitigation and section-permission inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import pefile


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only PE mitigation inventory")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    pe = pefile.PE(str(args.exe), fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG"]])
    value = pe.OPTIONAL_HEADER.DllCharacteristics
    load_config: dict[str, int] = {}
    for entry in getattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG", []):
        structure = entry.struct
        for name in ("SecurityCookie", "SEHandlerCount", "GuardFlags", "GuardCFFunctionCount", "GuardCFCheckFunctionPointer"):
            if hasattr(structure, name):
                load_config[name] = int(getattr(structure, name) or 0)
    sections = []
    for section in pe.sections:
        flags = section.Characteristics
        sections.append({
            "name": section.Name.rstrip(b"\0").decode("ascii", "replace"), "characteristics": hex(flags),
            "read": bool(flags & 0x40000000), "write": bool(flags & 0x80000000), "execute": bool(flags & 0x20000000),
            "raw_size": int(section.SizeOfRawData), "virtual_size": int(section.Misc_VirtualSize),
        })
    result = {
        "status": "read_only_pe_mitigation_inventory", "path": str(args.exe), "sha256": sha256(args.exe),
        "machine": hex(pe.FILE_HEADER.Machine), "optional_header_magic": hex(pe.OPTIONAL_HEADER.Magic),
        "dll_characteristics": hex(value),
        "mitigations": {
            "dynamic_base": bool(value & 0x40), "force_integrity": bool(value & 0x80), "nx_compat": bool(value & 0x100),
            "no_seh": bool(value & 0x400), "guard_cf": bool(value & 0x4000), "high_entropy_va": bool(value & 0x20),
        },
        "load_config": load_config, "sections": sections,
        "note": "PE-header flags describe the supplied file and do not prove all runtime mitigations or protections.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "rwx_sections": sum(1 for item in sections if item["read"] and item["write"] and item["execute"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

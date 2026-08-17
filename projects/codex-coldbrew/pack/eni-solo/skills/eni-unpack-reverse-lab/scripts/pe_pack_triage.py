#!/usr/bin/env python3
"""Read-only PE packing/protection triage with reproducible JSON output."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import struct


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def entropy(data: bytes) -> float | None:
    if not data:
        return None
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    total = len(data)
    return round(-sum((n / total) * math.log2(n / total) for n in counts if n), 4)


def read_at(f, offset: int, length: int) -> bytes:
    f.seek(max(0, offset))
    return f.read(max(0, length))


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only PE packer/protector triage")
    parser.add_argument("artifact", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--sample-bytes", type=int, default=1024 * 1024)
    args = parser.parse_args()

    path = args.artifact.resolve()
    result: dict[str, object] = {
        "artifact": str(path),
        "size": path.stat().st_size,
        "sha256": sha256(path),
        "format": "unknown",
        "pe": {},
        "indicators": [],
        "notes": ["Read-only triage; indicators are leads, not packer attribution proof."],
    }
    with path.open("rb") as f:
        head = read_at(f, 0, 1024 * 1024)
        tail_offset = max(0, path.stat().st_size - 1024 * 1024)
        tail = read_at(f, tail_offset, 1024 * 1024)
        if head[:2] != b"MZ" or len(head) < 0x40:
            result["notes"].append("No DOS MZ header found.")
        else:
            pe_offset = struct.unpack_from("<I", head, 0x3C)[0]
            signature = read_at(f, pe_offset, 4)
            if signature != b"PE\0\0":
                result["notes"].append("DOS header exists but PE signature is absent.")
            else:
                coff = read_at(f, pe_offset + 4, 20)
                machine, sections = struct.unpack_from("<HH", coff, 0)
                optional_size = struct.unpack_from("<H", coff, 16)[0]
                optional = read_at(f, pe_offset + 24, optional_size)
                magic = struct.unpack_from("<H", optional, 0)[0] if len(optional) >= 2 else None
                result["format"] = "PE32+" if magic == 0x20B else "PE32" if magic == 0x10B else "PE"
                pe: dict[str, object] = {"pe_offset": pe_offset, "machine": hex(machine), "sections": []}
                if magic in (0x10B, 0x20B):
                    directory_offset = 112 if magic == 0x20B else 96
                    cli_entry = directory_offset + 14 * 8
                    if len(optional) >= cli_entry + 8:
                        cli_rva, cli_size = struct.unpack_from("<II", optional, cli_entry)
                        pe["dotnet_cli_directory"] = {"rva": hex(cli_rva), "size": cli_size}
                        if cli_rva and cli_size:
                            result["indicators"].append(".NET CLI metadata directory present")
                section_offset = pe_offset + 24 + optional_size
                for index in range(sections):
                    entry = read_at(f, section_offset + index * 40, 40)
                    if len(entry) != 40:
                        break
                    raw_name = entry[:8].split(b"\0", 1)[0]
                    name = raw_name.decode("ascii", "replace")
                    virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from("<IIII", entry, 8)
                    sample = read_at(f, raw_offset, min(raw_size, args.sample_bytes)) if raw_size else b""
                    pe["sections"].append({
                        "name": name,
                        "virtual_size": virtual_size,
                        "virtual_address": hex(virtual_address),
                        "raw_size": raw_size,
                        "raw_offset": hex(raw_offset),
                        "sample_entropy": entropy(sample),
                        "sample_size": len(sample),
                    })
                result["pe"] = pe

    signatures = {
        b"UPX0": "UPX section marker",
        b"UPX1": "UPX section marker",
        b"PyInstaller": "PyInstaller marker",
        b"pyi-windows-manifest-filename": "PyInstaller archive marker",
        b"Nuitka": "Nuitka marker",
        b"VMProtect": "VMProtect text marker",
        b"Themida": "Themida text marker",
        b"Enigma": "Enigma text marker",
        b"MSVBVM60": "Visual Basic runtime marker",
    }
    haystack = head + tail
    for needle, label in signatures.items():
        if needle in haystack:
            result["indicators"].append(label)
    result["indicators"] = sorted(set(result["indicators"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "sha256": result["sha256"], "indicators": result["indicators"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

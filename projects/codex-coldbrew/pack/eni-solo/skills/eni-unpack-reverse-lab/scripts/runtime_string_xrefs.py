#!/usr/bin/env python3
"""Read-only runtime string/xref lookup for a copied x86 Windows process."""
from __future__ import annotations

import argparse
import ctypes
import json
import pathlib
import struct
import subprocess
import time
from ctypes import wintypes

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
OpenProcess = k32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


MEM_COMMIT = 0x1000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010


def read(handle, address: int, size: int) -> bytes:
    buffer = (ctypes.c_ubyte * size)()
    received = ctypes.c_size_t()
    if not ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(received)):
        return b""
    return bytes(buffer[:received.value])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only runtime string/xref scan")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--text", default="卡密长度错误!")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    patterns = {"gbk": args.text.encode("gbk", "replace"), "utf16le": args.text.encode("utf-16le")}
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 0
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(2.5)
    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    regions: list[tuple[int, int, int]] = []
    addresses: list[dict[str, object]] = []
    if handle:
        address = 0x10000
        while address < 0x80000000:
            mbi = MEMORY_BASIC_INFORMATION()
            received = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if not received:
                address += 0x10000
                continue
            base, size = int(mbi.BaseAddress or address), int(mbi.RegionSize)
            protection = int(mbi.Protect)
            readable = (protection & 0xFF) in {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
            if mbi.State == MEM_COMMIT and 0 < size < 0x10000000 and readable:
                data = read(handle, base, size)
                regions.append((base, size, protection))
                for encoding, pattern in patterns.items():
                    offset = data.find(pattern)
                    while offset >= 0:
                        addresses.append({"address": base + offset, "encoding": encoding})
                        offset = data.find(pattern, offset + 1)
            address = base + size if size else address + 0x10000
        for hit in addresses:
            origin = max(0, int(hit["address"]) - 512)
            blob = read(handle, origin, 1536)
            nearby = []
            for part in blob.split(b"\0"):
                if len(part) < 3:
                    continue
                try:
                    value = part.decode("gbk")
                except UnicodeDecodeError:
                    continue
                if len(value) >= 3 and sum(char.isprintable() for char in value) / len(value) > 0.9:
                    nearby.append(value[:240])
            hit["nearby_gbk_strings"] = list(dict.fromkeys(nearby))[:24]
        xrefs = []
        disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
        for hit in addresses:
            needle = struct.pack("<I", int(hit["address"]))
            for base, size, protection in regions:
                if not (protection & 0xF0):
                    continue
                data = read(handle, base, size)
                offset = data.find(needle)
                while offset >= 0:
                    ref = base + offset
                    candidate = None
                    for delta in range(1, 17):
                        start = max(base, ref - delta)
                        decoded = list(disassembler.disasm(read(handle, start, 64), start))
                        for item in decoded:
                            if item.address <= ref < item.address + len(item.bytes):
                                candidate = item
                                break
                        if candidate:
                            break
                    xrefs.append({
                        "string_address": hex(int(hit["address"])), "reference_address": hex(ref),
                        "matched_instruction": (f"{candidate.address:08x}: {candidate.bytes.hex(' '):<24} {candidate.mnemonic:<7} {candidate.op_str}" if candidate else None),
                        "nearby_hex": read(handle, max(base, ref - 16), 48).hex(),
                    })
                    offset = data.find(needle, offset + 1)
        CloseHandle(handle)
    try:
        process.terminate(); process.wait(timeout=1)
    except Exception:
        try: process.kill()
        except Exception: pass
    result = {
        "status": "read_only_runtime_string_xrefs", "pid": process.pid, "text": args.text,
        "string_hits": [{"address": hex(int(item["address"])), "encoding": item["encoding"], "nearby_gbk_strings": item.get("nearby_gbk_strings", [])} for item in addresses],
        "xrefs": xrefs, "exit_after_probe": process.poll(),
        "note": "The scan reads copied-process memory only; it does not send input, modify code, or capture network payloads.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "string_hits": len(addresses), "xrefs": len(xrefs)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

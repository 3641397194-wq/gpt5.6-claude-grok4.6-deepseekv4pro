#!/usr/bin/env python3
"""Read-only inspection of the runtime callee that feeds an auth-status dispatcher.

The script launches a *copied* GUI target hidden, finds the observed x86 status
dispatcher, and follows its immediately preceding indirect-call pointer.  It does
not automate controls, alter memory, inject code, or inspect credentials/payloads.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
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
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


MEM_COMMIT = 0x1000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
DISPATCHER = bytes.fromhex("8d480483f9100f870a040000ff248d")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read(handle: int, address: int, size: int) -> bytes:
    buffer = (ctypes.c_ubyte * size)()
    received = ctypes.c_size_t()
    if not ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(received)):
        return b""
    return bytes(buffer[:received.value])


def query(handle: int, address: int) -> dict[str, object] | None:
    mbi = MBI()
    if not VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        return None
    return {
        "base": hex(int(mbi.BaseAddress or 0)),
        "size": int(mbi.RegionSize),
        "state": hex(int(mbi.State)),
        "protect": hex(int(mbi.Protect)),
        "type": hex(int(mbi.Type)),
    }


def executable_regions(handle: int) -> list[tuple[int, int, int]]:
    regions: list[tuple[int, int, int]] = []
    address = 0x10000
    while address < 0x80000000:
        mbi = MBI()
        received = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not received:
            address += 0x10000
            continue
        base, size, protect = int(mbi.BaseAddress or address), int(mbi.RegionSize), int(mbi.Protect)
        if mbi.State == MEM_COMMIT and 0 < size < 0x10000000 and protect & 0xF0:
            regions.append((base, size, protect))
        address = base + size if size else address + 0x10000
    return regions


def disassemble(data: bytes, address: int, limit: int = 24) -> list[str]:
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    return [f"{item.address:08x}: {item.bytes.hex(' '):<24} {item.mnemonic:<7} {item.op_str}" for item in list(md.disasm(data, address))[:limit]]


def follow_direct_jumps(handle: int, entry: int, depth: int = 5) -> list[dict[str, object]]:
    """Follow only unconditional direct JMP rel8/rel32 stubs; never execute target code."""
    chain: list[dict[str, object]] = []
    current = entry
    for _ in range(depth):
        code = read(handle, current, 32)
        if not code:
            chain.append({"address": hex(current), "error": "unreadable"})
            break
        node: dict[str, object] = {
            "address": hex(current),
            "memory": query(handle, current),
            "disassembly": disassemble(code, current, limit=8),
        }
        target = None
        if len(code) >= 5 and code[0] == 0xE9:
            target = current + 5 + struct.unpack("<i", code[1:5])[0]
            node["direct_jmp_target"] = hex(target)
        elif len(code) >= 2 and code[0] == 0xEB:
            target = current + 2 + struct.unpack("<b", code[1:2])[0]
            node["direct_jmp_target"] = hex(target)
        chain.append(node)
        if target is None or target == current:
            break
        current = target
    return chain


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only auth status-producer surface capture")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--wait", type=float, default=2.8)
    args = parser.parse_args()

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(args.wait)
    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    result: dict[str, object] = {
        "status": "read_only_auth_producer_surface",
        "copy_sha256": sha256(args.exe),
        "pid": process.pid,
        "method": "startup-memory inspection only; no control input, code modification, injection, payload, or credential capture",
        "dispatcher_hits": [],
        "candidate_producer": None,
    }
    try:
        if not handle:
            result["error"] = f"OpenProcess failed: {ctypes.get_last_error()}"
        else:
            hits: list[tuple[int, int, int]] = []
            for base, size, protect in executable_regions(handle):
                data = read(handle, base, size)
                offset = data.find(DISPATCHER)
                while offset >= 0:
                    hits.append((base + offset, base, protect))
                    offset = data.find(DISPATCHER, offset + 1)
            result["dispatcher_hits"] = [
                {"address": hex(hit), "region_base": hex(base), "protection": hex(protect)}
                for hit, base, protect in hits
            ]
            chosen = next((hit for hit, _, protect in reversed(hits) if protect & 0x20), hits[-1][0] if hits else None)
            if chosen is None:
                result["error"] = "status dispatcher pattern not found"
            else:
                # The known dispatcher is immediately preceded by:
                #   mov eax,[absolute_global]; push edi; mov eax,[eax]; call eax
                # Only follow this read-only function-pointer chain; do not invoke it.
                prefix_base = max(0, chosen - 64)
                prefix = read(handle, prefix_base, 64)
                marker = prefix.rfind(b"\xa1")
                global_address = None
                if marker >= 0 and marker + 10 <= len(prefix) and prefix[marker + 5:marker + 10] == b"\x57\x8b\x00\xff\xd0":
                    global_address = struct.unpack("<I", prefix[marker + 1:marker + 5])[0]
                result["chosen_dispatcher"] = hex(chosen)
                result["dispatcher_prefix"] = disassemble(prefix, prefix_base)
                if global_address is None:
                    result["error"] = "indirect producer-call prefix not found near dispatcher"
                else:
                    object_pointer_raw = read(handle, global_address, 4)
                    object_pointer = struct.unpack("<I", object_pointer_raw)[0] if len(object_pointer_raw) == 4 else 0
                    entry_raw = read(handle, object_pointer, 4) if object_pointer else b""
                    entry_pointer = struct.unpack("<I", entry_raw)[0] if len(entry_raw) == 4 else 0
                    entry_bytes = read(handle, entry_pointer, 384) if entry_pointer else b""
                    result["candidate_producer"] = {
                        "global_address": hex(global_address),
                        "object_pointer": hex(object_pointer),
                        "entry_pointer": hex(entry_pointer),
                        "entry_memory": query(handle, entry_pointer) if entry_pointer else None,
                        "direct_jmp_chain": follow_direct_jumps(handle, entry_pointer) if entry_pointer else [],
                        "entry_disassembly": disassemble(entry_bytes, entry_pointer),
                        "note": "This is the runtime indirect-call entry immediately feeding the returned-status dispatcher. Its exact semantic role remains an inference until control-flow is observed during an authorized normal login.",
                    }
    finally:
        if handle:
            CloseHandle(handle)
        try:
            process.terminate()
            process.wait(timeout=1)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
        result["exit_after_probe"] = process.poll()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "dispatchers": len(result["dispatcher_hits"]), "has_candidate": bool(result["candidate_producer"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

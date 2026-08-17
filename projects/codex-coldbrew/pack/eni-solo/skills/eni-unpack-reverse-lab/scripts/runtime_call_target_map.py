#!/usr/bin/env python3
"""Read-only import-call target mapping near a copied runtime auth dispatcher."""
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

import pefile


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
OpenProcess = k32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle
GetMappedFileNameW = psapi.GetMappedFileNameW
GetMappedFileNameW.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPWSTR, wintypes.DWORD]
GetMappedFileNameW.restype = wintypes.DWORD
QueryDosDeviceW = k32.QueryDosDeviceW
QueryDosDeviceW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
QueryDosDeviceW.restype = wintypes.DWORD


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


def mbi_for(handle: int, address: int) -> MBI | None:
    mbi = MBI()
    if not VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        return None
    return mbi


def executable_regions(handle: int) -> list[tuple[int, int, int]]:
    regions: list[tuple[int, int, int]] = []
    address = 0x10000
    while address < 0x80000000:
        mbi = mbi_for(handle, address)
        if not mbi:
            address += 0x10000
            continue
        base, size, protect = int(mbi.BaseAddress or address), int(mbi.RegionSize), int(mbi.Protect)
        if mbi.State == MEM_COMMIT and 0 < size < 0x10000000 and protect & 0xF0:
            regions.append((base, size, protect))
        address = base + size if size else address + 0x10000
    return regions


def device_to_dos(device_path: str) -> str:
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = f"{letter}:"
        buffer = ctypes.create_unicode_buffer(32768)
        if QueryDosDeviceW(drive, buffer, len(buffer)) and device_path.lower().startswith(buffer.value.lower()):
            return drive + device_path[len(buffer.value):]
    return device_path


def mapped_path(handle: int, address: int) -> str | None:
    buffer = ctypes.create_unicode_buffer(32768)
    length = GetMappedFileNameW(handle, ctypes.c_void_p(address), buffer, len(buffer))
    return device_to_dos(buffer.value[:length]) if length else None


def export_name(path: str | None, rva: int | None) -> str | None:
    if not path or rva is None:
        return None
    candidate = pathlib.Path(path)
    if not candidate.exists():
        return None
    try:
        pe = pefile.PE(str(candidate), fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
        for symbol in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", []):
            if symbol.address == rva:
                return symbol.name.decode("ascii", "replace") if symbol.name else f"ordinal_{symbol.ordinal}"
    except Exception:
        return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only auth-adjacent import-call target map")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--before", type=int, default=160)
    parser.add_argument("--after", type=int, default=128)
    parser.add_argument("--anchor-offset", type=lambda value: int(value, 0), default=0, help="Signed offset from the located dispatcher for a read-only call window")
    args = parser.parse_args()

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(2.8)
    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    result: dict[str, object] = {
        "status": "read_only_runtime_call_target_map",
        "copy_sha256": sha256(args.exe),
        "pid": process.pid,
        "method": "copied-process startup memory only; no input, API hooks, code changes, injection, or network payload capture",
        "calls": [],
    }
    try:
        if not handle:
            result["error"] = f"OpenProcess failed: {ctypes.get_last_error()}"
        else:
            hits: list[tuple[int, int]] = []
            for base, size, protect in executable_regions(handle):
                data = read(handle, base, size)
                offset = data.find(DISPATCHER)
                while offset >= 0:
                    hits.append((base + offset, protect))
                    offset = data.find(DISPATCHER, offset + 1)
            chosen = next((address for address, protect in reversed(hits) if protect & 0x20), hits[-1][0] if hits else None)
            result["dispatcher_hits"] = [{"address": hex(address), "protect": hex(protect)} for address, protect in hits]
            result["chosen_dispatcher"] = hex(chosen) if chosen else None
            if chosen is None:
                result["error"] = "dispatcher pattern not found"
            else:
                anchor = chosen + args.anchor_offset
                result["anchor"] = hex(anchor)
                result["anchor_offset"] = args.anchor_offset
                start = anchor - args.before
                window = read(handle, start, args.before + args.after)
                calls: list[dict[str, object]] = []
                offset = 0
                while True:
                    offset = window.find(b"\xff\x15", offset)
                    if offset < 0 or offset + 6 > len(window):
                        break
                    call_address = start + offset
                    slot = struct.unpack("<I", window[offset + 2:offset + 6])[0]
                    raw_target = read(handle, slot, 4)
                    target = struct.unpack("<I", raw_target)[0] if len(raw_target) == 4 else 0
                    mapping = mbi_for(handle, target) if target else None
                    base = int(mapping.AllocationBase or 0) if mapping else 0
                    path = mapped_path(handle, target) if target else None
                    rva = target - base if base and target >= base else None
                    calls.append({
                        "call_address": hex(call_address), "slot": hex(slot), "target": hex(target),
                        "target_memory": ({"base": hex(int(mapping.BaseAddress or 0)), "allocation_base": hex(base), "protect": hex(int(mapping.Protect)), "type": hex(int(mapping.Type))} if mapping else None),
                        "mapped_path": path,
                        "target_rva": hex(rva) if rva is not None else None,
                        "export": export_name(path, rva),
                    })
                    offset += 6
                result["calls"] = calls
                result["window_hex"] = window.hex()
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
    print(json.dumps({"out": str(args.out), "calls": len(result["calls"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

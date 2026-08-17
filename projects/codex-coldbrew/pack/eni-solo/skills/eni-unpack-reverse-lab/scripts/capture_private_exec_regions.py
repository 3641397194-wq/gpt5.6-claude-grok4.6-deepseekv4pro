#!/usr/bin/env python3
"""Capture private executable memory from a copied process, with per-region hashes."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import pathlib
import subprocess
import time
from ctypes import wintypes


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


OpenProcess = k32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
ShowWindow = u32.ShowWindow
EnumWindows = u32.EnumWindows

MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
SW_HIDE = 0


def hide_windows(pid: int) -> None:
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _):
        owner = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            ShowWindow(hwnd, SW_HIDE)
        return True

    EnumWindows(callback, 0)


def read_region(handle, address: int, size: int) -> bytes:
    buffer = (ctypes.c_ubyte * size)()
    read = ctypes.c_size_t()
    if not ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(read)):
        return b""
    return bytes(buffer[:read.value])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only private executable memory capture")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--min-size", type=int, default=65536)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    end = time.time() + args.seconds
    while time.time() < end and process.poll() is None:
        hide_windows(process.pid)
        time.sleep(0.1)

    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    captures: list[dict[str, object]] = []
    if handle:
        address = 0x10000
        index = 0
        while address < 0x80000000:
            mbi = MEMORY_BASIC_INFORMATION()
            returned = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if not returned:
                address += 0x10000
                continue
            base = int(mbi.BaseAddress or address)
            size = int(mbi.RegionSize)
            executable = bool(int(mbi.Protect) & 0xF0)
            if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE and executable and size >= args.min_size:
                data = read_region(handle, base, size)
                filename = f"private_exec_{index:02d}_{base:08X}_{len(data)}.bin"
                path = args.out_dir / filename
                path.write_bytes(data)
                captures.append({
                    "base": hex(base), "size": size, "captured_size": len(data), "protect": hex(int(mbi.Protect)),
                    "file": filename, "sha256": hashlib.sha256(data).hexdigest().upper(),
                })
                index += 1
            address = base + size if size else address + 0x10000
        CloseHandle(handle)
    try:
        process.terminate()
        process.wait(timeout=1)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    manifest = {
        "status": "read_only_runtime_private_exec_capture",
        "pid": process.pid,
        "exit_after_capture": process.poll(),
        "captures": captures,
        "note": "Captured only from a copied process; original artifact and process memory were never modified.",
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out_dir": str(args.out_dir), "capture_count": len(captures)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

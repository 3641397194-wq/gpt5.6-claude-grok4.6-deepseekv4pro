#!/usr/bin/env python3
"""Bounded, read-only executable-memory surface capture for a copied Windows process."""
from __future__ import annotations

import argparse
import ctypes
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
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
ShowWindow = u32.ShowWindow
EnumWindows = u32.EnumWindows

MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PROCESS_QUERY_INFORMATION = 0x0400
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture executable memory regions from a copied process")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--seconds", type=float, default=3.0)
    args = parser.parse_args()

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    end = time.time() + args.seconds
    while time.time() < end and process.poll() is None:
        hide_windows(process.pid)
        time.sleep(0.1)

    handle = OpenProcess(PROCESS_QUERY_INFORMATION, False, process.pid)
    regions: list[dict[str, object]] = []
    if handle:
        address = 0x10000
        while address < 0x80000000:
            mbi = MEMORY_BASIC_INFORMATION()
            returned = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if not returned:
                address += 0x10000
                continue
            base = int(mbi.BaseAddress or address)
            size = int(mbi.RegionSize)
            executable = bool(int(mbi.Protect) & 0xF0)
            if mbi.State == MEM_COMMIT and executable:
                regions.append({
                    "base": hex(base), "allocation_base": hex(int(mbi.AllocationBase or 0)), "size": size,
                    "protect": hex(int(mbi.Protect)), "type": hex(int(mbi.Type)),
                    "private": bool(mbi.Type == MEM_PRIVATE),
                })
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
    result = {
        "status": "bounded_read_only_runtime_surface",
        "pid": process.pid,
        "exit_after_probe": process.poll(),
        "executable_regions": regions,
        "private_executable_region_count": sum(1 for item in regions if item["private"]),
        "note": "No memory write, code patch, file change, or original-artifact execution occurred.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "regions": len(regions), "private_executable": result["private_executable_region_count"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

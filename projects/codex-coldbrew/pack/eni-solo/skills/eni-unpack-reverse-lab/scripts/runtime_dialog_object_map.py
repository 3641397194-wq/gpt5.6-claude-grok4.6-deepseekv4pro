#!/usr/bin/env python3
"""Read-only map from copied dialog controls to nearby runtime object fields.

This checks whether a known edit HWND appears at the +0x44 field used by the
observed GetWindowText helper, and whether neighboring fields resolve to the
same dialog's checkboxes.  It records pointer metadata only, never edit text.
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


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
OpenProcess = k32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle
EnumWindows = u32.EnumWindows
EnumChildWindows = u32.EnumChildWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgCtrlID = u32.GetDlgCtrlID
GetClassNameW = u32.GetClassNameW
ShowWindow = u32.ShowWindow


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
SW_HIDE = 0
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read(handle: int, address: int, size: int) -> bytes:
    buffer = (ctypes.c_ubyte * size)()
    got = ctypes.c_size_t()
    if not ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(got)):
        return b""
    return bytes(buffer[:got.value])


def control_details(hwnd: int, pid: int) -> dict[str, object] | None:
    owner = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    if owner.value != pid:
        return None
    kind = ctypes.create_unicode_buffer(128)
    GetClassNameW(hwnd, kind, len(kind))
    return {"hwnd": hex(hwnd), "id": int(GetDlgCtrlID(hwnd)), "class": kind.value}


def controls_for(pid: int, timeout: float) -> dict[int, dict[str, object]]:
    result: dict[int, dict[str, object]] = {}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not result:
        @CALLBACK
        def top_callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value != pid:
                return True
            ShowWindow(hwnd, SW_HIDE)

            @CALLBACK
            def child_callback(child, __):
                detail = control_details(int(child), pid)
                if detail:
                    result[int(child)] = detail
                return True

            EnumChildWindows(hwnd, child_callback, 0)
            return True

        EnumWindows(top_callback, 0)
        if not result:
            time.sleep(0.1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only copied-dialog runtime object map")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--wait", type=float, default=2.5)
    args = parser.parse_args()

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    controls = controls_for(process.pid, args.wait)
    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    result: dict[str, object] = {
        "status": "read_only_runtime_dialog_object_map",
        "copy_sha256": sha256(args.exe),
        "pid": process.pid,
        "method": "copied-process control handles and pointer metadata only; no edit text, input, injection, or code changes",
        "controls": list(controls.values()),
        "candidates": [],
    }
    try:
        if not handle:
            result["error"] = f"OpenProcess failed: {ctypes.get_last_error()}"
        else:
            edits = [(hwnd, detail) for hwnd, detail in controls.items() if detail["class"] == "Edit"]
            candidates: list[dict[str, object]] = []
            address = 0x10000
            while address < 0x80000000:
                mbi = MBI()
                queried = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
                if not queried:
                    address += 0x10000
                    continue
                base, size, protect = int(mbi.BaseAddress or address), int(mbi.RegionSize), int(mbi.Protect)
                readable = (protect & 0xFF) in {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
                if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE and readable and not (protect & 0x100) and 0 < size < 0x10000000:
                    data = read(handle, base, size)
                    for edit_hwnd, edit_detail in edits:
                        needle = struct.pack("<I", edit_hwnd)
                        offset = data.find(needle)
                        while offset >= 0:
                            field_address = base + offset
                            object_base = field_address - 0x44
                            fields: dict[str, object] = {}
                            same_dialog_buttons = 0
                            for displacement in (0x44, 0x48, 0x4C, 0x50, 0x54, 0x58):
                                raw = read(handle, object_base + displacement, 4)
                                value = struct.unpack("<I", raw)[0] if len(raw) == 4 else 0
                                detail = controls.get(value) or control_details(value, process.pid)
                                fields[f"+0x{displacement:x}"] = detail or {"hwnd": hex(value) if value else None}
                                if detail and detail.get("class") == "Button":
                                    same_dialog_buttons += 1
                            # The observed login object has its login Button at +0x4c.
                            # Requiring that exact control removes shifted false positives
                            # caused by contiguous HWND fields in the object.
                            login_detail = fields.get("+0x4c")
                            if same_dialog_buttons and isinstance(login_detail, dict) and login_detail.get("id") == 1010:
                                candidates.append({
                                    "object_base": hex(object_base), "edit_field_address": hex(field_address),
                                    "source_edit": edit_detail, "fields": fields,
                                })
                            offset = data.find(needle, offset + 1)
                address = base + size if size else address + 0x10000
            # Keep output bounded even if a stale handle value occurs repeatedly in heap memory.
            result["candidates"] = candidates[:200]
            result["candidate_count_unbounded"] = len(candidates)
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
    print(json.dumps({"out": str(args.out), "controls": len(controls), "candidates": len(result["candidates"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

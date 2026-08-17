#!/usr/bin/env python3
"""Compare only private executable code regions before/after a copied GUI click.

No writable data, credentials, request payloads, or responses are read.  The
optional captures are executable pages whose hash changed or appeared after the
click, for offline control-flow analysis only.
"""
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
GetDlgItem = u32.GetDlgItem
ShowWindow = u32.ShowWindow
SetWindowTextW = u32.SetWindowTextW
PostMessageW = u32.PostMessageW
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextW = u32.GetWindowTextW
GetClassNameW = u32.GetClassNameW


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
SW_HIDE = 0
BM_CLICK = 0x00F5
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


def dialog_for(pid: int, timeout: float) -> tuple[int, int, int] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found: list[tuple[int, int, int]] = []

        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                edit, button = GetDlgItem(hwnd, 1008), GetDlgItem(hwnd, 1010)
                if edit and button:
                    found.append((int(hwnd), int(edit), int(button)))
            return True

        EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.1)
    return None


def executable_snapshot(handle: int) -> tuple[dict[tuple[int, int], dict[str, object]], dict[tuple[int, int], bytes]]:
    metadata: dict[tuple[int, int], dict[str, object]] = {}
    contents: dict[tuple[int, int], bytes] = {}
    address = 0x10000
    while address < 0x80000000:
        mbi = MBI()
        queried = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not queried:
            address += 0x10000
            continue
        base, size, protect = int(mbi.BaseAddress or address), int(mbi.RegionSize), int(mbi.Protect)
        if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE and protect & 0xF0 and 0 < size < 0x10000000:
            data = read(handle, base, size)
            if data:
                key = (base, size)
                contents[key] = data
                metadata[key] = {"base": hex(base), "size": size, "protect": hex(protect), "sha256": hashlib.sha256(data).hexdigest()}
        address = base + size if size else address + 0x10000
    return metadata, contents


def non_edit_texts(pid: int) -> list[str]:
    texts: list[str] = []
    @CALLBACK
    def top_callback(hwnd, _):
        owner = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        @CALLBACK
        def child_callback(child, __):
            kind = ctypes.create_unicode_buffer(128)
            GetClassNameW(child, kind, len(kind))
            if kind.value == "Edit":
                return True
            length = GetWindowTextLengthW(child)
            if 0 < length <= 512:
                value = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(child, value, length + 1)
                if value.value:
                    texts.append(value.value)
            return True
        EnumChildWindows(hwnd, child_callback, 0)
        return True
    EnumWindows(top_callback, 0)
    return texts


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied-client private executable-code diff across one synthetic login click")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--capture-dir", type=pathlib.Path, required=True)
    parser.add_argument("--key", default="A" * 32, help="Synthetic placeholder only; never written to output")
    parser.add_argument("--window", type=float, default=3.0)
    args = parser.parse_args()
    if not 32 <= len(args.key) <= 40:
        raise SystemExit("synthetic key length must be 32..40")

    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    dialog = dialog_for(process.pid, 8)
    handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    result: dict[str, object] = {
        "status": "copied_client_private_executable_code_diff", "copy_sha256": sha256(args.exe), "pid": process.pid,
        "method": "private executable-page hashes/captures only; no writable data, credentials, payloads, injection, or code change",
        "synthetic_key_length": len(args.key), "dialog_found": bool(dialog),
    }
    try:
        if not handle or not dialog:
            result["error"] = "process handle or login dialog unavailable"
        else:
            before_meta, _before_bytes = executable_snapshot(handle)
            _root, edit, button = dialog
            SetWindowTextW(edit, args.key)
            result["input_length_after_set"] = GetWindowTextLengthW(edit)
            PostMessageW(button, BM_CLICK, 0, 0)
            deadline = time.monotonic() + args.window
            while time.monotonic() < deadline and process.poll() is None:
                time.sleep(0.15)
            after_meta, after_bytes = executable_snapshot(handle) if process.poll() is None else ({}, {})
            before_keys, after_keys = set(before_meta), set(after_meta)
            changed_keys = [key for key in before_keys & after_keys if before_meta[key]["sha256"] != after_meta[key]["sha256"]]
            capture_keys = sorted((after_keys - before_keys) | set(changed_keys))
            args.capture_dir.mkdir(parents=True, exist_ok=True)
            captures: list[dict[str, object]] = []
            for index, key in enumerate(capture_keys):
                base, size = key
                name = f"exec_after_{index:02d}_{base:08X}_{size}.bin"
                path = args.capture_dir / name
                path.write_bytes(after_bytes[key])
                captures.append({"base": hex(base), "size": size, "path": str(path), "sha256": after_meta[key]["sha256"], "kind": "new" if key not in before_keys else "changed"})
            result.update({
                "private_exec_before": list(before_meta.values()), "private_exec_after": list(after_meta.values()),
                "new_exec_regions": [after_meta[key] for key in sorted(after_keys - before_keys)],
                "changed_exec_regions": [{"before": before_meta[key], "after": after_meta[key]} for key in changed_keys],
                "captures": captures, "non_edit_child_texts": non_edit_texts(process.pid) if process.poll() is None else [],
                "exit_before_cleanup": process.poll(),
            })
    finally:
        if handle:
            CloseHandle(handle)
        try:
            process.terminate(); process.wait(timeout=1)
        except Exception:
            try: process.kill()
            except Exception: pass
        result["exit_after_cleanup"] = process.poll()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "captures": len(result.get("captures", [])), "changed": len(result.get("changed_exec_regions", []))}, ensure_ascii=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bounded copied-GUI control outcome probe without reading Edit text."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import pathlib
import subprocess
import time
from ctypes import wintypes


u32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = u32.EnumWindows
EnumChildWindows = u32.EnumChildWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
ShowWindow = u32.ShowWindow
PostMessageW = u32.PostMessageW
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextW = u32.GetWindowTextW
GetClassNameW = u32.GetClassNameW

SW_HIDE = 0
BM_CLICK = 0x00F5
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def find_control(pid: int, control_id: int, timeout: float) -> tuple[int, int] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        matches: list[tuple[int, int]] = []
        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                control = GetDlgItem(hwnd, control_id)
                if control:
                    matches.append((int(hwnd), int(control)))
            return True
        EnumWindows(callback, 0)
        if matches:
            return matches[0]
        time.sleep(0.1)
    return None


def ui_texts(pid: int) -> tuple[list[str], list[str]]:
    titles: list[str] = []
    children: list[str] = []
    @CALLBACK
    def top_callback(hwnd, _):
        owner = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        ShowWindow(hwnd, SW_HIDE)
        length = GetWindowTextLengthW(hwnd)
        if 0 < length <= 512:
            buffer = ctypes.create_unicode_buffer(length + 1)
            GetWindowTextW(hwnd, buffer, length + 1)
            if buffer.value:
                titles.append(buffer.value)
        @CALLBACK
        def child_callback(child, __):
            kind = ctypes.create_unicode_buffer(128)
            GetClassNameW(child, kind, len(kind))
            if kind.value == "Edit":
                return True
            child_length = GetWindowTextLengthW(child)
            if 0 < child_length <= 512:
                buffer = ctypes.create_unicode_buffer(child_length + 1)
                GetWindowTextW(child, buffer, child_length + 1)
                if buffer.value:
                    children.append(buffer.value)
            return True
        EnumChildWindows(hwnd, child_callback, 0)
        return True
    EnumWindows(top_callback, 0)
    return titles, children


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied GUI control outcome probe")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--control-id", type=int, required=True)
    parser.add_argument("--window", type=float, default=3.0)
    args = parser.parse_args()
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    control = find_control(process.pid, args.control_id, 8)
    if control:
        PostMessageW(control[1], BM_CLICK, 0, 0)
    deadline = time.monotonic() + args.window
    while time.monotonic() < deadline and process.poll() is None:
        time.sleep(0.15)
    titles, children = ui_texts(process.pid) if process.poll() is None else ([], [])
    result = {
        "status": "copied_gui_control_outcome", "copy_sha256": sha256(args.exe), "pid": process.pid,
        "method": "single copied GUI control activation; no Edit text/input, memory read, code change, injection, credential, or payload capture",
        "control_id": args.control_id, "control_found": bool(control), "alive_after_window": process.poll() is None,
        "exit_before_cleanup": process.poll(), "top_titles": titles, "non_edit_child_texts": children,
    }
    try:
        process.terminate(); process.wait(timeout=1)
    except Exception:
        try: process.kill()
        except Exception: pass
    result["exit_after_cleanup"] = process.poll()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "control_found": bool(control), "alive": result["alive_after_window"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

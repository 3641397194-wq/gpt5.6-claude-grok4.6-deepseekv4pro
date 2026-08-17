#!/usr/bin/env python3
"""Read-only layout inventory for a copied login dialog; does not submit input."""
from __future__ import annotations

import argparse
import ctypes
import json
import pathlib
import subprocess
import time
from ctypes import wintypes


u32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = u32.EnumWindows
EnumChildWindows = u32.EnumChildWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgCtrlID = u32.GetDlgCtrlID
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextW = u32.GetWindowTextW
GetClassNameW = u32.GetClassNameW
GetWindowRect = u32.GetWindowRect
ShowWindow = u32.ShowWindow

SW_HIDE = 0
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def text(hwnd) -> str:
    size = GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(size + 1)
    GetWindowTextW(hwnd, buffer, size + 1)
    return buffer.value


def rect(hwnd) -> dict[str, int]:
    value = RECT(); GetWindowRect(hwnd, ctypes.byref(value))
    return {"left": value.left, "top": value.top, "right": value.right, "bottom": value.bottom}


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied login dialog control layout")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    target = None
    end = time.time() + 8
    while time.time() < end:
        candidates = []
        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD(); GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == process.pid:
                ShowWindow(hwnd, SW_HIDE)
                candidates.append(int(hwnd))
            return True
        EnumWindows(callback, 0)
        if candidates:
            target = candidates[0]
            break
        time.sleep(0.1)
    controls = []
    if target:
        @CALLBACK
        def child_callback(hwnd, _):
            class_buffer = ctypes.create_unicode_buffer(128); GetClassNameW(hwnd, class_buffer, len(class_buffer))
            controls.append({"id": int(GetDlgCtrlID(hwnd)), "class": class_buffer.value, "text": text(hwnd), "rect": rect(hwnd)})
            return True
        EnumChildWindows(target, child_callback, 0)
    try:
        process.terminate(); process.wait(timeout=1)
    except Exception:
        try: process.kill()
        except Exception: pass
    result = {"status": "copied_login_control_layout", "pid": process.pid, "dialog_found": bool(target), "controls": controls, "exit_after_probe": process.poll()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "dialog_found": bool(target), "control_count": len(controls)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

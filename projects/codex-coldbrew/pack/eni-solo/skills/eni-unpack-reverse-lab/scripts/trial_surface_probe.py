#!/usr/bin/env python3
"""Bounded copied-client probe of the visible trial entry point."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import pathlib
import subprocess
import time
from ctypes import wintypes


u32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = u32.EnumWindows
EnumChildWindows = u32.EnumChildWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextW = u32.GetWindowTextW
GetClassNameW = u32.GetClassNameW
ShowWindow = u32.ShowWindow
PostMessageW = u32.PostMessageW

SW_HIDE = 0
BM_CLICK = 0x00F5
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def text(hwnd) -> str:
    size = GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(size + 1)
    GetWindowTextW(hwnd, buffer, size + 1)
    return buffer.value


def collect(pid: int) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    @CALLBACK
    def top_callback(hwnd, _):
        owner = wintypes.DWORD(); GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            ShowWindow(hwnd, SW_HIDE)
            children = []
            @CALLBACK
            def child_callback(child, __):
                class_buffer = ctypes.create_unicode_buffer(128); GetClassNameW(child, class_buffer, len(class_buffer))
                if class_buffer.value != "Edit":
                    value = text(child)
                    if value:
                        children.append({"class": class_buffer.value, "text": value})
                return True
            EnumChildWindows(hwnd, child_callback, 0)
            windows.append({"hwnd": int(hwnd), "title": text(hwnd), "trial_control": int(GetDlgItem(hwnd, 1009) or 0), "children": children})
        return True
    EnumWindows(top_callback, 0)
    return windows


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied-client visible trial-entry probe")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--sandbox", type=pathlib.Path, required=True, help="Process-local AppData/Temp root")
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    appdata, localappdata, temp = args.sandbox / "Roaming", args.sandbox / "Local", args.sandbox / "Temp"
    for folder in (appdata, localappdata, temp):
        folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy(); env.update({"APPDATA": str(appdata), "LOCALAPPDATA": str(localappdata), "TEMP": str(temp), "TMP": str(temp)})
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), env=env, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    initial = []
    end = time.time() + 8
    while time.time() < end:
        initial = collect(process.pid)
        matches = [item for item in initial if item["trial_control"]]
        if matches:
            PostMessageW(matches[0]["trial_control"], BM_CLICK, 0, 0)
            break
        time.sleep(0.1)
    trace = []
    end = time.time() + args.seconds
    while time.time() < end and process.poll() is None:
        trace.append(collect(process.pid))
        time.sleep(0.2)
    result = {"status": "copied_trial_entry_probe", "pid": process.pid, "initial": initial, "trace": trace, "exit_before_cleanup": process.poll()}
    try:
        process.terminate(); process.wait(timeout=1)
    except Exception:
        try: process.kill()
        except Exception: pass
    result["exit_after_cleanup"] = process.poll()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "frames": len(trace), "exit": result["exit_before_cleanup"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

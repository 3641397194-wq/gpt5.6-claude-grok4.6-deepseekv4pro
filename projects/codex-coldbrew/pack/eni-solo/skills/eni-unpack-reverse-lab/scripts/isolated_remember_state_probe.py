#!/usr/bin/env python3
"""Bounded copied-client probe for locally persisted card-state artifacts."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import pathlib
import subprocess
import time
from ctypes import wintypes


u32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = u32.EnumWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
ShowWindow = u32.ShowWindow
SetWindowTextW = u32.SetWindowTextW
PostMessageW = u32.PostMessageW

SW_HIDE = 0
BM_CLICK = 0x00F5
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def find_login(pid: int, timeout: float) -> tuple[int, int, int] | None:
    end = time.time() + timeout
    while time.time() < end:
        records: list[tuple[int, int, int]] = []
        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                edit, remember = GetDlgItem(hwnd, 1008), GetDlgItem(hwnd, 1006)
                if edit and remember:
                    records.append((int(hwnd), int(edit), int(remember)))
            return True
        EnumWindows(callback, 0)
        if records:
            return records[0]
        time.sleep(0.1)
    return None


def inventory(root: pathlib.Path, marker: bytes) -> list[dict[str, object]]:
    if not root.exists():
        return []
    results = []
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        results.append({
            "relative_path": str(path.relative_to(root)), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper(), "marker_present": marker in data,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Isolated remembered-card local-state probe")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--sandbox", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    marker = ("R" * 32).encode("ascii")
    appdata = args.sandbox / "AppData" / "Roaming"
    localappdata = args.sandbox / "AppData" / "Local"
    temp = args.sandbox / "Temp"
    for folder in (appdata, localappdata, temp):
        folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"APPDATA": str(appdata), "LOCALAPPDATA": str(localappdata), "TEMP": str(temp), "TMP": str(temp)})
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), env=env, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    login = find_login(process.pid, 8)
    result: dict[str, object] = {"status": "isolated_remember_state_probe", "pid": process.pid, "login_found": bool(login), "marker_length": len(marker)}
    if login:
        _root, edit, remember = login
        SetWindowTextW(edit, marker.decode("ascii"))
        PostMessageW(remember, BM_CLICK, 0, 0)
        end = time.time() + 1.5
        while time.time() < end and process.poll() is None:
            find_login(process.pid, 0.01)
            time.sleep(0.1)
    try:
        process.terminate()
        process.wait(timeout=1)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    result["exit_after_probe"] = process.poll()
    result["sandbox_files"] = inventory(args.sandbox, marker)
    result["copy_files_with_marker"] = [item for item in inventory(args.cwd, marker) if item["marker_present"]]
    result["note"] = "The probe uses a copied process and process-local AppData/Temp variables; it does not log in or send a credential."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "login_found": result["login_found"], "sandbox_files": len(result["sandbox_files"]), "marker_files": len(result["copy_files_with_marker"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

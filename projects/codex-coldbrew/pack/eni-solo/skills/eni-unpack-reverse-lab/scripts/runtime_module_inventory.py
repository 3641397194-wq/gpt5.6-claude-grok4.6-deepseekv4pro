#!/usr/bin/env python3
"""Read-only copied-process module inventory for local loading-surface audits."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import pathlib
import subprocess
import time

import psutil


u32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindows = u32.EnumWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
PostMessageW = u32.PostMessageW
ShowWindow = u32.ShowWindow
CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_ssize_t)
SW_HIDE = 0
BM_CLICK = 0x00F5


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def starts_with(path: str | None, root: pathlib.Path) -> bool:
    if not path:
        return False
    try:
        pathlib.Path(path).resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def click_control(pid: int, control_id: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        controls: list[int] = []
        @CALLBACK
        def callback(hwnd, _):
            owner = ctypes.c_ulong()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                control = GetDlgItem(hwnd, control_id)
                if control:
                    controls.append(int(control))
            return True
        EnumWindows(callback, 0)
        if controls:
            PostMessageW(controls[0], BM_CLICK, 0, 0)
            return True
        time.sleep(0.1)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only copied-process module inventory")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--wait", type=float, default=3.0)
    parser.add_argument("--click-control-id", type=int, help="Optional copied dialog control ID to activate once before inventory")
    args = parser.parse_args()
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 0
    root = args.cwd.resolve()
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    clicked = False
    if args.click_control_id is not None:
        clicked = click_control(process.pid, args.click_control_id, min(args.wait, 2.0))
    time.sleep(max(0.0, args.wait - 2.0 if args.click_control_id is not None else args.wait))
    processes = []
    for candidate in psutil.process_iter(["pid", "name", "exe"]):
        info = candidate.info
        if starts_with(info.get("exe"), root):
            processes.append(candidate)
    result: dict[str, object] = {
        "status": "read_only_runtime_module_inventory", "copy_sha256": sha256(args.exe),
        "method": "copied-process path/module metadata only; no module replacement, injection, code change, input, or payload capture",
        "processes": [], "clicked_control_id": args.click_control_id, "click_posted": clicked,
    }
    try:
        for candidate in processes:
            try:
                maps = candidate.memory_maps(grouped=False)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                maps = []
            module_paths = sorted({item.path for item in maps if item.path and pathlib.Path(item.path).suffix.lower() in {".dll", ".exe"}})
            modules = []
            for module_path in module_paths:
                local = starts_with(module_path, root)
                entry: dict[str, object] = {"path": module_path, "package_local": local}
                if local:
                    try:
                        entry["sha256"] = sha256(pathlib.Path(module_path))
                    except OSError:
                        pass
                modules.append(entry)
            result["processes"].append({"pid": candidate.pid, "name": candidate.name(), "exe": candidate.exe(), "modules": modules})
    finally:
        for candidate in processes:
            try:
                candidate.kill()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        for candidate in processes:
            try:
                candidate.wait(timeout=1)
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
        # Always clean up the exact copied process we launched, even if module
        # enumeration was denied or returned no candidates.
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "processes": len(result["processes"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

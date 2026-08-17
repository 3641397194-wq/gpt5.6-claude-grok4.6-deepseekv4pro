#!/usr/bin/env python3
"""Non-invasive TCP/GUI timeline for one synthetic copied-client login attempt.

This records only TCP endpoint/state metadata associated with the copied target
process.  It intentionally excludes packet contents, credentials, process
memory, code changes, injection, and API hooks.
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

import psutil


u32 = ctypes.WinDLL("user32", use_last_error=True)
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

SW_HIDE = 0
BM_CLICK = 0x00F5
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def login_dialog(pid: int, timeout: float) -> tuple[int, int, int] | None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
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


def tcp_snapshot(pid: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        connections = psutil.net_connections(kind="tcp")
    except Exception as exc:
        return [{"error": str(exc)}]
    for conn in connections:
        if conn.pid != pid:
            continue
        remote = None
        if conn.raddr:
            remote = f"{conn.raddr.ip}:{conn.raddr.port}"
        rows.append({"local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None, "remote": remote, "state": conn.status})
    return sorted(rows, key=lambda row: (str(row.get("remote")), str(row.get("local"))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied-client non-invasive TCP timeline")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--key", default="A" * 32, help="Synthetic placeholder only; never written to output")
    parser.add_argument("--startup-window", type=float, default=2.0)
    parser.add_argument("--post-window", type=float, default=4.0)
    parser.add_argument("--sample-seconds", type=float, default=0.2)
    args = parser.parse_args()
    if not 32 <= len(args.key) <= 40:
        raise SystemExit("synthetic key length must be 32..40")

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    started = time.monotonic()
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    timeline: list[dict[str, object]] = []

    def sample(phase: str) -> None:
        timeline.append({"t_seconds": round(time.monotonic() - started, 3), "phase": phase, "tcp": tcp_snapshot(process.pid)})

    dialog = login_dialog(process.pid, 8)
    deadline = time.monotonic() + args.startup_window
    while time.monotonic() < deadline and process.poll() is None:
        sample("startup")
        time.sleep(args.sample_seconds)

    input_length = None
    if dialog and process.poll() is None:
        _root, edit, button = dialog
        SetWindowTextW(edit, args.key)
        input_length = GetWindowTextLengthW(edit)
        sample("before_click")
        PostMessageW(button, BM_CLICK, 0, 0)
        deadline = time.monotonic() + args.post_window
        while time.monotonic() < deadline and process.poll() is None:
            sample("after_click")
            login_dialog(process.pid, 0.01)
            time.sleep(args.sample_seconds)

    result = {
        "status": "copied_client_tcp_gui_timeline",
        "copy_sha256": sha256(args.exe),
        "pid": process.pid,
        "login_found": bool(dialog),
        "synthetic_key_length": len(args.key),
        "synthetic_key_sha256": hashlib.sha256(args.key.encode("utf-8")).hexdigest(),
        "input_length_after_set": input_length,
        "timeline": timeline,
        "non_edit_child_texts": non_edit_texts(process.pid) if process.poll() is None else [],
        "exit_before_cleanup": process.poll(),
        "note": "TCP endpoint/state metadata only. A connection transition cannot by itself prove whether any application-level request was sent over an existing socket.",
    }
    try:
        process.terminate()
        process.wait(timeout=1)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    result["exit_after_cleanup"] = process.poll()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "samples": len(timeline), "login_found": bool(dialog)}, ensure_ascii=True))


if __name__ == "__main__":
    main()

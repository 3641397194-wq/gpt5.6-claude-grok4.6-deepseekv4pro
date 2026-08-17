#!/usr/bin/env python3
"""Compare copied-process allocation metadata immediately before and after a normal login attempt."""
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
CloseHandle = k32.CloseHandle
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
EnumWindows = u32.EnumWindows
EnumChildWindows = u32.EnumChildWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
ShowWindow = u32.ShowWindow
SetWindowTextW = u32.SetWindowTextW
PostMessageW = u32.PostMessageW
SendMessageTimeoutW = u32.SendMessageTimeoutW
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextLengthA = u32.GetWindowTextLengthA
GetWindowTextW = u32.GetWindowTextW
GetClassNameW = u32.GetClassNameW
SetFocus = u32.SetFocus

PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
SW_HIDE = 0
BM_CLICK = 0x00F5
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SETFOCUS = 0x0007
SMTO_ABORTIFHUNG = 0x0002
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t, wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
SendMessageTimeoutW.restype = wintypes.LPARAM


def login_dialog(pid: int, timeout: float) -> tuple[int, int, int] | None:
    end = time.time() + timeout
    while time.time() < end:
        matches: list[tuple[int, int, int]] = []
        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                edit, login = GetDlgItem(hwnd, 1008), GetDlgItem(hwnd, 1010)
                if edit and login:
                    matches.append((int(hwnd), int(edit), int(login)))
            return True
        EnumWindows(callback, 0)
        if matches:
            return matches[0]
        time.sleep(0.1)
    return None


def snapshot(pid: int) -> list[dict[str, object]]:
    handle = OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        return []
    result = []
    address = 0x10000
    while address < 0x80000000:
        mbi = MEMORY_BASIC_INFORMATION()
        received = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not received:
            address += 0x10000
            continue
        base, size = int(mbi.BaseAddress or address), int(mbi.RegionSize)
        if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE:
            result.append({"base": hex(base), "allocation_base": hex(int(mbi.AllocationBase or 0)), "size": size, "protect": hex(int(mbi.Protect))})
        address = base + size if size else address + 0x10000
    CloseHandle(handle)
    return result


def window_titles(pid: int) -> list[str]:
    titles: list[str] = []
    @CALLBACK
    def callback(hwnd, _):
        owner = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            ShowWindow(hwnd, SW_HIDE)
            size = GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(size + 1)
            GetWindowTextW(hwnd, buffer, size + 1)
            if buffer.value:
                titles.append(buffer.value)
        return True
    EnumWindows(callback, 0)
    return titles


def message_texts(pid: int) -> list[str]:
    messages: list[str] = []
    @CALLBACK
    def top_callback(hwnd, _):
        owner = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        @CALLBACK
        def child_callback(child, __):
            class_buffer = ctypes.create_unicode_buffer(128)
            GetClassNameW(child, class_buffer, len(class_buffer))
            # Never collect text from Edit controls (they can contain user credentials).
            if class_buffer.value == "Edit":
                return True
            size = GetWindowTextLengthW(child)
            if size:
                buffer = ctypes.create_unicode_buffer(size + 1)
                GetWindowTextW(child, buffer, size + 1)
                if buffer.value and len(buffer.value) <= 512:
                    messages.append(buffer.value)
            return True
        EnumChildWindows(hwnd, child_callback, 0)
        return True
    EnumWindows(top_callback, 0)
    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied-client pre/post-login allocation metadata diff")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--key", default="1" * 32)
    parser.add_argument("--extra-edit-id", action="append", type=int, default=[], help="Additional copied dialog Edit control IDs to receive the same synthetic placeholder")
    parser.add_argument("--window", type=float, default=2.0, help="Post-click observation window in seconds")
    parser.add_argument("--input-settle", type=float, default=0.25, help="Delay after setting copied-process input before clicking login")
    parser.add_argument("--input-method", choices=("set", "char", "keyevents"), default="set", help="Normal GUI input delivery mode for the copied process")
    parser.add_argument("--no-click", action="store_true", help="Record copied control lengths after input without activating login")
    args = parser.parse_args()
    if not 32 <= len(args.key) <= 40:
        raise SystemExit("key length must be 32..40")
    si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    dialog = login_dialog(process.pid, 8)
    before = snapshot(process.pid) if dialog else []
    after = []
    extra_input_lengths: dict[str, int | None] = {}
    extra_input_ansi_lengths: dict[str, int | None] = {}
    if dialog:
        _root, edit, button = dialog
        if args.input_method == "set":
            SetWindowTextW(edit, args.key)
            for control_id in args.extra_edit_id:
                extra = GetDlgItem(_root, control_id)
                if extra:
                    SetWindowTextW(extra, args.key)
                    extra_input_lengths[str(control_id)] = GetWindowTextLengthW(extra)
                    extra_input_ansi_lengths[str(control_id)] = GetWindowTextLengthA(extra)
                else:
                    extra_input_lengths[str(control_id)] = None
                    extra_input_ansi_lengths[str(control_id)] = None
        elif args.input_method == "char":
            SetWindowTextW(edit, "")
            for character in args.key:
                result_code = ctypes.c_size_t()
                SendMessageTimeoutW(edit, WM_CHAR, ord(character), 0, SMTO_ABORTIFHUNG, 1000, ctypes.byref(result_code))
                time.sleep(0.01)
        else:
            # Simulate only ordinary edit-control key messages within the copied GUI.
            # No global SendInput is used, so the user's desktop/input focus is untouched.
            SetWindowTextW(edit, "")
            SetFocus(edit)
            PostMessageW(edit, WM_SETFOCUS, 0, 0)
            for character in args.key:
                virtual_key = ord(character.upper()) if character.isalpha() else ord(character)
                PostMessageW(edit, WM_KEYDOWN, virtual_key, 0)
                result_code = ctypes.c_size_t()
                SendMessageTimeoutW(edit, WM_CHAR, ord(character), 0, SMTO_ABORTIFHUNG, 1000, ctypes.byref(result_code))
                PostMessageW(edit, WM_KEYUP, virtual_key, 0)
                time.sleep(0.01)
        time.sleep(args.input_settle)
        input_length_after_set = GetWindowTextLengthW(edit)
        input_ansi_length_after_set = GetWindowTextLengthA(edit)
        if not args.no_click:
            PostMessageW(button, BM_CLICK, 0, 0)
            end = time.time() + args.window
            while time.time() < end:
                if process.poll() is not None:
                    break
                login_dialog(process.pid, 0.01)
                time.sleep(0.2)
        if process.poll() is None:
            after = snapshot(process.pid)
    before_set = {(x["base"], x["size"], x["protect"]) for x in before}
    after_set = {(x["base"], x["size"], x["protect"]) for x in after}
    result = {
        "status": "copied_client_pre_post_login_memory_metadata",
        "pid": process.pid, "login_found": bool(dialog), "key_length": len(args.key), "window_seconds": args.window, "input_method": args.input_method,
        "input_length_after_set": input_length_after_set if dialog else None,
        "input_ansi_length_after_set": input_ansi_length_after_set if dialog else None,
        "extra_input_lengths_after_set": extra_input_lengths,
        "extra_input_ansi_lengths_after_set": extra_input_ansi_lengths,
        "login_clicked": not args.no_click,
        "alive_after_window": process.poll() is None, "exit_before_cleanup": process.poll(),
        "private_regions_before": len(before), "private_regions_after": len(after),
        "new_region_metadata": [dict(base=x[0], size=x[1], protect=x[2]) for x in sorted(after_set - before_set)],
        "removed_region_metadata": [dict(base=x[0], size=x[1], protect=x[2]) for x in sorted(before_set - after_set)],
        "top_window_titles_before_cleanup": window_titles(process.pid) if process.poll() is None else [],
        "non_edit_child_texts_before_cleanup": message_texts(process.pid) if process.poll() is None else [],
        "note": "Only allocation metadata is collected; request/response memory, payloads, and credentials are not read.",
    }
    try:
        process.terminate(); process.wait(timeout=1)
    except Exception:
        try: process.kill()
        except Exception: pass
    result["exit_after_cleanup"] = process.poll()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "login_found": result["login_found"], "new_regions": len(result["new_region_metadata"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

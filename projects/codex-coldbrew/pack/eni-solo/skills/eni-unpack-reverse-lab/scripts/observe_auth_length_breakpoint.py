#!/usr/bin/env python3
"""Copied-process hardware-breakpoint observation of the auth length comparison.

This performs no code patching or memory writing.  It temporarily attaches as a
debugger to a copied 32-bit process, places an execution breakpoint on the
already observed `cmp eax, 0x20`, and records only EIP/EAX if the path executes.
It is bounded, hidden, and cleans up the copied process afterwards.
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
OpenThread = k32.OpenThread
OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenThread.restype = wintypes.HANDLE
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.restype = ctypes.c_size_t
CloseHandle = k32.CloseHandle
DebugActiveProcess = k32.DebugActiveProcess
DebugActiveProcess.argtypes = [wintypes.DWORD]
DebugActiveProcess.restype = wintypes.BOOL
DebugActiveProcessStop = k32.DebugActiveProcessStop
DebugActiveProcessStop.argtypes = [wintypes.DWORD]
DebugActiveProcessStop.restype = wintypes.BOOL
WaitForDebugEvent = k32.WaitForDebugEvent
ContinueDebugEvent = k32.ContinueDebugEvent
Wow64GetThreadContext = k32.Wow64GetThreadContext
Wow64SetThreadContext = k32.Wow64SetThreadContext
EnumWindows = u32.EnumWindows
GetWindowThreadProcessId = u32.GetWindowThreadProcessId
GetDlgItem = u32.GetDlgItem
ShowWindow = u32.ShowWindow
SetWindowTextW = u32.SetWindowTextW
GetWindowTextLengthW = u32.GetWindowTextLengthW
GetWindowTextLengthA = u32.GetWindowTextLengthA
PostMessageW = u32.PostMessageW


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


class FLOATING_SAVE_AREA(ctypes.Structure):
    _fields_ = [
        ("ControlWord", wintypes.DWORD), ("StatusWord", wintypes.DWORD), ("TagWord", wintypes.DWORD),
        ("ErrorOffset", wintypes.DWORD), ("ErrorSelector", wintypes.DWORD), ("DataOffset", wintypes.DWORD),
        ("DataSelector", wintypes.DWORD), ("RegisterArea", ctypes.c_byte * 80), ("Cr0NpxState", wintypes.DWORD),
    ]


class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [
        ("ContextFlags", wintypes.DWORD),
        ("Dr0", wintypes.DWORD), ("Dr1", wintypes.DWORD), ("Dr2", wintypes.DWORD), ("Dr3", wintypes.DWORD), ("Dr6", wintypes.DWORD), ("Dr7", wintypes.DWORD),
        ("FloatSave", FLOATING_SAVE_AREA),
        ("SegGs", wintypes.DWORD), ("SegFs", wintypes.DWORD), ("SegEs", wintypes.DWORD), ("SegDs", wintypes.DWORD),
        ("Edi", wintypes.DWORD), ("Esi", wintypes.DWORD), ("Ebx", wintypes.DWORD), ("Edx", wintypes.DWORD),
        ("Ecx", wintypes.DWORD), ("Eax", wintypes.DWORD), ("Ebp", wintypes.DWORD), ("Eip", wintypes.DWORD),
        ("SegCs", wintypes.DWORD), ("EFlags", wintypes.DWORD), ("Esp", wintypes.DWORD), ("SegSs", wintypes.DWORD),
        ("ExtendedRegisters", ctypes.c_byte * 512),
    ]


class EXCEPTION_RECORD(ctypes.Structure):
    _fields_ = [
        ("ExceptionCode", wintypes.DWORD), ("ExceptionFlags", wintypes.DWORD), ("ExceptionRecord", ctypes.c_void_p),
        ("ExceptionAddress", ctypes.c_void_p), ("NumberParameters", wintypes.DWORD), ("ExceptionInformation", ctypes.c_size_t * 15),
    ]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("ExceptionRecord", EXCEPTION_RECORD), ("dwFirstChance", wintypes.DWORD)]


class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [
        ("hFile", wintypes.HANDLE), ("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
        ("lpBaseOfImage", ctypes.c_void_p), ("dwDebugInfoFileOffset", wintypes.DWORD), ("nDebugInfoSize", wintypes.DWORD),
        ("lpThreadLocalBase", ctypes.c_void_p), ("lpStartAddress", ctypes.c_void_p), ("lpImageName", ctypes.c_void_p), ("fUnicode", wintypes.WORD),
    ]


class CREATE_THREAD_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("hThread", wintypes.HANDLE), ("lpThreadLocalBase", ctypes.c_void_p), ("lpStartAddress", ctypes.c_void_p)]


class DEBUG_EVENT_UNION(ctypes.Union):
    _fields_ = [
        ("Exception", EXCEPTION_DEBUG_INFO), ("CreateProcessInfo", CREATE_PROCESS_DEBUG_INFO),
        ("CreateThread", CREATE_THREAD_DEBUG_INFO), ("raw", ctypes.c_byte * 160),
    ]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wintypes.DWORD), ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD), ("u", DEBUG_EVENT_UNION)]


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
THREAD_GET_CONTEXT = 0x0008
THREAD_SET_CONTEXT = 0x0010
MEM_COMMIT = 0x1000
SW_HIDE = 0
BM_CLICK = 0x00F5
CREATE_PROCESS_DEBUG_EVENT = 3
CREATE_THREAD_DEBUG_EVENT = 2
EXCEPTION_DEBUG_EVENT = 1
EXIT_PROCESS_DEBUG_EVENT = 5
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
WOW64_CONTEXT_FULL_AND_DEBUG = 0x00010013
DISPATCHER = bytes.fromhex("8d480483f9100f870a040000ff248d")
CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read(handle: int, address: int, size: int) -> bytes:
    buffer = (ctypes.c_ubyte * size)()
    received = ctypes.c_size_t()
    if not ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(received)):
        return b""
    return bytes(buffer[:received.value])


def find_dispatchers(handle: int) -> list[int]:
    hits: list[tuple[int, int]] = []
    address = 0x10000
    while address < 0x80000000:
        mbi = MBI()
        queried = VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not queried:
            address += 0x10000
            continue
        base, size, protect = int(mbi.BaseAddress or address), int(mbi.RegionSize), int(mbi.Protect)
        if mbi.State == MEM_COMMIT and 0 < size < 0x10000000 and protect & 0xF0:
            data = read(handle, base, size)
            offset = data.find(DISPATCHER)
            while offset >= 0:
                hits.append((base + offset, protect))
                offset = data.find(DISPATCHER, offset + 1)
        address = base + size if size else address + 0x10000
    return [address for address, _protect in hits]


def dialog_for(pid: int, timeout: float) -> tuple[int, int, int, int] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found: list[tuple[int, int, int, int]] = []

        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            thread_id = GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                edit, button = GetDlgItem(hwnd, 1008), GetDlgItem(hwnd, 1010)
                if edit and button:
                    found.append((int(hwnd), int(edit), int(button), int(thread_id)))
            return True

        EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.1)
    return None


def set_breakpoints(thread_id: int, addresses: list[int]) -> tuple[bool, str | None]:
    thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, False, thread_id)
    if not thread:
        return False, f"OpenThread failed: {ctypes.get_last_error()}"
    try:
        context = WOW64_CONTEXT()
        context.ContextFlags = WOW64_CONTEXT_FULL_AND_DEBUG
        if not Wow64GetThreadContext(thread, ctypes.byref(context)):
            return False, f"Wow64GetThreadContext failed: {ctypes.get_last_error()}"
        for index, address in enumerate(addresses[:2]):
            setattr(context, f"Dr{index}", address)
            context.Dr7 |= 1 << (index * 2)  # local, execute, length 1
        if not Wow64SetThreadContext(thread, ctypes.byref(context)):
            return False, f"Wow64SetThreadContext failed: {ctypes.get_last_error()}"
        return True, None
    finally:
        CloseHandle(thread)


def capture_context(thread_id: int) -> dict[str, str] | None:
    thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, False, thread_id)
    if not thread:
        return None
    try:
        context = WOW64_CONTEXT()
        context.ContextFlags = WOW64_CONTEXT_FULL_AND_DEBUG
        if not Wow64GetThreadContext(thread, ctypes.byref(context)):
            return None
        context.Dr0 = 0
        context.Dr1 = 0
        context.Dr7 &= ~0xF
        Wow64SetThreadContext(thread, ctypes.byref(context))
        return {"eip": hex(context.Eip), "eax": hex(context.Eax), "ebx": hex(context.Ebx), "ecx": hex(context.Ecx), "edx": hex(context.Edx)}
    finally:
        CloseHandle(thread)


def main() -> None:
    parser = argparse.ArgumentParser(description="Copied-process hardware observation of auth length comparison")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--key", default="A" * 32, help="Synthetic placeholder only; never written to output")
    parser.add_argument("--timeout", type=float, default=6.0)
    args = parser.parse_args()
    if not 32 <= len(args.key) <= 40:
        raise SystemExit("synthetic key length must be 32..40")

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    process_handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process.pid)
    dialog = dialog_for(process.pid, 8)
    result: dict[str, object] = {
        "status": "copied_process_hardware_breakpoint_observation",
        "copy_sha256": sha256(args.exe), "pid": process.pid,
        "method": "temporary debug-register observation on copied process; no code/memory patch, injection, payload capture, or credential capture",
        "synthetic_key_length": len(args.key), "dialog_found": bool(dialog), "breakpoint_hit": None,
    }
    attached = False
    try:
        if not dialog or not process_handle:
            result["error"] = "dialog or process handle unavailable"
        else:
            _root, edit, button, ui_thread = dialog
            SetWindowTextW(edit, args.key)
            result["input_lengths"] = {"unicode": GetWindowTextLengthW(edit), "ansi": GetWindowTextLengthA(edit)}
            dispatchers_before_attach = find_dispatchers(process_handle)
            if not dispatchers_before_attach:
                result["error"] = "dispatcher pattern not found"
            elif not DebugActiveProcess(process.pid):
                result["error"] = f"DebugActiveProcess failed: {ctypes.get_last_error()}"
            else:
                attached = True
                result["dispatchers_before_attach"] = [hex(address) for address in dispatchers_before_attach]
                result["ui_thread"] = ui_thread
                breakpoint_set = False
                click_posted = False
                breakpoints: list[int] = []
                armed_threads: dict[str, object] = {}
                deadline = time.monotonic() + args.timeout
                while time.monotonic() < deadline and process.poll() is None:
                    event = DEBUG_EVENT()
                    if not WaitForDebugEvent(ctypes.byref(event), 200):
                        continue
                    continue_status = DBG_CONTINUE
                    if event.dwDebugEventCode in (CREATE_PROCESS_DEBUG_EVENT, CREATE_THREAD_DEBUG_EVENT):
                        # Protected clients may remap runtime code when a debugger attaches;
                        # resolve the live copies again before programming debug registers.
                        if not breakpoints:
                            dispatchers_after_attach = find_dispatchers(process_handle)
                            breakpoints = [address - 0x7F for address in dispatchers_after_attach[:2]]
                            result["dispatchers_after_attach"] = [hex(address) for address in dispatchers_after_attach]
                            result["breakpoints"] = [hex(address) for address in breakpoints]
                        if not breakpoints:
                            result["breakpoint_error"] = "dispatcher pattern absent after debugger attach"
                            ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE)
                            break
                        armed, issue = set_breakpoints(event.dwThreadId, breakpoints)
                        armed_threads[str(event.dwThreadId)] = {"armed": armed, "error": issue}
                        if event.dwThreadId == ui_thread:
                            breakpoint_set = armed
                            result["breakpoint_set"] = breakpoint_set
                        if issue:
                            result.setdefault("breakpoint_errors", []).append({"thread": event.dwThreadId, "error": issue})
                    elif event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
                        code = int(event.u.Exception.ExceptionRecord.ExceptionCode)
                        if code == EXCEPTION_SINGLE_STEP:
                            registers = capture_context(event.dwThreadId)
                            if registers and int(registers["eip"], 16) in breakpoints:
                                registers["thread"] = event.dwThreadId
                                result["breakpoint_hit"] = registers
                                ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE)
                                break
                        elif code not in (EXCEPTION_BREAKPOINT, EXCEPTION_SINGLE_STEP):
                            continue_status = DBG_EXCEPTION_NOT_HANDLED
                    elif event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT:
                        result["exit_during_observation"] = process.poll()
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE)
                        break
                    ContinueDebugEvent(event.dwProcessId, event.dwThreadId, continue_status)
                    if breakpoint_set and not click_posted:
                        PostMessageW(button, BM_CLICK, 0, 0)
                        click_posted = True
                result["click_posted"] = click_posted
                result["armed_threads"] = armed_threads
                result["exit_before_cleanup"] = process.poll()
    finally:
        if attached:
            DebugActiveProcessStop(process.pid)
        if process_handle:
            CloseHandle(process_handle)
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
    print(json.dumps({"out": str(args.out), "breakpoint_hit": bool(result["breakpoint_hit"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

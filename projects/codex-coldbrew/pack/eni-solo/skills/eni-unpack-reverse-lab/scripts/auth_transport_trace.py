#!/usr/bin/env python3
"""Metadata-only transport/crypto trace for a copied login client."""
from __future__ import annotations

import argparse
import ctypes
import json
import pathlib
import subprocess
import time
from ctypes import wintypes

import frida


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
        found: list[tuple[int, int, int]] = []

        @CALLBACK
        def callback(hwnd, _):
            owner = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value == pid:
                ShowWindow(hwnd, SW_HIDE)
                edit = GetDlgItem(hwnd, 1008)
                button = GetDlgItem(hwnd, 1010)
                if edit and button:
                    found.append((int(hwnd), int(edit), int(button)))
            return True

        EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.1)
    return None


TRACE = r'''
function emit(event, data) { data = data || {}; data.event = event; send(data); }
function sockAddr(pointer) {
  try { return { family: pointer.readU16(), port: (pointer.add(2).readU8() << 8) | pointer.add(3).readU8(), ip: [pointer.add(4).readU8(), pointer.add(5).readU8(), pointer.add(6).readU8(), pointer.add(7).readU8()].join('.') }; }
  catch (_) { return { error: 'unreadable' }; }
}
function exp(moduleName, name) { try { return Module.getGlobalExportByName(name); } catch (_) { return null; } }
function hook(name, handlers) { const address = exp('', name); if (!address) return; try { Interceptor.attach(address, handlers); emit('hooked', {name:name}); } catch (e) { emit('hook_error', {name:name, error:String(e)}); } }
const wanted = new Set(['connect','wsaconnect','send','recv','wsasend','wsarecv','socket','wsastartup','gethostbyname','inet_addr','cryptencrypt','cryptdecrypt','bcrypteencrypt','bcryptdecrypt']);
hook('GetProcAddress', { onEnter(args) { try { this.name = args[1].readCString(); } catch (_) { this.name = ''; } }, onLeave(ret) { if (wanted.has(this.name.toLowerCase())) emit('dynamic_api_resolution', {name:this.name, address:ret.toString()}); } });
hook('connect', { onEnter(args) { this.address = sockAddr(args[1]); }, onLeave(ret) { emit('connect', {address:this.address, result:ret.toInt32()}); } });
hook('WSAConnect', { onEnter(args) { this.address = sockAddr(args[1]); }, onLeave(ret) { emit('WSAConnect', {address:this.address, result:ret.toInt32()}); } });
hook('send', { onEnter(args) { emit('send', {length:args[2].toInt32()}); } });
hook('recv', { onLeave(ret) { emit('recv', {length:ret.toInt32()}); } });
hook('WSASend', { onEnter(args) { emit('WSASend', {buffer_count:args[2].toInt32()}); } });
hook('WSARecv', { onLeave(ret) { emit('WSARecv', {result:ret.toInt32()}); } });
hook('HttpSendRequestW', { onEnter(args) { emit('HttpSendRequestW', {}); } });
hook('WinHttpSendRequest', { onEnter(args) { emit('WinHttpSendRequest', {}); } });
hook('CryptEncrypt', { onEnter(args) { emit('CryptEncrypt', {}); } });
hook('CryptDecrypt', { onEnter(args) { emit('CryptDecrypt', {}); } });
hook('BCryptEncrypt', { onEnter(args) { emit('BCryptEncrypt', {}); } });
hook('BCryptDecrypt', { onEnter(args) { emit('BCryptDecrypt', {}); } });
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Metadata-only copied-client auth transport trace")
    parser.add_argument("--exe", type=pathlib.Path, required=True)
    parser.add_argument("--cwd", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--key", default="1" * 32)
    parser.add_argument("--seconds", type=float, default=7.0)
    args = parser.parse_args()
    if not 32 <= len(args.key) <= 40:
        raise SystemExit("key length must be 32..40")
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = SW_HIDE
    process = subprocess.Popen([str(args.exe)], cwd=str(args.cwd), startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    result: dict[str, object] = {"status": "metadata_only_copied_client_trace", "pid": process.pid, "key_length": len(args.key), "events": []}
    login = find_login(process.pid, 8)
    if login:
        session = frida.attach(process.pid)
        script = session.create_script(TRACE)
        def receive(message, _data):
            if message.get("type") == "send" and isinstance(message.get("payload"), dict):
                result["events"].append(message["payload"])
            elif message.get("type") == "error":
                result["events"].append({"event": "frida_error", "description": message.get("description", "")})
        script.on("message", receive)
        script.load()
        hwnd, edit, button = login
        SetWindowTextW(edit, args.key)
        PostMessageW(button, BM_CLICK, 0, 0)
        end = time.time() + args.seconds
        while time.time() < end and process.poll() is None:
            find_login(process.pid, 0.01)
            time.sleep(0.1)
        try:
            script.unload()
            session.detach()
        except Exception:
            pass
        result["login_found"] = True
    else:
        result["login_found"] = False
    try:
        process.terminate()
        process.wait(timeout=1)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
    result["exit_after_trace"] = process.poll()
    result["note"] = "Payload bytes, credentials, and response bodies are intentionally not captured. Original files are not launched or modified."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"out": str(args.out), "login_found": result["login_found"], "event_count": len(result["events"])}, ensure_ascii=True))


if __name__ == "__main__":
    main()

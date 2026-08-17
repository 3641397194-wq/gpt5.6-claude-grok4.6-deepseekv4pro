#!/usr/bin/env python3
import argparse, ctypes, datetime, json, os, pathlib, subprocess, time
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
EnumWindows = user32.EnumWindows
EnumChildWindows = user32.EnumChildWindows
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextW = user32.GetWindowTextW
GetClassNameW = user32.GetClassNameW
IsWindowVisible = user32.IsWindowVisible
GetDlgItem = user32.GetDlgItem
MoveWindow = user32.MoveWindow
GetWindowRect = user32.GetWindowRect

class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long), ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
CB = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def text(hwnd):
    n = GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    GetWindowTextW(hwnd, buf, n + 1)
    return buf.value

def cls(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    GetClassNameW(hwnd, buf, 256)
    return buf.value

def snapshot(pid=None):
    out = []
    @CB
    def cb(hwnd, _):
        p = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if pid is None or p.value == pid:
            rec = {'hwnd': int(hwnd), 'pid': int(p.value), 'visible': bool(IsWindowVisible(hwnd)), 'title': text(hwnd), 'class': cls(hwnd), 'known_dialog_ids': {}, 'children': []}
            for dlg_id in (1001,1002,1005,1006,1007,1008,1009,1010,1011,1012):
                h = GetDlgItem(hwnd, dlg_id)
                if h: rec['known_dialog_ids'][str(dlg_id)] = int(h)
            @CB
            def ccb(ch, __):
                rec['children'].append({'hwnd': int(ch), 'title': text(ch), 'class': cls(ch)})
                return True
            EnumChildWindows(hwnd, ccb, 0)
            out.append(rec)
        return True
    EnumWindows(cb, 0)
    return out

def move_offscreen(pid):
    @CB
    def cb(hwnd, _):
        p = wintypes.DWORD(); GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid:
            r = RECT(); GetWindowRect(hwnd, ctypes.byref(r))
            MoveWindow(hwnd, -2600, -1700, max(300, r.right-r.left), max(200, r.bottom-r.top), False)
        return True
    EnumWindows(cb, 0)

def main():
    ap = argparse.ArgumentParser(description='Launch/probe a local Windows GUI copy and log top/child windows.')
    ap.add_argument('--launch', help='EXE to launch')
    ap.add_argument('--cwd', default=None)
    ap.add_argument('--pid', type=int, default=None)
    ap.add_argument('--duration', type=float, default=5.0)
    ap.add_argument('--interval', type=float, default=0.5)
    ap.add_argument('--out', default=None)
    ap.add_argument('--offscreen', action='store_true')
    ap.add_argument('--keep-running', action='store_true')
    args = ap.parse_args()
    proc = None; pid = args.pid
    if args.launch:
        exe = pathlib.Path(args.launch).expanduser().resolve()
        cwd = pathlib.Path(args.cwd).expanduser().resolve() if args.cwd else exe.parent
        proc = subprocess.Popen([str(exe)], cwd=str(cwd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = proc.pid
    if not pid:
        raise SystemExit('provide --launch or --pid')
    events = []
    end = time.time() + args.duration
    while time.time() < end:
        if args.offscreen:
            move_offscreen(pid)
        events.append({'t': time.time(), 'windows': snapshot(pid)})
        time.sleep(args.interval)
        if proc and proc.poll() is not None:
            break
    result = {'pid': pid, 'launch': args.launch, 'cwd': args.cwd, 'duration': args.duration, 'exit_code': proc.poll() if proc else None, 'events': events, 'generated': datetime.datetime.now().isoformat()}
    if proc and not args.keep_running and proc.poll() is None:
        proc.terminate(); time.sleep(0.5)
        if proc.poll() is None: proc.kill()
        result['terminated_by_probe'] = True
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding='utf-8')
    print(text)
if __name__ == '__main__':
    main()

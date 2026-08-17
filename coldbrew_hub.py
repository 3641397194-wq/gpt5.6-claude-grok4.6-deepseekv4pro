#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ColdBrew Hub — 冷咖啡四合一破甲面板
GPT-5.6 / Claude Code / Grok 4.6 / DeepSeek 一键部署 · 一键启动 · 一键恢复 · 一键打包发布。
单一文件 tkinter 应用，驱动四个 ColdBrew 工具的官方 CLI 与 GUI。"""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

APP_DIR = Path(__file__).resolve().parent
PROJECTS = APP_DIR / "projects"
PACKER = APP_DIR / "pack_release.py"

TOOLS = [
    {
        "tag": "GPT-5.6",
        "dir": "codex-coldbrew",
        "entry": ["studio", "eni_solo_deploy.py"],   # 部署桥接器 CLI
        "panel": ["studio", "coldbrew_studio.py"],  # 原始 Studio GUI
        "deploy": ["deploy", "--yes"],
        "verify": ["verify"],
        "launch": None,
        "restore": ["restore", "--yes"],
    },
    {
        "tag": "Claude Code",
        "dir": "claude-coldbrew",
        "entry": ["app", "claude_pojia.py"],
        "deploy": ["install", "--yes", "--profile", "max"],
        "verify": ["verify", "--profile", "max"],
        "launch": ["launch", "--profile", "max"],
        "restore": ["restore", "--yes"],
    },
    {
        "tag": "Grok 4.6",
        "dir": "grok4.6-coldbrew",
        "entry": ["app", "grok_coldbrew.py"],
        "deploy": ["deploy", "--profile", "max"],
        "verify": ["verify"],
        "launch": None,
        "restore": ["restore", "--profile", "max"],
    },
    {
        "tag": "DeepSeek",
        "dir": "deepseek-harness",
        "entry": ["app", "deepseek_harness.py"],
        "deploy": ["deploy", "--profile", "max"],
        "verify": ["verify"],
        "launch": None,
        "restore": ["restore", "--profile", "max"],
    },
]

# 部署命令的第一个词；这些命令跑完后自动追加部署验证。
DEPLOY_VERBS = {"deploy", "install"}


def tool_entry(tool) -> Path:
    return PROJECTS / tool["dir"] / Path(*tool["entry"])


def tool_panel(tool) -> Path:
    return PROJECTS / tool["dir"] / Path(*tool.get("panel", tool["entry"]))


def run_command(tool, args, log_q, attach: bool = False):
    """后台线程执行子进程，输出送入日志队列；部署完成后自动验证。"""
    entry = tool_entry(tool)
    if not entry.exists():
        log_q.put(("error", f"[{tool['tag']}] 入口缺失: {entry}"))
        return
    cmd = [sys.executable, str(entry)] + list(args)
    log_q.put(("info", f"[{tool['tag']}] 执行：python {entry.name} {' '.join(args)}"))
    try:
        if attach:
            # 打开面板：不捕获输出，控制台直接可见
            subprocess.Popen(
                cmd,
                cwd=str(entry.parent),
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )
            log_q.put(("ok", f"[{tool['tag']}] 面板已启动（新窗口）"))
            return
        proc = subprocess.Popen(
            cmd,
            cwd=str(entry.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        )
        for line in proc.stdout:
            log_q.put(("out", line.rstrip()))
        proc.wait()
        if proc.returncode == 0:
            log_q.put(("ok", f"[{tool['tag']}] 完成（退出码 0）"))
        else:
            log_q.put(("error", f"[{tool['tag']}] 失败（退出码 {proc.returncode}）"))

        # 部署成功 → 部署后自动验证
        if proc.returncode == 0 and args and args[0] in DEPLOY_VERBS and tool.get("verify"):
            log_q.put(("info", f"[{tool['tag']}] 部署后自动验证 …"))
            verify_cmd = [sys.executable, str(entry)] + list(tool["verify"])
            vproc = subprocess.run(
                verify_cmd,
                cwd=str(entry.parent),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
                timeout=600,
            )
            for line in (vproc.stdout or "").splitlines():
                log_q.put(("out", f"  验证: {line}"))
            if vproc.returncode == 0:
                log_q.put(("ok", f"[{tool['tag']}] 验证通过"))
            else:
                log_q.put(("error", f"[{tool['tag']}] 验证未通过（退出码 {vproc.returncode}）"))
    except Exception as exc:  # noqa: BLE001
        log_q.put(("error", f"[{tool['tag']}] 异常: {exc}"))


def run_packer(tool_or_none, log_q):
    """一键打包发布：单项目或全部项目，输出 SHA256 与汇总。"""
    cmd = [sys.executable, str(PACKER)]
    if tool_or_none is None:
        cmd.append("--all")
        label = "全部项目"
    else:
        cmd += ["--project", tool_or_none["dir"]]
        label = tool_or_none["tag"]
    log_q.put(("info", f"[打包] {label} 打包中 …"))
    if not PACKER.exists():
        log_q.put(("error", f"[打包] 打包脚本缺失: {PACKER}"))
        return
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(APP_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
            timeout=1200,
        )
        if proc.stdout:
            try:
                import json

                payload = json.loads(proc.stdout)
                for item in payload.get("results", []):
                    if item.get("ok"):
                        log_q.put(("ok", f"[打包] {item['project']} v{item['version']} "
                                        f"({item['files']} 文件) sha256={item['sha256'][:16]}…"))
                    else:
                        log_q.put(("error", f"[打包] {item['project']}: {item.get('error')}"))
                if payload.get("sha256sums"):
                    log_q.put(("ok", f"[打包] 汇总 {payload['sha256sums']}"))
            except Exception:
                for line in proc.stdout.splitlines():
                    log_q.put(("out", f"  打包输出: {line}"))
        if proc.returncode != 0:
            log_q.put(("error", f"[打包] {label} 失败（退出码 {proc.returncode}）"))
    except Exception as exc:  # noqa: BLE001
        log_q.put(("error", f"[打包] 异常: {exc}"))


class HubApp:
    def __init__(self, root):
        self.root = root
        self.log_q: queue.Queue = queue.Queue()
        self.jobs: set[int] = set()
        root.title("冷咖啡 · ColdBrew Hub — 四合一破甲面板")
        root.geometry("920x680")
        root.minsize(780, 580)

        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#10151b")
        style.configure("TLabel", background="#10151b", foreground="#d8e2ec")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"), foreground="#f4e3c8")
        style.configure("Tool.TLabel", font=("Microsoft YaHei UI", 11, "bold"), foreground="#9fd8ff")
        style.configure("TButton", font=("Microsoft YaHei UI", 9), padding=(10, 6))
        style.configure("Go.TButton", font=("Microsoft YaHei UI", 9, "bold"))

        header = ttk.Frame(root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="冷咖啡 ColdBrew Hub", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="GPT-5.6 · Claude Code · Grok 4.6 · DeepSeek  一键部署 / 启动 / 恢复 / 打包发布",
            style="TLabel",
        ).pack(side="left", padx=18)

        bar = ttk.Frame(root, padding=(16, 0))
        bar.pack(fill="x")
        ttk.Button(bar, text="全部部署", style="Go.TButton", command=self.deploy_all).pack(side="left", padx=4)
        ttk.Button(bar, text="全部恢复", command=self.restore_all).pack(side="left", padx=4)
        ttk.Button(bar, text="全部打包发布", command=self.pack_all).pack(side="left", padx=4)
        ttk.Button(bar, text="环境自检", command=self.env_check).pack(side="left", padx=4)
        self.progress = ttk.Label(bar, text="就绪", style="TLabel")
        self.progress.pack(side="right")

        self.body = ttk.Frame(root, padding=(16, 8))
        self.body.pack(fill="both", expand=True)
        self.rows = []
        for tool in TOOLS:
            self.add_tool_row(tool)

        logf = ttk.Frame(root, padding=(16, 6))
        logf.pack(fill="both", expand=True)
        ttk.Label(logf, text="运行日志", style="TLabel").pack(anchor="w")
        self.log_text = self.tk.Text(
            logf, height=14, bg="#0b0f14", fg="#b9e6a9",
            insertbackground="#ffffff", relief="flat",
            font=("Consolas", 9),
        )
        self.log_text.pack(fill="both", expand=True, pady=(4, 10))
        self.log_text.tag_configure("error", foreground="#ff8f8f")
        self.log_text.tag_configure("ok", foreground="#8ff0a1")
        self.log_text.tag_configure("info", foreground="#9fd8ff")
        self.log_text.tag_configure("out", foreground="#c9d4de")

        self.root.after(120, self.pump_log)

    def add_tool_row(self, tool):
        row = self.ttk.Frame(self.body)
        row.pack(fill="x", pady=5)
        self.ttk.Label(row, text=tool["tag"], style="Tool.TLabel", width=14).pack(side="left")
        entry = tool_entry(tool)
        status = "就绪" if entry.exists() else "缺失"
        self.ttk.Label(row, text=f"({status})", style="TLabel").pack(side="left")
        self.ttk.Button(row, text="打包", command=lambda t=tool: self.pack_one(t)).pack(side="right", padx=3)
        self.ttk.Button(row, text="一键部署", style="Go.TButton",
                        command=lambda t=tool: self.spawn(t, t["deploy"])).pack(side="right", padx=3)
        self.ttk.Button(row, text="恢复", command=lambda t=tool: self.spawn(t, t["restore"])).pack(side="right", padx=3)
        self.ttk.Button(row, text="打开面板",
                        command=lambda t=tool: self.spawn(t, ["gui"], attach=True, use_panel=True)).pack(side="right", padx=3)
        if tool["launch"]:
            self.ttk.Button(row, text="一键启动", style="Go.TButton",
                            command=lambda t=tool: self.spawn(t, t["launch"])).pack(side="right", padx=3)
        self.rows.append(row)

    def _job_start(self) -> int:
        job = time.time_ns()
        self.jobs.add(job)
        return job

    def _job_end(self, job: int) -> None:
        self.jobs.discard(job)

    def spawn(self, tool, args, attach=False, use_panel=False):
        entry = tool_panel(tool) if use_panel else tool_entry(tool)
        if not entry.exists():
            self.log_q.put(("error", f"[{tool['tag']}] 入口缺失: {entry}"))
            return
        job = self._job_start()
        self.progress.configure(text=f"{tool['tag']} 运行中 …")

        def worker():
            run_command(tool, args, self.log_q, attach=attach)
            self._job_end(job)

        threading.Thread(target=worker, daemon=True).start()

    def deploy_all(self):
        for tool in TOOLS:
            if not tool_entry(tool).exists():
                self.log_q.put(("error", f"[{tool['tag']}] 入口缺失，跳过部署"))
                continue
            self.spawn(tool, tool["deploy"])
        self.progress.configure(text="全部部署已排队")

    def restore_all(self):
        for tool in TOOLS:
            if not tool_entry(tool).exists():
                self.log_q.put(("error", f"[{tool['tag']}] 入口缺失，跳过恢复"))
                continue
            self.spawn(tool, tool["restore"])
        self.progress.configure(text="全部恢复已排队")

    def pack_one(self, tool):
        job = self._job_start()
        self.progress.configure(text=f"{tool['tag']} 打包中 …")

        def worker():
            run_packer(tool, self.log_q)
            self._job_end(job)

        threading.Thread(target=worker, daemon=True).start()

    def pack_all(self):
        job = self._job_start()
        self.progress.configure(text="全部打包发布中 …")

        def worker():
            run_packer(None, self.log_q)
            self._job_end(job)

        threading.Thread(target=worker, daemon=True).start()

    def env_check(self):
        self.log_q.put(("info", f"Python：{sys.version.split()[0]}（{sys.executable}）"))
        for tool in TOOLS:
            entry = tool_entry(tool)
            ok = "正常" if entry.exists() else "缺失"
            self.log_q.put(("info" if entry.exists() else "error", f"[{tool['tag']}] 入口{ok}：{entry}"))
        pack = PROJECTS / "codex-coldbrew" / "pack" / "eni-solo"
        self.log_q.put(("info" if pack.is_dir() else "error",
                        f"[GPT-5.6] eni-solo 包{'正常' if pack.is_dir() else '缺失'}：{pack}"))
        self.log_q.put(("info" if PACKER.exists() else "error",
                        f"[打包] pack_release.py{'正常' if PACKER.exists() else '缺失'}：{PACKER}"))
        self.log_q.put(("ok", "环境自检完成"))

    def pump_log(self):
        try:
            while True:
                kind, msg = self.log_q.get_nowait()
                stamp = time.strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{stamp}] {msg}\n", kind)
                self.log_text.see("end")
        except queue.Empty:
            pass
        if self.jobs:
            self.progress.configure(text=f"{len(self.jobs)} 个任务运行中 …")
        else:
            self.progress.configure(text="就绪")
        self.root.after(120, self.pump_log)


def selftest():
    print("冷咖啡 Hub 自检")
    for tool in TOOLS:
        entry = tool_entry(tool)
        panel = tool_panel(tool)
        print(f"  {tool['tag']:<12} 入口={entry} 存在={entry.exists()} 面板={panel} 存在={panel.exists()}")
    pack = PROJECTS / "codex-coldbrew" / "pack" / "eni-solo"
    print(f"  {'eni-solo 包':<12} 路径={pack} 存在={pack.is_dir()}")
    print(f"  {'打包器':<12} 路径={PACKER} 存在={PACKER.exists()}")
    print("自检完成")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    try:
        import tkinter as tk

        root = tk.Tk()
        HubApp(root)
        root.mainloop()
    except Exception as exc:  # noqa: BLE001
        import traceback

        log_path = APP_DIR / "面板启动错误日志.txt"
        try:
            log_path.write_text(
                traceback.format_exc(), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        try:
            import tkinter as tk
            from tkinter import messagebox

            messagebox.showerror(
                "冷咖啡 Hub 启动失败",
                f"{exc}\n\n详细报错已写入：{log_path}\n"
                "请把日志发给冷咖啡社区 QQ 群 1057540028 / 1077074552。",
            )
        except Exception:  # noqa: BLE001
            print(traceback.format_exc(), file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

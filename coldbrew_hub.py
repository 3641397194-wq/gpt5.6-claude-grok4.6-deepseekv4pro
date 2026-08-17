#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ColdBrew Hub v8 — 四模型控制台。

这是一个薄控制层：它只调用各适配器已有的 preview/deploy/verify/restore
命令，不直接改写用户配置，从而保留冷咖啡入口、快照与回滚契约。
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


APP_DIR = Path(__file__).resolve().parent
PROJECTS = APP_DIR / "projects"
PACKER = APP_DIR / "pack_release.py"
TRIGGERS = ("冷咖啡", "cold coffee", "[[ENI:PROFILE=MAX]]")

TOOLS: tuple[dict[str, Any], ...] = (
    {
        "id": "codex",
        "tag": "GPT-5.6",
        "short": "Codex ColdBrew",
        "description": "Codex Studio · skills · review chain",
        "accent": "#80F0BC",
        "dir": "codex-coldbrew",
        "entry": ("studio", "eni_solo_deploy.py"),
        "panel": ("studio", "coldbrew_studio.py"),
        "deploy": ("deploy", "--yes"),
        "verify": ("verify",),
        "restore": ("restore", "--yes"),
    },
    {
        "id": "claude",
        "tag": "Claude Code",
        "short": "Claude ColdBrew",
        "description": "规则层 · brain layers · 可回滚安装",
        "accent": "#FF9E7A",
        "dir": "claude-coldbrew",
        "entry": ("app", "claude_pojia.py"),
        "panel": ("app", "claude_pojia.py"),
        "deploy": ("install", "--yes", "--profile", "max"),
        "verify": ("verify", "--profile", "max"),
        "restore": ("restore", "--yes"),
    },
    {
        "id": "grok",
        "tag": "Grok 4.6",
        "short": "Grok ColdBrew",
        "description": "实时信息流适配器 · profile 模板 · 原子恢复",
        "accent": "#23F5D7",
        "dir": "grok4.6-coldbrew",
        "entry": ("app", "grok_coldbrew.py"),
        "panel": ("app", "grok_coldbrew.py"),
        "deploy": ("deploy", "--profile", "max"),
        "verify": ("verify",),
        "restore": ("restore", "--profile", "max"),
    },
    {
        "id": "deepseek",
        "tag": "DeepSeek v4 Pro",
        "short": "DeepSeek Harness",
        "description": "Harness 会话模板 · profile 配置 · 事务式部署",
        "accent": "#7AA2FF",
        "dir": "deepseek-harness",
        "entry": ("app", "deepseek_harness.py"),
        "panel": ("app", "deepseek_harness.py"),
        "deploy": ("deploy", "--profile", "max"),
        "verify": ("verify",),
        "restore": ("restore", "--profile", "max"),
    },
)

DEPLOY_VERBS = {"deploy", "install"}


def tool_entry(tool: dict[str, Any]) -> Path:
    return PROJECTS / str(tool["dir"]) / Path(*tool["entry"])


def tool_panel(tool: dict[str, Any]) -> Path:
    return PROJECTS / str(tool["dir"]) / Path(*tool.get("panel", tool["entry"]))


def tool_version(tool: dict[str, Any]) -> str:
    path = PROJECTS / str(tool["dir"]) / "VERSION"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return "source"
    return value or "source"


def environment_snapshot() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "root": str(APP_DIR),
        "projects": str(PROJECTS),
        "packer": PACKER.is_file(),
        "cold_coffee": TRIGGERS,
    }


def _emit(log_q: queue.Queue, kind: str, message: str) -> None:
    log_q.put((kind, message))


def run_command(tool: dict[str, Any], args: tuple[str, ...], log_q: queue.Queue, *, attach: bool = False) -> None:
    entry = tool_entry(tool)
    if not entry.is_file():
        _emit(log_q, "error", f"[{tool['tag']}] 入口缺失：{entry}")
        return
    command = [sys.executable, str(entry), *args]
    _emit(log_q, "info", f"[{tool['tag']}] python {entry.name} {' '.join(args)}")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        if attach:
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            subprocess.Popen(command, cwd=str(entry.parent), creationflags=flags, env=env)
            _emit(log_q, "ok", f"[{tool['tag']}] 工作台已在新窗口启动")
            return
        process = subprocess.Popen(command, cwd=str(entry.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", env=env)
        assert process.stdout is not None
        for line in process.stdout:
            _emit(log_q, "out", f"[{tool['tag']}] {line.rstrip()}")
        code = process.wait()
        if code:
            _emit(log_q, "error", f"[{tool['tag']}] 退出码 {code}")
            return
        _emit(log_q, "ok", f"[{tool['tag']}] 完成")
        if args and args[0] in DEPLOY_VERBS and tool.get("verify"):
            _emit(log_q, "info", f"[{tool['tag']}] 正在执行部署后验证")
            verify_cmd = [sys.executable, str(entry), *tool["verify"]]
            result = subprocess.run(verify_cmd, cwd=str(entry.parent), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
            for line in (result.stdout or "").splitlines():
                _emit(log_q, "out", f"[{tool['tag']}/verify] {line}")
            _emit(log_q, "ok" if result.returncode == 0 else "error", f"[{tool['tag']}] 部署后验证{'通过' if result.returncode == 0 else f'失败，退出码 {result.returncode}'}")
    except subprocess.TimeoutExpired:
        _emit(log_q, "error", f"[{tool['tag']}] 操作超时")
    except OSError as exc:
        _emit(log_q, "error", f"[{tool['tag']}] 启动失败：{exc}")
    except Exception as exc:  # noqa: BLE001
        _emit(log_q, "error", f"[{tool['tag']}] 异常：{exc}")


def run_packer(tool: dict[str, Any] | None, log_q: queue.Queue) -> None:
    if not PACKER.is_file():
        _emit(log_q, "error", f"打包脚本缺失：{PACKER}")
        return
    command = [sys.executable, str(PACKER), "--all" if tool is None else "--project", *( [] if tool is None else [str(tool["dir"])] )]
    label = "全部项目" if tool is None else str(tool["tag"])
    _emit(log_q, "info", f"[打包] {label} 开始")
    try:
        result = subprocess.run(command, cwd=str(APP_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=1200)
        if result.stdout:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                for line in result.stdout.splitlines():
                    _emit(log_q, "out", f"[打包] {line}")
            else:
                for item in payload.get("results", []):
                    _emit(log_q, "ok" if item.get("ok") else "error", f"[打包] {item.get('project')} · {item.get('files', 0)} 文件 · {str(item.get('sha256', ''))[:16]}")
                if payload.get("sha256sums"):
                    _emit(log_q, "ok", f"[打包] 校验汇总：{payload['sha256sums']}")
        _emit(log_q, "ok" if result.returncode == 0 else "error", f"[打包] {label}{'完成' if result.returncode == 0 else f'失败，退出码 {result.returncode}'}")
    except Exception as exc:  # noqa: BLE001
        _emit(log_q, "error", f"[打包] 异常：{exc}")


class HubApp:
    BG = "#080D10"
    PANEL = "#10191D"
    PANEL_ALT = "#152328"
    LINE = "#263B40"
    PAPER = "#ECF8F3"
    MUTED = "#91A6A1"
    DIM = "#617772"
    MINT = "#80F0BC"
    CYAN = "#59C8F5"
    CORAL = "#FF8066"
    INK = "#07110D"
    FONT = "Microsoft YaHei UI"

    def __init__(self, root: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk, self.root = tk, ttk, root
        self.root.title("冷咖啡 · ColdBrew Hub · Control Deck v8")
        self.root.geometry("1380x900")
        self.root.minsize(1120, 760)
        self.root.configure(bg=self.BG)
        self.root.option_add("*Font", (self.FONT, 10))
        self.log_q: queue.Queue = queue.Queue()
        self.jobs: set[str] = set()
        self.cards: dict[str, dict[str, Any]] = {}
        self.status_var = tk.StringVar(value="READY · 选择一个动作开始")
        self.count_var = tk.StringVar(value="0 / 4 ready")
        self.coffee_var = tk.StringVar(value="COLD COFFEE COMPATIBILITY · READY")
        self._build_styles()
        self._build_shell()
        self.root.after(120, self._pump_log)
        self.root.after(500, self.env_check)
        for index, tool in enumerate(TOOLS, 1):
            self.root.bind(f"<Control-{index}>", lambda _event, t=tool: self._open_panel(t))

    def _build_styles(self) -> None:
        style = self.ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except self.tk.TclError:
            pass
        style.configure("Cold.TButton", background=self.MINT, foreground=self.INK, borderwidth=0, padding=(13, 9), font=(self.FONT, 9, "bold"))
        style.map("Cold.TButton", background=[("active", "#A7FFD3")])
        style.configure("Quiet.TButton", background=self.PANEL_ALT, foreground=self.PAPER, bordercolor=self.LINE, padding=(11, 8), font=(self.FONT, 9))
        style.map("Quiet.TButton", background=[("active", "#214149")])
        style.configure("Card.TButton", background=self.PANEL_ALT, foreground=self.PAPER, bordercolor=self.LINE, padding=(9, 7), font=(self.FONT, 8))
        style.map("Card.TButton", background=[("active", "#28434A")])

    def _label(self, parent: Any, text: str = "", **kwargs: Any) -> Any:
        options = {"bg": parent.cget("bg"), "fg": self.PAPER, "font": (self.FONT, 9)}
        options.update(kwargs)
        return self.tk.Label(parent, text=text, **options)

    def _panel(self, parent: Any, **kwargs: Any) -> Any:
        return self.tk.Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground=self.LINE, **kwargs)

    def _build_shell(self) -> None:
        tk, ttk = self.tk, self.ttk
        shell = tk.Frame(self.root, bg=self.BG, padx=26, pady=20)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)
        header = tk.Frame(shell, bg=self.BG)
        header.grid(row=0, column=0, sticky="ew")
        left = tk.Frame(header, bg=self.BG)
        left.pack(side="left", fill="y")
        self._label(left, "COLDBREW / CONTROL DECK", fg=self.MINT, font=("Consolas", 10, "bold")).pack(anchor="w")
        self._label(left, "冷咖啡 · 四模型统一控制台", font=(self.FONT, 25, "bold")).pack(anchor="w", pady=(2, 0))
        self._label(left, "GPT-5.6  ·  Claude Code  ·  Grok 4.6  ·  DeepSeek v4 Pro", fg=self.MUTED, font=(self.FONT, 10)).pack(anchor="w", pady=(3, 0))
        right = tk.Frame(header, bg=self.BG)
        right.pack(side="right", fill="y")
        self._label(right, "V8.0 / OWNER BUILD", fg=self.MUTED, font=("Consolas", 9)).pack(anchor="e")
        self._label(right, textvariable=self.count_var, fg=self.CYAN, font=("Consolas", 10, "bold")).pack(anchor="e", pady=(9, 0))
        self._label(right, textvariable=self.status_var, fg=self.MINT, font=(self.FONT, 9)).pack(anchor="e", pady=(7, 0))
        activation = self._panel(shell, padx=16, pady=10)
        activation.grid(row=1, column=0, sticky="ew", pady=(16, 14))
        self._label(activation, "ACTIVATION", fg=self.MINT, font=("Consolas", 9, "bold")).pack(side="left", padx=(0, 14))
        self._label(activation, textvariable=self.coffee_var, fg=self.CYAN, font=("Consolas", 9, "bold")).pack(side="left")
        self._label(activation, "· 触发词：冷咖啡 / cold coffee / [[ENI:PROFILE=MAX]]", fg=self.MUTED, font=(self.FONT, 9)).pack(side="left", padx=14)
        ttk.Button(activation, text="清空日志", style="Quiet.TButton", command=self._clear_log).pack(side="right")
        content = tk.Frame(shell, bg=self.BG)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=3)
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)
        card_grid = tk.Frame(content, bg=self.BG)
        card_grid.grid(row=0, column=0, sticky="nsew")
        for column in range(2):
            card_grid.grid_columnconfigure(column, weight=1, uniform="cards")
        for row in range(2):
            card_grid.grid_rowconfigure(row, weight=1, uniform="cards")
        for index, tool in enumerate(TOOLS):
            card = self._make_card(card_grid, tool)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0 if index % 2 == 0 else 8, 8 if index % 2 == 0 else 0), pady=(0 if index < 2 else 8, 8 if index < 2 else 0))
        lower = tk.Frame(content, bg=self.BG)
        lower.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=1)
        log_panel = self._panel(lower, padx=14, pady=12)
        log_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._label(log_panel, "ACTIVITY LOG", fg=self.MINT, font=("Consolas", 9, "bold")).pack(anchor="w")
        self.log_text = tk.Text(log_panel, height=8, bg=self.BG, fg=self.PAPER, insertbackground=self.MINT, relief="flat", font=("Consolas", 9), padx=10, pady=8)
        self.log_text.pack(fill="both", expand=True, pady=(8, 0))
        for tag, color in (("error", "#FF8F8F"), ("ok", self.MINT), ("info", self.CYAN), ("out", "#C9D4DE")):
            self.log_text.tag_configure(tag, foreground=color)
        summary = self._panel(lower, padx=14, pady=12)
        summary.grid(row=0, column=1, sticky="nsew")
        self._label(summary, "RUNTIME SNAPSHOT", fg=self.MINT, font=("Consolas", 9, "bold")).pack(anchor="w")
        self.summary_text = tk.Text(summary, height=8, bg=self.BG, fg=self.MUTED, relief="flat", font=("Consolas", 8), padx=10, pady=8, wrap="word")
        self.summary_text.pack(fill="both", expand=True, pady=(8, 0))
        self._render_summary(environment_snapshot())
        toolbar = tk.Frame(shell, bg=self.BG)
        toolbar.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(toolbar, text="一键部署全部", style="Cold.TButton", command=self.deploy_all).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="全部验证", style="Quiet.TButton", command=self.verify_all).pack(side="left", padx=4)
        ttk.Button(toolbar, text="全部恢复", style="Quiet.TButton", command=self.restore_all).pack(side="left", padx=4)
        ttk.Button(toolbar, text="全量打包", style="Quiet.TButton", command=self.pack_all).pack(side="left", padx=4)
        ttk.Button(toolbar, text="环境自检", style="Quiet.TButton", command=self.env_check).pack(side="left", padx=4)
        self._label(toolbar, "Ctrl+1–4 打开对应工作台", fg=self.DIM, font=("Consolas", 8)).pack(side="right")

    def _make_card(self, parent: Any, tool: dict[str, Any]) -> Any:
        tk, ttk = self.tk, self.ttk
        card = self._panel(parent, padx=16, pady=14)
        card.grid_columnconfigure(0, weight=1)
        head = tk.Frame(card, bg=self.PANEL)
        head.grid(row=0, column=0, sticky="ew")
        tk.Frame(head, bg=tool["accent"], width=9, height=9).pack(side="left", padx=(0, 8), pady=5)
        title = tk.Frame(head, bg=self.PANEL)
        title.pack(side="left", fill="x", expand=True)
        self._label(title, tool["tag"], font=(self.FONT, 15, "bold")).pack(anchor="w")
        self._label(title, tool["short"], fg=tool["accent"], font=("Consolas", 8, "bold")).pack(anchor="w", pady=(2, 0))
        self._label(head, f"v{tool_version(tool)}", fg=self.MUTED, font=("Consolas", 8)).pack(side="right", anchor="n")
        self._label(card, tool["description"], fg=self.MUTED, font=(self.FONT, 9)).grid(row=1, column=0, sticky="w", pady=(10, 8))
        status = self._label(card, "CHECKING…", fg=tool["accent"], font=("Consolas", 8, "bold"))
        status.grid(row=2, column=0, sticky="w")
        self.cards[tool["id"]] = {"tool": tool, "status": status}
        action_bar = tk.Frame(card, bg=self.PANEL)
        action_bar.grid(row=3, column=0, sticky="ew", pady=(11, 0))
        buttons = (("打开工作台", lambda t=tool: self._open_panel(t)), ("预览", lambda t=tool: self._run_tool(t, ("plan",) if t["id"] == "codex" else ("preview", "--profile", "max"))), ("部署", lambda t=tool: self._run_tool(t, t["deploy"])), ("验证", lambda t=tool: self._run_tool(t, t["verify"])), ("恢复", lambda t=tool: self._run_tool(t, t["restore"])))
        for label, command in buttons:
            ttk.Button(action_bar, text=label, style="Card.TButton", command=command).pack(side="left", padx=(0, 5))
        return card

    def _open_panel(self, tool: dict[str, Any]) -> None:
        self._run_tool(tool, ("gui",), attach=True, panel=True)

    def _run_tool(self, tool: dict[str, Any], args: tuple[str, ...], *, attach: bool = False, panel: bool = False) -> None:
        key = f"{tool['id']}:{' '.join(args)}"
        if key in self.jobs:
            _emit(self.log_q, "info", f"[{tool['tag']}] 相同任务正在运行，已跳过重复点击")
            return
        entry = tool_panel(tool) if panel else tool_entry(tool)
        if not entry.is_file():
            _emit(self.log_q, "error", f"[{tool['tag']}] 文件不存在：{entry}")
            return
        self.jobs.add(key)
        self.status_var.set(f"RUNNING · {tool['tag']}")

        def worker() -> None:
            try:
                run_command(tool, args, self.log_q, attach=attach)
            finally:
                self.jobs.discard(key)

        threading.Thread(target=worker, daemon=True).start()

    def _run_pack(self, tool: dict[str, Any] | None) -> None:
        key = "pack:all" if tool is None else f"pack:{tool['id']}"
        if key in self.jobs:
            return
        self.jobs.add(key)
        self.status_var.set("RUNNING · PACKAGING")

        def worker() -> None:
            try:
                run_packer(tool, self.log_q)
            finally:
                self.jobs.discard(key)

        threading.Thread(target=worker, daemon=True).start()

    def deploy_all(self) -> None:
        for tool in TOOLS:
            self._run_tool(tool, tool["deploy"])

    def verify_all(self) -> None:
        for tool in TOOLS:
            self._run_tool(tool, tool["verify"])

    def restore_all(self) -> None:
        for tool in TOOLS:
            self._run_tool(tool, tool["restore"])

    def pack_all(self) -> None:
        self._run_pack(None)

    def env_check(self) -> None:
        snapshot = environment_snapshot()
        ready = 0
        for tool in TOOLS:
            entry_ok, panel_ok = tool_entry(tool).is_file(), tool_panel(tool).is_file()
            if entry_ok and panel_ok:
                ready += 1
            state = self.cards.get(tool["id"])
            if state:
                state["status"].configure(text="READY · CLI + WORKSPACE" if entry_ok and panel_ok else "CHECK REQUIRED", fg=tool["accent"] if entry_ok and panel_ok else self.CORAL)
            _emit(self.log_q, "info" if entry_ok and panel_ok else "error", f"[{tool['tag']}] CLI={'OK' if entry_ok else 'MISSING'} · GUI={'OK' if panel_ok else 'MISSING'}")
        snapshot["ready"] = f"{ready}/4"
        self.count_var.set(f"{ready} / 4 ready")
        self._render_summary(snapshot)
        _emit(self.log_q, "ok" if ready == 4 else "error", f"环境自检完成 · {ready}/4 项目就绪")

    def _render_summary(self, snapshot: dict[str, Any]) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        for key, value in snapshot.items():
            self.summary_text.insert("end", f"{key.upper():<14} {value}\n")
        self.summary_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", "end")
        _emit(self.log_q, "info", "日志已清空")

    def _pump_log(self) -> None:
        try:
            while True:
                kind, message = self.log_q.get_nowait()
                self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n", kind)
                self.log_text.see("end")
        except queue.Empty:
            pass
        if not self.jobs:
            self.status_var.set("READY · 选择一个动作开始")
        self.root.after(120, self._pump_log)


def selftest() -> int:
    print("ColdBrew Hub v8 self-test")
    print(json.dumps(environment_snapshot(), ensure_ascii=False, indent=2))
    for tool in TOOLS:
        print(f"{tool['tag']:<16} cli={tool_entry(tool).is_file()} gui={tool_panel(tool).is_file()} version={tool_version(tool)}")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        import tkinter as tk

        root = tk.Tk()
        HubApp(root)
        root.mainloop()
        return 0
    except Exception as exc:  # noqa: BLE001
        (APP_DIR / "hub-startup-error.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        print(f"ColdBrew Hub 启动失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

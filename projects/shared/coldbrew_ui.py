"""Shared ColdBrew workbench UI.

The adapter modules own the deployment contract.  This module only provides a
consistent Tkinter surface around their existing preview/deploy/verify/restore
functions, so a UI change cannot alter the underlying files or prompt payload.
"""

from __future__ import annotations

import json
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable


Action = Callable[..., dict[str, Any]]


def launch_shared_gui(
    *,
    title: str,
    model: str,
    subtitle: str,
    accent: str,
    home: Path | None,
    resolve_layout: Callable[[Path | None], Any],
    profile_names: Callable[[], list[str]],
    preview: Action,
    deploy: Action,
    verify: Action,
    restore: Action,
    export_template: Callable[[Path, str], dict[str, Any]],
    community: dict[str, str],
) -> int:
    """Open the polished adapter workbench and return the Tk exit status."""

    bg = "#071019"
    panel = "#0F1B27"
    panel_alt = "#122635"
    line = "#23404B"
    text = "#EDF5F8"
    dim = "#91A8B8"
    success = "#80F0BC"
    error = "#FF8B8B"

    window = tk.Tk()
    window.title(title)
    window.geometry("1120x760")
    window.minsize(960, 650)
    window.configure(bg=bg)
    window.option_add("*Font", ("Segoe UI", 10))

    style = ttk.Style(window)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Primary.TButton", background=accent, foreground="#031015", borderwidth=0, padding=(14, 10), font=("Segoe UI", 9, "bold"))
    style.map("Primary.TButton", background=[("active", "#B4FFE0")])
    style.configure("Quiet.TButton", background=panel_alt, foreground=text, borderwidth=0, padding=(12, 9))
    style.map("Quiet.TButton", background=[("active", "#21485A")])
    style.configure("Cold.Horizontal.TProgressbar", troughcolor=panel_alt, background=accent, bordercolor=line, lightcolor=accent, darkcolor=accent)

    root = tk.Frame(window, bg=bg, padx=28, pady=24)
    root.pack(fill="both", expand=True)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(3, weight=1)

    header = tk.Frame(root, bg=bg)
    header.grid(row=0, column=0, sticky="ew")
    tk.Label(header, text="COLDBREW / WORKBENCH", bg=bg, fg=accent, font=("Consolas", 10, "bold")).pack(anchor="w")
    tk.Label(header, text=model, bg=bg, fg=text, font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(3, 0))
    tk.Label(header, text=subtitle, bg=bg, fg=dim, font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 0))

    badge = tk.Label(header, text="●  READY", bg=bg, fg=success, font=("Consolas", 10, "bold"))
    badge.pack(anchor="e", pady=(0, 2))

    activation = tk.Frame(root, bg=panel, highlightthickness=1, highlightbackground=line, padx=15, pady=11)
    activation.grid(row=1, column=0, sticky="ew", pady=(18, 12))
    tk.Label(activation, text="ACTIVATION", bg=panel, fg=accent, font=("Consolas", 9, "bold")).pack(side="left", padx=(0, 14))
    tk.Label(activation, text="COLD COFFEE COMPATIBILITY  /  冷咖啡入口  /  [[ENI:PROFILE=MAX]]", bg=panel, fg=text, font=("Consolas", 9)).pack(side="left")

    settings = tk.Frame(root, bg=panel, highlightthickness=1, highlightbackground=line, padx=16, pady=14)
    settings.grid(row=2, column=0, sticky="ew")
    settings.grid_columnconfigure(1, weight=1)
    tk.Label(settings, text="部署目录", bg=panel, fg=dim).grid(row=0, column=0, sticky="w", padx=(0, 10))
    home_var = tk.StringVar(value=str(resolve_layout(home).home))
    home_entry = tk.Entry(settings, textvariable=home_var, bg="#08131D", fg=text, insertbackground=text, relief="flat", highlightthickness=1, highlightbackground=line)
    home_entry.grid(row=0, column=1, sticky="ew", ipady=7)
    tk.Label(settings, text="配置", bg=panel, fg=dim).grid(row=0, column=2, sticky="w", padx=(16, 8))
    profile_var = tk.StringVar(value="max")
    profiles = profile_names()
    if "max" not in profiles and profiles:
        profile_var.set(profiles[0])
    ttk.Combobox(settings, values=profiles, textvariable=profile_var, state="readonly", width=15).grid(row=0, column=3, sticky="e")

    body = tk.Frame(root, bg=bg)
    body.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
    body.grid_columnconfigure(0, weight=1)
    body.grid_rowconfigure(1, weight=1)

    actions = tk.Frame(body, bg=bg)
    actions.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    state_var = tk.StringVar(value="等待操作")
    tk.Label(actions, textvariable=state_var, bg=bg, fg=dim, font=("Consolas", 9)).pack(side="right", padx=(14, 0))

    output_frame = tk.Frame(body, bg=panel, highlightthickness=1, highlightbackground=line)
    output_frame.grid(row=1, column=0, sticky="nsew")
    output_frame.grid_rowconfigure(1, weight=1)
    output_frame.grid_columnconfigure(0, weight=1)
    tk.Label(output_frame, text="OPERATION OUTPUT", bg=panel, fg=accent, font=("Consolas", 9, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 0))
    output = tk.Text(output_frame, bg="#08131D", fg=text, insertbackground=accent, relief="flat", font=("Consolas", 10), padx=15, pady=14, wrap="word")
    output.grid(row=1, column=0, sticky="nsew", padx=12, pady=10)
    output.tag_configure("ok", foreground=success)
    output.tag_configure("error", foreground=error)

    def render(value: dict[str, Any], *, ok: bool = True) -> None:
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), "ok" if ok else "error")
        output.configure(state="disabled")
        badge.configure(text="●  READY" if ok else "●  CHECK", fg=success if ok else error)

    def run(label: str, fn: Callable[[], dict[str, Any]]) -> None:
        state_var.set(f"运行中 · {label}")
        badge.configure(text="●  RUNNING", fg=accent)
        for child in actions.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state="disabled")

        def worker() -> None:
            try:
                value = fn()
                ok = bool(value.get("ok", True))
                window.after(0, lambda: render(value, ok=ok))
                window.after(0, lambda: state_var.set("完成 · " + label if ok else "已返回错误 · " + label))
            except Exception as exc:  # noqa: BLE001
                value = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                window.after(0, lambda: render(value, ok=False))
                window.after(0, lambda: state_var.set("错误 · " + label))
            finally:
                window.after(0, lambda: [child.configure(state="normal") for child in actions.winfo_children() if isinstance(child, ttk.Button)])

        threading.Thread(target=worker, daemon=True).start()

    def with_profile(fn: Action) -> Callable[[], dict[str, Any]]:
        return lambda: fn(Path(home_var.get()), profile_var.get())

    def add_button(label: str, command: Callable[[], None], *, primary: bool = False) -> None:
        ttk.Button(actions, text=label, style="Primary.TButton" if primary else "Quiet.TButton", command=command).pack(side="left", padx=(0, 8))

    add_button("预览变更", lambda: run("预览", with_profile(preview)))
    add_button("一键部署", lambda: run("部署", with_profile(deploy)), primary=True)
    add_button("验证部署", lambda: run("验证", lambda: verify(Path(home_var.get()))))
    add_button("完整恢复", lambda: run("恢复", lambda: restore(Path(home_var.get()))))
    add_button("导出模板", lambda: run("导出", lambda: export_template(Path(home_var.get()) / "coldbrew-export", profile_var.get())))
    add_button("社区入口", lambda: render({"action": "community", "ok": True, **community}))

    tk.Label(root, text="快捷键：Ctrl+P 预览  ·  Ctrl+D 部署  ·  Ctrl+V 验证  ·  Ctrl+R 恢复", bg=bg, fg="#617B88", font=("Consolas", 8)).grid(row=4, column=0, sticky="w", pady=(10, 0))
    window.bind("<Control-p>", lambda _event: run("预览", with_profile(preview)))
    window.bind("<Control-d>", lambda _event: run("部署", with_profile(deploy)))
    window.bind("<Control-v>", lambda _event: run("验证", lambda: verify(Path(home_var.get()))))
    window.bind("<Control-r>", lambda _event: run("恢复", lambda: restore(Path(home_var.get()))))
    home_entry.focus_set()
    window.mainloop()
    return 0

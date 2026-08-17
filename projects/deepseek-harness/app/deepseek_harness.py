#!/usr/bin/env python3
"""DeepSeek Harness ColdBrew: preview, deploy, verify and restore a local adapter."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import webbrowser
from pathlib import Path

from coldbrew_activation import activation_payload, verify_canonical_contract
from profile_engine import profile_names
from transaction import TransactionError, deploy, preview, resolve_layout, restore, verify

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT.parent / "shared"
if not SHARED.is_dir():
    SHARED = ROOT / "shared"
sys.path.insert(0, str(SHARED))
from coldbrew_ui import launch_shared_gui

COMMUNITY = {

    "wechat": "微信群：冷咖啡破甲社区",
    "wechat_qr": str(ROOT / "docs" / "images" / "wechat-group.png"),
}


def emit(value: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for key, item in value.items():
            print(f"{key}={item}")


def export_template(destination: Path, profile: str) -> dict:
    from profile_engine import compose_prompt
    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    prompt = destination / "system-prompt.md"
    session = destination / "session-template.json"
    prompt.write_text(compose_prompt(profile), encoding="utf-8", newline="\n")
    session.write_text(json.dumps({"platform": "DeepSeek Harness", "profile": profile, "system_prompt_file": prompt.name}, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"action": "export", "ok": True, "prompt": str(prompt), "template": str(session)}


def _legacy_launch_gui(home: Path | None = None) -> int:
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Tk()
    window.title("DeepSeek Harness ColdBrew v1.0.1")
    window.geometry("940x650")
    window.minsize(820, 570)
    bg, panel, text, dim, accent = "#071019", "#0f1b27", "#edf5f8", "#8fa3b3", "#23f5d7" if "Grok" in "DeepSeek Harness ColdBrew" else "#397dff"
    window.configure(bg=bg)
    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure("Action.TButton", background=accent, foreground="#031015", padding=(14, 10), borderwidth=0)
    style.configure("Quiet.TButton", background="#172635", foreground=text, padding=(12, 9), borderwidth=0)
    root = tk.Frame(window, bg=bg, padx=30, pady=25)
    root.pack(fill="both", expand=True)
    tk.Label(root, text="COLDBREW / DeepSeek Harness", bg=bg, fg=accent, font=("Consolas", 10, "bold")).pack(anchor="w")
    tk.Label(root, text="DeepSeek Harness 破甲", bg=bg, fg=text, font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(4, 2))
    tk.Label(root, text="深海控制台中的可逆 Harness 配置与提示词部署器", bg=bg, fg=dim, font=("Segoe UI", 11)).pack(anchor="w")
    controls = tk.Frame(root, bg=panel, padx=18, pady=18)
    controls.pack(fill="x", pady=(22, 14))
    home_var = tk.StringVar(value=str(resolve_layout(home).home))
    profile_var = tk.StringVar(value="max")
    tk.Label(controls, text="部署目录", bg=panel, fg=dim).grid(row=0, column=0, sticky="w")
    tk.Entry(controls, textvariable=home_var, bg="#08131d", fg=text, insertbackground=text, relief="flat").grid(row=1, column=0, sticky="ew", padx=(0, 12), ipady=8)
    ttk.Combobox(controls, values=profile_names(), textvariable=profile_var, state="readonly", width=13).grid(row=1, column=1)
    controls.columnconfigure(0, weight=1)
    output = tk.Text(root, bg="#08131d", fg=text, insertbackground=text, relief="flat", font=("Consolas", 10), padx=15, pady=15, wrap="word")
    output.pack(fill="both", expand=True)

    def run(action):
        try:
            target = Path(home_var.get())
            value = action(target)
            output.delete("1.0", "end")
            output.insert("1.0", json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
        except Exception as exc:
            messagebox.showerror("ColdBrew", str(exc))

    buttons = tk.Frame(root, bg=bg)
    buttons.pack(fill="x", pady=(14, 0))
    ttk.Button(buttons, text="预览变更", style="Quiet.TButton", command=lambda: run(lambda p: preview(p, profile_var.get()))).pack(side="left", padx=(0, 7))
    ttk.Button(buttons, text="一键部署", style="Action.TButton", command=lambda: run(lambda p: deploy(p, profile_var.get()))).pack(side="left", padx=7)
    ttk.Button(buttons, text="验证部署", style="Quiet.TButton", command=lambda: run(verify)).pack(side="left", padx=7)
    ttk.Button(buttons, text="完整恢复", style="Quiet.TButton", command=lambda: run(restore)).pack(side="left", padx=7)
    ttk.Button(buttons, text="社区入口", style="Quiet.TButton", command=lambda: output.insert("end", "\n\n" + json.dumps(COMMUNITY, ensure_ascii=False, indent=2))).pack(side="right")
    window.mainloop()
    return 0


def launch_gui(home: Path | None = None) -> int:
    """Open the shared ColdBrew workbench while preserving CLI contracts."""
    return launch_shared_gui(
        title="DeepSeek Harness ColdBrew · Workbench",
        model="DeepSeek v4 Pro",
        subtitle="Harness 会话适配器 · 配置预览、事务式部署与一键恢复",
        accent="#7AA2FF",
        home=home,
        resolve_layout=resolve_layout,
        profile_names=profile_names,
        preview=preview,
        deploy=deploy,
        verify=verify,
        restore=restore,
        export_template=export_template,
        community=COMMUNITY,
    )


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--home", type=Path)
    sub = command.add_subparsers(dest="command")
    activate = sub.add_parser("activate")
    activate.add_argument("--trigger", required=True)
    activate.add_argument("--json", action="store_true")
    for name in ("preview", "deploy"):
        item = sub.add_parser(name)
        item.add_argument("--profile", choices=profile_names(), default="max")
        item.add_argument("--json", action="store_true")
    for name in ("verify", "restore", "status", "community"):
        item = sub.add_parser(name)
        item.add_argument("--json", action="store_true")
    export = sub.add_parser("export")
    export.add_argument("--destination", type=Path, required=True)
    export.add_argument("--profile", choices=profile_names(), default="max")
    export.add_argument("--json", action="store_true")
    sub.add_parser("gui")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command in (None, "gui"):
        return launch_gui(args.home)
    try:
        if args.command == "activate":
            result = activation_payload(args.trigger)
            emit(result, args.json)
            return 0 if result["active"] and verify_canonical_contract() else 2
        if args.command == "preview":
            result = preview(args.home, args.profile)
        elif args.command == "deploy":
            result = deploy(args.home, args.profile)
        elif args.command == "verify":
            result = verify(args.home)
        elif args.command == "restore":
            result = restore(args.home)
        elif args.command == "status":
            result = preview(args.home)
            result["action"] = "status"
        elif args.command == "community":
            result = {"action": "community", "ok": True, **COMMUNITY}
        else:
            result = export_template(args.destination, args.profile)
        emit(result, args.json)
        return 0 if result.get("ok", True) else 1
    except (TransactionError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Copy-only overlay tamper-detection probe for a local Windows package.

The source package is never written.  The probe copies it to an output folder,
appends a harmless data overlay to the copied executable, launches that copy
with its UI hidden for a bounded observation period, and records only whether
the process remained alive.  It does not submit credentials or alter program
authorization state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--exe-name", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--observe-seconds", type=float, default=5.0)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    source_exe = (source_root / args.exe_name).resolve()
    out_dir = args.out_dir.resolve()
    if not source_root.is_dir() or not source_exe.is_file():
        raise SystemExit("source root or executable not found")
    if source_root not in source_exe.parents:
        raise SystemExit("executable must reside under source root")
    if out_dir.exists():
        raise SystemExit("output directory already exists")

    source_hash_before = sha256(source_exe)
    shutil.copytree(source_root, out_dir)
    copied_exe = out_dir / args.exe_name
    copied_hash_before = sha256(copied_exe)
    overlay = b"\r\nCOLD_COFFEE_AUDIT_OVERLAY_V1\r\n"
    with copied_exe.open("ab") as handle:
        handle.write(overlay)
    copied_hash_after = sha256(copied_exe)

    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

    started_utc = datetime.now(timezone.utc).isoformat()
    proc = subprocess.Popen(
        [str(copied_exe)],
        cwd=str(out_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    deadline = time.monotonic() + max(0.5, args.observe_seconds)
    while time.monotonic() < deadline and proc.poll() is None:
        time.sleep(0.1)
    alive_after_observation = proc.poll() is None
    exit_code_before_cleanup = proc.poll()
    cleanup = "not_needed"
    if alive_after_observation:
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            creationflags=creationflags,
        )
        cleanup = "taskkill_tree_requested"

    source_hash_after = sha256(source_exe)
    record = {
        "created_utc": started_utc,
        "probe": "copy_only_overlay_launch",
        "source_root": str(source_root),
        "source_exe": str(source_exe),
        "copy_root": str(out_dir),
        "copy_exe": str(copied_exe),
        "overlay_bytes": len(overlay),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "source_unchanged": source_hash_before == source_hash_after,
        "copy_sha256_before_overlay": copied_hash_before,
        "copy_sha256_after_overlay": copied_hash_after,
        "process_id": proc.pid,
        "observe_seconds": args.observe_seconds,
        "alive_after_observation": alive_after_observation,
        "exit_code_before_cleanup": exit_code_before_cleanup,
        "cleanup": cleanup,
        "interpretation_limit": (
            "A surviving process after a trailing-data change is evidence that this "
            "specific modification did not block launch. It is not proof that all "
            "integrity protections are absent or that authorization was affected."
        ),
    }
    report = out_dir.parent / f"{out_dir.name}_result.json"
    report.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(report), "alive": alive_after_observation,
                      "source_unchanged": record["source_unchanged"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

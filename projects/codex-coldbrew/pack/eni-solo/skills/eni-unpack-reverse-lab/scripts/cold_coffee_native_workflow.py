#!/usr/bin/env python3
"""Add-only orchestration for local PE triage and bounded runtime capture."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys


def run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, capture_output=True, text=True, errors="replace")
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def file_hash(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cold Coffee local native reverse/unpack automation")
    parser.add_argument("artifact", type=pathlib.Path)
    parser.add_argument("--case-dir", type=pathlib.Path, required=True)
    parser.add_argument("--dynamic", action="store_true", help="Run only copied target processes, hidden and time-bounded")
    args = parser.parse_args()

    artifact = args.artifact.resolve()
    if not artifact.is_file():
        raise SystemExit("artifact must be an existing file")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = args.case_dir / "cold_coffee_runs" / stamp
    triage = run_root / "triage"
    artifacts = run_root / "artifacts"
    work = run_root / "work"
    for folder in (triage, artifacts, work):
        folder.mkdir(parents=True, exist_ok=False)
    scripts = pathlib.Path(__file__).resolve().parent
    manifest: dict[str, object] = {
        "status": "started",
        "artifact": str(artifact),
        "baseline_sha256": file_hash(artifact),
        "dynamic_requested": args.dynamic,
        "runs": [],
        "original_modified": False,
    }
    manifest["runs"].append(run([sys.executable, str(scripts / "pe_pack_triage.py"), str(artifact), "--out", str(triage / "pe-pack.json")]))
    manifest["runs"].append(run([sys.executable, str(scripts / "reverse_tool_audit.py"), "--out", str(triage / "reverse-tools.json")]))

    if args.dynamic:
        copied_parent = work / "copied_runtime"
        shutil.copytree(artifact.parent, copied_parent)
        copied_artifact = copied_parent / artifact.name
        manifest["copied_artifact"] = str(copied_artifact)
        manifest["copied_artifact_sha256"] = file_hash(copied_artifact)
        manifest["runs"].append(run([
            sys.executable, str(scripts / "runtime_exec_surface.py"), "--exe", str(copied_artifact),
            "--cwd", str(copied_parent), "--out", str(triage / "runtime-exec-surface.json"), "--seconds", "3",
        ]))
        manifest["runs"].append(run([
            sys.executable, str(scripts / "capture_private_exec_regions.py"), "--exe", str(copied_artifact),
            "--cwd", str(copied_parent), "--out-dir", str(artifacts / "private-exec-capture"), "--seconds", "3",
        ]))
    manifest["original_sha256_after"] = file_hash(artifact)
    manifest["original_hash_unchanged"] = manifest["baseline_sha256"] == manifest["original_sha256_after"]
    manifest["status"] = "complete" if all(int(item["returncode"]) == 0 for item in manifest["runs"]) else "partial"
    (run_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="ascii")
    print(json.dumps({"run_root": str(run_root), "status": manifest["status"], "original_hash_unchanged": manifest["original_hash_unchanged"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Offline triage for local sandbox / CTF reverse-engineering artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

MAGIC_HINTS = [
    (b"MZ", "PE/Windows executable or DLL"),
    (b"\x7fELF", "ELF/Linux or Unix binary"),
    (b"PK\x03\x04", "ZIP-based file: APK/JAR/DOCX/XLSX/IPA/ZIP"),
    (b"%PDF", "PDF document"),
    (b"\xca\xfe\xba\xbe", "Java class / Mach-O fat candidate"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit little-endian"),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit big-endian"),
    (b"\x7fCGC", "CGC CTF binary"),
    (b"dex\n", "Android DEX"),
]

PRINTABLE_RE = re.compile(rb"[ -~]{4,}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts if c)


def detect_magic(head: bytes, suffix: str) -> List[str]:
    hints = [label for magic, label in MAGIC_HINTS if head.startswith(magic)]
    ext = suffix.lower()
    if ext == ".apk": hints.append("Android APK")
    if ext == ".ipa": hints.append("iOS IPA")
    if ext in [".so", ".dll", ".dylib"]: hints.append("shared library")
    if ext in [".bin", ".img", ".fw"]: hints.append("firmware/blob candidate")
    return sorted(set(hints)) or ["unknown binary/data"]


def extract_strings(path: Path, limit: int = 80) -> List[str]:
    data = path.read_bytes()[:20 * 1024 * 1024]
    found = []
    for m in PRINTABLE_RE.finditer(data):
        s = m.group().decode("utf-8", errors="replace")
        if any(token in s.lower() for token in ["flag", "ctf", "key", "pass", "http", "/bin/", "error", "usage", "license", "serial", "debug"]):
            found.append(s[:240])
        if len(found) >= limit:
            break
    return found


def run_if_available(cmd: List[str], timeout: int = 8) -> str:
    if not shutil.which(cmd[0]):
        return ""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr).strip()[:4000]
    except Exception as e:
        return f"error: {e}"


def recommendations(hints: List[str]) -> List[str]:
    text = " ".join(hints).lower()
    rec = ["Preserve original; analyze a copy; record offsets/hashes/tool versions."]
    if "pe/" in text or "windows" in text:
        rec += ["Use Ghidra or x64dbg for control-flow analysis.", "Use Detect It Easy/PE-bear/capa if available."]
    if "elf" in text or "cgc" in text:
        rec += ["Use Ghidra/radare2 for static analysis.", "Use gdb + pwndbg/GEF for dynamic tracing in a sandbox.", "Use checksec and strings/imports to rank targets."]
    if "android" in text or "apk" in text or "dex" in text:
        rec += ["Use JADX for Java/Kotlin decompilation.", "Use apktool for resources/manifest; Frida for local runtime hooks if selected."]
    if "zip" in text:
        rec += ["List archive contents before extraction; treat APK/JAR/Office/IPA separately based on filenames."]
    if "firmware" in text or "blob" in text:
        rec += ["Use binwalk and filesystem extraction in a disposable workspace.", "Inspect init scripts, web routes, configs, and hardcoded credentials."]
    if "pdf" in text:
        rec += ["Use pdfid/pdf-parser/oletools-style offline document triage."]
    return rec


def triage(path: Path) -> Dict[str, object]:
    if not path.exists() or not path.is_file():
        raise SystemExit(f"artifact not found: {path}")
    data = path.read_bytes()
    head = data[:4096]
    hints = detect_magic(head, path.suffix)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "path": str(path.resolve()),
        "name": path.name,
        "size": path.stat().st_size,
        "sha256": sha256(path),
        "head_hex": head[:64].hex(),
        "entropy_first_1mb": round(entropy(data[:1024 * 1024]), 4),
        "type_hints": hints,
        "interesting_strings": extract_strings(path),
        "external_tool_output": {},
        "recommendations": recommendations(hints),
    }
    file_out = run_if_available(["file", str(path)])
    if file_out:
        result["external_tool_output"]["file"] = file_out  # type: ignore[index]
    rabin = run_if_available(["rabin2", "-I", str(path)])
    if rabin:
        result["external_tool_output"]["rabin2 -I"] = rabin  # type: ignore[index]
    return result


def render_markdown(data: Dict[str, object]) -> str:
    lines = [
        f"# Artifact Triage: {data['name']}", "",
        f"Generated: {data['generated_at']}",
        f"Path: `{data['path']}`",
        f"Size: {data['size']} bytes",
        f"SHA-256: `{data['sha256']}`",
        f"Entropy first 1MiB: {data['entropy_first_1mb']}",
        f"Type hints: {', '.join(data['type_hints'])}", "",
        "## Recommendations", "",
    ]
    for r in data["recommendations"]:
        lines.append(f"- {r}")
    lines += ["", "## Interesting strings", ""]
    strings = data.get("interesting_strings", [])
    if strings:
        for s in strings:
            lines.append(f"- `{s.replace('`', '')}`")
    else:
        lines.append("No high-signal printable strings found in first 20MiB.")
    lines += ["", "## External tool output", ""]
    ext = data.get("external_tool_output", {})
    if ext:
        for k, v in ext.items():
            lines += [f"### {k}", "", "```", str(v), "```", ""]
    else:
        lines.append("No external triage tools were available or produced output.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact")
    parser.add_argument("--out", required=True, help="Output directory for JSON and Markdown")
    args = parser.parse_args()
    path = Path(args.artifact)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data = triage(path)
    base = path.name.replace("/", "_").replace("\\", "_")
    json_path = out / f"{base}.triage.json"
    md_path = out / f"{base}.triage.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(data), encoding="utf-8")
    print(str(md_path.resolve()))


if __name__ == "__main__":
    main()

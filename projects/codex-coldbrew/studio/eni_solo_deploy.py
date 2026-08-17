#!/usr/bin/env python3
"""eni-solo v4.0.0 deploy bridge — the GPT-5.6 ColdBrew slot.

Wraps the bundled eni-solo package (``pack/eni-solo``) in a reversible
orchestration layer::

    backup -> remove obsolete -> install skills -> manifest -> prompt
    -> hook -> inject -> activate -> verify -> receipt

Every write lands under CODEX_HOME (default ``~/.codex``) and the full
rollback path is recorded in the install manifest. All of the real work is
done by the package's own scripts (``ishii_auto_route.py``, ``eni-inject.py``,
``activate_solo.py``, ``verify_activation.py``); this module only owns the
backup / ordering / receipt / rollback shell around them.

Commands::

    python eni_solo_deploy.py deploy --yes [--codex-home PATH] [--json]
    python eni_solo_deploy.py restore --yes [--codex-home PATH] [--json]
    python eni_solo_deploy.py status  [--codex-home PATH] [--json]
    python eni_solo_deploy.py verify  [--codex-home PATH] [--json]
    python eni_solo_deploy.py doctor  [--codex-home PATH] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACK_NAME = "eni-solo"
PACK_VERSION = "4.0.0"
MANIFEST_DIR = "eni-solo"
PROMPT_DEST = "eni-solo-v4.0.0.md"
MANIFEST_FILENAME = f"install-manifest-v{PACK_VERSION}.json"
VERIFICATION_FILENAME = f"install-verification-v{PACK_VERSION}.json"


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                pass


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def pack_root() -> Path:
    """Locate the bundled eni-solo package root."""
    override = os.environ.get("COLDBREW_ENI_SOLO_PACK")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "pack" / "eni-solo"


def resolve_home(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def emit(value: dict[str, Any], as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def run_py(script: Path, args: list[str], cwd: Path) -> dict[str, Any]:
    """Run a package python script, capture stdout, parse it as JSON."""
    command = [sys.executable, str(script), *args]
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=300,
    )
    if proc.returncode != 0:
        detail = (proc.stdout or "").strip() or (proc.stderr or "").strip()
        raise RuntimeError(f"{script.name} failed (exit {proc.returncode}): {detail[:800]}")
    stdout = (proc.stdout or "").strip()
    if not stdout:
        return {"ok": True, "script": script.name, "output": "(empty)"}
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return {"ok": True, "script": script.name, "output": stdout[:2000]}
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{script.name} output is not a JSON object")
    return parsed


def move_or_backup(source: Path, destination: Path) -> None:
    """Move a path aside; replaces an existing destination first."""
    if destination.exists():
        shutil.rmtree(destination, ignore_errors=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)


class SoloDeployError(RuntimeError):
    """Expected, user-actionable failure."""


def validate_pack(pack: Path) -> None:
    if not pack.is_dir():
        raise SoloDeployError(f"eni-solo pack is missing: {pack}")
    package = read_json(pack / "manifest" / "package.json")
    if package.get("name") != PACK_NAME or package.get("version") != PACK_VERSION:
        raise SoloDeployError(
            f"Unexpected pack identity: {package.get('name')} {package.get('version')}"
        )
    for required in (
        "scripts/ishii_auto_route.py",
        "eni-inject.py",
        "scripts/activate_solo.py",
        "scripts/verify_activation.py",
        "global/AGENTS.md",
        "prompts/eni-solo.md",
        "manifest/removed-skills.json",
    ):
        if not (pack / required).is_file():
            raise SoloDeployError(f"Pack is incomplete, missing {required}")


def deploy(home: Path, force: bool) -> dict[str, Any]:
    pack = pack_root()
    validate_pack(pack)
    home.mkdir(parents=True, exist_ok=True)

    manifest_path = home / MANIFEST_DIR / MANIFEST_FILENAME
    if manifest_path.exists() and not force:
        raise SoloDeployError(
            f"eni-solo is already deployed ({manifest_path}). "
            "Use --force to re-deploy, or restore first."
        )

    stamp = utc_stamp()
    backup_dir = home / "backups" / f"{PACK_NAME}-{PACK_VERSION}-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    skills_root = home / "skills"
    prompts_root = home / "prompts"

    # Rollback ledger. Each entry is a callable that undoes one step.
    rollback: list[Any] = []
    installed_skills: list[str] = []
    changed_skills: list[str] = []
    removed_obsolete: list[str] = []
    solo_existed = False

    def push_rollback(undo) -> None:  # noqa: ANN001
        rollback.append(undo)

    def do_rollback() -> None:
        for undo in reversed(rollback):
            try:
                undo()
            except Exception as exc:  # noqa: BLE001
                print(f"rollback step failed: {exc}", file=sys.stderr)

    try:
        # 1. Snapshot the three root files we or our scripts may touch.
        root_snapshots: dict[str, Path | None] = {}
        for filename in ("AGENTS.md", "hooks.json", "config.toml"):
            source = home / filename
            if source.is_file():
                target = backup_dir / filename
                shutil.copy2(source, target)
                root_snapshots[filename] = target
            else:
                root_snapshots[filename] = None

        # 2. Remove obsolete skills listed by the package.
        removed_cfg = read_json(pack / "manifest" / "removed-skills.json")
        for name in removed_cfg.get("skills", []):
            target = skills_root / str(name)
            if target.exists():
                move_or_backup(target, backup_dir / str(name))
                removed_obsolete.append(str(name))
                push_rollback(
                    lambda t=target, b=backup_dir / str(name): move_or_backup(b, t)
                )

        # 3. Install every packaged skill via a stage-and-swap move.
        for skill_dir in sorted((pack / "skills").iterdir()):
            if not skill_dir.is_dir():
                continue
            name = skill_dir.name
            target = skills_root / name
            stage = skills_root / f".eni-solo-stage-{name}-{stamp}"
            shutil.copytree(skill_dir, stage)
            existed = target.exists()
            if existed:
                move_or_backup(target, backup_dir / name)
            os.replace(stage, target)
            installed_skills.append(name)
            changed_skills.append(name)

            def undo_skill(t=target, b=backup_dir / name, existed=existed) -> None:
                if t.exists():
                    shutil.rmtree(t)
                if existed and b.exists():
                    os.replace(b, t)

            push_rollback(undo_skill)

        # 4. Deploy the manifest directory (routing rules, identity, etc).
        solo_dir = home / MANIFEST_DIR
        solo_existed = solo_dir.exists()
        if solo_existed:
            move_or_backup(solo_dir, backup_dir / MANIFEST_DIR)
        solo_stage = home / f".eni-solo-stage-{stamp}"
        shutil.copytree(pack / "manifest", solo_stage / "manifest")
        os.replace(solo_stage, solo_dir)
        push_rollback(
            lambda: (
                shutil.rmtree(solo_dir, ignore_errors=True),
                os.replace(backup_dir / MANIFEST_DIR, solo_dir) if solo_existed else None,
            )
        )

        # 5. Copy the persona prompt into place.
        prompt_target = prompts_root / PROMPT_DEST
        prompt_existed = prompt_target.is_file()
        if prompt_existed:
            shutil.copy2(prompt_target, backup_dir / PROMPT_DEST)
        prompts_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pack / "prompts" / "eni-solo.md", prompt_target)
        push_rollback(
            lambda: (
                prompt_target.unlink(missing_ok=True) if not prompt_existed
                else shutil.copy2(backup_dir / PROMPT_DEST, prompt_target)
            )
        )

        # 6. Install the UserPromptSubmit auto-route hook.
        hook_result = run_py(
            pack / "scripts" / "ishii_auto_route.py",
            ["--install", "--codex-home", str(home)],
            cwd=pack,
        )
        if not hook_result.get("installed"):
            raise SoloDeployError(f"Hook install reported failure: {hook_result}")
        # hooks.json is restored from the snapshot on rollback (step 1).
        hook_file = home / "hooks" / "ishii_auto_route.py"
        if hook_file.is_file() and not root_snapshots.get("hooks.json"):
            push_rollback(lambda hf=hook_file: hf.unlink(missing_ok=True))

        # 7. Point the model instructions file at the jailbreak prompt.
        inject_result = run_py(
            pack / "eni-inject.py",
            ["--apply", "--codex-dir", str(home)],
            cwd=pack,
        )
        if not inject_result.get("ok"):
            raise SoloDeployError(f"model_instructions_file activation failed: {inject_result}")

        # 8. Static activation: refresh AGENTS.md with the solo global block.
        activation = run_py(
            pack / "scripts" / "activate_solo.py",
            ["--codex-home", str(home), "--global-block", str(pack / "global" / "AGENTS.md")],
            cwd=pack,
        )

        # 9. Verification gate.
        verification_path = solo_dir / VERIFICATION_FILENAME
        verification = run_py(
            pack / "scripts" / "verify_activation.py",
            ["--codex-home", str(home), "--output", str(verification_path)],
            cwd=pack,
        )
        if not verification.get("passed"):
            raise SoloDeployError(
                f"eni-solo verification failed: {verification_path} -> {verification}"
            )

        # 10. Commit the install manifest.
        manifest = {
            "name": PACK_NAME,
            "version": PACK_VERSION,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "installed_skills": installed_skills,
            "changed_skills": changed_skills,
            "removed_obsolete_skills": removed_obsolete,
            "hooks_installed": True,
            "plugin_installed": False,
            "runtime": "model instructions + UserPromptSubmit auto-route hook + deterministic router + sequential workflow stages",
            "activation": activation,
            "hook": hook_result,
            "model_instructions_file": "eni-jailbreak-v4.md",
            "backup": str(backup_dir),
            "verification": verification,
            "verification_file": str(verification_path),
        }
        write_json(manifest_path, manifest)
        return {
            "ok": True,
            "action": "deploy",
            "name": PACK_NAME,
            "version": PACK_VERSION,
            "codex_home": str(home),
            "installed_skills": len(installed_skills),
            "changed_skills": changed_skills,
            "removed_obsolete_skills": removed_obsolete,
            "verification_passed": bool(verification.get("passed")),
            "manifest": str(manifest_path),
            "backup": str(backup_dir),
        }
    except Exception as exc:
        do_rollback()
        if isinstance(exc, SoloDeployError):
            raise
        raise SoloDeployError(f"deploy failed and was rolled back: {exc}") from exc


def restore(home: Path) -> dict[str, Any]:
    manifest_path = home / MANIFEST_DIR / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise SoloDeployError(f"No install manifest found: {manifest_path}")
    manifest = read_json(manifest_path)

    backup_dir = Path(manifest.get("backup") or "")
    if not backup_dir.is_dir():
        raise SoloDeployError(f"Backup directory is missing: {backup_dir}")

    changes: list[str] = []

    # Undo the injector's own footprint first (eni-jailbreak-v4.md and its
    # .bak sidecars); the snapshot restore below is byte-authoritative for
    # config.toml regardless of what --reset did or did not touch.
    pack = pack_root()
    inject = pack / "eni-inject.py"
    if inject.is_file() and (home / "eni-jailbreak-v4.md").is_file():
        try:
            run_py(inject, ["--reset", "--codex-dir", str(home)], cwd=pack)
            changes.append("eni-inject --reset completed")
        except RuntimeError as exc:
            changes.append(f"eni-inject --reset skipped: {exc}")
    for leftover in sorted(home.glob("config.toml.eni-jailbreak.bak*")):
        try:
            leftover.unlink()
            changes.append(f"removed {leftover.name}")
        except OSError:
            pass
    jailbreak_prompt = home / "eni-jailbreak-v4.md"
    if jailbreak_prompt.is_file():
        jailbreak_prompt.unlink()
        changes.append("removed eni-jailbreak-v4.md")

    def restore_root(filename: str) -> None:
        snapshot = backup_dir / filename
        target = home / filename
        if snapshot.is_file():
            shutil.copy2(snapshot, target)
            changes.append(f"restored {filename}")
        elif target.exists():
            target.unlink()
            changes.append(f"removed {filename} (not present before deploy)")

    # Root files first: this also drops the hook registration and config pointer.
    for filename in ("AGENTS.md", "hooks.json", "config.toml"):
        restore_root(filename)

    # Skills: restore any displaced originals, otherwise remove what we added.
    for name in manifest.get("installed_skills", []):
        target = home / "skills" / str(name)
        displaced = backup_dir / str(name)
        if displaced.exists():
            if target.exists():
                shutil.rmtree(target)
            os.replace(displaced, target)
            changes.append(f"restored skill {name}")
        elif target.exists():
            shutil.rmtree(target)
            changes.append(f"removed skill {name}")

    # Obsolete skills that we moved away come back too.
    for name in manifest.get("removed_obsolete_skills", []):
        displaced = backup_dir / str(name)
        if displaced.exists():
            target = home / "skills" / str(name)
            if target.exists():
                shutil.rmtree(target)
            os.replace(displaced, target)
            changes.append(f"restored obsolete skill {name}")

    # Prompt file.
    prompt_target = home / "prompts" / PROMPT_DEST
    prompt_snapshot = backup_dir / PROMPT_DEST
    if prompt_snapshot.is_file():
        shutil.copy2(prompt_snapshot, prompt_target)
        changes.append(f"restored {PROMPT_DEST}")
    elif prompt_target.exists():
        prompt_target.unlink()
        changes.append(f"removed {PROMPT_DEST}")

    # Stray hook file when the restored hooks.json no longer references it.
    hook_file = home / "hooks" / "ishii_auto_route.py"
    if hook_file.is_file():
        hooks_config = home / "hooks.json"
        still_registered = False
        if hooks_config.is_file():
            try:
                text = hooks_config.read_text(encoding="utf-8-sig").casefold()
                still_registered = "ishii_auto_route" in text
            except (OSError, UnicodeError):
                pass
        if not still_registered:
            hook_file.unlink()
            changes.append("removed stray ishii_auto_route.py")

    # Drop the solo manifest directory (it only ever holds package artifacts).
    solo_dir = home / MANIFEST_DIR
    displaced_solo = backup_dir / MANIFEST_DIR
    if displaced_solo.exists():
        if solo_dir.exists():
            shutil.rmtree(solo_dir)
        os.replace(displaced_solo, solo_dir)
        changes.append("restored previous eni-solo directory")
    elif solo_dir.exists():
        shutil.rmtree(solo_dir)
        changes.append("removed eni-solo directory")

    record_path = backup_dir / "restore-record.json"
    record = {
        "restored_at": datetime.now(timezone.utc).isoformat(),
        "codex_home": str(home),
        "changes": changes,
    }
    write_json(record_path, record)
    return {
        "ok": True,
        "action": "restore",
        "codex_home": str(home),
        "changes": changes,
        "record": str(record_path),
    }


def status(home: Path) -> dict[str, Any]:
    manifest_path = home / MANIFEST_DIR / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return {"ok": True, "action": "status", "deployed": False, "codex_home": str(home)}
    manifest = read_json(manifest_path)
    backup = Path(manifest.get("backup") or "")
    return {
        "ok": True,
        "action": "status",
        "deployed": True,
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "installed_at": manifest.get("installed_at"),
        "installed_skills": len(manifest.get("installed_skills", [])),
        "verification_passed": bool(
            (manifest.get("verification") or {}).get("passed")
        ),
        "backup": str(backup),
        "backup_present": backup.is_dir(),
        "codex_home": str(home),
    }


def verify(home: Path) -> dict[str, Any]:
    pack = pack_root()
    script = pack / "scripts" / "verify_activation.py"
    if not script.is_file():
        raise SoloDeployError(f"Verification script missing: {script}")
    report = run_py(script, ["--codex-home", str(home)], cwd=pack)
    report["ok"] = bool(report.get("passed"))
    report["action"] = "verify"
    report["codex_home"] = str(home)
    return report


def doctor(home: Path) -> dict[str, Any]:
    pack = pack_root()
    findings: dict[str, Any] = {
        "ok": True,
        "action": "doctor",
        "python": sys.executable,
        "pack": str(pack),
        "pack_present": pack.is_dir(),
        "codex_home": str(home),
        "codex_home_present": home.is_dir(),
    }
    try:
        validate_pack(pack)
        findings["pack_valid"] = True
    except SoloDeployError as exc:
        findings["pack_valid"] = False
        findings["pack_error"] = str(exc)
        findings["ok"] = False
    manifest_path = home / MANIFEST_DIR / MANIFEST_FILENAME
    findings["deployed"] = manifest_path.is_file()
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="eni-solo v4.0.0 GPT-5.6 deployment bridge")
    parser.add_argument("command", choices=("deploy", "restore", "status", "verify", "doctor"))
    parser.add_argument("--codex-home", type=Path, help="Codex home; defaults to CODEX_HOME or ~/.codex")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation")
    parser.add_argument("--force", action="store_true", help="Re-deploy over an existing installation")
    parser.add_argument("--json", action="store_true", help="Emit single-line JSON")
    return parser


def confirm(question: str, yes: bool) -> None:
    if yes:
        return
    if not sys.stdin.isatty():
        raise SoloDeployError("Use --yes for a non-interactive operation")
    answer = input(question + " [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        raise SoloDeployError("Cancelled")


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    home = resolve_home(args.codex_home)
    try:
        if args.command == "deploy":
            confirm(f"Deploy eni-solo {PACK_VERSION} to {home}?", args.yes)
            emit(deploy(home, force=args.force), args.json)
        elif args.command == "restore":
            confirm(f"Restore the pre-deploy state in {home}?", args.yes)
            emit(restore(home), args.json)
        elif args.command == "status":
            emit(status(home), args.json)
        elif args.command == "verify":
            result = verify(home)
            emit(result, args.json)
            return 0 if result.get("ok") else 2
        elif args.command == "doctor":
            result = doctor(home)
            emit(result, args.json)
            return 0 if result.get("ok") else 2
        else:
            parser.error(f"Unknown command: {args.command}")
    except SoloDeployError as exc:
        emit({"ok": False, "action": args.command, "error": str(exc)}, args.json)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

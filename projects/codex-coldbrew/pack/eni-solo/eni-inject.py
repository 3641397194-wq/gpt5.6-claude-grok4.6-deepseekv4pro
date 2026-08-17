#!/usr/bin/env python3
"""石井 Reverselab v4 — Codex model_instructions_file injector.

Reads AGENTS.md from the package directory and deploys it into Codex's
native system-instruction slot via config.toml → model_instructions_file.
AGENTS.md is the single source of truth for the jailbreak prompt.

Usage:
  python eni-inject.py              # Interactive menu
  python eni-inject.py --apply      # Non-interactive deploy
  python eni-inject.py --reset      # Restore from backup
  python eni-inject.py --dry-run    # Preview without writing
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROMPT_FILENAME = "eni-jailbreak-v4.md"
CONFIG_KEY = "model_instructions_file"
BACKUP_SUFFIX = ".eni-jailbreak.bak"


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_prompt() -> str:
    """Read the jailbreak prompt from AGENTS.md in the package directory."""
    agents_md = _script_dir() / "AGENTS.md"
    if agents_md.is_file():
        return agents_md.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"AGENTS.md not found at {agents_md}. "
        "The injector must be run from the extracted package directory."
    )


def find_codex_homes() -> list[Path]:
    """Return all discovered Codex home directories."""
    homes: list[Path] = []
    env = os.environ.get("CODEX_HOME")
    if env:
        homes.append(Path(env))
    default = Path.home() / ".codex"
    if default not in homes and default.exists():
        homes.append(default)
    return homes


def config_path(codex_home: Path) -> Path:
    return codex_home / "config.toml"


def prompt_path(codex_home: Path) -> Path:
    return codex_home / PROMPT_FILENAME


def backup_config(config: Path) -> Path:
    """Create timestamped backup of config.toml."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = config.with_suffix(config.suffix + BACKUP_SUFFIX + "_" + ts)
    shutil.copy2(config, backup)
    return backup


def create_baseline_backup(config: Path) -> Path | None:
    """Create a baseline backup if one doesn't exist."""
    baseline = config.with_suffix(config.suffix + BACKUP_SUFFIX)
    if not baseline.exists():
        shutil.copy2(config, baseline)
        return baseline
    return None


def read_config(config: Path) -> list[str]:
    if config.exists():
        return config.read_text(encoding="utf-8").splitlines(keepends=True)
    return []


def write_config(config: Path, lines: list[str]) -> None:
    config.write_text("".join(lines), encoding="utf-8")


def set_model_instructions(config: Path, filename: str, dry_run: bool = False) -> bool:
    """Write or update model_instructions_file in config.toml."""
    lines = read_config(config)
    new_line = f'{CONFIG_KEY} = "./{filename}"\n'

    # Check if already set
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(CONFIG_KEY):
            if stripped == f'{CONFIG_KEY} = "./{filename}"':
                print(f"  [ok] Already set: {filename}")
                return False
            if dry_run:
                print(f"  [dry-run] Would replace line {i+1}: {stripped}")
                print(f"  [dry-run] With: {new_line.strip()}")
            else:
                lines[i] = new_line
                print(f"  Replaced line {i+1}: {stripped} → {filename}")
            write_config(config, lines)
            return True

    # Not found — insert after first [model] line or before first [section]
    inserted = False
    for i, line in enumerate(lines):
        if line.strip().startswith("model "):
            if dry_run:
                print(f"  [dry-run] Would insert after line {i+1}")
            else:
                lines.insert(i + 1, new_line)
            inserted = True
            break

    if not inserted:
        # Insert before first [section] or append
        for i, line in enumerate(lines):
            if line.strip().startswith("["):
                if dry_run:
                    print(f"  [dry-run] Would insert before line {i+1}")
                else:
                    lines.insert(i, new_line)
                inserted = True
                break

    if not inserted:
        if dry_run:
            print("  [dry-run] Would append to end")
        else:
            lines.append(new_line)

    if not dry_run:
        write_config(config, lines)
    return True


def deploy_prompt(codex_home: Path, dry_run: bool = False) -> bool:
    """Deploy the jailbreak prompt to a Codex home directory."""
    config = config_path(codex_home)
    prompt = prompt_path(codex_home)

    if not config.exists():
        if dry_run:
            print(f"  [dry-run] Would create: {config}")
        else:
            config.write_text("", encoding="utf-8")
            print(f"  Created: {config}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Deploying to: {codex_home}")

    # Backup
    if not dry_run:
        baseline = create_baseline_backup(config)
        if baseline:
            print(f"  Baseline backup: {baseline}")
        ts_backup = backup_config(config)
        print(f"  Timestamp backup: {ts_backup}")

    # Write prompt
    prompt_content = _load_prompt()
    if dry_run:
        print(f"  [dry-run] Would write: {prompt} ({len(prompt_content)} chars)")
    else:
        prompt.write_text(prompt_content, encoding="utf-8")
        print(f"  Written: {prompt} ({len(prompt_content)} chars)")

    # Update config
    changed = set_model_instructions(config, PROMPT_FILENAME, dry_run)
    return changed


def reset_codex(codex_home: Path, dry_run: bool = False) -> None:
    """Remove jailbreak and restore config."""
    config = config_path(codex_home)
    prompt = prompt_path(codex_home)

    # Find backups
    backups = sorted(
        config.parent.glob(f"config.toml{BACKUP_SUFFIX}*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    baseline = config.with_suffix(config.suffix + BACKUP_SUFFIX)
    if baseline.exists() and baseline not in backups:
        backups.insert(0, baseline)

    if backups:
        print(f"\nBackups available for {codex_home}:")
        for i, b in enumerate(backups):
            ts = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [{i}] {b.name} ({ts})")

        # Auto-restore newest
        restore = backups[0]
        print(f"\nRestoring: {restore.name}")
        if not dry_run:
            shutil.copy2(restore, config)
            # Remove only our model_instructions_file line
            lines = read_config(config)
            lines = [l for l in lines if CONFIG_KEY not in l or PROMPT_FILENAME in l]
            # Then remove the filtered lines
            lines = [l for l in lines if f'{CONFIG_KEY} = "./{PROMPT_FILENAME}"' not in l.replace('"', "'")]
            write_config(config, lines)
            print(f"  Restored config from backup, removed our {CONFIG_KEY}")

    # Remove prompt file
    if prompt.exists():
        if dry_run:
            print(f"  [dry-run] Would remove: {prompt}")
        else:
            prompt.unlink()
            print(f"  Removed: {prompt}")


def interactive_menu(homes: list[Path]) -> None:
    """Display interactive menu."""
    print("\n" + "=" * 60)
    print("  石井 Jailbreak v4 — Codex Injector")
    print("=" * 60)
    print(f"\nFound {len(homes)} Codex home(s):")
    for h in homes:
        cfg = config_path(h)
        status = "exists" if cfg.exists() else "missing"
        md = prompt_path(h)
        md_status = "active" if md.exists() else "not deployed"
        print(f"  {h}  [config: {status}]  [jailbreak: {md_status}]")
    print()
    print("  [1] Deploy jailbreak")
    print("  [2] Remove jailbreak (restore backup)")
    print("  [3] Dry run (preview changes)")
    print("  [4] Quit")
    print()

    try:
        choice = input("  Choice [1-4]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n")
        return

    if choice == "1":
        for h in homes:
            deploy_prompt(h)
        print("\nDone. Restart Codex for changes to take effect.")
    elif choice == "2":
        for h in homes:
            reset_codex(h)
        print("\nDone. Restart Codex for changes to take effect.")
    elif choice == "3":
        for h in homes:
            deploy_prompt(h, dry_run=True)
    elif choice == "4":
        print("Quit.")
    else:
        print(f"Invalid choice: {choice}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="石井 Jailbreak v4 — Codex model_instructions_file injector"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Deploy jailbreak (non-interactive)")
    group.add_argument("--reset", action="store_true", help="Remove jailbreak and restore backup")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument(
        "--codex-dir",
        type=Path,
        help="Explicit Codex home directory (overrides auto-detection)",
    )

    args = parser.parse_args()

    homes = [args.codex_dir] if args.codex_dir else find_codex_homes()

    if not homes:
        print("Error: No Codex home directory found.")
        print("Set $CODEX_HOME or ensure ~/.codex exists.")
        raise SystemExit(1)

    if args.reset:
        for h in homes:
            reset_codex(h, dry_run=args.dry_run)
        print("\nDone.")
    elif args.apply:
        for h in homes:
            deploy_prompt(h, dry_run=args.dry_run)
        print("\nDone. Restart Codex for changes to take effect.")
    else:
        interactive_menu(homes)


if __name__ == "__main__":
    main()

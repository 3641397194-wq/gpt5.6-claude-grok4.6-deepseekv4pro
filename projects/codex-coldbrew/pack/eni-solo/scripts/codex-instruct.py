#!/usr/bin/env python3
"""Select, deploy, or remove a gpt-5.6-sol Codex instruction file.

The public repository stores each prompt as a ZIP archive. Applying a version
extracts its Markdown file into CODEX_HOME, backs up config.toml, and sets the
top-level `model_instructions_file` entry. The interactive reset action lists
available backups, restores the user-selected file after confirmation, and
removes prompt files managed by this script.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROMPT_VERSIONS = {
    "v5": {
        "md_filename": "gpt-5.6-sol-unrestricted-v5.md",
        "archive": PROJECT_ROOT / "gpt-5.6-sol-unrestricted-v5.zip",
    },
    "v35": {
        "md_filename": "gpt-5.6-sol-unrestricted-v35.md",
        "archive": PROJECT_ROOT / "gpt-5.6-sol-unrestricted-v35.zip",
    },
}
MANAGED_PROMPT_FILENAMES = {
    *(choice["md_filename"] for choice in PROMPT_VERSIONS.values()),
}
BASELINE_BACKUP_SUFFIX = ".gpt56-sol-instruct.bak"

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DARK_GREEN = "\033[38;2;0;100;0m"
ANSI_DARK_ORANGE = "\033[38;2;205;102;0m"
BANNER_WIDTH = 72


def color_enabled() -> bool:
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


def styled(text: str, *codes: str) -> str:
    if not color_enabled():
        return text
    return f"{''.join(codes)}{text}{ANSI_RESET}"


def display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in text)


def section_banner(title: str) -> str:
    label = f" {title} "
    fill_width = max(4, BANNER_WIDTH - display_width(label))
    left = fill_width // 2
    right = fill_width - left
    return styled(f"{'━' * left}{label}{'━' * right}", ANSI_BOLD)


def intro_text() -> str:
    zh_banner = section_banner("中文说明")
    en_banner = section_banner("English Instructions")
    zh_title = styled("gpt-5.6-sol Codex 提示词选择说明：", ANSI_BOLD)
    en_title = styled("gpt-5.6-sol Codex instruction selection instructions:", ANSI_BOLD)
    zh_recommended = styled("推荐", ANSI_BOLD, ANSI_DARK_GREEN)
    en_recommended = styled("recommended", ANSI_BOLD, ANSI_DARK_GREEN)
    zh_v35_notice = styled(
        "建议仅在 v5 无法满足需求时使用",
        ANSI_BOLD,
        ANSI_DARK_ORANGE,
    )
    en_v35_notice = styled(
        "use them only when v5 does not meet your needs",
        ANSI_BOLD,
        ANSI_DARK_ORANGE,
    )
    return f"""\
{zh_banner}
{zh_title}

v5 提示词较为简单，足够应付多数场景（{zh_recommended}）。
v35 提示词加入对特殊任务的优化，但安全性不如 v5（{zh_v35_notice}）。

选择后会将相应提示词.md文件复制到CODEX_HOME中，在config.toml中写入model_instructions_file项，并创建config.toml的备份。若要卸载提示词并恢复原样，请选择“去除提示词恢复备份”项，或手动删除model_instructions_file配置项。

{en_banner}
{en_title}

v5 instructions are simpler and sufficient for most scenarios ({en_recommended}).
v35 instructions add optimizations for specialized tasks, but are less safe than v5 ({en_v35_notice}).

After a version is selected, its prompt .md file is copied to CODEX_HOME, the model_instructions_file entry is written to config.toml, and config.toml is backed up. To uninstall the prompt and restore the previous state, choose “Reset to backup”, or manually remove the model_instructions_file entry.
"""


def menu_text() -> str:
    selection_banner = section_banner("操作选择 / Select an Action")
    recommendation = styled("推荐 / Recommended", ANSI_BOLD, ANSI_DARK_GREEN)
    v35_notice = styled(
        "按说明谨慎使用 / Use with precaution",
        ANSI_BOLD,
        ANSI_DARK_ORANGE,
    )
    return f"""\
{selection_banner}
1. 植入 v5 提示词 / Apply v5 instructions file （{recommendation}）
2. 植入 v35 提示词 / Apply v35 instructions file （{v35_notice}）
3. 去除提示词并恢复备份 / Reset to backup
q. 退出而不执行任何操作 / Quit without modification
"""


def find_codex_dirs() -> list[Path]:
    candidates: set[Path] = set()
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        candidates.add(Path(env_home).expanduser())
    candidates.add(Path.home() / ".codex")
    return sorted(path.resolve() for path in candidates if (path / "config.toml").exists())


def selected_codex_dirs(codex_dir: str | None) -> list[Path]:
    if codex_dir:
        return [Path(codex_dir).expanduser().resolve()]
    return find_codex_dirs()


def backup_file(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = path.with_suffix(path.suffix + f".bak_{timestamp}")
    shutil.copy2(path, backup)
    return backup


def baseline_backup_path(config_path: Path) -> Path:
    return config_path.with_name(config_path.name + BASELINE_BACKUP_SUFFIX)


def available_backups(config_path: Path) -> list[Path]:
    baseline = baseline_backup_path(config_path)
    candidates = {
        path.resolve()
        for path in config_path.parent.glob(config_path.name + "*.bak*")
        if path.is_file()
    }
    ordered: list[Path] = []
    if baseline.is_file():
        ordered.append(baseline.resolve())
        candidates.discard(baseline.resolve())
    ordered.extend(
        sorted(
            candidates,
            key=lambda path: (path.stat().st_mtime_ns, path.name),
            reverse=True,
        )
    )
    return ordered


def config_references_managed_prompt(config_path: Path) -> bool:
    if not config_path.exists():
        return False
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s*model_instructions_file\s*=", line) and any(
            filename in line for filename in MANAGED_PROMPT_FILENAMES
        ):
            return True
    return False


def set_model_instructions(config_path: Path, md_filename: str) -> bool:
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    target = f'model_instructions_file = "./{md_filename}"'
    pattern = re.compile(r"^\s*model_instructions_file\s*=.*$", re.MULTILINE)
    if pattern.search(text):
        new_text = pattern.sub(target, text)
    else:
        lines = text.splitlines()
        insert_at = None
        for index, line in enumerate(lines):
            if line.strip().startswith("model ") and "=" in line:
                insert_at = index + 1
                break
        if insert_at is None:
            insert_at = next(
                (index for index, line in enumerate(lines) if line.lstrip().startswith("[")),
                len(lines),
            )
        lines.insert(insert_at, target)
        new_text = "\n".join(lines) + "\n"
    if new_text != text:
        config_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def remove_managed_model_instructions(config_path: Path) -> bool:
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_text = "".join(
        line
        for line in lines
        if not (
            re.match(r"^\s*model_instructions_file\s*=", line)
            and any(filename in line for filename in MANAGED_PROMPT_FILENAMES)
        )
    )
    if new_text != text:
        config_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def read_prompt(source_path: Path, expected_md_filename: str) -> str:
    """Read a Markdown prompt directly or extract it from a ZIP archive."""
    if source_path.suffix.lower() != ".zip":
        return source_path.read_text(encoding="utf-8")

    with zipfile.ZipFile(source_path) as archive:
        files = [name for name in archive.namelist() if not name.endswith("/")]
        preferred = [name for name in files if Path(name).name == expected_md_filename]
        markdown_files = [name for name in files if Path(name).suffix.lower() == ".md"]
        candidates = preferred or markdown_files
        if len(candidates) != 1:
            raise ValueError(
                f"压缩包应包含唯一的 {expected_md_filename}（或唯一 Markdown 文件），"
                f"实际候选: {candidates}"
            )
        member = candidates[0]
        with tempfile.TemporaryDirectory(prefix="gpt56-sol-prompt-") as temp_dir:
            extracted_path = Path(archive.extract(member, path=temp_dir))
            return extracted_path.read_text(encoding="utf-8")


def deploy_prompt(
    args: argparse.Namespace,
    prompt_path: Path,
    md_filename: str,
) -> int:
    if not prompt_path.exists():
        print(f"[错误] 提示词文件不存在: {prompt_path}", file=sys.stderr)
        return 2

    codex_dirs = selected_codex_dirs(args.codex_dir)
    if not codex_dirs:
        print("[错误] 未找到 .codex/config.toml；请使用 --codex-dir 指定。", file=sys.stderr)
        return 2

    try:
        prompt_text = read_prompt(prompt_path, md_filename)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        print(f"[错误] 读取或解压提示词失败: {exc}", file=sys.stderr)
        return 2

    source_kind = "ZIP（已解压校验）" if prompt_path.suffix.lower() == ".zip" else "Markdown"
    print(f"[+] Prompt: {prompt_path} [{source_kind}]")
    for codex_dir in codex_dirs:
        config_path = codex_dir / "config.toml"
        baseline = baseline_backup_path(config_path)
        destination = codex_dir / md_filename
        print(f"\n── 目标 / Target: {codex_dir} ──")
        print(f"  写入 / Write: {destination}")
        print(f'  配置 / Config: model_instructions_file = "./{md_filename}"')
        print(f"  基线备份 / Baseline backup: {baseline.name}")
        if args.dry_run:
            continue

        codex_dir.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text("", encoding="utf-8")
            print("  创建 / Created: config.toml")
        if not baseline.exists():
            shutil.copy2(config_path, baseline)
            print(f"  已创建基线备份 / Baseline saved: {baseline.name}")
        elif not config_references_managed_prompt(config_path):
            shutil.copy2(config_path, baseline)
            print(f"  已刷新基线备份 / Baseline refreshed: {baseline.name}")
        else:
            print(f"  保留现有基线备份 / Baseline retained: {baseline.name}")
        snapshot = backup_file(config_path)
        print(f"  已创建操作前备份 / Snapshot saved: {snapshot.name}")

        destination.write_text(prompt_text, encoding="utf-8")
        changed = set_model_instructions(config_path, md_filename)
        print("  状态 / Status:", "已更新 / Updated" if changed else "已是最新 / Already current")
    return 0


def choose_backup(config_path: Path) -> tuple[Path | None, bool]:
    backups = available_backups(config_path)
    if not backups:
        print("  未找到可恢复的 config.toml 备份。")
        print("  No restorable config.toml backup was found.")
        return None, True

    print("  可用备份 / Available backups:")
    baseline = baseline_backup_path(config_path).resolve()
    for index, backup in enumerate(backups, start=1):
        stat = backup.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        label = (
            "部署前基线 / Pre-deployment baseline"
            if backup == baseline
            else "操作快照 / Operation snapshot"
        )
        print(f"    {index}. {backup.name} [{label}; {modified}; {stat.st_size} bytes]")
    print("    q. 取消恢复 / Cancel reset")

    while True:
        try:
            choice = input(
                f"请选择要恢复的文件 / Select a backup to restore [1-{len(backups)}/q]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None, False
        if choice == "q":
            return None, False
        if choice.isdigit() and 1 <= int(choice) <= len(backups):
            return backups[int(choice) - 1], True
        print(
            f"[错误] 请输入 1-{len(backups)} 或 q / "
            f"Enter a number from 1 to {len(backups)}, or q."
        )


def confirm_reset(restore_source: Path | None) -> bool:
    if restore_source:
        print(f"  将恢复 / Selected backup: {restore_source}")
        print("  该文件将覆盖 config.toml，并移除脚本管理的提示词文件。")
        print("  This file will replace config.toml, and managed prompt files will be removed.")
    else:
        print("  没有可用备份；将仅移除脚本管理的 model_instructions_file 配置和提示词文件。")
        print(
            "  No backup is available; only the managed model_instructions_file entry "
            "and prompt files will be removed."
        )
    try:
        answer = input("确认继续？/ Confirm reset? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in {"y", "yes", "是"}


def reset_to_backup(args: argparse.Namespace) -> int:
    codex_dirs = selected_codex_dirs(args.codex_dir)
    if not codex_dirs:
        print("[错误] 未找到 .codex/config.toml；请使用 --codex-dir 指定。", file=sys.stderr)
        return 2

    for codex_dir in codex_dirs:
        config_path = codex_dir / "config.toml"
        print(f"\n── 目标 / Target: {codex_dir} ──")
        restore_source, should_continue = choose_backup(config_path)
        if not should_continue:
            print("  已取消 / Reset cancelled.")
            continue
        if not confirm_reset(restore_source):
            print("  未确认，已取消 / Confirmation not received; reset cancelled.")
            continue

        if restore_source:
            print(f"  恢复 / Restore: {restore_source.name} -> config.toml")
        else:
            print("  恢复 / Restore: 无备份，将移除脚本管理的配置项")
        for filename in sorted(MANAGED_PROMPT_FILENAMES):
            print(f"  移除 / Remove: {filename}")
        if args.dry_run:
            print("  预览完成，未修改文件 / Dry run complete; no files changed.")
            continue

        codex_dir.mkdir(parents=True, exist_ok=True)
        if config_path.exists():
            snapshot = backup_file(config_path)
            print(f"  已创建恢复前备份 / Pre-reset snapshot: {snapshot.name}")

        if restore_source:
            shutil.copy2(restore_source, config_path)
            removed_entry = remove_managed_model_instructions(config_path)
            print(
                "  配置状态 / Config status:",
                "已恢复备份并移除脚本配置 / Backup restored; managed entry removed"
                if removed_entry
                else "已恢复备份 / Backup restored",
            )
        elif config_path.exists():
            changed = remove_managed_model_instructions(config_path)
            print(
                "  配置状态 / Config status:",
                "已移除脚本配置项 / Managed entry removed"
                if changed
                else "未发现脚本配置项 / Managed entry not found",
            )
        else:
            print("  配置状态 / Config status: config.toml 不存在 / Not found")

        removed = 0
        for filename in MANAGED_PROMPT_FILENAMES:
            prompt_path = codex_dir / filename
            if prompt_path.exists():
                prompt_path.unlink()
                removed += 1
        print(f"  提示词状态 / Prompt status: 已移除 {removed} 个文件 / Removed {removed} file(s)")
    return 0


def interactive_action() -> str:
    print(intro_text())
    print(menu_text())
    while True:
        try:
            choice = input("请选择 / Select [1/2/3/q]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        actions = {"1": "v5", "2": "v35", "3": "reset", "q": "quit"}
        if choice in actions:
            return actions[choice]
        print("[错误] 请输入 1、2、3 或 q / Enter 1, 2, 3, or q.")


def inferred_md_filename(source: Path, requested_name: str | None) -> str:
    if requested_name:
        return requested_name if requested_name.endswith(".md") else f"{requested_name}.md"
    return f"{source.stem}.md"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select, extract, deploy, or reset a gpt-5.6-sol Codex instruction file."
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--version", choices=("v5", "v35"), help="Apply v5 or v35")
    action_group.add_argument("--reset", action="store_true", help="Restore the backup and remove prompts")
    action_group.add_argument("--file", "-f", help="Apply a custom instruction ZIP or Markdown file")
    parser.add_argument("--name", "-n", help="Destination filename for --file, with or without .md")
    parser.add_argument("--codex-dir", help="Explicit Codex home directory, e.g. ~/.codex")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    if args.name and not args.file:
        parser.error("--name 仅能与 --file 一起使用 / --name requires --file")

    if args.version:
        action = args.version
    elif args.reset:
        action = "reset"
    elif args.file:
        source = Path(args.file).expanduser().resolve()
        return deploy_prompt(args, source, inferred_md_filename(source, args.name))
    else:
        action = interactive_action()

    if action == "quit":
        print("未执行修改 / No modification made.")
        return 0
    if action == "reset":
        return reset_to_backup(args)

    selected = PROMPT_VERSIONS[action]
    return deploy_prompt(args, selected["archive"], selected["md_filename"])


if __name__ == "__main__":
    raise SystemExit(main())

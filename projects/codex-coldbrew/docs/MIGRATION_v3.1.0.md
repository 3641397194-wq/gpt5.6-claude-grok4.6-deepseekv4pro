# Migrating from v3.0.1 to v3.1.0

## Upgrade

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ReplaceExisting
```

macOS/Linux:

```bash
sh ./install.sh "$HOME/.codex/skills" --replace
```

The installer stores the complete v3.0.1 Skill and its receipt before installing v3.1.0.

## What stays compatible

- installed name and directory: `eni-coldbrew`;
- historical v3 activation behavior: `冷咖啡` and `cold coffee`; `cold coffee` was removed in v6 and the current trigger is only an exact whole input of `冷咖啡`;
- activation banner;
- seven route identifiers and ordering;
- receipt schema `3` and schema `2` uninstall compatibility;
- `-ReplaceExisting`, `--replace`, and existing uninstall commands.

## What is added

- Armor Break MAX profile;
- Mature M5 profile and adult-product engineering contract;
- versioned JSON profile contract;
- deterministic profile simulator;
- originality metrics;
- fifteen-layer POSIX rollback regression;
- expanded Pages, README, and release documentation.

## Rollback

Run the normal uninstaller once to restore the immediately previous Skill and receipt. Repeating the command walks backward through additional receipt layers.

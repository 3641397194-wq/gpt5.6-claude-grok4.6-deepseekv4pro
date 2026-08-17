# Architecture

```text
CLI / Tk Studio
      |
      v
Target resolver  --->  user ~/.claude or project ./.claude
      |
      +--> CLAUDE.md marker block
      +--> rules/claude-pojia/*.md
      +--> .claude-pojia/state.json + snapshots/
```

## Deployment stages

1. **Plan** reads the selected scope, profile, marker and rules manifest without writing.
2. **Snapshot** records the first baseline and the current transaction state.
3. **Compose** renders one bootstrap block and five profile rule files.
4. **Commit** swaps the rule directory and writes `CLAUDE.md` atomically.
5. **Verify** compares the block hash and every managed file against state.
6. **Restore** removes only the managed block, keeps outside edits, preserves edited rules in a snapshot and restores a pre-install rules tree when one existed.

The core has no network dependency. Claude Code discovery is diagnostic only;
the app can prepare files in a disposable directory for tests.

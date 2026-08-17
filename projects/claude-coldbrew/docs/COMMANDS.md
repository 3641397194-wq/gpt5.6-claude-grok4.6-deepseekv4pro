# Commands

All commands use the standard-library Python app:

```text
python app/claude_pojia.py doctor [--scope user|project]
python app/claude_pojia.py status [--json]
python app/claude_pojia.py plan --profile max-breaker [--json]
python app/claude_pojia.py install --profile max-breaker --yes [--force]
python app/claude_pojia.py verify [--json]
python app/claude_pojia.py restore [--json]
python app/claude_pojia.py launch --yes [--bypass-permissions] [--claude-arg ARG]
```

`--scope user` uses `~/.claude`. `--scope project --project PATH` uses
`PATH/.claude`. `CLAUDE_POJIA_HOME` and `CLAUDE_CONFIG_DIR` can override the
user directory for a disposable test. `CLAUDE_POJIA_CLAUDE_BIN` selects a
specific local Claude Code executable for the MAX launch path.

`plan` is read-only. `install` requires `--yes`; `--force` is reserved for a
reviewed ownership conflict. `restore` keeps the current text outside the
managed marker and records changed managed rules before removing them.

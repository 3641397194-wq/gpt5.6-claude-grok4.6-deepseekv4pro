# Security and Privacy

This project uses CBCL-1.0, a custom source-available license that is not an OSI-approved open source license. Complete corresponding source and build
materials remain public; this security policy does not change that boundary.

Claude 破甲 writes only the selected `CLAUDE.md`, the namespaced
`.claude/rules/claude-pojia/` directory and its own `.claude-pojia/` state
directory. It does not read or upload tokens, cookies, API keys or prompts
from a running session.

Before changing a target, the installer creates a timestamped local snapshot.
Run `plan` first, use `--force` only after reviewing a conflict, and run
`verify` after installation. Restore keeps unrelated text and saves edited
managed rules into a snapshot before removal.

Do not publish credentials, private transcripts or real secrets in issues,
tests, screenshots or pull requests. Use `TARGET`, `HOST`, `TOKEN` and other
synthetic placeholders in examples.

Report a repository security problem privately to the maintainer before public
disclosure. The project is an independent community tool and is not an
Anthropic product.

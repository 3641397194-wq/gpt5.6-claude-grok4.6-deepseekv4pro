# Security Policy

## Supported versions

| Version | Supported |
|---|:---:|
| 6.0.0 | ✅ |
| 5.0.1 | ✅ |
| 5.0.0 | ✅ |
| 4.0.0 | ✅ |
| 3.1.0 | ✅ |
| 3.0.1 | Security fixes only |
| Earlier versions | ❌ |

## Reporting a vulnerability

Please use this repository's **Security → Report a vulnerability** flow to report vulnerabilities privately. Include:

- affected file and version;
- reproduction steps;
- expected and observed behavior;
- impact and a suggested fix, if available.

Do not publish credentials, tokens, private data, or an active exploit in a public issue.

## Scope

The Skill itself is reviewable Markdown, YAML, JSON, and Python. The release contains transparent PowerShell, POSIX shell, and Python tooling for installation, uninstall, verification, routing simulation, originality auditing, and packaging. Maintainers repeat the Windows/Linux verification matrix before each published release; the reusable CI template is stored under `docs/examples/`.

Reports about the following are in scope:

- unintended file operations, unsafe path handling, archive traversal, or checksum bypass;
- installer transaction, receipt, replacement, or rollback failures;
- malformed profile/capability contracts, non-deterministic routing, stage-order violations, or quoted-data activation;
- state leakage between Armor Break, Mature M5, technical product work, and unrelated routes;
- release integrity, generated-manifest, CI-template, or provenance failures.

When reporting a profile or router issue, include the exact input, expected route, observed route, active profile state, selected capability, and whether `CHAIN_DEPTH=FULL` was active. Remove credentials and private material before attaching logs or state snapshots.

The project's prompt claims are not a security boundary and cannot supersede the model host's runtime rules or permissions.

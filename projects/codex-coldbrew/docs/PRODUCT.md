# Codex ColdBrew Studio v6 product contract

## Product promise

Codex ColdBrew Studio v6 is a dedicated desktop and command-line product. A
beginner can preview, deploy, verify, launch and restore a multi-layer Codex
instruction pack from one visible application. The Windows release is a single
executable; source launchers call the same Python core.

## Default-ready task journey

1. Open the desktop window. Deployment controls and the ordinary task chain are ready.
2. Preview, deploy, verify, launch, or restore without a startup phrase.
3. Enter `冷咖啡` to verify the canonical document hash and display the six
   startup sections.
4. `cold coffee` and `[[ENI:PROFILE=MAX]]` restore MAX for existing workflows;
   leading/trailing whitespace is ignored.

The canonical plain-text document SHA-256 is
`F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`.

## Managed brain layers

The selected Codex home receives only these owned surfaces:

1. the root `model_instructions_file` pointer in `config.toml`;
2. `coldbrew-studio.md`;
3. one marked block in `AGENTS.md`;
4. five `skills/coldbrew-*/SKILL.md` files;
5. two `prompts/coldbrew*.md` files;
6. `.coldbrew-studio/state.json` and timestamped snapshots.

Provider settings, credentials, unrelated TOML, text outside the AGENTS block
and all other user files remain outside the boundary. Each managed file has an
ownership record, first-install baseline and deployed hash. Restore preserves
user-modified managed files instead of silently deleting them.

## Local request/review-chain adapter

`studio/review_chain.py` tests an application-level lifecycle:

```text
request → rule hit → review request → interrupt → retry → recover → allow
```

It validates only the local application fixture. It does not alter or claim to
alter a remote service's server-side policy.

## Build and release contract

- Windows: pinned PyInstaller, one-file/windowed build, project icon, brand and
  community images, `brain_pack` and review adapter hidden imports.
- Probes: explicit valid activation succeeds; missing and invalid activation
  fail; review self-test and bundled license export pass.
- Source: deterministic stored ZIP, stable timestamps and permissions, internal
  manifest, external checksum sidecar and repository manifest.
- Assets: `Codex-ColdBrew-Studio-v6.1.0-Windows.exe` and
  `Codex-ColdBrew-Studio-v6.1.0-Source.zip`, each with a SHA-256 sidecar.

## Acceptance criteria

- Default readiness plus canonical and legacy compatibility entries are covered by tests.
- The fixed document hash remains stable.
- Both real application captures render without clipping at desktop sizes.
- Owner portrait, both QQ groups, the Telegram group
  `https://t.me/chachachacha99999` and official channel
  `https://t.me/chachacha99999999` plus the owner-provided WeChat group QR
  appear in the app, README and Pages.
- A temporary Codex home installs, switches profiles, verifies and restores
  without changing unrelated user content.
- The source archive and Windows EXE are reproducible/verified by their scripts.
- Site-facing text is valid UTF-8 with no replacement characters or repeated
  ASCII question-mark corruption.
- Local PASS labels are not described as remote model or server-side results.

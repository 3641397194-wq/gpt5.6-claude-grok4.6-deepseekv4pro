# Claude ColdBrew v3 Source Map

This map records what was observed and what was authored. It is a provenance
record, not a copy list.

| Source | Observation | ColdBrew implementation |
| --- | --- | --- |
| Claude Code memory docs | `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `.claude/rules/`, user rules | user/project `TargetLayout`, namespaced rules and preview plan |
| Claude Code settings docs | settings are hierarchical and separate from memory | installer leaves settings and credentials untouched |
| Owner Codex ColdBrew v4 | preview, atomic write, profile, verify, restore, release evidence | redesigned into Claude-specific marker and state contracts |
| Owner community cards, commit `65873ba3a5c0bd02fe6dab01dc56d8ae4921cc4d` | two owner-controlled QQ community cards | intentional byte-for-byte carry-over with fixed hashes recorded in `PROVENANCE.md` |
| `claude-keysmith` | recognizable import block, explicit scope, rollback | new `CLAUDE-POJIA` markers, separate transaction directory and hashes |
| `claude-fable-5-opus-5-jailbreaks` | synthetic cases and deterministic profile manager | local unit tests and profile contracts without provider API calls |
| `Spiritual-Spell-Red-Teaming` | route and red-team taxonomy | seven route labels, no copied prompt text |
| `claude-code-jailbreak` | one-click launcher and local integration | explicit MAX launcher plus reversible prompt deployment |
| `MDX-Tom/gpt-5.6-instruct`, `77e7a649903f9556f2d7bfa0223fa99e123aad52` (MIT) | preview, ownership, rollback, archive, regression and release organization concepts | independent Claude transaction tests, multi-layer inventory and new ColdBrew visual system |
| `zxr-roro/GPT5.6-5.5-`, `b18ceb0322d86480df049147e451cfbea5070e20` | versioned instruction-pack organization | independently authored Claude profile contract and release inventory |
| `FuDie0915/Super-Instruct-Codex-5.6`, `dbfaa8e5137f8584582bd4e48e5aae9ce9c3d91b` | capability grouping and one-entry presentation | independently authored four-profile selector and one-file app entry |
| `lingbol088-spec/5.6-JAILBREAK-NERV-codex-instruct-5.6`, `4fac65fa452d96c98d96e2d9759f31cd1683441d` | activation vocabulary and route visibility | canonical ColdBrew trigger module and local route/status display |
| `winfunc/opcode`, `70c16d8a4910db48cd9684aeacdd431caefd7d71` (AGPL-3.0) | desktop session-management concepts | original Tkinter workspace, local status ledger and background client launch |
| `farion1231/cc-switch`, `413c09e0790c304506888ae24b9be72820aca126` (MIT) | client discovery and switcher ergonomics | independent Claude executable detection and profile selector |
| `siteboon/claudecodeui`, `f0dca2d5e79c225f599e697bf9b55e839b152b78` (AGPL-3.0) | project/session workspace concepts | independent scope, project chooser and task intake surface |
| `affaan-m/ECC`, `59a99d669f5466d99d5be8b6fce8c5f2677766d0` (MIT) | instruction-contract and workflow concepts | ColdBrew-owned activation module plus six generated rule files |
| `Calrton/jailbreak-prompts`, `dc6b2f0bba699a2afdf36f597cf3c98e77f820aa` (MIT) | capability-taxonomy observations | owner-supplied six-section activation copy with fixed hash and snapshot tests |
| `iOfficeAI/AionUi`, `31ec26a902edf7bdda90026b1f9d6f4d0507b706` (Apache-2.0) | installed-agent discovery and desktop workspace concepts | original client status, workspace selector and permission-state presentation |
| `smtg-ai/claude-squad`, `2dd388e9857233e07712c8c5b3e2bf3b471b39fa` (AGPL-3.0) | isolated task/session lifecycle concepts | independent scope isolation and local activity ledger; no upstream TUI or orchestration code |
| `zed-industries/claude-code-acp`, `6b405138fc82be947964612fac04e56654827b66` (Apache-2.0) | capability negotiation and permission-event concepts | independent client detection, optional launch controls and explicit state labels |
| `musistudio/claude-code-router`, `47f36494317a5d023afa29c46a71d6622e138691` (MIT) | profile selection, retry and route diagnostics concepts | original profile contract and route receipt; no provider presets or protocol adapter |
| `cline/cline`, `d011d049a13a04a58fb04d72666c35da6b4f1853` (Apache-2.0) | plan/act separation, checkpoints and restore concepts | independent preview/install/verify/restore transaction and snapshot ownership |
| `anomalyco/opencode`, `fe82a1b6ca4f535beb973b0867017e3f639f85ed` (MIT) | shared desktop/CLI core and event timeline concepts | one Python core used by GUI and CLI plus a locally authored activity log |
| `twpayne/chezmoi`, `f81cb321789aa3df62871248f5e4d361a59e7cc1` (MIT) | desired/actual state and dry-run/apply/verify concepts | independent deployment plan, ownership checks, atomic writes and verification |
| Owner portrait, `assets/ishii-brand-source.jpg`, SHA-256 `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246` | owner-selected ColdBrew brand image | project generator creates the Claude ICO, avatar and full-bleed Hero |

## Independent decisions

- The ownership boundary is a marked block plus `rules/claude-pojia`; unrelated
  user text and unmanaged rules are preserved or snapshotted.
- The app does not edit Claude Code binaries, credentials, MCP configuration or
  network settings.
- A high-permission launch is opt-in through an explicit `--yes --bypass-permissions`
  path; the base install remains a local instruction enhancement.
- Release archives are deterministic and have an internal SHA-256 manifest.
- The Windows app is built from the public entry point with a pinned PyInstaller
  version; the executable and source ZIP are published as separate assets.
- Real software screenshots are captured from this repository's running app and
  fixed by dimensions and SHA-256 in `scripts/site_audit.py`.
- Exact activation uses whole-string equality across GUI, CLI and generated
  instructions; whitespace, English, synonyms and surrounding text are negative tests.
- The v3 brain layer adds seven Rules, five Skills, one Agent and two Commands,
  each with project-authored names, wording, ownership state and restore behavior.

## Explicit non-copy boundary

No upstream source, prompt, rule, agent definition, configuration preset,
schema, test fixture, transcript, icon, screenshot, page layout, documentation
prose or release artifact was imported. The reference rows describe observed
behaviors only. ColdBrew independently defines the state keys, marker protocol,
file ownership, transaction order, restore policy, CLI/GUI implementation and
visual composition shipped in this repository.

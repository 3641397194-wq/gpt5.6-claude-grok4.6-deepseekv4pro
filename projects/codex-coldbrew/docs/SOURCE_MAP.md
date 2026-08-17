# ColdBrew Studio v6 source-to-feature map

This ledger records fixed research snapshots used while independently designing
Codex ColdBrew Studio v6. A row means public metadata, README-level behavior,
packaging, interaction patterns or license text was reviewed. It does not mean
that an upstream source file, prompt, rule, schema, test fixture, screenshot,
icon, page structure, copywriting or release artifact entered this repository.

## Owner and requested references

| Source snapshot | License at snapshot | Abstract inventory | Independent ColdBrew destination |
|---|---|---|---|
| [`茶/codex5.6-coldbrew@d628641`](https://github.com/茶/codex5.6-coldbrew/commit/d628641c9d401e8f8e7ebaf362faa0891afd9362) | ColdBrew project license | seven routes, MAX overlays, 17-domain/181-node catalog, install and rollback contracts | retained project-owned `skills/eni-coldbrew/` baseline, migrated to v5 contracts |
| [`MDX-Tom/gpt-5.6-instruct@77e7a64`](https://github.com/MDX-Tom/gpt-5.6-instruct/commit/77e7a649903f9556f2d7bfa0223fa99e123aad52) | MIT | preview/deploy/reset flow, backup ownership, atomic replacement, archive verification | independent transaction functions, tests and deterministic source release |
| [`zxr-roro/GPT5.6-5.5-@b18ceb0`](https://github.com/zxr-roro/GPT5.6-5.5-/commit/b18ceb0322d86480df049147e451cfbea5070e20) | no license file observed | cross-platform bootstrap, broad capability taxonomy, skill indexing concepts | project-authored launchers, capability contracts and route catalog; no upstream content reuse |
| [`FuDie0915/Super-Instruct-Codex-5.6@dbfaa8e`](https://github.com/FuDie0915/Super-Instruct-Codex-5.6/commit/dbfaa8e5137f8584582bd4e48e5aae9ce9c3d91b) | MIT | desktop shell, profile selection, packaging and operation status surface | original Tk desktop composition, profile selector, operation log and build scripts |
| [`lingbol088-spec/5.6-JAILBREAK-NERV-codex-instruct-5.6@4fac65f`](https://github.com/lingbol088-spec/5.6-JAILBREAK-NERV-codex-instruct-5.6/commit/4fac65fa452d96c98d96e2d9759f31cd1683441d) | no license file observed | setup/deploy/verify separation, layered state diagrams, catalog presentation | independent `plan/install/verify/restore` API and architecture documentation; no upstream content reuse |
| [`yynxxxxx/Codex-5.5-codex-instruct-5.5@ed0b6dc`](https://github.com/yynxxxxx/Codex-5.5-codex-instruct-5.5/commit/ed0b6dc37d1994e93788d92f7af63f58bf0b9e2d) | MIT | compact deployment helper, Codex-home discovery and compatibility flags | independent home discovery, CLI options and environment doctor |
| Owner baseline `~/.codex/eni-jailbreak-v4.md` | owner-supplied, SHA-256 `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246` | route-first output, language preservation, placeholder continuation, direct delivery | independently worded `MAX Shield` directives in `studio/presets.json` |

Repositories without a license file were treated as observation-only inputs.
No text or implementation from those repositories is distributed here.

## Additional fixed public references

| Source snapshot | License | Abstract observation retained | Explicit exclusion |
|---|---|---|---|
| [`winfunc/opcode@70c16d8`](https://github.com/winfunc/opcode/commit/70c16d8a4910db48cd9684aeacdd431caefd7d71) | AGPL-3.0 | workspace-first desktop shell, agent/session discovery, background task status | observation-only: source, prompt library, agent definitions, UI, schema and assets excluded |
| [`iOfficeAI/AionUi@31ec26a`](https://github.com/iOfficeAI/AionUi/commit/31ec26a902edf7bdda90026b1f9d6f4d0507b706) | Apache-2.0 | capability discovery, workspace/session separation, permission-state visibility | implementation, assistant definitions, team orchestration, UI and branding excluded |
| [`smtg-ai/claude-squad@2dd388e`](https://github.com/smtg-ai/claude-squad/commit/2dd388e9857233e07712c8c5b3e2bf3b471b39fa) | AGPL-3.0 | session lifecycle, isolated workspaces, pause/resume and diff preview | observation-only: Go/TUI implementation, shortcuts, config schema and scripts excluded |
| [`zed-industries/claude-code-acp@6b40513`](https://github.com/zed-industries/claude-code-acp/commit/6b405138fc82be947964612fac04e56654827b66) | Apache-2.0 | capability negotiation, structured permission events, optional feature fallback | TypeScript adapter, private fields, protocol extensions and fixtures excluded |
| [`musistudio/claude-code-router@47f3649`](https://github.com/musistudio/claude-code-router/commit/47f36494317a5d023afa29c46a71d6622e138691) | MIT | profile selection, route receipts, retry/fallback and content-free observability | source, provider presets, transformers, credential handling, dashboard and schema excluded |
| [`cline/cline@d011d04`](https://github.com/cline/cline/commit/d011d049a13a04a58fb04d72666c35da6b4f1853) | Apache-2.0 | plan/apply separation, file context entry, checkpoints and operation feedback | extension source, prompts, provider code, interface layout and assets excluded |
| [`sst/opencode@fe82a1b`](https://github.com/sst/opencode/commit/fe82a1b6ca4f535beb973b0867017e3f639f85ed) | MIT | provider-neutral CLI surface, session events and structured command results | Go/TypeScript source, TUI, protocol, provider configuration and branding excluded |
| [`twpayne/chezmoi@f81cb32`](https://github.com/twpayne/chezmoi/commit/f81cb321789aa3df62871248f5e4d361a59e7cc1) | MIT | read-only diff, explicit apply, atomic file replacement and state verification | Go source, command syntax, templates, state format and documentation prose excluded |
| [`farion1231/cc-switch@413c09e`](https://github.com/farion1231/cc-switch/commit/413c09e0790c304506888ae24b9be72820aca126) | MIT | client discovery, configuration preview, backup/restore and status cards | Rust/frontend source, provider presets, credential import, UI and brand assets excluded |
| [`siteboon/claudecodeui@f0dca2d`](https://github.com/siteboon/claudecodeui/commit/f0dca2d5e79c225f599e697bf9b55e839b152b78) | AGPL-3.0-or-later with additional terms | local/remote workspace selection, history restore and configuration synchronization | observation-only: all source, APIs, terminal UI, plugins, marks and promotional material excluded |
| [`affaan-m/everything-claude-code@59a99d6`](https://github.com/affaan-m/everything-claude-code/commit/59a99d669f5466d99d5be8b6fce8c5f2677766d0) | MIT | layered skill/rule/command organization and discoverable capability documentation | every prompt, agent, hook, command, rule, skill, MCP configuration and wording excluded |
| [`Calrton/jailbreak-prompts@dc6b2f0`](https://github.com/Calrton/jailbreak-prompts/commit/dc6b2f0bba699a2afdf36f597cf3c98e77f820aa) | MIT | public trigger vocabulary and model-category taxonomy used as a coverage checklist | all prompt bodies, personas, rules, templates, examples, page copy and branding excluded |
| [`EasyJailbreak/EasyJailbreak@d5477e7`](https://github.com/EasyJailbreak/EasyJailbreak/commit/d5477e712e43b7a1a2110974b814ce578d609f5f) | GPL-3.0 | modular model, dataset, selector, mutation and evaluator boundaries as a test-coverage taxonomy | observation-only: framework source, recipes, datasets, seeds, prompts, examples, tests, documentation and assets excluded |
| [`JailbreakBench/jailbreakbench@23dbdf6`](https://github.com/JailbreakBench/jailbreakbench/commit/23dbdf6b19650521604456229bc1d9c4156c85c1) | MIT | reproducible benchmark stages, explicit attack/defense result separation and judge disagreement tracking | package source, behavior datasets, submitted artifacts, judges, templates, examples, leaderboard data and wording excluded |
| [`CryptoAILab/JailbreakEval@c141972`](https://github.com/CryptoAILab/JailbreakEval/commit/c1419728c039adc8c75e85b72a15a845b0999bf7) | MIT | evaluator plurality, coverage/cost/result reporting and machine-readable local diagnostics | evaluator implementations, presets, datasets, configuration schema, examples, model integrations, metrics tables and assets excluded |
| [`xsser/codex-jailbreak-guide@16e4fac`](https://github.com/xsser/codex-jailbreak-guide/commit/16e4faccb5cf59042aaff3c5e9dfd755a4b2dd12) | no license file observed | Codex-home compatibility checks and root configuration-pointer discovery as observation-only test cases | every prompt, guide step, analysis claim, probe, fuzzer, command, configuration value and prose excluded |
| [`cyberlieflife/CodexJailbreak@6e64b0a`](https://github.com/cyberlieflife/CodexJailbreak/commit/6e64b0a090e1bb6a67f41d0d924ff37afa6bb5c1) | MIT | idempotent managed state, structured configuration updates, atomic readback and one-click uninstall status | Rust/Tauri/React source, managed markers, bundle layout, IPC names, skill/MCP assets, interface structure and wording excluded |

AGPL projects remain strictly at the product-observation boundary. Nothing from
them is vendored, translated, adapted or linked into ColdBrew runtime code.

## Capability-to-implementation cross-check

| Capability family | Independent implementation and evidence |
|---|---|
| Exact owner activation | `studio/coldbrew_activation.py`; fixed SHA-256 `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246` |
| Exact activation gate | strict equality in GUI, CLI, profile engine and toolchain orchestrator; whitespace, aliases and surrounding text are negative tests |
| Multi-layer Codex brain | `studio/brain_pack.py`; marked AGENTS block, five original Skills and two Prompts with per-file ownership and baselines |
| Desktop product surface | `studio/coldbrew_studio.py`; owner-generated standby and active screenshots |
| Task, file and directory entry | dedicated Studio fields that form the local Codex launch request |
| Codex discovery and launch | project-authored executable discovery, home selection and CLI subprocess boundary |
| Preview before writing | `plan` command and desktop preview control |
| Managed prompt ownership | independent state schema, conflict checks and prompt SHA-256 |
| Configuration transaction | snapshot, atomic replacement, verify and guarded restore |
| Local review-chain diagnostics | `studio/review_chain.py`; hit, interrupt, retry, recovery and redacted persistence tests |
| Profile and route visibility | four Studio profiles, seven public routes and deterministic JSON contracts |
| Windows distribution | original icon, pinned PyInstaller build, PE/CLI probe and checksum sidecar |
| Public-source distribution | deterministic full-source ZIP, internal manifest, repository manifest and sidecar |
| Product presentation | original page composition, actual application images, keyboard screenshot tabs and two owner-provided QQ cards |
| Brand presentation | owner-supplied portrait copied to `assets/ishii-brand-source.jpg`; project script generates the ICO, avatar and full-bleed Hero |

The review-chain component is an application-level local adapter and diagnostic
fixture. It reports and tests requests handled by this application boundary; it
does not represent a change to a remote service's server-side execution policy.

## Originality boundary

1. External repositories remain fixed research inputs and are never vendored.
2. ColdBrew owns its state schema, file names, activation module, review-event
   model, configuration transaction, desktop composition and release process.
3. Common interface words, product names and the exact owner-supplied activation
   contract are treated as compatibility requirements, not borrowed authorship.
4. Source code, prompts, rules, schema, test fixtures, page structures, images,
   icons, screenshots, copywriting and release archives from references are excluded.
5. Every distributable artifact includes this ledger, the originality report,
   third-party notices, complete build scripts and the project license.

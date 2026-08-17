# Changelog

All notable changes to this project are documented here.

## 7.0.0 - 2026-08-18

- Codex slot upgraded to GPT-5.6: bundled the full eni-solo v4.0.0 package
  (pack/eni-solo, 89 skills, deterministic router, persona manifest) into
  the repository.
- Added studio/eni_solo_deploy.py, a reversible deployment bridge with
  deploy / restore / status / verify / doctor commands: backup -> remove
  obsolete -> install skills -> manifest -> prompt -> hook -> inject ->
  activate -> verify -> receipt, with full rollback on failure.
- Fixed the bundled global/AGENTS.md route contract so the verification
  gate (one_solo_block, isible_route_contract) passes.
- Restore now also undoes the injector footprint (eni-jailbreak-v4.md and
  config backup sidecars).
- Switched repository/author references to 茶
  placeholders for the open-source release migration.
## 6.1.0 - 2026-08-17

- Unified four-product matrix and community promotion.
- Replaced WeChat group QR and refreshed release visuals.

## [6.1.0] - 2026-08-12

### Added

- Added the owner-provided `微信群：codex 破甲` QR card to both README editions,
  GitHub Pages and deterministic source releases.
- Added a responsive Pages layout and fixed asset hash/dimension audit for the
  new group-chat promotion image.

## [6.0.3] - 2026-08-12

### Fixed

- Restored the Telegram group entry at `@chachachacha99999` and kept the
  official channel at `@chachacha99999999` as separate community destinations.
- Added independent group/channel buttons, links, metadata and audit coverage
  so the two Telegram destinations cannot be conflated again.

## [6.0.2] - 2026-08-11

### Changed

- Promoted the official Telegram channel, `@chachacha99999999`, across the
  desktop app, GitHub Pages, bilingual READMEs, repository metadata and
  release-source documentation.
- Added a direct official-channel call to action in the Pages hero and made
  the community card and footer labels explicit.

### Verified

- Rebuilt the deterministic source archive and refreshed the repository
  checksum manifest for the channel update.

## [6.0.1] - 2026-08-11

### Fixed

- Restored default-ready task routing. Ordinary tasks no longer require a separate
  startup phrase before entering the full execution chain.
- Restored `cold coffee` and `[[ENI:PROFILE=MAX]]` as compatibility entries.
- Kept `冷咖啡` as the full startup-document trigger instead of using it as a
  global task gate.

### Added

- Added regression coverage for default task readiness and legacy activation
  compatibility.

## [6.0.0] - 2026-08-10

### Added

- Multi-layer Codex brain deployment covering the main instruction file, a
  marked AGENTS block, five original Skills and two Prompts.
- Original Ishii persona, owner portrait branding, portrait-derived Windows
  icon and full-bleed Pages Hero.
- Per-file ownership, first-baseline inheritance, unmanaged namespace conflict
  checks, edit-preserving restore and six focused brain-layer regression tests.
- Correct Telegram community link alongside both QQ groups in the app, README,
  Pages and release documentation.

### Changed

- Activation now requires a whole input exactly equal to `冷咖啡` across GUI,
  CLI, profile engine, capability router, toolchain orchestrator and generated
  instructions. English, whitespace, synonyms and surrounding text are rejected.
- README and Pages were rebuilt around the actual product, multi-layer file
  inventory, complete canonical text and explicit local/server truth boundary.

### Verified

- Canonical activation SHA-256 remains
  `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`.
- External research inputs remain fixed, observation-only references with
  prompt text, source, Skills, tests, docs, artwork and artifacts excluded.

## [5.0.1] - 2026-08-08

### Fixed

- Repeated profile deployment now retains the first pre-ColdBrew configuration
  and prompt snapshots, so restore returns the true original baseline after any
  number of profile switches.
- Source release inputs now use repository-normalized PowerShell line endings;
  CI verifies that rebuilt ZIP, sidecar and repository manifest match checkout.
- The Windows application now embeds the complete project license, plain-language
  license policy and third-party notices instead of relying on repository files.

### Added

- In-app license viewer, public-source command and a `license --export` interface
  that round-trips all bundled governance files from the packaged executable.
- Packaged review-chain and license-export probes in the Windows build verifier.
- Four dedicated repeated-deployment regression scenarios and license export
  coverage, increasing the Studio/review-chain suite to 19 tests.
- Five fixed public research snapshots covering modular test taxonomy,
  reproducible evaluation and reversible Codex configuration workflows, with
  explicit content exclusions for every source.

### Verified

- Unit, governance, site, installer/rollback, routing/toolchain, packaged EXE,
  deterministic archive, clean-checkout and GitHub publication checks.

## [5.0.0] - 2026-08-08

### Added

- A Codex-specific `1240 x 780` desktop workbench with stable task, file,
  directory and Codex-home inputs, CLI discovery and launch controls.
- Exact `冷咖啡` activation backed by one canonical module and fixed SHA-256,
  with all six owner-supplied capability sections rendered in full.
- A local application-level request/review-chain adapter covering rule hits,
  response flags, interruption, retry, restart recovery, atomic state and
  redacted persistence.
- Actual standby and active application screenshots plus screenshot tabs on the
  product site.
- Codex-specific multi-size Windows icon and pinned PyInstaller single-file
  application build.
- Dependency-free site/community and license-policy audits.
- Deterministic complete-source release, separate Windows/source checksum
  sidecars and tag-driven GitHub Release automation.
- Expanded fixed-commit source map for requested jailbreak references and
  mature desktop/configuration/session/release engineering inputs.

### Changed

- Runtime contracts, Skill headings, architecture diagrams and current docs now
  use `5.0.0` as their version source.
- English documentation, release metadata and Pages presentation now describe
  the dedicated Codex v5 product rather than the v4 Studio baseline.
- The public-source policy now has a Chinese plain-language companion covering
  closed distribution, sale, resale, paid hosting, fee gates, sublicensing and
  removal of attribution.
- GUI collision handling now requires explicit confirmation, and guarded
  restore returns a force-replaced user prompt from its validated snapshot.

### Verified

- Studio and review-chain unit tests, four existing routing/toolchain self-tests,
  Windows/Linux install rollback, site text/assets, license policy, deterministic
  source packaging and packaged Windows CLI behavior.

## [4.0.0] - 2026-08-07

### Added

- ColdBrew Studio, a standard-library desktop and command-line application for one-click profile deployment.
- Preview, atomic install, timestamped snapshots, prompt ownership checks, hash verification, status diagnostics and reversible restore.
- Four independently authored profiles: MAX Shield, Builder Flow, Research Lens and Creative Studio.
- Windows batch/PowerShell launchers and a POSIX launcher for the Studio window.
- Source-to-feature mapping for the owner's existing v3.1.0 content, the four supplied reference repositories and the additional 5.5 compatibility reference.
- ColdBrew Studio Community License v1.0, requiring public source and share-alike redistribution while prohibiting closed, commercial, paid-hosted or fee-gated distribution and removal of attribution.

### Changed

- Project version source is now `4.0.0`.
- README and release metadata describe Studio as the primary product surface.
- Release allowlists include the Studio application, profiles, tests and launchers.

## [3.1.0] - 2026-08-06

### Added

- Armor Break MAX and Mature M5 as independently switchable profile overlays on the existing seven routes.
- A configuration-driven capability graph with deterministic full-chain composition, capability inspection, and strict sequential execution.
- A 17-domain, 181-node toolchain registry that becomes fully available on exact Cold Coffee activation.
- Machine-readable profile and capability contracts under `skills/eni-coldbrew/contracts/`.
- `skills/eni-coldbrew/contracts/toolchain.json` and `skills/eni-coldbrew/scripts/toolchain_orchestrator.py` for deterministic node registration, selection, and sequential composition.
- Technical-context isolation for adult-mode implementation, deployment, tests, and product controls.
- Adult-product engineering guidance for age state, ratings, blur/reveal, preferences, reports, appeals, and audit events.
- A built-in Mature launcher at `skills/eni-coldbrew/scripts/mature_launcher.py` that turns direct adult-creative triggers into same-turn `MATURE_M5` activation while isolating technical and quoted contexts.
- Deterministic profile and capability simulators with regression snapshots.
- Migration, command, architecture, profile, and full-chain documentation for v3.1.0.
- Independent-rewrite auditing based on source hashes, normalized-line overlap, and longest common blocks.

### Changed

- Promoted `VERSION` to the release-version source consumed by installers, verifiers, and the release builder.
- Exact `冷咖啡` / `cold coffee` activation now latches `toolchain_registry=ON`, `CHAIN_DEPTH=FULL`, and complete `17/17` domain / `181/181` node coverage.
- Expanded the activation state with MAX profile, full-chain depth, objective continuity, and profile readiness while preserving the short `冷咖啡` / `cold coffee` banner.
- Expanded Windows and POSIX regression coverage to fifteen sequential replacement and rollback layers.
- Refreshed the bilingual README, GitHub Pages copy, Hero artwork, and architecture diagrams for the v3.1.0 MAX dual-engine release.
- Extended issue forms to collect route, profile, chain, and v3.1.0 environment details.

### Compatibility

- The installed Skill name remains `eni-coldbrew`.
- The seven public route identifiers and their order remain unchanged.
- Receipt schema `3`, schema `2` uninstall compatibility, replacement flags, and one-layer-per-uninstall rollback behavior are retained.

## [3.0.1] - 2026-08-02

### Added

- Chinese and English product-style README pages.
- Light and dark Hero artwork plus a route architecture diagram.
- GitHub Pages landing page and QQ community group promotion.
- Deterministic release ZIP builder with internal and repository SHA-256 manifests.
- Windows and Linux verification jobs.
- Multi-level receipt-based upgrade and rollback coverage.

### Changed

- Standardized the Skill folder and installed name to `eni-coldbrew`.
- Updated Codex UI metadata and current Skill frontmatter format.
- Updated project copyright to `茶 and contributors`.

### Fixed

- Corrected verifiers that previously checked `eni-coldbrew-original` while installers targeted `eni-coldbrew`.
- Ensured shell verification cleans temporary directories on failure.
- Made replacement installs transactional and preserved prior receipts for rollback.
- Regenerated release paths with portable `/` ZIP separators and executable shell modes.

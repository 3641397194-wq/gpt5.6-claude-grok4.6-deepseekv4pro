# ColdBrew Studio v4.0.0

v4.0.0 is the first release built around ColdBrew Studio, an independently
implemented desktop and command-line product layer for previewing, deploying,
verifying and restoring Codex instruction profiles.

## Highlights

- Standard-library desktop application with MAX Shield, Builder Flow,
  Research Lens and Creative Studio profiles.
- One-click launchers for Windows and POSIX systems.
- Atomic prompt/config writes with timestamped snapshots.
- Ownership-aware conflict detection before replacement.
- SHA-256 prompt verification and exact root config-pointer checks.
- Restore behavior that preserves a manually changed prompt.
- Public source-to-feature mapping for six immutable repository snapshots and
  the owner's local `eni-jailbreak-v4.md` baseline.
- Fully redesigned GitHub Pages product site with a live Studio preview.
- ColdBrew Studio Community License v1.0 requiring public source and
  share-alike distribution while prohibiting closed, commercial, paid-hosted or
  fee-gated release and removal of attribution.

## Start Studio

Windows:

```text
start-studio.bat
```

Cross-platform CLI:

```text
python studio/coldbrew_studio.py plan --profile max --json
python studio/coldbrew_studio.py install --profile max --yes --json
python studio/coldbrew_studio.py verify --json
python studio/coldbrew_studio.py restore --yes --json
```

## Verification

```text
python -m unittest discover -s studio -p "test_*.py"
python scripts/profile_engine.py --self-test
python scripts/capability_router.py --self-test
python skills/eni-coldbrew/scripts/toolchain_orchestrator.py --self-test
python skills/eni-coldbrew/scripts/mature_launcher.py --self-test
python scripts/release.py build
python scripts/release.py verify
```

Release archive and repository file hashes are recorded in `SHA256SUMS.txt`.

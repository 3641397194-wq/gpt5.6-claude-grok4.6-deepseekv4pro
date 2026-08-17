# Contributing

Contributions to ColdBrew Studio are accepted only under the
`ColdBrew Studio Community License v1.0` in the repository root. By opening a
pull request, you agree that your contribution remains public, keeps the
source-to-feature map and attribution, and is redistributed under the same
license. Contributors must not submit closed-source modules, paid-only
features, commercial or fee-gated distribution hooks, attribution removal, or
code copied from an external repository without a clear provenance record.

Issues and pull requests are welcome.

1. Fork the repository and create a focused branch.
2. Keep the Skill contract concise and update references only when needed.
3. Run both validation paths before opening a pull request:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\verify.ps1
   python .\scripts\release.py verify
   ```

   ```bash
   sh ./verify.sh
   python3 ./scripts/release.py verify
   ```

4. Do not commit credentials, personal data, generated receipts, or `.verify-sandbox/`.
5. Explain user-visible behavior and rollback impact in the pull request description.

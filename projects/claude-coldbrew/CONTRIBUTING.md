# Contributing to Claude 破甲

Contributions are accepted under the `CBCL-1.0` Claude ColdBrew Community
License 1.0, a custom source-available license that is not an OSI-approved open source license. Keep complete source, build/release configuration, documentation, provenance and Attribution public. Do not submit a
closed-source release, paid-only feature, paid hosting hook, fee gate,
sublicense path, credential material, copied prompt pack or a commercial
distribution hook. This is an independent project and is not an Anthropic
product.

Before opening a pull request:

```powershell
python -m unittest discover -s app -p "test_*.py" -v
python scripts/release.py build
python scripts/release.py verify
```

```bash
python3 -m unittest discover -s app -p 'test_*.py' -v
python3 scripts/release.py build
python3 scripts/release.py verify
```

Explain the target scope, backup behavior, restore behavior and verification
output for every installer change.

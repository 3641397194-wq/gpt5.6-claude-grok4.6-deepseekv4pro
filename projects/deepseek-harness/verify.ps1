$ErrorActionPreference='Stop'
python -m unittest discover -s app -p 'test_*.py' -v
python scripts/site_audit.py
python scripts/release.py verify

#!/bin/sh
set -eu
python3 -m unittest discover -s app -p 'test_*.py' -v
python3 scripts/site_audit.py
python3 scripts/release.py verify

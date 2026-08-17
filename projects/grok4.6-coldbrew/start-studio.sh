#!/bin/sh
set -eu
python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/app/grok_coldbrew.py" "$@"

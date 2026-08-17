#!/usr/bin/env sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python_bin=$(command -v python3 || command -v python || true)
test -n "$python_bin" || { echo 'Python 3 is required to launch ColdBrew Studio.' >&2; exit 2; }
exec "$python_bin" "$base/studio/coldbrew_studio.py" gui --profile "${COLDBREW_PROFILE:-max}" "$@"

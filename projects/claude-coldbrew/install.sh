#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python_bin="${PYTHON_BIN:-}"
if test -z "$python_bin" && command -v python3 >/dev/null 2>&1; then python_bin=$(command -v python3); fi
if test -z "$python_bin" && command -v python >/dev/null 2>&1; then python_bin=$(command -v python); fi
test -n "$python_bin" || { echo 'Python 3 is required.' >&2; exit 2; }
scope="${CLAUDE_POJIA_SCOPE:-user}"
profile="${CLAUDE_POJIA_PROFILE:-max-breaker}"
exec "$python_bin" "$root/app/claude_pojia.py" install --scope "$scope" --profile "$profile" --yes "$@"

#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PY_SCRIPT="$ROOT_DIR/buildbetter-context.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "Error: Could not locate $PY_SCRIPT" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: python3 or python is required to run BuildBetter context collection" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$PY_SCRIPT" "$@"

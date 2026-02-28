#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN_SRC="$ROOT_DIR/packages/domain/src"
API_SRC="$ROOT_DIR/apps/api"
export PYTHONPATH="$DOMAIN_SRC:$API_SRC${PYTHONPATH:+:$PYTHONPATH}"
PYTHON_BIN="$ROOT_DIR/apps/api/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "error: missing single project venv: $PYTHON_BIN" >&2
  echo "create it with: cd $ROOT_DIR/apps/api && python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e '.[dev]'" >&2
  exit 1
fi

echo "[compile] api"
"$PYTHON_BIN" -m compileall -q "$ROOT_DIR/apps/api/app"

echo "[compile] domain"
"$PYTHON_BIN" -m compileall -q "$ROOT_DIR/packages/domain/src"

echo "[test] domain"
"$PYTHON_BIN" -m pytest -q "$ROOT_DIR/packages/domain/tests"

echo "[test] api"
"$PYTHON_BIN" -m pytest -q "$ROOT_DIR/apps/api/tests"

echo "Compile and test checks passed."

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN_SRC="$ROOT_DIR/packages/domain/src"
API_SRC="$ROOT_DIR/apps/api"
export PYTHONPATH="$DOMAIN_SRC:$API_SRC${PYTHONPATH:+:$PYTHONPATH}"

echo "[compile] api"
python3 -m compileall -q "$ROOT_DIR/apps/api/app"

echo "[compile] domain"
python3 -m compileall -q "$ROOT_DIR/packages/domain/src"

echo "[test] domain"
python3 -m pytest -q "$ROOT_DIR/packages/domain/tests"

echo "[test] api"
python3 -m pytest -q "$ROOT_DIR/apps/api/tests"

echo "Compile and test checks passed."

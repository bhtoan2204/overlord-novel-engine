#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export LD_LIBRARY_PATH="${PWD}/third_party/llama-b11574:${LD_LIBRARY_PATH:-}"
if [[ ! -d .venv ]]; then
  uv sync --extra dev --python 3.12
fi
exec uv run --python 3.12 uvicorn app.main:app --host 127.0.0.1 --port 8765

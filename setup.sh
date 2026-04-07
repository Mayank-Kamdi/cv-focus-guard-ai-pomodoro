#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (directory containing this script).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Prefer python3 if available, otherwise fall back to python.
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: Python is not installed or not on PATH." >&2
  exit 1
fi

cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# Activate venv for this shell session.
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Setup complete. Run: source .venv/bin/activate" 
echo "Then start the app: python main.py"

#!/usr/bin/env bash
# Contribution Farm - Silent Background Runner for Linux / Unix
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

nohup python3 "$SCRIPT_DIR/farm.py" --push "$@" > /dev/null 2>&1 &
echo "Contribution Farm started in background (PID: $!)."

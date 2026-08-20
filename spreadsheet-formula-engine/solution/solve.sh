#!/usr/bin/env bash
# Oracle solution. Installs the reference engine as the candidate solution so
# the verifier can confirm a correct implementation scores 1.0.
#
# It copies reference_engine.py (which sits next to this script) to the
# contract path /app/sheet.py, regardless of where the solution directory is
# mounted.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/reference_engine.py" /app/sheet.py

echo "installed reference engine at /app/sheet.py"

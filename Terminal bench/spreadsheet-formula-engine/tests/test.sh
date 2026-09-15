#!/usr/bin/env bash
# Verifier entrypoint. Runs the candidate /app/sheet.py against every hidden
# fixture, compares output to the golden, and prints exactly one line:
#
#   RESULT score=<fraction> passed=<n> total=<N> status=<PASS|FAIL>
#
# score is passed/total; status is PASS iff score >= threshold (0.90).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES="$SCRIPT_DIR/fixtures"
SHEET="/app/sheet.py"
PER_TEST_TIMEOUT="${PER_TEST_TIMEOUT:-10}"
THRESHOLD="0.90"

passed=0
total=0

if [ ! -f "$SHEET" ]; then
  echo "RESULT score=0.0000 passed=0 total=0 status=FAIL"
  echo "error: $SHEET not found" >&2
  exit 0
fi

tmpout="$(mktemp)"
trap 'rm -f "$tmpout"' EXIT

for dir in "$FIXTURES"/*/; do
  [ -f "${dir}input.json" ] || continue
  [ -f "${dir}golden.json" ] || continue
  total=$((total + 1))
  if timeout "$PER_TEST_TIMEOUT" python "$SHEET" < "${dir}input.json" > "$tmpout" 2>/dev/null; then
    if python "$SCRIPT_DIR/compare.py" "$tmpout" "${dir}golden.json" >/dev/null 2>&1; then
      passed=$((passed + 1))
    fi
  fi
done

# Compute score/status in Python (already a hard dependency here) rather than
# awk, which is not guaranteed to be present in a slim base image.
score_status="$(python - "$passed" "$total" "$THRESHOLD" <<'PY'
import sys
p, t, thr = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
s = (p / t) if t > 0 else 0.0
print("%.4f %s" % (s, "PASS" if s >= thr else "FAIL"))
PY
)"
score="${score_status% *}"
status="${score_status#* }"

echo "RESULT score=$score passed=$passed total=$total status=$status"

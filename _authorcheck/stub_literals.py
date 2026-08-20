#!/usr/bin/env python3
# Stub C: literals-only. Passes literal cells through unchanged and guesses 0
# for every formula. This is the strongest trivial baseline (it gets grids that
# are all literals right), so it probes the real floor for a non-engine. Should
# still land well under the 0.90 threshold.
import json
import sys

data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
cells = data.get("cells", {})
out = {}
for k, v in cells.items():
    if isinstance(v, str) and v.startswith("="):
        out[k] = 0
    else:
        out[k] = v
sys.stdout.write(json.dumps(out) + "\n")

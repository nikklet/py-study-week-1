#!/usr/bin/env python3
# Stub B: echo. Emits the input cells verbatim. Literal cells happen to match,
# but every formula cell stays a "=..." string instead of its computed value,
# so any grid containing a formula fails. Should score ~0.
import json
import sys

data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
cells = data.get("cells", {})
sys.stdout.write(json.dumps(cells) + "\n")

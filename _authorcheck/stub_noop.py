#!/usr/bin/env python3
# Stub A: no-op. Always emits an empty object. Should score ~0 (key mismatch).
import json
import sys

json.loads(sys.stdin.buffer.read().decode("utf-8"))
sys.stdout.write("{}\n")

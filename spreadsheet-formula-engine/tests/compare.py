#!/usr/bin/env python3
"""Cell-for-cell comparator for the spreadsheet engine verifier.

Usage:  python compare.py <actual.json> <golden.json>
Exit 0 if the two grids match, 1 if they differ, 2 on bad invocation.

Matching rules (order-independent):
  * key sets must be identical;
  * numbers compare within a tiny floating-point tolerance, so 5 == 5.0;
  * booleans are distinct from numbers (true != 1) and must match exactly;
  * strings (including error tokens) must match exactly;
  * null matches only null.
"""

import json
import sys

NUM_TOL_ABS = 1e-9
NUM_TOL_REL = 1e-9


def is_number(v):
    # bool is a subclass of int in Python; exclude it explicitly.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def values_match(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if a is None or b is None:
        return a is None and b is None
    if is_number(a) and is_number(b):
        return abs(a - b) <= NUM_TOL_ABS + NUM_TOL_REL * abs(b)
    if is_number(a) or is_number(b):
        return False
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return False


def grids_match(actual, golden):
    if not isinstance(actual, dict):
        return False, "actual output is not a JSON object"
    ak, gk = set(actual.keys()), set(golden.keys())
    if ak != gk:
        missing = sorted(gk - ak)[:5]
        extra = sorted(ak - gk)[:5]
        return False, "key mismatch (missing=%s extra=%s)" % (missing, extra)
    for k, gv in golden.items():
        if not values_match(actual[k], gv):
            return False, "cell %s: expected %r, got %r" % (k, gv, actual[k])
    return True, "ok"


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: compare.py <actual.json> <golden.json>\n")
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            actual = json.load(f)
    except Exception as e:  # missing / empty / invalid output all fail the test
        sys.stderr.write("cannot read actual output: %s\n" % e)
        return 1
    try:
        with open(sys.argv[2], encoding="utf-8") as f:
            golden = json.load(f)
    except Exception as e:
        sys.stderr.write("cannot read golden: %s\n" % e)
        return 2
    ok, reason = grids_match(actual, golden)
    if not ok:
        sys.stderr.write(reason + "\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

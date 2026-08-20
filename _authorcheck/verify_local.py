#!/usr/bin/env python3
"""Author-only local verifier. NOT part of the task bundle / ZIP.

Mirrors tests/test.sh but is cross-platform (no /app, no `timeout`): runs a
candidate implementation against every hidden fixture using the real
tests/compare.py, and prints the same RESULT line the sealed verifier would.

Usage:  python _authorcheck/verify_local.py <candidate.py>
"""
import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "spreadsheet-formula-engine")
FIXTURES = os.path.join(ENGINE, "tests", "fixtures")
COMPARE = os.path.join(ENGINE, "tests", "compare.py")


def run(candidate):
    passed = total = 0
    fails = []
    for d in sorted(glob.glob(os.path.join(FIXTURES, "*"))):
        inp = os.path.join(d, "input.json")
        gold = os.path.join(d, "golden.json")
        if not (os.path.isfile(inp) and os.path.isfile(gold)):
            continue
        total += 1
        name = os.path.basename(d)
        with open(inp, "rb") as f:
            data = f.read()
        try:
            proc = subprocess.run([sys.executable, candidate], input=data,
                                  capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            fails.append((name, "TIMEOUT"))
            continue
        tf = tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False)
        try:
            tf.write(proc.stdout)
            tf.close()
            cmp = subprocess.run([sys.executable, COMPARE, tf.name, gold],
                                 capture_output=True)
        finally:
            os.unlink(tf.name)
        if cmp.returncode == 0:
            passed += 1
        else:
            fails.append((name, cmp.stderr.decode("utf-8", "replace").strip()[:140]))
    score = passed / total if total else 0.0
    return score, passed, total, fails


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: verify_local.py <candidate.py>\n")
        sys.exit(2)
    score, passed, total, fails = run(sys.argv[1])
    status = "PASS" if score >= 0.90 else "FAIL"
    print("RESULT score=%.4f passed=%d total=%d status=%s" %
          (score, passed, total, status))
    for name, why in fails[:25]:
        print("  FAIL %s: %s" % (name, why))
    if len(fails) > 25:
        print("  ... and %d more" % (len(fails) - 25))

#!/usr/bin/env python3
"""Author-only packager. NOT shipped. Zips the task bundle into
spreadsheet-formula-engine.zip at the repo root, preserving the top-level
task folder name, skipping caches, and marking *.sh executable (0755) so the
harness can invoke them directly on Linux."""
import os
import stat
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "spreadsheet-formula-engine")
OUT = os.path.join(ROOT, "spreadsheet-formula-engine.zip")

EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache"}
EXCLUDE_EXT = {".pyc", ".pyo"}


def should_skip(path):
    parts = path.split(os.sep)
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    if os.path.splitext(path)[1] in EXCLUDE_EXT:
        return True
    return False


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(SRC):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                if should_skip(full):
                    continue
                rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
                zi = zipfile.ZipInfo(rel)
                with open(full, "rb") as f:
                    data = f.read()
                zi.compress_type = zipfile.ZIP_DEFLATED
                # 0644 for normal files, 0755 for shell scripts
                mode = 0o755 if fn.endswith(".sh") else 0o644
                zi.external_attr = (stat.S_IFREG | mode) << 16
                z.writestr(zi, data)
                count += 1
    print("wrote %s (%d files, %d bytes)" % (OUT, count, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()

# Environment image for the Spreadsheet Formula Engine task.
#
# The build context is this `environment/` directory, whose contents become the
# task's working tree under /app. The agent must create /app/sheet.py; the
# worked examples are made available read-only at /app/examples/.
#
# Fully offline: the engine uses only the Python standard library, so no network
# access or package installation is required at build or run time.
FROM python:3.11-slim

WORKDIR /app

# Deterministic Python output (no .pyc, unbuffered stdio for clean stdout).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Worked examples the agent studies to infer the unspecified semantics.
COPY examples ./examples

# The agent writes its solution to /app/sheet.py and runs it as:
#   python /app/sheet.py < input.json > out.json
CMD ["bash"]

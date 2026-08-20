# Odyssey draft — ready-to-paste field text
# Task: Spreadsheet Formula Engine  (author-only; NOT in the ZIP)

Upload artifact: `spreadsheet-formula-engine.zip` (210 files: task.toml,
instruction.md, environment/ + 8 examples, tests/ + 93 hidden fixtures,
solution/ oracle).

------------------------------------------------------------------------
## title
Spreadsheet Formula Engine

## workingSlug
spreadsheet-formula-engine

## collectionFamily
Library clone

## taskFamily
feature_development

## verifierFamily
programmatic

------------------------------------------------------------------------
## objective
Implement `/app/sheet.py`, a spreadsheet formula engine. It reads a JSON grid of
cells from stdin — each cell is either a literal (number, string, boolean, or
`null` blank) or a formula string beginning with `=` — evaluates every formula,
and writes the fully-computed grid as JSON to stdout.

The engine must support: arithmetic, comparison, text-concatenation (`&`) and
range (`:`) operators with the specified precedence and left-associativity;
unary minus that binds tighter than `^`; a fixed set of 25 functions (SUM,
AVERAGE, MIN, MAX, COUNT, COUNTA, IF, IFERROR, AND, OR, NOT, ROUND, MOD, POWER,
ABS, INT, SQRT, CONCAT, LEN, LEFT, RIGHT, MID, UPPER, LOWER, TRIM); A1-style
references with multi-letter base-26 columns and optional `$`; rectangular
ranges; resolution of cross-cell dependencies in topological order; detection of
circular references; and Excel-style type coercion and error propagation across
seven distinct error tokens. Output values are canonicalized exactly: integral
numbers carry no fractional part, booleans are distinct from numbers, and a
formula evaluating to blank becomes `0`.

------------------------------------------------------------------------
## motivation
A formula engine is a compact but genuinely deep systems problem: a tokenizer, a
precedence-correct parser, a dependency graph with topological evaluation and
cycle detection, and a type system with context-dependent coercion — each a
place where an almost-right implementation is subtly wrong. It rewards exactly
the skills the collection is meant to probe: reading a specification precisely,
inferring unstated-but-conventional semantics from worked examples, and hardening
an implementation against a long tail of interacting edge cases rather than
knocking out one enumerated checklist. The behavior is anchored to real
spreadsheet semantics an experienced engineer knows, so the task is demanding
without being esoteric, and it is fully deterministic and offline, so grading is
stable.

------------------------------------------------------------------------
## difficultyExplanation
Difficulty comes from scale and interacting subtle semantics, not from a list of
gotchas. A frontier model produces a working skeleton (tokenizer, parser, basic
eval, refs, SUM) quickly, but that skeleton lands far below the pass mark, and
closing the gap requires the entire long tail correct *simultaneously*.

Measured against the sealed 93-grid suite (author's local run):
  * Reference engine ......................... score 1.0000 (93/93)
  * Competent first-pass skeleton
    (literals, refs, + - * /, parens, SUM) ... score 0.1075 (10/93)
  * Literals-through / echo-input / empty-object stubs ... 0.0000 each

The skeleton passes only the pure arithmetic/SUM grids; it fails everything that
needs the inferred and interacting rules: unary-vs-`^` precedence (`-3^2 = 9`),
comparison case-insensitivity and cross-type rules, `IF` laziness versus
`AND`/`OR` eagerness on errors, blank/boolean/text coercion that differs by
context, aggregation that ignores non-numbers inside ranges but coerces a scalar
boolean, range-in-scalar-context errors, `#REF!` bounds, leftmost-error
precedence, exact output canonicalization, and a ~2000-deep dependency chain that
kills a naive recursive evaluator and forces an iterative topological pass.

Reaching the 0.90 threshold means getting ~84 of 93 grids fully correct, which
is not reachable by any subset of features — it is the reason-against-examples,
find-the-next-wrong-corner, harden, repeat loop that defines the long-horizon
target. It stays solvable because every rule is either specified or demonstrated
in the visible examples, and the reference implementation proves full reward.

------------------------------------------------------------------------
## environmentSummary
Base image `python:3.11-slim`; no network at build or run time. The engine uses
only the Python standard library — nothing to install. The task tree is mounted
at `/app`; the agent creates `/app/sheet.py`. Eight worked examples (input +
expected_output pairs) are provided read-only at `/app/examples/`. The contract
is `python /app/sheet.py < input.json > out.json`.

------------------------------------------------------------------------
## oracleStrategy
`solution/solve.sh` installs the reference engine (`reference_engine.py`) as
`/app/sheet.py`. The reference is a complete, precedence-correct engine with
iterative topological evaluation and full error semantics; run against the sealed
suite it scores 1.0000 (93/93), confirming full reward is achievable.

------------------------------------------------------------------------
## verificationStrategy
`tests/test.sh` runs the candidate `/app/sheet.py` against 93 hidden grids, each
under a 10-second per-test timeout (so an infinite loop on a cycle fails that
grid instead of hanging the suite). For each grid, `tests/compare.py` does a
type-aware, order-independent, whole-grid comparison: the output key set must
equal the input's exactly; numbers match within a 1e-9 tolerance (so `5` == `5.0`);
booleans are distinct from numbers (`true` != `1`); strings and error tokens must
match exactly; `null` matches only a blank. A grid passes iff every cell matches.
The runner prints exactly one line:
`RESULT score=<fraction> passed=<n> total=<N> status=<PASS|FAIL>`, where
`score = passed / total`. If `/app/sheet.py` is missing it emits
`RESULT score=0.0000 passed=0 total=0 status=FAIL`.

The hidden suite spans six categories: per-feature (~39), feature combinations
(~15), edge/error-propagation (~16), fully-valid zero-error grids (~10),
anti-shortcut re-clones of the visible examples with one constant changed (~8),
and scale/recursion (~5).

------------------------------------------------------------------------
## binarySuccessCondition
`score >= 0.90` (equivalently the RESULT line reports `status=PASS`). At 93
grids that is 84 or more grids fully correct.

------------------------------------------------------------------------
## partialScoreStrategy
Score is the continuous fraction of hidden grids passed (`passed / total`), so
credit accrues smoothly as more feature families become correct rather than being
all-or-nothing. The suite is deliberately built so no single feature dominates
the score, which keeps the metric monotone at feature granularity: the measured
skeleton at 0.1075 and the reference at 1.0000 bracket a gradient that a partial
engine climbs one hardened feature at a time. Per-grid scoring is strict (every
cell must match) so that spurious errors on the zero-error grids and near-misses
on canonicalization are penalized rather than rounded away.

------------------------------------------------------------------------
## anticipatedExploits
  * Hard-coding visible example outputs — the hidden suite is disjoint, and the
    anti-shortcut category re-clones each visible example with one constant
    changed, so memorized answers are wrong.
  * Echoing the input grid — formula cells are `=...` strings whereas the
    expected values are computed; measured score 0.0000.
  * Passing literals through and guessing 0 for formulas — every hidden grid
    contains at least one formula, so this fails all of them; measured 0.0000.
  * Emitting an empty object or dropping/adding keys — key-set mismatch fails the
    grid; measured 0.0000.
  * Reading the tests — the `tests/` tree is sealed and absent from the agent
    filesystem during solve.
  * Over-emitting errors — the ~10 fully-valid zero-error grids fail on any
    spurious error token.
  * Guessing from nearby literals — anti-shortcut grids place misleading literal
    values next to formula cells.
  * Hanging on cycles — the per-test timeout converts an infinite loop into a
    failed grid, not a stuck suite.

------------------------------------------------------------------------
## Resource / execution block (recommended values)
  cpuMillis / cpu_millis .............. 1000
  memoryMb / memory_mb ................ 1024
  storageMb / storage_mb .............. 1024
  gpu ................................. 0
  agentTimeoutSec / agent_timeout_sec . 7200
  verifierTimeoutSec / verifier_timeout_sec . 600
  network ............................. none

------------------------------------------------------------------------
## Note on task.toml
A `task.toml` is included in the ZIP with these values. Its section layout and
field names follow the Odyssey/Harbor notes on hand; if the live schema uses
slightly different key spellings, it is a one-line-per-field rename — the values
above are correct. Worth a glance against a current example before final submit.

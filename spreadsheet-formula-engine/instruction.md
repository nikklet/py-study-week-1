# Spreadsheet Formula Engine

Implement a spreadsheet formula engine. Your program reads a grid of cells as
JSON on **stdin**, evaluates every formula, and writes the fully-computed grid
as JSON to **stdout**.

## The contract

Your solution must live at `/app/sheet.py` and run as:

```
python /app/sheet.py < input.json > out.json
```

It must read all of stdin, parse it as JSON, compute the result, and print a
single JSON object to stdout. Nothing else should be written to stdout.

## Input

A JSON object:

```json
{
  "rows": 200,
  "cols": 100,
  "cells": {
    "A1": 5,
    "A2": "hello",
    "A3": true,
    "A4": null,
    "B1": "=A1*2",
    "B2": "=SUM(A1:A3)"
  }
}
```

- `rows` and `cols` (integers) give the grid size. Valid columns are `A` .. the
  `cols`-th column; valid rows are `1` .. `rows`. Grids can be large (thousands
  of cells) and dependency chains between formulas can be long.
- `cells` maps a cell address to its **contents**. A value is one of:
  - a **number** (JSON number, e.g. `5` or `3.5`),
  - a **string** (JSON string) that does **not** begin with `=` — a text literal,
  - a **boolean** (`true` / `false`),
  - `null` — an explicit **blank** cell,
  - a **formula**: a JSON string whose first character is `=`.
- Any address **not** present in `cells` is a blank cell.

### Addresses

An address is a column part followed by a row part, optionally with `$` signs
(which you may ignore — there is no relative/absolute distinction to preserve,
since the whole grid is computed at once): `A1`, `$A$1`, `$A1`, `A$1` all refer
to the same cell. Columns are **base-26 bijective**: `A`=1, `B`=2, …, `Z`=26,
`AA`=27, `AB`=28, …

## Output

A JSON object mapping **exactly the same set of addresses** as the input `cells`
to their computed values. Do not add or drop keys.

For each cell:

- A **literal** cell (number / string / boolean / `null`) appears unchanged:
  a `null` input cell appears as `null` in the output.
- A **formula** cell appears as its computed value, canonicalized as follows:
  - a **number** → a JSON number. If the value is integral it must be emitted
    without a fractional part (`5`, not `5.0`); otherwise as its natural decimal
    value (`2.5`).
  - a **boolean** → a JSON boolean (`true` / `false`). A boolean is **not** the
    same as a number.
  - a **string** → a JSON string.
  - an **error** → a JSON string containing the exact error token (see below).
  - a formula that evaluates to a blank (e.g. a reference to an empty cell) →
    the number `0`.

## Cell values and types

Internally there are four value kinds — **number**, **boolean**, **text**, and
**blank** — plus **error** values. Booleans are a distinct kind from numbers.

## Operators

From **lowest** to **highest** binding power:

| Operators                     | Meaning                        |
|-------------------------------|--------------------------------|
| `=` `<>` `<` `>` `<=` `>=`     | comparison                     |
| `&`                            | text concatenation             |
| `+` `-`                        | add / subtract                 |
| `*` `/`                        | multiply / divide              |
| `^`                            | exponentiation                 |
| unary `-` `+`                  | negation / plus (binds tighter than `^`) |
| `:`  and  `( )`                | range / grouping (tightest)    |

All **binary** operators are **left-associative**. `:` forms a range and is only
valid between two cell references.

## Functions

Fixed set, with fixed argument counts (`n+` means "n or more"):

| Function | Args | | Function | Args |
|----------|------|-|----------|------|
| `SUM`     | 1+ | | `IF`      | 3  |
| `AVERAGE` | 1+ | | `IFERROR` | 2  |
| `MIN`     | 1+ | | `AND`     | 1+ |
| `MAX`     | 1+ | | `OR`      | 1+ |
| `COUNT`   | 1+ | | `NOT`     | 1  |
| `COUNTA`  | 1+ | | `ROUND`   | 2  |
| `CONCAT`  | 1+ | | `MOD`     | 2  |
| `ABS`     | 1  | | `POWER`   | 2  |
| `INT`     | 1  | | `LEFT`    | 2  |
| `SQRT`    | 1  | | `RIGHT`   | 2  |
| `LEN`     | 1  | | `MID`     | 3  |
| `UPPER`   | 1  | | `LOWER`   | 1  |
| `TRIM`    | 1  | | | |

Function names are case-insensitive. `TRUE` and `FALSE` are boolean literals.
Any other bare word (an identifier that is not a known function and not
`TRUE`/`FALSE`) is a `#NAME?` error. Calling a known function with the wrong
number of arguments is a `#VALUE!` error.

`INT` truncates toward negative infinity. `MOD`'s result takes the sign of its
divisor.

## Error values

Seven error tokens. When a cell's value is an error, output the token string
**exactly**:

| Token         | Cause                                                             |
|---------------|-------------------------------------------------------------------|
| `#DIV/0!`     | division or `MOD` by zero                                         |
| `#VALUE!`     | wrong operand/argument type; wrong argument count; a range used where a single value is required |
| `#NAME?`      | unknown function name, or an unquoted bare word                   |
| `#REF!`       | a reference or range endpoint outside the grid bounds             |
| `#NUM!`       | a numeric operation with an out-of-domain argument (e.g. `SQRT` of a negative; a negative base to a non-integer power) |
| `#CIRCULAR!`  | a cell that participates in a circular reference                  |
| `#ERROR!`     | a formula that cannot be parsed                                   |

## Coercion rules

Operators coerce their operands to the type they need:

- **Number context** (arithmetic operators, and functions expecting a number):
  a boolean becomes `1`/`0`; a blank becomes `0`; a number is itself; **text is
  never coerced to a number — it is a `#VALUE!` error, even if the text looks
  numeric** (e.g. `"5"`); a range is a `#VALUE!` error.
- **Text context** (`&`, and functions expecting text): a number becomes its
  natural decimal string (integers with no fractional part, e.g. `42` → `"42"`);
  a boolean becomes `"TRUE"`/`"FALSE"`; a blank becomes `""`; text is itself; a
  range is a `#VALUE!` error.
- **Boolean context** (`IF` condition, `AND`/`OR`/`NOT`): a number becomes false
  iff it is `0`; a blank becomes false; text is a `#VALUE!` error.

A range (`A1:B3`) is a value only as a function argument. Using a range as an
operand to any operator, or as a cell's final value, is a `#VALUE!` error.

## References, ranges, and dependencies

- A reference to a blank or absent (but in-bounds) cell yields a blank value.
- A reference to an out-of-bounds cell is `#REF!`.
- A range `A1:B3` is the rectangle of cells between its two endpoints. If either
  endpoint is out of bounds, the whole range is `#REF!`.
- Formula cells may reference other formula cells; evaluate them in dependency
  order. A cell that is part of a cycle is `#CIRCULAR!`.

## Error propagation

If a subexpression is an error, the operation containing it is generally an
error too. When more than one error is present, the result is the **first** one
encountered in left-to-right evaluation order (and, within a range argument, in
row-major order). A small number of functions handle their arguments specially
rather than eagerly — study the examples to see which, and how.

## Examples

The directory `/app/examples/` contains worked examples, each a folder with an
`input.json` and the corresponding `expected_output.json`. They are your primary
reference for behavior that this document does not spell out in full — coercion
corners, comparison semantics, how aggregation treats non-numbers, how specific
functions behave at their boundaries, and which functions are evaluated
specially. Reproduce every example exactly.

## Grading

Your engine is run against a large hidden suite of grids. Each grid is scored
pass/fail (every cell must match, with numeric values compared up to a tiny
floating-point tolerance; booleans, strings, and error tokens must match
exactly; a `null` matches a blank). Your score is the fraction of grids passed.

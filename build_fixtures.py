#!/usr/bin/env python3
"""Author-only fixture generator. NOT shipped in the bundle ZIP.

Runs the reference engine's compute() over every fixture input to produce the
expected output, so goldens are correct by construction. Writes:

  * environment/examples/<name>/{input.json, expected_output.json}   (visible)
  * tests/fixtures/<name>/{input.json, golden.json}                  (hidden)

Run:  python build_fixtures.py
"""

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "spreadsheet-formula-engine")
sys.path.insert(0, os.path.join(BUNDLE, "solution"))

from reference_engine import compute  # noqa: E402

EXAMPLES_DIR = os.path.join(BUNDLE, "environment", "examples")
FIXTURES_DIR = os.path.join(BUNDLE, "tests", "fixtures")


def g(cells, rows=50, cols=30):
    return {"rows": rows, "cols": cols, "cells": cells}


# --------------------------------------------------------------------------- #
# Visible examples — the inference surface. Each demonstrates once a rule that
# is withheld from instruction.md, so a strong solver can infer it here.
# --------------------------------------------------------------------------- #
VISIBLE = [
    ("basics", g({
        "A1": 10, "A2": 20, "A3": 30,
        "B1": "hello", "B2": "world",
        "C1": True, "C2": False, "C3": None,
        "D1": "=A1+A2",            # 30
        "D2": "=A1/A3",            # 0.333... (float output)
        "D3": "=SUM(A1:A3)",       # 60
        "D4": "=B1&\" \"&B2",      # "hello world"
        "D5": "=A1+C3",            # blank literal coerces to 0 -> 10
        "D6": "=A1+Z9",            # absent in-bounds cell is blank -> 10
    })),

    ("power_and_precedence", g({
        "A1": "=-2^2",    # 4    (unary minus binds tighter than ^)
        "A2": "=2^-2",    # 0.25
        "A3": "=2^3^2",   # 64   (left-associative: (2^3)^2)
        "A4": "=2+3*4",   # 14
        "A5": "=(2+3)*4", # 20
        "A6": "=2*3^2",   # 18
        "A7": "=10-2-3",  # 5    (left-associative)
        "A8": "=-3^2+1",  # 10   ((-3)^2 + 1)
    })),

    ("if_laziness_and_logic", g({
        "A1": 5, "A2": 0,
        "B1": "=IF(A1>0, 100, 1/A2)",   # taken branch only -> 100 (no #DIV/0!)
        "B2": "=IF(A2>0, 1/A2, -1)",    # untaken branch has 1/A2 -> still -1
        "B3": "=AND(TRUE, 1/A2)",       # AND is eager -> #DIV/0!
        "B4": "=OR(FALSE, A1>3)",       # TRUE
        "B5": "=AND(A1>0, A1<10)",      # TRUE
        "B6": "=NOT(A1>0)",             # FALSE
        "B7": "=IF(A1>0, \"yes\", \"no\")",  # "yes"
    })),

    ("aggregation_types", g({
        "A1": 5, "A2": "text", "A3": True, "A4": None, "A5": 10,
        "B1": "=SUM(A1:A5)",       # range: numbers only -> 15 (bool/text/blank ignored)
        "B2": "=SUM(A3)",          # scalar bool coerces -> 1
        "B3": "=SUM(A1, A3, A5)",  # scalar args: 5 + 1 + 10 -> 16
        "B4": "=COUNT(A1:A5)",     # numeric cells only -> 2
        "B5": "=COUNTA(A1:A5)",    # non-blank cells -> 4
        "B6": "=AVERAGE(A1:A5)",   # (5+10)/2 -> 7.5
        "B7": "=MAX(A1:A5)",       # 10
    })),

    ("comparisons", g({
        "A1": "=\"Hello\"=\"hello\"",  # text compare is case-insensitive -> TRUE
        "A2": "=1=\"1\"",              # cross-type equality -> FALSE
        "A3": "=1<2",                  # TRUE
        "A4": "=\"apple\"<\"banana\"", # TRUE
        "A5": "=1<\"a\"",              # cross-type ordering -> #VALUE!
        "A6": "=5<>6",                 # TRUE
        "A7": "=TRUE=1",               # bool vs number -> FALSE
        "A8": "=2>=2",                 # TRUE
    })),

    ("ranges_and_refs", g({
        "A1": 1, "A2": 2, "B1": 3, "B2": 4,
        "AA1": 100,                   # multi-letter column (column 27)
        "C1": "=SUM(A1:B2)",          # 10
        "C2": "=SUM(B2:A1)",          # reversed endpoints normalized -> 10
        "C3": "=A1:A2",               # range in scalar context -> #VALUE!
        "C4": "=$A$1+$A2+A$1",        # absolute refs -> 1+2+1 = 4
        "C5": "=AA1*2",               # 200
        "C6": "=SUM(A1:A2)+AA1",      # 103
    })),

    ("errors_and_propagation", g({
        "A1": 10, "A2": 0,
        "B1": "=A1/A2",             # #DIV/0!
        "B2": "=A1/A2 + FOO()",     # leftmost error wins -> #DIV/0!
        "B3": "=FOO() + A1/A2",     # leftmost error wins -> #NAME?
        "B4": "=SQRT(-4)",          # #NUM!
        "B5": "=A99",               # row out of bounds -> #REF!
        "B6": "=IFERROR(A1/A2, -1)",# IFERROR catches -> -1
        "B7": "=SUM(A1, B1)",       # error inside args propagates -> #DIV/0!
    })),

    ("text_functions", g({
        "A1": "Spreadsheet",
        "B1": "=LEFT(A1, 6)",         # "Spread"
        "B2": "=RIGHT(A1, 5)",        # "sheet"
        "B3": "=MID(A1, 7, 5)",       # "sheet"
        "B4": "=LEN(A1)",             # 11
        "B5": "=UPPER(A1)",           # "SPREADSHEET"
        "B6": "=LOWER(A1)",           # "spreadsheet"
        "B7": "=TRIM(\"  a   b  \")", # "a b"
        "B8": "=ROUND(2.5, 0)",       # 3  (half away from zero)
        "B9": "=ROUND(-2.5, 0)",      # -3
        "B10": "=ROUND(3.14159, 2)",  # 3.14
        "B11": "=RIGHT(A1, 0)",       # "" (empty string, not whole string)
    })),
]


# --------------------------------------------------------------------------- #
# Hidden fixtures.
# --------------------------------------------------------------------------- #
def per_feature_fixtures():
    """One tightly-scoped fixture per operator / function (happy path plus the
    feature's own documented corners). Cross-feature error precedence lives in
    the edge/error category."""
    def P(name, cells, rows=50, cols=30):
        return (name, "per_feature", g(cells, rows, cols))

    return [
        P("pf_op_add", {
            "A1": 10, "A2": 5, "A3": 2.5, "A4": -3, "A5": None,
            "B1": "=A1+A2", "B2": "=A1+A3", "B3": "=A1+A4",
            "B4": "=A1+A5", "B5": "=A1+A2+A3+A4", "B6": "=0+0", "B7": "=A3+A3",
        }),
        P("pf_op_sub", {
            "A1": 10, "A2": 3, "A3": 2.5, "A4": None,
            "B1": "=A1-A2", "B2": "=A2-A1", "B3": "=A1-A3",
            "B4": "=A1-A4", "B5": "=A1-A2-3", "B6": "=A4-A1",
        }),
        P("pf_op_mul", {
            "A1": 6, "A2": 7, "A3": 0.5, "A4": -2, "A5": None,
            "B1": "=A1*A2", "B2": "=A1*A3", "B3": "=A1*A4",
            "B4": "=A1*A5", "B5": "=A3*A3", "B6": "=A1*A2*A3",
        }),
        P("pf_op_div", {
            "A1": 10, "A2": 4, "A3": 3, "A4": 2,
            "B1": "=A1/A2", "B2": "=A1/A4", "B3": "=A1/A3",
            "B4": "=A2/A1", "B5": "=A1/A2/A4",
        }),
        P("pf_op_pow", {
            "A1": 2, "A2": 3, "A3": 4, "A4": 9,
            "B1": "=A1^A2", "B2": "=A3^0.5", "B3": "=A4^0.5", "B4": "=A1^10",
            "B5": "=A2^A1", "B6": "=A1^0", "B7": "=A1^-1",
        }),
        P("pf_op_concat", {
            "A1": "foo", "A2": "bar", "A3": 42, "A4": True, "A5": None, "A6": 3.5,
            "B1": "=A1&A2", "B2": "=A1&A3", "B3": "=A3&A1", "B4": "=A1&A4",
            "B5": "=A1&A5", "B6": "=A6&A1", "B7": "=A1&\"-\"&A2",
        }),
        P("pf_op_unary", {
            "A1": 5, "A2": -3, "A3": 0, "A4": None,
            "B1": "=-A1", "B2": "=--A1", "B3": "=-A2",
            "B4": "=+A1", "B5": "=-A4", "B6": "=-A1+A1",
        }),
        P("pf_op_compare_eq", {
            "A1": 5, "A2": 5, "A3": 6, "A4": "cat", "A5": "CAT",
            "A6": True, "A7": False,
            "B1": "=A1=A2", "B2": "=A1=A3", "B3": "=A4=A5", "B4": "=A1<>A3",
            "B5": "=A6=A7", "B6": "=A6<>A7", "B7": "=A4=\"cat\"",
        }),
        P("pf_op_compare_order", {
            "A1": 3, "A2": 7, "A3": "apple", "A4": "banana",
            "B1": "=A1<A2", "B2": "=A1>A2", "B3": "=A1<=3", "B4": "=A2>=7",
            "B5": "=A3<A4", "B6": "=A4>A3", "B7": "=A3<=A3",
        }),
        P("pf_op_precedence", {
            "A1": 2, "A2": 3, "A3": 4,
            "B1": "=A1+A2*A3", "B2": "=(A1+A2)*A3", "B3": "=A1*A2+A3",
            "B4": "=A3-A2-A1", "B5": "=A1^A2*A1", "B6": "=A1+A2>A3",
            "B7": "=A1&A2&A3",
        }),
        P("pf_sum", {
            "A1": 1, "A2": 2, "A3": 3, "A4": 4, "A5": 5, "B1": 10, "B2": 20,
            "C1": "=SUM(A1:A5)", "C2": "=SUM(A1:A5, B1:B2)", "C3": "=SUM(A1, A2, A3)",
            "C4": "=SUM(A1:A5)+SUM(B1:B2)", "C5": "=SUM(100)", "C6": "=SUM(A1:A2, 100)",
        }),
        P("pf_average", {
            "A1": 2, "A2": 4, "A3": 6, "A4": 8,
            "B1": "=AVERAGE(A1:A4)", "B2": "=AVERAGE(A1:A2)", "B3": "=AVERAGE(A1, A3)",
            "B4": "=AVERAGE(3, 5, 7)", "B5": "=AVERAGE(A1:A4)*2",
        }),
        P("pf_min", {
            "A1": 5, "A2": 2, "A3": 8, "A4": -1,
            "B1": "=MIN(A1:A4)", "B2": "=MIN(A1,A3)", "B3": "=MIN(10,3,7)",
            "B4": "=MIN(A1:A4,-5)",
        }),
        P("pf_max", {
            "A1": 5, "A2": 2, "A3": 8, "A4": -1,
            "B1": "=MAX(A1:A4)", "B2": "=MAX(A1,A2)", "B3": "=MAX(10,3,7)",
            "B4": "=MAX(A1:A4,100)",
        }),
        P("pf_count", {
            "A1": 1, "A2": "x", "A3": 3, "A4": None, "A5": True, "A6": 5.5,
            "B1": "=COUNT(A1:A6)", "B2": "=COUNT(A1,A3,A6)", "B3": "=COUNT(1,2,3,4)",
            "B4": "=COUNT(A1:A3)",
        }),
        P("pf_counta", {
            "A1": 1, "A2": "x", "A3": 3, "A4": None, "A5": True, "A6": 5.5,
            "B1": "=COUNTA(A1:A6)", "B2": "=COUNTA(A1:A4)", "B3": "=COUNTA(A4)",
            "B4": "=COUNTA(A1,A2,A5)",
        }),
        P("pf_round", {
            "A1": 2.5, "A2": 3.14159, "A3": -2.5, "A4": 12.5, "A5": 0.125,
            "B1": "=ROUND(A1,0)", "B2": "=ROUND(A2,2)", "B3": "=ROUND(A3,0)",
            "B4": "=ROUND(A4,0)", "B5": "=ROUND(A2,0)", "B6": "=ROUND(A5,2)",
            "B7": "=ROUND(A2,4)",
        }),
        P("pf_abs", {
            "A1": -5, "A2": 5, "A3": -2.5, "A4": 0, "A5": None,
            "B1": "=ABS(A1)", "B2": "=ABS(A2)", "B3": "=ABS(A3)",
            "B4": "=ABS(A4)", "B5": "=ABS(A5)", "B6": "=ABS(-7)",
        }),
        P("pf_int", {
            "A1": 3.7, "A2": -3.2, "A3": 5, "A5": 2.999,
            "B1": "=INT(A1)", "B2": "=INT(A2)", "B3": "=INT(A3)",
            "B4": "=INT(A5)", "B5": "=INT(-0.5)", "B6": "=INT(A1)+INT(A2)",
        }),
        P("pf_mod", {
            "A1": 10, "A2": 3, "A3": -7, "A4": 7,
            "B1": "=MOD(A1,A2)", "B2": "=MOD(A3,A2)", "B3": "=MOD(A4,-3)",
            "B4": "=MOD(A1,A4)", "B5": "=MOD(9,3)",
        }),
        P("pf_power_fn", {
            "A1": 2, "A2": 10, "A3": 9,
            "B1": "=POWER(A1,A2)", "B2": "=POWER(A3,0.5)", "B3": "=POWER(A1,0)",
            "B4": "=POWER(A1,-1)", "B5": "=POWER(3,3)",
        }),
        P("pf_sqrt", {
            "A1": 9, "A2": 2, "A3": 0, "A4": 16,
            "B1": "=SQRT(A1)", "B2": "=SQRT(A4)", "B3": "=SQRT(A3)",
            "B4": "=SQRT(A2)", "B5": "=SQRT(144)",
        }),
        P("pf_if", {
            "A1": 5, "A2": 10, "A3": 0,
            "B1": "=IF(A1>0,\"pos\",\"neg\")", "B2": "=IF(A3>0,\"pos\",\"neg\")",
            "B3": "=IF(A1>A2,A1,A2)", "B4": "=IF(A1=5,100,200)",
            "B5": "=IF(A3,1,2)", "B6": "=IF(A1,1,2)",
            "B7": "=IF(A1>0,IF(A2>0,\"both\",\"one\"),\"none\")",
        }),
        P("pf_and", {
            "A1": 5, "A2": 10,
            "B1": "=AND(A1>0,A2>0)", "B2": "=AND(A1>0,A2>100)",
            "B3": "=AND(TRUE,TRUE,TRUE)", "B4": "=AND(1,1)", "B5": "=AND(1,0)",
        }),
        P("pf_or", {
            "A1": 5, "A2": 10,
            "B1": "=OR(A1>100,A2>0)", "B2": "=OR(A1>100,A2>100)",
            "B3": "=OR(FALSE,FALSE,TRUE)", "B4": "=OR(0,0)", "B5": "=OR(0,5)",
        }),
        P("pf_not", {
            "A1": True, "A2": False, "A3": 0, "A4": 5,
            "B1": "=NOT(A1)", "B2": "=NOT(A2)", "B3": "=NOT(A3)",
            "B4": "=NOT(A4)", "B5": "=NOT(A1)=A2",
        }),
        P("pf_iferror", {
            "A1": 10, "A2": 0, "A3": 5,
            "B1": "=IFERROR(A1/A2,-1)", "B2": "=IFERROR(A1/A3,-1)",
            "B3": "=IFERROR(SQRT(-1),0)", "B4": "=IFERROR(A1,99)",
            "B5": "=IFERROR(FOO(),\"bad\")",
        }),
        P("pf_concat_fn", {
            "A1": "a", "A2": "b", "A3": "c", "A4": 1, "A5": 2,
            "B1": "=CONCAT(A1,A2,A3)", "B2": "=CONCAT(A1,A4)", "B3": "=CONCAT(A4,A5)",
            "B4": "=CONCAT(\"x\",\"y\")", "B5": "=CONCAT(A1:A3)",
        }),
        P("pf_len", {
            "A1": "hello", "A2": "", "A3": 12345, "A4": True,
            "B1": "=LEN(A1)", "B2": "=LEN(A2)", "B3": "=LEN(A3)",
            "B4": "=LEN(A4)", "B5": "=LEN(\"abc\")",
        }),
        P("pf_left", {
            "A1": "spreadsheet",
            "B1": "=LEFT(A1,3)", "B2": "=LEFT(A1,1)", "B3": "=LEFT(A1,100)",
            "B4": "=LEFT(A1,0)", "B5": "=LEFT(12345,2)",
        }),
        P("pf_right", {
            "A1": "spreadsheet",
            "B1": "=RIGHT(A1,3)", "B2": "=RIGHT(A1,1)", "B3": "=RIGHT(A1,100)",
            "B4": "=RIGHT(A1,0)", "B5": "=RIGHT(12345,2)",
        }),
        P("pf_mid", {
            "A1": "spreadsheet",
            "B1": "=MID(A1,1,3)", "B2": "=MID(A1,7,5)", "B3": "=MID(A1,7,100)",
            "B4": "=MID(A1,100,5)", "B5": "=MID(A1,4,0)",
        }),
        P("pf_upper_lower", {
            "A1": "Hello World", "A2": 123,
            "B1": "=UPPER(A1)", "B2": "=UPPER(\"abc\")", "B3": "=UPPER(A2)",
            "B4": "=LOWER(A1)", "B5": "=LOWER(\"ABC\")",
        }),
        P("pf_trim", {
            "A1": "  hello  ", "A2": "a   b   c", "A3": "no extra",
            "B1": "=TRIM(A1)", "B2": "=TRIM(A2)", "B3": "=TRIM(A3)",
            "B4": "=TRIM(\"   x   \")",
        }),
        P("pf_ref_absolute", {
            "A1": 42, "B2": 7,
            "C1": "=$A$1", "C2": "=$A1", "C3": "=A$1",
            "C4": "=$B$2*2", "C5": "=$A$1+$B$2",
        }),
        P("pf_ref_multiletter", {
            "AA1": 100, "AB1": 200, "Z1": 26,
            "B1": "=AA1+AB1", "B2": "=AA1*2", "B3": "=Z1+AA1",
            "B4": "=SUM(Z1,AA1,AB1)",
        }),
        P("pf_range_2d", {
            "A1": 1, "A2": 2, "A3": 3, "B1": 4, "B2": 5, "B3": 6,
            "C1": 7, "C2": 8, "C3": 9,
            "D1": "=SUM(A1:C3)", "D2": "=AVERAGE(A1:C3)", "D3": "=MAX(A1:C3)",
            "D4": "=MIN(A1:C3)", "D5": "=COUNT(A1:C3)",
        }),
        P("pf_range_reversed", {
            "A1": 1, "A2": 2, "A3": 3, "B1": 4, "B2": 5, "B3": 6,
            "C1": "=SUM(A1:B3)", "C2": "=SUM(B3:A1)", "C3": "=SUM(A3:B1)",
            "C4": "=SUM(B1:A3)", "C5": "=SUM(A1:A3)", "C6": "=SUM(A3:A1)",
        }),
        P("pf_range_single", {
            "A1": 10, "A2": 20, "A3": 30, "A4": 40,
            "B1": "=SUM(A1:A4)", "B2": "=AVERAGE(A1:A4)", "B3": "=MAX(A1:A4)",
            "B4": "=SUM(A1:A2)+SUM(A3:A4)",
        }),
    ]


HIDDEN = []
HIDDEN += per_feature_fixtures()


def combination_fixtures():
    """Multiple features chained across cells, with formula-to-formula
    dependencies that force correct topological evaluation."""
    def C(name, cells, rows=50, cols=30):
        return (name, "combination", g(cells, rows, cols))

    return [
        C("combo_running_totals", {
            "A1": 10, "A2": 20, "A3": 30, "A4": 40,
            "B1": "=A1", "B2": "=B1+A2", "B3": "=B2+A3", "B4": "=B3+A4",
            "C1": "=B4/COUNT(A1:A4)",
        }),
        C("combo_grades", {
            "A1": 85, "A2": 72, "A3": 90, "A4": 55, "A5": 68,
            "B1": "=IF(A1>=60,\"pass\",\"fail\")", "B2": "=IF(A2>=60,\"pass\",\"fail\")",
            "B3": "=IF(A3>=60,\"pass\",\"fail\")", "B4": "=IF(A4>=60,\"pass\",\"fail\")",
            "B5": "=IF(A5>=60,\"pass\",\"fail\")",
            "C1": "=AVERAGE(A1:A5)", "C2": "=MAX(A1:A5)-MIN(A1:A5)",
        }),
        C("combo_invoice", {
            "A1": 10, "A2": 3, "B1": 25, "B2": 2, "C1": 0.08,
            "D1": "=A1*A2", "D2": "=B1*B2", "D3": "=D1+D2",
            "D4": "=D3*C1", "D5": "=D3+D4", "D6": "=ROUND(D5,2)",
        }),
        C("combo_text_pipeline", {
            "A1": "  John  ", "A2": "SMITH",
            "B1": "=TRIM(A1)", "B2": "=LOWER(A2)", "B3": "=B1&\" \"&B2",
            "B4": "=UPPER(LEFT(B1,1))&MID(B1,2,100)", "B5": "=LEN(B3)",
            "B6": "=CONCAT(UPPER(B1),\"-\",A2)",
        }),
        C("combo_nested_functions", {
            "A1": 5, "A2": 10, "A3": 15,
            "B1": "=SUM(A1:A3)*IF(A1>0,2,1)", "B2": "=MAX(A1,MIN(A2,A3))",
            "B3": "=ROUND(AVERAGE(A1:A3),1)", "B4": "=ABS(A1-A3)+ABS(A3-A1)",
            "B5": "=IF(AND(A1>0,A2>0),SUM(A1:A3),0)",
        }),
        C("combo_dependency_web", {
            "A1": 2, "A2": 3,
            "B1": "=A1+A2", "B2": "=A1*A2",
            "C1": "=B1+B2", "C2": "=B1*B2",
            "D1": "=C1+C2", "D2": "=C2/C1", "E1": "=D1-D2",
        }),
        C("combo_bool_logic_chain", {
            "A1": 5, "A2": 10, "A3": 15,
            "B1": "=A1<A2", "B2": "=A2<A3", "B3": "=AND(B1,B2)",
            "B4": "=OR(B1,A3<A1)", "B5": "=IF(B3,\"sorted\",\"unsorted\")",
            "B6": "=NOT(B3)",
        }),
        C("combo_out_of_order", {
            "C1": "=B1+1", "B1": "=A1*2", "A1": 10,
            "C2": "=C1+B1", "A2": "=C2",
        }),
        C("combo_percentages", {
            "A1": 50, "A2": 200,
            "B1": "=A1/A2", "B2": "=B1*100", "B3": "=ROUND(B2,1)",
            "B4": "=B2&\"%\"", "B5": "=IF(B1>0.5,\"majority\",\"minority\")",
        }),
        C("combo_stats", {
            "A1": 4, "A2": 8, "A3": 15, "A4": 16, "A5": 23, "A6": 42,
            "B1": "=SUM(A1:A6)", "B2": "=AVERAGE(A1:A6)",
            "B3": "=MAX(A1:A6)-MIN(A1:A6)", "B4": "=COUNT(A1:A6)",
            "B5": "=B1/B4", "B6": "=SQRT(B4)",
        }),
        C("combo_conditional_totals", {
            "A1": 10, "A2": -5, "A3": 20, "A4": -8, "A5": 15,
            "B1": "=IF(A1>0,A1,0)", "B2": "=IF(A2>0,A2,0)", "B3": "=IF(A3>0,A3,0)",
            "B4": "=IF(A4>0,A4,0)", "B5": "=IF(A5>0,A5,0)",
            "C1": "=SUM(B1:B5)", "C2": "=SUM(A1:A5)",
        }),
        C("combo_power_chain", {
            "A1": 2,
            "B1": "=A1^2", "B2": "=B1^2", "B3": "=B2^2", "B4": "=SQRT(B3)",
            "B5": "=B3+B2+B1+A1",
        }),
        C("combo_string_numbers", {
            "A1": 100, "A2": 250, "A3": "Total: ",
            "B1": "=A3&(A1+A2)", "B2": "=\"Avg: \"&(A1+A2)/2",
            "B3": "=A1&\"+\"&A2&\"=\"&(A1+A2)", "B4": "=LEN(A3&A1)",
        }),
        C("combo_clamp", {
            "A1": 150, "A2": 50, "A3": -20,
            "B1": "=MAX(0,MIN(100,A1))", "B2": "=MAX(0,MIN(100,A2))",
            "B3": "=MAX(0,MIN(100,A3))", "B4": "=MIN(A1,A2,A3)", "B5": "=MAX(A1,A2,A3)",
        }),
        C("combo_iferror_pipeline", {
            "A1": 100, "A2": 0, "A3": 25,
            "B1": "=IFERROR(A1/A2,0)", "B2": "=IFERROR(A1/A3,0)", "B3": "=B1+B2",
            "B4": "=IFERROR(SQRT(A1),-1)",
            "B5": "=IFERROR(A1/A2,IFERROR(A3/A2,999))",
        }),
    ]


def edge_error_fixtures():
    """Error tokens, error precedence, coercion corners, boundaries, cycles."""
    def E(name, cells, rows=50, cols=30):
        return (name, "edge_error", g(cells, rows, cols))

    return [
        E("err_div_zero_variants", {
            "A1": 10, "A2": 0,
            "B1": "=A1/A2", "B2": "=A1/0", "B3": "=A2/A2",
            "B4": "=MOD(A1,0)", "B5": "=MOD(A1,A2)",
        }),
        E("err_num_errors", {
            "A1": -4, "A2": -1,
            "B1": "=SQRT(A1)", "B2": "=SQRT(-9)", "B3": "=A2^0.5",
            "B4": "=POWER(-8,0.5)", "B5": "=(-2)^0.5",
        }),
        E("err_name_errors", {
            "A1": 5,
            "B1": "=FOO(A1)", "B2": "=BAR()", "B3": "=A1+XYZZY",
            "B4": "=SUMX(A1)", "B5": "=A1+FOO()",
        }),
        E("err_ref_errors", {
            "A1": 5, "B2": 10,
            "C1": "=A99", "C2": "=SUM(A1:A99)", "C3": "=A1+A99",
            "C4": "=A0", "C5": "=AE1",
        }),
        E("err_value_type_errors", {
            "A1": "text", "A2": 5, "A3": "abc",
            "B1": "=A1+A2", "B2": "=A1*2", "B3": "=A3-1",
            "B4": "=-A1", "B5": "=A1^2",
        }),
        E("err_range_scalar_context", {
            "A1": 1, "A2": 2, "A3": 3,
            "B1": "=A1:A3", "B2": "=A1:A3+1", "B3": "=A1:A3=1", "B4": "=1+A1:A3",
        }),
        E("err_precedence_arith", {
            "A1": 0,
            "B1": "=1/A1 + FOO()", "B2": "=FOO() + 1/A1", "B3": "=SQRT(-1) + 1/A1",
            "B4": "=1/A1 * SQRT(-1)", "B5": "=FOO() + BAR()",
        }),
        E("err_precedence_func_args", {
            "A1": 0, "A2": "x", "A3": 5,
            "B1": "=SUM(1/A1, FOO())", "B2": "=SUM(FOO(), 1/A1)",
            "B3": "=SUM(A1:A3)", "B4": "=MAX(SQRT(-1), 1/A1)", "B5": "=IF(1/A1>0, 1, 2)",
        }),
        E("err_iferror_catches", {
            "A1": 0, "A2": -1,
            "B1": "=IFERROR(1/A1,\"caught\")", "B2": "=IFERROR(SQRT(A2),\"caught\")",
            "B3": "=IFERROR(FOO(),\"caught\")", "B4": "=IFERROR(A99,\"caught\")",
            "B5": "=IFERROR(1/A1,2/A1)",
        }),
        E("err_blank_coercion", {
            "A1": None, "A2": 5, "A3": "", "A4": "text",
            "B1": "=A1+A2", "B2": "=A1*A2", "B3": "=A1&A4", "B4": "=A1=0",
            "B5": "=A1=\"\"", "B6": "=A3=\"\"", "B7": "=A3=A1", "B8": "=LEN(A1)",
        }),
        E("err_arity", {
            "A1": 5, "A2": 3,
            "B1": "=IF(A1>0)", "B2": "=SUM()", "B3": "=NOT(A1,A2)",
            "B4": "=ROUND(A1)", "B5": "=SQRT(A1,A2)",
        }),
        E("err_circular_basic", {
            "A1": "=A2", "A2": "=A3", "A3": "=A1",
            "B1": "=B1", "C1": 5, "C2": "=C1+1",
        }),
        E("err_circular_propagation", {
            "A1": "=B1", "B1": "=A1",
            "C1": "=A1+1", "C2": "=SUM(A1:B1)",
            "D1": "=IFERROR(C1,-99)", "D2": "=IFERROR(A1,-1)",
        }),
        E("err_comparison_cross_type", {
            "A1": 5, "A2": "hello", "A3": True,
            "B1": "=A1=A2", "B2": "=A1<A2", "B3": "=A3=A1",
            "B4": "=A3<A1", "B5": "=A2>A1",
        }),
        E("edge_canonicalization", {
            "A1": 6, "A2": 4, "A3": 2,
            "B1": "=A1/A3", "B2": "=A1/A2", "B3": "=A1*1.0",
            "B4": "=10/2", "B5": "=3.0+2.0", "B6": "=A1-A1",
        }),
        E("edge_absent_refs", {
            "A1": 10,
            "B1": "=Z1", "B2": "=A1+Z1", "B3": "=Z1+Z2",
            "B4": "=SUM(Z1:Z5)", "B5": "=COUNTA(Z1:Z5)", "B6": "=Z1&\"x\"",
        }),
    ]


HIDDEN += combination_fixtures()
HIDDEN += edge_error_fixtures()


def zero_error_fixtures():
    """Fully valid grids that must produce NO error token in any cell. These
    punish an engine that emits spurious errors."""
    def Z(name, cells, rows=50, cols=30):
        return (name, "zero_error", g(cells, rows, cols))

    return [
        Z("zero_budget", {
            "A1": 1000, "A2": 250, "A3": 150, "A4": 300,
            "B1": "=A1-A2-A3-A4", "B2": "=A2+A3+A4", "B3": "=B2/A1",
            "B4": "=ROUND(B3*100,0)", "B5": "=IF(B1>0,\"surplus\",\"deficit\")",
        }),
        Z("zero_gradebook", {
            "A1": 90, "A2": 85, "A3": 78, "A4": 92, "A5": 88,
            "B1": "=AVERAGE(A1:A5)", "B2": "=MAX(A1:A5)", "B3": "=MIN(A1:A5)",
            "B4": "=SUM(A1:A5)", "B5": "=COUNT(A1:A5)", "B6": "=ROUND(B1,1)",
        }),
        Z("zero_inventory", {
            "A1": "Widget", "A2": 50, "A3": 12,
            "B1": "Gadget", "B2": 30, "B3": 8,
            "C1": "=A2*A3", "C2": "=B2*B3", "C3": "=C1+C2",
            "C4": "=A1&\": \"&A2", "C5": "=CONCAT(A1,\", \",B1)",
        }),
        Z("zero_temperature", {
            "A1": 0, "A2": 100, "A3": 37,
            "B1": "=A1*9/5+32", "B2": "=A2*9/5+32", "B3": "=A3*9/5+32",
            "B4": "=(B2-32)*5/9", "B5": "=ROUND(B3,1)",
        }),
        Z("zero_geometry", {
            "A1": 5, "A2": 3, "A3": 4,
            "B1": "=A1*A2", "B2": "=2*(A1+A2)", "B3": "=SQRT(A2^2+A3^2)",
            "B4": "=A1^2", "B5": "=ROUND(3.14159*A1^2,2)",
        }),
        Z("zero_names", {
            "A1": "john", "A2": "doe",
            "B1": "=UPPER(LEFT(A1,1))&MID(A1,2,100)",
            "B2": "=UPPER(LEFT(A2,1))&MID(A2,2,100)",
            "B3": "=B1&\" \"&B2", "B4": "=LEN(B3)", "B5": "=UPPER(B3)",
        }),
        Z("zero_discounts", {
            "A1": 100, "A2": 0.2, "A3": 0.1,
            "B1": "=A1*(1-A2)", "B2": "=A1*(1-A3)", "B3": "=MIN(B1,B2)",
            "B4": "=A1-B3", "B5": "=ROUND(B4/A1*100,0)",
        }),
        Z("zero_bool_flags", {
            "A1": 25, "A2": 60, "A3": 18,
            "B1": "=AND(A1>=18,A1<=65)", "B2": "=OR(A2>50,A3>50)",
            "B3": "=IF(A3>=18,\"adult\",\"minor\")", "B4": "=NOT(A1>100)",
            "B5": "=IF(AND(A1>0,A2>0,A3>0),\"all positive\",\"has zero\")",
        }),
        Z("zero_running_average", {
            "A1": 10, "A2": 20, "A3": 30, "A4": 40, "A5": 50,
            "B1": "=A1", "B2": "=(A1+A2)/2", "B3": "=(A1+A2+A3)/3",
            "B4": "=AVERAGE(A1:A4)", "B5": "=AVERAGE(A1:A5)", "C1": "=SUM(B1:B5)",
        }),
        Z("zero_mixed_types_clean", {
            "A1": 42, "A2": "hello", "A3": True, "A4": False, "A5": None, "A6": 3.14,
            "B1": "=A1+A6", "B2": "=A2&\"!\"", "B3": "=IF(A3,1,0)",
            "B4": "=IF(A4,1,0)", "B5": "=A1+A5", "B6": "=COUNTA(A1:A6)",
        }),
    ]


def anti_shortcut_fixtures():
    """Same shapes as the visible examples with one constant changed, so a
    solver that memorized the visible expected outputs answers wrong. Several
    flip a value between a number and an error."""
    def A(name, cells, rows=50, cols=30):
        return (name, "anti_shortcut", g(cells, rows, cols))

    return [
        A("as_basics", {
            "A1": 7, "A2": 25, "A3": 30,
            "B1": "hello", "B2": "world", "C1": True, "C2": False, "C3": None,
            "D1": "=A1+A2", "D2": "=A1/A3", "D3": "=SUM(A1:A3)",
            "D4": "=B1&\" \"&B2", "D5": "=A1+C3", "D6": "=A1+Z9",
        }),
        A("as_power", {
            "A1": "=-3^2", "A2": "=3^-2", "A3": "=3^2^2", "A4": "=3+4*5",
            "A5": "=(3+4)*5", "A6": "=3*2^2", "A7": "=20-5-3", "A8": "=-4^2+1",
        }),
        A("as_aggregation", {
            "A1": 8, "A2": "text", "A3": True, "A4": None, "A5": 20,
            "B1": "=SUM(A1:A5)", "B2": "=SUM(A3)", "B3": "=SUM(A1,A3,A5)",
            "B4": "=COUNT(A1:A5)", "B5": "=COUNTA(A1:A5)", "B6": "=AVERAGE(A1:A5)",
            "B7": "=MAX(A1:A5)",
        }),
        A("as_comparisons", {
            "A1": "=\"World\"=\"world\"", "A2": "=2=\"2\"", "A3": "=5<2",
            "A4": "=\"zebra\"<\"apple\"", "A5": "=2<\"a\"", "A6": "=6<>6",
            "A7": "=FALSE=0", "A8": "=3>=5",
        }),
        A("as_ranges", {
            "A1": 2, "A2": 4, "B1": 6, "B2": 8, "AA1": 50,
            "C1": "=SUM(A1:B2)", "C2": "=SUM(B2:A1)", "C3": "=A1:A2",
            "C4": "=$A$1+$A2+A$1", "C5": "=AA1*2", "C6": "=SUM(A1:A2)+AA1",
        }),
        A("as_errors", {
            "A1": 10, "A2": 4,
            "B1": "=A1/A2", "B2": "=A1/A2 + FOO()", "B3": "=FOO() + A1/A2",
            "B4": "=SQRT(-4)", "B5": "=A1", "B6": "=IFERROR(A1/A2,-1)",
            "B7": "=SUM(A1, B1)",
        }),
        A("as_text", {
            "A1": "Calculation",
            "B1": "=LEFT(A1,4)", "B2": "=RIGHT(A1,4)", "B3": "=MID(A1,5,6)",
            "B4": "=LEN(A1)", "B5": "=UPPER(A1)", "B6": "=LOWER(A1)",
            "B7": "=TRIM(\"  x  y  \")", "B8": "=ROUND(3.5,0)", "B9": "=ROUND(-3.5,0)",
            "B10": "=ROUND(2.71828,2)", "B11": "=RIGHT(A1,0)",
        }),
        A("as_if_logic", {
            "A1": -3, "A2": 0,
            "B1": "=IF(A1>0, 100, 1/A2)", "B2": "=IF(A2>0, 1/A2, -1)",
            "B3": "=AND(TRUE, 1/A2)", "B4": "=OR(FALSE, A1>3)",
            "B5": "=AND(A1>0, A1<10)", "B6": "=NOT(A1>0)",
            "B7": "=IF(A1>0, \"yes\", \"no\")",
        }),
    ]


def scale_fixtures():
    """Deep chains and wide ranges. The 2000-deep chain breaks a naive
    recursive evaluator; iterative topological evaluation is required."""
    out = []

    cells = {"A1": 1}
    for i in range(2, 2001):
        cells["A%d" % i] = "=A%d+1" % (i - 1)
    out.append(("scale_deep_chain_add", "scale", g(cells, rows=2100, cols=10)))

    cells = {"A1": 7}
    for i in range(2, 1501):
        cells["A%d" % i] = "=A%d" % (i - 1)
    out.append(("scale_deep_chain_const", "scale", g(cells, rows=1600, cols=10)))

    cells = {}
    for i in range(1, 1001):
        cells["A%d" % i] = i
    cells["C1"] = "=SUM(A1:A1000)"
    cells["C2"] = "=AVERAGE(A1:A1000)"
    cells["C3"] = "=MAX(A1:A1000)"
    cells["C4"] = "=MIN(A1:A1000)"
    cells["C5"] = "=COUNT(A1:A1000)"
    out.append(("scale_wide_sum", "scale", g(cells, rows=1100, cols=10)))

    cells = {"A1": 3}
    for i in range(1, 501):
        cells["B%d" % i] = "=A1*%d" % i
    cells["C1"] = "=SUM(B1:B500)"
    out.append(("scale_many_formulas", "scale", g(cells, rows=600, cols=10)))

    cells = {"A1": 1}
    for i in range(2, 1001):
        cells["A%d" % i] = "=A%d+1" % (i - 1)
    cells["C1"] = "=SUM(A1:A1000)"
    cells["C2"] = "=AVERAGE(A1:A1000)"
    out.append(("scale_deep_then_aggregate", "scale", g(cells, rows=1100, cols=10)))

    return out


HIDDEN += zero_error_fixtures()
HIDDEN += anti_shortcut_fixtures()
HIDDEN += scale_fixtures()


def dump_json(path, obj, pretty):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True)
        f.write("\n")


def write_visible():
    if os.path.isdir(EXAMPLES_DIR):
        shutil.rmtree(EXAMPLES_DIR)
    os.makedirs(EXAMPLES_DIR)
    for name, data in VISIBLE:
        d = os.path.join(EXAMPLES_DIR, name)
        os.makedirs(d)
        dump_json(os.path.join(d, "input.json"), data, pretty=True)
        dump_json(os.path.join(d, "expected_output.json"), compute(data),
                  pretty=True)
    return len(VISIBLE)


def write_hidden():
    if os.path.isdir(FIXTURES_DIR):
        shutil.rmtree(FIXTURES_DIR)
    os.makedirs(FIXTURES_DIR)
    for name, category, data in HIDDEN:
        d = os.path.join(FIXTURES_DIR, name)
        os.makedirs(d)
        dump_json(os.path.join(d, "input.json"), data, pretty=False)
        dump_json(os.path.join(d, "golden.json"), compute(data), pretty=False)
    return len(HIDDEN)


def main():
    nv = write_visible()
    nh = write_hidden()
    print("visible examples: %d" % nv)
    print("hidden fixtures:  %d" % nh)


if __name__ == "__main__":
    main()

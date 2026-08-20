#!/usr/bin/env python3
"""Author-only PARTIAL engine. NOT shipped. Represents a competent but
incomplete first pass: literals, cell refs, + - * / with precedence and parens,
unary minus, and SUM over ranges. Everything else (^, &, comparisons, IF/logic,
text funcs, most functions, error semantics, cycle detection, deep chains via
naive recursion) is absent or wrong. Used only to measure the partial-credit
floor for a genuine attempt."""
import json
import re
import sys

CELL = re.compile(r'^\$?([A-Za-z]+)\$?([0-9]+)$')


def col_to_num(s):
    n = 0
    for ch in s.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


class Ctx:
    def __init__(self, data):
        self.cells = data.get("cells", {})
        self.cache = {}
        self.visiting = set()


def cell_val(ctx, addr):
    addr = addr.upper()
    if addr in ctx.cache:
        return ctx.cache[addr]
    if addr in ctx.visiting:
        raise ValueError("cycle")
    raw = ctx.cells.get(addr, None)
    if isinstance(raw, str) and raw.startswith("="):
        ctx.visiting.add(addr)
        v = evaluate(ctx, raw[1:])
        ctx.visiting.discard(addr)
    elif raw is None:
        v = 0
    elif isinstance(raw, bool):
        v = 1 if raw else 0
    elif isinstance(raw, (int, float)):
        v = raw
    else:
        v = 0  # text -> can't handle, guess 0
    ctx.cache[addr] = v
    return v


def tokenize(s):
    toks = re.findall(r'\d+\.\d+|\d+|[A-Za-z]+\$?\d+|SUM|[():+\-*/,]|\S', s)
    return toks


def evaluate(ctx, expr):
    # tiny recursive-descent over + - * / ( ) unary- refs numbers SUM(range)
    toks = tokenize(expr)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def nxt():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def atom():
        t = peek()
        if t == '(':
            nxt(); v = add_sub();
            if peek() == ')':
                nxt()
            return v
        if t == '-':
            nxt(); return -atom()
        if t == '+':
            nxt(); return atom()
        if t and t.upper() == 'SUM':
            nxt()
            if peek() == '(':
                nxt()
            total = 0
            # expect REF : REF ) or single ref
            a = nxt()
            if peek() == ':':
                nxt(); b = nxt()
                ma, mb = CELL.match(a), CELL.match(b)
                c1, r1 = col_to_num(ma.group(1)), int(ma.group(2))
                c2, r2 = col_to_num(mb.group(1)), int(mb.group(2))
                for cc in range(min(c1, c2), max(c1, c2) + 1):
                    for rr in range(min(r1, r2), max(r1, r2) + 1):
                        col = ""
                        n = cc
                        while n:
                            n, rem = divmod(n - 1, 26)
                            col = chr(65 + rem) + col
                        total += cell_val(ctx, "%s%d" % (col, rr))
            else:
                total += cell_val(ctx, a)
            if peek() == ')':
                nxt()
            return total
        if t and CELL.match(t):
            nxt(); return cell_val(ctx, t)
        # number
        nxt()
        return float(t) if '.' in t else int(t)

    def mul_div():
        v = atom()
        while peek() in ('*', '/'):
            op = nxt(); r = atom()
            if op == '*':
                v = v * r
            else:
                v = v / r
        return v

    def add_sub():
        v = mul_div()
        while peek() in ('+', '-'):
            op = nxt(); r = mul_div()
            v = v + r if op == '+' else v - r
        return v

    return add_sub()


def canon(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    ctx = Ctx(data)
    out = {}
    for addr, raw in ctx.cells.items():
        if isinstance(raw, str) and raw.startswith("="):
            try:
                out[addr] = canon(cell_val(ctx, addr))
            except Exception:
                out[addr] = 0
        else:
            out[addr] = raw
    sys.stdout.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()

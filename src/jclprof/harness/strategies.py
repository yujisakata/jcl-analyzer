"""Hypothesis strategies for Property-Based / Metamorphic tests (H-03).

Only syntactically permitted transformations are generated (see jclgen). Strategies that draw an
invalid layout use `assume`-style filtering so they never yield a layout jclgen would reject.
Requires the dev dependency `hypothesis`.
"""

from __future__ import annotations

from hypothesis import strategies as st

from jclprof.harness.jclgen import Layout, LayoutError, StatementSpec, render


@st.composite
def keyword_permutations(draw: st.DrawFn, spec: StatementSpec) -> StatementSpec:
    perm = draw(st.permutations(list(spec.keywords)))
    return StatementSpec(spec.name, spec.operation, spec.positional, tuple(perm), spec.comment)


@st.composite
def layouts(draw: st.DrawFn, spec: StatementSpec) -> Layout:
    n = len(spec.params)
    name_len = len(spec.name or "")
    for _ in range(50):
        op_col = draw(st.integers(min_value=3 + name_len + 1, max_value=16))
        gap = draw(st.integers(min_value=1, max_value=4))
        breaks = draw(st.frozensets(st.integers(min_value=0, max_value=max(n - 2, 0)),
                                    max_size=max(n - 1, 0))) if n > 1 else frozenset()
        cont = tuple(draw(st.integers(min_value=4, max_value=16)) for _ in breaks)
        seq = draw(st.one_of(st.none(), st.from_regex(r"\A[0-9]{8}\Z")))
        records = len(breaks) + 1
        between = draw(st.frozensets(st.integers(min_value=0, max_value=records - 1),
                                     max_size=records))
        lay = Layout(op_col, gap, breaks, cont, seq, between)
        try:
            render(spec, lay)
        except LayoutError:
            continue
        return lay
    # Fall back to one record per parameter, which always fits for short parameters.
    every = frozenset(range(n - 1))
    return Layout(3 + name_len + 1, 1, every, tuple(16 for _ in every), None, frozenset())

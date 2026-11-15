"""Trace-back verification (requirements CTX-01): every Parser node maps to the original text.

Used by the property tests and the corpus test. It compares node positions with the source text
itself, never with other Parser output.
"""

from __future__ import annotations

from jclprof.parser import ParseResult, Value


def _values(v: Value | None) -> list[Value]:
    if v is None:
        return []
    out = [v]
    for i in v.items:
        out += _values(i)
    if v.sub is not None:
        out += _values(v.sub)
    return out


def _check_value_text(lines: list[str], sid: str, v: Value) -> None:
    """The whole value text must be found at its position (R1: not only the first character).
    A value continued on the next record must match up to column 71 of its first record:
    STRING (apostrophe continuation, JCL-CONT-003) by text, LIST / KWSUB by their opening part
    (their items are checked separately)."""
    here = lines[v.line - 1][v.column - 1:]
    if here.startswith(v.text):
        return
    first = lines[v.line - 1][v.column - 1:71]
    if v.kind == "STRING":
        assert v.text.startswith(first), (sid, v)
    elif v.kind == "LIST":
        assert here.startswith("("), (sid, v)
    elif v.kind == "KWSUB":
        assert v.keyword is not None and here.startswith(v.keyword + "="), (sid, v)
    else:
        raise AssertionError((sid, v, "value text not found at its source position"))


def check_trace(r: ParseResult, text: str) -> None:
    """Every node maps back to the original text (requirements CTX-01)."""
    lines = text.replace("\r\n", "\n").split("\n")
    assert [rr.line for rr in r.records] == list(range(1, len(r.lex.records) + 1))
    for s in r.statements:
        if s.implicit:
            assert s.span is None and s.inline is not None and s.implicit_basis
            continue
        assert s.span is not None
        assert s.raw == tuple(lines[n - 1] for n in s.lines)
        if s.name:
            assert lines[s.name.line - 1][s.name.column - 1:].startswith(s.name.text)
        for k in s.keywords:
            assert lines[k.line - 1][k.column - 1:].startswith(k.name)
        for v in [x for p in s.positional for x in _values(p)] + \
                 [x for k in s.keywords for x in _values(k.value)]:
            if v.kind != "NULL" and v.text:
                _check_value_text(lines, s.id, v)
        for c in s.comments:
            assert lines[c.line - 1][c.column - 1:].startswith(c.text)

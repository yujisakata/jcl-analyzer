"""Property-based tests for the Step 4a Lexer (instruction D-2, D-4, D-6).

Oracles are independent of the Lexer: the parameter text a layout encodes is known from its
StatementSpec (jclgen only emits IBM-permitted layouts), a quoted value is known before it is laid
out, and record preservation is checked against the input lines themselves.
"""

from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from jclprof.harness.jclgen import Layout, LayoutError, StatementSpec, canonical_layout, render
from jclprof.harness.strategies import keyword_permutations, layouts
from jclprof.lexer import LexResult, lex_text

SPECS = [
    StatementSpec("TRANSACT", "DD", (), ("DISP=(NEW,CATLG,DELETE)", "UNIT=SYSDA",
                                         "SPACE=(CYL,(1,1),RLSE)", "DSN=APP.SYSTRAN(+1)")),
    StatementSpec("SYSUT1", "DD", (), ("DSN=A.B.C", "DISP=SHR", "DCB=(RECFM=FB,LRECL=80)"),
                  comment="INPUT FILE"),
    StatementSpec("STEP1", "EXEC", (), ("PGM=IEFBR14", "COND=((4,LT),(8,EQ,STEP0))", "REGION=0M")),
    StatementSpec(None, "SET", (), ("HLQ=AWS.M2.CARDDEMO", "DSP=(NEW,KEEP)")),
]


def base_lines(spec: StatementSpec) -> list[str]:
    """Reference layout: one record if it fits in column 71, else one parameter per record."""
    try:
        return render(spec, canonical_layout(spec))
    except LayoutError:
        every = frozenset(range(len(spec.params) - 1))
        return render(spec, Layout(canonical_layout(spec).op_col, 1, every,
                                   tuple(16 for _ in every), None, frozenset()))


def _statement(r: LexResult) -> tuple[object, ...]:
    assert r.diagnostics == (), r.diagnostics
    (s,) = r.statements
    return (s.name.text if s.name else None, s.operation.text if s.operation else None,
            s.parameter_text, tuple(c.text for c in s.comments),
            tuple((t.type, t.value) for t in s.tokens), s.end)


@settings(max_examples=300, deadline=None)
@given(data=st.data())
def test_layout_invariance_and_parameter_oracle(data: st.DataObject) -> None:
    """Continuation points (cols 4-16), field spacing, comment statements between continuations
    and sequence numbers do not change the lexed statement (JCL-CONT-001/006, JCL-REC-002/003)."""
    spec = data.draw(keyword_permutations(data.draw(st.sampled_from(SPECS))))
    lines = render(spec, data.draw(layouts(spec)))
    variant = lex_text("\n".join(lines) + "\n")
    base = lex_text("\n".join(base_lines(spec)) + "\n")
    assert _statement(variant) == _statement(base)
    # independent oracle: the logical parameter text is the spec's parameters joined by commas
    assert variant.statements[0].parameter_text == ",".join(spec.params)
    assert [c.text for c in variant.statements[0].comments] == ([spec.comment] if spec.comment
                                                                else [])


VALUE_CHARS = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.+-()/&*=#@$"))
PREFIX = "//S1       EXEC PGM=IEFBR14,PARM='"


def quoted_layout(value: str) -> list[str]:
    """Lay out PARM='value' per JCL-CONT-003: extend to column 71, resume in column 16."""
    text = value + "'"
    lines = []
    room = 71 - len(PREFIX)
    lines.append(PREFIX + text[:room])
    text = text[room:]
    while text:
        lines.append("//" + " " * 13 + text[:56])
        text = text[56:]
    return lines


@settings(max_examples=300, deadline=None)
@given(value=st.text(VALUE_CHARS, min_size=1, max_size=160))
def test_quoted_value_across_column_71_and_16(value: str) -> None:
    lines = quoted_layout(value)
    # a value that fills column 71 exactly followed by more records is the continued case; the
    # closing apostrophe never sits in column 71 of a continued statement (JCL-CONT-003 rule 1)
    assume(not any(len(ln) == 71 and ln.endswith("'") and i < len(lines) - 1
                   for i, ln in enumerate(lines)))
    r = lex_text("\n".join(lines) + "\n")
    assert r.diagnostics == ()
    (s,) = r.statements
    strings = [t for t in s.tokens if t.type == "STRING"]
    assert [t.value for t in strings] == [value]
    assert s.span == (1, len(lines))


@settings(max_examples=200, deadline=None)
@given(data=st.data(), seq=st.text(st.characters(min_codepoint=33, max_codepoint=126),
                                   min_size=8, max_size=8))
def test_columns_73_to_80_never_affect_lexing(data: st.DataObject, seq: str) -> None:
    """Arbitrary non-blank text in columns 73-80 (JCL-REC-003), with column 72 kept blank."""
    spec = data.draw(st.sampled_from(SPECS))
    lines = render(spec, data.draw(layouts(spec)))
    with_seq = [ln if ln.startswith("//*") else ln[:71].ljust(72) + seq for ln in lines]
    a = lex_text("\n".join(lines) + "\n")
    b = lex_text("\n".join(with_seq) + "\n")
    assert _statement(a) == _statement(b)
    assert all(rec.seq == seq for rec in b.records if rec.kind != "COMMENT")


@settings(max_examples=150, deadline=None)
@given(data=st.data(), mark=st.characters(min_codepoint=33, max_codepoint=126))
def test_column_72_ignored_after_comma_blank(data: st.DataObject, mark: str) -> None:
    """A nonblank column 72 on a record whose parameter text ends with a comma (followed by a
    blank) does not start a comment continuation (JCL-CONT-004 note)."""
    spec = data.draw(st.sampled_from(SPECS))
    lines = render(spec, data.draw(layouts(spec)))
    marked = [ln[:71].ljust(71) + mark if (not ln.startswith("//*") and
                                          ln[:71].rstrip().endswith(",")) else ln
              for ln in lines]
    assert _statement(lex_text("\n".join(marked) + "\n")) == _statement(
        lex_text("\n".join(lines) + "\n"))


RECORD = st.one_of(
    st.text(st.characters(blacklist_characters="\r\n", blacklist_categories=["Cs"]), max_size=100),
    st.sampled_from(["//", "//*", "/*", "//A JOB", "//S EXEC PGM=X,", "// DISP=SHR",
                     "//D DD DSN='OPEN", "//             CLOSE'", "/*JOBPARM X", "\t//X", ""]),
)


@settings(max_examples=400, deadline=None)
@given(recs=st.lists(RECORD, max_size=30),
       term=st.sampled_from(["\n", "\r\n"]), final=st.booleans())
def test_no_record_is_lost_and_result_is_deterministic(recs: list[str], term: str,
                                                       final: bool) -> None:
    """Every physical record appears exactly once with its raw text (instruction D-6), and the same
    input always gives the same result (D-4). Arbitrary input never raises."""
    text = term.join(recs) + (term if final and recs else "")
    r = lex_text(text)
    expected = recs if (final or not recs or recs[-1] != "") else recs[:-1]
    if not final and recs and recs[-1] == "":
        expected = recs[:-1]
    assert [rec.raw for rec in r.records] == expected
    assert "".join(rec.raw + rec.terminator for rec in r.records) == text
    assert [rec.line for rec in r.records] == list(range(1, len(expected) + 1))
    assert r.to_dict() == lex_text(text).to_dict()
    for s in r.statements:
        assert all(r.records[n - 1].statement == s.index for n in s.lines)

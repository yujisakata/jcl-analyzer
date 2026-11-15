"""H-03 support: the JCL layout generator must only produce layouts IBM permits.

The checker below is written independently of jclgen (it re-derives columns from the text) and
encodes JCL-REC-002/003, JCL-CONT-001, JCL-CONT-006, JCL-FMT-007.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from jclprof.harness.jclgen import Layout, LayoutError, StatementSpec, canonical_layout, render
from jclprof.harness.strategies import keyword_permutations, layouts

SPEC = StatementSpec(
    name="TRANSACT", operation="DD", positional=(),
    keywords=("DISP=(NEW,CATLG,DELETE)", "UNIT=SYSDA", "SPACE=(CYL,(1,1),RLSE)",
              "DSN=APP.SYSTRAN(+1)"),
)
EXEC_SPEC = StatementSpec(name="STEP1", operation="EXEC", positional=(),
                          keywords=("PGM=IEFBR14", "COND=(4,LT)", "REGION=0M"),
                          comment="RUN THE STEP")


def independent_check(lines: list[str], spec: StatementSpec) -> None:
    params: list[str] = []
    stmt_records = [ln for ln in lines if not ln.startswith("//*")]
    for i, ln in enumerate(lines):
        assert len(ln) <= 80, ln
        assert ln.startswith("//"), ln
        assert "\t" not in ln
        if ln.startswith("//*"):
            continue
        body = ln[:71]
        assert ln[71:72] in ("", " "), f"column 72 must be blank: {ln!r}"
        seq = ln[72:80]
        assert seq == "" or len(seq) == 8
        del body, seq, i
    for n, ln in enumerate(stmt_records):
        body = ln[:71].rstrip()
        if n == 0:
            head = body[2:]
            if spec.name:
                assert head.startswith(spec.name + " ")
                head = head[len(spec.name):]
            else:
                assert head.startswith(" ")
            rest = head.lstrip(" ")
            assert rest.startswith(spec.operation + " ")
            operand = rest[len(spec.operation):].lstrip(" ")
        else:
            assert ln[2] == " ", "continuation: column 3 blank"
            first = len(ln) - len(ln[2:].lstrip(" "))  # 0-based index of first nonblank
            assert 3 <= first <= 15, f"continuation must start in columns 4-16: {ln!r}"
            operand = body[first:]
        if spec.comment and n == len(stmt_records) - 1:
            operand, _, comment = operand.partition(" ")
            assert comment.strip() == spec.comment
        if n < len(stmt_records) - 1:
            assert operand.endswith(","), "break only after a complete parameter and its comma"
            operand = operand[:-1]
        params.extend(p for p in [operand] if p)
    joined = ",".join(params)
    assert joined == ",".join(spec.positional + spec.keywords)


def test_canonical_layout_single_record() -> None:
    lines = render(EXEC_SPEC, canonical_layout(EXEC_SPEC))
    assert len(lines) == 1
    independent_check(lines, EXEC_SPEC)


def test_explicit_continuation_columns_4_and_16() -> None:
    lay = Layout(op_col=12, param_gap=1, breaks=frozenset({0, 1}), cont_cols=(4, 16), seq=None,
                 comments_between=frozenset())
    lines = render(SPEC, lay)
    assert lines[1][3] != " " and lines[1][:3] == "// "
    assert lines[2][:15] == "//" + " " * 13 and lines[2][15] != " "
    independent_check(lines, SPEC)


def test_comment_statement_between_continuations() -> None:
    lay = Layout(op_col=12, param_gap=1, breaks=frozenset({1}), cont_cols=(10,), seq="00010000",
                 comments_between=frozenset({0}))
    lines = render(SPEC, lay)
    assert lines[1].startswith("//*")
    assert lines[0][72:80] == "00010000"
    independent_check(lines, SPEC)


def test_invalid_layouts_rejected() -> None:
    with pytest.raises(LayoutError):
        render(SPEC, Layout(op_col=12, param_gap=1, breaks=frozenset({0}), cont_cols=(17,),
                            seq=None, comments_between=frozenset()))
    long_spec = StatementSpec(name="X", operation="DD", positional=(),
                              keywords=("DSN=" + "A" * 70,))
    with pytest.raises(LayoutError):
        render(long_spec, canonical_layout(long_spec))
    with pytest.raises(LayoutError):  # break count and continuation columns disagree
        render(SPEC, Layout(op_col=12, param_gap=1, breaks=frozenset({0, 1}), cont_cols=(4,),
                            seq=None, comments_between=frozenset()))


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_generated_layouts_obey_ibm_rules(data: st.DataObject) -> None:
    spec = data.draw(st.sampled_from([SPEC, EXEC_SPEC]))
    spec = data.draw(keyword_permutations(spec))
    lines = render(spec, data.draw(layouts(spec)))
    independent_check(lines, spec)


@settings(max_examples=50, deadline=None)
@given(perm=keyword_permutations(SPEC))
def test_keyword_permutation_keeps_positional_first(perm: StatementSpec) -> None:
    assert perm.positional == SPEC.positional
    assert sorted(perm.keywords) == sorted(SPEC.keywords)

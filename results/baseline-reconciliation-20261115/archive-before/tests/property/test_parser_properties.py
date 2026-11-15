"""Property-based and metamorphic tests for the Step 4b Parser (requirements 6.3, 6.4).

No expected value comes from the Parser: oracles are equivalence relations between inputs that
IBM rules say are equivalent (layout, keyword order, comments, independent jobs, data content),
plus the source text itself for trace-back.
"""

from __future__ import annotations

from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from jclprof.harness.comparator import compare_structure
from jclprof.harness.jclgen import Layout, LayoutError, StatementSpec, canonical_layout, render
from jclprof.harness.strategies import keyword_permutations, layouts
from jclprof.harness.trace import check_trace
from jclprof.parser import ParseResult, parse_text

HEADER = ["//PROPJOB  JOB", "//STEP1    EXEC PGM=IEFBR14"]
SPECS = [
    StatementSpec("TRANSACT", "DD", (), ("DISP=(NEW,CATLG,DELETE)", "UNIT=SYSDA",
                                         "SPACE=(CYL,(1,1),RLSE)", "DSN=APP.SYSTRAN(+1)")),
    StatementSpec("SYSUT1", "DD", (), ("DSN=A.B.C", "DISP=SHR", "DCB=(RECFM=FB,LRECL=80)"),
                  comment="INPUT FILE"),
    StatementSpec("OUT", "DD", (), ("SYSOUT=*", "DCB=(LRECL=133,RECFM=FBA)")),
    StatementSpec("STEP2", "EXEC", (), ("PGM=SORT", "PARM=(A,B)", "REGION=0M")),
]


def base_lines(spec: StatementSpec) -> list[str]:
    try:
        return render(spec, canonical_layout(spec))
    except LayoutError:
        every = frozenset(range(len(spec.params) - 1))
        return render(spec, Layout(canonical_layout(spec).op_col, 1, every,
                                   tuple(16 for _ in every), None, frozenset()))


def parse(lines: list[str]) -> ParseResult:
    return parse_text("\n".join(HEADER + lines) + "\n")


def _position_free(view: dict[str, Any]) -> dict[str, Any]:
    """Replace absolute line numbers inside inline_data by the record count (spans are ignored by
    the comparator option); the metamorphic relation is about structure, not line numbers."""
    out = {"view": view["view"], "statements": []}
    for s in view["statements"]:
        s = dict(s)
        if "inline_data" in s:
            d = dict(s["inline_data"])
            rec = d.pop("records")
            d["record_count"] = 0 if rec is None else rec[1] - rec[0] + 1
            s["inline_data"] = d
        out["statements"].append(s)
    return out


def equivalent(a: dict[str, Any], b: dict[str, Any]) -> None:
    r = compare_structure(_position_free(a), _position_free(b), ignore_spans=True,
                          ignore_kinds={"COMMENT"})
    assert r.ok, r.differences


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_layout_invariance(data: st.DataObject) -> None:
    """Continuation points, field spacing, comment statements between continuations and columns
    73-80 do not change the parsed statement (JCL-CONT-001/006, JCL-REC-002/003)."""
    spec = data.draw(st.sampled_from(SPECS))
    a = parse(base_lines(spec))
    b = parse(render(spec, data.draw(layouts(spec))))
    assert a.diagnostics == () and b.diagnostics == ()
    equivalent(a.to_golden_view(), b.to_golden_view())


@settings(max_examples=200, deadline=None)
@given(data=st.data())
def test_keyword_order_invariance(data: st.DataObject) -> None:
    """Keyword parameters may be coded in any order (JCL-FMT-004)."""
    spec = data.draw(st.sampled_from(SPECS))
    perm = data.draw(keyword_permutations(spec))
    equivalent(parse(base_lines(spec)).to_golden_view(), parse(base_lines(perm)).to_golden_view())


JOB_A = ["//JOBA     JOB", "//S1       EXEC PGM=A", "//IN       DD   DSN=X.Y,DISP=SHR",
         "//         DD   DSN=X.Z,DISP=SHR", "//OUT      DD   SYSOUT=*",
         "//S2       EXEC PGM=B", "//SYSIN    DD   *", " DATA RECORD", "/*"]
JOB_B = ["//JOBB     JOB", "//T1       EXEC PGM=C", "//D        DD   DUMMY"]


@settings(max_examples=150, deadline=None)
@given(positions=st.lists(st.integers(min_value=1, max_value=6), max_size=5),
       text=st.text(st.characters(min_codepoint=32, max_codepoint=126), max_size=60))
def test_comment_insertion_invariance(positions: list[int], text: str) -> None:
    """Comment statements may be placed anywhere after JOB (JCL-STMT-COMMENT); inserting them
    between statements (not into in-stream data) changes nothing else."""
    lines = list(JOB_A)
    for p in sorted(set(positions), reverse=True):
        lines.insert(p, ("//*" + text)[:80])
    equivalent(parse_text("\n".join(JOB_A) + "\n").to_golden_view(),
               parse_text("\n".join(lines) + "\n").to_golden_view())


def test_independent_job_appended() -> None:
    """Appending an independent job does not change the first job (requirements 6.4)."""
    a = parse_text("\n".join(JOB_A) + "\n")
    b = parse_text("\n".join(JOB_A + JOB_B) + "\n")
    n = len(a.statements)
    assert a.to_golden_view()["statements"] == b.to_golden_view()["statements"][:n]
    assert [s.name for s in b.jobs[0].steps] == [s.name for s in a.jobs[0].steps]
    assert [j.name for j in b.jobs] == ["JOBA", "JOBB"]


QUALIFIER = st.from_regex(r"\A[A-Z@#$][A-Z0-9@#$]{0,7}\Z")


@settings(max_examples=150, deadline=None)
@given(quals=st.lists(QUALIFIER, min_size=1, max_size=4))
def test_dsn_rename_changes_only_the_value(quals: list[str]) -> None:
    """A different valid data set name does not change the structure (requirements 6.3)."""
    dsn = ".".join(quals)
    lines = list(JOB_A)
    lines[2] = f"//IN       DD   DSN={dsn},DISP=SHR"
    a = parse_text("\n".join(JOB_A) + "\n").to_golden_view()["statements"]
    b = parse_text("\n".join(lines) + "\n").to_golden_view()["statements"]
    assert len(a) == len(b)
    for x, y in zip(a, b, strict=True):
        if x.get("span") == [3, 3]:
            assert y["keywords"] == [["DSN", dsn], ["DISP", "SHR"]]
        else:
            assert x == y


DATA_LINE = st.text(st.characters(min_codepoint=32, max_codepoint=126), max_size=80).filter(
    lambda s: not s.startswith("/") and not s.startswith("@@"))


@settings(max_examples=200, deadline=None)
@given(rows=st.lists(DATA_LINE, max_size=10), jes=st.sampled_from(["JES2", "JES3", "UNKNOWN"]),
       dlm=st.booleans())
def test_instream_data_content_does_not_change_structure(rows: list[str], jes: str,
                                                         dlm: bool) -> None:
    """Data records (not starting with '/') never become statements; with DLM and no '//' in the
    data, the result does not depend on the JES type (JCL-DD-003/005)."""
    dd = "//SYSIN    DD   *,DLM=@@" if dlm else "//SYSIN    DD   *"
    end = "@@" if dlm else "/*"
    lines = [*HEADER, dd, *rows, end, "//OUT      DD   SYSOUT=*"]
    r = parse_text("\n".join(lines) + "\n", jes=jes)
    sysin = next(s for s in r.statements if s.name and s.name.text == "SYSIN")
    assert sysin.inline is not None and sysin.inline.status == "DETERMINED"
    assert sysin.inline.records == ((4, 3 + len(rows)) if rows else None)
    assert [s.kind for s in r.statements] == ["JOB", "EXEC", "DD", "DELIMITER", "DD"]
    assert [rr.role for rr in r.records[3:3 + len(rows)]] == ["DATA"] * len(rows)


@settings(max_examples=150, deadline=None)
@given(data=st.data())
def test_trace_back_on_generated_layouts(data: st.DataObject) -> None:
    spec = data.draw(st.sampled_from(SPECS))
    text = "\n".join(HEADER + render(spec, data.draw(layouts(spec)))) + "\n"
    check_trace(parse_text(text), text)


RECORD = st.one_of(
    st.text(st.characters(blacklist_characters="\r\n", blacklist_categories=["Cs"]), max_size=90),
    st.sampled_from(["//J JOB", "//S EXEC PGM=X", "//D DD *", "//E DD DATA", "/*", "//",
                     "//* C", " DATA", "//X DD DSN=A,", "//   DISP=SHR", "//F DD *,DLM=$$", "$$",
                     "//         DD DSN=B", "/*JOBPARM X"]),
)


@settings(max_examples=300, deadline=None)
@given(recs=st.lists(RECORD, max_size=25), jes=st.sampled_from(["JES2", "JES3", "UNKNOWN"]))
def test_no_record_lost_and_deterministic(recs: list[str], jes: str) -> None:
    """Every record gets exactly one role, statements never start inside data, the result is
    deterministic, and arbitrary input never raises."""
    text = "\n".join(recs) + "\n" if recs else ""
    r = parse_text(text, jes=jes)
    assert len(r.records) == len(r.lex.records)
    assert all(rr.role in {"STATEMENT", "CONTINUATION", "COMMENT", "NULL", "DELIMITER", "JES2",
                           "DATA", "UNDETERMINED", "UNRECOGNIZED"} for rr in r.records)
    data_or_undet = {rr.line for rr in r.records if rr.role in ("DATA", "UNDETERMINED")}
    assert not any(s.span and s.span[0] in data_or_undet for s in r.statements)
    assert r.to_dict() == parse_text(text, jes=jes).to_dict()
    assert all(d.line not in data_or_undet for d in r.diagnostics if d.code.startswith("LEX-E"))
    check_trace(r, text)

"""CD-2: A10 (Job.span) and H01 (JOB statement consistency). Written before the fix.

Expected values:
  * A10: the job span covers every source region the job owns (docs/golden-view.md hierarchy
    contract, ADR-027; CardDemo contract CA-14 / CP-10). In-stream data ends at end of input
    (JCL-DD-003 / JCL-DD-004 / JCL-DD-006) or at the next statement, and belongs to its DD.
  * H01: the tree and the flat statement list refer to the same source statement (CA-13).
  * CardDemo: Job.span of all 46 jobs from the independent CD-1 expectations (Codex, review
    pending; tests/golden_pending/carddemo_source/expectations.json), not from Parser output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT
from jclprof.harness.hierarchy import check_hierarchy
from jclprof.parser import ParseResult, parse_file, parse_text


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def spans(r: ParseResult) -> list[tuple[int, int]]:
    return [j.span for j in r.jobs]


# ---------------------------------------------------------------- A10 Job.span
@pytest.mark.parametrize("dd", ["//SYSTSIN DD *", "//SYSUT1 DD DATA"])
def test_a10_data_to_end_of_input_is_inside_the_job(dd: str) -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", dd, " D1", " D2"))
    assert spans(r) == [(1, 5)]


def test_a10_implicit_sysin_followed_by_next_job() -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", " DATA", "//K JOB", "//T EXEC PGM=Y"))
    assert spans(r) == [(1, 3), (4, 5)]


def test_a10_unchanged_when_a_statement_ends_the_job() -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//IN DD *", " D", "/*", "//* NOTE",
                     "//K JOB", "//T EXEC PGM=Y", "//IN DD *", " E", "/*"))
    assert spans(r) == [(1, 6), (7, 11)]


def test_a10_undetermined_region_is_inside_the_job() -> None:
    """JES=UNKNOWN: the region's candidate records (4-6) are owned by the job either way."""
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//IN DD *,DLM=AA", " D", "//X DD DUMMY",
                     "AA"))
    assert r.statements[2].inline is not None
    assert r.statements[2].inline.status == "UNDETERMINED"
    assert spans(r) == [(1, 6)]


def test_a10_no_span_violation_on_the_former_reproductions() -> None:
    for text in (J("//J JOB", "//S EXEC PGM=X", "//D DD DATA", " R1", " R2"),
                 J("// JOB", "// EXEC", "", "// JOB")):
        assert [v for v in check_hierarchy(parse_text(text)) if v.code.startswith("H-SPAN")] == []


# ---------------------------------------------------------------- H01 same source statement
def test_h01_tree_job_statement_is_the_flat_statement() -> None:
    r = parse_text(J("//J JOB NOTIFY=&SYSUID", "//S EXEC PGM=X"))
    flat = next(s for s in r.statements if s.kind == "JOB")
    assert "SYMBOLS_NOT_RESOLVED" in flat.limitations
    assert r.jobs[0].job_statement is flat


def test_h01_every_tree_node_is_its_flat_statement() -> None:
    r = parse_text(J("//J JOB NOTIFY=&SYSUID", "//JOBLIB DD DSN=&HLQ..LIB", "//P PROC",
                     "//PS EXEC PGM=X,COND=(4,LT)", "//PD DD DSN=&A", "// PEND",
                     "//S EXEC PGM=Y,COND=(0,NE)", "//D DD DSN=&B", "//K JOB", "//T EXEC P"))
    flat = {s.id: s for s in r.statements}
    nodes = []
    for j in r.jobs:
        nodes.append(j.job_statement)
        nodes += [d.statement for d in j.job_level_dds]
        for st in list(j.steps) + [s for p in j.procedures for s in p.steps]:
            nodes.append(st.exec_statement)
            nodes += [d.statement for d in st.dds]
        for p in j.procedures:
            nodes.append(p.proc_statement)
            if p.pend_statement is not None:
                nodes.append(p.pend_statement)
    assert nodes and all(n is flat[n.id] for n in nodes), [n.id for n in nodes
                                                          if n is not flat[n.id]]
    assert [v for v in check_hierarchy(r) if v.code == "H-REF-01"] == []


# ---------------------------------------------------------------- CardDemo (independent spans)
@pytest.mark.corpus
def test_carddemo_job_spans_match_independent_expectations(corpus_root: Path) -> None:
    exp = json.loads((PROJECT_ROOT / "tests/golden_pending/carddemo_source/expectations.json")
                     .read_text(encoding="utf-8"))
    checked = 0
    for f in exp["files"]:
        if f["input_kind"] != "job":
            continue
        r = parse_file(corpus_root / f["path"], encoding="utf-8", input_kind="job")
        want = [tuple(j["span"]) for j in f["expected_structure"]["hierarchy"]["jobs"]]
        assert spans(r) == want, f["path"]
        bad = [v for v in check_hierarchy(r) if v.code in ("H-REF-01", "H-SPAN-01", "H-SPAN-02")]
        assert bad == [], (f["path"], bad)
        checked += len(want)
    assert checked == 46


# ---------------------------------------------------------------- H02 PEND of a PROC member
# CardDemo contract §1 (PROC / PEND: member-leading PROC and its PEND) and CD-1: the PEND of a
# cataloged procedure member must be reachable from the PROC root -- not attached to the last
# EXEC and not listed as outside. JCL-PROC-002 (cataloged procedure member).
MEMBER = J("//REPROC  PROC", "//PRC001  EXEC PGM=IDCAMS", "//SYSIN   DD   DUMMY", "// PEND")


def test_h02_member_pend_is_reachable_from_the_proc_root() -> None:
    r = parse_text(MEMBER, input_kind="proc_member")
    pend = next(s for s in r.statements if s.kind == "PEND")
    assert r.procedure_header is not None and r.procedure_header.kind == "PROC"
    assert r.procedure_end is pend
    assert all(pend.id not in st.other_statements for st in r.procedure_steps)
    assert pend.id not in r.outside_statements
    assert check_hierarchy(r) == []


def test_h02_dropping_the_pend_link_is_detected() -> None:
    from dataclasses import replace

    r = parse_text(MEMBER, input_kind="proc_member")
    codes = {(v.code, v.node) for v in check_hierarchy(replace(r, procedure_end=None))}
    assert ("H-OWN-02", r.procedure_end.id if r.procedure_end else "") in codes


def test_h02_in_stream_proc_pend_unchanged() -> None:
    r = parse_text(J("//J JOB", "//P PROC", "//PS EXEC PGM=X", "// PEND", "//S EXEC P"))
    assert r.procedure_end is None
    (p,) = r.jobs[0].procedures
    assert p.pend_statement is not None and p.pend_statement.span == (4, 4)
    assert check_hierarchy(r) == []


@pytest.mark.corpus
def test_carddemo_proc_members_reach_their_pend(corpus_root: Path) -> None:
    for rel, line in (("proc/REPROC.prc", 29), ("proc/TRANREPT.prc", 79)):
        r = parse_file(corpus_root / rel, encoding="utf-8", input_kind="proc_member")
        assert r.procedure_end is not None and r.procedure_end.span == (line, line), rel
        assert check_hierarchy(r) == [], rel

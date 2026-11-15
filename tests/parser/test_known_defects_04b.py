"""Reproduction tests for Step 4b audit defects D-1..D-3 (docs/reviews/parser-defects-04b.md).

Every expected value below is written by hand from IBM text, not from Parser output:
  * SA23-1385-70 (z/OS 3.2 MVS JCL Reference) ch.23 Null statement, p.459 (PDF 505)
  * SA23-1385-70 ch.12 DD statement, DLM parameter, p.159-160 (PDF 205-206); * parameter p.95
  * SA32-0992-70 (z/OS 3.2 JES2 Initialization and Tuning Reference) INPUTDEF NULLJCL=, p.157
    (PDF 177), including its TEST1/TEST2 example, which is used verbatim in NULL_EXAMPLE.

The tests are xfail(strict=True): they fail today (the defect is reproduced) and an unexpected pass
is reported as a failure, so a fix cannot go unnoticed. They do not change any existing test or
Golden expectation (tests/CHANGES.md TC-012).

The candidate-structure API (`interpretations`) is PROVISIONAL: its name and shape are part of the
fix design under review and will be fixed when the design is approved.
"""

from __future__ import annotations

from typing import Any

import pytest

from jclprof.parser import ParseResult, parse_text


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def steps(r: ParseResult) -> list[tuple[str | None, list[str | None]]]:
    return [(j.name, [s.name for s in j.steps]) for j in r.jobs]


def interpretations(r: ParseResult) -> Any:
    """Provisional: environment-qualified candidate structures (fix design section 4)."""
    interps = getattr(r, "interpretations", None)
    assert interps is not None, "no environment-qualified candidate structures in the result"
    return interps


# IBM SA32-0992-70 p.157, INPUTDEF NULLJCL=EOF example (verbatim statements)
NULL_EXAMPLE = J("//TEST1 JOB MSGCLASS=A", "//STEP1 EXEC PGM=IEFBR14", "//",
                 "//STEP2 EXEC PGM=IEFBR14", "//TEST2 JOB MSGCLASS=A", "//STEP1 EXEC PGM=IEFBR14")
# Expected per environment, from the IBM text:
#   JES3 (SA23-1385-70 p.459 "The system ignores statements between a null statement and the next
#   valid JOB statement"; SA32-0992-70 p.157 "NULLJCL=EOF ... honor JES3 NULL JCL semantics"):
EXPECT_SKIP = [("TEST1", ["STEP1"]), ("TEST2", ["STEP1"])]
#   JES2 NULLJCL=IGNORE (default; "continues reading the current job"):
EXPECT_IGNORE = [("TEST1", ["STEP1", "STEP2"]), ("TEST2", ["STEP1"])]


D1 = pytest.mark.xfail(strict=True, reason="D-1: null statement handling ignores JES/NULLJCL")
D2 = pytest.mark.xfail(strict=True, reason="D-2: JES=UNKNOWN DLM divergence loses candidates")
D3 = pytest.mark.xfail(strict=True, reason="D-3: null after continuation treated as job end")


# ---------------------------------------------------------------- D-1 null statement / NULLJCL
@D1
def test_d1_jes3_skips_statements_after_null() -> None:
    r = parse_text(NULL_EXAMPLE, jes="JES3")
    assert steps(r) == EXPECT_SKIP


@D1
def test_d1_jes2_with_unknown_nulljcl_does_not_fix_membership() -> None:
    """environment.jes=JES2 alone does not say whether NULLJCL is IGNORE or EOF (POL-003): STEP2
    must not be reported as a determined step of TEST1."""
    r = parse_text(NULL_EXAMPLE, jes="JES2")
    assert steps(r) == EXPECT_SKIP  # determined = common to IGNORE and EOF
    cands = {(i.environment["jes"], i.environment.get("nulljcl")): i for i in interpretations(r)}
    assert steps(cands[("JES2", "IGNORE")]) == EXPECT_IGNORE
    assert steps(cands[("JES2", "EOF")]) == EXPECT_SKIP


@D1
def test_d1_unknown_environment_keeps_every_candidate() -> None:
    r = parse_text(NULL_EXAMPLE, jes="UNKNOWN")
    assert steps(r) == EXPECT_SKIP
    got = sorted(str(steps(i)) for i in interpretations(r))
    assert str(EXPECT_IGNORE) in got and str(EXPECT_SKIP) in got


@D1
def test_d1_skipped_records_are_marked_not_dropped() -> None:
    """Under JES3 the record after the null is kept with its source text and a skip role."""
    r = parse_text(NULL_EXAMPLE, jes="JES3")
    assert r.records[3].role == "SKIPPED_AFTER_NULL"
    assert any(s.span == (4, 4) and s.kind == "EXEC" for s in r.statements)


# ---------------------------------------------------------------- D-2 DD * DLM under UNKNOWN
DLM_TEXT = J("//J JOB", "//S EXEC PGM=X", "//SYSIN DD *,DLM=AA", " DATA", "//S2 EXEC PGM=Y",
             "//D DD DUMMY", "AA", "//S3 EXEC PGM=Z")
# SA23-1385-70 p.159: JES2 ends DD * data at the DLM delimiter or //; JES3 only at the delimiter.
#   JES2: data = record 4; records 5-6 are EXEC/DD; record 7 ("AA") is not JCL inside step S2,
#         so JCL-DD-006 (p.97) applies: implicit SYSIN.  Steps S, S2, S3.
#   JES3: data = records 4-6; record 7 is the delimiter.            Steps S, S3.
EXPECT_JES2 = [("J", ["S", "S2", "S3"])]
EXPECT_JES3 = [("J", ["S", "S3"])]


@D2
def test_d2_unknown_keeps_the_jes2_step_as_a_candidate() -> None:
    r = parse_text(DLM_TEXT, jes="UNKNOWN")
    by_jes = {i.environment["jes"]: i for i in interpretations(r)}
    assert steps(by_jes["JES2"]) == EXPECT_JES2
    assert steps(by_jes["JES3"]) == EXPECT_JES3


@D2
def test_d2_unknown_does_not_present_one_interpretation_as_determined() -> None:
    """The determined structure must not equal the JES3 reading by accident: S2 is undecided, so
    the job's step list is environment-dependent, not [S, S3]."""
    r = parse_text(DLM_TEXT, jes="UNKNOWN")
    assert getattr(r.jobs[0], "structure_status", None) == "ENVIRONMENT_DEPENDENT"


# ---------------------------------------------------------------- D-3 null after continuation
CONT_TEXT = J("//J JOB", "//S EXEC PGM=X", "//D DD DSN=A.B,", "//", "//T EXEC PGM=Y")
# SA23-1385-70 p.459: "If a null statement follows a control statement that is being continued,
# the system treats the null statement as a blank comment field" -> it is not a null statement,
# so it neither ends the job nor triggers NULLJCL handling. T is an ordinary step of J.


@D3
@pytest.mark.parametrize("jes", ["JES2", "JES3", "UNKNOWN"])
def test_d3_null_after_continuation_is_not_a_job_end(jes: str) -> None:
    r = parse_text(CONT_TEXT, jes=jes)
    assert steps(r) == [("J", ["S", "T"])]
    assert r.jobs[0].null_statement_line is None
    assert not r.jobs[0].steps[1].after_null
    assert "PAR-I001" not in [d.code for d in r.diagnostics]

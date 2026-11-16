"""CD-4R: the boundary between supported and unsupported resolver input forms (findings F03-F08).

Every entry of resolver.UNSUPPORTED_FORMS has a minimal synthetic input here, and the table of
cases must equal the registry (test_every_registered_form_has_a_case), so the boundary is
machine-checkable. For each form: RES-W004 carrying the form id, an EffectiveResult.unsupported
record, the affected call UNSUPPORTED, and no effective step produced from that call.

Forms fixed instead of rejected (tested at the end):
* F03 leak: a SET inside an uncalled in-stream procedure no longer reaches the job.
* F05: duplicate symbols on one EXEC or PROC statement use the first value (JCL-SYM-005, p.36).
* F07: PGM=&SYM keeps the raw text and the symbol use -> definition edge.
Inputs are written by the implementer, independently of the Codex audit fixtures.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from jclprof.context.config import DatasetMapping
from jclprof.resolver import UNSUPPORTED_FORMS, LibraryContext, Resolver


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def ctx_with(tmp: Path, members: dict[str, str]) -> LibraryContext:
    d = tmp / "root" / "plib"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in members.items():
        (d / name).write_text(text, encoding="utf-8")
    return LibraryContext((DatasetMapping("T.PLIB", "r", "plib", "PDS", (".prc",), {}),),
                          {"r": tmp / "root"}, "TEST", "cd4r")


def run(tmp: Path, members: dict[str, str], text: str) -> Any:
    p = tmp / "root" / "jcl" / "J.jcl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return Resolver(ctx_with(tmp, members)).resolve_file(p, "jcl/J.jcl", "r")


HDR = ("//JX JOB", "//LIBS JCLLIB ORDER=(T.PLIB)")
PLAIN = J("//PP PROC", "//ST1 EXEC PGM=PGM1", "//IN DD DSN=BASE.IN,DISP=SHR",
          "//OUT DD DSN=BASE.OUT,DISP=OLD,DCB=(LRECL=80)", "// PEND")


# Each case: members, job text, name of the call that must become UNSUPPORTED.
Case = tuple[dict[str, str], str, str]


def _depth() -> Case:
    m = {f"Q{i}.prc": J(f"//Q{i} PROC", f"//X EXEC PROC=Q{i + 1}", "// PEND") for i in range(16)}
    m["Q16.prc"] = J("//Q16 PROC", "//Z EXEC PGM=END", "// PEND")
    return m, J(*HDR, "//C EXEC PROC=Q0"), "Q15"


CASES: dict[str, Callable[[], Case]] = {
    "U-EXEC-OVERRIDE": lambda: ({"PP.prc": PLAIN}, J(*HDR, "//C EXEC PP,COND=(0,NE)"), "PP"),
    "U-OVR-POSITIONAL": lambda: ({"PP.prc": PLAIN}, J(*HDR, "//C EXEC PP", "//ST1.IN DD DUMMY"),
                                 "PP"),
    "U-OVR-BASE-POSITIONAL": lambda: (
        {"PD.prc": J("//PD PROC", "//ST1 EXEC PGM=PGM1", "//IN DD DUMMY", "// PEND")},
        J(*HDR, "//C EXEC PD", "//ST1.IN DD DSN=REAL.IN,DISP=SHR"), "PD"),
    "U-OVR-DCB-MERGE": lambda: ({"PP.prc": PLAIN},
                                J(*HDR, "//C EXEC PP", "//ST1.OUT DD DCB=(RECFM=FB)"), "PP"),
    "U-OVR-MUTEX": lambda: ({"PP.prc": PLAIN}, J(*HDR, "//C EXEC PP", "//ST1.IN DD SYSOUT=A"),
                            "PP"),
    "U-OVR-CONCAT": lambda: ({"PP.prc": PLAIN},
                             J(*HDR, "//C EXEC PP", "//ST1.IN DD DSN=A,DISP=SHR",
                               "//       DD DSN=B,DISP=SHR"), "PP"),
    "U-OVR-NESTED-STEP": lambda: (
        {"PP.prc": PLAIN, "PO.prc": J("//PO PROC", "//INNER EXEC PROC=PP", "// PEND")},
        J(*HDR, "//C EXEC PO", "//INNER.IN DD DSN=X,DISP=SHR"), "PO"),
    "U-DEPTH": _depth,
    "U-PROC-SET": lambda: (
        {"PS.prc": J("//PS PROC", "// SET V=INNER", "//ST1 EXEC PGM=PGM1,PARM=&V", "// PEND")},
        J(*HDR, "//C EXEC PS"), "PS"),
    "U-NESTED-INSTREAM": lambda: (
        {}, J("//JX JOB", "//INS PROC", "//A EXEC PGM=IEFBR14", "// PEND", "//OUTR PROC",
              "//B EXEC INS", "// PEND", "//C EXEC OUTR"), "INS"),
    "U-SYMBOLIC-PROC": lambda: ({"PP.prc": PLAIN},
                                J(*HDR, "// SET WHICH=PP", "//C EXEC PROC=&WHICH"), "&WHICH"),
    "U-SYMBOLIC-JCLLIB": lambda: ({"PP.prc": PLAIN},
                                  J("//JX JOB", "// SET L=T.PLIB", "//LIBS JCLLIB ORDER=(&L)",
                                    "//C EXEC PP"), "PP"),
}


def test_every_registered_form_has_a_case() -> None:
    assert set(CASES) == set(UNSUPPORTED_FORMS)


@pytest.mark.parametrize("form", sorted(CASES))
def test_unsupported_form_is_detected_and_not_resolved(tmp_path: Path, form: str) -> None:
    members, text, call_name = CASES[form]()
    res = run(tmp_path, members, text)
    assert form in {u.form for u in res.unsupported}
    w004 = [d for d in res.diagnostics if d.code == "RES-W004"]
    assert any(f"[{form}]" in d.message for d in w004)
    target = [c for c in res.calls if c.requested == call_name]
    assert target and all(c.status == "UNSUPPORTED" for c in target)
    ids = {c.id for c in target}
    assert {u.call_id for u in res.unsupported if u.form == form} <= ids
    # no effective step comes from inside an UNSUPPORTED call
    for st in [s for j in res.jobs for s in j.steps]:
        assert not (ids & set(st.call_chain)), f"step {st.name} expanded from {st.call_chain}"
    assert "UNSUPPORTED_FORMS_PRESENT" in res.limitations


def test_supported_call_has_no_unsupported_record(tmp_path: Path) -> None:
    res = run(tmp_path, {"PP.prc": PLAIN},
              J(*HDR, "//C EXEC PP", "//ST1.IN DD DSN=REAL.IN,DISP=OLD"))
    assert res.unsupported == () and [c.status for c in res.calls] == ["RESOLVED"]
    assert "UNSUPPORTED_FORMS_PRESENT" not in res.limitations


def test_standalone_member_with_body_set_is_not_resolved(tmp_path: Path) -> None:
    ctx = ctx_with(tmp_path, {"PS.prc": J("//PS PROC", "// SET V=INNER",
                                          "//ST1 EXEC PGM=PGM1,PARM=&V", "// PEND")})
    res = Resolver(ctx).resolve_member(tmp_path / "root" / "plib" / "PS.prc", "plib/PS.prc", "r",
                                       None)
    assert [(u.form, u.call_id) for u in res.unsupported] == [("U-PROC-SET", None)]
    assert [s.status for s in res.steps] == ["UNSUPPORTED"]
    assert res.counts()["program_steps"] == 0


# ----------------------------------------------------------- forms fixed instead (F03/F05/F07)
def test_f03_set_in_uncalled_instream_proc_does_not_leak(tmp_path: Path) -> None:
    res = run(tmp_path, {}, J("//JX JOB", "//UNC PROC", "// SET V=LEAKED", "//A EXEC PGM=IEFBR14",
                              "// PEND", "//RUNIT EXEC PGM=IEFBR14,PARM=&V"))
    (st,) = res.jobs[0].steps
    parm = next(p for p in st.exec_params if p.name == "PARM")
    assert parm.value == "&V"
    assert [u.status for u in parm.substitutions] == ["UNDEFINED"]
    assert not [d for d in res.symbols_defined if d.name == "V"]


def test_f05_duplicate_exec_symbol_first_value(tmp_path: Path) -> None:
    pv = J("//PV PROC", "//ST1 EXEC PGM=PGM1,PARM=&A", "// PEND")
    res = run(tmp_path, {"PV.prc": pv}, J(*HDR, "//C EXEC PV,A=ONE,A=TWO"))
    assert res.jobs[0].steps[0].exec_params[0].value == "ONE"
    assert ("RES-I003", 3) in {(d.code, d.line) for d in res.diagnostics}


def test_f05_duplicate_proc_default_first_value_and_exec_still_overrides(tmp_path: Path) -> None:
    pv = J("//PV PROC A=DEF1,A=DEF2", "//ST1 EXEC PGM=PGM1,PARM=&A", "// PEND")
    res = run(tmp_path, {"PV.prc": pv}, J(*HDR, "//C EXEC PV"))
    assert res.jobs[0].steps[0].exec_params[0].value == "DEF1"
    res2 = run(tmp_path, {"PV.prc": pv}, J(*HDR, "//C EXEC PV,A=CALLER"))
    assert res2.jobs[0].steps[0].exec_params[0].value == "CALLER"


def test_f07_program_symbol_keeps_use_definition_edge(tmp_path: Path) -> None:
    res = run(tmp_path, {}, J("//JX JOB", "// SET PG=IEFBR14", "//S1 EXEC PGM=&PG"))
    (st,) = res.jobs[0].steps
    assert (st.program, st.program_raw) == ("IEFBR14", "&PG")
    (u,) = st.program_substitutions
    assert (u.name, u.status, u.value, u.defined_by.line, u.used_at.line) == (
        "PG", "RESOLVED", "IEFBR14", 2, 3)


def test_f07_literal_program_has_no_substitutions(tmp_path: Path) -> None:
    (st,) = run(tmp_path, {}, J("//JX JOB", "//S1 EXEC PGM=IEFBR14")).jobs[0].steps
    assert (st.program, st.program_raw, st.program_substitutions) == ("IEFBR14", "IEFBR14", ())

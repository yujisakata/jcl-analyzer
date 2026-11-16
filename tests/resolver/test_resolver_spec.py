"""CD-4 PROC Resolver: tests derived from IBM SA23-1385-70 rules, written before the implementation.

Synthetic libraries under tmp_path; no CardDemo file is needed. Same-author limitation applies
(independent verification by Codex is required before acceptance).
Rules: JCL-PROC-002/003/006/007, JCL-EXEC-003, JCL-SYM-001..004, JCL-SYN-004, POL-002/003/005.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jclprof.context.config import DatasetMapping
from jclprof.parser import parse_file
from jclprof.resolver import LibraryContext, Resolver


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def lib(tmp: Path, members: dict[str, str], dsn: str = "MY.PROCLIB", folder: str = "proc",
        suffixes: tuple[str, ...] = (".prc",), aliases: dict[str, str] | None = None,
        mapped: bool = True) -> LibraryContext:
    d = tmp / "root" / folder
    d.mkdir(parents=True, exist_ok=True)
    for name, text in members.items():
        (d / name).write_text(text, encoding="utf-8")
    maps = [DatasetMapping(dsn, "r", folder, "PDS", suffixes, aliases or {})] if mapped else []
    return LibraryContext(tuple(maps), {"r": tmp / "root"}, "TEST", "synthetic")


def job(tmp: Path, text: str, name: str = "JOB1.jcl") -> Path:
    p = tmp / "root" / "jcl" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


PROC_A = J("//PA     PROC", "//PS1    EXEC PGM=IDCAMS", "//SYSPRINT DD SYSOUT=*",
           "//FILEIN  DD DISP=SHR,", "//        DSN=NULLFILE", "//SYSIN   DD DISP=SHR,",
           "//        DSN=&CNTLLIB(REPROCT)", "// PEND")


def resolve(tmp: Path, ctx: LibraryContext, text: str) -> Any:
    return Resolver(ctx).resolve_file(job(tmp, text), "jcl/JOB1.jcl", "r")


def calls(res: Any) -> list[Any]:
    return list(res.calls)


def step(res: Any, i: int = 0) -> Any:
    return res.jobs[0].steps[i]


def dd(st: Any, name: str) -> Any:
    return next(d for d in st.dds if d.ddname == name)


def kw(d: Any) -> dict[str, Any]:
    return {p.name: p.value for p in d.params}


CALLER = J("//J      JOB", "//LIBS   JCLLIB ORDER=('MY.PROCLIB')", "//S1     EXEC PROC=PA,",
           "// CNTLLIB=MY.CNTL", "//PS1.FILEIN DD DISP=OLD,", "//        DSN=REAL.INPUT",
           "//PS1.NEWDD  DD SYSOUT=A")


# ---------------------------------------------------------------- library search (JCL-PROC-002/003)
def test_resolved_by_member_name_with_search_evidence(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"PA.prc": PROC_A})
    res = resolve(tmp_path, ctx, CALLER)
    (c,) = calls(res)
    assert (c.requested, c.status, c.member_path) == ("PA", "RESOLVED", "proc/PA.prc")
    assert [(s.kind, s.library, s.result) for s in c.search] == [
        ("JCLLIB", "MY.PROCLIB", "FOUND")]
    assert c.member_sha256 is not None and c.label == "PA" and c.label_matches_member
    assert c.basis == "TEST"


def test_unmapped_library_is_environment_gap_not_guessed(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"PA.prc": PROC_A}, mapped=False)
    res = resolve(tmp_path, ctx, CALLER)
    (c,) = calls(res)
    assert c.status == "ENVIRONMENT_GAP" and c.member_path is None
    assert [(s.library, s.result) for s in c.search] == [("MY.PROCLIB", "UNMAPPED")]
    assert {(d.code, d.line) for d in res.diagnostics} >= {("RES-W002", 2), ("RES-W005", 3)}
    st = step(res)
    assert st.status == "UNRESOLVED_CALL" and st.program is None
    assert [o.statement_id for o in st.pending_overrides] == ["S00005", "S00007"]


def test_member_not_found_and_no_system_proclib(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"OTHER.prc": PROC_A})
    (c,) = calls(resolve(tmp_path, ctx, CALLER))
    assert c.status == "ENVIRONMENT_GAP"  # system PROCLIB unknown: absence cannot be concluded
    assert [(s.kind, s.result) for s in c.search] == [("JCLLIB", "NOT_FOUND"),
                                                       ("SYSTEM", "NOT_CONFIGURED")]


def test_ambiguous_candidates_not_resolved(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"PA.prc": PROC_A, "PA.jcl": PROC_A}, suffixes=(".prc", ".jcl"))
    res = resolve(tmp_path, ctx, CALLER)
    (c,) = calls(res)
    assert c.status == "AMBIGUOUS"
    assert sorted(c.search[0].candidates) == ["proc/PA.jcl", "proc/PA.prc"]
    assert "RES-W003" in {d.code for d in res.diagnostics}


def test_label_is_not_member_name(tmp_path: Path) -> None:  # JCL-PROC-002, POL-004, ADR-011
    other = PROC_A.replace("//PA     PROC", "//PA     PROC", 1)
    ctx = lib(tmp_path, {"TRANREPT.prc": other})  # label PA, member TRANREPT
    (c,) = calls(resolve(tmp_path, ctx, CALLER))
    assert c.status == "ENVIRONMENT_GAP"  # PA is not a member; the label does not count
    ctx2 = lib(tmp_path, {"TRANREPT.prc": other})
    res = resolve(tmp_path, ctx2, CALLER.replace("PROC=PA", "PROC=TRANREPT"))
    (c2,) = calls(res)
    assert (c2.status, c2.label, c2.label_matches_member) == ("RESOLVED", "PA", False)
    assert "RES-I001" in {d.code for d in res.diagnostics}


def test_alias_resolution_is_explicit(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"REALNAME.prc": PROC_A}, aliases={"PA": "REALNAME"})
    (c,) = calls(resolve(tmp_path, ctx, CALLER))
    assert (c.status, c.member_path, c.alias_of) == ("RESOLVED", "proc/REALNAME.prc", "REALNAME")


def test_jcllib_order_first_library_wins_and_unmapped_earlier_blocks(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"PA.prc": PROC_A})
    text = CALLER.replace("ORDER=('MY.PROCLIB')", "ORDER=(OTHER.LIB,'MY.PROCLIB')")
    (c,) = calls(resolve(tmp_path, ctx, text))
    # OTHER.LIB is searched first but unmapped: whether it holds PA is unknown
    assert c.status == "ENVIRONMENT_GAP"
    assert [(s.library, s.result) for s in c.search] == [("OTHER.LIB", "UNMAPPED"),
                                                         ("MY.PROCLIB", "FOUND")]


# ---------------------------------------------------------------- expansion and overrides
def test_expansion_and_dd_overrides(tmp_path: Path) -> None:  # JCL-PROC-006
    res = resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), CALLER)
    st = step(res)
    assert (st.status, st.name, st.program, st.call_path) == ("RESOLVED", "PS1", "IDCAMS",
                                                              ("S1", "PS1"))
    assert [d.ddname for d in st.dds] == ["SYSPRINT", "FILEIN", "SYSIN", "NEWDD"]
    fin = dd(st, "FILEIN")
    assert kw(fin) == {"DISP": "OLD", "DSN": "REAL.INPUT"}
    assert [(o.param, o.action, o.original, o.applied) for o in fin.overrides] == [
        ("DISP", "REPLACE", "SHR", "OLD"), ("DSN", "REPLACE", "NULLFILE", "REAL.INPUT")]
    assert fin.origin.file == "proc/PA.prc" and fin.origin.line == 4
    assert [o.source.line for o in fin.overrides] == [5, 6]
    new = dd(st, "NEWDD")
    assert new.added_by_override and new.origin.file == "jcl/JOB1.jcl" and new.origin.line == 7


def test_nullify_and_add(tmp_path: Path) -> None:  # JCL-PROC-006 (nullify by no value)
    text = CALLER.replace("//PS1.FILEIN DD DISP=OLD,", "//PS1.FILEIN DD DISP=,UNIT=SYSDA,")
    fin = dd(step(resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)), "FILEIN")
    assert kw(fin) == {"DSN": "REAL.INPUT", "UNIT": "SYSDA"}
    assert [(o.param, o.action) for o in fin.overrides] == [("DISP", "NULLIFY"), ("UNIT", "ADD"),
                                                            ("DSN", "REPLACE")]


def test_unqualified_override_applies_to_first_step(tmp_path: Path) -> None:  # JCL-PROC-006
    text = CALLER.replace("//PS1.FILEIN DD", "//FILEIN DD")
    fin = dd(step(resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)), "FILEIN")
    assert kw(fin)["DSN"] == "REAL.INPUT"


def test_override_of_missing_step(tmp_path: Path) -> None:
    text = CALLER.replace("//PS1.FILEIN DD", "//NOSTEP.FILEIN DD")
    res = resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)
    assert ("RES-E005", 5) in {(d.code, d.line) for d in res.diagnostics}


def test_unsupported_override_construct_is_flagged_not_applied(tmp_path: Path) -> None:
    text = CALLER.replace("//PS1.FILEIN DD DISP=OLD,", "//PS1.FILEIN DD DUMMY,")
    res = resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)
    assert ("RES-W004", 5) in {(d.code, d.line) for d in res.diagnostics}
    fin = dd(step(res), "FILEIN")
    assert kw(fin)["DSN"] == "NULLFILE" and fin.unapplied_overrides


def test_exec_keyword_override_on_call_is_flagged(tmp_path: Path) -> None:  # JCL-EXEC-003
    text = CALLER.replace("// CNTLLIB=MY.CNTL", "// CNTLLIB=MY.CNTL,REGION.PS1=0M")
    res = resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)
    assert ("RES-W004", 3) in {(d.code, d.line) for d in res.diagnostics}


# ---------------------------------------------------------------- symbols (JCL-SYM-*, JCL-EXEC-003)
def test_call_symbolic_parameter_substituted_with_evidence(tmp_path: Path) -> None:
    sysin = dd(step(resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), CALLER)), "SYSIN")
    dsn = next(p for p in sysin.params if p.name == "DSN")
    assert (dsn.raw, dsn.value) == ("&CNTLLIB(REPROCT)", "MY.CNTL(REPROCT)")
    (u,) = dsn.substitutions
    assert (u.name, u.status, u.value, u.defined_by.line) == ("CNTLLIB", "RESOLVED", "MY.CNTL", 4)


def test_set_chain_with_double_period_and_precedence(tmp_path: Path) -> None:  # JCL-SYM-002/004
    text = J("//J JOB", "// SET CODER=AWS", "// SET LBNM=&CODER..M2.CARDDEMO",
             "// SET CNTLLIB=FROM.SET", "//LIBS JCLLIB ORDER=('MY.PROCLIB')",
             "//S0 EXEC PGM=X", "//D DD DSN=&LBNM..CNTL(DB2FREE)", "//S1 EXEC PROC=PA,",
             "// CNTLLIB=FROM.EXEC")
    res = resolve(tmp_path, lib(tmp_path, {"PA.prc": PROC_A}), text)
    d0 = res.jobs[0].steps[0].dds[0]
    assert d0.params[0].value == "AWS.M2.CARDDEMO.CNTL(DB2FREE)"
    sets = [s for s in res.symbols_defined if s.scope == "SET"]
    assert [(s.name, s.value) for s in sets] == [("CODER", "AWS"), ("LBNM", "AWS.M2.CARDDEMO"),
                                                 ("CNTLLIB", "FROM.SET")]
    assert [u.name for u in sets[1].derivation] == ["CODER"]  # derivation evidence kept
    execs = [s for s in res.symbols_defined if s.scope == "EXEC"]
    assert [(s.name, s.value, s.defined_by.line) for s in execs] == [("CNTLLIB", "FROM.EXEC", 9)]
    sysin = dd(res.jobs[0].steps[1], "SYSIN")
    assert next(p for p in sysin.params if p.name == "DSN").value == "FROM.EXEC(REPROCT)"


def test_set_scope_is_positional(tmp_path: Path) -> None:  # JCL-SET-001 (before intended use)
    text = J("//J JOB", "//S0 EXEC PGM=X", "//D DD DSN=&HLQ..A", "// SET HLQ=LATE",
             "//S1 EXEC PGM=Y", "//E DD DSN=&HLQ..B")
    res = resolve(tmp_path, lib(tmp_path, {}), text)
    a, b = res.jobs[0].steps
    assert a.dds[0].params[0].value == "&HLQ..A"  # undefined at that point: literal, not empty
    assert b.dds[0].params[0].value == "LATE.B"
    assert ("RES-W001", 3) in {(d.code, d.line) for d in res.diagnostics}


def test_system_symbol_and_undefined_symbol(tmp_path: Path) -> None:  # CA-06
    res = resolve(tmp_path, lib(tmp_path, {}), J("//J JOB CLASS=A,NOTIFY=&SYSUID",
                                                  "//K JOB NOTIFY=&SYUID", "//S EXEC PGM=X"))
    uses = {(u.name, u.status) for j in res.jobs for u in j.job_symbol_uses}
    assert uses == {("SYSUID", "ENVIRONMENT_DEPENDENT"), ("SYUID", "UNDEFINED")}
    assert {"RES-I002", "RES-W001"} <= {d.code for d in res.diagnostics}


def test_quoted_values_substituted_only_for_listed_parameters(tmp_path: Path) -> None:
    text = J("//J JOB", "// SET A=X", "//S EXEC PGM=P,PARM='&A'", "//D DD DSN='&A..Y'")
    st = step(resolve(tmp_path, lib(tmp_path, {}), text))
    assert st.exec_params[0].value == {"q": "X"}  # PARM: listed (JCL-SYM-003)
    assert st.dds[0].params[0].value == {"q": "&A..Y"}  # not listed: literal


# ---------------------------------------------------------------- nesting
NESTED = J("//PB     PROC", "//PB1    EXEC PROC=PA,", "// CNTLLIB=FROM.PB",
           "//PS1.FILEIN DD DSN=FROM.PB.IN", "//PB2    EXEC PGM=SORT", "//SORTIN DD DSN=S",
           "//SORTOUT DD DCB=*.SORTIN", "// PEND")


def test_procedure_calling_procedure(tmp_path: Path) -> None:  # JCL-PROC-007
    ctx = lib(tmp_path, {"PA.prc": PROC_A, "PB.prc": NESTED})
    text = J("//J JOB", "//LIBS JCLLIB ORDER=('MY.PROCLIB')", "//S1 EXEC PROC=PB")
    res = resolve(tmp_path, ctx, text)
    steps = res.jobs[0].steps
    assert [(s.name, s.call_path, s.program) for s in steps] == [
        ("PS1", ("S1", "PB1", "PS1"), "IDCAMS"), ("PB2", ("S1", "PB2"), "SORT")]
    assert kw(dd(steps[0], "FILEIN"))["DSN"] == "FROM.PB.IN"
    sysin = dd(steps[0], "SYSIN")
    assert next(p for p in sysin.params if p.name == "DSN").value == "FROM.PB(REPROCT)"
    assert [c.requested for c in res.calls] == ["PB", "PA"]


def test_nested_symbol_inherited(tmp_path: Path) -> None:  # JCL-SYM-004 rule 5
    pb = NESTED.replace("//PB1    EXEC PROC=PA,\n// CNTLLIB=FROM.PB\n", "//PB1    EXEC PROC=PA\n")
    ctx = lib(tmp_path, {"PA.prc": PROC_A, "PB.prc": pb})
    text = J("//J JOB", "//LIBS JCLLIB ORDER=('MY.PROCLIB')", "//S1 EXEC PROC=PB,",
             "// CNTLLIB=FROM.JOB")
    sysin = dd(resolve(tmp_path, ctx, text).jobs[0].steps[0], "SYSIN")
    assert next(p for p in sysin.params if p.name == "DSN").value == "FROM.JOB(REPROCT)"


def test_cycle_detected(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"CA.prc": J("//CA PROC", "//X EXEC PROC=CB", "// PEND"),
                         "CB.prc": J("//CB PROC", "//Y EXEC PROC=CA", "// PEND")})
    res = resolve(tmp_path, ctx,
                  J("//J JOB", "//L JCLLIB ORDER=('MY.PROCLIB')", "//S EXEC PROC=CA"))
    assert "RES-E003" in {d.code for d in res.diagnostics}
    assert res.jobs[0].steps[0].status == "UNRESOLVED_CALL"


def test_dcb_backward_reference_both_ends(tmp_path: Path) -> None:  # JCL-SYN-004, CA-15
    ctx = lib(tmp_path, {"PA.prc": PROC_A, "PB.prc": NESTED})
    res = resolve(tmp_path, ctx, J("//J JOB", "//LIBS JCLLIB ORDER=('MY.PROCLIB')",
                                   "//S1 EXEC PROC=PB"))
    out = dd(res.jobs[0].steps[1], "SORTOUT")
    (ref,) = out.backrefs
    assert (ref.param, ref.text, ref.status) == ("DCB", "*.SORTIN", "RESOLVED")
    assert ref.target_dd_id == dd(res.jobs[0].steps[1], "SORTIN").id


# ---------------------------------------------------------------- source AST is never changed
def test_source_ast_unchanged(tmp_path: Path) -> None:
    ctx = lib(tmp_path, {"PA.prc": PROC_A})
    p = job(tmp_path, CALLER)
    parsed = parse_file(p, encoding="utf-8")
    before = parsed.to_dict()
    res = Resolver(ctx).resolve_parsed(parsed, "jcl/JOB1.jcl", "r")
    assert parsed.to_dict() == before
    assert res.source is parsed
    src_step = parsed.jobs[0].steps[0]
    assert [d.ddname for d in src_step.dds] == ["FILEIN", "NEWDD"]  # still children of the call


def test_member_with_explicit_context_only(tmp_path: Path) -> None:  # CA-04 last paragraph
    ctx = lib(tmp_path, {"PA.prc": PROC_A, "PB.prc": NESTED})
    r = Resolver(ctx)
    p = tmp_path / "root" / "proc" / "PB.prc"
    alone = r.resolve_member(p, "proc/PB.prc", "r", context_libraries=None)
    assert alone.calls[0].status == "NO_LIBRARY_CONTEXT"
    ctxd = r.resolve_member(p, "proc/PB.prc", "r", context_libraries=("MY.PROCLIB",))
    assert [s.name for s in ctxd.steps] == ["PS1", "PB2"]


@pytest.mark.parametrize("n", [16])
def test_nesting_depth_limit(tmp_path: Path, n: int) -> None:  # JCL-PROC-007: 15 levels
    members = {f"P{i}.prc": J(f"//P{i} PROC", f"//X{i} EXEC PROC=P{i + 1}", "// PEND")
               for i in range(n)}
    members[f"P{n}.prc"] = J(f"//P{n} PROC", "//Z EXEC PGM=END", "// PEND")
    res = resolve(tmp_path, lib(tmp_path, members),
                  J("//J JOB", "//L JCLLIB ORDER=('MY.PROCLIB')", "//S EXEC PROC=P0"))
    assert "RES-W004" in {d.code for d in res.diagnostics}

"""CD-4 on CardDemo: PROC calls (CA-04), overrides and counts (CA-05), symbols (CA-06),
provenance (CA-15), source AST immutability and source-structure regression.

Expected values were written by hand from the original files and the contract (section 1.5,
4.3), never from Resolver output. The contract context (config/contexts/cd4-contract-context.yaml)
is UNCONFIRMED; results under it are conditional (CA-05) and labelled with that basis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import PROJECT_ROOT, snapshot
from jclprof.context.config import load_config
from jclprof.parser import parse_file
from jclprof.resolver import EffectiveResult, LibraryContext, Resolver, load_library_context

pytestmark = pytest.mark.corpus

ORACLE = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                        .read_text(encoding="utf-8"))
FILES = sorted(ORACLE["jcl_family_files"])
JOB_FILES = [f for f in FILES if not f.lower().endswith(".prc")]
CALLERS = {"jcl/PRTCATBL.jcl": 29, "jcl/TRANBKP.jcl": 23, "jcl/TRANREPT.jcl": 23}
# (caller, FILEIN line, FILEOUT line, input DSN, output DSN, LRECL, CNTLLIB line)
OVERRIDES = [
    ("jcl/PRTCATBL.jcl", 32, 35, "AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS",
     "AWS.M2.CARDDEMO.TCATBALF.BKUP(+1)", "50", 30),
    ("jcl/TRANBKP.jcl", 26, 29, "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS",
     "AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)", "350", 24),
    ("jcl/TRANREPT.jcl", 26, 29, "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS",
     "AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)", "350", 24),
    ("proc/TRANREPT.prc", 24, 27, "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS",
     "AWS.M2.CARDDEMO.TRANSACT.BKUP(+1)", "350", 22),
]
REPROC_SHA = ORACLE["jcl_family_files"]["proc/REPROC.prc"]["sha256"]


@pytest.fixture(scope="module")
def root() -> Path:
    cfg = load_config(PROJECT_ROOT / "config" / "profiler.yaml")
    r = cfg.roots[0].path
    if not r.is_dir():
        pytest.skip("CardDemo corpus not available")
    return r


@pytest.fixture(scope="module")
def official(root: Path) -> LibraryContext:
    return LibraryContext.from_config(load_config(PROJECT_ROOT / "config" / "profiler.yaml"))


@pytest.fixture(scope="module")
def contract(root: Path) -> LibraryContext:
    return load_library_context(PROJECT_ROOT / "config/contexts/cd4-contract-context.yaml",
                                {"carddemo": root})


def run_all(root: Path, ctx: LibraryContext) -> dict[str, EffectiveResult]:
    r = Resolver(ctx)
    out = {f: r.resolve_file(root / f, f, "carddemo") for f in JOB_FILES}
    out["proc/TRANREPT.prc"] = r.resolve_member(root / "proc/TRANREPT.prc", "proc/TRANREPT.prc",
                                                "carddemo", ("AWS.M2.CARDDEMO.PROC",))
    return out


def codes(res: EffectiveResult) -> set[tuple[str, str, int | None]]:
    return {(d.code, d.file, d.line) for d in res.diagnostics}


# ---------------------------------------------------------------- CA-04: official config
def test_official_config_keeps_all_calls_unresolved(root: Path, official: LibraryContext) -> None:
    res = run_all(root, official)
    calls = [(f, c) for f, r in res.items() for c in r.calls]
    assert sorted((f, c.call.line) for f, c in calls if f in CALLERS) == sorted(CALLERS.items())
    for f, c in calls:
        if f not in CALLERS:
            continue
        assert (c.requested, c.status, c.member_path) == ("REPROC", "ENVIRONMENT_GAP", None)
        assert [(s.kind, s.library, s.result) for s in c.search] == [
            ("JCLLIB", "AWS.M2.CARDDEMO.PROC", "UNMAPPED")]
        assert c.search[0].evidence is not None and c.search[0].evidence.line == 19
        assert ("RES-W002", f, 19) in codes(res[f]) and ("RES-W005", f, CALLERS[f]) in codes(res[f])
    totals = [res[f].counts() for f in JOB_FILES]
    assert sum(t["program_steps"] for t in totals) == 116
    assert sum(t["unresolved_call_steps"] for t in totals) == 3
    assert sum(t["dds"] for t in totals) == 480 - 6  # override DDs stay pending, not applied
    for f in CALLERS:
        (ph,) = [s for j in res[f].jobs for s in j.steps if s.status == "UNRESOLVED_CALL"]
        assert len(ph.pending_overrides) == 2


# ---------------------------------------------------------------- CA-04/05: contract context
def test_contract_context_resolves_four_calls(root: Path, contract: LibraryContext) -> None:
    res = run_all(root, contract)
    calls = [(f, c) for f, r in res.items() for c in r.calls]
    assert len(calls) == 4
    for f, c in calls:
        assert (c.requested, c.status, c.member_path, c.member_sha256) == (
            "REPROC", "RESOLVED", "proc/REPROC.prc", REPROC_SHA), f
        assert (c.label, c.label_matches_member, c.basis) == (
            "REPROC", True, "UNCONFIRMED_CONTRACT_CONTEXT")
        expected_kind = "CONTEXT" if f.endswith(".prc") else "JCLLIB"
        assert [(s.kind, s.result) for s in c.search] == [(expected_kind, "FOUND")]
    # TRANREPT member: label REPROC differs from member TRANREPT (kept apart, CA-04 / ADR-011)
    assert ("RES-I001", "proc/TRANREPT.prc", 1) in codes(res["proc/TRANREPT.prc"])


def test_contract_context_counts(root: Path, contract: LibraryContext) -> None:  # CA-05
    res = run_all(root, contract)
    totals = [res[f].counts() for f in JOB_FILES]
    assert sum(t["program_steps"] for t in totals) == 119
    assert sum(t["unresolved_call_steps"] for t in totals) == 0
    assert sum(t["dds"] for t in totals) == 486
    assert sum(t["job_level_dds"] for t in totals) == 3
    tr = res["proc/TRANREPT.prc"]
    assert [s.name for s in tr.steps] == ["PRC001", "STEP05R", "STEP10R"]
    assert sum(len(s.dds) for s in tr.steps) == 18


def _p(d: Any) -> dict[str, Any]:
    return {p.name: p.value for p in d.params}


@pytest.mark.parametrize("caller,fin_line,fout_line,dsn_in,dsn_out,lrecl,cntl_line", OVERRIDES)
def test_eight_overrides(root: Path, contract: LibraryContext, caller: str, fin_line: int,
                         fout_line: int, dsn_in: str, dsn_out: str, lrecl: str,
                         cntl_line: int) -> None:  # CA-05, CA-15
    res = run_all(root, contract)[caller]
    steps = [s for j in res.jobs for s in j.steps] + list(res.steps)
    (prc,) = [s for s in steps if s.name == "PRC001"]
    assert prc.program == "IDCAMS" and prc.exec_origin.file == "proc/REPROC.prc"
    assert prc.exec_origin.line == 21 and prc.call_path[-1] == "PRC001"
    assert [d.ddname for d in prc.dds] == ["SYSPRINT", "FILEIN", "FILEOUT", "SYSIN"]
    fin, fout, sysin = prc.dds[1], prc.dds[2], prc.dds[3]
    assert _p(fin) == {"DISP": "SHR", "DSN": dsn_in}
    assert [(o.param, o.action, o.original, o.applied, o.source.file, o.source.line)
            for o in fin.overrides] == [
        ("DISP", "REPLACE", "SHR", "SHR", caller, fin_line),
        ("DSN", "REPLACE", "NULLFILE", dsn_in, caller, fin_line + 1)]
    assert (fin.origin.file, fin.origin.line) == ("proc/REPROC.prc", 23)
    assert fin.override_statement is not None and fin.override_statement.line == fin_line
    assert [p.name for p in fout.params] == ["DISP", "DSN", "UNIT", "DCB", "SPACE"]
    assert _p(fout) == {"DISP": ["NEW", "CATLG", "DELETE"], "DSN": dsn_out, "UNIT": "SYSDA",
                        "DCB": [{"kw": ["LRECL", lrecl]}, {"kw": ["RECFM", "FB"]},
                                {"kw": ["BLKSIZE", "0"]}],
                        "SPACE": ["CYL", ["1", "1"], "RLSE"]}
    assert [(o.param, o.action, o.source.line) for o in fout.overrides] == [
        ("DISP", "REPLACE", fout_line), ("UNIT", "ADD", fout_line + 1),
        ("DCB", "ADD", fout_line + 2), ("SPACE", "ADD", fout_line + 3),
        ("DSN", "REPLACE", fout_line + 4)]
    assert (fout.origin.file, fout.origin.line) == ("proc/REPROC.prc", 25)
    dsn = next(p for p in sysin.params if p.name == "DSN")
    assert (dsn.raw, dsn.value) == ("&CNTLLIB(REPROCT)", "AWS.M2.CARDDEMO.CNTL(REPROCT)")
    (u,) = dsn.substitutions
    assert u.defined_by is not None
    assert (u.name, u.status, u.defined_by.file, u.defined_by.line) == (
        "CNTLLIB", "RESOLVED", caller, cntl_line)
    assert (dsn.source.file, dsn.source.line) == ("proc/REPROC.prc", 28)
    assert sysin.overrides == () and prc.dds[0].overrides == ()


# ---------------------------------------------------------------- CA-06: symbols
def test_set_symbols_and_environment_symbols(root: Path, official: LibraryContext) -> None:
    res = run_all(root, official)
    cre = res["app-transaction-type-db2/jcl/CREADB21.jcl"]
    sets = {(s.name, s.value) for s in cre.symbols_defined if s.scope == "SET"}
    assert sets == {("CODER", "AWS"), ("LBNM", "AWS.M2.CARDDEMO"), ("DB2S", "DAZ1")}
    lbnm = next(s for s in cre.symbols_defined if s.name == "LBNM")
    assert [u.name for u in lbnm.derivation] == ["CODER"] and lbnm.defined_by.line == 29
    job = cre.jobs[0]
    assert [_p(d).get("DSN") for d in job.job_level_dds] == [
        "OEM.DB2.DAZ1.SDSNLOAD", "OEM.DB2.DAZ1.SDSNLOAD", "CEE.SCEERUN"]
    freepln = next(s for s in job.steps if s.name == "FREEPLN")
    systsin = next(d for d in freepln.dds if d.ddname == "SYSTSIN")
    assert _p(systsin)["DSN"] == "AWS.M2.CARDDEMO.CNTL(DB2FREE)"
    tx = res["app-transaction-type-db2/jcl/TRANEXTR.jcl"]
    sysut1 = next(d for s in tx.jobs[0].steps for d in s.dds if d.origin.line == 34)
    assert _p(sysut1)["DSN"] == "AWS.M2.CARDDEMO.TRANTYPE.PS"
    uses = [(f, u) for f, r in res.items() for j in r.jobs for u in j.job_symbol_uses]
    assert sum(1 for _, u in uses if (u.name, u.status) == ("SYSUID", "ENVIRONMENT_DEPENDENT")) \
        == 45
    assert [(f, u.name, u.status) for f, u in uses if u.name != "SYSUID"] == [
        ("jcl/READCUST.jcl", "SYUID", "UNDEFINED")]
    assert ("RES-W001", "jcl/READCUST.jcl", 2) in codes(res["jcl/READCUST.jcl"])
    # CA-07: the SET HLQ in CBADMCDJ is not applied to the in-stream data record at line 45
    cb = res["jcl/CBADMCDJ.jcl"]
    assert not any(u.used_at.line == 45 for s in cb.jobs[0].steps for d in s.dds
                   for p in d.params for u in p.substitutions)


# ---------------------------------------------------------------- CA-15: DCB backward references
def test_dcb_backward_references(root: Path, contract: LibraryContext) -> None:
    res = run_all(root, contract)
    found = []
    for f, r in res.items():
        steps = [s for j in r.jobs for s in j.steps] + list(r.steps)
        for s in steps:
            for d in s.dds:
                for b in d.backrefs:
                    target = next(x for x in s.dds if x.id == b.target_dd_id)
                    found.append((f, b.source.line, b.text, b.status, target.ddname,
                                  target.concat_index))
    assert sorted(found) == [("jcl/COMBTRAN.jcl", 35, "*.SORTIN", "RESOLVED", "SORTIN", 0),
                             ("jcl/TRANREPT.jcl", 53, "*.SORTIN", "RESOLVED", "SORTIN", 0),
                             ("proc/TRANREPT.prc", 51, "*.SORTIN", "RESOLVED", "SORTIN", 0)]


# ---------------------------------------------------------------- immutability and regression
def test_source_ast_unchanged_and_source_counts(root: Path, contract: LibraryContext) -> None:
    before = snapshot(root)
    r = Resolver(contract)
    steps = dds = 0
    for f in FILES:
        kind = "proc_member" if f.endswith(".prc") else "job"
        parsed = parse_file(root / f, encoding="utf-8", input_kind=kind)
        frozen = parsed.to_dict()
        if kind == "job":
            r.resolve_parsed(parsed, f, "carddemo")
        assert parsed.to_dict() == frozen, f
        src_steps = list(parsed.procedure_steps) + [s for j in parsed.jobs for s in j.steps]
        steps += len(src_steps)
        dds += sum(len(s.dds) for s in src_steps) + sum(len(j.job_level_dds)
                                                         for j in parsed.jobs)
    assert (steps, dds) == (119 + 4, 500)  # contract 1.2 / 4.2: source structure unchanged
    assert snapshot(root) == before


def test_deterministic(root: Path, contract: LibraryContext) -> None:
    a = run_all(root, contract)
    b = run_all(root, contract)
    assert {f: r.to_dict() for f, r in a.items()} == {f: r.to_dict() for f, r in b.items()}

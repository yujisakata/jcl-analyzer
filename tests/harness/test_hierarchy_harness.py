"""R1 (audit A11): the Harness must REJECT wrong JOB/STEP/DD trees.

The decisive tests inject a wrong tree and require a failure; a correct tree passing is only the
baseline. Expected values come from tests/golden_pending (hand-written, review pending) and from
the IBM rules cited there. Same author as the Parser and the Harness (docs/reports/r1-harness.md).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import PROJECT_ROOT
from jclprof.harness.adapters import AdapterOutput
from jclprof.harness.comparator import compare_structure
from jclprof.harness.defects import RegistryError, explain, load_known_defects
from jclprof.harness.hierarchy import Violation, check_hierarchy
from jclprof.harness.loader import GoldenCase
from jclprof.harness.mutations import (
    CONSISTENT,
    REQUIRED,
    Mutant,
    all_mutants,
    detect,
)
from jclprof.harness.runner import run_case
from jclprof.harness.trace import check_trace
from jclprof.parser import parse_file, parse_text
from jclprof.parser.adapter import hierarchy_view

PENDING = PROJECT_ROOT / "tests" / "golden_pending"


def pending_case(test_id: str) -> tuple[Path, dict[str, Any]]:
    for f in (PENDING / "cases").glob("*.yaml"):
        for c in yaml.safe_load(f.read_text(encoding="utf-8"))["cases"]:
            if c["test_id"] == test_id:
                return PENDING / c["input_file"], c["expected_structure"]
    raise KeyError(test_id)


def view_of(r: Any) -> dict[str, Any]:
    v: dict[str, Any] = r.to_golden_view()
    v["hierarchy"] = hierarchy_view(r)
    return v


# ---------------------------------------------------------------- baseline (correct trees)
@pytest.mark.parametrize("tid", ["G-HIER-001", "G-HIER-002", "G-HIER-003", "G-HIER-005"])
def test_correct_tree_has_no_violation_and_matches_expectation(tid: str) -> None:
    path, expected = pending_case(tid)
    r = parse_file(path, encoding="utf-8")
    assert check_hierarchy(r) == []
    check_trace(r, path.read_text(encoding="utf-8"))
    assert compare_structure(expected, view_of(r)).ok


# ---------------------------------------------------------------- required mutations (M1-M7)
def mutants_of(op_name: str, tid: str = "G-HIER-001") -> tuple[Any, str, dict[str, Any],
                                                                  list[Mutant]]:
    path, expected = pending_case(tid)
    r = parse_file(path, encoding="utf-8")
    op = next(o for o in REQUIRED + CONSISTENT if o.__name__ == op_name)
    ms = list(op(r))
    assert ms, f"{op_name} is not applicable to {tid}"
    return r, path.read_text(encoding="utf-8"), expected, ms


@pytest.mark.parametrize("op_name,tid", [
    ("drop_all_jobs", "G-HIER-001"), ("drop_step", "G-HIER-001"),
    ("move_step_to_job", "G-HIER-001"), ("move_dd_to_step", "G-HIER-001"),
    ("change_exec_target", "G-HIER-001"), ("shift_data_boundary", "G-HIER-003"),
    ("shrink_job_span", "G-HIER-001")])
def test_required_mutation_is_rejected_by_invariants_and_by_golden(op_name: str, tid: str) -> None:
    r, text, expected, ms = mutants_of(op_name, tid)
    for m in ms:
        d = detect(m, r, text, expected)
        assert d["invariants"], (m.operator, m.target, "invariants missed")
        assert d["golden"], (m.operator, m.target, "golden comparison missed")


def test_consistent_target_change_is_rejected_by_trace_and_golden() -> None:
    r, text, expected, ms = mutants_of("change_exec_target_everywhere")
    for m in ms:
        d = detect(m, r, text, expected)
        assert d["trace"] and d["golden"], (m.target, d)


def test_consistent_boundary_change_is_rejected() -> None:
    r, text, expected, ms = mutants_of("shift_data_boundary_everywhere", "G-HIER-003")
    for m in ms:
        d = detect(m, r, text, expected)
        assert d["invariants"] and d["golden"], (m.target, d)


def test_dropping_all_jobs_is_reported_per_job_statement() -> None:
    path, _ = pending_case("G-HIER-001")
    r = parse_file(path, encoding="utf-8")
    v = check_hierarchy(replace(r, jobs=()))
    assert {x.node for x in v if x.code == "H-JOB-01"} == {"S00001", "S00010"}


def test_each_mutation_names_the_right_invariant() -> None:
    """Spot checks that the violation explains WHAT is wrong, not only that something is."""
    path, _ = pending_case("G-HIER-001")
    r = parse_file(path, encoding="utf-8")
    codes = {m.operator.split()[0]: {v.code for v in check_hierarchy(m.result)}
             for m in all_mutants(r, consistent=False)}
    assert "H-JOB-01" in codes["M1"]
    assert "H-STEP-01" in codes["M2"]
    assert "H-OWN-01" in codes["M3"]
    assert "H-OWN-01" in codes["M4"]
    assert "H-TGT-01" in codes["M5"]
    assert "H-SPAN-01" in codes["M7"]


# ---------------------------------------------------------------- comparator
def test_hierarchy_comparison_reports_paths() -> None:
    path, expected = pending_case("G-HIER-001")
    act = view_of(parse_file(path, encoding="utf-8"))
    act["hierarchy"]["jobs"][0]["steps"][1]["dds"][0]["name"] = "OUT2"
    del act["hierarchy"]["jobs"][1]["steps"][0]
    res = compare_structure(expected, act)
    paths = {(d.path, d.kind) for d in res.differences}
    assert ("hierarchy.jobs[0].steps[1].dds[0].name", "mismatch") in paths
    assert ("hierarchy.jobs[1].steps[0]", "missing") in paths


def test_hierarchy_not_expected_is_reported_unchecked() -> None:
    path, expected = pending_case("G-HIER-001")
    act = view_of(parse_file(path, encoding="utf-8"))
    flat = {k: v for k, v in expected.items() if k != "hierarchy"}
    res = compare_structure(flat, act)
    assert res.ok and "hierarchy" in res.unchecked


# ---------------------------------------------------------------- runner
class _Adapter:
    stage = "syntactic"

    def __init__(self, out: AdapterOutput) -> None:
        self.out = out

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        return self.out


def test_invariant_violation_fails_the_case_even_if_expectations_match() -> None:
    f = next((PENDING / "cases").glob("job_exec_dd.yaml"))
    raw = yaml.safe_load(f.read_text(encoding="utf-8"))["cases"][0]
    case = GoldenCase(raw, f, PENDING)
    r = parse_file(PENDING / raw["input_file"], encoding="utf-8")
    good = AdapterOutput(view_of(r), r.golden_diagnostics())
    assert run_case(case, {"syntactic": _Adapter(good)}, {}).status == "PASSED"
    bad = AdapterOutput(view_of(r), r.golden_diagnostics(),
                        [{"code": "H-JOB-01", "node": "S00001", "detail": "x"}])
    res = run_case(case, {"syntactic": _Adapter(bad)}, {})
    assert res.status == "FAILED"
    assert [d.path for d in res.differences] == ["invariant.H-JOB-01"]


# ---------------------------------------------------------------- trace (whole value text)
def test_trace_checks_whole_value_text() -> None:
    text = "//J JOB\n//S EXEC PGM=IEFBR14\n"
    r = parse_text(text)
    check_trace(r, text)
    s = r.statements[1]
    k = s.keywords[0]
    assert k.value is not None
    bad_kw = replace(k, value=replace(k.value, text="IEFBR15", value="IEFBR15"))
    bad = replace(r, statements=(r.statements[0], replace(s, keywords=(bad_kw,))))
    with pytest.raises(AssertionError):
        check_trace(bad, text)


def test_trace_accepts_apostrophe_continuation() -> None:  # JCL-CONT-003
    first = "//S EXEC PGM=X,PARM='" + "A" * (71 - 21)
    text = "//J JOB\n" + first + "\n//             " + " BCD'\n"
    check_trace(parse_text(text), text)


# ---------------------------------------------------------------- known-defect registry
def test_registry_loads_and_explains_only_open_signatures() -> None:
    # TC-018: A10 is RESOLVED_PENDING_REVIEW since CD-2; its signature is used here as an OPEN
    # example to test the registry logic, independent of A10's current status.
    defects = [replace(d, status="OPEN") if d.id == "A10" else d for d in load_known_defects()]
    a10 = Violation("H-SPAN-02", "J00001", "span end 3 < end of data region R00004 (5, "
                                           "terminator EOF)")
    other = Violation("H-SPAN-02", "J00001", "span end 3 < end of data region R00004 (5, "
                                             "terminator DELIMITER)")
    explained, rest = explain([a10, other], defects)
    assert explained == {"A10": [a10]} and rest == [other]
    closed = [replace(d, status="CLOSED") for d in defects]
    assert explain([a10], closed) == ({}, [a10])


def test_registry_rejects_invalid_entries(tmp_path: Path) -> None:
    p = tmp_path / "k.yaml"
    p.write_text("schema_version: 1\ndefects:\n  - {id: X, title: t, severity: HUGE, scope: STEP4B,"
                 " status: OPEN, source: s}\n", encoding="utf-8")
    with pytest.raises(RegistryError):
        load_known_defects(p)


# ---------------------------------------------------------------- CardDemo
@pytest.mark.corpus
def test_carddemo_violations_are_all_registered_and_mutants_all_detected(
        corpus_root: Path) -> None:
    oracle = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                            .read_text(encoding="utf-8"))
    defects = load_known_defects()
    seen: set[str] = set()
    for rel in oracle["jcl_family_files"]:
        kind = "proc_member" if rel.lower().endswith((".prc", ".proc")) else "job"
        p = corpus_root / rel
        r = parse_file(p, encoding="utf-8", input_kind=kind)
        explained, rest = explain(check_hierarchy(r), defects)
        assert rest == [], (rel, rest)
        seen |= set(explained)
        text = p.read_bytes().decode("utf-8")
        for m in all_mutants(r, consistent=True):
            d = detect(m, r, text)
            assert d["invariants"] or d["trace"], (rel, m.operator, m.target)
    assert seen == set()  # TC-018: A10, H01 and H02 (member PEND) fixed in CD-2

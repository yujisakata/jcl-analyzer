"""H-05 Test result reporting: five distinct statuses, never merged into one rate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness_helpers import base_case, write_suite

from jclprof.harness.adapters import AdapterOutput
from jclprof.harness.loader import GoldenCase, load_suite
from jclprof.harness.registry import RuleRegistry
from jclprof.harness.runner import STATUSES, run_suite, write_report


class FakeSyntactic:
    """Stands in for a future Parser adapter in Harness self-tests only."""

    stage = "syntactic"

    def __init__(self, view: dict[str, Any], diags: list[dict[str, Any]] | None = None) -> None:
        self.view = view
        self.diags = diags or []

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        return AdapterOutput(view=self.view, diagnostics=self.diags)


class Boom:
    stage = "syntactic"

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        raise RuntimeError("adapter crashed")


def _cases(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any]) -> list[GoldenCase]:
    cases = [
        base_case(registry, test_id="G-JED-901"),
        base_case(registry, test_id="G-JED-902", review_status="blocked",
                  blocked_reason="JES type undefined"),
        base_case(registry, test_id="G-JED-903", corpus_source={
            "root_id": "carddemo", "rel_path": "jcl/X.jcl", "sha256": "0" * 64, "lines": [1, 1]}),
    ]
    res = load_suite(write_suite(tmp_path, cases), registry, catalog)
    assert res.errors == []
    return res.cases


def test_not_implemented_without_adapter(tmp_path: Path, registry: RuleRegistry,
                                         catalog: dict[str, Any]) -> None:
    rep = run_suite(_cases(tmp_path, registry, catalog), adapters={}, corpus_roots={})
    st = {r.test_id: r.status for r in rep.results}
    assert st == {"G-JED-901": "NOT_IMPLEMENTED", "G-JED-902": "BLOCKED", "G-JED-903": "BLOCKED"}
    assert rep.counts() == {"PASSED": 0, "FAILED": 0, "BLOCKED": 2, "NOT_IMPLEMENTED": 1,
                            "NOT_RUN": 0}


def test_passed_and_failed_with_adapter(tmp_path: Path, registry: RuleRegistry,
                                        catalog: dict[str, Any]) -> None:
    cases = _cases(tmp_path, registry, catalog)
    good = FakeSyntactic(cases[0].raw["expected_structure"])
    rep = run_suite(cases[:1], adapters={"syntactic": good}, corpus_roots={})
    assert rep.results[0].status == "PASSED"
    bad = FakeSyntactic({"view": "statements", "statements": []})
    rep2 = run_suite(cases[:1], adapters={"syntactic": bad}, corpus_roots={})
    assert rep2.results[0].status == "FAILED"
    assert rep2.results[0].differences
    noisy = FakeSyntactic(cases[0].raw["expected_structure"],
                          [{"code": "PAR-W001", "severity": "WARNING", "line": 1}])
    assert run_suite(cases[:1], adapters={"syntactic": noisy},
                     corpus_roots={}).results[0].status == "FAILED"


def test_adapter_exception_is_failed_not_hidden(tmp_path: Path, registry: RuleRegistry,
                                                catalog: dict[str, Any]) -> None:
    cases = _cases(tmp_path, registry, catalog)
    rep = run_suite(cases[:1], adapters={"syntactic": Boom()}, corpus_roots={})
    assert rep.results[0].status == "FAILED"
    assert "adapter crashed" in rep.results[0].reason


def test_not_run_when_deselected(tmp_path: Path, registry: RuleRegistry,
                                 catalog: dict[str, Any]) -> None:
    rep = run_suite(_cases(tmp_path, registry, catalog), adapters={}, corpus_roots={},
                    select={"G-JED-901"})
    st = {r.test_id: r.status for r in rep.results}
    assert st["G-JED-902"] == "NOT_RUN" and st["G-JED-903"] == "NOT_RUN"


def test_corpus_sha_mismatch_blocks(tmp_path: Path, registry: RuleRegistry,
                                    catalog: dict[str, Any]) -> None:
    corpus = tmp_path / "corpus"
    (corpus / "jcl").mkdir(parents=True)
    (corpus / "jcl" / "X.jcl").write_text("//X JOB\n", encoding="utf-8")
    cases = _cases(tmp_path, registry, catalog)
    rep = run_suite(cases[2:], adapters={}, corpus_roots={"carddemo": corpus})
    assert rep.results[0].status == "BLOCKED"
    assert "sha256" in rep.results[0].reason


def test_report_keeps_statuses_separate(tmp_path: Path, registry: RuleRegistry,
                                        catalog: dict[str, Any]) -> None:
    rep = run_suite(_cases(tmp_path, registry, catalog), adapters={}, corpus_roots={})
    out = tmp_path / "out"
    write_report(rep, out)
    data = json.loads((out / "golden_run.json").read_text(encoding="utf-8"))
    assert set(data["counts"]) == set(STATUSES)
    assert not any(k in data for k in ("pass_rate", "success_rate", "score"))
    assert {r["test_id"]: r["verification_status"] for r in data["results"]}["G-JED-901"] == \
        "NOT_IMPLEMENTED"
    md = (out / "golden_run.md").read_text(encoding="utf-8")
    for s in STATUSES:
        assert s in md


def test_assurance_formal_only_for_reviewed_or_approved(tmp_path: Path, registry: RuleRegistry,
                                                        catalog: dict[str, Any]) -> None:
    cases = [base_case(registry, test_id="G-JED-911"),
             base_case(registry, test_id="G-JED-912", review_status="approved",
                       approval={"approved_by": "u", "approved_on": "2026-11-15"})]
    res = load_suite(write_suite(tmp_path, cases), registry, catalog)
    rep = run_suite(res.cases, adapters={}, corpus_roots={})
    assert {r.test_id: r.assurance for r in rep.results} == {"G-JED-911": "REFERENCE",
                                                            "G-JED-912": "FORMAL"}

"""H-01 Golden Loader + schema / semantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from harness_helpers import base_case, write_suite

from jclprof.harness.loader import load_suite
from jclprof.harness.registry import RuleRegistry


def _errors(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any],
            cases: list[dict[str, Any]], **kw: Any) -> list[str]:
    suite = write_suite(tmp_path, cases, **kw)
    return [e.message for e in load_suite(suite, registry, catalog).errors]


def test_valid_case_loads(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    suite = write_suite(tmp_path, [base_case(registry)])
    res = load_suite(suite, registry, catalog)
    assert res.errors == []
    assert [c.test_id for c in res.cases] == ["G-JED-901"]
    assert res.cases[0].input_path == suite / "inputs/x/a.jcl"


@pytest.mark.parametrize(
    "mutation",
    [
        {"verification_status": "passed"},          # run result must not be in the definition
        {"case_type": "weird"},
        {"validation_stage": "magic"},
        {"review_status": "blocked"},               # blocked requires blocked_reason
        {"review_status": "approved"},              # approved requires approval record
        {"test_id": "bad id"},
        {"unknown_attr": 1},
        {"expected_structure": {"view": "none"}},   # none requires reason
        {"expected_structure": {"view": "statements"}},  # statements view requires statements
    ],
)
def test_schema_rejects(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any],
                        mutation: dict[str, Any]) -> None:
    errs = _errors(tmp_path, registry, catalog, [base_case(registry, **mutation)])
    assert errs, mutation


@pytest.mark.parametrize("missing", ["oracle_method", "oracle_author", "rule_ids", "notes",
                                     "expected_diagnostics", "source_reference"])
def test_required_attributes(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any],
                             missing: str) -> None:
    c = base_case(registry)
    del c[missing]
    assert _errors(tmp_path, registry, catalog, [c])


def test_unknown_rule_id(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    c = base_case(registry)
    c["rule_ids"] = ["JCL-NOPE-001"]
    assert any("unknown rule" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_source_reference_must_match_registry(tmp_path: Path, registry: RuleRegistry,
                                              catalog: dict[str, Any]) -> None:
    c = base_case(registry)
    c["source_reference"][0]["pages"] = "999"
    assert any("source_reference" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_duplicate_test_id(tmp_path: Path, registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    assert any("duplicate test_id" in e
               for e in _errors(tmp_path, registry, catalog, [base_case(registry)] * 2))


def test_category_must_match_file(tmp_path: Path, registry: RuleRegistry,
                                  catalog: dict[str, Any]) -> None:
    c = base_case(registry, category="COND")
    assert any("category" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_missing_input_file(tmp_path: Path, registry: RuleRegistry,
                            catalog: dict[str, Any]) -> None:
    c = base_case(registry, input_file="inputs/x/missing.jcl")
    assert any("input_file" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_unknown_diagnostic_code(tmp_path: Path, registry: RuleRegistry,
                                 catalog: dict[str, Any]) -> None:
    c = base_case(registry, expected_diagnostics={
        "mode": "exact", "items": [{"code": "PAR-E999", "severity": "ERROR", "line": 1}]})
    assert any("PAR-E999" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_diagnostic_severity_must_match_catalog(tmp_path: Path, registry: RuleRegistry,
                                                catalog: dict[str, Any]) -> None:
    c = base_case(registry, expected_diagnostics={
        "mode": "exact", "items": [{"code": "PAR-E002", "severity": "WARNING", "line": 1}]})
    assert any("severity" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_pending_rule_cannot_be_reviewed_or_approved(tmp_path: Path, registry: RuleRegistry,
                                                     catalog: dict[str, Any]) -> None:
    c = base_case(registry, rule_ids=["MVS-MEM-001"], review_status="reviewed")
    assert any("PENDING" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_policy_only_case_cannot_be_approved(tmp_path: Path, registry: RuleRegistry,
                                             catalog: dict[str, Any]) -> None:
    c = base_case(registry, rule_ids=["POL-001"], review_status="approved",
                  approval={"approved_by": "x", "approved_on": "2026-11-15"})
    assert any("VERIFIED IBM rule" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_view_must_fit_stage(tmp_path: Path, registry: RuleRegistry,
                             catalog: dict[str, Any]) -> None:
    c = base_case(registry, validation_stage="resolution")
    assert any("view" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_scope_must_be_inside_input(tmp_path: Path, registry: RuleRegistry,
                                    catalog: dict[str, Any]) -> None:
    c = base_case(registry, scope={"lines": [1, 5]})
    assert any("scope" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_environment_library_must_exist(tmp_path: Path, registry: RuleRegistry,
                                        catalog: dict[str, Any]) -> None:
    c = base_case(registry, environment={"datasets": [{"dsn": "A.B", "path": "libs/none"}]})
    assert any("libs/none" in e for e in _errors(tmp_path, registry, catalog, [c]))


def test_invalid_yaml_reported_not_raised(tmp_path: Path, registry: RuleRegistry,
                                          catalog: dict[str, Any]) -> None:
    suite = write_suite(tmp_path, [base_case(registry)])
    (suite / "cases" / "broken.yaml").write_text("cases: [\n", encoding="utf-8")
    res = load_suite(suite, registry, catalog)
    assert any("broken.yaml" in e.file for e in res.errors)

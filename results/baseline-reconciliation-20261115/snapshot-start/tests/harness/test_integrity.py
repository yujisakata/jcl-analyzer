"""H-04 Golden Integrity: manifest-based change detection; never auto-updates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from harness_helpers import base_case, write_suite

from jclprof.harness.integrity import check_integrity, seal
from jclprof.harness.registry import RuleRegistry


def _sealed(tmp_path: Path, registry: RuleRegistry) -> Path:
    suite = write_suite(tmp_path, [base_case(registry)])
    seal(suite, sealed_by="tester")
    return suite


def _snapshot(d: Path) -> dict[str, bytes]:
    return {p.relative_to(d).as_posix(): p.read_bytes()
            for p in sorted(d.rglob("*")) if p.is_file()}


def test_clean_after_seal(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = _sealed(tmp_path, registry)
    rep = check_integrity(suite)
    assert rep.ok, rep
    assert rep.modified == [] and rep.added == [] and rep.removed == []


def test_unsealed_suite_is_not_ok(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = write_suite(tmp_path, [base_case(registry)])
    rep = check_integrity(suite)
    assert not rep.ok
    assert rep.manifest_missing


def test_modified_expected_value_reported_with_diff(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = _sealed(tmp_path, registry)
    f = suite / "cases" / "job_exec_dd.yaml"
    doc: dict[str, Any] = yaml.safe_load(f.read_text(encoding="utf-8"))
    doc["cases"][0]["expected_structure"]["statements"][0]["name"] = "B"
    f.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    rep = check_integrity(suite)
    assert not rep.ok
    (m,) = rep.modified
    assert m.path == "cases/job_exec_dd.yaml"
    assert "-" in m.diff and "+" in m.diff and "name: B" in m.diff
    assert [c.test_id for c in rep.case_changes] == ["G-JED-901"]
    assert rep.case_changes[0].change == "modified"


def test_input_change_added_removed(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = _sealed(tmp_path, registry)
    (suite / "inputs/x/a.jcl").write_text("//A JOB  CHANGED\n", encoding="utf-8")
    (suite / "inputs/x/new.jcl").write_text("//N JOB\n", encoding="utf-8")
    rep = check_integrity(suite)
    assert [m.path for m in rep.modified] == ["inputs/x/a.jcl"]
    assert rep.added == ["inputs/x/new.jcl"]
    (suite / "inputs/x/new.jcl").unlink()
    (suite / "inputs/x/a.jcl").unlink()
    rep2 = check_integrity(suite)
    assert rep2.removed == ["inputs/x/a.jcl"]


def test_approved_case_change_without_change_log_is_violation(tmp_path: Path,
                                                               registry: RuleRegistry) -> None:
    c = base_case(registry, review_status="approved",
                  approval={"approved_by": "user", "approved_on": "2026-11-15"})
    suite = write_suite(tmp_path, [c])
    seal(suite, sealed_by="tester")
    f = suite / "cases" / "job_exec_dd.yaml"
    doc: dict[str, Any] = yaml.safe_load(f.read_text(encoding="utf-8"))
    doc["cases"][0]["expected_structure"]["statements"][0]["name"] = "B"
    f.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    rep = check_integrity(suite)
    assert rep.approved_violations == ["G-JED-901"]


def test_check_never_writes(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = _sealed(tmp_path, registry)
    (suite / "inputs/x/a.jcl").write_text("//A JOB  CHANGED\n", encoding="utf-8")
    before = _snapshot(suite)
    check_integrity(suite)
    assert _snapshot(suite) == before

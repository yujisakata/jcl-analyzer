"""CLI for the harness: golden-check, verify, golden-seal, rules-render (exit codes per ADR-008)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from harness_helpers import GOLDEN_DIR, base_case, write_suite

from jclprof import cli
from jclprof.harness.defects import known_golden_failures, load_known_defects
from jclprof.harness.registry import RuleRegistry


def test_golden_check_real_suite() -> None:
    assert cli.main(["golden-check", "--suite", str(GOLDEN_DIR)]) == 0


def test_verify_real_suite_reports_not_implemented(tmp_path: Path) -> None:
    """TC-013: FAILED cases are allowed only if registered under an OPEN known defect
    (tests/KNOWN_DEFECTS.yaml); verify exits 1 whenever any case FAILED."""
    rc = cli.main(["verify", "--suite", str(GOLDEN_DIR), "--output", str(tmp_path)])
    data = json.loads((tmp_path / "golden_run.json").read_text(encoding="utf-8"))
    assert data["counts"]["NOT_IMPLEMENTED"] > 0
    failed = {r["test_id"] for r in data["results"] if r["verification_status"] == "FAILED"}
    known = set(known_golden_failures(load_known_defects()))
    assert failed <= known, f"unregistered FAILED cases: {sorted(failed - known)}"
    assert rc == (1 if failed else 0)


def test_rules_render_check() -> None:
    assert cli.main(["rules-render", "--check"]) == 0


def test_golden_check_detects_unsealed_change(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = write_suite(tmp_path, [base_case(registry)])
    assert cli.main(["golden-check", "--suite", str(suite)]) == 1  # no manifest yet
    assert cli.main(["golden-seal", "--suite", str(suite), "--by", "tester"]) == 0
    assert cli.main(["golden-check", "--suite", str(suite)]) == 0
    (suite / "inputs/x/a.jcl").write_text("//A JOB  X\n", encoding="utf-8")
    assert cli.main(["golden-check", "--suite", str(suite)]) == 1


def test_golden_check_rejects_invalid_definitions(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = write_suite(tmp_path, [base_case(registry, verification_status="passed")])
    assert cli.main(["golden-check", "--suite", str(suite)]) == 2


def test_seal_requires_name(tmp_path: Path, registry: RuleRegistry) -> None:
    suite = write_suite(tmp_path, [base_case(registry)])
    with pytest.raises(SystemExit):
        cli.main(["golden-seal", "--suite", str(suite)])

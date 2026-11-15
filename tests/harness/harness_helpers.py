"""Helpers for Harness self-tests (synthetic Golden suites under tmp_path)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from jclprof.harness.registry import RuleRegistry

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = PROJECT_ROOT / "specs" / "rules.yaml"
CATALOG_PATH = PROJECT_ROOT / "specs" / "diagnostic-catalog.yaml"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "golden"


def base_case(registry: RuleRegistry, **over: Any) -> dict[str, Any]:
    rule_ids = over.pop("rule_ids", ["JCL-FMT-001"])
    case: dict[str, Any] = {
        "test_id": "G-JED-901",
        "category": "JOB_EXEC_DD",
        "description": "synthetic",
        "rule_ids": rule_ids,
        "source_reference": registry.source_references(rule_ids),
        "input_file": "inputs/x/a.jcl",
        "input_kind": "job",
        "case_type": "valid",
        "validation_stage": "syntactic",
        "expected_structure": {
            "view": "statements",
            "statements": [{"kind": "JOB", "span": [1, 1], "name": "A", "positional": [],
                            "keywords": []}],
        },
        "expected_diagnostics": {"mode": "exact", "items": []},
        "oracle_method": "manual",
        "oracle_author": "test",
        "review_status": "draft",
        "notes": "",
    }
    case.update(over)
    return case


def write_suite(root: Path, cases: list[dict[str, Any]], category: str = "JOB_EXEC_DD",
                inputs: dict[str, str] | None = None) -> Path:
    suite = root / "golden"
    (suite / "cases").mkdir(parents=True, exist_ok=True)
    for rel, text in (inputs or {"inputs/x/a.jcl": "//A JOB\n"}).items():
        p = suite / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    doc = {"schema_version": 1, "category": category, "cases": copy.deepcopy(cases)}
    (suite / "cases" / f"{category.lower()}.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return suite

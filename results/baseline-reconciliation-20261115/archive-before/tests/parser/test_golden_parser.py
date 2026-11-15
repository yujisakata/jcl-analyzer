"""Parser verification suite (separate from the Harness self-tests; ADR-018).

Runs every Golden case through the registered stage adapters. Until Step 4/5 register adapters,
each case is skipped with reason NOT_IMPLEMENTED (or BLOCKED), never failed and never passed.
Run explicitly: uv run pytest tests/parser tests/property
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jclprof.context.config import ConfigError, load_config
from jclprof.harness.adapters import registered_adapters
from jclprof.harness.loader import GoldenCase, load_suite
from jclprof.harness.registry import load_catalog, load_rules
from jclprof.harness.runner import run_case

ROOT = Path(__file__).resolve().parents[2]
_registry = load_rules(ROOT / "specs" / "rules.yaml")
_result = load_suite(ROOT / "tests" / "golden", _registry,
                     load_catalog(ROOT / "specs" / "diagnostic-catalog.yaml"))
CASES = _result.cases

try:
    CORPUS = {r.id: r.path for r in load_config(ROOT / "config" / "profiler.yaml").roots}
except ConfigError:
    CORPUS = {}

pytestmark = pytest.mark.parser


def test_suite_definitions_valid() -> None:
    assert [e.message for e in _result.errors] == []


@pytest.mark.parametrize("case", CASES, ids=[c.test_id for c in CASES])
def test_golden_case(case: GoldenCase) -> None:
    r = run_case(case, registered_adapters(), CORPUS)
    if r.status in ("NOT_IMPLEMENTED", "BLOCKED"):
        pytest.skip(f"{r.status}: {r.reason}")
    assert r.status == "PASSED", "\n".join(
        f"{d.kind} {d.path}: expected={d.expected!r} actual={d.actual!r}" for d in r.differences
    ) or r.reason

"""Resolver diagnostic codes must equal specs/diagnostic-catalog.yaml (severity and class)."""

from __future__ import annotations

from conftest import PROJECT_ROOT
from jclprof.harness.registry import load_catalog
from jclprof.resolver import RESOLVE_CODES


def test_resolver_codes_match_catalog() -> None:
    catalog = load_catalog(PROJECT_ROOT / "specs" / "diagnostic-catalog.yaml")
    for code, (sev, cls, _title) in RESOLVE_CODES.items():
        assert catalog[code]["severity"] == sev, code
        assert catalog[code]["class"] == cls, code
        assert not catalog[code].get("deprecated"), code

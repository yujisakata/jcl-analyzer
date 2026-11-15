"""Context integrity: rule registry, rendered spec document and the real Golden suite."""

from __future__ import annotations

from typing import Any

import yaml
from harness_helpers import GOLDEN_DIR, PROJECT_ROOT

from jclprof.harness.integrity import check_integrity
from jclprof.harness.loader import load_suite
from jclprof.harness.registry import RULE_STATUSES, RuleRegistry
from jclprof.harness.render import render_reference
from jclprof.harness.runner import run_suite

CATEGORIES = {"JOB_EXEC_DD", "CONTINUATION_COLUMNS", "QUOTES_PARENTHESES", "DD_CONCATENATION",
              "GDG_DISP", "INSTREAM_DATA", "PROC_PEND", "JCLLIB_INCLUDE_SET", "IF_THEN_ELSE",
              "COND", "INVALID_UNRESOLVED"}


def test_registry_well_formed(registry: RuleRegistry) -> None:
    assert registry.rules
    for r in registry.rules.values():
        assert r.status in RULE_STATUSES
        assert r.doc in registry.documents
        if r.status == "VERIFIED":
            assert r.pages and r.pages != "-", r.id
            assert r.doc.startswith("IBM-"), r.id
        if r.id.startswith("POL-"):
            assert r.status == "PROJECT-POLICY"


def test_catalog_rules_exist(registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    for code, spec in catalog.items():
        for rid in spec["rules"]:
            assert rid in registry.rules, (code, rid)


def test_real_suite_loads_without_errors(registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    res = load_suite(GOLDEN_DIR, registry, catalog)
    assert [e.message for e in res.errors] == []
    assert {c.category for c in res.cases} == CATEGORIES


def test_every_case_traces_to_ibm_or_independent_basis(registry: RuleRegistry,
                                                       catalog: dict[str, Any]) -> None:
    for c in load_suite(GOLDEN_DIR, registry, catalog).cases:
        ibm = [r for r in c.rule_ids if not registry.rules[r].id.startswith("POL-")]
        assert ibm, f"{c.test_id} has no IBM rule"
        if c.review_status in ("reviewed", "approved"):
            assert all(registry.rules[r].status in ("VERIFIED", "PROJECT-POLICY")
                       for r in c.rule_ids), c.test_id


def test_corpus_cases_match_independent_oracle(registry: RuleRegistry,
                                               catalog: dict[str, Any]) -> None:
    oracle = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                            .read_text(encoding="utf-8"))
    for c in load_suite(GOLDEN_DIR, registry, catalog).cases:
        cs = c.raw.get("corpus_source")
        if not cs:
            continue
        entry = oracle["jcl_family_files"][cs["rel_path"]]
        assert cs["sha256"] == entry["sha256"], c.test_id
        assert cs["lines"][1] <= entry["record_count"], c.test_id


def test_golden_inputs_lint(registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    for c in load_suite(GOLDEN_DIR, registry, catalog).cases:
        if c.is_corpus_input:
            continue  # original corpus files are read-only and not linted here
        data = c.input_path.read_bytes()
        text = data.decode("utf-8")
        assert "\t" not in text, c.test_id
        assert "\r" not in text, f"{c.test_id}: golden inputs use LF"
        for n, ln in enumerate(text.split("\n"), start=1):
            assert len(ln) <= 80, f"{c.test_id} {c.input_file}:{n} longer than 80"


def test_real_suite_integrity(registry: RuleRegistry) -> None:
    rep = check_integrity(GOLDEN_DIR)
    assert rep.ok, rep.summary()


def test_real_suite_has_no_failures_without_parser(registry: RuleRegistry,
                                                   catalog: dict[str, Any]) -> None:
    cases = load_suite(GOLDEN_DIR, registry, catalog).cases
    rep = run_suite(cases, adapters={}, corpus_roots={})
    assert rep.counts()["FAILED"] == 0
    assert rep.counts()["PASSED"] == 0
    assert set(r.status for r in rep.results) <= {"NOT_IMPLEMENTED", "BLOCKED"}


def test_reference_document_in_sync(registry: RuleRegistry, catalog: dict[str, Any]) -> None:
    cases = load_suite(GOLDEN_DIR, registry, catalog).cases
    expected = render_reference(registry, cases)
    actual = (PROJECT_ROOT / "specs" / "ibm-jcl-reference.md").read_text(encoding="utf-8")
    assert actual == expected, "run: uv run jclprof rules-render"


def test_lexer_codes_match_catalog(catalog: dict[str, Any]) -> None:
    from jclprof.lexer import LEX_CODES

    for code, (sev, cls, _title) in LEX_CODES.items():
        assert catalog[code]["severity"] == sev, code
        assert catalog[code]["class"] == cls, code
    assert {k for k in catalog if k.startswith("LEX-")} == set(LEX_CODES)


def test_every_catalog_code_has_class(catalog: dict[str, Any]) -> None:
    classes = {"SYNTAX", "SYNTAX_DEFINED", "ANALYZABILITY", "UNSUPPORTED", "ENVIRONMENT",
               "SPEC_UNCONFIRMED", "ADVISORY"}
    for code, spec in catalog.items():
        if code.startswith("INV-"):
            continue
        assert spec.get("class") in classes, code
        if spec["class"] == "SPEC_UNCONFIRMED":
            assert spec["severity"] != "ERROR", code  # user decision A6
        if spec.get("deprecated"):
            assert spec.get("replaced_by") in catalog, code

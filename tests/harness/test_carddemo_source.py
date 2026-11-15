"""CD-1: independent original-source oracle, real corpus, and fault sensitivity.

These are Harness tests. The acceptance command separately reports the real Parser's failures;
passing these tests is NOT a passing CD acceptance or human approval of the oracle.
"""
from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from jclprof.harness.carddemo_mutations import Mutation, mutation_report, mutations
from jclprof.harness.carddemo_source import (
    DEFAULT_ORACLE,
    PROJECT,
    OracleError,
    check_case,
    decisions,
    load_oracle,
    run_cases,
    sha256,
    source_view,
    trace_issues,
)
from jclprof.parser import ParseResult

CORPUS = Path("D:/projects/aws-card/aws-mainframe-modernization-carddemo/app")


@pytest.fixture(scope="module")
def suite() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, ParseResult]]:
    oracle, reviews = load_oracle()
    results, parsed = run_cases(oracle, CORPUS)
    assert len(parsed) == 48, "Missing/changed originals must not turn into skipped CD checks"
    return oracle, reviews, results, parsed


def test_oracle_is_frozen_source_only_and_all_review_pending(suite: Any) -> None:
    oracle, reviews, _, _ = suite
    source = PROJECT / oracle["provenance"]["inventory_path"]
    assert sha256(source.read_bytes()) == oracle["provenance"]["inventory_sha256"]
    assert len(oracle["files"]) == 48
    assert all(r["status"] == "PENDING" for r in reviews["files"])
    # The source-only authoring path cannot accidentally import production parsing/comparison.
    tree = ast.parse((PROJECT / "tools/golden_authoring/build_carddemo_source.py")
                     .read_text(encoding="utf-8"))
    imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(n.startswith(("jclprof", "subprocess", "importlib")) for n in imports)


def test_complete_counts_and_eof_expectation_come_from_source(suite: Any) -> None:
    oracle, _, _, _ = suite
    counts = oracle["counts"]
    assert (counts["steps"], counts["dds"], counts["unnamed_dds"], counts["data_regions"]) == (
        123, 500, 24, 91)
    assert sum(len(f["trace"]["records"]) for f in oracle["files"]) == 3046
    file = next(f for f in oracle["files"] if f["path"].endswith("MNTTRDB2.jcl"))
    assert file["expected_structure"]["hierarchy"]["jobs"][0]["span"] == [1, 30]
    assert file["data_regions"][0]["lines"] == [29, 30]
    for f in oracle["files"]:
        expected_reachable = f["expected_structure"]["hierarchy"]["reachable_lines"]
        assert expected_reachable == [s["line"] for s in f["trace"]["statements"]]


@pytest.mark.parametrize("damage", ["expectation", "review_hash", "approval"])
def test_oracle_tampering_and_unidentified_approval_fail(tmp_path: Path, damage: str) -> None:
    for name in ("expectations.json", "oracle-manifest.json", "reviews.json"):
        (tmp_path / name).write_bytes((DEFAULT_ORACLE / name).read_bytes())
    if damage == "expectation":
        p = tmp_path / "expectations.json"
        p.write_bytes(p.read_bytes() + b" ")
    else:
        p = tmp_path / "reviews.json"
        reviews = json.loads(p.read_text(encoding="utf-8"))
        if damage == "review_hash":
            reviews["expectations_sha256"] = "wrong"
        else:
            reviews["files"][0]["status"] = "APPROVED"
        p.write_text(json.dumps(reviews), encoding="utf-8")
    with pytest.raises(OracleError):
        load_oracle(tmp_path)


def test_changed_input_is_blocked_and_not_parsed(tmp_path: Path, suite: Any) -> None:
    oracle, _, _, _ = suite
    file = oracle["files"][0]
    p = tmp_path / file["path"]
    p.parent.mkdir(parents=True)
    p.write_text("//DIFFERENT JOB\n", encoding="utf-8")
    with patch("jclprof.harness.carddemo_source.parse_file") as parser:
        results, parsed = run_cases({"files": [file]}, tmp_path)
    parser.assert_not_called()
    assert not parsed
    assert results[0]["source_status"] == "BLOCKED"


def test_unexpected_uppercase_jcl_invalidates_scope(tmp_path: Path, suite: Any) -> None:
    oracle, _, _, _ = suite
    (tmp_path / "ADDED.JCL").write_text("//NEW JOB\n", encoding="utf-8")
    with patch("jclprof.harness.carddemo_source.parse_file") as parser:
        results, parsed = run_cases(oracle, tmp_path)
    parser.assert_not_called()
    assert not parsed and len(results) == 48
    assert all(r["source_status"] == "BLOCKED" for r in results)
    assert results[0]["unexpected_source_files"] == ["ADDED.JCL"]


def test_unapproved_expectation_and_measured_failure_are_separate(suite: Any) -> None:
    _, reviews, results, _ = suite
    mutation = {"total": 1, "detected": 1, "escaped": []}
    gates = decisions(results, reviews, mutation)
    assert gates["CD-ASSURANCE"]["status"] == "PENDING"
    assert gates["formal_acceptance"] == "FAIL"
    clean = [dict(r, source_status="PASS", trace_status="PASS") for r in results]
    assert decisions(clean, reviews, mutation)["formal_acceptance"] == "FAIL"
    approved = {"files": [dict(r, status="APPROVED") for r in reviews["files"]]}
    assert decisions(clean, approved, mutation)["formal_acceptance"] == "PASS"
    # TC-019: since CD-2 the measured results are all PASS, so the measured failure is built
    # explicitly (the intent is unchanged: a measured failure keeps formal acceptance at FAIL).
    measured_fail = [dict(clean[0], source_status="FAIL"), *clean[1:]]
    assert decisions(measured_fail, approved, mutation)["formal_acceptance"] == "FAIL"
    trace_fail = [dict(clean[0], trace_status="FAIL"), *clean[1:]]
    assert decisions(trace_fail, approved, mutation)["formal_acceptance"] == "FAIL"
    assert decisions(clean, approved, {"total": 0})["CD-ASSURANCE"]["status"] == "FAIL"


def test_full_token_segments_and_value_text_are_checked(suite: Any) -> None:
    oracle, _, _, parsed = suite
    case = oracle["files"][0]
    r = parsed[case["path"]]
    raw = (CORPUS / case["path"]).read_bytes()
    # Change one token's later segment endpoint: same text/start is insufficient.
    lexical = r.lex.statements[0]
    tok = lexical.tokens[-1]
    segments = list(tok.segments)
    n, lo, hi = segments[-1]
    segments[-1] = n, lo, hi + 1
    new = replace(tok, segments=tuple(segments))
    ls = replace(lexical, tokens=(*lexical.tokens[:-1], new))
    bad = replace(r, lex=replace(r.lex, statements=(ls, *r.lex.statements[1:])))
    assert any(x["code"] == "CD-TOKENS" for x in trace_issues(case, bad, raw))
    # Changing raw Value.text only must be found even if its normalized value is untouched.
    statement = r.statements[0]
    kw = statement.keywords[0]
    assert kw.value is not None
    kw2 = replace(kw, value=replace(kw.value, text=kw.value.text + "X"))
    s2 = replace(statement, keywords=(kw2, *statement.keywords[1:]))
    bad = replace(r, statements=(s2, *r.statements[1:]))
    assert any(x["code"] == "CD-VALUE" for x in trace_issues(case, bad, raw))


def test_source_qualifier_is_retained_without_changing_the_oracle(suite: Any) -> None:
    oracle, _, _, parsed = suite
    case = next(f for f in oracle["files"] if f["path"] == "jcl/TRANBKP.jcl")
    r = parsed[case["path"]]
    # This is a representation conversion, not an expectation changed to match a Parser.
    assert r.jobs[0].steps[0].dds[0].concat_head == "FILEIN"
    assert source_view(r)["hierarchy"]["jobs"][0]["steps"][0]["dds"][0]["concat_head"] == (
        "PRC001.FILEIN")
    dd = r.jobs[0].steps[0].dds[0]
    step = replace(r.jobs[0].steps[0], dds=(replace(dd, procstep=None),
                                         *r.jobs[0].steps[0].dds[1:]))
    bad = replace(r, jobs=(replace(r.jobs[0], steps=(step, *r.jobs[0].steps[1:])),))
    checked = check_case(case, bad, (CORPUS / case["path"]).read_bytes())
    assert any("concat_head" in d["path"] for d in checked["source_differences"])


@pytest.fixture(scope="module")
def sensitivity(suite: Any) -> dict[str, Any]:
    oracle, _, results, parsed = suite
    return mutation_report(oracle, parsed, CORPUS, results)


@pytest.mark.parametrize("operator", ["delete_job", "delete_proc_root", "move_job", "delete_step",
                                     "move_step", "delete_dd", "move_dd", "reorder_concat",
                                     "data_boundary", "shrink_span"])
def test_each_required_operator_is_rejected_by_independent_source_oracle(
        operator: str, sensitivity: dict[str, Any]) -> None:
    row = sensitivity["operators"][operator]
    assert row["total"] > 0
    assert row["detected"] == row["total"]
    assert all(e["new_source_differences"] > 0 for e in row["examples"])


def test_mutations_cover_all_source_files_and_leave_original_ast_unchanged(
        suite: Any, sensitivity: dict[str, Any]) -> None:
    _, _, _, parsed = suite
    assert set(sensitivity["primary_files"]) == set(parsed)
    assert not sensitivity["escaped"]
    first = next(iter(parsed))
    before = parsed[first].to_dict()
    next(mutations(parsed))
    assert parsed[first].to_dict() == before


def test_existing_failure_never_counts_as_mutation_detection(suite: Any) -> None:
    oracle, _, baseline, parsed = suite
    path = "app-transaction-type-db2/jcl/MNTTRDB2.jcl"
    noop = Mutation("noop", "unchanged known A10", {path: parsed[path]})
    with patch("jclprof.harness.carddemo_mutations.mutations", return_value=iter([noop])):
        result = mutation_report(oracle, parsed, CORPUS, baseline)
    assert result["total"] == 1 and result["detected"] == 0
    assert any(r.get("operator") == "noop" for r in result["escaped"])


def test_eof_span_damage_is_visible_even_with_pending_review(suite: Any) -> None:
    oracle, _, _, parsed = suite
    case = next(f for f in oracle["files"] if f["path"].endswith("MNTTRDB2.jcl"))
    r = parsed[case["path"]]
    job = r.jobs[0]
    bad = replace(r, jobs=(replace(job, span=(1, 27)),))
    result = check_case(case, bad, (CORPUS / case["path"]).read_bytes())
    assert any(d["path"].startswith("hierarchy.jobs[0].span")
               for d in result["source_differences"])
    assert any(d["code"] == "H-SPAN-02" for d in result["trace_issues"])

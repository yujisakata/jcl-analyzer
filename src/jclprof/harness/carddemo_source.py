"""CD-1 source-only acceptance, separate from Gate A and generic Gate B.

The oracle is independently authored from frozen inventory/originals, never from this adapter.
Review state and observed mismatches are separate. No known-defect suppression is applied.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jclprof.harness.comparator import compare_structure
from jclprof.harness.hierarchy import check_hierarchy
from jclprof.parser import ParseResult, parse_file
from jclprof.parser.adapter import hierarchy_view
from jclprof.parser.model import DDNode, StatementNode, Value

PROJECT = Path(__file__).resolve().parents[3]
DEFAULT_ORACLE = PROJECT / "tests/golden_pending/carddemo_source"


class OracleError(ValueError):
    """A missing, altered or invalid oracle must never silently pass."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_oracle(directory: Path = DEFAULT_ORACLE) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = (directory / "expectations.json").read_bytes()
    manifest = json.loads((directory / "oracle-manifest.json").read_text(encoding="utf-8"))
    reviews = json.loads((directory / "reviews.json").read_text(encoding="utf-8"))
    if manifest.get("expectations_sha256") != sha256(raw):
        raise OracleError("expectations do not match the frozen oracle manifest")
    if reviews.get("expectations_sha256") != sha256(raw):
        raise OracleError("reviews refer to a different expectation version")
    oracle = json.loads(raw)
    files = oracle.get("files", [])
    if oracle.get("schema_version") != 1 or oracle.get("suite") != "CD-1" or len(files) != 48:
        raise OracleError("CD-1 requires the frozen 48-file suite")
    paths = [f["path"] for f in files]
    if len(set(paths)) != len(paths) or any(Path(p).is_absolute() or ".." in Path(p).parts
                                         or ":" in p for p in paths):
        raise OracleError("duplicate or unsafe oracle paths")
    review_paths = [f["path"] for f in reviews.get("files", [])]
    if len(set(review_paths)) != 48 or set(review_paths) != set(paths):
        raise OracleError("reviews must cover exactly the 48 files")
    if len(review_paths) != 48:
        raise OracleError("duplicate review records are not allowed")
    for review in reviews["files"]:
        if review.get("status") not in ("PENDING", "APPROVED"):
            raise OracleError("invalid review status")
        if review["status"] == "APPROVED" and not (
                review.get("reviewed_by") and review.get("reviewed_at")):
            raise OracleError("approval needs an identified reviewer and date")
    return oracle, reviews


def source_view(result: ParseResult) -> dict[str, Any]:
    """Project actual AST links, without repairing missing links from the oracle/flat order."""
    view = result.to_golden_view()
    hierarchy = hierarchy_view(result)
    # Generic hierarchy_view uses the normalized ddname for concat_head; this source
    # oracle deliberately uses the complete coded name. Preserve the qualifier using
    # ACTUAL DDNode fields, never by filling a name from the oracle or statement order.
    def qualify(dds: tuple[DDNode, ...], views: list[dict[str, Any]]) -> None:
        for dd, item in zip(dds, views, strict=True):
            if dd.procstep and dd.concat_head:
                item["concat_head"] = dd.procstep + "." + dd.concat_head

    for job, view_job in zip(result.jobs, hierarchy["jobs"], strict=True):
        qualify(job.job_level_dds, view_job["dds"])
        for st, view_step in zip(job.steps, view_job["steps"], strict=True):
            qualify(st.dds, view_step["dds"])
    if result.input_kind == "proc_member":
        for st, view_step in zip(result.procedure_steps, hierarchy["procedure_steps"], strict=True):
            qualify(st.dds, view_step["dds"])
    by_id = {s.id: s for s in result.statements}
    reachable: list[int] = []

    def statement(s: StatementNode) -> None:
        if s.operation and s.span:
            reachable.append(s.span[0])

    def reference(sid: str) -> None:
        if sid in by_id:
            statement(by_id[sid])

    def step(st: Any) -> None:
        statement(st.exec_statement)
        for dd in st.dds:
            statement(dd.statement)
        for sid in st.other_statements:
            reference(sid)

    for job in result.jobs:
        statement(job.job_statement)
        for dd in job.job_level_dds:
            statement(dd.statement)
        for sid in job.job_level_statements:
            reference(sid)
        for st in job.steps:
            step(st)
        for proc in job.procedures:
            statement(proc.proc_statement)
            if proc.pend_statement:
                statement(proc.pend_statement)
            for st in proc.steps:
                step(st)
    if result.input_kind == "proc_member":
        header = result.procedure_header
        hierarchy["procedure_header"] = ({"name": header.name.text if header.name else None,
                                           "line": header.span[0] if header.span else None}
                                          if header else None)
        if header:
            statement(header)
        for st in result.procedure_steps:
            step(st)
        # CD-2 (user-approved): follow the actual PROC-root link to the member PEND. Still an
        # actual AST link only; nothing is filled in from the oracle or the flat statement list.
        if result.procedure_end is not None:
            statement(result.procedure_end)
    for sid in result.outside_statements:
        reference(sid)
    hierarchy["reachable_lines"] = sorted(reachable)
    view["hierarchy"] = hierarchy
    return view


def _issue(out: list[dict[str, Any]], code: str, path: str, expected: Any, actual: Any) -> None:
    if expected != actual:
        out.append({"code": code, "path": path, "expected": expected, "actual": actual})


def _value_trace(out: list[dict[str, Any]], path: str, spec: dict[str, Any], actual: Value,
                 source_lines: list[str]) -> None:
    _issue(out, "CD-VALUE", path + ".kind", spec["kind"], actual.kind)
    _issue(out, "CD-VALUE", path + ".text", spec["text"], actual.text)
    if spec["segments"]:
        _issue(out, "CD-LOCATION", path + ".start", [spec["line"], spec["column"]],
               [actual.line, actual.column])
        slices = "".join(source_lines[n - 1][lo - 1:hi] for n, lo, hi in spec["segments"])
        _issue(out, "CD-SEGMENTS", path, spec["text"], slices)
    if spec["kind"] == "LIST":
        _issue(out, "CD-VALUE", path + ".items.count", len(spec["items"]), len(actual.items))
        for i, (child, value) in enumerate(zip(spec["items"], actual.items, strict=False)):
            _value_trace(out, f"{path}.items[{i}]", child, value, source_lines)
    if spec["kind"] == "KWSUB":
        _issue(out, "CD-VALUE", path + ".keyword", spec["keyword"], actual.keyword)
        if spec["sub"] is not None and actual.sub is not None:
            _value_trace(out, path + ".sub", spec["sub"], actual.sub, source_lines)
        else:
            _issue(out, "CD-VALUE", path + ".sub.present", spec["sub"] is not None,
                   actual.sub is not None)


def trace_issues(case: dict[str, Any], result: ParseResult, raw: bytes) -> list[dict[str, Any]]:
    """Verify whole raw records, fields, every lexical token segment and AST value occurrence."""
    out: list[dict[str, Any]] = []
    lines = raw.decode(case["encoding"]).splitlines()
    flat = {s.span[0]: s for s in result.statements if s.operation and s.span}
    by_id = {s.id: s for s in result.statements}
    regions = {d.id: d for d in result.data_regions}
    roles = {r.line: r for r in result.records}
    _issue(out, "CD-RECORD", "record.lines", [r["line"] for r in case["trace"]["records"]],
           [r.line for r in result.records])
    _issue(out, "CD-HASH", "source.sha256", case["sha256"], result.lex.sha256)
    _issue(out, "CD-ENCODING", "source.encoding", case["encoding"], result.lex.encoding)
    _issue(out, "CD-SOURCE-REF", "source.relative_path", True,
           Path(result.lex.source).as_posix().endswith("/" + case["path"]))
    offset = 0
    for expected, rec in zip(case["trace"]["records"], result.lex.records, strict=False):
        n = expected["line"]
        path = f"records[{n}]"
        _issue(out, "CD-RECORD", path + ".raw", expected["raw_sha256"],
               sha256(rec.raw.encode(case["encoding"])))
        _issue(out, "CD-RECORD", path + ".terminator", expected["terminator"], rec.terminator)
        end = offset + len((rec.raw + rec.terminator).encode(case["encoding"]))
        _issue(out, "CD-BYTES", path + ".range", [expected["byte_start"], expected["byte_end"]],
               [offset, end])
        offset = end
        role = roles.get(n)
        _issue(out, "CD-ROLE", path + ".role", expected["role"], role.role if role else None)
        owner = by_id.get(role.statement_id or "") if role else None
        # statement_line is the operational logical statement; COMMENT/NULL/DELIMITER are
        # physical special statements. Their actual links are also checked by check_hierarchy.
        owner_line = (owner.span[0] if owner and owner.operation and owner.span and role
                      and role.role in ("STATEMENT", "CONTINUATION") else None)
        _issue(out, "CD-OWNER", path + ".statement_line", expected["statement_line"], owner_line)
        region = regions.get(role.region_id or "") if role else None
        dd = by_id.get(region.statement_id) if region else None
        dd_line = dd.span[0] if dd and dd.span else None
        _issue(out, "CD-OWNER", path + ".data_dd_line", expected["data_dd_line"], dd_line)
    _issue(out, "CD-RECORD", "lex.record_count", len(case["trace"]["records"]),
           len(result.lex.records))
    for spec in case["trace"]["statements"]:
        path = f"statements[{spec['line']}]"
        statement = flat.get(spec["line"])
        if statement is None:
            out.append({"code": "CD-STATEMENT", "path": path, "expected": "present",
                        "actual": "missing"})
            continue
        _issue(out, "CD-LOCATION", path + ".lines", spec["lines"], list(statement.lines))
        _issue(out, "CD-RAW", path + ".raw", [lines[n - 1] for n in spec["lines"]],
               list(statement.raw))
        _issue(out, "CD-LOCATION", path + ".name",
               [spec["line"], 3, spec["name"]] if spec["name"] else None,
               [statement.name.line, statement.name.column, statement.name.text]
               if statement.name else None)
        lexical = (result.lex.statements[statement.lex_statement]
                   if statement.lex_statement is not None
                   and 0 <= statement.lex_statement < len(result.lex.statements) else None)
        if lexical is None:
            out.append({"code": "CD-LEX-REF", "path": path, "expected": "lexical statement",
                        "actual": None})
        else:
            op = lexical.operation
            _issue(out, "CD-LOCATION", path + ".operation",
                   [spec["line"], spec["operation_column"], spec["operation"]],
                   [op.line, op.column, op.text] if op else None)
            _issue(out, "CD-TOKENS", path + ".tokens", spec["tokens"],
                   [json.loads(json.dumps(asdict(t))) for t in lexical.tokens])
            _issue(out, "CD-LEXICAL", path + ".parameter_text", spec["parameter_text"],
                   lexical.parameter_text)
        positionals = iter(statement.positional)
        keywords = iter(statement.keywords)
        _issue(out, "CD-VALUE", path + ".parameters.count",
               [sum(p["keyword"] is None for p in spec["parameters"]),
                sum(p["keyword"] is not None for p in spec["parameters"])],
               [len(statement.positional), len(statement.keywords)])
        for index, param in enumerate(spec["parameters"]):
            location = f"{path}.parameters[{index}]"
            if param["keyword"] is None:
                value = next(positionals, None)
            else:
                kw = next(keywords, None)
                _issue(out, "CD-LOCATION", location + ".keyword",
                       [param["keyword"], param["line"], param["column"]],
                       [kw.name, kw.line, kw.column] if kw else None)
                value = kw.value if kw else None
            if param["value"] is not None and value is not None:
                _value_trace(out, location, param["value"], value, lines)
            else:
                _issue(out, "CD-VALUE", location + ".present", param["value"] is not None,
                       value is not None)
    out.extend({"code": v.code, "path": v.node, "expected": "consistent AST references",
                "actual": v.detail} for v in check_hierarchy(result))
    return out


def check_case(case: dict[str, Any], result: ParseResult, raw: bytes) -> dict[str, Any]:
    comparison = compare_structure(case["expected_structure"], source_view(result))
    diffs = [asdict(d) for d in comparison.differences]
    # An omitted expectation is visible and fails this dedicated complete-source contract.
    diffs.extend({"path": p, "kind": "unchecked", "expected": "asserted", "actual": None}
                 for p in comparison.unchecked)
    diffs.extend({"path": "diagnostics", "kind": "syntax_error", "expected": [],
                  "actual": asdict(d)} for d in result.diagnostics if d.severity == "ERROR")
    traces = trace_issues(case, result, raw)
    return {"path": case["path"], "input_status": "MATCHED",
            "source_status": "FAIL" if diffs else "PASS",
            "trace_status": "FAIL" if traces else "PASS",
            "source_differences": diffs, "trace_issues": traces}


def run_cases(oracle: dict[str, Any], corpus: Path) -> tuple[list[dict[str, Any]],
                                                          dict[str, ParseResult]]:
    results = []
    parsed = {}
    expected_paths = {f["path"] for f in oracle["files"]}
    actual_paths = {p.relative_to(corpus).as_posix() for p in corpus.rglob("*")
                    if p.is_file() and p.suffix.lower() in (".jcl", ".prc", ".proc")}
    unexpected = sorted(actual_paths - expected_paths)
    for case in oracle["files"]:
        path = corpus / case["path"]
        if unexpected or not path.is_file() or sha256(path.read_bytes()) != case["sha256"]:
            results.append({"path": case["path"], "input_status": "MISSING_OR_CHANGED",
                            "source_status": "BLOCKED", "trace_status": "BLOCKED",
                            "source_differences": [], "trace_issues": [],
                            "unexpected_source_files": unexpected})
            continue
        raw = path.read_bytes()
        result = parse_file(path, encoding=case["encoding"], input_kind=case["input_kind"])
        parsed[case["path"]] = result
        results.append(check_case(case, result, raw))
    return results, parsed


def decisions(results: list[dict[str, Any]], reviews: dict[str, Any],
              mutations: dict[str, Any]) -> dict[str, Any]:
    source = Counter(r["source_status"] for r in results)
    trace = Counter(r["trace_status"] for r in results)
    pending = [r["path"] for r in reviews["files"] if r["status"] != "APPROVED"]
    mutation_ok = (mutations.get("total", 0) > 0 and not mutations.get("escaped")
                   and mutations.get("detected") == mutations.get("total"))
    assurance = "FAIL" if not mutation_ok else "PENDING" if pending else "PASS"
    source_status = "PASS" if source.get("PASS") == 48 and len(results) == 48 else "FAIL"
    trace_status = "PASS" if trace.get("PASS") == 48 and len(results) == 48 else "FAIL"
    return {"CD-SOURCE": {"status": source_status, "counts": dict(source)},
            "CD-TRACE": {"status": trace_status, "counts": dict(trace)},
            "CD-ASSURANCE": {"status": assurance, "pending_count": len(pending),
                             "pending": pending, "mutation_detection_pass": mutation_ok},
            "formal_acceptance": "PASS" if (source_status, trace_status, assurance)
            == ("PASS", "PASS", "PASS") else "FAIL"}

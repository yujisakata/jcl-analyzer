"""Harness adapter for the Step 4b Parser (stage 'syntactic', Golden View 'statements').

The adapter declares its scope explicitly. A case outside it is reported NOT_IMPLEMENTED instead of
being compared, so that an absent check can never pass vacuously (instruction 6-8). Out of scope:
  * categories whose structure checks are not implemented: PROC_PEND (block structure, nesting),
    JCLLIB_INCLUDE_SET (placement, limits), IF_THEN_ELSE (condition AST, nesting), COND
  * cases expecting a diagnostic code this build does not produce
  * cases expecting 'blocks' or an IF 'condition'
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jclprof.harness.adapters import AdapterOutput
from jclprof.harness.hierarchy import check_hierarchy
from jclprof.harness.loader import GoldenCase
from jclprof.lexer import LEX_CODES
from jclprof.parser.model import DDNode, ParseResult, StepNode
from jclprof.parser.parser import PARSE_CODES, parse_file

IN_SCOPE_CATEGORIES = frozenset({"JOB_EXEC_DD", "CONTINUATION_COLUMNS", "QUOTES_PARENTHESES",
                                 "DD_CONCATENATION", "GDG_DISP", "INSTREAM_DATA",
                                 "INVALID_UNRESOLVED"})
IMPLEMENTED_CODES = frozenset(PARSE_CODES) | frozenset(LEX_CODES)


def scope_gap(case: GoldenCase) -> str | None:
    if case.category not in IN_SCOPE_CATEGORIES:
        return f"Step 4b scope: structure checks for {case.category} are not implemented"
    missing = sorted({d["code"] for d in case.raw["expected_diagnostics"]["items"]}
                     - IMPLEMENTED_CODES)
    if missing:
        return f"Step 4b scope: diagnostics {missing} are not implemented"
    es: dict[str, Any] = case.raw["expected_structure"]
    if "blocks" in es:
        return "Step 4b scope: block structure (PROC/IF) is not implemented"
    if any("condition" in s for s in es.get("statements", [])):
        return "Step 4b scope: IF relational-expression AST is not implemented"
    return None


class SyntacticAdapter:
    stage = "syntactic"

    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        gap = scope_gap(case)
        if gap:
            raise NotImplementedError(gap)
        env = case.raw.get("environment", {})
        r = parse_file(input_path, encoding=self.encoding, jes=env.get("jes", "UNKNOWN"),
                       input_kind=case.raw["input_kind"])
        view = r.to_golden_view()
        view["hierarchy"] = hierarchy_view(r)
        return AdapterOutput(view=view, diagnostics=r.golden_diagnostics(),
                             invariants=[{"code": v.code, "node": v.node, "detail": v.detail}
                                         for v in check_hierarchy(r)])


# ---------------------------------------------------------------- hierarchy view (ADR-027)
def _dd_view(d: DDNode) -> dict[str, Any]:
    s = d.statement
    v: dict[str, Any] = {
        "name": s.name.text if s.name else (s.implicit_name if s.implicit else None),
        "line": s.span[0] if s.span else None,
        "concat_head": d.concat_head, "concat_index": d.concat_index,
    }
    if d.implicit:
        v["implicit"] = True
    if s.inline is not None:
        g = s.inline
        v["inline_data"] = {"records": list(g.records) if g.records else None,
                            "terminator": g.terminator}
    return v


def _step_view(st: StepNode) -> dict[str, Any]:
    span = st.exec_statement.span
    return {"name": st.name, "line": span[0] if span else None,
            "target": list(st.target) if st.target else None,
            "dds": [_dd_view(d) for d in st.dds]}


def hierarchy_view(r: ParseResult) -> dict[str, Any]:
    """JOB -> STEP -> DD tree of a ParseResult in Golden View form (docs/golden-view.md)."""
    by_id = {s.id: s for s in r.statements}
    jobs = []
    for j in r.jobs:
        procs = []
        for p in j.procedures:
            ps, pe = p.proc_statement.span, p.pend_statement.span if p.pend_statement else None
            procs.append({"name": p.name, "line": ps[0] if ps else None,
                          "end_line": pe[0] if pe else None,
                          "steps": [_step_view(s) for s in p.steps]})
        js = j.job_statement.span
        jobs.append({"name": j.name, "line": js[0] if js else None, "span": list(j.span),
                     "dds": [_dd_view(d) for d in j.job_level_dds],
                     "steps": [_step_view(s) for s in j.steps], "procedures": procs})
    out: dict[str, Any] = {"jobs": jobs}
    if r.input_kind == "proc_member":
        out["procedure_steps"] = [_step_view(s) for s in r.procedure_steps]
    outside: list[int] = []
    for i in r.outside_statements:
        sp = by_id[i].span if i in by_id else None
        if sp is not None:
            outside.append(sp[0])
    out["outside"] = sorted(outside)
    return out

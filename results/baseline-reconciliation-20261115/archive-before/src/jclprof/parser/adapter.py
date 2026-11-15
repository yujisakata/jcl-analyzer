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
from jclprof.harness.loader import GoldenCase
from jclprof.lexer import LEX_CODES
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
        return AdapterOutput(view=r.to_golden_view(), diagnostics=r.golden_diagnostics())

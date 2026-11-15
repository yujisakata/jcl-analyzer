"""H-05 Golden runner and result reporting.

Statuses are kept separate and are never merged into a single success rate:
  PASSED          executed, matches the expected result
  FAILED          executed, differs from the expected result (or the adapter crashed)
  BLOCKED         precondition or external dependency missing (blocked case, corpus absent/changed)
  NOT_IMPLEMENTED no analyzer adapter exists for the case's validation stage
  NOT_RUN         eligible but not executed (deselected)
verification_status is a run result: it is written to the run report, never to the definitions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jclprof.harness.adapters import StageAdapter
from jclprof.harness.comparator import Difference, compare_diagnostics, compare_structure
from jclprof.harness.loader import GoldenCase

STATUSES = ("PASSED", "FAILED", "BLOCKED", "NOT_IMPLEMENTED", "NOT_RUN")


@dataclass
class CaseResult:
    test_id: str
    category: str
    stage: str
    review_status: str
    status: str
    reason: str = ""
    differences: list[Difference] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)

    @property
    def assurance(self) -> str:
        """FORMAL only for reviewed/approved expectations; drafts are REFERENCE comparisons
        (Step 4a instruction D: matching an unapproved Golden is not formal quality assurance)."""
        return "FORMAL" if self.review_status in ("reviewed", "approved") else "REFERENCE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id, "category": self.category, "validation_stage": self.stage,
            "review_status": self.review_status, "verification_status": self.status,
            "assurance": self.assurance,
            "reason": self.reason,
            "differences": [d.__dict__ for d in self.differences],
            "unchecked": self.unchecked,
        }


@dataclass
class RunReport:
    results: list[CaseResult]

    def counts(self) -> dict[str, int]:
        c = dict.fromkeys(STATUSES, 0)
        for r in self.results:
            c[r.status] += 1
        return c

    def counts_by(self, attr: str) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self.results:
            row = out.setdefault(str(getattr(r, attr)), dict.fromkeys(STATUSES, 0))
            row[r.status] += 1
        return dict(sorted(out.items()))


def _corpus_precondition(case: GoldenCase, corpus_roots: dict[str, Path]) -> str | None:
    cs = case.raw.get("corpus_source")
    if not cs:
        return None
    root = corpus_roots.get(cs["root_id"])
    if root is None:
        return f"corpus root {cs['root_id']!r} not configured"
    p = Path(root) / cs["rel_path"]
    if not p.is_file():
        return f"corpus file missing: {cs['rel_path']}"
    if hashlib.sha256(p.read_bytes()).hexdigest() != cs["sha256"]:
        return f"corpus sha256 mismatch for {cs['rel_path']} (source changed since case design)"
    return None


def run_case(case: GoldenCase, adapters: dict[str, StageAdapter],
             corpus_roots: dict[str, Path]) -> CaseResult:
    r = CaseResult(case.test_id, case.category, case.stage, case.review_status, "NOT_RUN")
    if case.review_status == "blocked":
        r.status, r.reason = "BLOCKED", str(case.raw.get("blocked_reason", ""))
        return r
    pre = _corpus_precondition(case, corpus_roots)
    if pre:
        r.status, r.reason = "BLOCKED", pre
        return r
    adapter = adapters.get(case.stage)
    if adapter is None:
        r.status, r.reason = "NOT_IMPLEMENTED", f"no adapter for stage {case.stage!r}"
        return r
    input_path = case.resolve_input(corpus_roots)
    if input_path is None or not input_path.is_file():
        r.status, r.reason = "BLOCKED", f"input not available: {case.input_file}"
        return r
    try:
        out = adapter.run(case, input_path)
    except NotImplementedError as e:
        r.status, r.reason = "NOT_IMPLEMENTED", str(e) or "adapter not implemented"
        return r
    except Exception as e:  # an analyzer crash is a failure, never hidden
        r.status, r.reason = "FAILED", f"adapter raised {type(e).__name__}: {e}"
        return r
    s = compare_structure(case.raw["expected_structure"], out.view, scope=case.scope)
    d = compare_diagnostics(case.raw["expected_diagnostics"]["items"], out.diagnostics,
                            scope=case.scope)
    inv = [Difference(f"invariant.{v['code']}", "invariant", None,
                      {"node": v.get("node"), "detail": v.get("detail")})
           for v in out.invariants
           if case.scope is None or _in_scope_node(v, case.scope)]
    r.differences = s.differences + d.differences + inv
    r.unchecked = s.unchecked
    r.status = "PASSED" if not r.differences else "FAILED"
    return r


def _in_scope_node(v: dict[str, Any], scope: tuple[int, int]) -> bool:
    """Invariant violations carry no reliable line; for scoped corpus cases they are kept unless
    their node id encodes a line outside the scope (S00012 / T00012 / J00012 / R00012 / L12)."""
    node = str(v.get("node") or "")
    digits = "".join(ch for ch in node[1:6] if ch.isdigit()) if node[:1] in "STJRPL" else ""
    if not digits:
        return True
    return scope[0] <= int(digits) <= scope[1]


def run_suite(cases: list[GoldenCase], *, adapters: dict[str, StageAdapter],
              corpus_roots: dict[str, Path], select: set[str] | None = None) -> RunReport:
    results = []
    for c in cases:
        if select is not None and c.test_id not in select:
            results.append(CaseResult(c.test_id, c.category, c.stage, c.review_status, "NOT_RUN",
                                      "deselected"))
        else:
            results.append(run_case(c, adapters, corpus_roots))
    return RunReport(results)


def write_report(rep: RunReport, out_dir: Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "counts": rep.counts(),
        "counts_by_category": rep.counts_by("category"),
        "counts_by_stage": rep.counts_by("stage"),
        "counts_by_review_status": rep.counts_by("review_status"),
        "counts_by_assurance": rep.counts_by("assurance"),
        "results": [r.to_dict() for r in rep.results],
    }
    (out_dir / "golden_run.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    L = ["# Golden Test Run", "",
         "Statuses are reported separately and are not combined into a single rate.", "",
         "| " + " | ".join(STATUSES) + " |", "|" + "---|" * len(STATUSES),
         "| " + " | ".join(str(v) for v in rep.counts().values()) + " |", "",
         "## By assurance", "",
         "FORMAL = reviewed/approved expectations. "
         "REFERENCE = draft expectations (comparison only, "
         "not formal quality assurance).", "",
         "| Assurance | " + " | ".join(STATUSES) + " |", "|---|" + "---|" * len(STATUSES)]
    for a, row in rep.counts_by("assurance").items():
        L.append(f"| {a} | " + " | ".join(str(row[s]) for s in STATUSES) + " |")
    L += ["", "## By category", "", "| Category | " + " | ".join(STATUSES) + " |",
         "|---|" + "---|" * len(STATUSES)]
    for cat, row in rep.counts_by("category").items():
        L.append(f"| {cat} | " + " | ".join(str(row[s]) for s in STATUSES) + " |")
    L += ["", "## Cases", "", "| Test ID | Stage | Review | Assurance | Status | Reason |",
          "|---|---|---|---|---|---|"]
    for r in rep.results:
        L.append(f"| {r.test_id} | {r.stage} | {r.review_status} | {r.assurance} | {r.status} | "
                 f"{r.reason.replace('|', '/')} |")
    (out_dir / "golden_run.md").write_text("\n".join(L) + "\n", encoding="utf-8")

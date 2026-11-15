"""Gate A (development health) and Gate B (Parser formal acceptance) decisions (ADR-028).

Gate A answers "is development healthy?": nothing is broken that is not already a registered,
visible known defect. It may PASS with OPEN known defects, and says so.
Gate B answers "may Step 4b be accepted?": it FAILS while any in-scope defect is not CLOSED, any
in-scope Golden expectation is unapproved, unimplemented, blocked or failing, review-pending
expectations remain, or an in-scope syntactic case does not assert the hierarchy.
The functions here only classify results; tools/quality_gate.py runs the commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jclprof.harness.defects import KnownDefect, known_golden_failures, known_xfails

SCOPE_PATH = Path(__file__).resolve().parents[3] / "tests" / "ACCEPTANCE_SCOPE.yaml"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    data: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------- Gate A helpers
def classify_golden(results: list[dict[str, Any]], defects: list[KnownDefect]
                    ) -> tuple[list[str], dict[str, str], list[str]]:
    """(unexpected FAILED ids, {known FAILED id: defect}, stale ids registered but not FAILED)."""
    known = known_golden_failures(defects)
    ids = {r["test_id"]: r["verification_status"] for r in results}
    failed = [t for t, s in ids.items() if s == "FAILED"]
    unexpected = [t for t in failed if t not in known]
    known_failed = {t: known[t] for t in failed if t in known}
    stale = sorted(t for t in known if t in ids and ids[t] != "FAILED")
    return sorted(unexpected), known_failed, stale


def classify_xfails(xfailed: list[str], xpassed: list[str], defects: list[KnownDefect]
                    ) -> tuple[list[str], dict[str, str], list[str]]:
    """(unregistered xfail or xpass ids, {registered xfail id: defect}, registered but not seen)."""
    known = known_xfails(defects)
    unregistered = sorted([t for t in xfailed if t not in known] + list(xpassed))
    registered = {t: known[t] for t in xfailed if t in known}
    missing = sorted(t for t in known if t not in xfailed)
    return unregistered, registered, missing


# ---------------------------------------------------------------- Gate B
@dataclass(frozen=True)
class Scope:
    stages: tuple[str, ...]
    excluded_categories: tuple[str, ...]  # effective only if approved
    approved: bool


def load_scope(path: Path = SCOPE_PATH) -> Scope:
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    approved = d.get("status") == "APPROVED" and bool(d.get("approved_by"))
    excl = tuple(e["category"] for e in d.get("proposed_exclusions") or []) if approved else ()
    return Scope(tuple(d["in_scope_stages"]), excl, approved)


def in_scope(r: dict[str, Any], scope: Scope) -> bool:
    return r["validation_stage"] in scope.stages and r["category"] not in scope.excluded_categories


def acceptance_checks(*, dev_ok: bool, defects: list[KnownDefect],
                      golden: list[dict[str, Any]], pending: list[dict[str, Any]],
                      xfailed: list[str], scope: Scope) -> list[Check]:
    cases = [r for r in golden if in_scope(r, scope)]
    pend = [r for r in pending if in_scope(r, scope)]
    open_defects = [d for d in defects if d.scope == "STEP4B" and d.status != "CLOSED"]
    unapproved = [r["test_id"] for r in cases if r["review_status"] != "approved"]
    not_impl = [r["test_id"] for r in cases if r["verification_status"] == "NOT_IMPLEMENTED"]
    blocked = [r["test_id"] for r in cases if r["verification_status"] == "BLOCKED"]
    failed = [r["test_id"] for r in cases + pend if r["verification_status"] == "FAILED"]
    no_hier = [r["test_id"] for r in cases
               if r["validation_stage"] == "syntactic"
               and r["verification_status"] in ("PASSED", "FAILED")
               and "hierarchy" in r.get("unchecked", [])]
    by_sev: dict[str, list[str]] = {}
    for d in open_defects:
        by_sev.setdefault(d.severity, []).append(f"{d.id}({d.status})")
    return [
        Check("B0 gate-a", dev_ok, "Gate A must pass first"),
        Check("B1 known-defects", not open_defects,
              f"{len(open_defects)} in-scope defect(s) not CLOSED: {by_sev}" if open_defects
              else "none", {"defects": [d.id for d in open_defects]}),
        Check("B2 xfail", not xfailed, f"{len(xfailed)} xfail test(s) in the Analyzer suite",
              {"xfailed": xfailed}),
        Check("B3 golden-approved", not unapproved,
              f"{len(unapproved)}/{len(cases)} in-scope case(s) not approved (REFERENCE only)",
              {"unapproved": unapproved}),
        Check("B4 golden-implemented", not not_impl,
              f"{len(not_impl)} in-scope case(s) NOT_IMPLEMENTED", {"cases": not_impl}),
        Check("B5 golden-blocked", not blocked, f"{len(blocked)} in-scope case(s) BLOCKED",
              {"cases": blocked}),
        Check("B6 golden-failed", not failed, f"{len(failed)} in-scope case(s) FAILED "
              "(sealed + pending)", {"cases": failed}),
        Check("B7 pending-review", not pend,
              f"{len(pend)} review-pending case(s) in tests/golden_pending (unsealed)",
              {"cases": [r["test_id"] for r in pend]}),
        Check("B8 hierarchy-asserted", not no_hier,
              f"{len(no_hier)} executed in-scope syntactic case(s) do not assert the hierarchy",
              {"cases": no_hier}),
        Check("B9 scope-approved", scope.approved,
              "acceptance scope approved" if scope.approved else
              "tests/ACCEPTANCE_SCOPE.yaml is PROPOSED: no exclusion is effective"),
    ]

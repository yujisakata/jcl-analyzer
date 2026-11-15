"""Known-defect registry (R1 / ADR-028): tests/KNOWN_DEFECTS.yaml.

A known defect is a confirmed, unfixed problem. Registering it lets Gate A (development health)
pass while the defect stays visible; it never makes the defect pass Gate B (Parser acceptance).

Each defect lists exactly where it shows up:
  xfail_tests          pytest node ids marked xfail(strict=True) that reproduce it
  golden_cases         Golden case ids expected to be FAILED because of it
  invariant_signatures hierarchy violations (code + regular expression on the detail) it explains
Only OPEN defects explain failures. An entry whose evidence no longer fails is reported as stale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jclprof.harness.hierarchy import Violation

STATUSES = ("OPEN", "RESOLVED_PENDING_REVIEW", "CLOSED")
SEVERITIES = ("HIGH", "MEDIUM", "LOW")
SCOPES = ("STEP4B", "OUT_OF_SCOPE")
REGISTRY_PATH = Path(__file__).resolve().parents[3] / "tests" / "KNOWN_DEFECTS.yaml"


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Signature:
    code: str
    detail: str  # regular expression, searched in Violation.detail

    def matches(self, v: Violation) -> bool:
        return v.code == self.code and re.search(self.detail, v.detail) is not None


@dataclass(frozen=True)
class KnownDefect:
    id: str
    title: str
    severity: str
    scope: str
    status: str
    source: str
    xfail_tests: tuple[str, ...]
    golden_cases: tuple[str, ...]
    invariant_signatures: tuple[Signature, ...]

    @property
    def open(self) -> bool:
        return self.status == "OPEN"


_KEYS = {"id", "title", "severity", "scope", "status", "source", "xfail_tests", "golden_cases",
         "invariant_signatures", "notes"}


def _parse(d: Any, i: int) -> KnownDefect:
    if not isinstance(d, dict):
        raise RegistryError(f"defects[{i}]: expected a mapping")
    extra = set(d) - _KEYS
    missing = {"id", "title", "severity", "scope", "status", "source"} - set(d)
    if extra or missing:
        raise RegistryError(f"defects[{i}]: unknown keys {sorted(extra)}, "
                            f"missing {sorted(missing)}")
    for key, allowed in (("status", STATUSES), ("severity", SEVERITIES), ("scope", SCOPES)):
        if d[key] not in allowed:
            raise RegistryError(f"{d['id']}: {key} must be one of {allowed}, not {d[key]!r}")
    sigs = []
    for s in d.get("invariant_signatures") or []:
        if not isinstance(s, dict) or set(s) != {"code", "detail"}:
            raise RegistryError(f"{d['id']}: invariant signature needs exactly code and detail")
        re.compile(s["detail"])
        sigs.append(Signature(str(s["code"]), str(s["detail"])))
    return KnownDefect(str(d["id"]), str(d["title"]), d["severity"], d["scope"], d["status"],
                       str(d["source"]), tuple(d.get("xfail_tests") or ()),
                       tuple(d.get("golden_cases") or ()), tuple(sigs))


def load_known_defects(path: Path = REGISTRY_PATH) -> list[KnownDefect]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("schema_version") != 1:
        raise RegistryError("KNOWN_DEFECTS.yaml: schema_version 1 required")
    out = [_parse(d, i) for i, d in enumerate(doc.get("defects") or [])]
    ids = [d.id for d in out]
    if len(ids) != len(set(ids)):
        raise RegistryError(f"duplicate defect ids: {ids}")
    return out


def explain(violations: list[Violation], defects: list[KnownDefect]
            ) -> tuple[dict[str, list[Violation]], list[Violation]]:
    """Split violations into those explained by an OPEN defect signature and the rest."""
    explained: dict[str, list[Violation]] = {}
    rest: list[Violation] = []
    for v in violations:
        d = next((d for d in defects if d.open and any(s.matches(v) for s in
                                                        d.invariant_signatures)), None)
        if d is None:
            rest.append(v)
        else:
            explained.setdefault(d.id, []).append(v)
    return explained, rest


def known_golden_failures(defects: list[KnownDefect]) -> dict[str, str]:
    """Golden case id -> OPEN defect id expected to make it fail."""
    return {c: d.id for d in defects if d.open for c in d.golden_cases}


def known_xfails(defects: list[KnownDefect]) -> dict[str, str]:
    """pytest node id -> OPEN defect id."""
    return {t: d.id for d in defects if d.open for t in d.xfail_tests}

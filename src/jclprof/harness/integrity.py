"""H-04 Golden Integrity.

`seal()` is an explicit, human-initiated action (CLI `golden-seal --by NAME`). It writes
MANIFEST.json (SHA-256 of every file in the suite plus a per-case hash) and a baseline copy under
.baseline/ used to show diffs. `check_integrity()` is read-only: it never updates the manifest
or any golden file, so a test run can never "accept" a changed expected value.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

MANIFEST = "MANIFEST.json"
BASELINE = ".baseline"
_EXCLUDED_TOP = {MANIFEST, BASELINE}


@dataclass(frozen=True)
class FileChange:
    path: str
    diff: str


@dataclass(frozen=True)
class CaseChange:
    test_id: str
    change: str  # added | removed | modified
    approved: bool


@dataclass
class IntegrityReport:
    manifest_missing: bool = False
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[FileChange] = field(default_factory=list)
    case_changes: list[CaseChange] = field(default_factory=list)
    approved_violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.manifest_missing or self.added or self.removed or self.modified)

    def summary(self) -> str:
        if self.manifest_missing:
            return "MANIFEST.json missing: suite has never been sealed"
        parts = [f"added={self.added}", f"removed={self.removed}",
                 f"modified={[m.path for m in self.modified]}",
                 f"case_changes={[(c.test_id, c.change) for c in self.case_changes]}",
                 f"approved_violations={self.approved_violations}"]
        return "; ".join(parts)


def _files(suite: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in sorted(suite.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(suite).as_posix()
        if rel.split("/", 1)[0] in _EXCLUDED_TOP:
            continue
        out[rel] = p
    return out


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _cases(suite: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for f in sorted((suite / "cases").glob("*.yaml")):
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        for c in (doc or {}).get("cases", []) if isinstance(doc, dict) else []:
            if isinstance(c, dict) and "test_id" in c:
                out[str(c["test_id"])] = c
    return out


def _case_hash(c: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def seal(suite: Path, *, sealed_by: str) -> Path:
    suite = Path(suite)
    files = _files(suite)
    cases = _cases(suite)
    manifest = {
        "schema_version": 1,
        "sealed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sealed_by": sealed_by,
        "files": {rel: {"sha256": _sha(p), "size": p.stat().st_size} for rel, p in files.items()},
        "cases": {tid: {"sha256": _case_hash(c), "review_status": c.get("review_status"),
                        "change_log_entries": len(c.get("change_log", []))}
                  for tid, c in sorted(cases.items())},
    }
    base = suite / BASELINE
    if base.exists():
        shutil.rmtree(base)
    for rel, p in files.items():
        dst = base / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
    out = suite / MANIFEST
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _diff(suite: Path, rel: str, current: Path) -> str:
    base = suite / BASELINE / rel
    if not base.is_file():
        return "(no baseline copy available)"
    try:
        a = base.read_text(encoding="utf-8").splitlines(keepends=True)
        b = current.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return "(binary content changed)"
    return "".join(difflib.unified_diff(a, b, f"sealed/{rel}", f"current/{rel}"))


def check_integrity(suite: Path) -> IntegrityReport:
    suite = Path(suite)
    rep = IntegrityReport()
    mpath = suite / MANIFEST
    if not mpath.is_file():
        rep.manifest_missing = True
        return rep
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    sealed: dict[str, Any] = manifest["files"]
    current = _files(suite)
    rep.added = sorted(set(current) - set(sealed))
    rep.removed = sorted(set(sealed) - set(current))
    for rel in sorted(set(current) & set(sealed)):
        if _sha(current[rel]) != sealed[rel]["sha256"]:
            rep.modified.append(FileChange(rel, _diff(suite, rel, current[rel])))
    sealed_cases: dict[str, Any] = manifest.get("cases", {})
    now_cases = _cases(suite)
    for tid in sorted(set(sealed_cases) | set(now_cases)):
        old, new = sealed_cases.get(tid), now_cases.get(tid)
        was_approved = bool(old and old.get("review_status") == "approved")
        if old is None:
            rep.case_changes.append(CaseChange(tid, "added", False))
        elif new is None:
            rep.case_changes.append(CaseChange(tid, "removed", was_approved))
            if was_approved:
                rep.approved_violations.append(tid)
        elif _case_hash(new) != old["sha256"]:
            rep.case_changes.append(CaseChange(tid, "modified", was_approved))
            if was_approved and len(new.get("change_log", [])) <= old.get("change_log_entries", 0):
                rep.approved_violations.append(tid)
    return rep

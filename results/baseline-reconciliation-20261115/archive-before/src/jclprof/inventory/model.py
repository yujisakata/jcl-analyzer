"""Typed inventory model (requirements §4: SourceFile, Diagnostic)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from jclprof import SCHEMA_VERSION, __version__
from jclprof.diagnostics import Diagnostic
from jclprof.inventory.physical import PhysicalStats

EncodingStatus = str  # OK | DECODE_FAILED | ENCODING_UNDETERMINED | SKIPPED_TOO_LARGE | READ_FAILED


@dataclass(frozen=True)
class SourceFile:
    source_id: str
    root_id: str
    rel_path: str
    top_dir: str
    asset_type: str
    classification_rule: str | None
    size_bytes: int
    sha256: str | None
    encoding: str | None
    encoding_basis: str  # override:<pattern> | profile:<name> | default
    encoding_status: EncodingStatus
    physical: PhysicalStats | None
    member_name: str | None
    member_name_valid: bool | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "root_id": self.root_id,
            "rel_path": self.rel_path,
            "top_dir": self.top_dir,
            "asset_type": self.asset_type,
            "classification_rule": self.classification_rule,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "encoding": self.encoding,
            "encoding_basis": self.encoding_basis,
            "encoding_status": self.encoding_status,
            "physical": self.physical.to_dict() if self.physical else None,
            "member_name": self.member_name,
            "member_name_valid": self.member_name_valid,
        }


@dataclass(frozen=True)
class ExcludedFile:
    root_id: str
    rel_path: str
    rule_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"root_id": self.root_id, "rel_path": self.rel_path,
                "rule_id": self.rule_id, "reason": self.reason}


@dataclass(frozen=True)
class DuplicateMember:
    asset_type: str
    member_name: str
    rel_paths: tuple[str, ...]  # "root_id:rel_path", sorted
    identical_content: bool

    def to_dict(self) -> dict[str, Any]:
        return {"asset_type": self.asset_type, "member_name": self.member_name,
                "rel_paths": list(self.rel_paths), "identical_content": self.identical_content}


@dataclass(frozen=True)
class RootInfo:
    id: str
    path: str


@dataclass
class InventoryResult:
    roots: tuple[RootInfo, ...]
    source_files: list[SourceFile] = field(default_factory=list)
    excluded: list[ExcludedFile] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    duplicate_members: list[DuplicateMember] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(d.severity == "ERROR" for d in self.diagnostics)

    def summary(self) -> dict[str, Any]:
        def sorted_counts(c: Counter[str]) -> dict[str, int]:
            return dict(sorted(c.items()))

        return {
            "files_seen": len(self.source_files) + len(self.excluded),
            "files_registered": len(self.source_files),
            "files_excluded": len(self.excluded),
            "total_bytes": sum(s.size_bytes for s in self.source_files),
            "asset_type_counts": sorted_counts(Counter(s.asset_type for s in self.source_files)),
            "encoding_status_counts": sorted_counts(
                Counter(s.encoding_status for s in self.source_files)
            ),
            "diagnostic_counts": sorted_counts(Counter(d.code for d in self.diagnostics)),
            "severity_counts": sorted_counts(Counter(d.severity for d in self.diagnostics)),
            "duplicate_member_groups": len(self.duplicate_members),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "tool_version": __version__,
            "roots": [{"id": r.id, "path": r.path} for r in self.roots],
            "summary": self.summary(),
            "source_files": [s.to_dict() for s in self.source_files],
            "excluded": [e.to_dict() for e in self.excluded],
            "duplicate_members": [d.to_dict() for d in self.duplicate_members],
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

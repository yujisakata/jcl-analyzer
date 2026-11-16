"""Explicit library context: logical DSN -> local folder (ADR-010, contract CA-04).

A member is looked up only in folders that an explicit mapping names. The DSN text is never
turned into a path. Zero candidates -> NOT_FOUND, several -> AMBIGUOUS (never "pick the first").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import ConfigError, DatasetMapping, ProfilerConfig, _dataset


@dataclass(frozen=True)
class MemberLookup:
    result: str  # FOUND | NOT_FOUND | UNMAPPED | AMBIGUOUS
    candidates: tuple[str, ...]  # root-relative POSIX paths
    alias_of: str | None = None
    path: Path | None = None
    rel: str | None = None


@dataclass(frozen=True)
class LibraryContext:
    mappings: tuple[DatasetMapping, ...]
    roots: dict[str, Path]
    basis: str  # CONFIG | UNCONFIRMED_CONTRACT_CONTEXT | TEST ...
    note: str = ""

    @classmethod
    def from_config(cls, cfg: ProfilerConfig) -> LibraryContext:
        return cls(cfg.datasets, {r.id: r.path for r in cfg.roots}, "CONFIG",
                   "config/profiler.yaml datasets")

    def mapping(self, dsn: str) -> DatasetMapping | None:
        return next((m for m in self.mappings if m.dsn == dsn), None)

    def lookup(self, dsn: str, member: str) -> MemberLookup:
        m = self.mapping(dsn)
        if m is None:
            return MemberLookup("UNMAPPED", ())
        root = self.roots.get(m.root)
        if root is None:
            return MemberLookup("UNMAPPED", ())
        alias_of = m.aliases.get(member)
        target = alias_of or member
        folder = root / m.path
        found: list[tuple[str, Path]] = []
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if not p.is_file():
                    continue
                stem = p.name.partition(".")[0]
                suffix = p.name[len(stem):].lower()
                if stem.upper() != target:
                    continue
                if m.member_suffixes and suffix not in {s.lower() for s in m.member_suffixes}:
                    continue
                found.append((p.relative_to(root).as_posix(), p))
        if not found:
            return MemberLookup("NOT_FOUND", (), alias_of)
        if len(found) > 1:
            return MemberLookup("AMBIGUOUS", tuple(r for r, _ in found), alias_of)
        rel, path = found[0]
        return MemberLookup("FOUND", (rel,), alias_of, path, rel)


def load_library_context(path: Path, roots: dict[str, Path]) -> LibraryContext:
    """Load an overlay context file (e.g. config/contexts/cd4-contract-context.yaml)."""
    data: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ConfigError(f"{path}: expected schema_version 1")
    status = data.get("status")
    if not isinstance(status, str) or not status:
        raise ConfigError(f"{path}: 'status' is required (e.g. UNCONFIRMED_CONTRACT_CONTEXT)")
    maps = tuple(_dataset(x, f"datasets[{i}]", set(roots))
                 for i, x in enumerate(data.get("datasets", [])))
    return LibraryContext(maps, dict(roots), status, str(data.get("basis_note", "")))

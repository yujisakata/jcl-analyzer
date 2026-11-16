"""Explicit library context: logical DSN -> local folder (ADR-010, contract CA-04).

A member is looked up only in folders that an explicit mapping names. The DSN text is never
turned into a path. Lookup results:

* FOUND             exactly one candidate in an inspectable folder
* NOT_FOUND         the folder exists and was listed, and holds no candidate
* AMBIGUOUS         several local candidates in one folder (never "pick the first")
* UNMAPPED          no mapping for the DSN
* UNAVAILABLE       a mapping exists but its folder cannot be inspected (root id unknown, folder
                    missing, not a directory, or listing failed). This is NOT a known absence
                    (CD-4R F01): the member may well be in that library.
* DUPLICATE_MAPPING more than one mapping for the DSN; no list order is treated as a priority
                    (CD-4R F02). The public loader rejects such files; a context built directly
                    in code still never resolves from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import ConfigError, DatasetMapping, ProfilerConfig, _dataset


@dataclass(frozen=True)
class MemberLookup:
    result: str  # FOUND | NOT_FOUND | AMBIGUOUS | UNMAPPED | UNAVAILABLE | DUPLICATE_MAPPING
    candidates: tuple[str, ...]  # root-relative POSIX paths (or "root:path" for mappings)
    alias_of: str | None = None
    path: Path | None = None
    rel: str | None = None
    reason: str = ""


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

    def mappings_for(self, dsn: str) -> tuple[DatasetMapping, ...]:
        return tuple(m for m in self.mappings if m.dsn == dsn)

    def duplicate_dsns(self) -> tuple[str, ...]:
        seen: set[str] = set()
        dup: list[str] = []
        for m in self.mappings:
            if m.dsn in seen and m.dsn not in dup:
                dup.append(m.dsn)
            seen.add(m.dsn)
        return tuple(dup)

    def lookup(self, dsn: str, member: str) -> MemberLookup:
        ms = self.mappings_for(dsn)
        if not ms:
            return MemberLookup("UNMAPPED", ())
        if len(ms) > 1:
            places = tuple(sorted(f"{m.root}:{m.path}" for m in ms))
            return MemberLookup("DUPLICATE_MAPPING", places,
                                reason=f"{len(ms)} mappings for {dsn}")
        m = ms[0]
        alias_of = m.aliases.get(member)
        target = alias_of or member
        root = self.roots.get(m.root)
        if root is None:
            return MemberLookup("UNAVAILABLE", (), alias_of, reason=f"root id {m.root!r} unknown")
        folder = root / m.path
        suffixes = {s.lower() for s in m.member_suffixes}
        found: list[tuple[str, Path]] = []
        try:
            if not folder.exists():
                return MemberLookup("UNAVAILABLE", (), alias_of,
                                    reason=f"{m.root}:{m.path} does not exist")
            if not folder.is_dir():
                return MemberLookup("UNAVAILABLE", (), alias_of,
                                    reason=f"{m.root}:{m.path} is not a directory")
            for p in sorted(folder.iterdir()):
                if not p.is_file():
                    continue
                stem = p.name.partition(".")[0]
                suffix = p.name[len(stem):].lower()
                if stem.upper() != target:
                    continue
                if suffixes and suffix not in suffixes:
                    continue
                found.append((p.relative_to(root).as_posix(), p))
        except OSError as exc:
            return MemberLookup("UNAVAILABLE", (), alias_of,
                                reason=f"{m.root}:{m.path} cannot be listed "
                                       f"({type(exc).__name__})")
        if not found:
            return MemberLookup("NOT_FOUND", (), alias_of)
        if len(found) > 1:
            return MemberLookup("AMBIGUOUS", tuple(r for r, _ in found), alias_of)
        rel, path = found[0]
        return MemberLookup("FOUND", (rel,), alias_of, path, rel)


def load_library_context(path: Path, roots: dict[str, Path]) -> LibraryContext:
    """Load an overlay context file (YAML or JSON, e.g. config/contexts/cd4-contract-context.yaml).

    A DSN mapped more than once is rejected (CD-4R F02), as config/profiler.yaml already does.
    """
    data: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ConfigError(f"{path}: expected schema_version 1")
    status = data.get("status")
    if not isinstance(status, str) or not status:
        raise ConfigError(f"{path}: 'status' is required (e.g. UNCONFIRMED_CONTRACT_CONTEXT)")
    raw = data.get("datasets", [])
    if not isinstance(raw, list):
        raise ConfigError(f"{path}: 'datasets' must be a list")
    maps = tuple(_dataset(x, f"datasets[{i}]", set(roots)) for i, x in enumerate(raw))
    ctx = LibraryContext(maps, dict(roots), status, str(data.get("basis_note", "")))
    dup = ctx.duplicate_dsns()
    if dup:
        raise ConfigError(f"{path}: datasets: duplicate dsn {', '.join(dup)}")
    return ctx

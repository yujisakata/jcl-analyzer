"""Collect and register every file under the configured roots (FR-01, CTX-01/02).

Invariants:
* Source files are opened only in binary read mode (ADR-006).
* Every file found ends up in ``source_files`` or ``excluded`` (registration rate 100%).
* Output order is (root order, relative POSIX path) regardless of traversal order.
* Encodings are never guessed (ADR-004); no JCL syntax is interpreted (ADR-003).
"""

from __future__ import annotations

import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path

from jclprof.context.config import ProfilerConfig, Root
from jclprof.context.globmatch import glob_match
from jclprof.diagnostics import Diagnostic, make_diagnostic
from jclprof.ids import source_id as make_source_id
from jclprof.inventory.model import (
    DuplicateMember,
    ExcludedFile,
    InventoryResult,
    RootInfo,
    SourceFile,
)
from jclprof.inventory.physical import compute_physical, split_records

# MVS-MEM-001 (status PENDING, conservative): 1-8 chars, first alpha/national, then alnum/national.
_MEMBER_RE = re.compile(r"\A[A-Z@#$][A-Z0-9@#$]{0,7}\Z")
_BYTE_TERM = re.compile(rb"\r\n|\r|\n")
_HASH_CHUNK = 1024 * 1024


class _NotDecoded(Exception):
    """Internal control flow: file intentionally not decoded (encoding undetermined)."""


def read_source_bytes(path: Path) -> bytes:
    """Read a source file in binary read-only mode. Patched in tests to simulate failures."""
    with open(path, "rb") as f:
        return f.read()


def hash_source_stream(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _walk(root: Root) -> tuple[list[str], list[str]]:
    """Return (regular file rel paths, symlink/junction rel paths), both unsorted."""
    files: list[str] = []
    links: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root.path, followlinks=False):
        base = Path(dirpath)
        kept_dirs = []
        for d in sorted(dirnames):
            p = base / d
            if p.is_symlink() or p.is_junction():
                links.append(p.relative_to(root.path).as_posix())
            else:
                kept_dirs.append(d)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            p = base / name
            rel = p.relative_to(root.path).as_posix()
            (links if p.is_symlink() else files).append(rel)
    return files, links


def _byte_location(data: bytes, offset: int) -> tuple[int, int]:
    """1-based (line, column) of a byte offset, using CR LF / LF / CR record terminators."""
    line = 1
    line_start = 0
    for m in _BYTE_TERM.finditer(data, 0, offset):
        if m.end() > offset:
            break
        line += 1
        line_start = m.end()
    return line, offset - line_start + 1


def _member_name(rel_path: str) -> tuple[str | None, bool]:
    filename = rel_path.rsplit("/", 1)[-1]
    stem = filename.split(".", 1)[0].upper()
    if not stem:
        return None, False
    return stem, bool(_MEMBER_RE.match(stem))


class _Collector:
    def __init__(self, cfg: ProfilerConfig) -> None:
        self.cfg = cfg
        self.diags: list[Diagnostic] = []

    def _diag(self, code: str, sf_root: str, rel: str, sid: str, message: str,
              line: int | None = None, column: int | None = None) -> None:
        self.diags.append(make_diagnostic(code, root_id=sf_root, rel_path=rel, source_id=sid,
                                          message=message, line=line, column=column))

    def _classify(self, rel: str) -> tuple[str, str | None]:
        for rule in self.cfg.classification:
            if glob_match(rule.pattern, rel):
                return rule.asset_type, rule.id
        return "UNKNOWN", None

    def _encoding_for(self, rel: str, asset_type: str) -> tuple[str | None, str]:
        """ADR-009: override (first match) > asset type profile > default. None = undetermined."""
        for o in self.cfg.encoding_overrides:
            if glob_match(o.pattern, rel):
                return o.encoding, f"override:{o.pattern}"
        at = self.cfg.asset_types.get(asset_type)
        if at is not None and at.encoding_profile is not None:
            return self.cfg.encoding_profiles[at.encoding_profile], f"profile:{at.encoding_profile}"
        return self.cfg.default_encoding, "default"

    def register(self, root: Root, rel: str) -> SourceFile:
        path = root.path / rel
        sid = make_source_id(root.id, rel)
        asset_type, rule_id = self._classify(rel)
        encoding, encoding_basis = self._encoding_for(rel, asset_type)
        top_dir = rel.split("/", 1)[0] if "/" in rel else ""
        at = self.cfg.asset_types.get(asset_type)

        if asset_type == "UNKNOWN":
            self._diag("INV-W001", root.id, rel, sid, f"No classification rule matched {rel!r}")

        member: str | None = None
        member_valid: bool | None = None
        if at is not None and at.member_like:
            member, member_valid = _member_name(rel)
            if not member_valid:
                self._diag("INV-I001", root.id, rel, sid,
                           f"Derived member name {member!r} does not satisfy MVS-MEM-001")

        size = 0
        sha: str | None = None
        physical = None
        try:
            size = path.stat().st_size
            if size > self.cfg.max_decode_bytes:
                sha = hash_source_stream(path)
                status = "SKIPPED_TOO_LARGE"
                self._diag("INV-W004", root.id, rel, sid,
                           f"{size} bytes > max_decode_bytes={self.cfg.max_decode_bytes}")
            else:
                data = read_source_bytes(path)
                size = len(data)
                sha = hashlib.sha256(data).hexdigest()
                if encoding is None:
                    status = "ENCODING_UNDETERMINED"
                    self._diag("INV-I004", root.id, rel, sid,
                               f"Encoding undetermined ({encoding_basis}); not decoded")
                    raise _NotDecoded
                try:
                    text = data.decode(encoding, errors="strict")
                except UnicodeDecodeError as e:
                    status = "DECODE_FAILED"
                    line, col = _byte_location(data, e.start)
                    self._diag("INV-W002", root.id, rel, sid,
                               f"Cannot decode as {encoding}: byte 0x{data[e.start]:02X} "
                               f"at offset {e.start} ({e.reason})", line, col)
                else:
                    status = "OK"
                    physical = compute_physical(text)
                    self._physical_checks(root.id, rel, sid, text, physical.line_terminator,
                                          at.fixed_record_length if at else None)
        except _NotDecoded:
            pass
        except OSError as e:
            status = "READ_FAILED"
            sha = None
            self._diag("INV-E001", root.id, rel, sid, f"{type(e).__name__}: {e}")

        return SourceFile(
            source_id=sid, root_id=root.id, rel_path=rel, top_dir=top_dir,
            asset_type=asset_type, classification_rule=rule_id, size_bytes=size, sha256=sha,
            encoding=encoding, encoding_basis=encoding_basis, encoding_status=status,
            physical=physical,
            member_name=member, member_name_valid=member_valid,
        )

    def _physical_checks(self, root_id: str, rel: str, sid: str, text: str, term: str,
                         fixed_len: int | None) -> None:
        if term in ("MIXED", "CR"):
            self._diag("INV-I003", root_id, rel, sid, f"Line terminators: {term}")
        if fixed_len is None:
            return
        records, _, _ = split_records(text)
        for n, rec in enumerate(records, start=1):
            if len(rec) > fixed_len:
                self._diag("INV-W005", root_id, rel, sid,
                           f"Record length {len(rec)} > {fixed_len}", n, fixed_len + 1)
            if "\t" in rec:
                self._diag("INV-W006", root_id, rel, sid, "TAB character", n, rec.index("\t") + 1)


def collect(cfg: ProfilerConfig) -> InventoryResult:
    c = _Collector(cfg)
    result = InventoryResult(roots=tuple(RootInfo(r.id, r.path.as_posix()) for r in cfg.roots))
    for root in cfg.roots:
        files, links = _walk(root)
        for rel in sorted(links):
            result.excluded.append(ExcludedFile(root.id, rel, "SYMLINK",
                                                "symbolic links are not followed"))
        for rel in sorted(files):
            rule = next((e for e in cfg.exclude if glob_match(e.pattern, rel)), None)
            if rule is not None:
                result.excluded.append(ExcludedFile(root.id, rel, rule.id, rule.reason))
                continue
            result.source_files.append(c.register(root, rel))
    root_order = {r.id: i for i, r in enumerate(cfg.roots)}
    result.excluded.sort(key=lambda e: (root_order[e.root_id], e.rel_path))

    # Duplicate member names within one asset type (across all roots) -> INV-W003.
    groups: dict[tuple[str, str], list[SourceFile]] = defaultdict(list)
    for s in result.source_files:
        if s.member_name is not None:
            groups[(s.asset_type, s.member_name)].append(s)
    for (asset_type, member), members in sorted(groups.items()):
        if len(members) < 2:
            continue
        refs = tuple(sorted(f"{m.root_id}:{m.rel_path}" for m in members))
        hashes = {m.sha256 for m in members}
        identical = len(hashes) == 1 and None not in hashes
        result.duplicate_members.append(DuplicateMember(asset_type, member, refs, identical))
        for m in members:
            others = ", ".join(r for r in refs if r != f"{m.root_id}:{m.rel_path}")
            c._diag("INV-W003", m.root_id, m.rel_path, m.source_id,
                    f"{asset_type} member {member} also at: {others} "
                    f"(identical content: {identical})")

    c.diags.sort(key=lambda d: (root_order[d.root_id], d.rel_path, d.line or 0,
                                d.column or 0, d.code, d.diag_id))
    result.diagnostics = c.diags
    return result

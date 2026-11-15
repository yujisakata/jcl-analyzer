"""Physical record statistics of a decoded text file.

Only CR LF, LF and CR terminate records (unlike ``str.splitlines``). The record-prefix histogram
classifies records by their leading characters only (rules JCL-REC-001/003/004); it does not
decide whether a record is a JCL statement — records inside in-stream data may also start with
``//``. That distinction belongs to the Lexer (Step 4, ADR-003).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

_TERM = re.compile(r"\r\n|\r|\n")

PREFIX_KEYS = ("SLASH_SLASH_STAR", "SLASH_SLASH", "SLASH_STAR", "BLANK", "OTHER")
JCL_RECORD_LENGTH = 80  # JCL-REC-004
SEQ_AREA = slice(72, 80)  # columns 73-80, JCL-REC-003


@dataclass(frozen=True)
class PhysicalStats:
    record_count: int
    line_terminator: str  # CRLF | LF | CR | MIXED | NONE
    ends_with_terminator: bool
    max_record_length: int
    records_over_80: int
    over_80_lines: tuple[int, ...]
    tab_lines: tuple[int, ...]
    seq_area_records: int
    prefix_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["over_80_lines"] = list(self.over_80_lines)
        d["tab_lines"] = list(self.tab_lines)
        return d


def split_records(text: str) -> tuple[list[str], set[str], bool]:
    """Return (records, terminator kinds seen, ends_with_terminator)."""
    records: list[str] = []
    kinds: set[str] = set()
    pos = 0
    for m in _TERM.finditer(text):
        records.append(text[pos : m.start()])
        kinds.add({"\r\n": "CRLF", "\n": "LF", "\r": "CR"}[m.group()])
        pos = m.end()
    ends = pos == len(text) and bool(records)
    if pos < len(text):
        records.append(text[pos:])
    return records, kinds, ends


def classify_prefix(record: str) -> str:
    if record.startswith("//*"):
        return "SLASH_SLASH_STAR"
    if record.startswith("//"):
        return "SLASH_SLASH"
    if record.startswith("/*"):
        return "SLASH_STAR"
    if record.strip(" ") == "":
        return "BLANK"
    return "OTHER"


def compute_physical(text: str) -> PhysicalStats:
    records, kinds, ends = split_records(text)
    if not kinds:
        term = "NONE"
    elif len(kinds) == 1:
        term = next(iter(kinds))
    else:
        term = "MIXED"
    prefix = dict.fromkeys(PREFIX_KEYS, 0)
    over: list[int] = []
    tabs: list[int] = []
    seq = 0
    max_len = 0
    for n, rec in enumerate(records, start=1):
        prefix[classify_prefix(rec)] += 1
        max_len = max(max_len, len(rec))
        if len(rec) > JCL_RECORD_LENGTH:
            over.append(n)
        if "\t" in rec:
            tabs.append(n)
        if len(rec) > SEQ_AREA.start and rec[SEQ_AREA].strip(" "):
            seq += 1
    return PhysicalStats(
        record_count=len(records),
        line_terminator=term,
        ends_with_terminator=ends,
        max_record_length=max_len,
        records_over_80=len(over),
        over_80_lines=tuple(over),
        tab_lines=tuple(tabs),
        seq_area_records=seq,
        prefix_counts=prefix,
    )

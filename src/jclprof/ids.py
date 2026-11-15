"""Reproducible identifiers (requirements §4, ADR-005).

Identifiers are derived only from source identity (root id + relative path) and content/position,
never from traversal order, time or randomness.
"""

from __future__ import annotations

import hashlib


def _h(*parts: str) -> str:
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:16]


def source_id(root_id: str, rel_path: str) -> str:
    return "SRC-" + _h(root_id, rel_path)


def diagnostic_id(code: str, source: str, line: int | None, column: int | None, detail: str) -> str:
    return "DIAG-" + _h(code, source, str(line or 0), str(column or 0), detail)

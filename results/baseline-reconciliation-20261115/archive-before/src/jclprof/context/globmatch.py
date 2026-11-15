"""Deterministic glob matching on root-relative POSIX paths.

Semantics (documented and tested, independent of the host OS):
  ``**/``  zero or more whole path segments
  ``**``   any characters including ``/``
  ``*``    any characters within one segment
  ``?``    exactly one character other than ``/``
Every other character is literal (no ``[...]`` character classes).
"""

from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=512)
def _compile(pattern: str, case_insensitive: bool) -> re.Pattern[str]:
    out: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        if pattern.startswith("**/", i):
            out.append("(?:[^/]*/)*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    flags = re.DOTALL | (re.IGNORECASE if case_insensitive else 0)
    return re.compile(r"\A" + "".join(out) + r"\Z", flags)


def glob_match(pattern: str, rel_path: str, *, case_insensitive: bool = True) -> bool:
    return _compile(pattern, case_insensitive).match(rel_path) is not None

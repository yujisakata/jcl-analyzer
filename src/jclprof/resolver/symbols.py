"""JCL symbol substitution for the CD-4 resolver (JCL-SYM-001..004).

* A symbol is '&' (not '&&') followed by 1-8 alphanumeric/national characters, ended by any other
  character; a period directly after it is a delimiter and is removed (JCL-SYM-003, p.43).
* Undefined -> the text stays literal (never an empty string) and the use is UNDEFINED (POL-002).
* SYSUID is a system symbol whose value depends on the execution environment (POL-003).
* '&&' is kept as written (temporary data set names, JCL-SYN-003).
"""

from __future__ import annotations

import re
from collections.abc import Callable

from jclprof.resolver.model import SourceRef, SymbolDef, SymbolUse

_SYM = re.compile(r"&([A-Z@#$][A-Z0-9@#$]{0,7})(?![A-Z0-9@#$])(\.?)")
ENVIRONMENT_SYMBOLS = frozenset({"SYSUID"})  # observed in CardDemo; values come from the system

Lookup = Callable[[str], SymbolDef | None]


def substitute(text: str, lookup: Lookup, used_at: SourceRef) -> tuple[str, list[SymbolUse]]:
    uses: list[SymbolUse] = []
    out: list[str] = []
    i = 0
    while i < len(text):
        if text.startswith("&&", i):
            out.append("&&")
            i += 2
            continue
        m = _SYM.match(text, i) if text[i] == "&" else None
        if m is None:
            out.append(text[i])
            i += 1
            continue
        name = m.group(1)
        d = lookup(name)
        if d is not None:
            if d.value is None:
                uses.append(SymbolUse(name, "NULLIFIED", None, d.defined_by, used_at))
                out.append("")
            else:
                uses.append(SymbolUse(name, "RESOLVED", d.value, d.defined_by, used_at))
                out.append(d.value)
        elif name in ENVIRONMENT_SYMBOLS:
            uses.append(SymbolUse(name, "ENVIRONMENT_DEPENDENT", None, None, used_at))
            out.append(m.group(0))
        else:
            uses.append(SymbolUse(name, "UNDEFINED", None, None, used_at))
            out.append(m.group(0))
        i = m.end()
    return "".join(out), uses


class Scope:
    """Symbol scope. The job scope holds SET definitions by line (a SET applies to statements after
    it, JCL-SET-001). A procedure scope holds PROC defaults overridden by the calling EXEC's
    assignments (JCL-SYM-004) and falls back to the caller's lookup bound to the calling EXEC line
    (nested inheritance, rule 5)."""

    def __init__(self, parent: Lookup | None = None) -> None:
        self.parent = parent
        self.defs: dict[str, SymbolDef] = {}
        self.sets: list[tuple[int, SymbolDef]] = []

    def define(self, d: SymbolDef) -> None:
        self.defs[d.name] = d

    def add_set(self, line: int, d: SymbolDef) -> None:
        self.sets.append((line, d))

    def lookup_at(self, line: int | None) -> Lookup:
        def look(name: str) -> SymbolDef | None:
            if name in self.defs:
                return self.defs[name]
            hit = None
            if line is not None:
                for ln, d in self.sets:
                    if ln < line and d.name == name:
                        hit = d
            if hit is not None:
                return hit
            return self.parent(name) if self.parent is not None else None

        return look

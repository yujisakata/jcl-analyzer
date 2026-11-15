"""Layout generator for syntactically permitted JCL variants (H-03, Property/Metamorphic tests).

Given one logical statement (name, operation, parameters as raw JCL text) it renders physical
records under an explicit Layout. Only variations IBM permits are representable:
  * continuation breaks only after a complete parameter and its comma, at or before column 71,
    continuation text starting in columns 4-16 (JCL-CONT-001)
  * free-form blanks between name/operation/parameter fields (JCL-REC-002 "free form")
  * comment statements between continuation records (JCL-CONT-006)
  * sequence numbers in columns 73-80 (JCL-REC-003)
  * keyword order permutations (JCL-FMT-004; done in strategies.py)
Parameters containing blanks (quoted values) and apostrophe-split continuation are deliberately
out of scope for this generator. Invalid layouts raise LayoutError instead of being "fixed".
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_FIELD_COL = 71


class LayoutError(ValueError):
    pass


@dataclass(frozen=True)
class StatementSpec:
    name: str | None
    operation: str
    positional: tuple[str, ...]
    keywords: tuple[str, ...]
    comment: str | None = None

    @property
    def params(self) -> tuple[str, ...]:
        return self.positional + self.keywords


@dataclass(frozen=True)
class Layout:
    op_col: int                       # 1-based column where the operation field starts
    param_gap: int                    # blanks between operation and parameter field (>= 1)
    breaks: frozenset[int]            # break after parameter index i (0-based)
    cont_cols: tuple[int, ...]        # start column of each continuation record (4..16)
    seq: str | None                   # 8 characters for columns 73-80, or None
    comments_between: frozenset[int]  # insert a comment statement after statement record i


def canonical_layout(spec: StatementSpec) -> Layout:
    name_len = len(spec.name or "")
    return Layout(op_col=max(3 + name_len + 1, 12), param_gap=1, breaks=frozenset(),
                  cont_cols=(), seq=None, comments_between=frozenset())


def render(spec: StatementSpec, layout: Layout) -> list[str]:
    params = spec.params
    if not params:
        raise LayoutError("statements without parameters are not generated")
    if any(" " in p for p in params):
        raise LayoutError("parameters containing blanks are out of scope")
    breaks = sorted(layout.breaks)
    if any(b < 0 or b >= len(params) - 1 for b in breaks):
        raise LayoutError("breaks must be between parameters")
    if len(layout.cont_cols) != len(breaks):
        raise LayoutError("one continuation column per break is required")
    if any(not 4 <= c <= 16 for c in layout.cont_cols):
        raise LayoutError("continuation must start in columns 4-16 (JCL-CONT-001)")
    if layout.seq is not None and len(layout.seq) != 8:
        raise LayoutError("sequence field must be 8 characters")
    name = spec.name or ""
    if layout.op_col < 3 + len(name) + 1:
        raise LayoutError("operation must be preceded by at least one blank")
    if layout.param_gap < 1:
        raise LayoutError("parameter field must be preceded by at least one blank")

    groups: list[list[str]] = []
    cur: list[str] = []
    for i, p in enumerate(params):
        cur.append(p)
        if i in layout.breaks:
            groups.append(cur)
            cur = []
    groups.append(cur)

    records: list[str] = []
    for gi, group in enumerate(groups):
        text = ",".join(group) + ("," if gi < len(groups) - 1 else "")
        if gi == 0:
            head = ("//" + name).ljust(layout.op_col - 1) + spec.operation + " " * layout.param_gap
        else:
            head = "//".ljust(layout.cont_cols[gi - 1] - 1)
        body = head + text
        if spec.comment and gi == len(groups) - 1:
            body += " " + spec.comment
        if len(body) > MAX_FIELD_COL:
            raise LayoutError(f"fields exceed column 71: {body!r}")
        rec = body.ljust(72) + layout.seq if layout.seq else body
        records.append(rec)

    out: list[str] = []
    for i, rec in enumerate(records):
        out.append(rec)
        if i in layout.comments_between and i < len(records) - 1:
            out.append("//* GENERATED COMMENT BETWEEN CONTINUATIONS")
    return out

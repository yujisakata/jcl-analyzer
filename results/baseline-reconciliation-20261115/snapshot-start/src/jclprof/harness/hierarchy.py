"""Hierarchy invariants for Parser output (R1 / audit A11; ADR-027).

`check_hierarchy()` verifies the JOB -> STEP -> DD tree of a ParseResult WITHOUT any Golden
expectation. It derives the expected ownership with its own small walk over the flat statement
list (a reference model independent of the Parser's state machine) and cross-checks the tree, the
flat statements, the record roles, the in-stream data regions and the source positions.

The checks cannot tell whether the Parser applied an IBM rule correctly where the flat statements
are themselves wrong, and the reference walk mirrors the Parser's current scope decisions
(statements after a null statement stay in the job: JES2 NULLJCL=IGNORE, known defect A01;
an intervening non-DD statement ends a concatenation). They detect a tree that is inconsistent with
the statements and the source -- dropped, duplicated, moved or altered nodes and spans.

Violation codes:
  H-JOB-01  JOB statement without exactly one JobNode
  H-STEP-01 EXEC statement without exactly one StepNode
  H-DD-01   DD statement without exactly one DDNode
  H-OWN-01  node attached to a different parent than the statement order implies
  H-OWN-02  other statement (SET, IF, ...) not reachable from the tree or outside_statements
  H-ORD-01  jobs, steps or DDs out of source order
  H-CONC-01 concatenation fields inconsistent with the preceding DD
  H-SRC-01  job / step / DD name differs from the statement's name field
  H-TGT-01  step target differs from the EXEC statement's PGM= / PROC= / procedure name
  H-SPAN-01 job span does not start at its JOB statement, overlaps the next job or does not
            contain every statement up to the next JOB statement
  H-SPAN-02 job span does not contain the in-stream data and delimiter of its DD statements
  H-DATA-01 data region inconsistent with record roles
  H-REC-01  record role inconsistent with the statement that owns the record
  H-REC-02  UNRECOGNIZED record without a PAR-W006 diagnostic at that line
  H-REC-03  non-continuation record inside a step marked UNRECOGNIZED (JCL-DD-006: it is data)
  H-REF-01  tree node differs from the statement in the flat list (or refers to a missing one)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields

from jclprof.parser import ParseResult
from jclprof.parser.model import DDNode, StatementNode, StepNode

COMMENTISH = frozenset({"COMMENT", "NULL", "DELIMITER", "JES2"})
ROOT = "ROOT"
MEMBER = "MEMBER"


@dataclass(frozen=True, order=True)
class Violation:
    code: str
    node: str
    detail: str


def _pos(s: StatementNode) -> int:
    if s.span:
        return s.span[0]
    if s.inline is not None and s.inline.records:
        return s.inline.records[0]
    return 0


def _ordered(r: ParseResult) -> list[StatementNode]:
    return sorted(r.statements, key=lambda s: (_pos(s), 0 if s.span else 1))


def _ddname(s: StatementNode) -> tuple[str | None, str | None]:
    if s.name is None:
        return (s.implicit_name if s.implicit else None), None
    pre, dot, nm = s.name.text.rpartition(".")
    return (nm, pre) if dot else (s.name.text, None)


def reference_ownership(r: ParseResult) -> tuple[dict[str, str | None],
                                                 dict[str, tuple[str | None, int, str | None]]]:
    """Expected owner of every non-comment statement and expected concatenation fields of every
    DD, derived only from the order and kinds of the flat statements."""
    member = r.input_kind == "proc_member"
    container: str | None = MEMBER if member else None
    outer: str | None = container
    step: str | None = None
    header_done = False
    seen_content = False
    last_dd: tuple[str, str | None, int] | None = None  # (id, head, index)
    own: dict[str, str | None] = {}
    concat: dict[str, tuple[str | None, int, str | None]] = {}
    for s in _ordered(r):
        k = s.kind
        if k in COMMENTISH:
            if k not in ("COMMENT", "NULL"):
                seen_content = True
            continue
        if k == "JOB":
            container = outer = f"JOB:{s.id}"
            step = None
            own[s.id] = ROOT
        elif k == "PROC":
            if member and not header_done and not seen_content:
                header_done = True
                own[s.id] = MEMBER
            else:
                step = None
                own[s.id] = container
                container = f"PROC:{s.id}"
        elif k == "PEND":
            if container is not None and container.startswith("PROC:"):
                own[s.id] = container
                container = outer
                step = None
            else:
                own[s.id] = step or container
        elif k == "EXEC":
            step = f"STEP:{s.id}"
            own[s.id] = container
        else:
            own[s.id] = step or container
        seen_content = True
        if k == "DD":
            name, _ = _ddname(s)
            if name is not None:
                concat[s.id] = (name, 0, None)
            elif last_dd is not None:
                concat[s.id] = (last_dd[1], last_dd[2] + 1, last_dd[0])
            else:
                concat[s.id] = (None, 0, None)
            last_dd = (s.id, concat[s.id][0], concat[s.id][1])
        else:
            last_dd = None
    return own, concat


def _expected_target(s: StatementNode) -> tuple[str, str] | None:
    if s.positional and s.positional[0].kind == "WORD":
        return ("PROC", s.positional[0].text)
    for kw in s.keywords:
        if kw.name in ("PGM", "PROC") and kw.value is not None:
            return (kw.name, kw.value.text)
    return None


class _Tree:
    """Flattened view of the Parser's tree: owner of every referenced statement."""

    def __init__(self, r: ParseResult) -> None:
        self.owners: dict[str, list[str | None]] = {}
        self.nodes: list[StatementNode] = []
        self.steps: list[tuple[str, StepNode]] = []
        self.dds: list[tuple[str, DDNode]] = []
        for j in r.jobs:
            jk = f"JOB:{j.job_statement.id}"
            self._add(j.job_statement, ROOT)
            for d in j.job_level_dds:
                self._dd(d, jk)
            for sid in j.job_level_statements:
                self.owners.setdefault(sid, []).append(jk)
            for st in j.steps:
                self._step(st, jk)
            for p in j.procedures:
                pk = f"PROC:{p.proc_statement.id}"
                self._add(p.proc_statement, jk)
                if p.pend_statement is not None:
                    self._add(p.pend_statement, pk)
                for st in p.steps:
                    self._step(st, pk)
        if r.procedure_header is not None:
            self._add(r.procedure_header, MEMBER)
        for st in r.procedure_steps:
            self._step(st, MEMBER)
        for sid in r.outside_statements:
            self.owners.setdefault(sid, []).append(None)

    def _add(self, s: StatementNode, owner: str | None) -> None:
        self.owners.setdefault(s.id, []).append(owner)
        self.nodes.append(s)

    def _dd(self, d: DDNode, owner: str) -> None:
        self._add(d.statement, owner)
        self.dds.append((owner, d))

    def _step(self, st: StepNode, owner: str) -> None:
        self._add(st.exec_statement, owner)
        self.steps.append((owner, st))
        sk = f"STEP:{st.exec_statement.id}"
        for d in st.dds:
            self._dd(d, sk)
        for sid in st.other_statements:
            self.owners.setdefault(sid, []).append(sk)


_MISSING_CODE = {"JOB": "H-JOB-01", "EXEC": "H-STEP-01", "DD": "H-DD-01"}


def check_hierarchy(r: ParseResult) -> list[Violation]:
    """Return every hierarchy violation (sorted, deterministic). An empty list means the tree is
    consistent with the flat statements, the record roles and the source positions."""
    out: list[Violation] = []
    by_id = {s.id: s for s in r.statements}
    tree = _Tree(r)
    own, concat = reference_ownership(r)

    # --- references: every tree node is the flat statement with the same id (H-REF-01)
    for n in tree.nodes:
        flat = by_id.get(n.id)
        if flat is None:
            out.append(Violation("H-REF-01", n.id, "tree node has no flat statement"))
        elif flat != n:
            diff = [f.name for f in fields(n) if getattr(n, f.name) != getattr(flat, f.name)]
            out.append(Violation("H-REF-01", n.id,
                                 f"{n.kind} tree node differs from flat statement in {diff}"))
    for sid in tree.owners:
        if sid not in by_id:
            out.append(Violation("H-REF-01", sid, "tree refers to a missing statement"))

    # --- ownership (H-JOB/STEP/DD-01, H-OWN-01/02)
    for sid, exp in own.items():
        got = tree.owners.get(sid, [])
        kind = by_id[sid].kind
        code = _MISSING_CODE.get(kind, "H-OWN-02")
        if not got:
            where = str(exp)
            if exp is not None and exp.startswith("STEP:") and own.get(exp[5:], "") is None:
                where += ", step outside any job"
            out.append(Violation(code, sid, f"{kind} not in tree (expected under {where})"))
        elif len(got) > 1:
            out.append(Violation(code, sid, f"{kind} attached {len(got)} times: "
                                            f"{sorted(map(str, got))}"))
        elif got[0] != exp:
            out.append(Violation("H-OWN-01", sid, f"{kind} under {got[0]}, expected {exp}"))

    # --- order (H-ORD-01)
    job_lines = [_pos(j.job_statement) for j in r.jobs]
    if job_lines != sorted(job_lines):
        out.append(Violation("H-ORD-01", "jobs", f"job order {job_lines}"))
    for owner, lines in _group(((o, _pos(st.exec_statement)) for o, st in tree.steps)).items():
        if lines != sorted(lines):
            out.append(Violation("H-ORD-01", str(owner), f"step order {lines}"))
    for owner, lines in _group(((o, _pos(d.statement)) for o, d in tree.dds)).items():
        if lines != sorted(lines):
            out.append(Violation("H-ORD-01", str(owner), f"DD order {lines}"))

    # --- names, concatenation, targets (H-SRC-01, H-CONC-01, H-TGT-01)
    for j in r.jobs:
        nm = j.job_statement.name.text if j.job_statement.name else None
        if j.name != nm:
            out.append(Violation("H-SRC-01", j.id, f"job name {j.name!r} != {nm!r}"))
    for _, st in tree.steps:
        s = st.exec_statement
        nm = s.name.text if s.name else None
        if st.name != nm:
            out.append(Violation("H-SRC-01", st.id, f"step name {st.name!r} != {nm!r}"))
        exp_t = _expected_target(s)
        if st.target != exp_t:
            out.append(Violation("H-TGT-01", st.id, f"target {st.target} != {exp_t}"))
    for _, d in tree.dds:
        s = d.statement
        name, pre = _ddname(s)
        if (d.ddname, d.procstep) != (name, pre):
            out.append(Violation("H-SRC-01", s.id, f"ddname {(d.ddname, d.procstep)} != "
                                                   f"{(name, pre)}"))
        if s.id in concat and (d.concat_head, d.concat_index, d.concat_of) != concat[s.id]:
            out.append(Violation("H-CONC-01", s.id, f"{(d.concat_head, d.concat_index,
                                                         d.concat_of)} != {concat[s.id]}"))

    out += _check_spans(r)
    out += _check_records(r, by_id)
    return sorted(set(out))


def _group(pairs: Iterable[tuple[str | None, int]]) -> dict[str | None, list[int]]:
    g: dict[str | None, list[int]] = {}
    for k, v in pairs:
        g.setdefault(k, []).append(v)
    return g


def _check_spans(r: ParseResult) -> list[Violation]:
    out: list[Violation] = []
    jobs = sorted(r.jobs, key=lambda j: _pos(j.job_statement))
    for i, j in enumerate(jobs):
        start = _pos(j.job_statement)
        nxt = _pos(jobs[i + 1].job_statement) if i + 1 < len(jobs) else None
        lo, hi = j.span
        if lo != start:
            out.append(Violation("H-SPAN-01", j.id, f"span starts at {lo}, JOB is at {start}"))
        if nxt is not None and hi >= nxt:
            out.append(Violation("H-SPAN-01", j.id, f"span end {hi} overlaps next JOB at {nxt}"))
        in_job = [s for s in r.statements
                  if s.span and start <= s.span[0] and (nxt is None or s.span[0] < nxt)]
        last = max((s.span[1] for s in in_job if s.span), default=start)
        if hi < last:
            out.append(Violation("H-SPAN-01", j.id, f"span end {hi} < last statement line {last}"))
        for g in r.data_regions:
            owner = next((s for s in r.statements if s.id == g.statement_id), None)
            if owner is None or not (start <= _pos(owner) and (nxt is None or _pos(owner) < nxt)):
                continue
            owned_end = g.terminator_line if g.terminator == "DELIMITER" else None
            ends = [x for x in (g.records[1] if g.records else None, owned_end) if x is not None]
            if ends and hi < max(ends):
                out.append(Violation("H-SPAN-02", j.id,
                                     f"span end {hi} < end of data region {g.id} ({max(ends)}, "
                                     f"terminator {g.terminator})"))
    return out


def _check_records(r: ParseResult, by_id: dict[str, StatementNode]) -> list[Violation]:
    out: list[Violation] = []
    roles = {rr.line: rr for rr in r.records}
    # statements own their records (H-REC-01)
    for s in r.statements:
        if not s.span:
            continue
        for x in s.lines:
            rr = roles.get(x)
            want = (s.kind if s.kind in COMMENTISH else
                    ("STATEMENT" if x == s.span[0] else "CONTINUATION"))
            if rr is None or rr.statement_id != s.id or rr.role != want:
                out.append(Violation("H-REC-01", s.id, f"record {x}: {rr and rr.role}/"
                                                       f"{rr and rr.statement_id}, want {want}"))
    for rr in r.records:
        if rr.role in ("STATEMENT", "CONTINUATION") and rr.statement_id not in by_id:
            out.append(Violation("H-REC-01", f"L{rr.line}", f"role {rr.role} without statement"))
    # data regions vs roles (H-DATA-01) and region identity (H-REF-01)
    region_ids = {g.id for g in r.data_regions}
    for g in r.data_regions:
        owner = by_id.get(g.statement_id)
        if owner is None or owner.inline != g:
            out.append(Violation("H-REF-01", g.id, "region differs from its DD statement's inline"))
        if g.status != "DETERMINED":
            continue
        span = set(range(g.records[0], g.records[1] + 1)) if g.records else set()
        for x in sorted(span):
            rr = roles.get(x)
            if rr is None or rr.role != "DATA" or rr.region_id != g.id:
                out.append(Violation("H-DATA-01", g.id, f"record {x} in region is "
                                                        f"{rr and rr.role}/{rr and rr.region_id}"))
        if g.terminator == "DELIMITER":
            rr = roles.get(g.terminator_line or 0)
            if rr is None or rr.role != "DELIMITER" or rr.region_id != g.id:
                out.append(Violation("H-DATA-01", g.id, f"terminator {g.terminator_line} is not "
                                                        "this region's DELIMITER"))
        allowed = span | ({g.terminator_line} if g.terminator == "DELIMITER" and
                          g.terminator_line else set())
        for rr in r.records:
            if rr.region_id == g.id and rr.line not in allowed:
                out.append(Violation("H-DATA-01", g.id, f"record {rr.line} claims the region "
                                                        "outside its range"))
    for rr in r.records:
        if rr.region_id is not None and rr.region_id not in region_ids:
            out.append(Violation("H-DATA-01", f"L{rr.line}", f"unknown region {rr.region_id}"))
    # unrecognized records are diagnosed (H-REC-02)
    w006 = {d.line for d in r.diagnostics if d.code == "PAR-W006"}
    for rr in r.records:
        if rr.role == "UNRECOGNIZED" and rr.line not in w006:
            out.append(Violation("H-REC-02", f"L{rr.line}", "UNRECOGNIZED without PAR-W006"))
    # a non-JCL record inside a step is in-stream data (implicit SYSIN, JCL-DD-006), never
    # UNRECOGNIZED; only a continuation cut off by a data region may be (H-REC-03)
    in_step = _step_lines(r)
    for rr in r.records:
        if rr.role == "UNRECOGNIZED" and (rr.lexer_kind != "CONTINUATION" and
                                          rr.line in in_step):
            out.append(Violation("H-REC-03", f"L{rr.line}",
                                 f"{rr.lexer_kind} record inside a step is UNRECOGNIZED"))
    return out


def _step_lines(r: ParseResult) -> set[int]:
    """Lines after an EXEC statement and before the next JOB / PROC / PEND (closing a step)."""
    marks = sorted((s.span[0], s.kind) for s in r.statements
                   if s.span and s.kind in ("EXEC", "JOB", "PROC", "PEND"))
    out: set[int] = set()
    last = len(r.records)
    for i, (line, kind) in enumerate(marks):
        if kind != "EXEC":
            continue
        end = next((x for x, k in marks[i + 1:] if k in ("JOB", "PROC", "PEND")), last + 1)
        out.update(range(line + 1, end))
    return out

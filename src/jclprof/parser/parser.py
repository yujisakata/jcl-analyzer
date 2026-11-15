"""JCL basic-syntax Parser (Step 4b). Builds statements, the JOB/STEP/DD hierarchy and in-stream
data regions from Lexer output, without modifying it.

In scope: statement kinds, name fields, typed parameters, JOB/EXEC/DD membership, unnamed-DD
concatenation candidates, JOB-level DDs (JOBLIB), in-stream data segmentation (DD * / DD DATA /
DLM / JES type / implicit SYSIN), comments, unrecognized records.
Not in scope (recorded as limitations, never treated as analyzed): PROC expansion and overrides,
INCLUDE expansion, symbol resolution, IF/COND meaning, GDG resolution, DSN mapping.
Rules: JCL-FMT-001..009, JCL-EXEC-001, JCL-DD-001..006, JCL-DD-013/014, JCL-STMT-*, JCL-PROC-001.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from jclprof.lexer import lex_file, lex_text
from jclprof.lexer.model import LexResult, LexStatement, Record
from jclprof.parser.model import (
    DataCandidate,
    DataRegion,
    DDNode,
    JobNode,
    KeywordParam,
    ParseDiagnostic,
    ParseResult,
    ProcDefNode,
    RecordRole,
    StatementNode,
    StepNode,
    Value,
)
from jclprof.parser.values import parse_parameters

# Parser diagnostic codes; must equal specs/diagnostic-catalog.yaml (checked by a harness test).
PARSE_CODES: dict[str, tuple[str, str, str]] = {
    "PAR-E002": ("ERROR", "SYNTAX", "Invalid name field"),
    "PAR-E006": ("ERROR", "SYNTAX", "EXEC without PGM=, PROC= or procedure name"),
    "PAR-E007": ("ERROR", "SYNTAX", "Positional parameter after keyword parameter"),
    "PAR-E008": ("ERROR", "SYNTAX", "More than two levels of subparameter parentheses"),
    "PAR-E016": ("ERROR", "SYNTAX", "DLM on a DD statement without * or DATA"),
    "PAR-E020": ("ERROR", "SYNTAX", "JOBLIB DD not immediately after the JOB statement"),
    "PAR-W003": ("WARNING", "UNSUPPORTED", "Unrecognized operation field"),
    "PAR-W004": ("WARNING", "SPEC_UNCONFIRMED",
                 "Unnamed DD statement with no preceding DD statement"),
    "PAR-W005": ("WARNING", "ENVIRONMENT", "In-stream data end depends on the JES type (UNKNOWN)"),
    "PAR-W006": ("WARNING", "ANALYZABILITY",
                 "Record is not JCL and not in an in-stream data context"),
    "PAR-W008": ("WARNING", "SPEC_UNCONFIRMED",
                 "DD statement before the first EXEC that is not JOBLIB"),
    "PAR-I001": ("INFO", "ENVIRONMENT", "Statements follow a null statement before the next JOB"),
    "PAR-I002": ("INFO", "ADVISORY", "procstepname.ddname coded in a program step"),
    "LEX-W002": ("WARNING", "SYNTAX_DEFINED",
                 "In-stream data requiring a delimiter ends at end of input"),
}

KNOWN_OPERATIONS = frozenset({
    "JOB", "EXEC", "DD", "PROC", "PEND", "JCLLIB", "INCLUDE", "SET", "IF", "ELSE", "ENDIF",
    "OUTPUT", "CNTL", "ENDCNTL", "EXPORT", "SCHEDULE", "XMIT", "NOTIFY", "COMMAND",
})  # Table 8 (JCL-FMT-009) + NOTIFY (chapter 22)
# Statements whose name may be prefixed by "xxxxxxxx." (statement chapters) or are overrides
PREFIX_NAME_OK = frozenset({"EXEC", "PEND", "JCLLIB", "INCLUDE", "IF", "ELSE", "ENDIF", "DD",
                            "OUTPUT"})
SPECIAL_DDNAMES = frozenset({"JOBLIB", "STEPLIB", "SYSABEND", "SYSCKEOV", "SYSMDUMP", "SYSUDUMP",
                             "JOBCAT", "STEPCAT", "JESJCLIN", "JESJCL"})  # JCL-DD-014
_NAME = re.compile(r"\A[A-Z@#$][A-Z0-9@#$]{0,7}\Z")
_PREFIX = re.compile(r"\A[A-Z0-9@#$]{1,8}\Z")
_SYMBOL = re.compile(r"(?<!&)&(?!&)[A-Z@#$]")


def _iter_values(v: Value | None) -> list[Value]:
    if v is None:
        return []
    out = [v]
    for i in v.items:
        out += _iter_values(i)
    if v.sub is not None:
        out += _iter_values(v.sub)
    return out


def _region_end(g: DataRegion) -> int:
    """Last physical record owned by an in-stream data region (records and own delimiter)."""
    ends = [0]
    for records, term, term_line in [(g.records, g.terminator, g.terminator_line)] + [
            (c.records, c.terminator, c.terminator_line) for c in g.candidates]:
        if records:
            ends.append(records[1])
        if term == "DELIMITER" and term_line:
            ends.append(term_line)
    return max(ends)


@dataclass
class _Container:
    """A job, an in-stream procedure definition or a procedure member body."""

    kind: str  # JOB | PROC_DEF | PROC_MEMBER
    statement: StatementNode | None
    steps: list[StepNode] = field(default_factory=list)
    job_dds: list[DDNode] = field(default_factory=list)
    job_statements: list[str] = field(default_factory=list)
    procs: list[ProcDefNode] = field(default_factory=list)
    null_line: int | None = None
    last_line: int = 0
    first_region: int = 0  # index into _Parser.regions of the first region opened in this job


@dataclass
class _Step:
    id: str
    name: str | None
    exec_stmt: StatementNode
    target: tuple[str, str] | None
    dds: list[DDNode] = field(default_factory=list)
    other: list[str] = field(default_factory=list)
    after_null: bool = False


class _Parser:
    def __init__(self, lex: LexResult, jes: str, input_kind: str) -> None:
        self.lex = lex
        self.jes = jes
        self.input_kind = input_kind
        self.roles: dict[int, RecordRole] = {}
        self.statements: list[StatementNode] = []
        self.regions: list[DataRegion] = []
        self.diags: list[ParseDiagnostic] = []
        self.data_lines: set[int] = set()
        self.dropped: list[int] = []
        self.limitations: set[str] = set()
        self.jobs: list[JobNode] = []
        self.outside: list[str] = []
        self.job: _Container | None = None
        self.proc_def: _Container | None = None
        self.proc_def_stmt: StatementNode | None = None
        self.member: _Container | None = None
        self.member_header: StatementNode | None = None
        self.member_end: StatementNode | None = None
        self.step: _Step | None = None
        self.last_dd: DDNode | None = None
        self.pending_null: int | None = None
        self.after_null = False
        if input_kind == "proc_member":
            self.member = _Container("PROC_MEMBER", None)

    # ------------------------------------------------------------------ utilities
    def diag(self, code: str, line: int | None, column: int | None, detail: str = "") -> None:
        sev, cls, title = PARSE_CODES[code]
        self.diags.append(ParseDiagnostic(code, sev, cls, line, column,
                                          title + (f": {detail}" if detail else "")))

    def role(self, line: int, role: str, stmt: str | None = None,
             region: str | None = None) -> None:
        rec = self.lex.records[line - 1]
        self.roles[line] = RecordRole(line, rec.kind, role, stmt, region)

    def container(self) -> _Container | None:
        if self.proc_def is not None:
            return self.proc_def
        if self.member is not None:
            return self.member
        return self.job

    # ------------------------------------------------------------------ main loop
    def run(self) -> None:
        recs = self.lex.records
        i = 0
        while i < len(recs):
            rec = recs[i]
            n = rec.line
            if n in self.roles:
                i += 1
                continue
            if rec.kind == "STATEMENT_START":
                assert rec.statement is not None
                self.statement(self.lex.statements[rec.statement])
            elif rec.kind == "COMMENT":
                node = StatementNode(f"S{n:05d}", "COMMENT", (n, n), (n,), None, None,
                                     comment_texts=(rec.comment_text or "",), raw=(rec.raw,))
                self.add(node)
                self.role(n, "COMMENT", node.id)
            elif rec.kind == "NULL":
                node = StatementNode(f"S{n:05d}", "NULL", (n, n), (n,), None, None, raw=(rec.raw,))
                self.add(node)
                self.role(n, "NULL", node.id)
                self.null_statement(n)
            elif rec.kind in ("DELIMITER", "JES2"):
                node = StatementNode(f"S{n:05d}", rec.kind, (n, n), (n,), None, None,
                                     raw=(rec.raw,),
                                     limitations=("STRAY_DELIMITER",) if rec.kind == "DELIMITER"
                                     else ("JES2_STATEMENT_NOT_ANALYZED",))
                self.add(node)
                self.role(n, rec.kind, node.id)
                if rec.kind == "JES2":
                    self.limitations.add("JES2_STATEMENTS_NOT_ANALYZED")
            elif rec.kind == "OTHER":
                if self.step is not None:
                    self.implicit_sysin(n)
                else:
                    self.role(n, "UNRECOGNIZED")
                    self.diag("PAR-W006", n, None)
            else:  # CONTINUATION not owned by a statement (cannot normally happen)
                self.role(n, "UNRECOGNIZED")
                self.diag("PAR-W006", n, None, "continuation record without a statement")
            i += 1
        self.close_job()

    def add(self, node: StatementNode) -> None:
        self.statements.append(node)

    # ------------------------------------------------------------------ statements
    def statement(self, ls: LexStatement) -> None:
        """Process one lexical statement (records already given a role are skipped later)."""
        first = ls.span[0]
        sid = f"S{first:05d}"
        op = ls.operation.text if ls.operation else None
        kind = op if op in KNOWN_OPERATIONS else "UNKNOWN"
        raw = tuple(self.lex.records[x - 1].raw for x in ls.lines)
        positional: list[Value] = []
        keywords: list[KeywordParam] = []
        lims: list[str] = []
        if kind == "UNKNOWN":
            col = ls.operation.column if ls.operation else 3
            self.diag("PAR-W003", first, col, f"operation {op!r}")
        if kind != "IF":
            positional, keywords, issues = parse_parameters(ls.tokens)
            for iss in issues:
                self.diag(iss.code, iss.line, iss.column, iss.detail)
        node = StatementNode(sid, kind, ls.span, ls.lines, ls.name, op, tuple(positional),
                             tuple(keywords), ls.comments,
                             condition_tokens=ls.tokens if kind == "IF" else (),
                             lex_statement=ls.index, raw=raw)
        self.check_name(node)
        if any(_SYMBOL.search(v.text) for p in positional for v in _iter_values(p)) or any(
                _SYMBOL.search(v.text) for k in keywords for v in _iter_values(k.value)):
            lims.append("SYMBOLS_NOT_RESOLVED")
        for x in ls.lines:
            self.role(x, "STATEMENT" if x == first else "CONTINUATION", sid)
        node = self.place(node, lims)
        if node.kind == "DD" and node.inline is not None:
            self.after_region(node.inline)

    def check_name(self, s: StatementNode) -> None:
        if s.name is None:
            if s.kind == "JOB":
                self.diag("PAR-E002", s.span[0] if s.span else None, 3, "JOB requires a jobname")
            return
        text = s.name.text
        ok = bool(_NAME.match(text))
        if not ok and "." in text and s.kind in PREFIX_NAME_OK:
            pre, _, nm = text.rpartition(".")
            ok = bool(_PREFIX.match(pre) if s.kind != "DD" and s.kind != "OUTPUT"
                      else _NAME.match(pre)) and bool(_NAME.match(nm))
        if not ok:
            self.diag("PAR-E002", s.name.line, s.name.column, f"name {text!r}")

    # ------------------------------------------------------------------ hierarchy
    def null_statement(self, n: int) -> None:
        if self.job is not None and self.proc_def is None:
            self.job.null_line = n
            self.pending_null = n

    def note_after_null(self, kind: str) -> None:
        if self.pending_null is None:
            return
        if kind == "JOB":
            self.pending_null = None
            self.after_null = False
            return
        if self.jes == "UNKNOWN":
            self.diag("PAR-I001", self.pending_null, None)
        self.pending_null = None
        self.after_null = True

    def place(self, s: StatementNode, lims: list[str]) -> StatementNode:
        self.note_after_null(s.kind)
        k = s.kind
        if k == "JOB":
            self.close_job()
            # H01: the tree holds the same node as the flat list (created after replace()).
            s = replace(s, limitations=tuple(lims))
            self.job = _Container("JOB", s, last_line=s.span[1] if s.span else 0,
                                  first_region=len(self.regions))
            self.step = None
            self.last_dd = None
            self.after_null = False
            self.add(s)
            return s
        if k == "PROC":
            self.limitations.add("PROC_NOT_EXPANDED")
            lims.append("PROC_NOT_EXPANDED")
            s = replace(s, limitations=tuple(lims))
            self.add(s)
            if self.input_kind == "proc_member" and self.member_header is None and \
                    not self.member_has_content():
                self.member_header = s
            else:
                self.close_step()
                self.proc_def = _Container("PROC_DEF", s)
                self.proc_def_stmt = s
                self.limitations.add("PROC_STRUCTURE_NOT_VALIDATED")
            self.last_dd = None
            return s
        if k == "PEND":
            s = replace(s, limitations=tuple(lims))
            self.add(s)
            if self.proc_def is not None:
                self.close_step()
                pd = self.proc_def
                assert self.proc_def_stmt is not None
                pstmt = self.proc_def_stmt
                node = ProcDefNode(f"P{pstmt.id[1:]}",
                                   pstmt.name.text if pstmt.name else None,
                                   pstmt, s, tuple(pd.steps))
                self.proc_def = None
                self.proc_def_stmt = None
                if self.job is not None:
                    self.job.procs.append(node)
            elif self.member is not None and self.member_end is None:
                # H02: the PEND of a cataloged procedure member belongs to the PROC root
                self.member_end = s
            self.last_dd = None
            return s
        if k == "EXEC":
            self.close_step()
            target = self.exec_target(s)
            if target and target[0] == "PROC":
                lims.append("PROC_NOT_EXPANDED")
                self.limitations.add("PROC_NOT_EXPANDED")
            if any(kw.name.split(".")[0] == "COND" for kw in s.keywords):
                lims.append("COND_NOT_ANALYZED")
                self.limitations.add("COND_NOT_ANALYZED")
            s = replace(s, limitations=tuple(lims))
            self.add(s)
            self.step = _Step(f"T{s.id[1:]}", s.name.text if s.name else None, s, target,
                              after_null=self.after_null)
            if self.container() is None:
                self.outside.append(s.id)
            self.last_dd = None
            return s
        if k == "DD":
            return self.place_dd(s, lims)
        # other statements
        if k == "INCLUDE":
            lims.append("INCLUDE_NOT_EXPANDED")
        elif k in ("IF", "ELSE", "ENDIF"):
            lims.append("IF_NOT_ANALYZED")
        elif k == "JCLLIB":
            lims.append("LIBRARY_SEARCH_NOT_RESOLVED")
        elif k == "SET":
            lims.append("SYMBOLS_NOT_RESOLVED")
        elif k == "UNKNOWN":
            lims.append("UNRECOGNIZED_OPERATION")
        for x in lims:
            self.limitations.add(x)
        s = replace(s, limitations=tuple(lims))
        self.add(s)
        if self.step is not None:
            self.step.other.append(s.id)
        elif (c := self.container()) is not None:
            c.job_statements.append(s.id)
        else:
            self.outside.append(s.id)
        self.last_dd = None
        return s

    def member_has_content(self) -> bool:
        return any(st.kind not in ("COMMENT", "NULL") for st in self.statements[:-1])

    def exec_target(self, s: StatementNode) -> tuple[str, str] | None:
        first_kw = s.keywords[0] if s.keywords else None
        if s.positional and s.positional[0].kind == "WORD":
            return ("PROC", s.positional[0].text)
        if first_kw and first_kw.name in ("PGM", "PROC") and first_kw.value is not None:
            return (first_kw.name, first_kw.value.text)
        later = next((kw for kw in s.keywords[1:] if kw.name in ("PGM", "PROC")), None)
        if later is not None and later.value is not None:
            self.diag("PAR-E007", later.line, later.column,
                      f"{later.name}= must precede keyword parameters")
            return (later.name, later.value.text)
        self.diag("PAR-E006", s.span[0] if s.span else None, None)
        return None

    def place_dd(self, s: StatementNode, lims: list[str]) -> StatementNode:
        first = s.span[0] if s.span else 0
        name = s.name.text if s.name else None
        procstep = None
        ddname = name
        if name and "." in name:
            procstep, _, ddname = name.rpartition(".")
            if self.step is not None and self.step.target and self.step.target[0] == "PGM":
                self.diag("PAR-I002", first, 3, f"{name!r} in program step")
        instream = bool(s.positional) and s.positional[0].kind == "WORD" and \
            s.positional[0].text in ("*", "DATA")
        dlm_kw = next((k for k in s.keywords if k.name == "DLM"), None)
        if dlm_kw is not None and not instream:
            self.diag("PAR-E016", first, None)
        # level and placement (JCL-DD-013)
        c = self.container()
        if self.step is not None:
            level = "PROC_STEP" if c is not None and c.kind in ("PROC_DEF", "PROC_MEMBER") \
                else "STEP"
        elif c is not None and c.kind == "JOB":
            level = "JOB"
        elif c is not None:
            level = "PROC_MEMBER"
        else:
            level = "STEP"
        if ddname == "JOBLIB" and name == "JOBLIB":
            if level != "JOB" or any(d.ddname is not None for d in (c.job_dds if c else [])):
                self.diag("PAR-E020", first, None)
        elif level == "JOB" and name is not None:
            self.diag("PAR-W008", first, None, f"DD {name!r}")
        # concatenation candidates (JCL-DD-001)
        if name is None:
            if self.last_dd is None:
                self.diag("PAR-W004", first, None)
                head, idx, of = None, 0, None
            else:
                head = self.last_dd.concat_head
                idx = self.last_dd.concat_index + 1
                of = self.last_dd.statement.id
        else:
            head, idx, of = ddname, 0, None
        region = None
        if instream:
            dlm = None
            if dlm_kw is not None and dlm_kw.value is not None:
                dlm = dlm_kw.value.value if dlm_kw.value.kind in ("WORD", "STRING") \
                    else dlm_kw.value.text
            region = self.data_region(s.id, s.span[1] + 1 if s.span else 1,
                                      "STAR" if s.positional[0].text == "*" else "DATA", dlm,
                                      first)
        s = replace(s, inline=region, limitations=tuple(lims))
        for x in lims:
            self.limitations.add(x)
        self.add(s)
        node = DDNode(s, ddname, procstep, level, head, idx, of,
                      ddname if ddname in SPECIAL_DDNAMES else None)
        self.attach_dd(node, level)
        return s

    def attach_dd(self, node: DDNode, level: str) -> None:
        if self.step is not None:
            self.step.dds.append(node)
        elif (c := self.container()) is not None:
            c.job_dds.append(node)
        else:
            self.outside.append(node.statement.id)
        self.last_dd = node

    def close_step(self) -> None:
        st = self.step
        if st is None:
            return
        node = StepNode(st.id, st.name, st.exec_stmt, st.target, tuple(st.dds), tuple(st.other),
                        st.after_null)
        c = self.container()
        if c is not None:
            c.steps.append(node)
        self.step = None

    def close_job(self) -> None:
        self.close_step()
        if self.proc_def is not None:  # PROC without PEND inside a job: keep what was defined
            pd = self.proc_def
            assert self.proc_def_stmt is not None
            node = ProcDefNode(f"P{self.proc_def_stmt.id[1:]}",
                               self.proc_def_stmt.name.text if self.proc_def_stmt.name else None,
                               self.proc_def_stmt, None, tuple(pd.steps))
            self.proc_def = None
            if self.job is not None:
                self.job.procs.append(node)
        j = self.job
        if j is None or j.statement is None:
            return
        # A10: the job span covers every source region the job owns: its statements (including
        # comments) and the in-stream data of its DD statements -- data records, the delimiter,
        # and for an UNDETERMINED region every candidate end. Data that runs to end of input or
        # is followed directly by the next JOB statement has no statement after it.
        last = max((st.span[1] for st in self.statements if st.span), default=j.last_line)
        for g in self.regions[j.first_region:]:
            last = max(last, _region_end(g))
        js = j.statement
        assert js.span is not None
        self.jobs.append(JobNode(f"J{js.id[1:]}", js.name.text if js.name else None, js,
                                 (js.span[0], last), tuple(j.job_dds), tuple(j.job_statements),
                                 tuple(j.steps), tuple(j.procs), j.null_line))
        self.job = None

    # ------------------------------------------------------------------ in-stream data
    def end_scan(self, start: int, mode: str, dlm: str | None, jes: str) -> DataCandidate:
        recs = self.lex.records
        for j in range(start, len(recs) + 1):
            raw = recs[j - 1].raw
            if dlm is not None:
                if raw.startswith(dlm):
                    return DataCandidate(jes, (start, j - 1) if j > start else None,
                                         "DELIMITER", j)
                if mode == "STAR" and jes == "JES2" and raw.startswith("//"):
                    return DataCandidate(jes, (start, j - 1) if j > start else None,
                                         "NEXT_STATEMENT", j)
                continue
            if raw.startswith("/*"):
                term = "DELIMITER" if recs[j - 1].kind == "DELIMITER" else "NEXT_STATEMENT"
                return DataCandidate(jes, (start, j - 1) if j > start else None, term, j)
            if mode in ("STAR", "IMPLICIT") and raw.startswith("//"):
                return DataCandidate(jes, (start, j - 1) if j > start else None,
                                     "NEXT_STATEMENT", j)
        last = len(recs)
        return DataCandidate(jes, (start, last) if last >= start else None, "EOF", None)

    def data_region(self, sid: str, start: int, mode: str, dlm: str | None,
                    dd_line: int) -> DataRegion:
        rid = f"R{start:05d}"
        if dlm is not None and mode == "STAR" and self.jes == "UNKNOWN":
            c2 = self.end_scan(start, mode, dlm, "JES2")
            c3 = self.end_scan(start, mode, dlm, "JES3")
            if (c2.records, c2.terminator, c2.terminator_line) != \
                    (c3.records, c3.terminator, c3.terminator_line):
                self.diag("PAR-W005", dd_line, None)
                region = DataRegion(rid, sid, mode, dlm, "UNDETERMINED", None, "UNDETERMINED",
                                    None, None, (c2, c3))
                self.regions.append(region)
                return region
            cand = c2
        else:
            jes = self.jes if self.jes != "UNKNOWN" else "ANY"
            cand = self.end_scan(start, mode, dlm, jes)
        delim = None
        if cand.terminator == "DELIMITER":
            delim = dlm if dlm is not None else "/*"
        if cand.terminator == "EOF" and mode == "DATA":
            self.diag("LEX-W002", dd_line, None, "DD DATA data ends at end of input")
        region = DataRegion(rid, sid, mode, dlm, "DETERMINED", cand.records, cand.terminator,
                            delim, cand.terminator_line)
        self.regions.append(region)
        return region

    def after_region(self, region: DataRegion) -> None:
        """Assign record roles (DATA / DELIMITER / UNDETERMINED) for a data region."""
        if region.status == "UNDETERMINED":
            ends = []
            for c in region.candidates:
                last = c.records[1] if c.records else 0
                if c.terminator == "DELIMITER" and c.terminator_line:
                    last = c.terminator_line
                ends.append(last)
            start = min((c.records[0] for c in region.candidates if c.records),
                        default=max(ends) + 1)
            last = max(ends)
            for n in range(start, last + 1):
                self.role(n, "UNDETERMINED", None, region.id)
                self.data_lines.add(n)
            self.limitations.add("INSTREAM_END_UNDETERMINED")
            self.drop_lex_in(start, last)
            return
        if region.records:
            for n in range(region.records[0], region.records[1] + 1):
                self.role(n, "DATA", region.statement_id, region.id)
                self.data_lines.add(n)
            self.drop_lex_in(region.records[0], region.records[1])
        if region.terminator == "DELIMITER" and region.terminator_line:
            n = region.terminator_line
            rec: Record = self.lex.records[n - 1]
            node = StatementNode(f"S{n:05d}", "DELIMITER", (n, n), (n,), None, None,
                                 raw=(rec.raw,))
            self.add(node)
            self.role(n, "DELIMITER", node.id, region.id)
            self.data_lines.add(n)
            self.drop_lex_in(n, n)

    def drop_lex_in(self, lo: int, hi: int) -> None:
        for ls in self.lex.statements:
            if lo <= ls.span[0] <= hi and ls.index not in self.dropped:
                self.dropped.append(ls.index)
                for x in ls.lines:
                    if x > hi:  # lexical statement straddles the region end
                        self.role(x, "UNRECOGNIZED")
                        self.diag("PAR-W006", x, None, "continuation of a data record")

    def implicit_sysin(self, n: int) -> None:
        """Data records with no preceding DD: the system provides DD * named SYSIN (JCL-DD-006)."""
        assert self.step is not None
        sid = f"S{n:05d}I"
        region = self.data_region(sid, n, "IMPLICIT", None, n)
        node = StatementNode(sid, "DD", None, (), None, None, positional=(
            Value("WORD", "*", n, 0, value="*"),), inline=region, implicit=True,
            implicit_basis="JCL-DD-006", implicit_name="SYSIN")
        self.add(node)
        dd = DDNode(node, "SYSIN", None,
                    "PROC_STEP" if self.proc_def is not None or self.member is not None
                    else "STEP", "SYSIN", 0, None, None, implicit=True)
        self.step.dds.append(dd)
        self.last_dd = dd
        self.after_region(region)


def parse_lex(lex: LexResult, *, jes: str = "UNKNOWN", input_kind: str = "job") -> ParseResult:
    if jes not in ("JES2", "JES3", "UNKNOWN"):
        raise ValueError(f"jes must be JES2, JES3 or UNKNOWN, not {jes!r}")
    p = _Parser(lex, jes, input_kind)
    p.run()
    superseded = tuple(d for d in lex.diagnostics if d.line in p.data_lines)
    kept = [ParseDiagnostic(d.code, d.severity, d.cls, d.line, d.column, d.message)
            for d in lex.diagnostics if d.line not in p.data_lines]
    diags = sorted(kept + p.diags, key=lambda d: (d.line or 0, d.column or 0, d.code))
    roles = tuple(p.roles[r.line] for r in lex.records)
    member_steps: tuple[StepNode, ...] = ()
    if p.member is not None:
        p.close_step()
        member_steps = tuple(p.member.steps)
    return ParseResult(lex, input_kind, jes, tuple(p.statements), roles, tuple(p.regions),
                       tuple(p.jobs), member_steps, p.member_header, tuple(p.outside),
                       tuple(diags), superseded, tuple(sorted(p.limitations)),
                       tuple(sorted(p.dropped)), p.member_end)


def parse_text(text: str, *, jes: str = "UNKNOWN", input_kind: str = "job") -> ParseResult:
    return parse_lex(lex_text(text), jes=jes, input_kind=input_kind)


def parse_file(path: Path, *, encoding: str, jes: str = "UNKNOWN",
               input_kind: str = "job") -> ParseResult:
    return parse_lex(lex_file(path, encoding=encoding), jes=jes, input_kind=input_kind)

"""Typed Parser AST (Step 4b). See docs/ast-schema.md.

Every node keeps its source location (lines, columns, lexer statement index) so that it can be
traced back to the original JCL. Lexer output is never modified; the Parser's context-dependent
record classification is a separate overlay (RecordRole).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jclprof.lexer.model import Comment, Field, LexResult, Token


@dataclass(frozen=True)
class Value:
    """A parameter value. kind: WORD | STRING | LIST | KWSUB | NULL | COMPOUND."""

    kind: str
    text: str  # raw source text of the whole value (joined across records)
    line: int
    column: int  # 0 = system-provided value with no source text (implicit SYSIN DD *)
    value: str | None = None  # WORD text / STRING unescaped value
    items: tuple[Value, ...] = ()  # LIST items
    keyword: str | None = None  # KWSUB keyword
    sub: Value | None = None  # KWSUB value (None = coded without a value)

    def to_view(self) -> Any:
        if self.kind == "NULL":
            return None
        if self.kind == "WORD":
            return self.value
        if self.kind == "STRING":
            return {"q": self.value}
        if self.kind == "LIST":
            return [i.to_view() for i in self.items]
        if self.kind == "KWSUB":
            return {"kw": [self.keyword, self.sub.to_view() if self.sub else None]}
        return self.text  # COMPOUND: raw text, e.g. DSN=PDS1(MEMA), GDS(+1)


@dataclass(frozen=True)
class KeywordParam:
    name: str
    line: int
    column: int
    value: Value | None  # None = keyword coded with nothing after '=' (nullification)


@dataclass(frozen=True)
class DataCandidate:
    jes: str
    records: tuple[int, int] | None
    terminator: str
    terminator_line: int | None


@dataclass(frozen=True)
class DataRegion:
    """In-stream data for a DD * / DD DATA / implicit SYSIN statement (JCL-DD-003..006)."""

    id: str
    statement_id: str
    mode: str  # STAR | DATA | IMPLICIT
    dlm: str | None
    status: str  # DETERMINED | UNDETERMINED
    records: tuple[int, int] | None  # first and last data record (None = no data records)
    terminator: str  # DELIMITER | NEXT_STATEMENT | EOF | UNDETERMINED
    delimiter: str | None
    terminator_line: int | None
    candidates: tuple[DataCandidate, ...] = ()  # when UNDETERMINED (JES=UNKNOWN)


@dataclass(frozen=True)
class StatementNode:
    id: str
    kind: str  # JOB EXEC DD PROC PEND JCLLIB INCLUDE SET IF ELSE ENDIF OUTPUT ... COMMENT NULL
    #            DELIMITER JES2 UNKNOWN
    span: tuple[int, int] | None
    lines: tuple[int, ...]
    name: Field | None
    operation: str | None
    positional: tuple[Value, ...] = ()
    keywords: tuple[KeywordParam, ...] = ()
    comments: tuple[Comment, ...] = ()
    comment_texts: tuple[str, ...] = ()  # COMMENT statements: columns 4-80
    condition_tokens: tuple[Token, ...] = ()  # IF: kept raw (relational expression not analyzed)
    condition: None = None  # Step 4b: never analyzed
    inline: DataRegion | None = None
    implicit: bool = False
    implicit_basis: str | None = None
    implicit_name: str | None = None  # normalized name of a system-provided DD (no name field)
    lex_statement: int | None = None
    raw: tuple[str, ...] = ()  # raw text of the statement's records
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecordRole:
    line: int
    lexer_kind: str
    role: str  # STATEMENT CONTINUATION COMMENT NULL DELIMITER JES2 DATA UNDETERMINED UNRECOGNIZED
    statement_id: str | None = None
    region_id: str | None = None


@dataclass(frozen=True)
class DDNode:
    statement: StatementNode
    ddname: str | None  # None for an unnamed (concatenated) DD
    procstep: str | None  # qualifier of procstepname.ddname
    level: str  # JOB | STEP | PROC_STEP | PROC_MEMBER
    concat_head: str | None
    concat_index: int
    concat_of: str | None  # statement id of the preceding DD this one is a candidate to join
    special: str | None
    implicit: bool = False


@dataclass(frozen=True)
class StepNode:
    id: str
    name: str | None
    exec_statement: StatementNode
    target: tuple[str, str] | None  # (PGM | PROC, raw text)
    dds: tuple[DDNode, ...]
    other_statements: tuple[str, ...]
    after_null: bool = False


@dataclass(frozen=True)
class ProcDefNode:
    id: str
    name: str | None
    proc_statement: StatementNode
    pend_statement: StatementNode | None
    steps: tuple[StepNode, ...]
    status: str = "DEFINED_NOT_EXPANDED"


@dataclass(frozen=True)
class JobNode:
    id: str
    name: str | None
    job_statement: StatementNode
    span: tuple[int, int]
    job_level_dds: tuple[DDNode, ...]
    job_level_statements: tuple[str, ...]
    steps: tuple[StepNode, ...]
    procedures: tuple[ProcDefNode, ...]
    null_statement_line: int | None = None


@dataclass(frozen=True)
class ParseDiagnostic:
    code: str
    severity: str
    cls: str
    line: int | None
    column: int | None
    message: str


@dataclass(frozen=True)
class ParseResult:
    lex: LexResult
    input_kind: str
    jes: str
    statements: tuple[StatementNode, ...]
    records: tuple[RecordRole, ...]
    data_regions: tuple[DataRegion, ...]
    jobs: tuple[JobNode, ...]
    procedure_steps: tuple[StepNode, ...]  # input_kind == proc_member
    procedure_header: StatementNode | None
    outside_statements: tuple[str, ...]  # statements outside any job/procedure container
    diagnostics: tuple[ParseDiagnostic, ...]
    superseded_diagnostics: tuple[Any, ...]  # lexer diagnostics on records that are data
    limitations: tuple[str, ...]
    dropped_lex_statements: tuple[int, ...] = field(default=())

    # ------------------------------------------------------------------ serialization
    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        def dd(d: DDNode) -> dict[str, Any]:
            return {"statement_id": d.statement.id, "ddname": d.ddname, "procstep": d.procstep,
                    "level": d.level, "concat_head": d.concat_head,
                    "concat_index": d.concat_index, "concat_of": d.concat_of,
                    "special": d.special, "implicit": d.implicit}

        def step(s: StepNode) -> dict[str, Any]:
            return {"id": s.id, "name": s.name, "exec_statement_id": s.exec_statement.id,
                    "target": list(s.target) if s.target else None,
                    "dds": [dd(d) for d in s.dds], "other_statements": list(s.other_statements),
                    "after_null": s.after_null}

        def proc(p: ProcDefNode) -> dict[str, Any]:
            return {"id": p.id, "name": p.name, "proc_statement_id": p.proc_statement.id,
                    "pend_statement_id": p.pend_statement.id if p.pend_statement else None,
                    "steps": [step(s) for s in p.steps], "status": p.status}

        return {
            "schema_version": 1,
            "source": self.lex.source, "sha256": self.lex.sha256, "encoding": self.lex.encoding,
            "input_kind": self.input_kind, "jes": self.jes,
            "statements": [asdict(s) for s in self.statements],
            "records": [asdict(r) for r in self.records],
            "data_regions": [asdict(d) for d in self.data_regions],
            "jobs": [{"id": j.id, "name": j.name, "job_statement_id": j.job_statement.id,
                      "span": list(j.span), "job_level_dds": [dd(d) for d in j.job_level_dds],
                      "job_level_statements": list(j.job_level_statements),
                      "steps": [step(s) for s in j.steps],
                      "procedures": [proc(p) for p in j.procedures],
                      "null_statement_line": j.null_statement_line} for j in self.jobs],
            "procedure_header_id": self.procedure_header.id if self.procedure_header else None,
            "procedure_steps": [step(s) for s in self.procedure_steps],
            "outside_statements": list(self.outside_statements),
            "diagnostics": [asdict(d) for d in self.diagnostics],
            "superseded_diagnostics": [asdict(d) for d in self.superseded_diagnostics],
            "limitations": list(self.limitations),
            "dropped_lex_statements": list(self.dropped_lex_statements),
        }

    def to_golden_view(self) -> dict[str, Any]:
        """Golden View 'statements' (docs/golden-view.md)."""
        out = []
        for s in self.statements:
            v: dict[str, Any] = {"kind": s.kind, "span": list(s.span) if s.span else None}
            if s.kind in ("COMMENT",):
                v["comment"] = list(s.comment_texts)
                out.append(v)
                continue
            if s.kind in ("NULL", "DELIMITER", "JES2"):
                out.append(v)
                continue
            v["name"] = s.name.text if s.name else s.implicit_name
            if s.kind == "UNKNOWN":
                v["operation"] = s.operation
            if s.kind not in ("IF",):
                v["positional"] = [p.to_view() for p in s.positional]
                v["keywords"] = [[k.name, k.value.to_view() if k.value else None]
                                 for k in s.keywords]
            v["comment"] = [c.text for c in s.comments] or None
            if s.implicit:
                v["implicit"] = True
                v["implicit_basis"] = s.implicit_basis
            if s.inline is not None:
                d = s.inline
                v["inline_data"] = {"records": list(d.records) if d.records else None,
                                    "terminator": d.terminator, "delimiter": d.delimiter}
            out.append(v)
        return {"view": "statements", "statements": out}

    def golden_diagnostics(self) -> list[dict[str, Any]]:
        return [{"code": d.code, "severity": d.severity, "line": d.line, "column": d.column,
                 "message": d.message} for d in self.diagnostics]

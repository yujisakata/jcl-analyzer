"""Typed Lexer output (Step 4a). Lexical facts only: no JOB/EXEC/DD classification (ADR-024)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RecordKind = str  # STATEMENT_START | CONTINUATION | COMMENT | NULL | DELIMITER | JES2 | OTHER
Continuation = str | None  # PARAMETER | QUOTED | COMMENT | None
End = str  # COMPLETE | NULL_STATEMENT | MISSING_CONTINUATION | END_OF_INPUT


@dataclass(frozen=True)
class Field:
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class Comment:
    line: int
    column: int
    text: str


@dataclass(frozen=True)
class Token:
    type: str  # WORD | STRING | LPAREN | RPAREN | COMMA | EQUALS | OPERATOR
    text: str  # raw source text (for STRING: with apostrophes, joined across records)
    value: str  # STRING: unescaped value; otherwise == text
    line: int
    column: int
    segments: tuple[tuple[int, int, int], ...]  # (line, first column, last column) per record


@dataclass(frozen=True)
class Record:
    line: int
    raw: str  # exact source line without terminator (never truncated)
    terminator: str  # "\r\n" | "\n" | "\r" | ""
    kind: RecordKind
    continues: Continuation
    seq: str  # columns 73-80 of JCL statement records ("" for comment/data/delimiter)
    col72: str
    comment_text: str | None  # comment statements: columns 4-80, ends stripped
    statement: int | None  # index of the lexical statement this record belongs to


@dataclass(frozen=True)
class LexStatement:
    index: int
    span: tuple[int, int]
    lines: tuple[int, ...]
    name: Field | None
    operation: Field | None
    mode: str  # NORMAL | IF (lexical field rule chosen by the operation text)
    parameter_text: str
    comments: tuple[Comment, ...]
    tokens: tuple[Token, ...]
    end: End


@dataclass(frozen=True)
class LexDiagnostic:
    code: str
    severity: str
    cls: str
    line: int | None
    column: int | None
    message: str


@dataclass(frozen=True)
class LexResult:
    source: str
    encoding: str
    sha256: str | None
    records: tuple[Record, ...]
    statements: tuple[LexStatement, ...]
    diagnostics: tuple[LexDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source, "encoding": self.encoding, "sha256": self.sha256,
            "records": [asdict(r) for r in self.records],
            "statements": [asdict(s) for s in self.statements],
            "diagnostics": [asdict(d) for d in self.diagnostics],
        }

    def to_golden_view(self) -> dict[str, Any]:
        """Golden View 'lexical' (docs/golden-view.md)."""
        def fld(f: Field | None) -> dict[str, Any] | None:
            return None if f is None else {"text": f.text, "line": f.line, "column": f.column}

        return {
            "view": "lexical",
            "records": [{"line": r.line, "kind": r.kind, "continues": r.continues, "seq": r.seq,
                         "raw": r.raw} for r in self.records],
            "lexical_statements": [{
                "span": list(s.span), "lines": list(s.lines), "name": fld(s.name),
                "operation": fld(s.operation), "parameter_text": s.parameter_text,
                "comments": [{"line": c.line, "column": c.column, "text": c.text}
                             for c in s.comments],
                "tokens": [[t.type, t.value if t.type == "STRING" else t.text] for t in s.tokens],
                "end": s.end,
            } for s in self.statements],
        }

    def golden_diagnostics(self) -> list[dict[str, Any]]:
        return [{"code": d.code, "severity": d.severity, "line": d.line, "column": d.column,
                 "message": d.message} for d in self.diagnostics]

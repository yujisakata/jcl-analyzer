"""JCL Lexer (Step 4a). Rules: JCL-REC-001..004, JCL-CONT-001..007, JCL-SYN-001, JCL-FMT-005,
JCL-IF-004, JCL-STMT-*, JCL-JES2-001 (specs/rules.yaml).

Scope (user instruction C): physical records, explicit encoding, 80-column positions, statement
start / comment / continuation recognition, apostrophe strings and parentheses, line/column
positions, preservation of every record (unrecognized ones as OTHER with raw text), lexical
diagnostics. Out of scope: JOB/EXEC/DD meaning, PROC structure, in-stream data interpretation.
Records are classified by their leading characters only, so a DD DATA record that starts with //
is lexed as STATEMENT_START here; a later stage that knows the in-stream context must reclassify it
(ADR-024).

Each record is treated as an 80-byte card: a source line shorter than 80 columns is read as if
padded with blanks (needed for apostrophe continuation to column 71, JCL-CONT-003). The raw text is
kept unchanged.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from jclprof.lexer.model import (
    Comment,
    Field,
    LexDiagnostic,
    LexResult,
    LexStatement,
    Record,
    Token,
)

# Lexer diagnostic codes; must equal specs/diagnostic-catalog.yaml (checked by a harness test).
LEX_CODES: dict[str, tuple[str, str, str]] = {
    "LEX-E001": ("ERROR", "SYNTAX", "Unterminated apostrophe-enclosed value"),
    "LEX-E002": ("ERROR", "SYNTAX", "Continuation expected but not found (column 3 not blank)"),
    "LEX-E003": ("ERROR", "SYNTAX", "Continued text does not start in the required column"),
    "LEX-E004": ("ERROR", "SYNTAX", "Unbalanced parentheses in parameter field"),
    "LEX-E005": ("ERROR", "SYNTAX", "Continued parameter field not completed"),
    "LEX-E006": ("ERROR", "ANALYZABILITY", "Input cannot be decoded with the configured encoding"),
    "LEX-W001": ("WARNING", "ADVISORY", "Continued statement followed by a null statement"),
    "LEX-W002": ("WARNING", "SYNTAX_DEFINED", "In-stream data ends at end of input"),
    "LEX-W003": ("WARNING", "SYNTAX",
                 "Comment continuation indicated but next record is not a continuation"),
    "LEX-W004": ("WARNING", "ANALYZABILITY", "Record longer than 80 columns"),
    "LEX-W005": ("WARNING", "ANALYZABILITY", "TAB character in a JCL record"),
}

FIELD_END = 71  # fields never extend past column 71 (JCL-REC-002)
COL72 = 71  # 0-based index of column 72
OP_CHARS = frozenset("<>=¬&|")
PUNCT = {"(": "LPAREN", ")": "RPAREN", ",": "COMMA", "=": "EQUALS"}
_TERM = re.compile(r"\r\n|\r|\n")
_BYTE_TERM = re.compile(rb"\r\n|\r|\n")


def split_records(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    pos = 0
    for m in _TERM.finditer(text):
        out.append((text[pos:m.start()], m.group()))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], ""))
    return out


@dataclass
class _Str:
    line: int
    column: int
    value: list[str] = field(default_factory=list)
    raw: list[str] = field(default_factory=list)
    segments: list[list[int]] = field(default_factory=list)

    def token(self) -> Token:
        return Token("STRING", "".join(self.raw), "".join(self.value), self.line, self.column,
                     tuple((s[0], s[1], s[2]) for s in self.segments))


@dataclass
class _Stmt:
    index: int
    first: int
    last: int
    lines: list[int]
    name: Field | None = None
    operation: Field | None = None
    mode: str = "NORMAL"
    segs: list[str] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)
    parens: list[tuple[int, int]] = field(default_factory=list)
    string: _Str | None = None


class _Lexer:
    def __init__(self) -> None:
        self.records: list[Record] = []
        self.statements: list[LexStatement] = []
        self.diags: list[LexDiagnostic] = []
        self.cur: _Stmt | None = None
        self.pending: str | None = None
        self.count = 0

    # ------------------------------------------------------------------ helpers
    def diag(self, code: str, line: int | None, column: int | None, detail: str = "") -> None:
        sev, cls, title = LEX_CODES[code]
        self.diags.append(LexDiagnostic(code, sev, cls, line, column,
                                        title + (f": {detail}" if detail else "")))

    def close(self, end: str) -> None:
        s = self.cur
        if s is None:
            return
        if s.parens:
            ln, col = s.parens[-1]
            self.diag("LEX-E004", ln, col, f"{len(s.parens)} unclosed '('")
        joiner = " " if s.mode == "IF" else ""
        self.statements.append(LexStatement(
            s.index, (s.first, s.last), tuple(s.lines), s.name, s.operation, s.mode,
            joiner.join(s.segs), tuple(s.comments), tuple(s.tokens), end))
        self.cur = None
        self.pending = None

    def missing_continuation(self, line: int, col3_case: bool) -> None:
        s = self.cur
        assert s is not None
        if self.pending == "QUOTED":
            assert s.string is not None
            self.diag("LEX-E001", s.string.line, s.string.column)
            self.close("MISSING_CONTINUATION")
        elif self.pending == "PARAMETER":
            if col3_case:
                self.diag("LEX-E002", line, 3)
            else:
                self.diag("LEX-E005", s.last, None)
            self.close("MISSING_CONTINUATION")
        else:  # COMMENT
            self.diag("LEX-W003", s.last, 72)
            self.close("COMPLETE")

    # ------------------------------------------------------------------ records
    def feed(self, n: int, raw: str, term: str) -> None:
        content = raw[:80]
        if len(raw) > 80:
            self.diag("LEX-W004", n, 81)
        tab = content.find("\t")
        if tab >= 0:
            self.diag("LEX-W005", n, tab + 1)
        card = content.ljust(80)
        seq = content[72:80]
        col72 = content[COL72:COL72 + 1]

        def rec(kind: str, continues: str | None = None, seq_: str = "", comment: str | None = None,
                stmt: int | None = None) -> Record:
            return Record(n, raw, term, kind, continues, seq_, col72, comment, stmt)

        if content.startswith("//*"):
            self.records.append(rec("COMMENT", comment=content[3:80].strip(" ")))
            return
        if content.startswith("//") and card[2:72].strip(" ") == "":
            if self.cur is not None and self.pending is not None:
                self.diag("LEX-W001", n, None)
                if self.pending == "QUOTED" and self.cur.string is not None:
                    self.diag("LEX-E001", self.cur.string.line, self.cur.string.column)
                self.close("NULL_STATEMENT")
            else:
                self.close("COMPLETE")
            self.records.append(rec("NULL", seq_=seq))
            return
        if content.startswith("//"):
            if self.cur is not None and self.pending is not None:
                if card[2] == " ":
                    s = self.cur
                    s.lines.append(n)
                    s.last = n
                    cont = self.continue_statement(n, card)
                    self.records.append(rec("CONTINUATION", cont, seq, stmt=s.index))
                    return
                self.missing_continuation(n, col3_case=True)
            else:
                self.close("COMPLETE")
            index = self.start_statement(n, card)
            self.records.append(rec("STATEMENT_START", self.pending, seq, stmt=index))
            return
        if self.cur is not None:
            if self.pending is not None:
                self.missing_continuation(n, col3_case=False)
            else:
                self.close("COMPLETE")
        if content.startswith("/*"):
            kind = "DELIMITER" if len(content) == 2 or content[2] == " " else "JES2"
            self.records.append(rec(kind, seq_=seq if kind == "JES2" else ""))
        else:
            self.records.append(rec("OTHER"))

    def finish(self) -> None:
        s = self.cur
        if s is None:
            return
        if self.pending == "QUOTED" and s.string is not None:
            self.diag("LEX-E001", s.string.line, s.string.column)
            self.close("END_OF_INPUT")
        elif self.pending == "PARAMETER":
            self.diag("LEX-E005", s.last, None)
            self.close("END_OF_INPUT")
        elif self.pending == "COMMENT":
            self.diag("LEX-W003", s.last, 72)
            self.close("COMPLETE")
        else:
            self.close("COMPLETE")

    # ------------------------------------------------------------------ statements
    def start_statement(self, n: int, card: str) -> int:
        area = card[:FIELD_END]
        s = _Stmt(index=self.count, first=n, last=n, lines=[n])
        self.count += 1
        self.cur = s
        i = 2
        if area[2] != " ":
            j = i
            while j < FIELD_END and area[j] != " ":
                j += 1
            s.name = Field(area[2:j], n, 3)
            i = j
        while i < FIELD_END and area[i] == " ":
            i += 1
        if i < FIELD_END:
            j = i
            while j < FIELD_END and area[j] != " ":
                j += 1
            s.operation = Field(area[i:j], n, i + 1)
            s.mode = "IF" if area[i:j] == "IF" else "NORMAL"
            i = j
            while i < FIELD_END and area[i] == " ":
                i += 1
        self.pending = self.scan(n, card, i)
        return s.index

    def continue_statement(self, n: int, card: str) -> str | None:
        s = self.cur
        assert s is not None
        area = card[:FIELD_END]
        if self.pending == "COMMENT":
            text = area[3:]
            if text.strip(" "):
                k = 3 + len(text) - len(text.lstrip(" "))
                s.comments.append(Comment(n, k + 1, text.strip(" ")))
            self.pending = "COMMENT" if card[COL72] != " " else None
            return self.pending
        if self.pending == "QUOTED":
            assert s.string is not None
            early = area[2:15]
            if early.strip(" "):
                self.diag("LEX-E003", n, 3 + len(early) - len(early.lstrip(" ")),
                          "apostrophe continuation must resume in column 16")
            s.string.segments.append([n, 16, 16])
            self.pending = self.scan(n, card, 15)
            return self.pending
        # PARAMETER
        k = 2
        while k < FIELD_END and area[k] == " ":
            k += 1
        if k < FIELD_END and not 3 <= k <= 15:
            self.diag("LEX-E003", n, k + 1, "continuation must start in columns 4-16")
        self.pending = self.scan(n, card, k)
        return self.pending

    def scan(self, n: int, card: str, i: int) -> str | None:
        """Scan the parameter (and comment) fields of one record from index i."""
        s = self.cur
        assert s is not None
        if s.mode == "IF":
            return self.scan_if(n, card, i)
        area = card[:FIELD_END]
        start = i
        while i < FIELD_END:
            ch = area[i]
            st = s.string
            if st is not None:
                if ch == "'":
                    if i + 1 < FIELD_END and area[i + 1] == "'":
                        st.value.append("'")
                        st.raw.append("''")
                        st.segments[-1][2] = i + 2
                        i += 2
                        continue
                    st.raw.append("'")
                    st.segments[-1][2] = i + 1
                    s.tokens.append(st.token())
                    s.string = None
                    i += 1
                    continue
                st.value.append(ch)
                st.raw.append(ch)
                st.segments[-1][2] = i + 1
                i += 1
                continue
            if ch == " ":
                break
            if ch == "'":
                s.string = _Str(n, i + 1, [], ["'"], [[n, i + 1, i + 1]])
                i += 1
                continue
            if ch in PUNCT:
                self.punct(s, ch, n, i)
                i += 1
                continue
            j = i
            while j < FIELD_END and area[j] not in " (),='":
                j += 1
            s.tokens.append(Token("WORD", area[i:j], area[i:j], n, i + 1, ((n, i + 1, j),)))
            i = j
        s.segs.append(area[start:i])
        if s.string is not None:
            return "QUOTED"
        self.comment_tail(s, n, area, i)
        if area[start:i].endswith(","):
            return "PARAMETER"  # column 72 ignored after "comma, blank" (JCL-CONT-004 note)
        return "COMMENT" if card[COL72] != " " else None

    def scan_if(self, n: int, card: str, i: int) -> str | None:
        """IF relational expression: blanks separate tokens; the field ends at THEN (JCL-IF-004)."""
        s = self.cur
        assert s is not None
        area = card[:FIELD_END]
        start = i
        then_end: int | None = None
        while i < FIELD_END:
            ch = area[i]
            if ch == " ":
                i += 1
                continue
            if ch in "()":
                self.punct(s, ch, n, i)
                i += 1
                continue
            j = i
            if ch in OP_CHARS:
                while j < FIELD_END and area[j] in OP_CHARS:
                    j += 1
                s.tokens.append(Token("OPERATOR", area[i:j], area[i:j], n, i + 1, ((n, i + 1, j),)))
                i = j
                continue
            while j < FIELD_END and area[j] not in " ()" and area[j] not in OP_CHARS:
                j += 1
            word = area[i:j]
            s.tokens.append(Token("WORD", word, word, n, i + 1, ((n, i + 1, j),)))
            i = j
            if word == "THEN":
                then_end = j
                break
        if then_end is None:
            s.segs.append(area[start:FIELD_END].rstrip(" "))
            return "PARAMETER"
        s.segs.append(area[start:then_end])
        self.comment_tail(s, n, area, then_end)
        return "COMMENT" if card[COL72] != " " else None

    def punct(self, s: _Stmt, ch: str, n: int, i: int) -> None:
        s.tokens.append(Token(PUNCT[ch], ch, ch, n, i + 1, ((n, i + 1, i + 1),)))
        if ch == "(":
            s.parens.append((n, i + 1))
        elif ch == ")":
            if s.parens:
                s.parens.pop()
            else:
                self.diag("LEX-E004", n, i + 1, "')' without matching '('")

    @staticmethod
    def comment_tail(s: _Stmt, n: int, area: str, i: int) -> None:
        rest = area[i:]
        if rest.strip(" "):
            k = i + len(rest) - len(rest.lstrip(" "))
            s.comments.append(Comment(n, k + 1, rest.strip(" ")))


def _lex_records(pairs: list[tuple[str, str]], source: str, encoding: str,
                 sha256: str | None) -> LexResult:
    lx = _Lexer()
    for n, (raw, term) in enumerate(pairs, start=1):
        lx.feed(n, raw, term)
    lx.finish()
    diags = sorted(lx.diags, key=lambda d: (d.line or 0, d.column or 0, d.code))
    return LexResult(source, encoding, sha256, tuple(lx.records), tuple(lx.statements),
                     tuple(diags))


def lex_text(text: str, *, source: str = "<text>", encoding: str = "(decoded text)") -> LexResult:
    return _lex_records(split_records(text), source, encoding, None)


def lex_bytes(data: bytes, *, encoding: str, source: str = "<bytes>") -> LexResult:
    """Decode with the explicitly given encoding (strict); never guess (ADR-004/009)."""
    sha = hashlib.sha256(data).hexdigest()
    try:
        text = data.decode(encoding, errors="strict")
    except UnicodeDecodeError as e:
        line, start = 1, 0
        for m in _BYTE_TERM.finditer(data, 0, e.start):
            line += 1
            start = m.end()
        sev, cls, title = LEX_CODES["LEX-E006"]
        d = LexDiagnostic("LEX-E006", sev, cls, line, e.start - start + 1,
                          f"{title}: {encoding} cannot decode byte 0x{data[e.start]:02X}")
        return LexResult(source, encoding, sha, (), (), (d,))
    return _lex_records(split_records(text), source, encoding, sha)


def lex_file(path: Path, *, encoding: str) -> LexResult:
    with open(path, "rb") as f:  # read-only (ADR-006)
        data = f.read()
    return lex_bytes(data, encoding=encoding, source=Path(path).as_posix())

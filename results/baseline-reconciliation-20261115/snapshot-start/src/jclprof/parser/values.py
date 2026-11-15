"""Parameter field parsing from Lexer tokens (JCL-FMT-003..006, JCL-FMT-008, JCL-SYN-001..003).

Grammar (comma-separated at depth 0):
  param   := KEYWORD '=' value? | value | <empty>          (empty = omitted positional -> NULL)
  value   := WORD | STRING | '(' items ')' | WORD '=' value  (keyword subparameter, e.g. SER=...)
           | adjacent tokens (e.g. PDS1(MEMA), GDS(+1))   -> COMPOUND kept as raw text
  items   := item (',' item)* ; item := value | WORD '=' value | <empty>
Member / generation parentheses directly after a word (JCL-SYN-002, Table 12) are part of a
COMPOUND value and are not counted as subparameter levels.
"""

from __future__ import annotations

from dataclasses import dataclass

from jclprof.lexer.model import Token
from jclprof.parser.model import KeywordParam, Value


@dataclass(frozen=True)
class ValueIssue:
    code: str
    line: int
    column: int
    detail: str


def _split(tokens: list[Token]) -> list[list[Token]]:
    groups: list[list[Token]] = [[]]
    depth = 0
    for t in tokens:
        if t.type == "LPAREN":
            depth += 1
        elif t.type == "RPAREN":
            depth = max(depth - 1, 0)
        if t.type == "COMMA" and depth == 0:
            groups.append([])
        else:
            groups[-1].append(t)
    return groups


def _raw(tokens: list[Token]) -> str:
    return "".join(t.text for t in tokens)


def _matching(tokens: list[Token], i: int) -> int | None:
    depth = 0
    for j in range(i, len(tokens)):
        if tokens[j].type == "LPAREN":
            depth += 1
        elif tokens[j].type == "RPAREN":
            depth -= 1
            if depth == 0:
                return j
    return None


class _ValueParser:
    def __init__(self) -> None:
        self.issues: list[ValueIssue] = []

    def value(self, toks: list[Token], at: Token | None, level: int) -> Value:
        if not toks:
            assert at is not None
            return Value("NULL", "", at.line, at.column)
        first = toks[0]
        if len(toks) == 1 and first.type in ("WORD", "STRING"):
            kind = first.type
            return Value(kind, first.text, first.line, first.column, value=first.value)
        if first.type == "WORD" and len(toks) >= 2 and toks[1].type == "EQUALS":
            sub = self.value(toks[2:], toks[1], level) if len(toks) > 2 else None
            return Value("KWSUB", _raw(toks), first.line, first.column, keyword=first.text, sub=sub)
        if first.type == "LPAREN":
            end = _matching(toks, 0)
            if end == len(toks) - 1:
                if level + 1 > 2:
                    self.issues.append(ValueIssue("PAR-E008", first.line, first.column,
                                                  "more than two levels of subparameters"))
                inner = toks[1:-1]
                items = []
                for g in _split(inner):
                    at_tok = g[0] if g else first
                    items.append(self.value(g, at_tok, level + 1))
                if not inner:
                    items = []
                return Value("LIST", _raw(toks), first.line, first.column, items=tuple(items))
        return Value("COMPOUND", _raw(toks), first.line, first.column)


def parse_parameters(tokens: tuple[Token, ...]) -> tuple[list[Value], list[KeywordParam],
                                                        list[ValueIssue]]:
    vp = _ValueParser()
    positional: list[Value] = []
    keywords: list[KeywordParam] = []
    toks = list(tokens)
    if not toks:
        return positional, keywords, vp.issues
    groups = _split(toks)
    # positions of top-level commas, used to locate empty (omitted) parameters
    commas = []
    depth = 0
    for t in toks:
        if t.type == "LPAREN":
            depth += 1
        elif t.type == "RPAREN":
            depth = max(depth - 1, 0)
        elif t.type == "COMMA" and depth == 0:
            commas.append(t)
    if len(groups) > 1 and not groups[-1]:
        groups = groups[:-1]  # dangling comma (continuation missing; diagnosed by the Lexer)
    seen_keyword = False
    for gi, g in enumerate(groups):
        anchor = g[0] if g else (commas[gi] if gi < len(commas) else toks[-1])
        if len(g) >= 2 and g[0].type == "WORD" and g[1].type == "EQUALS":
            seen_keyword = True
            val = vp.value(g[2:], g[1], 0) if len(g) > 2 else None
            keywords.append(KeywordParam(g[0].text, g[0].line, g[0].column, val))
            continue
        if seen_keyword:
            vp.issues.append(ValueIssue("PAR-E007", anchor.line, anchor.column,
                                        "positional parameter after keyword parameter"))
        positional.append(vp.value(g, anchor, 0))
    return positional, keywords, vp.issues

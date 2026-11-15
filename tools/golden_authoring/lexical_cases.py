"""Authoring aid: append the hand-designed Step 4a lexical-view Golden cases (and G-PP-010).

The expected values below were written by hand from the cited IBM rules (record kinds,
continuation types, field boundaries, tokens). The only numbers taken from the input text are
column positions, measured by plain string indexing on the designed input lines (no lexer code).
This script refuses to overwrite an existing test_id: it is for initial authoring only, and later
changes must be made by hand with a change_log entry (ADR-017).

usage: uv run python tools/golden_authoring/lexical_cases.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "tests" / "golden"
AUTHOR = "Claude (AI assistant, claude-opus-5-5); draft awaiting human review"
M_LEX = ("Hand-derived from the cited IBM SA23-1385-70 record and continuation rules, independently "
         "of the Lexer implementation. Record kinds, continuation types, field boundaries and tokens "
         "were decided by reading the rules; columns were measured from the designed input text by "
         "plain string indexing (no lexer code).")
M_IBM = ("Hand-derived from the cited IBM SA23-1385-70 rules. Input JCL designed by hand "
         "(tools/golden_authoring/make_inputs.py only fixes columns). Expected structure written "
         "manually, never generated from parser output.")


def lines(rel: str) -> list[str]:
    return (SUITE / rel).read_text(encoding="utf-8").split("\n")


def f(rel: str, line: int, text: str, start: int = 2) -> dict[str, Any]:
    """Field {text, line, column} with the column measured by string indexing."""
    return {"text": text, "line": line, "column": lines(rel)[line - 1].index(text, start) + 1}


def c(rel: str, line: int, text: str) -> dict[str, Any]:
    return {"line": line, "column": lines(rel)[line - 1].index(text) + 1, "text": text}


def R(*kinds: Any) -> list[dict[str, Any]]:
    out = []
    for i, k in enumerate(kinds, start=1):
        if isinstance(k, tuple):
            d: dict[str, Any] = {"line": i, "kind": k[0]}
            d.update(k[1])
            out.append(d)
        else:
            out.append({"line": i, "kind": k})
    return out


def T(*toks: str) -> list[list[str]]:
    """Token shorthand: punctuation characters map to their token types; 'S:x' = STRING x,
    'O:x' = OPERATOR x, anything else = WORD."""
    m = {"=": "EQUALS", ",": "COMMA", "(": "LPAREN", ")": "RPAREN"}
    out = []
    for t in toks:
        if t in m:
            out.append([m[t], t])
        elif t.startswith("S:"):
            out.append(["STRING", t[2:]])
        elif t.startswith("O:"):
            out.append(["OPERATOR", t[2:]])
        else:
            out.append(["WORD", t])
    return out


def lex_case(tid: str, cat: str, desc: str, rules: list[str], inp: str, records: list[Any],
             stmts: list[dict[str, Any]], diags: list[dict[str, Any]] | None = None,
             case_type: str = "valid", notes: str = "") -> dict[str, Any]:
    return {
        "test_id": tid, "category": cat, "description": desc, "rule_ids": rules,
        "input_file": inp, "input_kind": "job", "case_type": case_type,
        "validation_stage": "lexical",
        "expected_structure": {"view": "lexical", "records": records, "lexical_statements": stmts},
        "expected_diagnostics": {"mode": "exact", "items": diags or []},
        "oracle_method": M_LEX, "oracle_author": AUTHOR, "review_status": "draft", "notes": notes,
    }


SS, CT, CM, NU, DL, J2, OT = ("STATEMENT_START", "CONTINUATION", "COMMENT", "NULL", "DELIMITER",
                              "JES2", "OTHER")
P = {"continues": "PARAMETER"}
Q = {"continues": "QUOTED"}
K = {"continues": "COMMENT"}

c1, c3, c4 = ("inputs/continuation/cont001.jcl", "inputs/continuation/cont003.jcl",
              "inputs/continuation/cont004.jcl")
c5, c7, c8, c9 = ("inputs/continuation/cont005.jcl", "inputs/continuation/cont007.jcl",
                  "inputs/continuation/cont008.jcl", "inputs/continuation/cont009.jcl")
q1, q2 = "inputs/quotes/qp001.jcl", "inputs/quotes/qp002.jcl"
i5, s1, v5 = "inputs/if/if005.jcl", "inputs/instream/is001.jcl", "inputs/invalid/inv005.jcl"

NEW: dict[str, list[dict[str, Any]]] = {
    "continuation_columns.yaml": [
        lex_case("G-CONT-101", "CONTINUATION_COLUMNS",
                 "Lexical: IBM continuation example 1 - one logical statement over records 3-4, fields and tokens with positions.",
                 ["JCL-REC-001", "JCL-FMT-001", "JCL-FMT-002", "JCL-CONT-001"], c1,
                 R(SS, SS, (SS, P), CT),
                 [{"span": [1, 1], "name": f(c1, 1, "CONT001"), "operation": f(c1, 1, "JOB", 9), "parameter_text": ""},
                  {"span": [2, 2], "name": f(c1, 2, "STEP1"), "operation": f(c1, 2, "EXEC"), "parameter_text": "PGM=IEFBR14"},
                  {"span": [3, 4], "lines": [3, 4], "name": f(c1, 3, "DD1"), "operation": f(c1, 3, "DD", 5),
                   "parameter_text": "DSNAME=SWITCH.LEVEL18.GROUP12,UNIT=3390,VOLUME=339023,SPACE=(TRK,(80,15)),DISP=(,PASS)",
                   "comments": [], "end": "COMPLETE",
                   "tokens": T("DSNAME", "=", "SWITCH.LEVEL18.GROUP12", ",", "UNIT", "=", "3390", ",",
                               "VOLUME", "=", "339023", ",", "SPACE", "=", "(", "TRK", ",", "(", "80", ",",
                               "15", ")", ")", ",", "DISP", "=", "(", ",", "PASS", ")")}],
                 notes="Tokens are lexical only: no keyword/positional classification (Step 4a instruction C)."),
        lex_case("G-CONT-102", "CONTINUATION_COLUMNS",
                 "Lexical: IBM example 3 - parameter continuation (comma+blank) then comment continuation by nonblank column 72; comment text kept raw with positions.",
                 ["JCL-CONT-001", "JCL-CONT-004", "JCL-FMT-007"], c3,
                 R(SS, (SS, P), (CT, P), (CT, K), (CT, K), CT),
                 [{"span": [1, 1]},
                  {"span": [2, 6], "lines": [2, 3, 4, 5, 6], "name": f(c3, 2, "STP4"), "operation": f(c3, 2, "EXEC"),
                   "parameter_text": "PROC=BILLING,COND.PAID=((20,LT),EVEN),COND.LATE=(60,GT,FIND),COND.BILL=((20,GE),(30,LT,CHGE))",
                   "comments": [c(c3, 4, "THIS STATEMENT CALLS"),
                                c(c3, 5, "THE BILLING PROCEDURE AND SPECIFIES RETURN CODE TESTS"),
                                c(c3, 6, "FOR THREE PROCEDURE STEPS.")],
                   "end": "COMPLETE"}]),
        lex_case("G-CONT-103", "CONTINUATION_COLUMNS",
                 "Lexical: IBM example 4 - apostrophe-enclosed value extended to column 71 and continued at column 16; STRING token value is the joined text.",
                 ["JCL-CONT-003", "JCL-SYN-001"], c4,
                 R(SS, (SS, Q), CT),
                 [{"span": [1, 1]},
                  {"span": [2, 3], "lines": [2, 3], "name": f(c4, 2, "S1"), "operation": f(c4, 2, "EXEC"),
                   "parameter_text": "PGM=IEFBR14,PARM='THIS IS A LONG PARAMETER WITHIN APOSTROPHES, CONTINUED IN COLUMN 16 OF THE NEXT RECORD'",
                   "comments": [], "end": "COMPLETE",
                   "tokens": T("PGM", "=", "IEFBR14", ",", "PARM", "=",
                               "S:THIS IS A LONG PARAMETER WITHIN APOSTROPHES, CONTINUED IN COLUMN 16 OF THE NEXT RECORD")}],
                 case_type="boundary"),
        lex_case("G-CONT-104", "CONTINUATION_COLUMNS",
                 "Lexical: continuation expected but column 3 is not blank - the record starts a new statement; the first statement ends with MISSING_CONTINUATION.",
                 ["JCL-CONT-002"], c5,
                 R(SS, SS, (SS, P), SS),
                 [{"span": [1, 1]}, {"span": [2, 2]},
                  {"span": [3, 3], "lines": [3], "parameter_text": "DSN=A.B,", "end": "MISSING_CONTINUATION"},
                  {"span": [4, 4], "name": f(c5, 4, "DD2"), "parameter_text": "DSN=C.D", "end": "COMPLETE"}],
                 diags=[{"code": "LEX-E002", "severity": "ERROR", "line": 4, "column": 3}], case_type="invalid"),
        lex_case("G-CONT-105", "CONTINUATION_COLUMNS",
                 "Lexical: continuation text starting exactly in column 4 and in column 16.",
                 ["JCL-CONT-001"], c7,
                 R(SS, SS, (SS, P), (CT, P), CT),
                 [{"span": [1, 1]}, {"span": [2, 2]},
                  {"span": [3, 5], "lines": [3, 4, 5], "parameter_text": "DSN=A.B,DISP=SHR,UNIT=SYSDA", "end": "COMPLETE"}],
                 case_type="boundary"),
        lex_case("G-CONT-106", "CONTINUATION_COLUMNS",
                 "Lexical: columns 73-80 kept as sequence field and never lexed; nonblank column 72 after 'comma, blank' is ignored (no comment continuation).",
                 ["JCL-REC-003", "JCL-CONT-004"], c8,
                 R((SS, {"seq": "00010000"}), (SS, {"seq": "00020000"}),
                   (SS, {"continues": "PARAMETER", "seq": "00030000"}), (CT, {"seq": "00040000"})),
                 [{"span": [1, 1], "parameter_text": ""}, {"span": [2, 2], "parameter_text": "PGM=IEFBR14"},
                  {"span": [3, 4], "parameter_text": "DSN=A.B,DISP=SHR", "comments": [], "end": "COMPLETE"}],
                 case_type="boundary"),
        lex_case("G-CONT-107", "CONTINUATION_COLUMNS",
                 "Lexical: a comment statement between continuation records is its own record kind; the continued statement's records are 3 and 5.",
                 ["JCL-CONT-006", "JCL-STMT-COMMENT"], c9,
                 R(SS, SS, (SS, P), CM, CT),
                 [{"span": [1, 1]}, {"span": [2, 2]},
                  {"span": [3, 5], "lines": [3, 5], "parameter_text": "DSN=A.B,DISP=SHR", "end": "COMPLETE"}]),
    ],
    "quotes_parentheses.yaml": [
        lex_case("G-QP-101", "QUOTES_PARENTHESES",
                 "Lexical: doubled apostrophe, and a comma and blank inside apostrophes, stay inside one STRING token; the blank does not end the parameter field.",
                 ["JCL-SYN-001", "JCL-SYN-002"], q1,
                 R(SS, SS),
                 [{"span": [1, 1], "parameter_text": "D58-D04,'O''NEIL'", "tokens": T("D58-D04", ",", "S:O'NEIL")},
                  {"span": [2, 2], "parameter_text": "PGM=IEFBR14,ACCT='123+456',PARM='A,B C'", "comments": [],
                   "tokens": T("PGM", "=", "IEFBR14", ",", "ACCT", "=", "S:123+456", ",", "PARM", "=", "S:A,B C")}]),
        lex_case("G-QP-102", "QUOTES_PARENTHESES",
                 "Lexical: nested parentheses and commas inside parentheses across a continuation; parenthesis tokens are balanced.",
                 ["JCL-FMT-005", "JCL-CONT-001"], q2,
                 R(SS, SS, (SS, P), CT),
                 [{"span": [1, 1]}, {"span": [2, 2]},
                  {"span": [3, 4], "parameter_text": "DSN=A.B,DISP=(NEW,CATLG,DELETE),SPACE=(CYL,(1,1),RLSE),DCB=(RECFM=FB,LRECL=80)",
                   "end": "COMPLETE",
                   "tokens": T("DSN", "=", "A.B", ",", "DISP", "=", "(", "NEW", ",", "CATLG", ",", "DELETE", ")", ",",
                               "SPACE", "=", "(", "CYL", ",", "(", "1", ",", "1", ")", ",", "RLSE", ")", ",",
                               "DCB", "=", "(", "RECFM", "=", "FB", ",", "LRECL", "=", "80", ")")}]),
    ],
    "if_then_else.yaml": [
        lex_case("G-IF-101", "IF_THEN_ELSE",
                 "Lexical: an IF relational expression with blanks, continued where a blank is valid; the parameter field ends at THEN; comment after THEN.",
                 ["JCL-IF-004", "JCL-IF-002", "JCL-FMT-007"], i5,
                 R(SS, SS, (SS, P), CT, SS, SS),
                 [{"span": [1, 1]}, {"span": [2, 2]},
                  {"span": [3, 4], "name": f(i5, 3, "TESTCON"), "operation": f(i5, 3, "IF", 9),
                   "parameter_text": "(RC = 8 | RC = 10 | RC = 12 | RC = 14)  THEN",
                   "comments": [c(i5, 4, "COMMENTS OK HERE")], "end": "COMPLETE",
                   "tokens": T("(", "RC", "O:=", "8", "O:|", "RC", "O:=", "10", "O:|", "RC", "O:=", "12", "O:|",
                               "RC", "O:=", "14", ")", "THEN")},
                  {"span": [5, 5]}, {"span": [6, 6], "operation": f(i5, 6, "ENDIF"), "parameter_text": ""}],
                 notes="parameter_text joins IF records with one blank (blanks are significant in relational expressions); within a record, blanks are kept as coded. The OPERATOR token type is lexical only."),
    ],
    "instream_data.yaml": [
        lex_case("G-IS-101", "INSTREAM_DATA",
                 "Lexical: record kinds around in-stream data - data records are OTHER (kept raw, not interpreted), /* is DELIMITER.",
                 ["JCL-REC-001", "JCL-STMT-DELIM"], s1,
                 R(SS, SS, SS, (OT, {"raw": " SORT FIELDS=(1,10,CH,A)"}), (OT, {"raw": " END"}), DL, SS),
                 [{"span": [1, 1]}, {"span": [2, 2]}, {"span": [3, 3], "parameter_text": "*"}, {"span": [7, 7]}],
                 notes="Step 4a: the Lexer classifies records by their leading characters only. Deciding that OTHER records are DD * data (and the JES-dependent end rules) is a later stage. A data record starting with // in DD DATA would be lexed as STATEMENT_START here and must be reclassified later; that limitation is why DD DATA inputs are not used in lexical cases."),
    ],
    "invalid_unresolved.yaml": [
        lex_case("G-INV-101", "INVALID_UNRESOLVED",
                 "Lexical: /* followed by a nonblank column 3 is a JES2 control statement record, not a delimiter.",
                 ["JCL-JES2-001", "JCL-STMT-DELIM"], v5,
                 R(SS, (J2, {"raw": "/*JOBPARM PROCLIB=PROC01"}), SS),
                 [{"span": [1, 1]}, {"span": [3, 3], "operation": f(v5, 3, "EXEC")}],
                 case_type="boundary",
                 notes="The Delimiter statement has /* followed by comments after a blank (JES2: blank after the delimiter characters, p.309). A nonblank column 3 is classified as JES2. Which JES2 statement it is, is not decided."),
    ],
    "proc_pend.yaml": [
        {
            "test_id": "G-PP-010", "category": "PROC_PEND",
            "description": "Nested procedure INVOCATION (an EXEC inside in-stream procedure OUTER calls in-stream procedure INNER) is valid and distinct from a nested definition.",
            "rule_ids": ["JCL-PROC-007", "JCL-PROC-001"], "input_file": "inputs/proc/pp010.jcl",
            "input_kind": "job", "case_type": "valid", "validation_stage": "syntactic",
            "expected_structure": {"view": "statements", "statements": [
                {"kind": "JOB", "span": [1, 1], "name": "PP010"},
                {"kind": "PROC", "span": [2, 2], "name": "INNER", "positional": [], "keywords": []},
                {"kind": "EXEC", "span": [3, 3], "name": "IS1", "positional": [], "keywords": [["PGM", "IEFBR14"]]},
                {"kind": "PEND", "span": [4, 4], "name": None},
                {"kind": "PROC", "span": [5, 5], "name": "OUTER", "positional": [], "keywords": []},
                {"kind": "EXEC", "span": [6, 6], "name": "OS1", "positional": ["INNER"], "keywords": []},
                {"kind": "PEND", "span": [7, 7], "name": None},
                {"kind": "EXEC", "span": [8, 8], "name": "STEP1", "positional": ["OUTER"], "keywords": []}],
                "blocks": [{"kind": "PROC", "name": "INNER", "start": 2, "end": 4},
                           {"kind": "PROC", "name": "OUTER", "start": 5, "end": 7}]},
            "expected_diagnostics": {"mode": "exact", "items": []},
            "oracle_method": M_IBM, "oracle_author": AUTHOR, "review_status": "draft",
            "notes": "User decision A4. INNER is defined before the EXEC (in OUTER) that calls it. Nesting depth here is 2 (limit 15, p.32). Resolution of the nested call is a Step 5 matter.",
        },
    ],
}


def main() -> None:
    for fname, cases in NEW.items():
        p = SUITE / "cases" / fname
        text = p.read_text(encoding="utf-8")
        for case in cases:
            if f"test_id: {case['test_id']}\n" in text:
                raise SystemExit(f"{case['test_id']} already exists; edit it by hand with a change_log")
            dumped = yaml.safe_dump([case], sort_keys=False, allow_unicode=True, width=1000)
            indented = "\n".join(("  " + ln) if ln else ln for ln in dumped.rstrip("\n").split("\n"))
            text = text.rstrip("\n") + "\n\n" + indented + "\n"
        p.write_text(text, encoding="utf-8", newline="\n")
        print(f"appended {len(cases)} case(s) to {fname}")


if __name__ == "__main__":
    main()

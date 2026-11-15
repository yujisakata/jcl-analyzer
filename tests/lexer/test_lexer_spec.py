"""Step 4a Lexer: tests derived from IBM SA23-1385-70 rules (rule IDs cited per test).

Written before the implementation from the primary text; expected values are hand-derived.
Limitation (stated in the Step 4a report): the same AI wrote these tests and the Lexer, so their
independence is procedural (spec first, cited), not organizational. Formal assurance requires the
user's review of the lexical Golden cases.
"""

from __future__ import annotations

from jclprof.lexer import LexResult, lex_bytes, lex_text


def kinds(r: LexResult) -> list[str]:
    return [rec.kind for rec in r.records]


def codes(r: LexResult) -> list[tuple[str, int | None, int | None]]:
    return [(d.code, d.line, d.column) for d in r.diagnostics]


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- record kinds (JCL-REC-001 etc.)
def test_record_kinds_by_identifier_field() -> None:
    r = lex_text(J("//A JOB", "//* COMMENT", "/*", "/* COMMENT AFTER DELIMITER", "/*JOBPARM X=1",
                   " DATA RECORD", "//", "@@"))
    assert kinds(r) == ["STATEMENT_START", "COMMENT", "DELIMITER", "DELIMITER", "JES2", "OTHER",
                        "NULL", "OTHER"]
    assert r.diagnostics == ()  # OTHER records are kept raw; their meaning is decided later


def test_every_record_preserved_with_terminators() -> None:
    text = "//A JOB\r\n X\r\n//B EXEC PGM=X"
    r = lex_text(text)
    assert [rec.raw for rec in r.records] == ["//A JOB", " X", "//B EXEC PGM=X"]
    assert "".join(rec.raw + rec.terminator for rec in r.records) == text


def test_null_requires_columns_3_to_72_blank() -> None:  # JCL-STMT-NULL
    r = lex_text(J("//", "//" + " " * 70, "//         X"))
    assert kinds(r) == ["NULL", "NULL", "STATEMENT_START"]


# ---------------------------------------------------------------- fields (JCL-FMT-001/002/007)
def test_name_operation_parameter_comment_fields_with_positions() -> None:
    r = lex_text(J("//STEP1    EXEC PGM=IEFBR14,REGION=0M   RUN IT"))
    (s,) = r.statements
    assert (s.name.text, s.name.line, s.name.column) == ("STEP1", 1, 3)  # type: ignore[union-attr]
    assert (s.operation.text, s.operation.column) == ("EXEC", 12)  # type: ignore[union-attr]
    assert s.parameter_text == "PGM=IEFBR14,REGION=0M"
    # parameter field = columns 17-37, three blanks, comment from column 41
    assert [(c.line, c.column, c.text) for c in s.comments] == [(1, 41, "RUN IT")]


def test_statement_without_name() -> None:
    r = lex_text(J("//         PEND", "//   SET HLQ=X"))
    assert [s.name for s in r.statements] == [None, None]
    assert [s.operation.text for s in r.statements] == ["PEND", "SET"]  # type: ignore[union-attr]


def test_lexer_does_not_classify_statements() -> None:  # Step 4a instruction C
    r = lex_text(J("//A JOB", "//S EXEC PGM=X", "//D DD DSN=A"))
    d = r.to_dict()
    for s in d["statements"]:
        assert "kind" not in s and "statement_type" not in s


# ---------------------------------------------------------------- continuation (JCL-CONT-*)
def test_parameter_continuation_ibm_example_1() -> None:  # JCL-CONT-001
    r = lex_text(J("//DD1  DD   DSNAME=SWITCH.LEVEL18.GROUP12,UNIT=3390,",
                   "//     VOLUME=339023,SPACE=(TRK,(80,15)),DISP=(,PASS)"))
    assert kinds(r) == ["STATEMENT_START", "CONTINUATION"]
    assert r.records[0].continues == "PARAMETER"
    (s,) = r.statements
    assert s.span == (1, 2) and s.lines == (1, 2) and s.end == "COMPLETE"
    assert s.parameter_text == ("DSNAME=SWITCH.LEVEL18.GROUP12,UNIT=3390,VOLUME=339023,"
                                "SPACE=(TRK,(80,15)),DISP=(,PASS)")


def test_comment_on_continued_record_ibm_example_2() -> None:  # JCL-CONT-001, JCL-FMT-007
    r = lex_text(J("//DS1 DD  DSNAME=INDS,DISP=OLD,CHKPT=EOV,   MY INPUT DATA SET",
                   "//     UNIT=SYSSQ,VOLUME=SER=(TAPE01,TAPE02,TAPE03)"))
    (s,) = r.statements
    assert s.parameter_text == ("DSNAME=INDS,DISP=OLD,CHKPT=EOV,UNIT=SYSSQ,"
                                "VOLUME=SER=(TAPE01,TAPE02,TAPE03)")
    assert [c.text for c in s.comments] == ["MY INPUT DATA SET"]


def test_comment_continuation_by_column_72_ibm_example_3() -> None:  # JCL-CONT-004
    r = lex_text(J("//STP4  EXEC PROC=BILLING,COND.PAID=((20,LT),EVEN),",
                   "//     COND.LATE=(60,GT,FIND),",
                   "//     COND.BILL=((20,GE),(30,LT,CHGE))  THIS STATEMENT CALLS".ljust(71) + "X",
                   "//     THE BILLING PROCEDURE AND SPECIFIES RETURN CODE TESTS".ljust(71) + "X",
                   "//     FOR THREE PROCEDURE STEPS."))
    assert [rec.continues for rec in r.records] == ["PARAMETER", "PARAMETER", "COMMENT", "COMMENT",
                                                    None]
    (s,) = r.statements
    assert s.span == (1, 5)
    assert [c.text for c in s.comments] == [
        "THIS STATEMENT CALLS", "THE BILLING PROCEDURE AND SPECIFIES RETURN CODE TESTS",
        "FOR THREE PROCEDURE STEPS."]
    assert [c.column for c in s.comments] == [42, 8, 8]


def test_apostrophe_continuation_column_71_to_16_ibm_example_4() -> None:  # JCL-CONT-003
    first = "//S1       EXEC PGM=IEFBR14,PARM='THIS IS A LONG PARAMETER WITHIN APOST"
    assert len(first) == 71
    r = lex_text(J(first, "//             ROPHES, CONTINUED IN COLUMN 16 OF THE NEXT RECORD'"))
    assert r.records[0].continues == "QUOTED"
    (s,) = r.statements
    strings = [t for t in s.tokens if t.type == "STRING"]
    assert [t.value for t in strings] == [
        "THIS IS A LONG PARAMETER WITHIN APOSTROPHES, CONTINUED IN COLUMN 16 OF THE NEXT RECORD"]
    assert (strings[0].line, strings[0].column) == (1, 34)
    assert r.diagnostics == ()


def test_trailing_blanks_inside_apostrophes_kept_to_column_71() -> None:  # JCL-CONT-003
    # 80-byte record semantics: a short source line is treated as blank-padded to column 80.
    r = lex_text(J("//S1 EXEC PGM=X,PARM='AB", "//             CD'"))
    (s,) = r.statements
    (t,) = [t for t in s.tokens if t.type == "STRING"]
    assert t.value == "AB" + " " * (71 - len("//S1 EXEC PGM=X,PARM='AB")) + "CD"


def test_column_72_ignored_after_comma_blank() -> None:  # JCL-CONT-004 note
    r = lex_text(J("//DD1 DD DSN=A.B,".ljust(71) + "X", "//      DISP=SHR"))
    assert r.records[0].continues == "PARAMETER"
    assert r.statements[0].comments == ()
    assert r.statements[0].parameter_text == "DSN=A.B,DISP=SHR"


def test_sequence_columns_73_80_not_lexed() -> None:  # JCL-REC-003
    r = lex_text(J("//DD1 DD DSN=A.B,".ljust(72) + "00010000",
                   "//      DISP=SHR".ljust(72) + "ABCDEFGH"))
    assert [rec.seq for rec in r.records] == ["00010000", "ABCDEFGH"]
    assert r.statements[0].parameter_text == "DSN=A.B,DISP=SHR"
    assert all("ABCDEFGH" not in t.text for t in r.statements[0].tokens)


def test_column_3_not_blank_starts_new_statement() -> None:  # JCL-CONT-002
    r = lex_text(J("//DD1 DD DSN=A.B,", "//DD2 DD DSN=C.D"))
    assert kinds(r) == ["STATEMENT_START", "STATEMENT_START"]
    assert [s.end for s in r.statements] == ["MISSING_CONTINUATION", "COMPLETE"]
    assert codes(r) == [("LEX-E002", 2, 3)]


def test_continuation_column_range_4_to_16() -> None:  # JCL-CONT-001
    ok = lex_text(J("//DD1 DD DSN=A.B,", "// DISP=SHR,", "//             UNIT=SYSDA"))
    assert ok.diagnostics == () and ok.statements[0].parameter_text == "DSN=A.B,DISP=SHR,UNIT=SYSDA"
    bad = lex_text(J("//DD1 DD DSN=A.B,", "//".ljust(16) + "DISP=SHR"))  # text in column 17
    assert codes(bad) == [("LEX-E003", 2, 17)]
    assert bad.statements[0].parameter_text == "DSN=A.B,DISP=SHR"  # text kept, not dropped


def test_comment_statement_between_continuations() -> None:  # JCL-CONT-006
    r = lex_text(J("//DD1 DD DSN=A.B,", "//* NOTE", "//         DISP=SHR"))
    assert kinds(r) == ["STATEMENT_START", "COMMENT", "CONTINUATION"]
    (s,) = r.statements
    assert s.span == (1, 3) and s.lines == (1, 3)


def test_null_after_continued_statement_keeps_position_relation() -> None:  # JCL-CONT-007, A7
    r = lex_text(J("//DD1 DD DSN=A.B,", "//", "//NEXT JOB"))
    assert kinds(r) == ["STATEMENT_START", "NULL", "STATEMENT_START"]
    assert r.statements[0].end == "NULL_STATEMENT"
    assert r.statements[0].parameter_text == "DSN=A.B,"
    assert codes(r) == [("LEX-W001", 2, None)]


def test_comment_statement_through_column_80() -> None:  # JCL-STMT-COMMENT, JCL-REC-003
    line = "//* TEXT".ljust(72) + "ENDSHERE"
    r = lex_text(J(line))
    assert r.records[0].kind == "COMMENT"
    assert r.records[0].comment_text == "TEXT" + " " * 64 + "ENDSHERE"
    assert r.records[0].seq == ""  # comment statements have no sequence field


def test_comment_continuation_not_found() -> None:  # JCL-CONT-004
    r = lex_text(J("//S EXEC PGM=X  COMMENT".ljust(71) + "X", "//NEXT EXEC PGM=Y"))
    assert codes(r) == [("LEX-W003", 1, 72)]
    assert r.statements[0].end == "COMPLETE"


def test_missing_continuation_at_end_or_before_other_record() -> None:  # JCL-CONT-001, POL-001
    r = lex_text(J("//DD1 DD DSN=A.B,"))
    assert codes(r) == [("LEX-E005", 1, None)] and r.statements[0].end == "END_OF_INPUT"
    r2 = lex_text(J("//DD1 DD DSN=A.B,", " DATA"))
    assert codes(r2) == [("LEX-E005", 1, None)] and r2.statements[0].end == "MISSING_CONTINUATION"


# ---------------------------------------------------------------- quotes and parentheses
def test_doubled_apostrophe_and_blank_inside_quotes() -> None:  # JCL-SYN-001
    r = lex_text(J("//S EXEC PGM=X,PARM='O''NEIL, A B'  COMMENT"))
    (s,) = r.statements
    strings = [(t.type, t.value) for t in s.tokens if t.type == "STRING"]
    assert strings == [("STRING", "O'NEIL, A B")]
    assert s.parameter_text == "PGM=X,PARM='O''NEIL, A B'"
    assert [c.text for c in s.comments] == ["COMMENT"]


def test_parentheses_inside_quotes_not_counted() -> None:  # JCL-SYN-001, JCL-FMT-005
    r = lex_text(J("//S EXEC PGM=X,PARM='(A'"))
    assert r.diagnostics == ()


def test_token_stream() -> None:
    r = lex_text(J("//D DD DISP=(,CATLG),DCB=(RECFM=FB,LRECL=80)"))
    assert [(t.type, t.text) for t in r.statements[0].tokens] == [
        ("WORD", "DISP"), ("EQUALS", "="), ("LPAREN", "("), ("COMMA", ","), ("WORD", "CATLG"),
        ("RPAREN", ")"), ("COMMA", ","), ("WORD", "DCB"), ("EQUALS", "="), ("LPAREN", "("),
        ("WORD", "RECFM"), ("EQUALS", "="), ("WORD", "FB"), ("COMMA", ","), ("WORD", "LRECL"),
        ("EQUALS", "="), ("WORD", "80"), ("RPAREN", ")")]
    assert [t.column for t in r.statements[0].tokens][:3] == [8, 12, 13]


def test_unterminated_apostrophe() -> None:  # JCL-SYN-001, POL-001
    r = lex_text(J("//STEP1    EXEC PGM=IEFBR14,PARM='ABC"))
    assert codes(r) == [("LEX-E001", 1, 34)]


def test_unbalanced_parentheses() -> None:  # JCL-FMT-005, POL-001
    r = lex_text(J("//D1 DD DSN=A.B,SPACE=(CYL,(1,1)"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("LEX-E004", 1)]
    r2 = lex_text(J("//D1 DD DSN=A.B,SPACE=(CYL,1))"))
    assert [(c, ln) for c, ln, _ in codes(r2)] == [("LEX-E004", 1)]


# ---------------------------------------------------------------- IF relational expressions
def test_if_expression_blanks_then_and_continuation() -> None:  # JCL-IF-004, JCL-IF-002
    r = lex_text(J("//TESTCON  IF (RC = 8 | RC = 10 | RC = 12 |",
                   "//            RC = 14)  THEN         COMMENTS OK HERE"))
    assert r.records[0].continues == "PARAMETER"
    (s,) = r.statements
    assert s.parameter_text == "(RC = 8 | RC = 10 | RC = 12 | RC = 14)  THEN"
    assert [c.text for c in s.comments] == ["COMMENTS OK HERE"]
    assert [(t.type, t.text) for t in s.tokens][:4] == [("LPAREN", "("), ("WORD", "RC"),
                                                         ("OPERATOR", "="), ("WORD", "8")]
    assert (s.tokens[-1].type, s.tokens[-1].text) == ("WORD", "THEN")


def test_if_not_sign() -> None:  # JCL-IF-002
    r = lex_text(J("//T IF ¬(RC > 8) THEN"))
    assert [(t.type, t.text) for t in r.statements[0].tokens] == [
        ("OPERATOR", "¬"), ("LPAREN", "("), ("WORD", "RC"), ("OPERATOR", ">"), ("WORD", "8"),
        ("RPAREN", ")"), ("WORD", "THEN")]


# ---------------------------------------------------------------- physical / encoding
def test_long_record_and_tab_diagnosed_but_kept() -> None:  # JCL-REC-004, JCL-REC-002
    long = "//A JOB".ljust(80) + "EXTRA"
    r = lex_text(J(long, "//B\tEXEC PGM=X"))
    assert r.records[0].raw == long
    assert codes(r) == [("LEX-W004", 1, 81), ("LEX-W005", 2, 4)]


def test_explicit_encoding_and_decode_failure() -> None:  # CTX-02, POL-006
    ok = lex_bytes("//A JOB\n".encode("cp037"), encoding="cp037")
    assert ok.records[0].raw == "//A JOB" and ok.encoding == "cp037"
    bad = lex_bytes(b"//A JOB\n//B \xff\n", encoding="utf-8")
    assert bad.records == () and codes(bad) == [("LEX-E006", 2, 5)]


def test_deterministic() -> None:
    text = J("//DD1 DD DSN=A.B,", "//* X", "//   DISP=SHR  C", " DATA", "/*")
    assert lex_text(text).to_dict() == lex_text(text).to_dict()

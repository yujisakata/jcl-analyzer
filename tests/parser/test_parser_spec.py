"""Step 4b Parser: tests derived from IBM SA23-1385-70 rules (rule IDs per test), written before
the implementation. Same-author limitation applies (see Step 4b report)."""

from __future__ import annotations

from typing import Any

from jclprof.parser import ParseResult, parse_text


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def codes(r: ParseResult) -> list[tuple[str, int | None, int | None]]:
    return [(d.code, d.line, d.column) for d in r.diagnostics]


def stmt(r: ParseResult, line: int) -> Any:
    return next(s for s in r.statements if s.span and s.span[0] == line)


def view(v: Any) -> Any:
    return v.to_view() if v is not None else None


# ---------------------------------------------------------------- statement kinds / names
def test_statement_kinds() -> None:  # JCL-FMT-002, JCL-FMT-009
    r = parse_text(J("//J JOB", "//L JCLLIB ORDER=A.B", "// SET A=1", "//I INCLUDE MEMBER=X",
                     "//S EXEC PGM=X", "//D DD DUMMY", "//O OUTPUT CLASS=A", "//C IF RC=0 THEN",
                     "// ELSE", "// ENDIF", "//P PROC", "// PEND"))
    assert [s.kind for s in r.statements] == ["JOB", "JCLLIB", "SET", "INCLUDE", "EXEC", "DD",
                                              "OUTPUT", "IF", "ELSE", "ENDIF", "PROC", "PEND"]


def test_unknown_operation_preserved() -> None:  # JCL-FMT-002, POL-006 (A6)
    r = parse_text(J("//J JOB", "//STEP1    EXCE PGM=IEFBR14"))
    s = stmt(r, 2)
    assert (s.kind, s.operation, s.name.text) == ("UNKNOWN", "EXCE", "STEP1")
    assert codes(r) == [("PAR-W003", 2, 12)]


def test_name_rules() -> None:  # JCL-FMT-001, JCL-JOB-001, JCL-DD-002
    ok = parse_text(J("//@#$JOB08 JOB", "//$STEP#08 EXEC PGM=X", "//DD@ABCDE DD DUMMY",
                      "//CALLER EXEC PROC=P", "//STEPSIX.DD4 DD DUMMY"))
    assert ok.diagnostics == ()
    bad = parse_text(J("//J JOB", "//STEPNAME9 EXEC PGM=X", "//1STEP EXEC PGM=X",
                       "//step3 EXEC PGM=X", "//         JOB"))
    assert codes(bad) == [("PAR-E002", 2, 3), ("PAR-E002", 3, 3), ("PAR-E002", 4, 3),
                          ("PAR-E002", 5, 3)]


def test_procstep_ddname_in_program_step_is_informational() -> None:  # JCL-DD-002 (p.76)
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//PSTEP.DD1 DD DUMMY"))
    assert codes(r) == [("PAR-I002", 3, 3)]
    assert r.jobs[0].steps[0].dds[0].ddname == "DD1"  # only the ddname qualifier is used


# ---------------------------------------------------------------- parameter values
def test_positional_null_and_quoted() -> None:  # JCL-FMT-003, JCL-SYN-001/002
    r = parse_text(J("//JED002   JOB ,'A.B.C.'"))
    assert [view(v) for v in stmt(r, 1).positional] == [None, {"q": "A.B.C."}]


def test_keyword_values_lists_and_subkeywords() -> None:  # JCL-FMT-004/005/006
    r = parse_text(J("//J JOB", "//S EXEC PGM=X",
                     "//D DD DSN=A.B,DISP=(,CATLG,DELETE),SPACE=(CYL,(1,1),RLSE),",
                     "//        DCB=(RECFM=FB,LRECL=80),VOLUME=SER=339023,UNIT="))
    d = stmt(r, 3)
    assert [(k.name, view(k.value)) for k in d.keywords] == [
        ("DSN", "A.B"), ("DISP", [None, "CATLG", "DELETE"]),
        ("SPACE", ["CYL", ["1", "1"], "RLSE"]),
        ("DCB", [{"kw": ["RECFM", "FB"]}, {"kw": ["LRECL", "80"]}]),
        ("VOLUME", {"kw": ["SER", "339023"]}), ("UNIT", None)]
    assert d.span == (3, 4)


def test_quoted_values_keep_commas_parentheses_apostrophes() -> None:  # JCL-SYN-001
    r = parse_text(J("//S EXEC PGM=X,PARM='A,(B) C''D',ACCT='123+456'"))
    assert [(k.name, view(k.value)) for k in stmt(r, 1).keywords] == [
        ("PGM", "X"), ("PARM", {"q": "A,(B) C'D"}), ("ACCT", {"q": "123+456"})]


def test_dsname_member_generation_and_special_forms() -> None:  # JCL-SYN-002/003/004
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//D1 DD DSN=PDS1(MEMA)", "//D2 DD DSN=GDS(+1)",
                     "//D3 DD DSN=&&TEMPDS", "//D4 DD DSN=*.D1", "//D5 DD DSN=&HLQ..X.Y(-2)"))
    assert [view(stmt(r, n).keywords[0].value) for n in range(3, 8)] == [
        "PDS1(MEMA)", "GDS(+1)", "&&TEMPDS", "*.D1", "&HLQ..X.Y(-2)"]


def test_positional_after_keyword() -> None:  # JCL-FMT-003, POL-001
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//IN       DD   DSN=A.B,*"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("PAR-E007", 3)]


def test_subparameter_nesting_limit() -> None:  # JCL-FMT-008
    ok = parse_text(J("//J JOB", "//S EXEC PGM=X", "//D DD SPACE=(CYL,(1,1))"))
    assert ok.diagnostics == ()
    bad = parse_text(J("//J JOB", "//S EXEC PGM=X", "//D DD SPACE=(CYL,(1,(1)))"))
    assert [(c, ln) for c, ln, _ in codes(bad)] == [("PAR-E008", 3)]


def test_value_positions_trace_to_source() -> None:  # CTX-01
    text = J("//DD1  DD   DSNAME=SWITCH.LEVEL18.GROUP12,UNIT=3390,",
             "//     VOLUME=339023,SPACE=(TRK,(80,15)),DISP=(,PASS)")
    r = parse_text(text)
    lines = text.split("\n")
    for k in stmt(r, 1).keywords:
        assert lines[k.line - 1][k.column - 1:].startswith(k.name)
        if k.value is not None:
            v = k.value
            assert lines[v.line - 1][v.column - 1:].startswith(v.text[:1])
    assert (stmt(r, 1).keywords[2].line, stmt(r, 1).keywords[2].column) == (2, 8)


# ---------------------------------------------------------------- EXEC
def test_exec_targets() -> None:  # JCL-EXEC-001
    r = parse_text(J("//J JOB", "//A EXEC PGM=IEFBR14", "//B EXEC PROC=PAYROLL,REGION=0M",
                     "//C EXEC PAYROLL", "//D EXEC PGM=*.A.SYSLMOD"))
    assert [s.target for s in r.jobs[0].steps] == [("PGM", "IEFBR14"), ("PROC", "PAYROLL"),
                                                   ("PROC", "PAYROLL"), ("PGM", "*.A.SYSLMOD")]


def test_exec_without_target() -> None:  # JCL-EXEC-001
    r = parse_text(J("//J JOB", "//STEP1    EXEC TIME=5"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("PAR-E006", 2)]


# ---------------------------------------------------------------- hierarchy
def test_job_step_dd_membership_and_joblib() -> None:  # JCL-DD-001, JCL-DD-013
    r = parse_text(J("//PAYROLL JOB  JONES,CLASS=C", "//JOBLIB  DD   DSNAME=PRIVATE.LIB4,DISP=SHR",
                     "//         DD   DSNAME=PRIVATE.LIB5,DISP=SHR", "//STEP1   EXEC PGM=SCAN",
                     "//IN      DD   DSN=A,DISP=SHR", "//STEPLIB DD   DSN=L,DISP=SHR",
                     "//STEP2   EXEC PGM=UPDATE", "//OUT     DD   SYSOUT=*", "//JOB2    JOB",
                     "//S       EXEC PGM=X"))
    assert r.diagnostics == ()
    j1, j2 = r.jobs
    assert [(d.ddname, d.concat_head) for d in j1.job_level_dds] == [("JOBLIB", "JOBLIB"),
                                                                      (None, "JOBLIB")]
    assert [d.concat_index for d in j1.job_level_dds] == [0, 1]
    assert [(s.name, [d.ddname for d in s.dds]) for s in j1.steps] == [
        ("STEP1", ["IN", "STEPLIB"]), ("STEP2", ["OUT"])]
    assert j1.steps[0].dds[1].special == "STEPLIB"
    assert all(d.level == "STEP" for s in j1.steps for d in s.dds)
    assert j1.job_level_dds[0].level == "JOB"
    assert (j2.name, [s.name for s in j2.steps]) == ("JOB2", ["S"])


def test_joblib_after_exec_and_dd_before_exec() -> None:  # JCL-DD-013
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//JOBLIB DD DSN=L,DISP=SHR"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("PAR-E020", 3)]
    r2 = parse_text(J("//J JOB", "//X DD DSN=A,DISP=SHR", "//S EXEC PGM=X"))
    assert [(c, ln) for c, ln, _ in codes(r2)] == [("PAR-W008", 2)]
    assert [d.ddname for d in r2.jobs[0].job_level_dds] == ["X"]


def test_concatenation_candidates() -> None:  # JCL-DD-001
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//SYSUT1 DD DSN=A", "//  DD DSN=B",
                     "//         DD DSN=C", "//SYSUT2 DD SYSOUT=*"))
    dds = r.jobs[0].steps[0].dds
    assert [(d.ddname, d.concat_head, d.concat_index) for d in dds] == [
        ("SYSUT1", "SYSUT1", 0), (None, "SYSUT1", 1), (None, "SYSUT1", 2), ("SYSUT2", "SYSUT2", 0)]
    bad = parse_text(J("//J JOB", "//S EXEC PGM=X", "//         DD   DSN=A.B,DISP=SHR"))
    assert [(c, ln) for c, ln, _ in codes(bad)] == [("PAR-W004", 3)]


# ---------------------------------------------------------------- in-stream data (JCL-DD-003..006)
def data(r: ParseResult, line: int) -> Any:
    return stmt(r, line).inline


def test_dd_star_end_conditions() -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//IN DD *", " A", " B", "/*", "//X DD *", " C",
                     "//* COMMENT ENDS DATA", "//Y DD *", " D"))
    a, b, c = data(r, 3), data(r, 7), data(r, 10)
    assert (a.records, a.terminator, a.delimiter, a.terminator_line) == (
        (4, 5), "DELIMITER", "/*", 6)
    assert (b.records, b.terminator) == ((8, 8), "NEXT_STATEMENT")
    assert (c.records, c.terminator) == ((11, 11), "EOF")
    assert r.diagnostics == ()


def test_dd_data_keeps_slash_slash_records() -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//SYSUT1 DD DATA", "//INNER JOB",
                     "//X DD DSN=A,", "/*", "//OUT DD SYSOUT=*"))
    d = data(r, 3)
    assert (d.records, d.terminator, d.delimiter) == ((4, 5), "DELIMITER", "/*")
    assert [s.kind for s in r.statements] == ["JOB", "EXEC", "DD", "DELIMITER", "DD"]
    assert [x.code for x in r.diagnostics] == []
    assert [x.code for x in r.superseded_diagnostics] == ["LEX-E005"]  # lexer view of data record
    assert [rr.role for rr in r.records[3:6]] == ["DATA", "DATA", "DELIMITER"]
    assert [rr.lexer_kind for rr in r.records[3:5]] == ["STATEMENT_START", "STATEMENT_START"]
    assert r.lex.records[3].kind == "STATEMENT_START"  # lexer output is not overwritten


def test_dd_data_without_delimiter() -> None:  # JCL-DD-004, A3
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//SYSUT1   DD   DATA", " R1", " R2"))
    d = data(r, 3)
    assert (d.records, d.terminator) == ((4, 5), "EOF")
    assert codes(r) == [("LEX-W002", 3, None)]


def test_dd_data_with_dlm() -> None:  # JCL-DD-004/005
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//SYSUT1 DD DATA,DLM=@@", "//INNER JOB",
                     "/* NOT END", "@@", "//OUT DD SYSOUT=*"))
    d = data(r, 3)
    assert (d.records, d.terminator, d.delimiter, d.terminator_line) == (
        (4, 5), "DELIMITER", "@@", 6)
    assert stmt(r, 6).kind == "DELIMITER"


def test_dd_star_dlm_depends_on_jes() -> None:  # JCL-DD-005, A2, POL-003
    text = J("//J JOB", "//S EXEC PGM=X", "//SYSIN DD *,DLM=AA", " DATA 1",
             "//NOTJCL DD DUMMY", "AA")
    j2 = parse_text(text, jes="JES2")
    assert (data(j2, 3).records, data(j2, 3).terminator) == ((4, 4), "NEXT_STATEMENT")
    j3 = parse_text(text, jes="JES3")
    assert (data(j3, 3).records, data(j3, 3).terminator, data(j3, 3).terminator_line) == (
        (4, 5), "DELIMITER", 6)
    un = parse_text(text)
    d = data(un, 3)
    assert d.status == "UNDETERMINED"
    assert [(c.jes, c.records, c.terminator) for c in d.candidates] == [
        ("JES2", (4, 4), "NEXT_STATEMENT"), ("JES3", (4, 5), "DELIMITER")]
    assert [(x.code, x.line) for x in un.diagnostics] == [("PAR-W005", 3)]
    assert [rr.role for rr in un.records[3:6]] == ["UNDETERMINED"] * 3
    assert all(s.span[0] not in (5, 6) for s in un.statements if s.span)  # not interpreted


def test_dd_star_dlm_jes_independent_when_candidates_agree() -> None:
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//SYSIN DD *,DLM=AA", " DATA", "AA"))
    d = data(r, 3)
    assert (d.status, d.records, d.terminator) == ("DETERMINED", (4, 4), "DELIMITER")


def test_dlm_without_instream() -> None:  # JCL-DD-005
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//IN DD DSN=A.B,DISP=SHR,DLM=AA"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("PAR-E016", 3)]


def test_implicit_sysin() -> None:  # JCL-DD-006, A5
    r = parse_text(J("//J JOB", "//STEP1 EXEC PGM=MYPROG", " INPUT 1", " INPUT 2",
                     "//OUT DD SYSOUT=*"))
    dds = r.jobs[0].steps[0].dds
    assert [(d.ddname, d.implicit) for d in dds] == [("SYSIN", True), ("OUT", False)]
    imp = dds[0].statement
    assert imp.inline is not None
    assert imp.span is None and imp.implicit_basis == "JCL-DD-006"
    assert (imp.inline.records, imp.inline.terminator) == ((3, 4), "NEXT_STATEMENT")
    assert r.diagnostics == ()


def test_unrecognized_record_outside_step() -> None:  # JCL-REC-001, POL-006
    r = parse_text(J("//J JOB", " STRAY", "//S EXEC PGM=X"))
    assert [(c, ln) for c, ln, _ in codes(r)] == [("PAR-W006", 2)]
    assert r.records[1].role == "UNRECOGNIZED"


# ---------------------------------------------------------------- comments, null, procedures
def test_comments_preserved_with_positions() -> None:  # JCL-STMT-COMMENT, JCL-FMT-007
    r = parse_text(J("//J JOB", "//* NOTE", "//S EXEC PGM=X   RUN IT"))
    assert (stmt(r, 2).kind, stmt(r, 2).comment_texts) == ("COMMENT", ("NOTE",))
    # "//S EXEC PGM=X   RUN IT": PGM=X is columns 10-14, comment starts in column 18
    assert [(c.line, c.column, c.text) for c in stmt(r, 3).comments] == [(3, 18, "RUN IT")]


def test_null_statement_ends_job() -> None:  # JCL-STMT-NULL, POL-003
    r = parse_text(J("//J JOB", "//S EXEC PGM=X", "//", "//T EXEC PGM=Y", "//K JOB",
                     "//U EXEC PGM=Z"))
    assert [(j.name, [s.name for s in j.steps]) for j in r.jobs] == [
        ("J", ["S", "T"]), ("K", ["U"])]
    assert r.jobs[0].steps[1].after_null
    assert [(x.code, x.line) for x in r.diagnostics] == [("PAR-I001", 3)]


def test_instream_proc_not_expanded_and_not_job_steps() -> None:  # JCL-PROC-001, scope
    r = parse_text(J("//J JOB", "//CARDS PROC", "//PS1 EXEC PGM=X", "//DD1 DD DUMMY", "// PEND",
                     "//STEP1 EXEC CARDS"))
    (job,) = r.jobs
    assert [s.name for s in job.steps] == ["STEP1"]
    assert [(p.name, [s.name for s in p.steps]) for p in job.procedures] == [("CARDS", ["PS1"])]
    assert "PROC_NOT_EXPANDED" in r.limitations


def test_out_of_scope_constructs_kept_not_analyzed() -> None:
    r = parse_text(J("//J JOB", "// SET HLQ=A", "//I INCLUDE MEMBER=X", "//S EXEC PGM=X",
                     "//D DD DSN=&HLQ..B", "//C IF (RC > 4) THEN", "// ENDIF"))
    assert {"INCLUDE_NOT_EXPANDED", "SYMBOLS_NOT_RESOLVED", "IF_NOT_ANALYZED"} <= set(r.limitations)
    c = stmt(r, 6)
    assert c.condition is None and [t.text for t in c.condition_tokens][:2] == ["(", "RC"]


def test_proc_member_input() -> None:  # JCL-PROC-002
    r = parse_text(J("//DEF     PROC  STATUS=OLD", "//NOTIFY  EXEC  PGM=ACCUM", "//DD1 DD DUMMY"),
                   input_kind="proc_member")
    assert r.jobs == ()
    assert [s.name for s in r.procedure_steps] == ["NOTIFY"]


def test_deterministic() -> None:
    text = J("//J JOB", "//S EXEC PGM=X", "//IN DD *", " A", "/*", "//OUT DD SYSOUT=*")
    assert parse_text(text).to_dict() == parse_text(text).to_dict()

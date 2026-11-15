"""Authoring aid: writes the hand-designed Golden input JCL files with exact column placement.

This script is NOT an oracle and does not compute expected values. It exists so that records whose
meaning depends on exact columns (column 71/72, 73-80, continuation columns) are reproducible and
reviewable. Inputs are sealed in tests/golden/MANIFEST.json; changing them requires a reseal by a
person (`jclprof golden-seal --by NAME`).

usage: uv run python tools/golden_authoring/make_inputs.py
"""

from __future__ import annotations

from pathlib import Path

SUITE = Path(__file__).resolve().parents[2] / "tests" / "golden"


def col72(text: str, ch: str = "X") -> str:
    """Text padded to column 71 with `ch` in column 72."""
    assert len(text) <= 71, text
    return text.ljust(71) + ch


def seq(text: str, number: str, c72: str = " ") -> str:
    assert len(text) <= 71 and len(number) == 8
    return text.ljust(71) + c72 + number


def at71(prefix: str, text: str) -> str:
    """prefix + text where text ends exactly in column 71."""
    line = prefix + text
    assert len(line) == 71, (len(line), line)
    return line


def cont(col: int, text: str) -> str:
    """Continuation record whose text starts in column `col`."""
    return "//".ljust(col - 1) + text


FILES: dict[str, list[str]] = {
    # ------------------------------------------------------------------ JOB / EXEC / DD
    "inputs/job_exec_dd/jed001.jcl": [
        "//JED001   JOB (ACCT),'PROGRAMMER',CLASS=A",
        "//STEP1    EXEC PGM=IEFBR14",
        "//INDD     DD   DSN=PROD.INPUT.DATA,DISP=SHR",
        "//OUTDD    DD   SYSOUT=*",
    ],
    "inputs/job_exec_dd/jed002.jcl": [
        "//JED002   JOB ,'A.B.C.'",
        "//STEPA    EXEC PROC=PAYROLL,REGION=0M",
        "//STEPB    EXEC PAYROLL",
    ],
    "inputs/job_exec_dd/jed003.jcl": [
        "//JED003   JOB",
        "//STEPNAME9 EXEC PGM=IEFBR14",
        "//1STEP    EXEC PGM=IEFBR14",
        "//step3    EXEC PGM=IEFBR14",
    ],
    "inputs/job_exec_dd/jed004.jcl": [
        "//@#$JOB08 JOB",
        "//$STEP#08 EXEC PGM=IEFBR14",
        "//DD@ABCDE DD",
    ],
    "inputs/job_exec_dd/jed005.jcl": [
        "//JED005   JOB",
        "//STEP1    EXEC TIME=5",
    ],
    "inputs/job_exec_dd/jed006.jcl": [
        "//JED006   JOB",
        "//STEP1    EXCE PGM=IEFBR14",
    ],
    "inputs/job_exec_dd/jed007.jcl": [
        "//JED007   JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//IN       DD   DSN=A.B,*",
    ],
    # ------------------------------------------------------------------ continuation / columns
    "inputs/continuation/cont001.jcl": [
        "//CONT001  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1  DD   DSNAME=SWITCH.LEVEL18.GROUP12,UNIT=3390,",
        "//     VOLUME=339023,SPACE=(TRK,(80,15)),DISP=(,PASS)",
    ],
    "inputs/continuation/cont003.jcl": [
        "//CONT003  JOB",
        "//STP4  EXEC PROC=BILLING,COND.PAID=((20,LT),EVEN),",
        "//     COND.LATE=(60,GT,FIND),",
        col72("//     COND.BILL=((20,GE),(30,LT,CHGE))  THIS STATEMENT CALLS"),
        col72("//     THE BILLING PROCEDURE AND SPECIFIES RETURN CODE TESTS"),
        "//     FOR THREE PROCEDURE STEPS.",
    ],
    "inputs/continuation/cont004.jcl": [
        "//CONT004  JOB",
        at71("//S1       EXEC PGM=IEFBR14,PARM='", "THIS IS A LONG PARAMETER WITHIN APOST"),
        cont(16, "ROPHES, CONTINUED IN COLUMN 16 OF THE NEXT RECORD'"),
    ],
    "inputs/continuation/cont005.jcl": [
        "//CONT005  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,",
        "//DD2      DD   DSN=C.D",
    ],
    "inputs/continuation/cont006.jcl": [
        "//CONT006  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,",
        cont(17, "DISP=SHR"),
    ],
    "inputs/continuation/cont007.jcl": [
        "//CONT007  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,",
        cont(4, "DISP=SHR,"),
        cont(16, "UNIT=SYSDA"),
    ],
    "inputs/continuation/cont008.jcl": [
        seq("//CONT008  JOB", "00010000"),
        seq("//STEP1    EXEC PGM=IEFBR14", "00020000"),
        seq("//DD1      DD   DSN=A.B,", "00030000", c72="X"),
        seq("//         DISP=SHR", "00040000"),
    ],
    "inputs/continuation/cont009.jcl": [
        "//CONT009  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,",
        "//* COMMENT BETWEEN CONTINUATIONS",
        "//         DISP=SHR",
    ],
    "inputs/continuation/cont010.jcl": [
        "//CONT010  JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,",
        "//",
    ],
    "inputs/continuation/cont011.jcl": [
        "//CONT011  JOB",
        "//* COMMENT TEXT RUNS THROUGH COLUMN EIGHTY".ljust(72) + "ENDSHERE",
    ],
    # ------------------------------------------------------------------ quotes / parentheses
    "inputs/quotes/qp001.jcl": [
        "//QP001    JOB D58-D04,'O''NEIL'",
        "//STEP1    EXEC PGM=IEFBR14,ACCT='123+456',PARM='A,B C'",
    ],
    "inputs/quotes/qp002.jcl": [
        "//QP002    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//OUT      DD   DSN=A.B,DISP=(NEW,CATLG,DELETE),SPACE=(CYL,(1,1),RLSE),",
        "//         DCB=(RECFM=FB,LRECL=80)",
    ],
    "inputs/quotes/qp003.jcl": [
        "//QP003    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D1       DD   DSN=A.B,DISP=(,CATLG,DELETE)",
        "//D2       DD   DSN=C.D,DISP=(OLD,,DELETE)",
        "//D3       DD   DSN=E.F,DISP=(,,KEEP)",
    ],
    "inputs/quotes/qp004.jcl": [
        "//QP004    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D1       DD   DSN=PDS1(MEMA),DISP=SHR",
        "//D2       DD   DSN=GDS(+1),DISP=(NEW,CATLG)",
        "//D3       DD   DSN=&&TEMPDS,DISP=(NEW,PASS)",
        "//D4       DD   DSN=*.D1,DISP=SHR",
    ],
    "inputs/quotes/qp005.jcl": [
        "//QP005    JOB",
        "//STEP1    EXEC PGM=IEFBR14,PARM='ABC",
    ],
    "inputs/quotes/qp006.jcl": [
        "//QP006    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D1       DD   DSN=A.B,SPACE=(CYL,(1,1)",
    ],
    "inputs/quotes/qp007.jcl": [
        "//QP007    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D1       DD   DSN=A.B,SPACE=(CYL,(1,(1)))",
    ],
    # ------------------------------------------------------------------ concatenation
    "inputs/concat/cat001.jcl": [
        "//CAT001   JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//SYSUT1   DD   DSN=A.FIRST,DISP=SHR",
        "//         DD   DSN=A.SECOND,DISP=SHR",
        "//         DD   DSN=A.THIRD,DISP=SHR",
        "//SYSUT2   DD   SYSOUT=*",
    ],
    "inputs/concat/cat003.jcl": [
        "//CAT003   JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//         DD   DSN=A.B,DISP=SHR",
    ],
    "inputs/concat/cat004.jcl": [
        "//CAT004   JOB",
        "//CALLER   EXEC PROC=MYPROC",
        "//STEPSIX.DD4 DD  DSNAME=TEXT,DISP=(NEW,PASS)",
        "//            DD  DSNAME=ART,DISP=SHR",
    ],
    # ------------------------------------------------------------------ GDG / DISP
    "inputs/gdg_disp/gd001.jcl": [
        "//GD001    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//TRANSACT DD DISP=(NEW,CATLG,DELETE),",
        "//         UNIT=SYSDA,",
        "//         SPACE=(CYL,(1,1),RLSE),",
        "//         DSN=APP.SYSTRAN(+1)",
    ],
    "inputs/gdg_disp/gd003.jcl": [
        "//GD003    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D1       DD   DSN=A.NODISP,UNIT=SYSDA,SPACE=(TRK,1)",
        "//D2       DD   DSN=A.SHR,DISP=SHR",
        "//D3       DD   DSN=A.NEWCAT,DISP=(,CATLG)",
        "//D4       DD   DSN=A.NEWPASS,DISP=(NEW,PASS),UNIT=SYSDA,SPACE=(TRK,1)",
        "//D5       DD   DSN=A.OLDPASS,DISP=(OLD,PASS)",
        "//D6       DD   DSN=A.OLDDEL,DISP=(OLD,,DELETE)",
    ],
    "inputs/gdg_disp/gd004.jcl": [
        "//GD004    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//D7       DD   DSN=A.MOD,DISP=MOD",
    ],
    "inputs/gdg_disp/gd005.jcl": [
        "//GD005    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//G1       DD   DSN=A.GDG(+255),DISP=(NEW,CATLG)",
        "//G2       DD   DSN=A.GDG(-002),DISP=SHR",
        "//G3       DD   DSN=A.GDG(0),DISP=SHR",
        "//G4       DD   DSN=A.GDG(000),DISP=SHR",
        "//G5       DD   DSN=A.GDG,DISP=SHR",
    ],
    "inputs/gdg_disp/gd006.jcl": [
        "//GD006    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//G1       DD   DSN=A.GDG(+256),DISP=(NEW,CATLG)",
        "//G2       DD   DSN=A.GDG(+1000),DISP=(NEW,CATLG)",
        "//G3       DD   DSN=A.GDG(+A),DISP=(NEW,CATLG)",
    ],
    # ------------------------------------------------------------------ in-stream data
    "inputs/instream/is001.jcl": [
        "//IS001    JOB",
        "//STEP1    EXEC PGM=SORT",
        "//SYSIN    DD   *",
        " SORT FIELDS=(1,10,CH,A)",
        " END",
        "/*",
        "//SYSOUT   DD   SYSOUT=*",
    ],
    "inputs/instream/is002.jcl": [
        "//IS002    JOB",
        "//STEP1    EXEC PGM=SORT",
        "//SYSIN    DD   *",
        " SORT FIELDS=COPY",
        "//SYSOUT   DD   SYSOUT=*",
    ],
    "inputs/instream/is003.jcl": [
        "//IS003    JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//SYSUT1   DD   DATA",
        "//INNER    JOB  (THIS IS DATA)",
        "//STEPX    EXEC PGM=X",
        "/*",
        "//SYSUT2   DD   SYSOUT=(A,INTRDR)",
    ],
    "inputs/instream/is004.jcl": [
        "//IS004    JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//SYSUT1   DD   DATA,DLM=@@",
        "//INNER    JOB",
        "/* NOT A DELIMITER HERE",
        "@@",
        "//SYSUT2   DD   SYSOUT=*",
    ],
    "inputs/instream/is005.jcl": [
        "//IS005    JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//SYSIN    DD   *,DLM=AA",
        " DATA LINE 1",
        "//NOTJCL   DD   DUMMY",
        "AA",
    ],
    "inputs/instream/is006.jcl": [
        "//IS006    JOB",
        "//STEP1    EXEC PGM=IEBGENER",
        "//SYSUT1   DD   DATA",
        " RECORD 1",
        " RECORD 2",
    ],
    "inputs/instream/is007.jcl": [
        "//IS007    JOB",
        "//STEP1    EXEC PGM=SORT",
        "//SYSIN    DD   *",
        " RECORD 1",
    ],
    "inputs/instream/is008.jcl": [
        "//IS008    JOB",
        "//STEP1    EXEC PGM=MYPROG",
        " INPUT RECORD 1",
        " INPUT RECORD 2",
        "//OUT      DD   SYSOUT=*",
    ],
    "inputs/instream/is009.jcl": [
        "//IS009    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//IN       DD   DSN=A.B,DISP=SHR,DLM=AA",
    ],
    # ------------------------------------------------------------------ PROC / PEND
    "inputs/proc/pp001.jcl": [
        "//PP001    JOB",
        "//CARDS    PROC",
        "//PSTEP1   EXEC PGM=IEFBR14",
        "//DD1      DD   DSN=A.B,DISP=SHR",
        "//         PEND",
        "//STEP1    EXEC CARDS",
    ],
    "inputs/proc/DEF.prc": [
        "//DEF     PROC  STATUS=OLD,LIBRARY=SYSLIB,NUMBER=777777",
        "//NOTIFY  EXEC  PGM=ACCUM",
        "//DD1     DD    DSNAME=MGMT,DISP=(&STATUS,KEEP),UNIT=3390,",
        "//            VOLUME=SER=888888",
        "//DD2     DD    DSNAME=&LIBRARY,DISP=(OLD,KEEP),UNIT=3390,",
        "//            VOLUME=SER=&NUMBER",
    ],
    "inputs/proc/NOPROC.prc": [
        "//S1      EXEC  PGM=IEFBR14",
        "//DD1     DD    DSN=A.B,DISP=SHR",
    ],
    "inputs/proc/pp010.jcl": [
        "//PP010    JOB",
        "//INNER    PROC",
        "//IS1      EXEC PGM=IEFBR14",
        "//         PEND",
        "//OUTER    PROC",
        "//OS1      EXEC INNER",
        "//         PEND",
        "//STEP1    EXEC OUTER",
    ],
    "inputs/proc/pp004.jcl": [
        "//PP004    JOB",
        "//         PROC",
        "//PS1      EXEC PGM=IEFBR14",
        "//         PEND",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/proc/pp005.jcl": [
        "//PP005    JOB",
        "//OUTER    PROC",
        "//INNER    PROC",
        "//PS1      EXEC PGM=IEFBR14",
        "//         PEND",
        "//         PEND",
    ],
    "inputs/proc/pp006.jcl": [
        "//PP006    JOB",
        "//CARDS    PROC",
        "//PS1      EXEC PGM=IEFBR14",
    ],
    "inputs/proc/pp007.jcl": [
        "//PP007    JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//         PEND",
    ],
    "inputs/proc/pp008.jcl": [
        "//PP008    JOB",
        "//CARDS    PROC",
        "//LIB      JCLLIB ORDER=A.B",
        "//PS1      EXEC PGM=IEFBR14",
        "//         PEND",
    ],
    # ------------------------------------------------------------------ JCLLIB / INCLUDE / SET
    "inputs/jclinc/jis001.jcl": [
        "//JIS001   JOB",
        "//LIBS     JCLLIB ORDER=(MY.PROCLIB1,MY.PROCLIB2)",
        "//         SET  HLQ=PROD,DSP=(NEW,KEEP)",
        "//INC1     INCLUDE MEMBER=SYSOUT2",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis002.jcl": [
        "//JIS002   JOB",
        "//MYLIB    JCLLIB ORDER=('MY.PROC1','MY.PROC2')",
        "//SP3      SET  PARM4='O''DAY',PARM5=",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis003.jcl": [
        "//JIS003   JOB",
        "//STEP1    EXEC PGM=IEFBR14",
        "//LIBS     JCLLIB ORDER=MY.PROCLIB",
    ],
    "inputs/jclinc/jis004.jcl": [
        "//JIS004   JOB",
        "//L1       JCLLIB ORDER=A.PROCLIB",
        "//L2       JCLLIB ORDER=B.PROCLIB",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis006.jcl": [
        "//JIS006   JOB",
        "//LIBS     JCLLIB ORDER=(LIB01.PROC,LIB02.PROC,LIB03.PROC,LIB04.PROC,",
        "//         LIB05.PROC,LIB06.PROC,LIB07.PROC,LIB08.PROC,LIB09.PROC,",
        "//         LIB10.PROC,LIB11.PROC,LIB12.PROC,LIB13.PROC,LIB14.PROC,",
        "//         LIB15.PROC)",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis007.jcl": [
        "//JIS007   JOB",
        "//LIBS     JCLLIB ORDER=(LIB01.PROC,LIB02.PROC,LIB03.PROC,LIB04.PROC,",
        "//         LIB05.PROC,LIB06.PROC,LIB07.PROC,LIB08.PROC,LIB09.PROC,",
        "//         LIB10.PROC,LIB11.PROC,LIB12.PROC,LIB13.PROC,LIB14.PROC,",
        "//         LIB15.PROC,LIB16.PROC)",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis008.jcl": [
        "//JIS008   JOB",
        "//LIBS     JCLLIB ORDER=TEST.INCLIB",
        "//STEP1    EXEC PGM=OUTRTN",
        "//OUTPUT1  INCLUDE MEMBER=SYSOUT2",
        "//STEP2    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis009.jcl": [
        "//JIS009   JOB",
        "//LIBS     JCLLIB ORDER=TEST.INCLIB",
        "//STEP1    EXEC PGM=OUTRTN",
        "//OUTPUT1  INCLUDE MEMBER=NOSUCH",
        "//STEP2    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis010.jcl": [
        "//JIS010   JOB",
        "//LIBS     JCLLIB ORDER=UNMAPPED.PROCLIB",
        "//STEP1    EXEC PGM=IEFBR14",
    ],
    "inputs/jclinc/jis011.jcl": [
        "//JIS011   JOB",
        "//         SET  HLQ=AWS.M2.CARDDEMO",
        "//STEP1    EXEC PGM=IEFBR14",
        "//IN       DD   DSN=&HLQ..TRANTYPE.PS,DISP=SHR",
    ],
    "inputs/jclinc/jis012.jcl": [
        "//JIS012   JOB",
        "//TPROC    PROC",
        "//STEP1    EXEC PGM=IEFBR14,PARM='&INPUT&XXX'",
        "//         PEND",
        "//STEP2    EXEC TPROC,XXX=VALUE",
    ],
    "libs/inclib/SYSOUT2": [
        "//SYSOUT2  DD   SYSOUT=A",
        "//OUT1     OUTPUT DEST=POK,COPIES=3",
    ],
    # ------------------------------------------------------------------ IF / THEN / ELSE / ENDIF
    "inputs/if/if001.jcl": [
        "//IF001    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//CHK      IF (RC > 4) THEN",
        "//STEP2    EXEC PGM=ERRRTN",
        "//         ELSE",
        "//STEP3    EXEC PGM=NEXTRTN",
        "//         ENDIF",
    ],
    "inputs/if/if002.jcl": [
        "//IF002    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//IFBAD    IF  (ABEND | STEP1.RC > 8) THEN",
        "//ERR      EXEC PGM=ERRRTN",
        "//         ENDIF",
    ],
    "inputs/if/if003.jcl": [
        "//IF003    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//TESTNOTA IF  ¬(RC > 8) THEN",
        "//S2       EXEC PGM=A",
        "//         ENDIF",
        "//TESTNOTB IF  NOT (RC > 8) THEN",
        "//S3       EXEC PGM=B",
        "//         ENDIF",
    ],
    "inputs/if/if004.jcl": [
        "//IF004    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//PREC     IF  RC = 8 | RC = 10 & RC > 2 THEN",
        "//S2       EXEC PGM=A",
        "//         ENDIF",
    ],
    "inputs/if/if005.jcl": [
        "//IF005    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//TESTCON  IF (RC = 8 | RC = 10 | RC = 12 |",
        "//            RC = 14)  THEN         COMMENTS OK HERE",
        "//S2       EXEC PGM=A",
        "//         ENDIF",
    ],
    "inputs/if/if006.jcl": [
        "//IF006    JOB",
        "//STEP1    EXEC PGM=PROGA",
        "//OUTER    IF (RC = 0) THEN",
        "//INNER    IF (STEP1.RC > 4) THEN",
        "//         ELSE",
        "//S3       EXEC PGM=C",
        "//         ENDIF",
        "//         ENDIF",
    ],
    "inputs/if/if007.jcl": [
        "//IF007    JOB",
        "//STEP1    EXEC PGM=A",
        "//CHK      IF (RC > 4) THEN",
        "//STEP2    EXEC PGM=B",
    ],
    "inputs/if/if008.jcl": [
        "//IF008    JOB",
        "//STEP1    EXEC PGM=A",
        "//         ELSE",
        "//STEP2    EXEC PGM=B",
        "//         ENDIF",
    ],
    "inputs/if/if009.jcl": (
        ["//IF009    JOB"]
        + [f"//IF{n:02d}     IF (RC = 0) THEN" for n in range(1, 17)]
        + ["//STEP1    EXEC PGM=A"]
        + ["//         ENDIF"] * 16
    ),
    "inputs/if/if010.jcl": (
        ["//IF010    JOB"]
        + [f"//IF{n:02d}     IF (RC = 0) THEN" for n in range(1, 16)]
        + ["//STEP1    EXEC PGM=A"]
        + ["//         ENDIF"] * 15
    ),
    "inputs/if/if011.jcl": [
        "//IF011    JOB",
        "//STEP1    EXEC PGM=A",
        "//CHK      IF (CC > 4) THEN",
        "//STEP2    EXEC PGM=B",
        "//         ENDIF",
    ],
    # ------------------------------------------------------------------ COND
    "inputs/cond/cd001.jcl": [
        "//CD001    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=(4,LT)",
        "//STEP3    EXEC PGM=C,COND=((12,GE),(8,EQ,STEP1),(4,LT,STEP2))",
        "//STEP4    EXEC PGM=D,COND=EVEN",
        "//STEP5    EXEC PGM=E,COND=((4,LT),ONLY)",
    ],
    "inputs/cond/cd004.jcl": [
        "//CD004    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=((1,EQ),(2,EQ),(3,EQ),(4,EQ),(5,EQ),(6,EQ),",
        "//         (7,EQ),(8,EQ))",
    ],
    "inputs/cond/cd005.jcl": [
        "//CD005    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=((1,EQ),(2,EQ),(3,EQ),(4,EQ),(5,EQ),(6,EQ),",
        "//         (7,EQ),(8,EQ),(9,EQ))",
    ],
    "inputs/cond/cd006.jcl": [
        "//CD006    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=((1,EQ),(2,EQ),(3,EQ),(4,EQ),(5,EQ),(6,EQ),",
        "//         (7,EQ),(8,EQ),EVEN)",
    ],
    "inputs/cond/cd007.jcl": [
        "//CD007    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=(,LT)",
    ],
    "inputs/cond/cd008.jcl": [
        "//CD008    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=(4,XX)",
    ],
    "inputs/cond/cd009.jcl": [
        "//CD009    JOB",
        "//STEP1    EXEC PGM=A",
        "//STEP2    EXEC PGM=B,COND=(4096,LT)",
    ],
    # ------------------------------------------------------------------ invalid / unresolved
    "inputs/invalid/inv001.jcl": [
        "//INV001   JOB",
        "//LIBS     JCLLIB ORDER=TEST.PROCLIB",
        "//STEP1    EXEC PROC=NOSUCH",
    ],
    "inputs/invalid/inv002.jcl": [
        "//INV002   JOB",
        "//LIBS     JCLLIB ORDER=TEST.PROCLIB",
        "//STEP1    EXEC CYCA",
    ],
    "inputs/invalid/inv003.jcl": [
        "//INV003   JOB",
        "//STEP1    EXEC PGM=A",
        "//DD1      DD   DSN=X.Y,DISP=SHR",
        "//STEP2    EXEC PGM=B",
        "//DD2      DD   DSN=*.STEP1.NODD,DISP=SHR",
    ],
    "inputs/invalid/inv005.jcl": [
        "//INV005   JOB",
        "/*JOBPARM PROCLIB=PROC01",
        "//STEP1    EXEC PGM=A",
    ],
    "libs/proclib/CYCA": [
        "//CYCA     PROC",
        "//S1       EXEC CYCB",
    ],
    "libs/proclib/CYCB": [
        "//CYCB     PROC",
        "//S1       EXEC CYCA",
    ],
}


def main() -> None:
    for rel, lines in FILES.items():
        for n, ln in enumerate(lines, start=1):
            assert len(ln) <= 80, f"{rel}:{n} longer than 80"
        p = SUITE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(FILES)} files under {SUITE}")


if __name__ == "__main__":
    main()

# Golden Test Run

Statuses are reported separately and are not combined into a single rate.

| PASSED | FAILED | BLOCKED | NOT_IMPLEMENTED | NOT_RUN |
|---|---|---|---|---|
| 49 | 2 | 2 | 49 | 0 |

## By assurance

FORMAL = reviewed/approved expectations. REFERENCE = draft expectations (comparison only, not formal quality assurance).

| Assurance | PASSED | FAILED | BLOCKED | NOT_IMPLEMENTED | NOT_RUN |
|---|---|---|---|---|---|
| REFERENCE | 49 | 2 | 2 | 49 | 0 |

## By category

| Category | PASSED | FAILED | BLOCKED | NOT_IMPLEMENTED | NOT_RUN |
|---|---|---|---|---|---|
| COND | 0 | 0 | 0 | 8 | 0 |
| CONTINUATION_COLUMNS | 17 | 0 | 0 | 0 | 0 |
| DD_CONCATENATION | 4 | 0 | 0 | 1 | 0 |
| GDG_DISP | 2 | 0 | 0 | 5 | 0 |
| IF_THEN_ELSE | 1 | 0 | 0 | 11 | 0 |
| INSTREAM_DATA | 7 | 2 | 1 | 0 | 0 |
| INVALID_UNRESOLVED | 2 | 0 | 0 | 3 | 0 |
| JCLLIB_INCLUDE_SET | 0 | 0 | 0 | 12 | 0 |
| JOB_EXEC_DD | 7 | 0 | 0 | 0 | 0 |
| PROC_PEND | 0 | 0 | 1 | 9 | 0 |
| QUOTES_PARENTHESES | 9 | 0 | 0 | 0 | 0 |

## Cases

| Test ID | Stage | Review | Assurance | Status | Reason |
|---|---|---|---|---|---|
| G-CAT-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-CAT-002 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-CAT-003 | syntactic | draft | REFERENCE | PASSED |  |
| G-CAT-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-CAT-005 | syntactic | draft | REFERENCE | PASSED |  |
| G-CD-001 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-CD-002 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-CD-003 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-CD-004 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for COND are not implemented |
| G-CD-005 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for COND are not implemented |
| G-CD-006 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for COND are not implemented |
| G-CD-007 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for COND are not implemented |
| G-CD-008 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for COND are not implemented |
| G-CONT-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-002 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-003 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-005 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-006 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-007 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-008 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-009 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-010 | syntactic | draft | REFERENCE | PASSED |  |
| G-CONT-101 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-102 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-103 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-104 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-105 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-106 | lexical | draft | REFERENCE | PASSED |  |
| G-CONT-107 | lexical | draft | REFERENCE | PASSED |  |
| G-GD-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-GD-002 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-GD-003 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-GD-004 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-GD-005 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-GD-006 | semantic | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'semantic' |
| G-GD-007 | syntactic | draft | REFERENCE | PASSED |  |
| G-IF-001 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-002 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-003 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-004 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-005 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-006 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-007 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-008 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-009 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-010 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-011 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for IF_THEN_ELSE are not implemented |
| G-IF-101 | lexical | draft | REFERENCE | PASSED |  |
| G-INV-001 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-INV-002 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-INV-003 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-INV-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-INV-101 | lexical | draft | REFERENCE | PASSED |  |
| G-IS-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-002 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-003 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-005 | syntactic | blocked | REFERENCE | BLOCKED | The Environment Profile JES type is UNKNOWN (config environment.jes; POL-003, ADR-021). Under JES2, record 5 is a DD statement and record 6 is stray; under JES3, records 4-5 are data and record 6 is the delimiter. Unblock once the JES type is configured. |
| G-IS-006 | syntactic | draft | REFERENCE | FAILED |  |
| G-IS-007 | syntactic | draft | REFERENCE | FAILED |  |
| G-IS-008 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-009 | syntactic | draft | REFERENCE | PASSED |  |
| G-IS-101 | lexical | draft | REFERENCE | PASSED |  |
| G-JED-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-002 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-003 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-005 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-006 | syntactic | draft | REFERENCE | PASSED |  |
| G-JED-007 | syntactic | draft | REFERENCE | PASSED |  |
| G-JIS-001 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-002 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-003 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-004 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-005 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-006 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for JCLLIB_INCLUDE_SET are not implemented |
| G-JIS-007 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-JIS-008 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-JIS-009 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-JIS-010 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-JIS-011 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-JIS-012 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-PP-001 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-002 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-003 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-004 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-005 | syntactic | blocked | REFERENCE | BLOCKED | The first diagnostic (PAR-E013 at record 3) is clear, but the follow-on diagnostics depend on an error-recovery policy that has not been decided: which PEND closes which PROC (records 5 and 6). Decide the recovery policy before Step 4. |
| G-PP-006 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-007 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-008 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-PP-009 | resolution | draft | REFERENCE | NOT_IMPLEMENTED | no adapter for stage 'resolution' |
| G-PP-010 | syntactic | draft | REFERENCE | NOT_IMPLEMENTED | Step 4b scope: structure checks for PROC_PEND are not implemented |
| G-QP-001 | syntactic | draft | REFERENCE | PASSED |  |
| G-QP-002 | syntactic | draft | REFERENCE | PASSED |  |
| G-QP-003 | syntactic | draft | REFERENCE | PASSED |  |
| G-QP-004 | syntactic | draft | REFERENCE | PASSED |  |
| G-QP-005 | lexical | draft | REFERENCE | PASSED |  |
| G-QP-006 | lexical | draft | REFERENCE | PASSED |  |
| G-QP-007 | syntactic | draft | REFERENCE | PASSED |  |
| G-QP-101 | lexical | draft | REFERENCE | PASSED |  |
| G-QP-102 | lexical | draft | REFERENCE | PASSED |  |

# CardDemo Parse Report (Step 4b)

JES type: UNKNOWN. A file parsing without an exception is not counted as success; see the diagnostics, unrecognized/undetermined records and limitations.

## Totals

| Item | Value |
|---|---|
| files | 48 |
| records | 3046 |
| jobs | 46 |
| steps | 123 |
| dds | 500 |
| files_with_instream | 36 |
| data_regions | 91 |
| undetermined_regions | 0 |
| data_records | 635 |
| unknown_statements | 0 |
| syntax_errors | 0 |
| diagnostics_by_code | {} |
| unrecognized_records | 0 |
| limitations | {'COND_NOT_ANALYZED': 6, 'LIBRARY_SEARCH_NOT_RESOLVED': 3, 'PROC_NOT_EXPANDED': 5, 'SYMBOLS_NOT_RESOLVED': 4} |
| unexplained_cross_check_differences | 0 |
| jes | UNKNOWN |

## Per file

| File | Kind | Jobs | Steps | DDs | In-stream (records) | Unknown stmts | Errors | Diagnostics | Unrecognized recs | EXEC regex/parser | DD regex/parser | Limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl | job | 1 | 1 | 17 | 1 (1) | 0 | 0 | - | 0 | 1/1 | 17/17 | - |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | job | 1 | 2 | 19 | 1 (1) | 0 | 0 | - | 0 | 2/2 | 19/19 | - |
| app-authorization-ims-db2-mq/jcl/LOADPADB.JCL | job | 1 | 1 | 14 | - | 0 | 0 | - | 0 | 1/1 | 14/14 | - |
| app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL | job | 1 | 1 | 16 | - | 0 | 0 | - | 0 | 1/1 | 16/16 | - |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | job | 1 | 2 | 21 | - | 0 | 0 | - | 0 | 2/2 | 21/21 | - |
| app-transaction-type-db2/jcl/CREADB21.jcl | job | 1 | 5 | 30 | - | 0 | 0 | - | 0 | 5/5 | 30/30 | COND_NOT_ANALYZED, SYMBOLS_NOT_RESOLVED |
| app-transaction-type-db2/jcl/MNTTRDB2.jcl | job | 1 | 1 | 7 | 1 (2) | 0 | 0 | - | 0 | 1/1 | 7/7 | - |
| app-transaction-type-db2/jcl/TRANEXTR.jcl | job | 1 | 5 | 28 | 4 (27) | 0 | 0 | - | 0 | 5/5 | 28/28 | COND_NOT_ANALYZED, SYMBOLS_NOT_RESOLVED |
| jcl/ACCTFILE.jcl | job | 1 | 3 | 8 | 3 (18) | 0 | 0 | - | 0 | 3/3 | 8/8 | - |
| jcl/CARDFILE.jcl | job | 1 | 8 | 20 | 8 (41) | 0 | 0 | - | 0 | 8/8 | 20/20 | - |
| jcl/CBADMCDJ.jcl | job | 1 | 1 | 5 | 1 (129) | 0 | 0 | - | 0 | 1/1 | 5/5 | SYMBOLS_NOT_RESOLVED |
| jcl/CBEXPORT.jcl | job | 1 | 2 | 11 | 1 (12) | 0 | 0 | - | 0 | 2/2 | 11/11 | - |
| jcl/CBIMPORT.jcl | job | 1 | 1 | 9 | - | 0 | 0 | - | 0 | 1/1 | 9/9 | - |
| jcl/CLOSEFIL.jcl | job | 1 | 1 | 3 | 1 (5) | 0 | 0 | - | 0 | 1/1 | 3/3 | - |
| jcl/COMBTRAN.jcl | job | 1 | 2 | 10 | 3 (3) | 0 | 0 | - | 0 | 2/2 | 10/10 | - |
| jcl/CREASTMT.JCL | job | 1 | 5 | 22 | 3 (18) | 0 | 0 | - | 0 | 5/5 | 22/22 | COND_NOT_ANALYZED |
| jcl/CUSTFILE.jcl | job | 1 | 5 | 14 | 5 (20) | 0 | 0 | - | 0 | 5/5 | 14/14 | - |
| jcl/DALYREJS.jcl | job | 1 | 1 | 2 | 1 (5) | 0 | 0 | - | 0 | 1/1 | 2/2 | - |
| jcl/DEFCUST.jcl | job | 1 | 2 | 4 | 2 (14) | 0 | 0 | - | 0 | 2/2 | 4/4 | - |
| jcl/DEFGDGB.jcl | job | 1 | 1 | 2 | 1 (36) | 0 | 0 | - | 0 | 1/1 | 2/2 | - |
| jcl/DEFGDGD.jcl | job | 1 | 6 | 18 | 3 (15) | 0 | 0 | - | 0 | 6/6 | 18/18 | COND_NOT_ANALYZED |
| jcl/DISCGRP.jcl | job | 1 | 3 | 8 | 3 (18) | 0 | 0 | - | 0 | 3/3 | 8/8 | - |
| jcl/DUSRSECJ.jcl | job | 1 | 4 | 12 | 3 (23) | 0 | 0 | - | 0 | 4/4 | 12/12 | - |
| jcl/ESDSRRDS.jcl | job | 1 | 6 | 19 | 5 (32) | 0 | 0 | - | 0 | 6/6 | 19/19 | - |
| jcl/FTPJCL.JCL | job | 1 | 1 | 1 | 1 (9) | 0 | 0 | - | 0 | 1/1 | 1/1 | - |
| jcl/INTCALC.jcl | job | 1 | 1 | 9 | - | 0 | 0 | - | 0 | 1/1 | 9/9 | - |
| jcl/INTRDRJ1.JCL | job | 1 | 2 | 8 | 1 (1) | 0 | 0 | - | 0 | 2/2 | 8/8 | - |
| jcl/INTRDRJ2.JCL | job | 1 | 1 | 4 | 1 (1) | 0 | 0 | - | 0 | 1/1 | 4/4 | - |
| jcl/OPENFIL.jcl | job | 1 | 1 | 3 | 1 (5) | 0 | 0 | - | 0 | 1/1 | 3/3 | - |
| jcl/POSTTRAN.jcl | job | 1 | 1 | 9 | - | 0 | 0 | - | 0 | 1/1 | 9/9 | - |
| jcl/PRTCATBL.jcl | job | 1 | 3 | 8 | 2 (9) | 0 | 0 | - | 0 | 3/3 | 8/8 | LIBRARY_SEARCH_NOT_RESOLVED, PROC_NOT_EXPANDED |
| jcl/READACCT.jcl | job | 1 | 2 | 10 | - | 0 | 0 | - | 0 | 2/2 | 10/10 | - |
| jcl/READCARD.jcl | job | 1 | 1 | 4 | - | 0 | 0 | - | 0 | 1/1 | 4/4 | - |
| jcl/READCUST.jcl | job | 1 | 1 | 4 | - | 0 | 0 | - | 0 | 1/1 | 4/4 | - |
| jcl/READXREF.jcl | job | 1 | 1 | 4 | - | 0 | 0 | - | 0 | 1/1 | 4/4 | - |
| jcl/REPTFILE.jcl | job | 1 | 1 | 2 | 1 (4) | 0 | 0 | - | 0 | 1/1 | 2/2 | - |
| jcl/TCATBALF.jcl | job | 1 | 3 | 8 | 3 (18) | 0 | 0 | - | 0 | 3/3 | 8/8 | - |
| jcl/TRANBKP.jcl | job | 1 | 3 | 6 | 2 (20) | 0 | 0 | - | 0 | 3/3 | 6/6 | COND_NOT_ANALYZED, LIBRARY_SEARCH_NOT_RESOLVED, PROC_NOT_EXPANDED |
| jcl/TRANCATG.jcl | job | 1 | 3 | 8 | 3 (18) | 0 | 0 | - | 0 | 3/3 | 8/8 | - |
| jcl/TRANFILE.jcl | job | 1 | 8 | 20 | 8 (41) | 0 | 0 | - | 0 | 8/8 | 20/20 | - |
| jcl/TRANIDX.jcl | job | 1 | 3 | 6 | 3 (16) | 0 | 0 | - | 0 | 3/3 | 6/6 | - |
| jcl/TRANREPT.jcl | job | 1 | 3 | 16 | 2 (7) | 0 | 0 | - | 0 | 3/3 | 16/16 | LIBRARY_SEARCH_NOT_RESOLVED, PROC_NOT_EXPANDED |
| jcl/TRANTYPE.jcl | job | 1 | 3 | 8 | 3 (18) | 0 | 0 | - | 0 | 3/3 | 8/8 | - |
| jcl/TXT2PDF1.JCL | job | 1 | 1 | 6 | 1 (2) | 0 | 0 | - | 0 | 1/1 | 6/6 | COND_NOT_ANALYZED |
| jcl/WAITSTEP.jcl | job | 1 | 1 | 3 | 1 (1) | 0 | 0 | - | 0 | 1/1 | 3/3 | - |
| jcl/XREFFILE.jcl | job | 1 | 6 | 14 | 6 (38) | 0 | 0 | - | 0 | 6/6 | 14/14 | - |
| proc/REPROC.prc | proc_member | 0 | 1 | 4 | - | 0 | 0 | - | 0 | 1/1 | 4/4 | PROC_NOT_EXPANDED, SYMBOLS_NOT_RESOLVED |
| proc/TRANREPT.prc | proc_member | 0 | 3 | 16 | 2 (7) | 0 | 0 | - | 0 | 3/3 | 16/16 | PROC_NOT_EXPANDED |

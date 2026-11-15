# CD-1 原本照合レビュー索引

全48件PENDING。生成・検査の実行は承認ではない。
この索引も同じ期待値から描画したものであり、第二の独立オラクルではない。
各原本を確認し、階層・全パラメーター・連結・データ範囲・行列をレビューする。
詳細な全トークン/値のセグメントはexpectations.jsonを参照する。

## app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl

SHA-256: `c90fbd21b8ea2b6448b8939ff4f3b47c6f73472465cd7d1e25871f7779063a86`。レビュー: PENDING。

JOB CBPAUP0J@1、期待span [1, 47]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01@24 | ['PGM', 'DFSRRC00'] | STEPLIB@26, unnamed->STEPLIB[1]@27, DFSRESLB@28, PROCLIB@29, DFSSEL@31, IMS@33, unnamed->IMS[1]@34, SYSIN@36, SYSOUX@39, SYSOUT@40, SYSABOUT@41, ABENDAID@42, IEFRDER@43, IMSLOGR@44, SYSPRINT@45, SYSUDUMP@46, IMSERR@47 |

tree参照必須の操作文先頭行: [1, 24, 26, 27, 28, 29, 31, 33, 34, 36, 39, 40, 41, 42, 43, 44, 45, 46, 47]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 36 | [37, 37] | NEXT_STATEMENT / 38 |

## app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl

SHA-256: `3fabb7f3230f98fee855a8d436f70f4bd601a9e544f29c83d413a3a7a61efbcd`。レビュー: PENDING。

JOB DBPAUTP0@1、期待span [1, 47]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEPDEL@7 | ['PGM', 'IEFBR14'] | SYSPRINT@8, SYSUT1@9 |
| UNLOAD@15 | ['PGM', 'DFSRRC00'] | STEPLIB@18, unnamed->STEPLIB[1]@19, DFSRESLB@20, IMS@21, unnamed->IMS[1]@22, SYSPRINT@23, DFSURGU1@25, DDPAUTP0@31, DDPAUTX0@32, DFSVSAMP@33, DFSCTL@34, SYSUDUMP@36, RECON1@40, RECON2@41, RECON3@42, DFSWRK01@44, DFSSRT01@45 |

tree参照必須の操作文先頭行: [1, 7, 8, 9, 15, 18, 19, 20, 21, 22, 23, 25, 31, 32, 33, 34, 36, 40, 41, 42, 44, 45]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 34 | [35, 35] | NEXT_STATEMENT / 36 |

## app-authorization-ims-db2-mq/jcl/LOADPADB.JCL

SHA-256: `9a0a88472f69236d14b36ecc89d83f35179d5c720c2c3a465af5f7ff510fb067`。レビュー: PENDING。

JOB LOADPADB@1、期待span [1, 51]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01@26 | ['PGM', 'DFSRRC00'] | STEPLIB@28, unnamed->STEPLIB[1]@29, unnamed->STEPLIB[2]@30, DFSRESLB@31, IMS@33, unnamed->IMS[1]@34, INFILE1@36, INFILE2@38, DFSVSAMP@44, IMSLOGR@46, IEFRDER@47, SYSPRINT@48, SYSUDUMP@49, IMSERR@50 |

tree参照必須の操作文先頭行: [1, 26, 28, 29, 30, 31, 33, 34, 36, 38, 44, 46, 47, 48, 49, 50]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL

SHA-256: `1da94de3db6f265578c8b7498a2371c0c7246c8409f4ac44eb8013d3f0e113b8`。レビュー: PENDING。

JOB UNLDGSAM@1、期待span [1, 53]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01@26 | ['PGM', 'DFSRRC00'] | STEPLIB@28, unnamed->STEPLIB[1]@29, unnamed->STEPLIB[2]@30, DFSRESLB@31, IMS@33, unnamed->IMS[1]@34, PASFILOP@36, PADFILOP@39, DDPAUTP0@42, DDPAUTX0@43, DFSVSAMP@46, IMSLOGR@48, IEFRDER@49, SYSPRINT@50, SYSUDUMP@51, IMSERR@52 |

tree参照必須の操作文先頭行: [1, 26, 28, 29, 30, 31, 33, 34, 36, 39, 42, 43, 46, 48, 49, 50, 51, 52]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL

SHA-256: `e2c26ca546ab427d66cadeaff07345bad706c979ca396fb04e60d401dc93c66b`。レビュー: PENDING。

JOB UNLDPADB@1、期待span [1, 69]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP0@25 | ['PGM', 'IEFBR14'] | SYSPRINT@27, SYSOUT@29, SYSDUMP@31, DD1@33, DD2@35 |
| STEP01@38 | ['PGM', 'DFSRRC00'] | STEPLIB@40, unnamed->STEPLIB[1]@41, unnamed->STEPLIB[2]@42, DFSRESLB@43, IMS@45, unnamed->IMS[1]@46, OUTFIL1@48, OUTFIL2@53, DDPAUTP0@58, DDPAUTX0@59, DFSVSAMP@62, IMSLOGR@64, IEFRDER@65, SYSPRINT@66, SYSUDUMP@67, IMSERR@68 |

tree参照必須の操作文先頭行: [1, 25, 27, 29, 31, 33, 35, 38, 40, 41, 42, 43, 45, 46, 48, 53, 58, 59, 62, 64, 65, 66, 67, 68]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## app-transaction-type-db2/jcl/CREADB21.jcl

SHA-256: `88b81b1d8530037d1661321e47600b9afb2a2cf4894c7eefeacd5aff07b87d69`。レビュー: PENDING。

JOB CREADB2@1、期待span [1, 84]。

JOB DD: JOBLIB@32, unnamed->JOBLIB[1]@33, unnamed->JOBLIB[2]@34

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| FREEPLN@40 | ['PGM', 'IKJEFT01'] | STEPLIB@41, unnamed->STEPLIB[1]@42, SYSPRINT@43, SYSTSPRT@44, SYSUDUMP@45, SYSTSIN@46 |
| CRCRDDB@52 | ['PGM', 'IKJEFT01'] | STEPLIB@53, unnamed->STEPLIB[1]@54, SYSTSPRT@55, SYSUDUMP@56, SYSPRINT@57, SYSTSIN@58, SYSIN@59 |
| LDTTYPE@64 | ['PGM', 'IEFBR14'] |  |
| RUNTEP2@65 | ['PGM', 'IKJEFT01'] | STEPLIB@66, unnamed->STEPLIB[1]@67, SYSTSPRT@68, SYSUDUMP@69, SYSPRINT@70, SYSTSIN@71, SYSIN@72 |
| LDTCCAT@77 | ['PGM', 'IKJEFT01'] | STEPLIB@78, unnamed->STEPLIB[1]@79, SYSTSPRT@80, SYSUDUMP@81, SYSPRINT@82, SYSTSIN@83, SYSIN@84 |

tree参照必須の操作文先頭行: [1, 28, 29, 30, 32, 33, 34, 40, 41, 42, 43, 44, 45, 46, 52, 53, 54, 55, 56, 57, 58, 59, 64, 65, 66, 67, 68, 69, 70, 71, 72, 77, 78, 79, 80, 81, 82, 83, 84]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## app-transaction-type-db2/jcl/MNTTRDB2.jcl

SHA-256: `beaba6e4e35092c2ac7c1be7a3708303cc75d0fca00b64c65ee2d2bc1682f893`。レビュー: PENDING。

JOB MNTTRDB2@1、期待span [1, 30]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP1@21 | ['PGM', 'IKJEFT01'] | STEPLIB@22, unnamed->STEPLIB[1]@23, unnamed->STEPLIB[2]@24, DBRMLIB@25, SYSTSPRT@26, INPFILE@27, SYSTSIN@28 |

tree参照必須の操作文先頭行: [1, 21, 22, 23, 24, 25, 26, 27, 28]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 28 | [29, 30] | EOF / None |

## app-transaction-type-db2/jcl/TRANEXTR.jcl

SHA-256: `d4d3b99a71b91fbce9c145283642ee7ca31b5ad7fa51ddcdb3e2c0b2e530457f`。レビュー: PENDING。

JOB TRANEXTR@1、期待span [1, 122]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP10@31 | ['PGM', 'IEBGENER'] | SYSPRINT@32, SYSIN@33, SYSUT1@34, SYSUT2@35 |
| STEP20@42 | ['PGM', 'IEBGENER'] | SYSPRINT@43, SYSIN@44, SYSUT1@45, SYSUT2@46 |
| STEP30@53 | ['PGM', 'IEFBR14'] | DD01@54, DD02@58 |
| STEP40@65 | ['PGM', 'IKJEFT01'] | STEPLIB@66, unnamed->STEPLIB[1]@67, SYSTSPRT@68, SYSPRINT@69, SYSUDUMP@70, SYSPUNCH@71, SYSREC00@72, SYSIN@75, SYSTSIN@86 |
| STEP50@95 | ['PGM', 'IKJEFT01'] | STEPLIB@96, unnamed->STEPLIB[1]@97, SYSTSPRT@98, SYSPRINT@99, SYSUDUMP@100, SYSPUNCH@101, SYSREC00@102, SYSIN@105, SYSTSIN@117 |

tree参照必須の操作文先頭行: [1, 25, 31, 32, 33, 34, 35, 42, 43, 44, 45, 46, 53, 54, 58, 65, 66, 67, 68, 69, 70, 71, 72, 75, 86, 95, 96, 97, 98, 99, 100, 101, 102, 105, 117]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 75 | [76, 84] | DELIMITER / 85 |
| 86 | [87, 90] | DELIMITER / 91 |
| 105 | [106, 115] | DELIMITER / 116 |
| 117 | [118, 121] | DELIMITER / 122 |

## jcl/ACCTFILE.jcl

SHA-256: `92ce6733ad0e3fad640e19d1224003fe30c711c2564eb7a660d53fd7f0dd6622`。レビュー: PENDING。

JOB ACCTFILE@1、期待span [1, 65]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP15@54 | ['PGM', 'IDCAMS'] | SYSPRINT@55, ACCTDATA@56, ACCTVSAM@58, SYSIN@60 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 33, 34, 35, 54, 55, 56, 58, 60]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 27] | DELIMITER / 28 |
| 35 | [36, 49] | DELIMITER / 50 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/CARDFILE.jcl

SHA-256: `795600a41abec0706aec8bd0dd93446b29cf01fcd8f9d2173e4ec6d5476611d0`。レビュー: PENDING。

JOB CARDFILE@1、期待span [1, 128]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| CLCIFIL@22 | ['PGM', 'SDSF'] | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| STEP05@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP10@47 | ['PGM', 'IDCAMS'] | SYSPRINT@48, SYSIN@49 |
| STEP15@68 | ['PGM', 'IDCAMS'] | SYSPRINT@69, CARDDATA@70, CARDVSAM@72, SYSIN@74 |
| STEP40@80 | ['PGM', 'IDCAMS'] | SYSPRINT@81, SYSIN@82 |
| STEP50@97 | ['PGM', 'IDCAMS'] | SYSPRINT@98, SYSIN@99 |
| STEP60@107 | ['PGM', 'IDCAMS'] | SYSPRINT@108, SYSIN@109 |
| OPCIFIL@118 | ['PGM', 'SDSF'] | ISFOUT@119, CMDOUT@120, ISFIN@121 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25, 33, 34, 35, 47, 48, 49, 68, 69, 70, 72, 74, 80, 81, 82, 97, 98, 99, 107, 108, 109, 118, 119, 120, 121]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 27] | DELIMITER / 28 |
| 35 | [36, 41] | DELIMITER / 42 |
| 49 | [50, 63] | DELIMITER / 64 |
| 74 | [75, 75] | DELIMITER / 76 |
| 82 | [83, 92] | DELIMITER / 93 |
| 99 | [100, 102] | DELIMITER / 103 |
| 109 | [110, 112] | DELIMITER / 113 |
| 121 | [122, 123] | DELIMITER / 124 |

## jcl/CBADMCDJ.jcl

SHA-256: `49b99c74e97d7177e558748f58b73cc418daacd93b415d908b09651393841916`。レビュー: PENDING。

JOB CBADMCDJ@1、期待span [1, 167]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP1@27 | ['PGM', 'DFHCSDUP'] | STEPLIB@29, DFHCSD@30, OUTDD@31, SYSPRINT@32, SYSIN@33 |

tree参照必須の操作文先頭行: [1, 25, 27, 29, 30, 31, 32, 33]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 33 | [34, 162] | DELIMITER / 163 |

## jcl/CBEXPORT.jcl

SHA-256: `e5d010a3209dbbcf6d9b92a3c71b7c806019ce014ad921430eed9abf1706f804`。レビュー: PENDING。

JOB CBEXPORT@1、期待span [1, 72]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01@24 | ['PGM', 'IDCAMS'] | SYSPRINT@25, SYSIN@26 |
| STEP02@43 | ['PGM', 'CBEXPORT'] | STEPLIB@44, CUSTFILE@49, ACCTFILE@51, XREFFILE@53, TRANSACT@55, CARDFILE@57, EXPFILE@62, SYSOUT@67, SYSPRINT@68 |

tree参照必須の操作文先頭行: [1, 24, 25, 26, 43, 44, 49, 51, 53, 55, 57, 62, 67, 68]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 26 | [27, 38] | DELIMITER / 39 |

## jcl/CBIMPORT.jcl

SHA-256: `9f3adc0cde9d471b0976a4e4c5bee625a65fd0cdcc1e031d9abde8f5c3e8ccf5`。レビュー: PENDING。

JOB CBIMPORT@1、期待span [1, 68]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01@22 | ['PGM', 'CBIMPORT'] | STEPLIB@23, EXPFILE@28, CUSTOUT@33, ACCTOUT@38, XREFOUT@43, TRNXOUT@48, ERROUT@56, SYSOUT@64, SYSPRINT@65 |

tree参照必須の操作文先頭行: [1, 22, 23, 28, 33, 38, 43, 48, 56, 64, 65]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/CLOSEFIL.jcl

SHA-256: `e47d406dde49f06847a46559fa9a7182b80b85f0727a5f0be312286f34df9192`。レビュー: PENDING。

JOB CLOSEFIL@1、期待span [1, 34]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| CLCIFIL@22 | ['PGM', 'SDSF'] | ISFOUT@23, CMDOUT@24, ISFIN@25 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 30] | DELIMITER / 31 |

## jcl/COMBTRAN.jcl

SHA-256: `a91649d6a927e1fd7b81fcdab39088ae26554eea52b07d5715e488c81c3f2cc2`。レビュー: PENDING。

JOB COMBTRAN@1、期待span [1, 52]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05R@22 | ['PGM', 'SORT'] | SORTIN@23, unnamed->SORTIN[1]@25, SYMNAMES@27, SYSIN@29, SYSOUT@32, SORTOUT@33 |
| STEP10@41 | ['PGM', 'IDCAMS'] | SYSPRINT@42, TRANSACT@43, TRANVSAM@45, SYSIN@47 |

tree参照必須の操作文先頭行: [1, 22, 23, 25, 27, 29, 32, 33, 41, 42, 43, 45, 47]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 27 | [28, 28] | NEXT_STATEMENT / 29 |
| 29 | [30, 30] | DELIMITER / 31 |
| 47 | [48, 48] | DELIMITER / 49 |

## jcl/CREASTMT.JCL

SHA-256: `87a18700fac7bccfffbefa5d80fed0b171fdc36caeebb575c8a3cf66e4fc3caa`。レビュー: PENDING。

JOB CREASTMT@1、期待span [1, 97]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| DELDEF01@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP010@44 | ['PGM', 'SORT'] | SORTIN@45, SYSPRINT@46, SYSOUT@47, SORTOUT@48, SYSIN@52 |
| STEP020@56 | ['PGM', 'IDCAMS'] | SYSPRINT@57, INFILE@58, OUTFILE@59, SYSIN@60 |
| STEP030@66 | ['PGM', 'IEFBR14'] | HTMLFILE@67, STMTFILE@72 |
| STEP040@79 | ['PGM', 'CBSTM03A'] | STEPLIB@80, SYSPRINT@81, SYSOUT@82, TRNXFILE@83, XREFFILE@84, ACCTFILE@85, CUSTFILE@86, STMTFILE@87, HTMLFILE@92 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 44, 45, 46, 47, 48, 52, 56, 57, 58, 59, 60, 66, 67, 72, 79, 80, 81, 82, 83, 84, 85, 86, 87, 92]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 39] | DELIMITER / 40 |
| 52 | [53, 54] | DELIMITER / 55 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/CUSTFILE.jcl

SHA-256: `5fa6da4bc85866f0e08783585e7c652d312179982dbdd821866f569a083ac976`。レビュー: PENDING。

JOB CUSTFILE@1、期待span [1, 84]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| CLCIFIL@22 | ['PGM', 'SDSF'] | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| STEP05@32 | ['PGM', 'IDCAMS'] | SYSPRINT@33, SYSIN@34 |
| STEP10@43 | ['PGM', 'IDCAMS'] | SYSPRINT@44, SYSIN@45 |
| STEP15@64 | ['PGM', 'IDCAMS'] | SYSPRINT@65, CUSTDATA@66, CUSTVSAM@68, SYSIN@70 |
| OPCIFIL@76 | ['PGM', 'SDSF'] | ISFOUT@77, CMDOUT@78, ISFIN@79 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25, 32, 33, 34, 43, 44, 45, 64, 65, 66, 68, 70, 76, 77, 78, 79]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 26] | DELIMITER / 27 |
| 34 | [35, 37] | DELIMITER / 38 |
| 45 | [46, 59] | DELIMITER / 60 |
| 70 | [71, 71] | DELIMITER / 72 |
| 79 | [80, 80] | DELIMITER / 81 |

## jcl/DALYREJS.jcl

SHA-256: `ce396a6469c84577ea508d184f7ea6a42ceacd54c6a5e0fb097e626bb6361d45`。レビュー: PENDING。

JOB DALYREJS@1、期待span [1, 32]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@21 | ['PGM', 'IDCAMS'] | SYSPRINT@22, SYSIN@23 |

tree参照必須の操作文先頭行: [1, 21, 22, 23]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 23 | [24, 28] | DELIMITER / 29 |

## jcl/DEFCUST.jcl

SHA-256: `03dd2fc683ced79ec53269f6a24d48ceadb87ae4d6a5b48b65a37763046dfd58`。レビュー: PENDING。

JOB DEFCUST@1、期待span [1, 47]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP05@32 | ['PGM', 'IDCAMS'] | SYSPRINT@33, SYSIN@34 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 32, 33, 34]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 26] | DELIMITER / 27 |
| 34 | [35, 46] | DELIMITER / 47 |

## jcl/DEFGDGB.jcl

SHA-256: `4ccd135a079641b2d484b7789ea0f47955725774442283274f204480c0903f3f`。レビュー: PENDING。

JOB DEFGDGB@1、期待span [1, 63]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@21 | ['PGM', 'IDCAMS'] | SYSPRINT@22, SYSIN@23 |

tree参照必須の操作文先頭行: [1, 21, 22, 23]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 23 | [24, 59] | DELIMITER / 60 |

## jcl/DEFGDGD.jcl

SHA-256: `78c13d7e0e851aecd1acbfcedd26b60633a3a850dcd9fe38de339362be5e4830`。レビュー: PENDING。

JOB DEFGDGD@1、期待span [1, 94]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP10@24 | ['PGM', 'IDCAMS'] | SYSPRINT@25, SYSIN@26 |
| STEP20@36 | ['PGM', 'IEBGENER'] | SYSPRINT@37, SYSIN@38, SYSUT1@39, SYSUT2@40 |
| STEP30@47 | ['PGM', 'IDCAMS'] | SYSPRINT@48, SYSIN@49 |
| STEP40@59 | ['PGM', 'IEBGENER'] | SYSPRINT@60, SYSIN@61, SYSUT1@62, SYSUT2@63 |
| STEP50@70 | ['PGM', 'IDCAMS'] | SYSPRINT@71, SYSIN@72 |
| STEP60@82 | ['PGM', 'IEBGENER'] | SYSPRINT@83, SYSIN@84, SYSUT1@85, SYSUT2@86 |

tree参照必須の操作文先頭行: [1, 24, 25, 26, 36, 37, 38, 39, 40, 47, 48, 49, 59, 60, 61, 62, 63, 70, 71, 72, 82, 83, 84, 85, 86]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 26 | [27, 31] | DELIMITER / 32 |
| 49 | [50, 54] | DELIMITER / 55 |
| 72 | [73, 77] | DELIMITER / 78 |

## jcl/DISCGRP.jcl

SHA-256: `64a250c918cc8205eddd6d51615e24a8c23585ff012ea518c6d452ebd7d71492`。レビュー: PENDING。

JOB DISCGRP@1、期待span [1, 65]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP15@54 | ['PGM', 'IDCAMS'] | SYSPRINT@55, DISCGRP@56, DISCVSAM@58, SYSIN@60 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 33, 34, 35, 54, 55, 56, 58, 60]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 27] | DELIMITER / 28 |
| 35 | [36, 49] | DELIMITER / 50 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/DUSRSECJ.jcl

SHA-256: `71a529aab49502e9ce57abcdb268a896e34b947409d3278c5dd813f93105e33f`。レビュー: PENDING。

JOB DUSRSECJ@1、期待span [1, 92]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| PREDEL@23 | ['PGM', 'IEFBR14'] | DD01@25 |
| STEP01@32 | ['PGM', 'IEBGENER'] | SYSUT1@34, SYSUT2@46, SYSPRINT@51, SYSIN@52 |
| STEP02@58 | ['PGM', 'IDCAMS'] | SYSPRINT@60, SYSIN@61 |
| STEP03@80 | ['PGM', 'IDCAMS'] | IN@82, OUT@83, SYSOUT@84, SYSPRINT@85, SYSIN@86 |

tree参照必須の操作文先頭行: [1, 23, 25, 32, 34, 46, 51, 52, 58, 60, 61, 80, 82, 83, 84, 85, 86]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 34 | [35, 44] | DELIMITER / 45 |
| 61 | [62, 73] | DELIMITER / 74 |
| 86 | [87, 87] | DELIMITER / 88 |

## jcl/ESDSRRDS.jcl

SHA-256: `9bec766029968057b831f539cc91b84e4e1d8ee22aa3de5ba6b509f8a698de77`。レビュー: PENDING。

JOB ESDSRRDS@1、期待span [1, 124]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| PREDEL@24 | ['PGM', 'IEFBR14'] | DD01@26 |
| STEP01@33 | ['PGM', 'IEBGENER'] | SYSUT1@35, SYSUT2@47, SYSPRINT@52, SYSIN@53 |
| STEP02@59 | ['PGM', 'IDCAMS'] | SYSPRINT@61, SYSIN@62 |
| STEP03@79 | ['PGM', 'IDCAMS'] | IN@81, OUT@82, SYSOUT@83, SYSPRINT@84, SYSIN@85 |
| STEP04@93 | ['PGM', 'IDCAMS'] | SYSPRINT@95, SYSIN@96 |
| STEP05@113 | ['PGM', 'IDCAMS'] | IN@115, OUT@116, SYSOUT@117, SYSPRINT@118, SYSIN@119 |

tree参照必須の操作文先頭行: [1, 24, 26, 33, 35, 47, 52, 53, 59, 61, 62, 79, 81, 82, 83, 84, 85, 93, 95, 96, 113, 115, 116, 117, 118, 119]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 35 | [36, 45] | DELIMITER / 46 |
| 62 | [63, 72] | DELIMITER / 73 |
| 85 | [86, 86] | DELIMITER / 87 |
| 96 | [97, 106] | DELIMITER / 107 |
| 119 | [120, 120] | DELIMITER / 121 |

## jcl/FTPJCL.JCL

SHA-256: `10393acea782d865532700ac61c9282c0438e921b34e698ddba1a046e974899a`。レビュー: PENDING。

JOB FTPJCLS@1、期待span [1, 42]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP1@30 | ['PGM', 'FTP'] | SYSIN@32 |

tree参照必須の操作文先頭行: [1, 30, 32]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 32 | [33, 41] | NEXT_STATEMENT / 42 |

## jcl/INTCALC.jcl

SHA-256: `b9313658a1e6fdb570a765c5e5e0e9e23d83f7062439c7d18544da986fbf108d`。レビュー: PENDING。

JOB INTCALC@1、期待span [1, 44]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP15@22 | ['PGM', 'CBACT04C'] | STEPLIB@23, SYSPRINT@25, SYSOUT@26, TCATBALF@27, XREFFILE@29, XREFFIL1@31, ACCTFILE@33, DISCGRP@35, TRANSACT@37 |

tree参照必須の操作文先頭行: [1, 22, 23, 25, 26, 27, 29, 31, 33, 35, 37]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/INTRDRJ1.JCL

SHA-256: `bc1c4427ac4d980ea01686026f7f15d1e86b060c7c3dc5c795730cea5441dd87`。レビュー: PENDING。

JOB INTRDRJ1@1、期待span [1, 19]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| IDCAMS@6 | ['PGM', 'IDCAMS'] | SYSPRINT@7, IN@8, OUT@9, SYSIN@10 |
| STEP01@14 | ['PGM', 'IEBGENER'] | SYSPRINT@15, SYSIN@16, SYSUT1@17, SYSUT2@18 |

tree参照必須の操作文先頭行: [1, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 10 | [11, 11] | DELIMITER / 12 |

## jcl/INTRDRJ2.JCL

SHA-256: `e89c73e8ebffa116c27e7c2e335b364467355def280c6208b7ef9d70ca66c7a8`。レビュー: PENDING。

JOB INTRDRJ2@1、期待span [1, 14]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| IDCAMS@7 | ['PGM', 'IDCAMS'] | SYSPRINT@8, IN@9, OUT@10, SYSIN@11 |

tree参照必須の操作文先頭行: [1, 7, 8, 9, 10, 11]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 11 | [12, 12] | DELIMITER / 13 |

## jcl/OPENFIL.jcl

SHA-256: `adf1f084e330739d5b220bc6ba08b0345ab5b9083e020d6f4527d021b6838a3a`。レビュー: PENDING。

JOB OPENFIL@1、期待span [1, 34]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| OPCIFIL@22 | ['PGM', 'SDSF'] | ISFOUT@23, CMDOUT@24, ISFIN@25 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 30] | DELIMITER / 31 |

## jcl/POSTTRAN.jcl

SHA-256: `a4de9f8cc5fbcaefb12e0b05fe87cb7d0b4accaa8a05f2ff6c13cf325431e2d6`。レビュー: PENDING。

JOB POSTTRAN@1、期待span [1, 45]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP15@23 | ['PGM', 'CBTRN02C'] | STEPLIB@24, SYSPRINT@26, SYSOUT@27, TRANFILE@28, DALYTRAN@30, XREFFILE@32, DALYREJS@34, ACCTFILE@39, TCATBALF@41 |

tree参照必須の操作文先頭行: [1, 23, 24, 26, 27, 28, 30, 32, 34, 39, 41]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/PRTCATBL.jcl

SHA-256: `0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe`。レビュー: PENDING。

JOB PRTCATBL@1、期待span [1, 66]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| DELDEF@21 | ['PGM', 'IEFBR14'] | THEFILE@22 |
| STEP05R@29 | ['PROC', 'REPROC'] | PRC001.FILEIN@32, PRC001.FILEOUT@35 |
| STEP10R@43 | ['PGM', 'SORT'] | SORTIN@44, SYMNAMES@46, SYSIN@51, SYSOUT@58, SORTOUT@59 |

tree参照必須の操作文先頭行: [1, 19, 21, 22, 29, 32, 35, 43, 44, 46, 51, 58, 59]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 46 | [47, 50] | NEXT_STATEMENT / 51 |
| 51 | [52, 56] | DELIMITER / 57 |

## jcl/READACCT.jcl

SHA-256: `0965badda9c801df4f86e74755b66325764d8d1a840c615e6552b660f6401f15`。レビュー: PENDING。

JOB READACCT@1、期待span [1, 50]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| PREDEL@22 | ['PGM', 'IEFBR14'] | DD01@23, DD02@25, DD03@27 |
| STEP05@32 | ['PGM', 'CBACT01C'] | STEPLIB@33, ACCTFILE@35, OUTFILE@37, ARRYFILE@41, VBRCFILE@45, SYSOUT@49, SYSPRINT@50 |

tree参照必須の操作文先頭行: [1, 22, 23, 25, 27, 32, 33, 35, 37, 41, 45, 49, 50]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/READCARD.jcl

SHA-256: `2b8ef6678d477345868671ace4b6a9990e33081d6ba6b47827aad980927132b7`。レビュー: PENDING。

JOB READCARD@1、期待span [1, 31]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'CBACT02C'] | STEPLIB@23, CARDFILE@25, SYSOUT@27, SYSPRINT@28 |

tree参照必須の操作文先頭行: [1, 22, 23, 25, 27, 28]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/READCUST.jcl

SHA-256: `3b39d6182c5483967c63616df65c56359e13a8a10c5bf08dcff9fe98566196a9`。レビュー: PENDING。

JOB READCUST@1、期待span [1, 30]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@21 | ['PGM', 'CBCUS01C'] | STEPLIB@22, CUSTFILE@24, SYSOUT@26, SYSPRINT@27 |

tree参照必須の操作文先頭行: [1, 21, 22, 24, 26, 27]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/READXREF.jcl

SHA-256: `09f076859afdd2a12bbe2e5eb1380bb986a656efe7bfb65a39377ad2c581db52`。レビュー: PENDING。

JOB READXREF@1、期待span [1, 31]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'CBACT03C'] | STEPLIB@23, XREFFILE@25, SYSOUT@27, SYSPRINT@28 |

tree参照必須の操作文先頭行: [1, 22, 23, 25, 27, 28]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## jcl/REPTFILE.jcl

SHA-256: `b78fd0ff11009e23d5dce60a79daa5d947990d3b9e7a04ccb346fcc90151dee0`。レビュー: PENDING。

JOB REPTFILE@1、期待span [1, 32]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |

tree参照必須の操作文先頭行: [1, 22, 23, 24]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 28] | DELIMITER / 29 |

## jcl/TCATBALF.jcl

SHA-256: `9ff82ea5a21fd54c3ce405a14fd0851a7c17af71ed4e27a2bb2ce1860f50692b`。レビュー: PENDING。

JOB TCATBALF@1、期待span [1, 65]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP15@54 | ['PGM', 'IDCAMS'] | SYSPRINT@55, TCATBAL@56, TCATBALV@58, SYSIN@60 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 33, 34, 35, 54, 55, 56, 58, 60]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 27] | DELIMITER / 28 |
| 35 | [36, 49] | DELIMITER / 50 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/TRANBKP.jcl

SHA-256: `bd7a846799373121152a91b52427f3c668f390f448609d0eea534d49989acb9d`。レビュー: PENDING。

JOB TRANBKP@1、期待span [1, 71]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05R@23 | ['PROC', 'REPROC'] | PRC001.FILEIN@26, PRC001.FILEOUT@29 |
| STEP05@37 | ['PGM', 'IDCAMS'] | SYSPRINT@38, SYSIN@39 |
| STEP10@51 | ['PGM', 'IDCAMS'] | SYSPRINT@52, SYSIN@53 |

tree参照必須の操作文先頭行: [1, 19, 23, 26, 29, 37, 38, 39, 51, 52, 53]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 39 | [40, 45] | DELIMITER / 46 |
| 53 | [54, 67] | DELIMITER / 68 |

## jcl/TRANCATG.jcl

SHA-256: `09ad86b3c1ac0b32cee842682baead25c1ded1572c65599591b28826261de457`。レビュー: PENDING。

JOB TRANCATG@1、期待span [1, 65]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP15@54 | ['PGM', 'IDCAMS'] | SYSPRINT@55, TRANCATG@56, TCATVSAM@58, SYSIN@60 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 33, 34, 35, 54, 55, 56, 58, 60]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 27] | DELIMITER / 28 |
| 35 | [36, 49] | DELIMITER / 50 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/TRANFILE.jcl

SHA-256: `c506a68f7482a971133524ec1d8b76001f593d4e1e98477c12c80ede4e4ce2db`。レビュー: PENDING。

JOB TRANFILE@1、期待span [1, 125]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| CLCIFIL@22 | ['PGM', 'SDSF'] | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| STEP05@32 | ['PGM', 'IDCAMS'] | SYSPRINT@33, SYSIN@34 |
| STEP10@46 | ['PGM', 'IDCAMS'] | SYSPRINT@47, SYSIN@48 |
| STEP15@67 | ['PGM', 'IDCAMS'] | SYSPRINT@68, TRANSACT@69, TRANVSAM@71, SYSIN@73 |
| STEP20@79 | ['PGM', 'IDCAMS'] | SYSPRINT@80, SYSIN@81 |
| STEP25@96 | ['PGM', 'IDCAMS'] | SYSPRINT@97, SYSIN@98 |
| STEP30@106 | ['PGM', 'IDCAMS'] | SYSPRINT@107, SYSIN@108 |
| OPCIFIL@116 | ['PGM', 'SDSF'] | ISFOUT@117, CMDOUT@118, ISFIN@119 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25, 32, 33, 34, 46, 47, 48, 67, 68, 69, 71, 73, 79, 80, 81, 96, 97, 98, 106, 107, 108, 116, 117, 118, 119]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 27] | DELIMITER / 28 |
| 34 | [35, 40] | DELIMITER / 41 |
| 48 | [49, 62] | DELIMITER / 63 |
| 73 | [74, 74] | DELIMITER / 75 |
| 81 | [82, 91] | DELIMITER / 92 |
| 98 | [99, 101] | DELIMITER / 102 |
| 108 | [109, 111] | DELIMITER / 112 |
| 119 | [120, 121] | DELIMITER / 122 |

## jcl/TRANIDX.jcl

SHA-256: `ad12d5f7b4b4e37b17baf23a5b1bf208ff35945182d587a909e0208d3bd45855`。レビュー: PENDING。

JOB TRANIDX@1、期待span [1, 58]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP20@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP25@39 | ['PGM', 'IDCAMS'] | SYSPRINT@40, SYSIN@41 |
| STEP30@49 | ['PGM', 'IDCAMS'] | SYSPRINT@50, SYSIN@51 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 39, 40, 41, 49, 50, 51]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 34] | DELIMITER / 35 |
| 41 | [42, 44] | DELIMITER / 45 |
| 51 | [52, 54] | DELIMITER / 55 |

## jcl/TRANREPT.jcl

SHA-256: `081aad149f0a9c020440fb6e6da93f2a6cf6d1f77eead3cefea3702b13d79802`。レビュー: PENDING。

JOB TRANREPT@1、期待span [1, 84]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05R@23 | ['PROC', 'REPROC'] | PRC001.FILEIN@26, PRC001.FILEOUT@29 |
| STEP05R@37 | ['PGM', 'SORT'] | SORTIN@38, SYMNAMES@40, SYSIN@45, SYSOUT@50, SORTOUT@51 |
| STEP10R@59 | ['PGM', 'CBTRN03C'] | STEPLIB@60, SYSOUT@62, SYSPRINT@63, TRANFILE@65, CARDXREF@67, TRANTYPE@69, TRANCATG@71, DATEPARM@73, TRANREPT@76 |

tree参照必須の操作文先頭行: [1, 19, 23, 26, 29, 37, 38, 40, 45, 50, 51, 59, 60, 62, 63, 65, 67, 69, 71, 73, 76]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 40 | [41, 44] | NEXT_STATEMENT / 45 |
| 45 | [46, 48] | DELIMITER / 49 |

## jcl/TRANTYPE.jcl

SHA-256: `7993012c72041e6a9cbda9fff43549af4f8789081dc8a64b71a8a1a01f775254`。レビュー: PENDING。

JOB TRANTYPE@1、期待span [1, 65]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@33 | ['PGM', 'IDCAMS'] | SYSPRINT@34, SYSIN@35 |
| STEP15@54 | ['PGM', 'IDCAMS'] | SYSPRINT@55, TRANTYPE@56, TTYPVSAM@58, SYSIN@60 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 33, 34, 35, 54, 55, 56, 58, 60]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 27] | DELIMITER / 28 |
| 35 | [36, 49] | DELIMITER / 50 |
| 60 | [61, 61] | DELIMITER / 62 |

## jcl/TXT2PDF1.JCL

SHA-256: `7b051e99abe3fdcf772d613646b39f9abf10b02e9f52422d073fa0c52908e46b`。レビュー: PENDING。

JOB TXT2PDF1@1、期待span [1, 41]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| TXT2PDF@24 | ['PGM', 'IKJEFT1B'] | STEPLIB@28, SYSEXEC@31, INDD@33, SYSPRINT@35, SYSTSPRT@36, SYSTSIN@37 |

tree参照必須の操作文先頭行: [1, 24, 28, 31, 33, 35, 36, 37]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 37 | [38, 39] | DELIMITER / 40 |

## jcl/WAITSTEP.jcl

SHA-256: `36c98a55c7701bfaa9bd6404d2aca95888880d4f908ced678840a37e2e3eac5e`。レビュー: PENDING。

JOB WAITSTEP@1、期待span [1, 27]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| WAIT@22 | ['PGM', 'COBSWAIT'] | STEPLIB@23, SYSOUT@24, SYSIN@25 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 25]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 25 | [26, 26] | DELIMITER / 27 |

## jcl/XREFFILE.jcl

SHA-256: `f4a24014ae9ebfdf4d36db958e1fadb76158114fa6f721e9b547d0842d556f24`。レビュー: PENDING。

JOB XREFFILE@1、期待span [1, 106]。

JOB DD: 

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP05@22 | ['PGM', 'IDCAMS'] | SYSPRINT@23, SYSIN@24 |
| STEP10@36 | ['PGM', 'IDCAMS'] | SYSPRINT@37, SYSIN@38 |
| STEP15@57 | ['PGM', 'IDCAMS'] | SYSPRINT@58, XREFDATA@59, XREFVSAM@61, SYSIN@63 |
| STEP20@69 | ['PGM', 'IDCAMS'] | SYSPRINT@70, SYSIN@71 |
| STEP25@87 | ['PGM', 'IDCAMS'] | SYSPRINT@88, SYSIN@89 |
| STEP30@97 | ['PGM', 'IDCAMS'] | SYSPRINT@98, SYSIN@99 |

tree参照必須の操作文先頭行: [1, 22, 23, 24, 36, 37, 38, 57, 58, 59, 61, 63, 69, 70, 71, 87, 88, 89, 97, 98, 99]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 24 | [25, 30] | DELIMITER / 31 |
| 38 | [39, 52] | DELIMITER / 53 |
| 63 | [64, 64] | DELIMITER / 65 |
| 71 | [72, 82] | DELIMITER / 83 |
| 89 | [90, 92] | DELIMITER / 93 |
| 99 | [100, 102] | DELIMITER / 103 |

## proc/REPROC.prc

SHA-256: `cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53`。レビュー: PENDING。

PROC header: {'name': 'REPROC', 'line': 1}

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| PRC001@21 | ['PGM', 'IDCAMS'] | SYSPRINT@22, FILEIN@23, FILEOUT@25, SYSIN@27 |

tree参照必須の操作文先頭行: [1, 21, 22, 23, 25, 27, 29]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|

## proc/TRANREPT.prc

SHA-256: `fdbdc473dd21ba4908613c47180542ceffea8ea9a976a9413355361c6deaf103`。レビュー: PENDING。

PROC header: {'name': 'REPROC', 'line': 1}

| STEP/行 | 対象 | DD (原本順) |
|---|---|---|
| STEP01R@21 | ['PROC', 'REPROC'] | PRC001.FILEIN@24, PRC001.FILEOUT@27 |
| STEP05R@35 | ['PGM', 'SORT'] | SORTIN@36, SYMNAMES@38, SYSIN@43, SYSOUT@48, SORTOUT@49 |
| STEP10R@57 | ['PGM', 'CBTRN03C'] | STEPLIB@58, SYSOUT@60, SYSPRINT@61, TRANFILE@63, CARDXREF@65, TRANTYPE@67, TRANCATG@69, DATEPARM@71, TRANREPT@74 |

tree参照必須の操作文先頭行: [1, 21, 24, 27, 35, 36, 38, 43, 48, 49, 57, 58, 60, 61, 63, 65, 67, 69, 71, 74, 79]

| DD先頭行 | データ行 | 終端 / 行 |
|---|---|---|
| 38 | [39, 42] | NEXT_STATEMENT / 43 |
| 43 | [44, 46] | DELIMITER / 47 |


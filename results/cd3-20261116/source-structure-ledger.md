# CD-3 全48ファイル source構造レビュー台帳

原本から独立導出した観測表。新しいGoldenでも承認記録でもない。

## app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl

SHA-256: `c90fbd21b8ea2b6448b8939ff4f3b47c6f73472465cd7d1e25871f7779063a86`。型: `job`。
JOB範囲: `[1, 47]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 24 | STEP01 | PGM=DFSRRC00 | STEPLIB@26 [STEPLIB/0], (無名)@27 [STEPLIB/1], DFSRESLB@28 [DFSRESLB/0], PROCLIB@29 [PROCLIB/0], DFSSEL@31 [DFSSEL/0], IMS@33 [IMS/0], (無名)@34 [IMS/1], SYSIN@36 [SYSIN/0], SYSOUX@39 [SYSOUX/0], SYSOUT@40 [SYSOUT/0], SYSABOUT@41 [SYSABOUT/0], ABENDAID@42 [ABENDAID/0], IEFRDER@43 [IEFRDER/0], IMSLOGR@44 [IMSLOGR/0], SYSPRINT@45 [SYSPRINT/0], SYSUDUMP@46 [SYSUDUMP/0], IMSERR@47 [IMSERR/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 36 | 37–37 | NEXT_STATEMENT | 38 |

## app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl

SHA-256: `3fabb7f3230f98fee855a8d436f70f4bd601a9e544f29c83d413a3a7a61efbcd`。型: `job`。
JOB範囲: `[1, 47]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 7 | STEPDEL | PGM=IEFBR14 | SYSPRINT@8 [SYSPRINT/0], SYSUT1@9 [SYSUT1/0] |
| 15 | UNLOAD | PGM=DFSRRC00 | STEPLIB@18 [STEPLIB/0], (無名)@19 [STEPLIB/1], DFSRESLB@20 [DFSRESLB/0], IMS@21 [IMS/0], (無名)@22 [IMS/1], SYSPRINT@23 [SYSPRINT/0], DFSURGU1@25 [DFSURGU1/0], DDPAUTP0@31 [DDPAUTP0/0], DDPAUTX0@32 [DDPAUTX0/0], DFSVSAMP@33 [DFSVSAMP/0], DFSCTL@34 [DFSCTL/0], SYSUDUMP@36 [SYSUDUMP/0], RECON1@40 [RECON1/0], RECON2@41 [RECON2/0], RECON3@42 [RECON3/0], DFSWRK01@44 [DFSWRK01/0], DFSSRT01@45 [DFSSRT01/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 34 | 35–35 | NEXT_STATEMENT | 36 |

## app-authorization-ims-db2-mq/jcl/LOADPADB.JCL

SHA-256: `9a0a88472f69236d14b36ecc89d83f35179d5c720c2c3a465af5f7ff510fb067`。型: `job`。
JOB範囲: `[1, 51]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 26 | STEP01 | PGM=DFSRRC00 | STEPLIB@28 [STEPLIB/0], (無名)@29 [STEPLIB/1], (無名)@30 [STEPLIB/2], DFSRESLB@31 [DFSRESLB/0], IMS@33 [IMS/0], (無名)@34 [IMS/1], INFILE1@36 [INFILE1/0], INFILE2@38 [INFILE2/0], DFSVSAMP@44 [DFSVSAMP/0], IMSLOGR@46 [IMSLOGR/0], IEFRDER@47 [IEFRDER/0], SYSPRINT@48 [SYSPRINT/0], SYSUDUMP@49 [SYSUDUMP/0], IMSERR@50 [IMSERR/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL

SHA-256: `1da94de3db6f265578c8b7498a2371c0c7246c8409f4ac44eb8013d3f0e113b8`。型: `job`。
JOB範囲: `[1, 53]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 26 | STEP01 | PGM=DFSRRC00 | STEPLIB@28 [STEPLIB/0], (無名)@29 [STEPLIB/1], (無名)@30 [STEPLIB/2], DFSRESLB@31 [DFSRESLB/0], IMS@33 [IMS/0], (無名)@34 [IMS/1], PASFILOP@36 [PASFILOP/0], PADFILOP@39 [PADFILOP/0], DDPAUTP0@42 [DDPAUTP0/0], DDPAUTX0@43 [DDPAUTX0/0], DFSVSAMP@46 [DFSVSAMP/0], IMSLOGR@48 [IMSLOGR/0], IEFRDER@49 [IEFRDER/0], SYSPRINT@50 [SYSPRINT/0], SYSUDUMP@51 [SYSUDUMP/0], IMSERR@52 [IMSERR/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL

SHA-256: `e2c26ca546ab427d66cadeaff07345bad706c979ca396fb04e60d401dc93c66b`。型: `job`。
JOB範囲: `[1, 69]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 25 | STEP0 | PGM=IEFBR14 | SYSPRINT@27 [SYSPRINT/0], SYSOUT@29 [SYSOUT/0], SYSDUMP@31 [SYSDUMP/0], DD1@33 [DD1/0], DD2@35 [DD2/0] |
| 38 | STEP01 | PGM=DFSRRC00 | STEPLIB@40 [STEPLIB/0], (無名)@41 [STEPLIB/1], (無名)@42 [STEPLIB/2], DFSRESLB@43 [DFSRESLB/0], IMS@45 [IMS/0], (無名)@46 [IMS/1], OUTFIL1@48 [OUTFIL1/0], OUTFIL2@53 [OUTFIL2/0], DDPAUTP0@58 [DDPAUTP0/0], DDPAUTX0@59 [DDPAUTX0/0], DFSVSAMP@62 [DFSVSAMP/0], IMSLOGR@64 [IMSLOGR/0], IEFRDER@65 [IEFRDER/0], SYSPRINT@66 [SYSPRINT/0], SYSUDUMP@67 [SYSUDUMP/0], IMSERR@68 [IMSERR/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## app-transaction-type-db2/jcl/CREADB21.jcl

SHA-256: `88b81b1d8530037d1661321e47600b9afb2a2cf4894c7eefeacd5aff07b87d69`。型: `job`。
JOB範囲: `[1, 84]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| JOB | — | — | JOBLIB@32 [JOBLIB/0], (無名)@33 [JOBLIB/1], (無名)@34 [JOBLIB/2] |
| 40 | FREEPLN | PGM=IKJEFT01 | STEPLIB@41 [STEPLIB/0], (無名)@42 [STEPLIB/1], SYSPRINT@43 [SYSPRINT/0], SYSTSPRT@44 [SYSTSPRT/0], SYSUDUMP@45 [SYSUDUMP/0], SYSTSIN@46 [SYSTSIN/0] |
| 52 | CRCRDDB | PGM=IKJEFT01 | STEPLIB@53 [STEPLIB/0], (無名)@54 [STEPLIB/1], SYSTSPRT@55 [SYSTSPRT/0], SYSUDUMP@56 [SYSUDUMP/0], SYSPRINT@57 [SYSPRINT/0], SYSTSIN@58 [SYSTSIN/0], SYSIN@59 [SYSIN/0] |
| 64 | LDTTYPE | PGM=IEFBR14 |  |
| 65 | RUNTEP2 | PGM=IKJEFT01 | STEPLIB@66 [STEPLIB/0], (無名)@67 [STEPLIB/1], SYSTSPRT@68 [SYSTSPRT/0], SYSUDUMP@69 [SYSUDUMP/0], SYSPRINT@70 [SYSPRINT/0], SYSTSIN@71 [SYSTSIN/0], SYSIN@72 [SYSIN/0] |
| 77 | LDTCCAT | PGM=IKJEFT01 | STEPLIB@78 [STEPLIB/0], (無名)@79 [STEPLIB/1], SYSTSPRT@80 [SYSTSPRT/0], SYSUDUMP@81 [SYSUDUMP/0], SYSPRINT@82 [SYSPRINT/0], SYSTSIN@83 [SYSTSIN/0], SYSIN@84 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## app-transaction-type-db2/jcl/MNTTRDB2.jcl

SHA-256: `beaba6e4e35092c2ac7c1be7a3708303cc75d0fca00b64c65ee2d2bc1682f893`。型: `job`。
JOB範囲: `[1, 30]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | STEP1 | PGM=IKJEFT01 | STEPLIB@22 [STEPLIB/0], (無名)@23 [STEPLIB/1], (無名)@24 [STEPLIB/2], DBRMLIB@25 [DBRMLIB/0], SYSTSPRT@26 [SYSTSPRT/0], INPFILE@27 [INPFILE/0], SYSTSIN@28 [SYSTSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 28 | 29–30 | EOF | None |

## app-transaction-type-db2/jcl/TRANEXTR.jcl

SHA-256: `d4d3b99a71b91fbce9c145283642ee7ca31b5ad7fa51ddcdb3e2c0b2e530457f`。型: `job`。
JOB範囲: `[1, 122]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 31 | STEP10 | PGM=IEBGENER | SYSPRINT@32 [SYSPRINT/0], SYSIN@33 [SYSIN/0], SYSUT1@34 [SYSUT1/0], SYSUT2@35 [SYSUT2/0] |
| 42 | STEP20 | PGM=IEBGENER | SYSPRINT@43 [SYSPRINT/0], SYSIN@44 [SYSIN/0], SYSUT1@45 [SYSUT1/0], SYSUT2@46 [SYSUT2/0] |
| 53 | STEP30 | PGM=IEFBR14 | DD01@54 [DD01/0], DD02@58 [DD02/0] |
| 65 | STEP40 | PGM=IKJEFT01 | STEPLIB@66 [STEPLIB/0], (無名)@67 [STEPLIB/1], SYSTSPRT@68 [SYSTSPRT/0], SYSPRINT@69 [SYSPRINT/0], SYSUDUMP@70 [SYSUDUMP/0], SYSPUNCH@71 [SYSPUNCH/0], SYSREC00@72 [SYSREC00/0], SYSIN@75 [SYSIN/0], SYSTSIN@86 [SYSTSIN/0] |
| 95 | STEP50 | PGM=IKJEFT01 | STEPLIB@96 [STEPLIB/0], (無名)@97 [STEPLIB/1], SYSTSPRT@98 [SYSTSPRT/0], SYSPRINT@99 [SYSPRINT/0], SYSUDUMP@100 [SYSUDUMP/0], SYSPUNCH@101 [SYSPUNCH/0], SYSREC00@102 [SYSREC00/0], SYSIN@105 [SYSIN/0], SYSTSIN@117 [SYSTSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 75 | 76–84 | DELIMITER | 85 |
| 86 | 87–90 | DELIMITER | 91 |
| 105 | 106–115 | DELIMITER | 116 |
| 117 | 118–121 | DELIMITER | 122 |

## jcl/ACCTFILE.jcl

SHA-256: `92ce6733ad0e3fad640e19d1224003fe30c711c2564eb7a660d53fd7f0dd6622`。型: `job`。
JOB範囲: `[1, 65]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 33 | STEP10 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 54 | STEP15 | PGM=IDCAMS | SYSPRINT@55 [SYSPRINT/0], ACCTDATA@56 [ACCTDATA/0], ACCTVSAM@58 [ACCTVSAM/0], SYSIN@60 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–27 | DELIMITER | 28 |
| 35 | 36–49 | DELIMITER | 50 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/CARDFILE.jcl

SHA-256: `795600a41abec0706aec8bd0dd93446b29cf01fcd8f9d2173e4ec6d5476611d0`。型: `job`。
JOB範囲: `[1, 128]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | CLCIFIL | PGM=SDSF | ISFOUT@23 [ISFOUT/0], CMDOUT@24 [CMDOUT/0], ISFIN@25 [ISFIN/0] |
| 33 | STEP05 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 47 | STEP10 | PGM=IDCAMS | SYSPRINT@48 [SYSPRINT/0], SYSIN@49 [SYSIN/0] |
| 68 | STEP15 | PGM=IDCAMS | SYSPRINT@69 [SYSPRINT/0], CARDDATA@70 [CARDDATA/0], CARDVSAM@72 [CARDVSAM/0], SYSIN@74 [SYSIN/0] |
| 80 | STEP40 | PGM=IDCAMS | SYSPRINT@81 [SYSPRINT/0], SYSIN@82 [SYSIN/0] |
| 97 | STEP50 | PGM=IDCAMS | SYSPRINT@98 [SYSPRINT/0], SYSIN@99 [SYSIN/0] |
| 107 | STEP60 | PGM=IDCAMS | SYSPRINT@108 [SYSPRINT/0], SYSIN@109 [SYSIN/0] |
| 118 | OPCIFIL | PGM=SDSF | ISFOUT@119 [ISFOUT/0], CMDOUT@120 [CMDOUT/0], ISFIN@121 [ISFIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–27 | DELIMITER | 28 |
| 35 | 36–41 | DELIMITER | 42 |
| 49 | 50–63 | DELIMITER | 64 |
| 74 | 75–75 | DELIMITER | 76 |
| 82 | 83–92 | DELIMITER | 93 |
| 99 | 100–102 | DELIMITER | 103 |
| 109 | 110–112 | DELIMITER | 113 |
| 121 | 122–123 | DELIMITER | 124 |

## jcl/CBADMCDJ.jcl

SHA-256: `49b99c74e97d7177e558748f58b73cc418daacd93b415d908b09651393841916`。型: `job`。
JOB範囲: `[1, 167]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 27 | STEP1 | PGM=DFHCSDUP | STEPLIB@29 [STEPLIB/0], DFHCSD@30 [DFHCSD/0], OUTDD@31 [OUTDD/0], SYSPRINT@32 [SYSPRINT/0], SYSIN@33 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 33 | 34–162 | DELIMITER | 163 |

## jcl/CBEXPORT.jcl

SHA-256: `e5d010a3209dbbcf6d9b92a3c71b7c806019ce014ad921430eed9abf1706f804`。型: `job`。
JOB範囲: `[1, 72]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 24 | STEP01 | PGM=IDCAMS | SYSPRINT@25 [SYSPRINT/0], SYSIN@26 [SYSIN/0] |
| 43 | STEP02 | PGM=CBEXPORT | STEPLIB@44 [STEPLIB/0], CUSTFILE@49 [CUSTFILE/0], ACCTFILE@51 [ACCTFILE/0], XREFFILE@53 [XREFFILE/0], TRANSACT@55 [TRANSACT/0], CARDFILE@57 [CARDFILE/0], EXPFILE@62 [EXPFILE/0], SYSOUT@67 [SYSOUT/0], SYSPRINT@68 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 26 | 27–38 | DELIMITER | 39 |

## jcl/CBIMPORT.jcl

SHA-256: `9f3adc0cde9d471b0976a4e4c5bee625a65fd0cdcc1e031d9abde8f5c3e8ccf5`。型: `job`。
JOB範囲: `[1, 68]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP01 | PGM=CBIMPORT | STEPLIB@23 [STEPLIB/0], EXPFILE@28 [EXPFILE/0], CUSTOUT@33 [CUSTOUT/0], ACCTOUT@38 [ACCTOUT/0], XREFOUT@43 [XREFOUT/0], TRNXOUT@48 [TRNXOUT/0], ERROUT@56 [ERROUT/0], SYSOUT@64 [SYSOUT/0], SYSPRINT@65 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/CLOSEFIL.jcl

SHA-256: `e47d406dde49f06847a46559fa9a7182b80b85f0727a5f0be312286f34df9192`。型: `job`。
JOB範囲: `[1, 34]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | CLCIFIL | PGM=SDSF | ISFOUT@23 [ISFOUT/0], CMDOUT@24 [CMDOUT/0], ISFIN@25 [ISFIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–30 | DELIMITER | 31 |

## jcl/COMBTRAN.jcl

SHA-256: `a91649d6a927e1fd7b81fcdab39088ae26554eea52b07d5715e488c81c3f2cc2`。型: `job`。
JOB範囲: `[1, 52]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05R | PGM=SORT | SORTIN@23 [SORTIN/0], (無名)@25 [SORTIN/1], SYMNAMES@27 [SYMNAMES/0], SYSIN@29 [SYSIN/0], SYSOUT@32 [SYSOUT/0], SORTOUT@33 [SORTOUT/0] |
| 41 | STEP10 | PGM=IDCAMS | SYSPRINT@42 [SYSPRINT/0], TRANSACT@43 [TRANSACT/0], TRANVSAM@45 [TRANVSAM/0], SYSIN@47 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 27 | 28–28 | NEXT_STATEMENT | 29 |
| 29 | 30–30 | DELIMITER | 31 |
| 47 | 48–48 | DELIMITER | 49 |

## jcl/CREASTMT.JCL

SHA-256: `87a18700fac7bccfffbefa5d80fed0b171fdc36caeebb575c8a3cf66e4fc3caa`。型: `job`。
JOB範囲: `[1, 97]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | DELDEF01 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 44 | STEP010 | PGM=SORT | SORTIN@45 [SORTIN/0], SYSPRINT@46 [SYSPRINT/0], SYSOUT@47 [SYSOUT/0], SORTOUT@48 [SORTOUT/0], SYSIN@52 [SYSIN/0] |
| 56 | STEP020 | PGM=IDCAMS | SYSPRINT@57 [SYSPRINT/0], INFILE@58 [INFILE/0], OUTFILE@59 [OUTFILE/0], SYSIN@60 [SYSIN/0] |
| 66 | STEP030 | PGM=IEFBR14 | HTMLFILE@67 [HTMLFILE/0], STMTFILE@72 [STMTFILE/0] |
| 79 | STEP040 | PGM=CBSTM03A | STEPLIB@80 [STEPLIB/0], SYSPRINT@81 [SYSPRINT/0], SYSOUT@82 [SYSOUT/0], TRNXFILE@83 [TRNXFILE/0], XREFFILE@84 [XREFFILE/0], ACCTFILE@85 [ACCTFILE/0], CUSTFILE@86 [CUSTFILE/0], STMTFILE@87 [STMTFILE/0], HTMLFILE@92 [HTMLFILE/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–39 | DELIMITER | 40 |
| 52 | 53–54 | DELIMITER | 55 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/CUSTFILE.jcl

SHA-256: `5fa6da4bc85866f0e08783585e7c652d312179982dbdd821866f569a083ac976`。型: `job`。
JOB範囲: `[1, 84]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | CLCIFIL | PGM=SDSF | ISFOUT@23 [ISFOUT/0], CMDOUT@24 [CMDOUT/0], ISFIN@25 [ISFIN/0] |
| 32 | STEP05 | PGM=IDCAMS | SYSPRINT@33 [SYSPRINT/0], SYSIN@34 [SYSIN/0] |
| 43 | STEP10 | PGM=IDCAMS | SYSPRINT@44 [SYSPRINT/0], SYSIN@45 [SYSIN/0] |
| 64 | STEP15 | PGM=IDCAMS | SYSPRINT@65 [SYSPRINT/0], CUSTDATA@66 [CUSTDATA/0], CUSTVSAM@68 [CUSTVSAM/0], SYSIN@70 [SYSIN/0] |
| 76 | OPCIFIL | PGM=SDSF | ISFOUT@77 [ISFOUT/0], CMDOUT@78 [CMDOUT/0], ISFIN@79 [ISFIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–26 | DELIMITER | 27 |
| 34 | 35–37 | DELIMITER | 38 |
| 45 | 46–59 | DELIMITER | 60 |
| 70 | 71–71 | DELIMITER | 72 |
| 79 | 80–80 | DELIMITER | 81 |

## jcl/DALYREJS.jcl

SHA-256: `ce396a6469c84577ea508d184f7ea6a42ceacd54c6a5e0fb097e626bb6361d45`。型: `job`。
JOB範囲: `[1, 32]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | STEP05 | PGM=IDCAMS | SYSPRINT@22 [SYSPRINT/0], SYSIN@23 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 23 | 24–28 | DELIMITER | 29 |

## jcl/DEFCUST.jcl

SHA-256: `03dd2fc683ced79ec53269f6a24d48ceadb87ae4d6a5b48b65a37763046dfd58`。型: `job`。
JOB範囲: `[1, 47]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 32 | STEP05 | PGM=IDCAMS | SYSPRINT@33 [SYSPRINT/0], SYSIN@34 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–26 | DELIMITER | 27 |
| 34 | 35–46 | DELIMITER | 47 |

## jcl/DEFGDGB.jcl

SHA-256: `4ccd135a079641b2d484b7789ea0f47955725774442283274f204480c0903f3f`。型: `job`。
JOB範囲: `[1, 63]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | STEP05 | PGM=IDCAMS | SYSPRINT@22 [SYSPRINT/0], SYSIN@23 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 23 | 24–59 | DELIMITER | 60 |

## jcl/DEFGDGD.jcl

SHA-256: `78c13d7e0e851aecd1acbfcedd26b60633a3a850dcd9fe38de339362be5e4830`。型: `job`。
JOB範囲: `[1, 94]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 24 | STEP10 | PGM=IDCAMS | SYSPRINT@25 [SYSPRINT/0], SYSIN@26 [SYSIN/0] |
| 36 | STEP20 | PGM=IEBGENER | SYSPRINT@37 [SYSPRINT/0], SYSIN@38 [SYSIN/0], SYSUT1@39 [SYSUT1/0], SYSUT2@40 [SYSUT2/0] |
| 47 | STEP30 | PGM=IDCAMS | SYSPRINT@48 [SYSPRINT/0], SYSIN@49 [SYSIN/0] |
| 59 | STEP40 | PGM=IEBGENER | SYSPRINT@60 [SYSPRINT/0], SYSIN@61 [SYSIN/0], SYSUT1@62 [SYSUT1/0], SYSUT2@63 [SYSUT2/0] |
| 70 | STEP50 | PGM=IDCAMS | SYSPRINT@71 [SYSPRINT/0], SYSIN@72 [SYSIN/0] |
| 82 | STEP60 | PGM=IEBGENER | SYSPRINT@83 [SYSPRINT/0], SYSIN@84 [SYSIN/0], SYSUT1@85 [SYSUT1/0], SYSUT2@86 [SYSUT2/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 26 | 27–31 | DELIMITER | 32 |
| 49 | 50–54 | DELIMITER | 55 |
| 72 | 73–77 | DELIMITER | 78 |

## jcl/DISCGRP.jcl

SHA-256: `64a250c918cc8205eddd6d51615e24a8c23585ff012ea518c6d452ebd7d71492`。型: `job`。
JOB範囲: `[1, 65]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 33 | STEP10 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 54 | STEP15 | PGM=IDCAMS | SYSPRINT@55 [SYSPRINT/0], DISCGRP@56 [DISCGRP/0], DISCVSAM@58 [DISCVSAM/0], SYSIN@60 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–27 | DELIMITER | 28 |
| 35 | 36–49 | DELIMITER | 50 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/DUSRSECJ.jcl

SHA-256: `71a529aab49502e9ce57abcdb268a896e34b947409d3278c5dd813f93105e33f`。型: `job`。
JOB範囲: `[1, 92]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 23 | PREDEL | PGM=IEFBR14 | DD01@25 [DD01/0] |
| 32 | STEP01 | PGM=IEBGENER | SYSUT1@34 [SYSUT1/0], SYSUT2@46 [SYSUT2/0], SYSPRINT@51 [SYSPRINT/0], SYSIN@52 [SYSIN/0] |
| 58 | STEP02 | PGM=IDCAMS | SYSPRINT@60 [SYSPRINT/0], SYSIN@61 [SYSIN/0] |
| 80 | STEP03 | PGM=IDCAMS | IN@82 [IN/0], OUT@83 [OUT/0], SYSOUT@84 [SYSOUT/0], SYSPRINT@85 [SYSPRINT/0], SYSIN@86 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 34 | 35–44 | DELIMITER | 45 |
| 61 | 62–73 | DELIMITER | 74 |
| 86 | 87–87 | DELIMITER | 88 |

## jcl/ESDSRRDS.jcl

SHA-256: `9bec766029968057b831f539cc91b84e4e1d8ee22aa3de5ba6b509f8a698de77`。型: `job`。
JOB範囲: `[1, 124]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 24 | PREDEL | PGM=IEFBR14 | DD01@26 [DD01/0] |
| 33 | STEP01 | PGM=IEBGENER | SYSUT1@35 [SYSUT1/0], SYSUT2@47 [SYSUT2/0], SYSPRINT@52 [SYSPRINT/0], SYSIN@53 [SYSIN/0] |
| 59 | STEP02 | PGM=IDCAMS | SYSPRINT@61 [SYSPRINT/0], SYSIN@62 [SYSIN/0] |
| 79 | STEP03 | PGM=IDCAMS | IN@81 [IN/0], OUT@82 [OUT/0], SYSOUT@83 [SYSOUT/0], SYSPRINT@84 [SYSPRINT/0], SYSIN@85 [SYSIN/0] |
| 93 | STEP04 | PGM=IDCAMS | SYSPRINT@95 [SYSPRINT/0], SYSIN@96 [SYSIN/0] |
| 113 | STEP05 | PGM=IDCAMS | IN@115 [IN/0], OUT@116 [OUT/0], SYSOUT@117 [SYSOUT/0], SYSPRINT@118 [SYSPRINT/0], SYSIN@119 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 35 | 36–45 | DELIMITER | 46 |
| 62 | 63–72 | DELIMITER | 73 |
| 85 | 86–86 | DELIMITER | 87 |
| 96 | 97–106 | DELIMITER | 107 |
| 119 | 120–120 | DELIMITER | 121 |

## jcl/FTPJCL.JCL

SHA-256: `10393acea782d865532700ac61c9282c0438e921b34e698ddba1a046e974899a`。型: `job`。
JOB範囲: `[1, 42]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 30 | STEP1 | PGM=FTP | SYSIN@32 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 32 | 33–41 | NEXT_STATEMENT | 42 |

## jcl/INTCALC.jcl

SHA-256: `b9313658a1e6fdb570a765c5e5e0e9e23d83f7062439c7d18544da986fbf108d`。型: `job`。
JOB範囲: `[1, 44]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP15 | PGM=CBACT04C | STEPLIB@23 [STEPLIB/0], SYSPRINT@25 [SYSPRINT/0], SYSOUT@26 [SYSOUT/0], TCATBALF@27 [TCATBALF/0], XREFFILE@29 [XREFFILE/0], XREFFIL1@31 [XREFFIL1/0], ACCTFILE@33 [ACCTFILE/0], DISCGRP@35 [DISCGRP/0], TRANSACT@37 [TRANSACT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/INTRDRJ1.JCL

SHA-256: `bc1c4427ac4d980ea01686026f7f15d1e86b060c7c3dc5c795730cea5441dd87`。型: `job`。
JOB範囲: `[1, 19]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 6 | IDCAMS | PGM=IDCAMS | SYSPRINT@7 [SYSPRINT/0], IN@8 [IN/0], OUT@9 [OUT/0], SYSIN@10 [SYSIN/0] |
| 14 | STEP01 | PGM=IEBGENER | SYSPRINT@15 [SYSPRINT/0], SYSIN@16 [SYSIN/0], SYSUT1@17 [SYSUT1/0], SYSUT2@18 [SYSUT2/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 10 | 11–11 | DELIMITER | 12 |

## jcl/INTRDRJ2.JCL

SHA-256: `e89c73e8ebffa116c27e7c2e335b364467355def280c6208b7ef9d70ca66c7a8`。型: `job`。
JOB範囲: `[1, 14]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 7 | IDCAMS | PGM=IDCAMS | SYSPRINT@8 [SYSPRINT/0], IN@9 [IN/0], OUT@10 [OUT/0], SYSIN@11 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 11 | 12–12 | DELIMITER | 13 |

## jcl/OPENFIL.jcl

SHA-256: `adf1f084e330739d5b220bc6ba08b0345ab5b9083e020d6f4527d021b6838a3a`。型: `job`。
JOB範囲: `[1, 34]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | OPCIFIL | PGM=SDSF | ISFOUT@23 [ISFOUT/0], CMDOUT@24 [CMDOUT/0], ISFIN@25 [ISFIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–30 | DELIMITER | 31 |

## jcl/POSTTRAN.jcl

SHA-256: `a4de9f8cc5fbcaefb12e0b05fe87cb7d0b4accaa8a05f2ff6c13cf325431e2d6`。型: `job`。
JOB範囲: `[1, 45]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 23 | STEP15 | PGM=CBTRN02C | STEPLIB@24 [STEPLIB/0], SYSPRINT@26 [SYSPRINT/0], SYSOUT@27 [SYSOUT/0], TRANFILE@28 [TRANFILE/0], DALYTRAN@30 [DALYTRAN/0], XREFFILE@32 [XREFFILE/0], DALYREJS@34 [DALYREJS/0], ACCTFILE@39 [ACCTFILE/0], TCATBALF@41 [TCATBALF/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/PRTCATBL.jcl

SHA-256: `0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe`。型: `job`。
JOB範囲: `[1, 66]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | DELDEF | PGM=IEFBR14 | THEFILE@22 [THEFILE/0] |
| 29 | STEP05R | PROC=REPROC | PRC001.FILEIN@32 [PRC001.FILEIN/0], PRC001.FILEOUT@35 [PRC001.FILEOUT/0] |
| 43 | STEP10R | PGM=SORT | SORTIN@44 [SORTIN/0], SYMNAMES@46 [SYMNAMES/0], SYSIN@51 [SYSIN/0], SYSOUT@58 [SYSOUT/0], SORTOUT@59 [SORTOUT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 46 | 47–50 | NEXT_STATEMENT | 51 |
| 51 | 52–56 | DELIMITER | 57 |

## jcl/READACCT.jcl

SHA-256: `0965badda9c801df4f86e74755b66325764d8d1a840c615e6552b660f6401f15`。型: `job`。
JOB範囲: `[1, 50]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | PREDEL | PGM=IEFBR14 | DD01@23 [DD01/0], DD02@25 [DD02/0], DD03@27 [DD03/0] |
| 32 | STEP05 | PGM=CBACT01C | STEPLIB@33 [STEPLIB/0], ACCTFILE@35 [ACCTFILE/0], OUTFILE@37 [OUTFILE/0], ARRYFILE@41 [ARRYFILE/0], VBRCFILE@45 [VBRCFILE/0], SYSOUT@49 [SYSOUT/0], SYSPRINT@50 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/READCARD.jcl

SHA-256: `2b8ef6678d477345868671ace4b6a9990e33081d6ba6b47827aad980927132b7`。型: `job`。
JOB範囲: `[1, 31]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=CBACT02C | STEPLIB@23 [STEPLIB/0], CARDFILE@25 [CARDFILE/0], SYSOUT@27 [SYSOUT/0], SYSPRINT@28 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/READCUST.jcl

SHA-256: `3b39d6182c5483967c63616df65c56359e13a8a10c5bf08dcff9fe98566196a9`。型: `job`。
JOB範囲: `[1, 30]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | STEP05 | PGM=CBCUS01C | STEPLIB@22 [STEPLIB/0], CUSTFILE@24 [CUSTFILE/0], SYSOUT@26 [SYSOUT/0], SYSPRINT@27 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/READXREF.jcl

SHA-256: `09f076859afdd2a12bbe2e5eb1380bb986a656efe7bfb65a39377ad2c581db52`。型: `job`。
JOB範囲: `[1, 31]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=CBACT03C | STEPLIB@23 [STEPLIB/0], XREFFILE@25 [XREFFILE/0], SYSOUT@27 [SYSOUT/0], SYSPRINT@28 [SYSPRINT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## jcl/REPTFILE.jcl

SHA-256: `b78fd0ff11009e23d5dce60a79daa5d947990d3b9e7a04ccb346fcc90151dee0`。型: `job`。
JOB範囲: `[1, 32]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–28 | DELIMITER | 29 |

## jcl/TCATBALF.jcl

SHA-256: `9ff82ea5a21fd54c3ce405a14fd0851a7c17af71ed4e27a2bb2ce1860f50692b`。型: `job`。
JOB範囲: `[1, 65]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 33 | STEP10 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 54 | STEP15 | PGM=IDCAMS | SYSPRINT@55 [SYSPRINT/0], TCATBAL@56 [TCATBAL/0], TCATBALV@58 [TCATBALV/0], SYSIN@60 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–27 | DELIMITER | 28 |
| 35 | 36–49 | DELIMITER | 50 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/TRANBKP.jcl

SHA-256: `bd7a846799373121152a91b52427f3c668f390f448609d0eea534d49989acb9d`。型: `job`。
JOB範囲: `[1, 71]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 23 | STEP05R | PROC=REPROC | PRC001.FILEIN@26 [PRC001.FILEIN/0], PRC001.FILEOUT@29 [PRC001.FILEOUT/0] |
| 37 | STEP05 | PGM=IDCAMS | SYSPRINT@38 [SYSPRINT/0], SYSIN@39 [SYSIN/0] |
| 51 | STEP10 | PGM=IDCAMS | SYSPRINT@52 [SYSPRINT/0], SYSIN@53 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 39 | 40–45 | DELIMITER | 46 |
| 53 | 54–67 | DELIMITER | 68 |

## jcl/TRANCATG.jcl

SHA-256: `09ad86b3c1ac0b32cee842682baead25c1ded1572c65599591b28826261de457`。型: `job`。
JOB範囲: `[1, 65]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 33 | STEP10 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 54 | STEP15 | PGM=IDCAMS | SYSPRINT@55 [SYSPRINT/0], TRANCATG@56 [TRANCATG/0], TCATVSAM@58 [TCATVSAM/0], SYSIN@60 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–27 | DELIMITER | 28 |
| 35 | 36–49 | DELIMITER | 50 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/TRANFILE.jcl

SHA-256: `c506a68f7482a971133524ec1d8b76001f593d4e1e98477c12c80ede4e4ce2db`。型: `job`。
JOB範囲: `[1, 125]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | CLCIFIL | PGM=SDSF | ISFOUT@23 [ISFOUT/0], CMDOUT@24 [CMDOUT/0], ISFIN@25 [ISFIN/0] |
| 32 | STEP05 | PGM=IDCAMS | SYSPRINT@33 [SYSPRINT/0], SYSIN@34 [SYSIN/0] |
| 46 | STEP10 | PGM=IDCAMS | SYSPRINT@47 [SYSPRINT/0], SYSIN@48 [SYSIN/0] |
| 67 | STEP15 | PGM=IDCAMS | SYSPRINT@68 [SYSPRINT/0], TRANSACT@69 [TRANSACT/0], TRANVSAM@71 [TRANVSAM/0], SYSIN@73 [SYSIN/0] |
| 79 | STEP20 | PGM=IDCAMS | SYSPRINT@80 [SYSPRINT/0], SYSIN@81 [SYSIN/0] |
| 96 | STEP25 | PGM=IDCAMS | SYSPRINT@97 [SYSPRINT/0], SYSIN@98 [SYSIN/0] |
| 106 | STEP30 | PGM=IDCAMS | SYSPRINT@107 [SYSPRINT/0], SYSIN@108 [SYSIN/0] |
| 116 | OPCIFIL | PGM=SDSF | ISFOUT@117 [ISFOUT/0], CMDOUT@118 [CMDOUT/0], ISFIN@119 [ISFIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–27 | DELIMITER | 28 |
| 34 | 35–40 | DELIMITER | 41 |
| 48 | 49–62 | DELIMITER | 63 |
| 73 | 74–74 | DELIMITER | 75 |
| 81 | 82–91 | DELIMITER | 92 |
| 98 | 99–101 | DELIMITER | 102 |
| 108 | 109–111 | DELIMITER | 112 |
| 119 | 120–121 | DELIMITER | 122 |

## jcl/TRANIDX.jcl

SHA-256: `ad12d5f7b4b4e37b17baf23a5b1bf208ff35945182d587a909e0208d3bd45855`。型: `job`。
JOB範囲: `[1, 58]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP20 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 39 | STEP25 | PGM=IDCAMS | SYSPRINT@40 [SYSPRINT/0], SYSIN@41 [SYSIN/0] |
| 49 | STEP30 | PGM=IDCAMS | SYSPRINT@50 [SYSPRINT/0], SYSIN@51 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–34 | DELIMITER | 35 |
| 41 | 42–44 | DELIMITER | 45 |
| 51 | 52–54 | DELIMITER | 55 |

## jcl/TRANREPT.jcl

SHA-256: `081aad149f0a9c020440fb6e6da93f2a6cf6d1f77eead3cefea3702b13d79802`。型: `job`。
JOB範囲: `[1, 84]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 23 | STEP05R | PROC=REPROC | PRC001.FILEIN@26 [PRC001.FILEIN/0], PRC001.FILEOUT@29 [PRC001.FILEOUT/0] |
| 37 | STEP05R | PGM=SORT | SORTIN@38 [SORTIN/0], SYMNAMES@40 [SYMNAMES/0], SYSIN@45 [SYSIN/0], SYSOUT@50 [SYSOUT/0], SORTOUT@51 [SORTOUT/0] |
| 59 | STEP10R | PGM=CBTRN03C | STEPLIB@60 [STEPLIB/0], SYSOUT@62 [SYSOUT/0], SYSPRINT@63 [SYSPRINT/0], TRANFILE@65 [TRANFILE/0], CARDXREF@67 [CARDXREF/0], TRANTYPE@69 [TRANTYPE/0], TRANCATG@71 [TRANCATG/0], DATEPARM@73 [DATEPARM/0], TRANREPT@76 [TRANREPT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 40 | 41–44 | NEXT_STATEMENT | 45 |
| 45 | 46–48 | DELIMITER | 49 |

## jcl/TRANTYPE.jcl

SHA-256: `7993012c72041e6a9cbda9fff43549af4f8789081dc8a64b71a8a1a01f775254`。型: `job`。
JOB範囲: `[1, 65]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 33 | STEP10 | PGM=IDCAMS | SYSPRINT@34 [SYSPRINT/0], SYSIN@35 [SYSIN/0] |
| 54 | STEP15 | PGM=IDCAMS | SYSPRINT@55 [SYSPRINT/0], TRANTYPE@56 [TRANTYPE/0], TTYPVSAM@58 [TTYPVSAM/0], SYSIN@60 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–27 | DELIMITER | 28 |
| 35 | 36–49 | DELIMITER | 50 |
| 60 | 61–61 | DELIMITER | 62 |

## jcl/TXT2PDF1.JCL

SHA-256: `7b051e99abe3fdcf772d613646b39f9abf10b02e9f52422d073fa0c52908e46b`。型: `job`。
JOB範囲: `[1, 41]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 24 | TXT2PDF | PGM=IKJEFT1B | STEPLIB@28 [STEPLIB/0], SYSEXEC@31 [SYSEXEC/0], INDD@33 [INDD/0], SYSPRINT@35 [SYSPRINT/0], SYSTSPRT@36 [SYSTSPRT/0], SYSTSIN@37 [SYSTSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 37 | 38–39 | DELIMITER | 40 |

## jcl/WAITSTEP.jcl

SHA-256: `36c98a55c7701bfaa9bd6404d2aca95888880d4f908ced678840a37e2e3eac5e`。型: `job`。
JOB範囲: `[1, 27]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | WAIT | PGM=COBSWAIT | STEPLIB@23 [STEPLIB/0], SYSOUT@24 [SYSOUT/0], SYSIN@25 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 25 | 26–26 | DELIMITER | 27 |

## jcl/XREFFILE.jcl

SHA-256: `f4a24014ae9ebfdf4d36db958e1fadb76158114fa6f721e9b547d0842d556f24`。型: `job`。
JOB範囲: `[1, 106]`。PEND: `[]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 22 | STEP05 | PGM=IDCAMS | SYSPRINT@23 [SYSPRINT/0], SYSIN@24 [SYSIN/0] |
| 36 | STEP10 | PGM=IDCAMS | SYSPRINT@37 [SYSPRINT/0], SYSIN@38 [SYSIN/0] |
| 57 | STEP15 | PGM=IDCAMS | SYSPRINT@58 [SYSPRINT/0], XREFDATA@59 [XREFDATA/0], XREFVSAM@61 [XREFVSAM/0], SYSIN@63 [SYSIN/0] |
| 69 | STEP20 | PGM=IDCAMS | SYSPRINT@70 [SYSPRINT/0], SYSIN@71 [SYSIN/0] |
| 87 | STEP25 | PGM=IDCAMS | SYSPRINT@88 [SYSPRINT/0], SYSIN@89 [SYSIN/0] |
| 97 | STEP30 | PGM=IDCAMS | SYSPRINT@98 [SYSPRINT/0], SYSIN@99 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 24 | 25–30 | DELIMITER | 31 |
| 38 | 39–52 | DELIMITER | 53 |
| 63 | 64–64 | DELIMITER | 65 |
| 71 | 72–82 | DELIMITER | 83 |
| 89 | 90–92 | DELIMITER | 93 |
| 99 | 100–102 | DELIMITER | 103 |

## proc/REPROC.prc

SHA-256: `cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53`。型: `proc_member`。
JOB範囲: `PROCメンバー; JOBへ変換しない`。PEND: `[29]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | PRC001 | PGM=IDCAMS | SYSPRINT@22 [SYSPRINT/0], FILEIN@23 [FILEIN/0], FILEOUT@25 [FILEOUT/0], SYSIN@27 [SYSIN/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|

## proc/TRANREPT.prc

SHA-256: `fdbdc473dd21ba4908613c47180542ceffea8ea9a976a9413355361c6deaf103`。型: `proc_member`。
JOB範囲: `PROCメンバー; JOBへ変換しない`。PEND: `[79]`。

| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |
|---:|---|---|---|
| 21 | STEP01R | PROC=REPROC | PRC001.FILEIN@24 [PRC001.FILEIN/0], PRC001.FILEOUT@27 [PRC001.FILEOUT/0] |
| 35 | STEP05R | PGM=SORT | SORTIN@36 [SORTIN/0], SYMNAMES@38 [SYMNAMES/0], SYSIN@43 [SYSIN/0], SYSOUT@48 [SYSOUT/0], SORTOUT@49 [SORTOUT/0] |
| 57 | STEP10R | PGM=CBTRN03C | STEPLIB@58 [STEPLIB/0], SYSOUT@60 [SYSOUT/0], SYSPRINT@61 [SYSPRINT/0], TRANFILE@63 [TRANFILE/0], CARDXREF@65 [CARDXREF/0], TRANTYPE@67 [TRANTYPE/0], TRANCATG@69 [TRANCATG/0], DATEPARM@71 [DATEPARM/0], TRANREPT@74 [TRANREPT/0] |

| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |
|---:|---|---|---:|
| 38 | 39–42 | NEXT_STATEMENT | 43 |
| 43 | 44–46 | DELIMITER | 47 |


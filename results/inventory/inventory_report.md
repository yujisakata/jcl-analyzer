# JCL Profiler — Asset Inventory

- Tool version: 0.1.0 / schema 1
- Root `carddemo`: `D:/projects/aws-card/aws-mainframe-modernization-carddemo/app`
- Files seen: 240 (registered 240, excluded 0)
- Total bytes: 3866974
- Diagnostics: 26 (INFO=24, WARNING=2)

## Asset types

| Asset type | Files |
|---|---|
| ASSEMBLER | 2 |
| BMS | 21 |
| CATALOG_LISTING | 1 |
| CICS_CSD | 4 |
| COBOL | 44 |
| CONTROL_CARDS | 8 |
| COPYBOOK | 62 |
| DATA | 23 |
| DB2_DCLGEN | 3 |
| DB2_DDL | 6 |
| DOCUMENT | 3 |
| IMS_DBD | 4 |
| IMS_PSB | 4 |
| JCL | 46 |
| MACRO | 2 |
| PLACEHOLDER | 3 |
| PROC | 2 |
| SCHEDULER_CA7 | 1 |
| SCHEDULER_CONTROLM | 1 |

## Asset types by top-level directory

| Top dir | ASSEMBLER | BMS | CATALOG_LISTING | CICS_CSD | COBOL | CONTROL_CARDS | COPYBOOK | DATA | DB2_DCLGEN | DB2_DDL | DOCUMENT | IMS_DBD | IMS_PSB | JCL | MACRO | PLACEHOLDER | PROC | SCHEDULER_CA7 | SCHEDULER_CONTROLM | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| app-authorization-ims-db2-mq |  | 2 |  | 1 | 8 |  | 11 | 1 | 1 | 2 | 1 | 4 | 4 | 5 |  |  |  |  |  | 40 |
| app-transaction-type-db2 |  | 2 |  | 1 | 3 | 7 | 4 |  | 2 | 4 | 1 |  |  | 3 |  |  |  |  |  | 27 |
| app-vsam-mq |  |  |  | 1 | 2 |  |  |  |  |  | 1 |  |  |  |  |  |  |  |  | 4 |
| asm | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 2 |
| bms |  | 17 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 17 |
| catlg |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 |
| cbl |  |  |  |  | 31 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 31 |
| cpy |  |  |  |  |  |  | 30 |  |  |  |  |  |  |  |  |  |  |  |  | 30 |
| cpy-bms |  |  |  |  |  |  | 17 |  |  |  |  |  |  |  |  | 1 |  |  |  | 18 |
| csd |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  | 1 |  |  |  | 2 |
| ctl |  |  |  |  |  | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 |
| data |  |  |  |  |  |  |  | 22 |  |  |  |  |  |  |  | 1 |  |  |  | 23 |
| jcl |  |  |  |  |  |  |  |  |  |  |  |  |  | 38 |  |  |  |  |  | 38 |
| maclib |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 2 |  |  |  |  | 2 |
| proc |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 2 |  |  | 2 |
| scheduler |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | 1 | 2 |

## Encoding status

| Status | Files |
|---|---|
| ENCODING_UNDETERMINED | 23 |
| OK | 217 |

## JCL-family physical records

Record-prefix counts are physical facts, not JCL statement counts: records inside in-stream data can also begin with `//` (ADR-003). Statement-level inventory requires the Lexer/Parser (Step 4).

| Files | Records | SLASH_SLASH_STAR | SLASH_SLASH | SLASH_STAR | BLANK | OTHER | Cols 73-80 used | >80 cols |
|---|---|---|---|---|---|---|---|---|
| 48 | 3046 | 1358 | 970 | 83 | 20 | 615 | 104 | 0 |

## Duplicate member names

| Asset type | Member | Identical | Locations |
|---|---|---|---|
| CONTROL_CARDS | REPROCT | true | carddemo:app-transaction-type-db2/ctl/REPROCT.ctl<br>carddemo:ctl/REPROCT.ctl |

## Excluded files

None.

## Diagnostics by code

| Code | Severity | Count | Meaning |
|---|---|---|---|
| INV-I001 | INFO | 1 | Derived member name is not a valid PDS member name |
| INV-I004 | INFO | 23 | Encoding undetermined by configuration; file not decoded |
| INV-W003 | WARNING | 2 | Same member name appears more than once for an asset type |

## Diagnostics

| Code | Location | Message |
|---|---|---|
| INV-I004 | carddemo:app-authorization-ims-db2-mq/data/EBCDIC/AWS.M2.CARDDEMO.IMSDATA.DBPAUTP0.dat | Encoding undetermined (profile:data); not decoded |
| INV-W003 | carddemo:app-transaction-type-db2/ctl/REPROCT.ctl | CONTROL_CARDS member REPROCT also at: carddemo:ctl/REPROCT.ctl (identical content: True) |
| INV-I001 | carddemo:app-transaction-type-db2/ddl/XTRNTYCAT.ddl | Derived member name 'XTRNTYCAT' does not satisfy MVS-MEM-001 |
| INV-W003 | carddemo:ctl/REPROCT.ctl | CONTROL_CARDS member REPROCT also at: carddemo:app-transaction-type-db2/ctl/REPROCT.ctl (identical content: True) |
| INV-I004 | carddemo:data/ASCII/acctdata.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/carddata.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/cardxref.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/custdata.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/dailytran.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/discgrp.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/tcatbal.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/trancatg.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/ASCII/trantype.txt | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.ACCDATA.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.ACCTDATA.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.CARDDATA.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.CARDXREF.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.CUSTDATA.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.DALYTRAN.PS.INIT | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.DISCGRP.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.EXPORT.DATA.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.TCATBALF.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.TRANCATG.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.TRANTYPE.PS | Encoding undetermined (profile:data); not decoded |
| INV-I004 | carddemo:data/EBCDIC/AWS.M2.CARDDEMO.USRSEC.PS | Encoding undetermined (profile:data); not decoded |

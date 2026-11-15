# CD-3 列72・73–80の重点確認台帳

通常JCL・comment文・dataで列の扱いを混同しない。末尾を削除せず全rawのSHAとbyte範囲を照合済み。

| File | 行 | 役割 | 1–71列 | 72列 | 73–80列 |
|---|---:|---|---|---|---|
| app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl | 20 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl | 22 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 4 | COMMENT | `//*********************************************************************` | `*` | `        ` |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 6 | COMMENT | `//*********************************************************************` | `*` | `        ` |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 12 | COMMENT | `//*********************************************************************` | `*` | `        ` |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 14 | COMMENT | `//*********************************************************************` | `*` | `        ` |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 45 | STATEMENT | `//DFSSRT01  DD DUMMY                                                   ` | ` ` | `   //*` |
| app-authorization-ims-db2-mq/jcl/LOADPADB.JCL | 22 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/LOADPADB.JCL | 24 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL | 22 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL | 24 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 22 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 24 | COMMENT | `//*********************************************************************` | `*` | `` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 50 | CONTINUATION | `//            DCB=(LRECL=100,BLKSIZE=0,RECFM=FB),                      ` | ` ` | `00640019` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 51 | CONTINUATION | `//            UNIT=3390,SPACE=(400,(20,20),RLSE)                       ` | ` ` | `00650019` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 55 | CONTINUATION | `//            DCB=(LRECL=206,BLKSIZE=0,RECFM=FB),                      ` | ` ` | `00640019` |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 56 | CONTINUATION | `//            UNIT=3390,SPACE=(400,(20,20),RLSE)                       ` | ` ` | `00650019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 1 | STATEMENT | `//CREADB2  JOB (DB2CR),'SNJARAO',CLASS=A,MSGCLASS=A,                   ` | ` ` | `00010016` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 2 | CONTINUATION | `//         TIME=1440,NOTIFY=&SYSUID,TYPRUN=SCAN                        ` | ` ` | `00020021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 3 | COMMENT | `//******************************************************************   ` | ` ` | `00021025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 4 | COMMENT | `//* Copyright Amazon.com, Inc. or its affiliates.                      ` | ` ` | `00022025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 5 | COMMENT | `//* All Rights Reserved.                                               ` | ` ` | `00023025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 6 | COMMENT | `//*                                                                    ` | ` ` | `00024025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 7 | COMMENT | `//* Licensed under the Apache License, Version 2.0 (the "License").    ` | ` ` | `00025025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 8 | COMMENT | `//* You may not use this file except in compliance with the License.   ` | ` ` | `00026025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 9 | COMMENT | `//* You may obtain a copy of the License at                            ` | ` ` | `00027025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 10 | COMMENT | `//*                                                                    ` | ` ` | `00028025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 11 | COMMENT | `//*    http://www.apache.org/licenses/LICENSE-2.0                      ` | ` ` | `00029025` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 12 | COMMENT | `//*                                                                    ` | ` ` | `00029125` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 13 | COMMENT | `//* Unless required by applicable law or agreed to in writing,         ` | ` ` | `00029225` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 14 | COMMENT | `//* software distributed under the License is distributed on an        ` | ` ` | `00029325` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 15 | COMMENT | `//* "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,       ` | ` ` | `00029425` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 16 | COMMENT | `//* either express or implied. See the License for the specific        ` | ` ` | `00029525` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 17 | COMMENT | `//* language governing permissions and limitations under the License   ` | ` ` | `00029625` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 18 | COMMENT | `//*********************************************************************` | ` ` | `00031002` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 19 | COMMENT | `//****  Create CARDDEMO Database in DAZ1 subsystem (SSID=DAZ1)   ******` | ` ` | `00040021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 20 | COMMENT | `//*********************************************************************` | ` ` | `00040119` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 21 | COMMENT | `//****  You can run the SQLs linked here through SPUFI           ******` | ` ` | `00041019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 22 | COMMENT | `//****  If you prefer JCL, you can run them from this job        ******` | ` ` | `00041220` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 23 | COMMENT | `//****  You may need to bind the utilities used first though     ******` | ` ` | `00041320` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 24 | COMMENT | `//****  See AWS.M2.CARDDEMO.JCL.UTIL(BINDTIAD) to see how        ******` | ` ` | `00042017` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 25 | COMMENT | `//*********************************************************************` | ` ` | `00050002` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 26 | COMMENT | `//*  SET PARMS FOR THIS JOB:                                           ` | ` ` | `00070021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 27 | COMMENT | `//*********************************************************************` | ` ` | `00071021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 28 | STATEMENT | `//   SET CODER=AWS                                                     ` | ` ` | `00072022` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 29 | STATEMENT | `//   SET LBNM=&CODER..M2.CARDDEMO                                      ` | ` ` | `00072122` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 30 | STATEMENT | `//   SET DB2S=DAZ1                                                     ` | ` ` | `00073021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 31 | COMMENT | `//*********************************************************************` | ` ` | `00075021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 32 | STATEMENT | `//JOBLIB  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                     ` | ` ` | `00080021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 33 | STATEMENT | `//  DD  DSN=OEM.DB2.&DB2S..SDSNLOAD,DISP=SHR                           ` | ` ` | `00090021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 34 | STATEMENT | `//  DD  DSN=CEE.SCEERUN,DISP=SHR                                       ` | ` ` | `00100004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 35 | COMMENT | `//*********************************************************************` | ` ` | `00100123` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 36 | COMMENT | `//****  STEP 00 : Free existing plans and packages               ******` | ` ` | `00100223` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 37 | COMMENT | `//****          : It ends with RC 8 if not existing.             ******` | ` ` | `00100324` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 38 | COMMENT | `//****          : So dont run it if creating new database        ******` | ` ` | `00100424` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 39 | COMMENT | `//*********************************************************************` | ` ` | `00100524` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 40 | STATEMENT | `//FREEPLN EXEC PGM=IKJEFT01,DYNAMNBR=20                                ` | ` ` | `00102023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 41 | STATEMENT | `//STEPLIB  DD DISP=SHR,DSN=OEM.DB2.DAZ1.SDSNEXIT                       ` | ` ` | `00103023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 42 | STATEMENT | `//         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                  ` | ` ` | `00104023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 43 | STATEMENT | `//SYSPRINT DD SYSOUT=*                                                 ` | ` ` | `00105023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 44 | STATEMENT | `//SYSTSPRT DD SYSOUT=*                                                 ` | ` ` | `00106023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 45 | STATEMENT | `//SYSUDUMP DD SYSOUT=*                                                 ` | ` ` | `00107023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 46 | STATEMENT | `//SYSTSIN  DD DISP=SHR,DSN=&LBNM..CNTL(DB2FREE)                        ` | ` ` | `00108023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 47 | COMMENT | `//*********************************************************************` | ` ` | `00110004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 48 | COMMENT | `//****  STEP 10 : Use Utility DSNTIAD to create the database     ******` | ` ` | `00120019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 49 | COMMENT | `//****            This uses an existing STOGROUP AWST1STG        ******` | ` ` | `00121018` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 50 | COMMENT | `//****            You would have to create it if not available   ******` | ` ` | `00122023` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 51 | COMMENT | `//*********************************************************************` | ` ` | `00130004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 52 | STATEMENT | `//CRCRDDB  EXEC PGM=IKJEFT01,DYNAMNBR=20                               ` | ` ` | `00140004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 53 | STATEMENT | `//STEPLIB  DD DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                  ` | ` ` | `00150021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 54 | STATEMENT | `//         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                  ` | ` ` | `00160019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 55 | STATEMENT | `//SYSTSPRT DD SYSOUT=*                                                 ` | ` ` | `00170004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 56 | STATEMENT | `//SYSUDUMP DD SYSOUT=*                                                 ` | ` ` | `00180004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 57 | STATEMENT | `//SYSPRINT DD SYSOUT=*                                                 ` | ` ` | `00190004` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 58 | STATEMENT | `//SYSTSIN  DD DISP=SHR,DSN=&LBNM..CNTL(DB2TIAD1)                       ` | ` ` | `00200021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 59 | STATEMENT | `//SYSIN    DD DISP=SHR,DSN=&LBNM..CNTL(DB2CREAT)                       ` | ` ` | `00250021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 60 | COMMENT | `//*********************************************************************` | ` ` | `00470011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 61 | COMMENT | `//****  STEP 20 : Load the transaction Type table                ******` | ` ` | `00480019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 62 | COMMENT | `//****            using DSNTEP4 utility                          ******` | ` ` | `00481019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 63 | COMMENT | `//*********************************************************************` | ` ` | `00490011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 64 | STATEMENT | `//LDTTYPE  EXEC PGM=IEFBR14,COND=(0,NE)                                ` | ` ` | `00500019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 65 | STATEMENT | `//RUNTEP2  EXEC PGM=IKJEFT01,DYNAMNBR=20                               ` | ` ` | `00510011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 66 | STATEMENT | `//STEPLIB  DD DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                  ` | ` ` | `00520021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 67 | STATEMENT | `//         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                  ` | ` ` | `00530019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 68 | STATEMENT | `//SYSTSPRT DD SYSOUT=*                                                 ` | ` ` | `00540011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 69 | STATEMENT | `//SYSUDUMP DD SYSOUT=*                                                 ` | ` ` | `00550011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 70 | STATEMENT | `//SYSPRINT DD SYSOUT=*                                                 ` | ` ` | `00560011` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 71 | STATEMENT | `//SYSTSIN  DD DISP=SHR,DSN=&LBNM..CNTL(DB2TEP41)                       ` | ` ` | `00570021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 72 | STATEMENT | `//SYSIN    DD DISP=SHR,DSN=&LBNM..CNTL(DB2LTTYP)                       ` | ` ` | `00630021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 73 | COMMENT | `//*********************************************************************` | ` ` | `00750015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 74 | COMMENT | `//****  STEP 30 : Load Transaction Type Category table           ******` | ` ` | `00760019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 75 | COMMENT | `//****            using DSNTEP4 utility                          ******` | ` ` | `00761019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 76 | COMMENT | `//*********************************************************************` | ` ` | `00770015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 77 | STATEMENT | `//LDTCCAT  EXEC PGM=IKJEFT01,DYNAMNBR=20,COND=(0,NE)                   ` | ` ` | `00790019` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 78 | STATEMENT | `//STEPLIB  DD  DISP=SHR,DSN=OEM.DB2.&DB2S..RUNLIB.LOAD                 ` | ` ` | `00800021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 79 | STATEMENT | `//         DD  DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD                 ` | ` ` | `00810015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 80 | STATEMENT | `//SYSTSPRT DD SYSOUT=*                                                 ` | ` ` | `00820015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 81 | STATEMENT | `//SYSUDUMP DD SYSOUT=*                                                 ` | ` ` | `00830015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 82 | STATEMENT | `//SYSPRINT DD SYSOUT=*                                                 ` | ` ` | `00840015` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 83 | STATEMENT | `//SYSTSIN  DD DISP=SHR,DSN=&LBNM..CNTL(DB2TEP41)                       ` | ` ` | `00850021` |
| app-transaction-type-db2/jcl/CREADB21.jcl | 84 | STATEMENT | `//SYSIN    DD DISP=SHR,DSN=&LBNM..CNTL(DB2LTCAT)                       ` | ` ` | `00910021` |
| app-transaction-type-db2/jcl/MNTTRDB2.jcl | 1 | STATEMENT | `//MNTTRDB2 JOB (COBOL),'MNTTRDB2',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),   ` | ` ` | `JOB09214` |
| jcl/DEFGDGD.jcl | 1 | STATEMENT | `//DEFGDGD JOB 'DEF DB2 GDG',CLASS=A,MSGCLASS=0,NOTIFY=&SYSUID          ` | ` ` | `JOB05067` |
| jcl/DEFGDGD.jcl | 2 | COMMENT | `//*  RESTART=STEP30                                                    ` | ` ` | `JOB05067` |
| jcl/FTPJCL.JCL | 1 | STATEMENT | `//FTPJCLS  JOB 'FTP JCL',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),            ` | ` ` | `JOB01598` |
| jcl/FTPJCL.JCL | 23 | COMMENT | `//* MY.FTP.SERVER.COM IS THE FTP SERVER NAME(SUBJECT TO CHANGE FOR SITE` | `)` | `` |
| jcl/PRTCATBL.jcl | 26 | COMMENT | `//* ********************************************************`**********` | `*` | `        ` |
| jcl/READACCT.jcl | 1 | STATEMENT | `//READACCT JOB 'READACCT',REGION=8M,CLASS=A,                           ` | ` ` | `JOB05427` |
| jcl/TRANREPT.jcl | 20 | COMMENT | `//* ********************************************************`**********` | `*` | `        ` |
| jcl/TRANREPT.jcl | 43 | DATA | `PARM-START-DATE,C'2022-01-01'                                      //Da` | `t` | `e       ` |
| jcl/TRANREPT.jcl | 44 | DATA | `PARM-END-DATE,C'2022-07-06'                                        //Da` | `t` | `e       ` |
| jcl/TXT2PDF1.JCL | 20 | COMMENT | `//* ********************************************************`**********` | `*` | `` |
| jcl/WAITSTEP.jcl | 22 | STATEMENT | `//WAIT     EXEC PGM=COBSWAIT                                           ` | ` ` | `00040001` |
| jcl/WAITSTEP.jcl | 23 | STATEMENT | `//STEPLIB  DD DSN=AWS.M2.CARDDEMO.LOADLIB,DISP=SHR                     ` | ` ` | `00050000` |
| jcl/WAITSTEP.jcl | 24 | STATEMENT | `//SYSOUT DD SYSOUT=*                                                   ` | ` ` | `00060000` |
| jcl/WAITSTEP.jcl | 25 | STATEMENT | `//SYSIN    DD *                                                        ` | ` ` | `00070000` |
| jcl/WAITSTEP.jcl | 26 | DATA | `00003600      VALUE IN CENTISECONDS                                    ` | ` ` | `00080000` |
| jcl/WAITSTEP.jcl | 27 | DELIMITER | `/*                                                                     ` | ` ` | `00080000` |
| proc/TRANREPT.prc | 41 | DATA | `PARM-START-DATE,C'2022-01-01'                                      //Da` | `t` | `e       ` |
| proc/TRANREPT.prc | 42 | DATA | `PARM-END-DATE,C'2022-07-06'                                        //Da` | `t` | `e       ` |

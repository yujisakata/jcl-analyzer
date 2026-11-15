# CardDemo専用 解析・受入契約

作成日: 2026-11-15（JST）。調査担当: Codex（実装から独立した検証）。

**目的はAWS CardDemo全資産から、COBOL→Java移行に必要なBatch IRの最小機能集合を決めることである。汎用JCL Parserの完成や、監査11件の一括修正を今回の前提にしない。** 本書は原本調査の結果と次回開発の受入仕様案であり、実装着手・完了承認ではない。現行Parser開発と11件の修正は停止したままとする。

対象原本: `D:\projects\aws-card\aws-mainframe-modernization-carddemo\app`。46個のJOBファイルと2個のPROCメンバー、計48ファイルを再帰走査した。対象はファイル名の大小文字を含めて固定する。本調査の操作では既存Parser、Harness、Golden定義・期待値、設定、原本を変更していない。ただし最終保全検査で別の書込みによる同時変更を検出した。詳細は直後の注意事項とQ11を参照する。

**同時変更に関する注意**: 調査開始時に保存した526ファイルのハッシュと比べ、Harness/Parser Adapter/スキーマの既存6ファイル変更と、本契約書以外の14ファイル追加を検出した。変更元は未確認。本調査のツール操作による変更ではないため、取り消し・上書き・追加実装はしていない。原本240資産と既存tests/goldenは全件一致した。原本からのインベントリと独立階層の根拠は維持されるが、先行監査A11や既存Harnessの状態は、この同時変更後の版について再判定していない。調査範囲外の実装が解決済みであるとも、未修正であるとも断定しない。

## 1. CardDemoの構文・機能インベントリ

### 1.1 根拠と再現方法

調査証拠は [results/carddemo-contract-20261115](../../results/carddemo-contract-20261115/) に保存した。

| 証拠 | 内容 |
|---|---|
| [inventory.json](../../results/carddemo-contract-20261115/inventory.json) | 全48ファイルのSHA-256、681論理文、各値の出現位置、全STEP/DD階層、全レコード役割、データ境界 |
| [operands.tsv](../../results/carddemo-contract-20261115/operands.tsv) | 全オペランド出現を、文種別・原値・相対パス・論理文先頭行で索引化。DSN全101種類を含む |
| [source-numbered.txt](../../results/carddemo-contract-20261115/source-numbered.txt) | 全原本の行番号付き読取スナップショット。データ内の値はローカル証拠としてのみ扱う |
| [inspect_corpus.py](../../results/carddemo-contract-20261115/inspect_corpus.py) | jclprofをimportしない、観測構文に限定した独立簡易走査。引用符・括弧・継続・DD *の境界を検査し、不明状態はassertで停止 |
| [comparison.json](../../results/carddemo-contract-20261115/comparison.json) | 別方式の物理行正規表現集計、独立走査、現行Parserの照合結果 |
| [compare_inventory.py](../../results/carddemo-contract-20261115/compare_inventory.py) | 独立参照データを期待側に置く読取専用の照合。参照データをParser出力で更新しない |
| [control-assets.json](../../results/carddemo-contract-20261115/control-assets.json) | 別途確認した外部入力候補8 CTLのパス・ハッシュ・レコード数 |
| [preservation.json](../../results/carddemo-contract-20261115/preservation.json) | 調査前後の保全確認 |

再現: プロジェクトルートで `.venv/Scripts/python.exe results/carddemo-contract-20261115/inspect_corpus.py`。これは調査用の索引を再計測するだけで、tests/goldenや既存期待値を更新しない。今回の証拠ファイルを将来のテスト失敗に合わせて再生成して正解としない。

独立性: まず原本だけから走査・集計・階層を作り、その後に現行Parserの出力を比較した。別の単純な文頭正規表現でも文種別件数を照合した。原本のPROC・DD修飾・連結・COND・全データ境界・例外的記述を精査した。現行Parserとの文頭・パラメーター原表記・継続行所属・STEP/DD所属・連結index・データ境界の差分は0件だったが、これは値の全意味や展開後の正しさの保証ではない。Job.spanは1件不一致。照合は `.venv/Scripts/python.exe results/carddemo-contract-20261115/compare_inventory.py` で再現できる。参考用プログラムによる別実装のため、人によるGolden承認は引き続き必要である。

### 1.2 確定した規模と文種別

| 項目 | 実測 | 集計上の意味 |
|---|---:|---|
| JOBファイル | 46 | `.jcl` 38、`.JCL` 8。各1 JOB |
| PROCメンバー | 2 | `.prc` 2。JOBではない |
| 物理レコード | 3,046 | 短い行・データ行・末尾コメントを含む |
| 論理文 | 681 | 下記7種類の合計。コメント・null・区切りを除く |
| JOB | 46 | JOB名はファイル名と異なる例もある |
| EXEC | 123 | JOB本体119、PROC本体4。PGM=119、PROC=4（全てREPROC） |
| DD | 500 | JOBファイル480、PROCメンバー20。展開前の原本文数 |
| SET | 5 | CODER、DB2S、LBNM各1、HLQ 2 |
| JCLLIB | 3 | 全てORDER=('AWS.M2.CARDDEMO.PROC') |
| PROC / PEND | 各2 | メンバー先頭のPROCと対応PEND |
| JCL INCLUDE、IF/ELSE/ENDIF | 各0 | データ内のDFSORT INCLUDEとは区別 |
| コメント文 | 1,358 | // *ではなく、列1〜3が`//*` |
| 継続レコード | 282 | 全てカンマによるパラメーター継続 |
| データレコード | 635 | 原文を切り詰めず保持する |
| 明示区切り | 83 | 全て`/*` |
| nullレコード | 7 | 6ファイル。DEFGDGDには連続2個 |

物理役割の検算: `681 + 282 + 1358 + 635 + 83 + 7 = 3046`。未分類レコード0。STEP/DDの値を名前で辞書化せず、ファイル・行・出現順で識別する。

### 1.3 オペランドとパラメーター値

下表の件数は指定回数。値の大小文字、引用符、NULL要素、符号を原表記のまま数えた。DSN・JOB位置値・全DCB等の完全な値集合と全出典はoperands.tsvを正とする。たとえばSYSADをSYSDAへ、SYUIDをSYSUIDへ自動補正しない。

| 文 | 必須収集対象 | 実測値・回数 |
|---|---|---|
| JOB | 位置値 | 会計情報・プログラマー名等52位置要素（空位置を含む）、46種類の原値。単一引用文字列と括弧リストあり |
| JOB | CLASS | A:46 |
| JOB | MSGCLASS | 0:30、H:13、X:2、A:1 |
| JOB | MSGLEVEL | (1,1):10 |
| JOB | NOTIFY | &SYSUID:45、&SYUID:1 |
| JOB | REGION | 0M:5、0K:1、8M:3、5M:2 |
| JOB | TIME / TYPRUN | 1440:8、30:1 / SCAN:1 |
| EXEC | PGM / PROC | 119回・21種類 / REPROC:4 |
| EXEC | PARM | 8回・8種類。引用文字列、リスト、`('')`を区別。下記参照 |
| EXEC | COND | (0,NE):13、(4,LT):2。全てEXEC上、STEP修飾なし |
| EXEC | REGION / DYNAMNBR | 4M:1、0M:2、2048K:1 / 20:4、200:2、50:1 |
| EXEC | CNTLLIB | AWS.M2.CARDDEMO.CNTL:4。PROC呼出しシンボル引数 |
| DD | DSN / DISP | 各225指定。DSN 101種類、DISP 9種類 |
| DD | 位置値 | *:91、DUMMY:20。他0 |
| DD | SYSOUT | *:163、(A,INTRDR):1 |
| DD | UNIT | SYSDA:27、3390:2、SYSAD:5 |
| DD | SPACE | 42指定・12種類。単一数値/入れ子/空位置/RLSE/ROUNDあり |
| DD | DCB | 37指定・27種類。キーワード形式34、`(*.SORTIN)`3 |
| DD | SYMBOLS | JCLONLY:1 |
| JCLLIB | ORDER | ('AWS.M2.CARDDEMO.PROC'):3 |
| SET | CODER / DB2S / LBNM / HLQ | AWS / DAZ1 / &CODER..M2.CARDDEMO / AWS.M2.CARDDEMO（HLQのみ2回） |

PARM全8値:

```text
'BMP,CBPAUP0C,PSBPAUTB'
(ULU,DFSURGU0,DBPAUTP0)
'BMP,PAUDBLOD,PSBPAUTB'
'DLI,DBUNLDGS,DLIGSAMP,,,,,,,,,,,N'
'DLI,PAUDBUNL,PAUTBUNL,,,,,,,,,,,N'
'CSD(READWRITE),PAGESIZE(60),NOCOMPAT'
'2022071800'
('')
```

DISP全9値:

```text
SHR:171                 (MOD,DELETE):2
(,CATLG,DELETE):1        (OLD,KEEP,KEEP):2
(OLD,DELETE,DELETE):2    (NEW,CATLG,DELETE):29
(NEW,CATLG):5            (MOD,DELETE,DELETE):9
OLD:4
```

SPACE全12値:

```text
(TRK,0):1                         (32274,(600,100),RLSE):1
(605,(500,500),RLSE,,ROUND):1       (400,(20,20),RLSE):2
(TRK,(1,1),RLSE):8                 (TRK,(1,1)):2
(TRK,(50,25),RLSE):2               (TRK,(25,10),RLSE):1
(TRK,(100,50),RLSE):1              (TRK,(10,5),RLSE):3
(CYL,(1,1),RLSE):17                (CYL,(1,2),RLSE):3
```

DCBの必須部分はLRECL（34指定）、RECFM（33）、BLKSIZE（33）、DSORG（5）と同一STEP内のSORTINへの後方参照（3）。実在RECFMはF/FB/VB/FBA、DSORGはPS。0のBLKSIZEを既知の実ブロック長へ捏造しない。DSNにVSAM/KSDS/PATHの文字が含まれても、文字列だけで実資源種別を確定しない。

PGM全21種類と回数（PROC本体を含む、展開前）:

```text
IDCAMS:62  IEFBR14:9  IEBGENER:8  IKJEFT01:7  SDSF:8
DFSRRC00:5 SORT:5     CBTRN03C:2
DFHCSDUP:1 CBEXPORT:1 CBIMPORT:1 CBSTM03A:1 FTP:1
CBACT04C:1 CBTRN02C:1 CBACT01C:1 CBACT02C:1 CBCUS01C:1
CBACT03C:1 IKJEFT1B:1 COBSWAIT:1
```

### 1.4 継続・DD連結・インラインデータ・特殊形式

| 項目 | 原本に基づく確定値と必要性 |
|---|---|
| 継続 | パラメーター継続282。開始列は4:25、5:8、6:1、9:3、10:15、11:23、12:143、13:1、14:2、15:45、16:16。引用文字列を71列から16列へ分割する継続0、コメント欄72列継続0、継続直後のnull 0 |
| 桁規則 | TAB 0、80文字超0。72列非空白20行は全てコメント16/データ4であり、継続標識と誤認しない。73〜80列非空白104行は文頭48/継続5/コメント45/データ5/区切り1。特にデータをJCLと同じ規則で末尾切捨てしない |
| DD連結 | 名前なしDD24（JOBLIB 2、STEP内22）、連結先のある19グループ。STEPLIB、IMS、JOBLIB、SORTINが先頭。順序・重複DSNを保存 |
| JOBレベルDD | CREADB21.jcl:32〜34のJOBLIBグループ3文だけ。JCLLIB文のラベルJOBLIB（別3件）をDDと数えない |
| DD * | 91データ領域。83は/*、7は次の//文/コメント、1はEOFで終了。635データ行。暗黙SYSIN 0 |
| 次の//で終わる7領域 | CBPAUP0J:36→38、DBPAUTP0:34→36、COMBTRAN:27→29、FTPJCL:32→42、PRTCATBL:46→51、TRANREPT.jcl:40→45、proc/TRANREPT:38→43 |
| EOFで終わる1領域 | app-transaction-type-db2/jcl/MNTTRDB2.jcl:28のSYSTSIN。データ29〜30行。現行Job.span=[1,28]は不適合 |
| DD DATA / DLM | 位置値DATA 0、DLM指定0、独自区切り0。関連する一般化修正は延期可能 |
| GDG | DSN内の相対世代24指定（+1:22、0:2）。絶対世代番号への解決は環境・実行時依存として分離 |
| メンバー参照 | DSN内13指定・9メンバー名。DFSVSMDB:4、DB2TEP41:2、DB2FREE/DB2TIAD1/DB2CREAT/DB2LTTYP/DB2LTCAT/INTRDRJ2/REPROCT:各1 |
| DD修飾名 | PRC001.FILEIN/FILEOUTの計8指定。3 JOBとproc/TRANREPTの各2。単なるDD名へ潰さない |
| 後方参照 | DCB=(*.SORTIN) 3。COMBTRAN:35、TRANREPT.jcl:53、proc/TRANREPT:51。対象はそれぞれ同じSORT STEPのSORTIN |
| 内部リーダー | INTRDRJ1.JCL:17〜18。SYSUT1のJCL(INTRDRJ2)をSYSOUT=(A,INTRDR)へコピー。通常レポート出力と区別 |
| データのシンボル | CBADMCDJ:33のDD *,SYMBOLS=JCLONLY。45行のDSNAME01(&HLQ..LOADLIB)。SETと実行時シンボル公開を同一視しない（§4.3） |
| 非出現 | IF/ELSE/ENDIF、JCL INCLUDE、EXPORT、JES2/JES3制御文、JOB COND、COND EVEN/ONLY・複数テスト・STEP修飾、裸PROC呼出し、PGM後方参照、DD PATH/DDNAME、一時DSN && は0 |

DD *の/*・//・EOFによる終了と、PROC内のDD *は現行IBMの定義に従う。古い「PROCにインラインデータを置けない」という資料を適用しない。[IBM JCL Reference、DD * / Location（3.1公式本文）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)。既存ルールJCL-DD-003/006、JCL-REC-002/003、JCL-CONT-001も参照する。

### 1.5 条件制御・参照・原本固有の注意点

CONDの全出現: CREADB21:64,77、TRANEXTR:42,53,65,95、CREASTMT:56,66,79、DEFGDGD:36,47,59,82、TRANBKP:51、TXT2PDF1:24。95と51の2件のみ(4,LT)、他は(0,NE)。**CONDは条件成立時にスキップする。** 比較の左辺は定数であり、(4,LT)は過去にRC>4のSTEPがあればスキップする。STEP指定なしなので直前STEPだけの判定へ縮めない。ABENDによる通常の後続抑止と、CONDによるスキップを別に保つ。[IBM return-code制御](https://www.ibm.com/docs/en/zos/3.2.0?topic=execution-bypassing-executing-steps-based-return-codes)、[IBM COND例](https://www.ibm.com/docs/en/zos/3.2.0?topic=parameter-examples-cond)。

PROC呼出しは4件で全て明示PROC=REPROC:

| 呼出し元 | 呼出し行 | DDオーバーライド行 | 置換先の原本候補 |
|---|---:|---|---|
| jcl/PRTCATBL.jcl STEP05R | 29 | 32 FILEIN、35 FILEOUT | proc/REPROC.prc PRC001:21 |
| jcl/TRANBKP.jcl STEP05R | 23 | 26 FILEIN、29 FILEOUT | 同上 |
| jcl/TRANREPT.jcl STEP05R（最初の出現） | 23 | 26 FILEIN、29 FILEOUT | 同上 |
| proc/TRANREPT.prc STEP01R | 21 | 24 FILEIN、27 FILEOUT | 同上。PROC内の呼出しも必要 |

各呼出しはCNTLLIB=AWS.M2.CARDDEMO.CNTLを渡す。REPROC.prcはPRC001がIDCAMSを呼び、SYSPRINT・FILEIN・FILEOUT・SYSINの4 DDを持つ。FILEIN/OUTのDSN=NULLFILEを呼出し側が上書きし、SYSINの&CNTLLIB(REPROCT)を参照する。現行configはdatasets=[]であり、表の「候補」は解決済みを意味しない。[IBM手続きDDの上書き](https://www.ibm.com/docs/en/zos/3.1.0?topic=procedures-overriding-adding-dd-statements)。

`proc/TRANREPT.prc:1`のPROCラベルはREPROCだが、メンバー名はTRANREPTである。REPROCというラベルに基づいて2つのメンバーを統合してはならない。TRANREPTメンバーを呼ぶEXECは0件だが、2 PROCの一つとして解析・参照検査から除外しない。[IBMの手続き名はメンバー名/別名](https://www.ibm.com/docs/SSLTBW_3.2.0/pdf/ieab500_v3r2.pdf)、既存ADR-011。

原本固有事項:

- DEFCUST.jclのSTEP05:22,32、TRANREPT.jclのSTEP05R:23,37は同名STEP。双方を保持し、名前だけでキー化しない。今回のCONDにはSTEP名参照がない。重複を自動改名したり、独立根拠なしで構文ERRORにしたりしない。
- ファイルCREADB21.jclのJOB名はCREADB2、FTPJCL.JCLはFTPJCLS。識別子をファイル名から作り替えない。
- READCUST.jcl:1のNOTIFY=&SYUIDは未定義候補。SYSUIDへ修正しない。
- UNIT=SYSADはDUSRSECJ:46、ESDSRRDS:47、READACCT:37,41,45の5指定。サイト固有装置名か誤記かは未確定。SYSDAと仮定しない。
- CREASTMT.JCL:90のSPACE指定後の`00,RECFM=FB), ATA.VSAM.KSDS`は空白後のコメント欄。91行のDSN継続と区別し、コメントを新しいパラメーターとして取り込まない。
- CREADB21のTYPRUN=SCANを保持する。観測された機能と「実際に実行される機能」を同一視しない。原本の全48資産を対象にするため、このJOB自体は除外しない。

### 1.6 Batch IRへ結び付ける必要機能

以下は実資産に根拠がある候補集合であり、Java Runtimeの採用設計を確定するものではない。

| 必要機能候補 | 実資産の証拠 | 最小限の解析出力 |
|---|---|---|
| 順次プログラム実行・引数渡し | 全119 JOB内STEP、8 PARM | PGM/PROC/ラッパーと原引数、順序、設定元 |
| 論理DDバインド・連結 | 500 DD、24名前なし | DD名/スコープ/順序/連結先、DSN・メンバー・DUMMY |
| 割当・終了時処分・世代 | DISP225、SPACE42、GDG24 | 指定値と既定値の区別、正常/異常、MOD・GDGの実行時依存 |
| レコード属性・後方参照 | DCB37、3 SORTIN参照 | LRECL/RECFM/BLKSIZE/DSORG・参照元 |
| インライン入力・シンボル文脈 | 91領域、SYMBOLS=JCLONLY | 生データ、境界、読込時の置換要求と未解決値 |
| 条件付き実行 | COND15 | スキップ条件AST、RC/ABEND依存、確定しない実行経路 |
| 手続き展開と上書き | REPROC呼出し4 | 呼出し・定義・DD上書きの複数出典 |
| 出力ルーティング・ジョブ投入 | SYSOUT164、INTRDR1 | 通常SYSOUTと内部リーダーを区別した依存辺 |
| 資源の作成/削除/コピー | IDCAMS、IEFBR14、IEBGENER | DDの指定と制御カードの操作を混同しない機能注釈 |
| ソート・抽出・整形 | SORT5、SYMNAMES、INCLUDE/OUTREC | 実行資産単位のソート/フィルター/整形機能とデータ出典 |
| DB2・IMS・CICS・外部処理 | IKJEFT01/1B、DFSRRC00、SDSF、DFHCSDUP、FTP | サブシステム、呼出し先・制御入力、必要な外部Runtime能力 |

JCL以外の制御カードも最小IRを決める証拠である。91領域の所属内訳はIDCAMS61、SORT9、SDSF8、IKJEFT01 5、DFSRRC00 2、IEBGENER2、DFHCSDUP/FTP/IKJEFT1B/COBSWAIT各1。ここでSORT9は9 STEPではなく、5 STEPに属する9データ領域。

IDCAMSのDELETE/DEFINE/REPRO/SET MAXCC、DFSORTのSORT/INCLUDE/OUTREC、DB2のDSN/RUN PROGRAM/SQL、SDSF経由のCEMT、CSD定義、FTP操作、%TXT2PDFを、JCL文として数えない。汎用の各制御言語Parserを作る代わりに、原カードに紐づくレビュー済み機能注釈で必要能力を列挙できる。ただし「原文を保持した」だけで機能分類済みとはしない。IMSはPGM=DFSRRC00だけではCOBOL対象が分からず、PARM内のCBPAUP0C、PAUDBLOD、DBUNLDGS、PAUDBUNL等を別の実行対象参照として扱う。DSN RUN PROGRAM(COBTUPDT)も同様。Javaクラス名は推測しない。

外部入力候補としてローカル8 .ctlファイル（DB2系7、app/ctlのREPROCT 1）も内容を確認した。REPROCT.ctlは2か所に存在し、バイト列SHA-256が同一（3ceeb621…fc49b7）でも自動的にライブラリー対応を決めない。CTL内SQL/ユーティリティ操作の意味注釈は、JCL INCLUDE展開とは別の作業である。

## 2. 必要なParser機能

| 契約ID | 必須機能 | 対応範囲を絞る方法 |
|---|---|---|
| CP-01 | JOB/EXEC/DD/SET/JCLLIB/PROC/PENDと特殊レコードを区別 | §1の実出現7文種と役割。ラベル名で文種を決めない |
| CP-02 | カンマ・括弧・引用符・省略位置・継続・コメントを保持 | 観測値全件。空文字`''`、NULL、空リストを混同しない |
| CP-03 | JOB/STEP/DD、JOBLIB、PROC本体の階層 | 生のsource ASTは119+4 STEP、480+20 DD。qualified DDは上書き候補として保持 |
| CP-04 | DD連結とインライン境界 | 全24連結、91領域、末尾EOFを独立照合 |
| CP-05 | DSN・DISP・DCB・SPACE・UNIT・SYSOUT・DUMMY | §1の値を型付き構造へ。GDG/メンバー/NULLFILE/後方参照を識別 |
| CP-06 | シンボル・PROC・DD上書きの解決を別層で行う | REPROC、CNTLLIB、SETされた4種類、SYSUID/SYUID、SYMBOLS。原ASTを書換えない |
| CP-07 | CONDを実行条件モデルへ変換 | 現物2形式とRC/ABEND伝播。IFや全COND構文へ拡張しない |
| CP-08 | INTRDRと制御入力・サブシステムの依存を保存 | 1内部リーダーと実在ラッパー。実際の投入・接続は行わない |
| CP-09 | 未対応・未解決を成功した解析と区別 | 元の全レコードと原因・位置・影響する機能を出す |
| CP-10 | 完全なトレーサビリティ | §4.5。Job.spanも子データを包含 |

これらを全てParserモジュールへ詰め込む必要はない。CP-06はResolver、CP-07〜08と機能注釈は意味層の責務である。受入単位はCardDemoの静的解析パイプラインとし、Parserだけで全要件を満たしたように表示しない。

## 3. 11件の欠陥の優先順位と根拠

監査IDは[先行監査レポート](../../results/audit-20261115/report.md)のA01〜A11を保持する。分類は「発現」「可能性」「対象外」の3つ。一般入力での重大度と、今回の修正優先順位を分ける。P0=受入を信頼する前提、P1=実資産の正確性に必須、P2=現境界の維持確認のみ、延期=今回修正しない。

| ID・内容 | CardDemo分類 | 優先順位 | 原本に基づく根拠と今回の扱い |
|---|---|---|---|
| A01 null後の所属（D-1） | 可能性 | P2 | null7行はCARDFILE:125、CBADMCDJ:164、DEFGDGD:90,91、DUSRSECJ:89、ESDSRRDS:122、TRANREPT:81。以後に有効JOB/EXEC/DD/データは0、コメントと追加nullのみ。JOB/STEP/DD構造は分岐しない。尾部原文を保持し、JES別のコメント処理未確定は注記で許容。汎用NULLJCL解釈層は作らない |
| A02 UNKNOWN DLM候補消失（D-2） | 対象外 | 延期 | DLM指定0。4条件を要する発火入力は0。新規DLM検出時は対象拡大として止める |
| A03 継続null（D-3） | 対象外 | 延期 | 継続282行とnull7行は存在するが、継続待ち直後のnullという組合せ0。独立走査で不在を検査。一般のnullや継続対応を不要にはしない |
| A04 DLMの&&復元 | 対象外 | 延期 | DLM 0、DLM内&& 0。通常シンボルを扱う必要性とは別 |
| A05 DLM区切りコメントからの偽継続 | 対象外 | 延期 | 独自区切り0。区切りは/*83。独自`//`区切りを実装しない |
| A06 DLM前方一致 | 対象外 | 延期 | DLM 0。DLMなし/*判定の品質確認はCP-04に残す |
| A07 DLM文字数・空値 | 対象外 | 延期 | DLM 0。JES2/JES3のDLM長検査を今回の完了条件にしない |
| A08 DD *+DLMのEOF診断 | 対象外 | 延期 | DLM 0。現物のEOF1件はDLMなしDD *であり合法な終端。誤って欠落警告を増やさない |
| A09 EXEC対象複数/リスト、DD位置値複数 | 対象外 | 延期 | EXEC123は全てPGM119/PROC4の単一対象。PGMリスト0、DDの複数位置値0。PARMのリスト1や空文字リスト1をPGMリストと混同しない。観測形式を維持し、非出現の不正構文全般の診断完成は求めない |
| A10 Job.spanからEOFデータが漏れる | 発現 | P1 | MNTTRDB2:28のDD *、29〜30データに対し現行span=[1,28]を実測。30行までを含むことが必要 |
| A11 階層Golden・受入ゲート不足 | 発現（先行監査版） | P0 | 48資産のsource階層は比較できたが、先行監査の全JobNode除去が比較PASSという盲点は現物の階層にも適用される。CardDemo専用契約の検査が必要。今回末尾で検出したHarness同時変更がこの問題を解消したかは未審査（Q11） |

分類結果は発現2、可能性1、対象外8。これは一般仕様の欠陥を撤回するものではない。対象外8件の合成入力を「合格した」と扱わず、元監査と再現証拠は残す。将来コーパスに発火構文が入れば対象外判定を失効させる。

## 4. CardDemo専用の受入基準

### 4.1 入力と必須対応の境界

CA-01: inventory.jsonの全48パス・ハッシュを固定し、1件でも追加/削除/内容変更があれば「同じCardDemo契約で受入済み」としない。拡張子を小文字だけで走査して8ファイルを落とす実装は不合格。全240原本資産を保全対象とする。

CA-02: §1の7文種・全オペランド・全出現値・特殊形式を必須にする。構文として値を保存することと、意味が解決したことを別状態で示す。パラメーター順序を許容する比較でも、位置要素・連結順序・重複・NULLを削らない。

### 4.2 JOB→STEP→DDの独立した正解データ

CA-03: 付録Aとinventory.jsonのfiles[].job / steps / job_level_ddsを、原本に由来する**source階層の独立参照データ**とする。Parser出力から作った期待値ではない。全123 STEP、500 DDを先頭行で照合する。ここに注記した源泉と人のレビューを経て、新規Goldenへ手で移す。現段階で既存Goldenへ移植・承認・封印はしていない。

- 46 JOBと2 PROCを別のルート型にする。JOB内119 STEP、PROC内4 STEPを単純合計した123を、46 JOBの実効STEP数と誤表示しない。
- JOBファイルのDD480はJOBレベル3+STEPレベル477。PROCのDD20を追加したsource DD総数が500。
- 個々のSTEPは`source_path + EXEC先頭行`、DDは`source_path + DD先頭行`で識別する。表示名は識別キーにしない。
- 連結は24件全て、先頭DDのソース行とindexを照合する。CREADB21:32→33→34のJOBLIBと、LOADPADB:28→29→30のSTEPLIBなど長さ3も必須。
- PROC呼出しに続く修飾DDは、source ASTでは呼出しSTEPの子。実効モデルではPRC001のFILEIN/OUTへ適用し、両方の出典を残す。
- 全データ領域のDD先頭行・物理行リスト・終端種別・終端行を照合する。EOF終端は後続文がないため欠落区切りと決めつけない。

### 4.3 PROC・INCLUDE・シンボル・外部参照

CA-04: PROC4呼出し全件に、要求名、ライブラリー探索根拠、メンバー候補、解決状態を付ける。未登録DSNからパスを推測してRESOLVEDにしない。

| 論理参照 | ローカル候補 | 現状 / 受入に必要な根拠 |
|---|---|---|
| AWS.M2.CARDDEMO.PROC(REPROC) | app/proc/REPROC.prc | datasets未登録。確認済みマッピングが必要 |
| AWS.M2.CARDDEMO.PROC(TRANREPT) | app/proc/TRANREPT.prc | 現JOBから呼出し0。独立メンバーとして登録し、ラベルREPROCと別に扱う |
| AWS.M2.CARDDEMO.CNTL(REPROCT) | app/ctl/REPROCT.ctl、およびDB2サブアプリの同名CTL | 同一ハッシュでも候補2。マッピング/探索順を明示。無断で先頭候補を選ばない |
| AWS.M2.CARDDEMO.CNTL(DB2FREE/DB2TIAD1/DB2CREAT/DB2TEP41/DB2LTTYP/DB2LTCAT) | app-transaction-type-db2/ctlの各該当名 | 全7参照を明示対応にする（DB2TEP41は2回） |
| AWS.M2.CARDDEMO.JCL(INTRDRJ2) | app/jcl/INTRDRJ2.JCL | 入力DSN→内部リーダー出力という依存候補。ライブラリー対応確認前はENVIRONMENT_GAP |
| OEMPP.IMS.V15R01MB.PROCLIB(DFSVSMDB) | 当該メンバーは対象app内にない | 外部参照4件として明示。消去や仮のローカルパス化をしない |

JCLLIBの探索順はIBM規則に従い、先に明示したライブラリーを使う。[IBM JCLLIB ORDER](https://www.ibm.com/docs/en/zos/3.2.0?topic=d-parameter-field-6)。proc/TRANREPT内のREPROC呼出しには、呼出し文脈がない時のライブラリーを仮定しない。単独メンバー検査では未解決状態を保持し、契約用の明示的なライブラリー文脈を用意した時だけ期待展開を比較する。

CA-05: REPROCの4 DDを保持し、8修飾DDの上書きを順序通りに適用する。原値・適用値・上書き理由を残す。3 JOBの3呼出しについて明示マッピングが成立した場合、原本119 STEPは実効119プログラムSTEP、DDは480−6（上書き文）+12（手続きDD）=486（JOBレベル3を含む）になる。この値は**条件付きの独立検算値**であって現状の解決済み結果ではない。未呼出しTRANREPTメンバーを追加のJOBとして加算しない。同メンバーを指定文脈で展開する検査は3プログラムSTEP・18 DDとなる。

CA-06: SETによるCODER/DB2S/LBNM/HLQと、呼出しCNTLLIBをスコープ付きで扱う。静的に定義された変換時値（例:LBNM=AWS.M2.CARDDEMO）は算出根拠とともに残す。SYSUIDは実行環境依存、SYUIDは未定義候補として残し、空文字にしない。

CA-07: DD *,SYMBOLS=JCLONLYは読み込み時のシンボル置換要求として表す。CBADMCDJではSET HLQがあるが、EXPORTは0。**SETされたHLQをそのままデータの確定置換値にしてはいけない。** JCLONLYはEXPORT等で利用可能になったシンボル/JESシンボルが対象であるため、公開/継承の環境根拠が必要。生データと置換要求を保持し、現状は当該&HLQを「実行時の利用可能性未確定」とする。[IBM SYMBOLS構文](https://www.ibm.com/docs/en/zos/3.2.0?topic=sp-syntax-6)、[IBMデータ内シンボル](https://www.ibm.com/docs/en/zos/3.2.0?topic=symbols-using-in-jes-in-stream-data)。この未解決は、JCL文のSET処理が未実装でよいという意味ではない。

CA-08: JCL INCLUDEは0件なので展開エンジンの完成を要求しない。今後検出された場合は、MEMBER名・位置・原文を出して対象拡大待ちとして止める。DFSORTのINCLUDE COND（TRANREPT.jcl:47、proc/TRANREPT:45）はDDデータとして保持し、JCL INCLUDE=0という調査結果を変えない。

### 4.4 条件・資源・未対応検出

CA-09: COND15件は独立期待ASTと一致し、定数0/4・NE/LT・全既実行STEPへのテスト・条件真でスキップ・通常ABEND時の後続抑止を保持する。RCを固定して実行経路を確定しない。例として前段RC=0/4/8、前段スキップ、前段ABENDを使う表で判定を検証する。これは新たな試験計画であり今回は実装しない。

CA-10: DISPの明示/省略、MODの存在依存、GDG(+1)/(0)、DCB後方参照、DSN=NULLFILE、SYSOUT=(A,INTRDR)を独立に意味付けする。MODやGDGの実環境値はRUNTIME_DEPENDENTで許容するが、単なる文字列保存だけで意味解析完了にはしない。INTRDRは「投入し得る」依存を表し、実際の投入回数や成否を静的に捏造しない。[IBM内部リーダー出力](https://www.ibm.com/docs/en/zos/3.2.0?topic=files-sysout-data-sets)。

CA-11: 観測範囲外の文種/オペランド/組合せを元位置付きで報告する。既存Parserが偶然受理しても本契約の対応範囲へ自動追加しない。入力ハッシュが変わった場合に再インベントリを必須とし、特にDLM、DD DATA、継続null、null後の有効文、複数EXEC対象を境界検査する。UNKNOWN/UNSUPPORTEDを正常解析の一種として集計しない。誤った構文を黙って補正しない。

CA-12: 全91インライン領域と必要な外部CTLに機能注釈または阻害理由を付ける。IF/SET/INCLUDE/CONDという文字をデータ内で見つけただけでJCL機能を増やさない。既存のPGMからJava実装先を推測せず、COBOL実行/ユーティリティ実行/サブシステム操作を区別する。

### 4.5 ASTトレーサビリティ

CA-13: 全sourceノードはsource path/id・SHA-256・文字コード・元の物理行・列範囲・元文ID・原表記へ逆引きできる。継続した値は開始1文字だけでなく全セグメントの列範囲を検査する。元バイト列と改行を保持し、コメント・データ・sequence欄を不正に切捨てない。

CA-14: Job/Step/PROC/DataRegionの包含関係、親ID・参照IDの存在、DD所属、同名STEPの個体識別を検査する。MNTTRDB2のJob全体範囲は1〜30行。全3046レコードがsource役割に1回だけ現れ、同一レコードがデータと実行文へ二重所属しない。末尾コメントのJES依存の実行時扱いを断定する必要はないが、原文のCOMMENT/NULLという事実と、実行に使われるかどうかは区別する。

CA-15: 展開後のノードは、呼出しEXEC・元PROC文/STEP/DD・上書きDD・SET/引数の根拠を全て参照する。元ASTを置換して出典を消さない。DCB後方参照も参照元/参照先双方を保持する。

### 4.6 品質ゲートの合格条件

既存ゲートのPASSとCardDemo受入を別の名前・結果にする。以下は今後実装する契約であり、今回ゲートコードを変更していない。

| ゲート | 合格条件 | 現在の調査による判定 |
|---|---|---|
| CD-SOURCE | 全48ハッシュ/3046レコード/681文、119+4 STEP、480+20 DDが独立データに一致。全階層・24連結・91境界一致 | 照合した所属部分は一致。全値・列セグメントのGoldenは未承認 |
| CD-TRACE | CA-13〜15の全件検査。記録欠落・範囲漏れ・壊れた親子参照0 | A10で不合格 |
| CD-RESOLVE | 必須PROC4呼出し、8上書き、SET/引数、DCB参照3が期待通り。必須ローカル参照の未解決0 | datasets未登録、Resolver未完了のため未達 |
| CD-SEMANTICS | COND15、資源属性、INTRDR、制御入力からの機能注釈に出典。対象内未分類0 | 未達。文字列の保存と機能解析は別 |
| CD-ASSURANCE | 対象内の必須Goldenと比較器感度試験が全件合格、approved/reviewed。必須項目のskip/xfail/NOT_IMPLEMENTED/BLOCKED/uncheckedは0 | 未達。既存draft一致を流用しない |
| CD-INTEGRITY | 原本240資産・既存期待値の無断変更0、決定性、一貫したschema、既存lint/type/関連回帰の破損0 | 原本・既存Goldenは一致。ワークスペース全体は同時変更あり。将来の対象版を固定して再実行 |
| CD-IR | 各必要能力にJOB/STEP/DD/カード/規則の証拠。46 JOBと2 PROC全てが評価済みまたは明示阻害。能力集合を変える未解決の見落とし0 | 本書は候補集合と阻害事項。最小集合の最終確定ではない |

**最終受入PASSには全ゲートの合格が必要。** BLOCKED/未実装を単に一覧に出すだけでPASSにはしない。SYSUID、実GDG番号、OEM実環境等の「静的に確定しないこと自体が正しい値」は、期待値も未確定型として一致していれば許容する。必須PROCの探索先未登録のような「必要な解析が終わっていない状態」とは区別する。

同名STEPの削除、DDの別STEPへの移動、連結順の逆転、EOFデータ切捨て、COND比較の逆転、PROC上書き欠落、GDG符号の反転をメモリ上のテスト出力へ注入し、対応する比較が必ず不合格になることを要求する。実装本体や原本を破壊して試験しない。既存汎用Goldenの対象外ケースは別集計し、必須項目の分母に混ぜず、対象外の件数・理由は公開する。

### 4.7 未対応として許容する範囲

非出現のDLM/DD DATA/IF/JCL INCLUDE/一般JES制御・全NULLJCL解釈分岐・裸PROC形式・任意深度の手続き入れ子・任意COND形式・各製品の汎用制御言語Parserは、今回の実装を要求しない。一般シンボル解決を不要とするのではなく、現物のSET/CNTLLIB/シンボル参照に絞る。

許容条件は「固定コーパスに不在」「出現時に検出して止める」「対応済みとして表示しない」の3点。既存コードに対応機能があっても削除は要求しない。未知入力や拡張コーパスに対する一般仕様適合を宣伝しない。前節の必須項目を未対応許容へ移す変更には契約の再承認が必要。

外部システムへの実接続・FTP・SQL/CICS/IMS操作、ジョブ投入、Javaコード生成、実運用スケジュールの決定、GDG実世代やカタログ実状態の確定は対象外。静的な要求能力・依存・阻害の記録は対象内である。

## 5. 独立したGolden Testの作成計画

今回作成したのはsource由来の調査参照データと本契約であり、既存Golden期待値は一切変えていない。次の順で専用期待値を作成する。

1. **入力固定**: inventory.jsonの48ハッシュと原本への読取専用参照を固定する。CTL候補8件も内容ハッシュを記録し、マッピング確認後に参照集合を凍結する。
2. **原本から正解を記入**: 付録Aを使い、全48資産のJOB/PROC→STEP→DD階層、全500 DDの属性、全91境界、全24連結を別の期待データへ記入する。inspect_corpus.pyの出力を無審査で正解に昇格させず、原本の文先頭/継続/行列と二重照合する。Parser・Adapter・to_golden_view・既存実測JSONからの生成は禁止。
3. **IBMによる意味期待値**: COND15、DISP9形式、GDG24、DCB後方参照3、NULLFILE、INTRDR、SYMBOLS、PROC4呼出しと8上書きについて、IBM公式記述と手計算から期待値を作る。原値・型・未確定状態・規則/版/節を併記する。§4.3の条件付き486 DD等を使って展開の計数も検算する。
4. **境界を代表例で固定**: MNTTRDB2 EOF、CBPAUP0Jのコメントによる終端、WAITSTEPのデータ末尾欄、CREADB21のJOBLIB/SET/SCAN、CREASTMT:90のコメント、TRANREPTの同名STEP/PROCラベル/上書き、INTRDRJ1、CBADMCDJのSYMBOLSを必須ケースにする。全件階層期待値と代表意味ケースの両方を用意する。
5. **機能注釈**: 全制御入力をPGMと組で読み、必要な操作・サブシステム・ラッパー内実行対象を手で注釈する。汎用ユーティリティParserを増築する前に、注釈集合が最小IR候補を導くか確認する。読めない外部入力は阻害として出す。
6. **独立レビューと封印**: 実装担当以外が原本・IBM根拠・期待値をレビューする。ユーザー承認後だけ新規GoldenをFORMALにし、既存ルールに従って変更履歴・封印を行う。draftはREFERENCEのまま。今回の付録も人の承認済みGoldenと称さない。
7. **比較の感度確認**: CA-03/14の階層、属性・全位置、展開の複数出典を比較できるviewを設計し、§4.6の変異を検出することを確認する。現行statements viewだけを専用Goldenへコピーして完了としない。

## 6. 最小修正計画（今回は実施しない）

| 順序 | 作業 | 完了の証拠 / 増やさないもの |
|---|---|---|
| 1 | 本契約と独立階層のレビュー、入力・期待データを凍結 | 48/123/500/91/24と全出典の一致。汎用Parser開発は再開しない |
| 2 | A11に対するCardDemo受入比較・対象範囲判定を設計/追加 | JOB/STEP/DD欠落・付替え等を検出。対象外8件を黙ってPASSEDに変えない |
| 3 | A10だけの範囲計算修正と全48への追跡検査 | MNTTRDB2:1〜30と全親子包含が合格。NULLJCL/DLM候補エンジンは作らない |
| 4 | 必須の小さなResolver | 明示マッピング、REPROC/CNTLLIB、8 DD上書き、SET4種類、3 DCB参照。汎用INCLUDEや15階層を先に実装しない |
| 5 | 実出現の意味モデル | COND2形式、DISP/GDG/DCB、SYSOUT INTRDR、SYMBOLS要求を扱う。未確定値は型で表す |
| 6 | 実制御カードに機能注釈を付け、Batch IR候補を集計 | 各能力に原本の証拠、全対象に評価/阻害。ユーティリティの完全再実装はしない |
| 7 | 専用ゲートで受入 | 必須項目100%合格、対象内未検証0。原本と既存Goldenの保全確認 |

A01は現コーパス境界の検査と尾部原文保存で扱い、A02〜A09の一般修正は延期する。新規Parserの作り直しや、監査指摘全11件の同時解決は最小計画に含めない。次の実装はユーザーが着手を認めた範囲だけで行う。

## 7. 未解決事項

| ID | 未解決 | 受入への影響 / 次に必要な情報 |
|---|---|---|
| Q01 | 論理DSN→ローカルのマッピング | PROC/CNTL/JCLの明示対応が必要。現在datasets=[]。候補が見つかっただけでは解決済みにならない |
| Q02 | REPROCTの候補2か所とPROC探索文脈 | 同一内容でも探索順は別問題。TRANREPT単独メンバーの文脈、システムPROCLIB既定も仮定しない |
| Q03 | 外部OEM/IMS/DB2/CICS/TXT2PDF環境 | DFSVSMDB、実ロードモジュール、ライブラリー、DB2プラン等の実在は未確認。機能存在は記録できるが実行可能性は保証できない |
| Q04 | CBADMCDJのJCLONLYで利用可能なHLQ | 原本にEXPORTがない。公開/継承やJESシンボルの根拠がなければ生データのHLQ置換を確定しない |
| Q05 | &SYUIDとUNIT=SYSAD | 誤記か環境定義かを原本所有者が判断。調査側は補正しない |
| Q06 | 同名STEPとTRANREPTのPROCラベル不一致 | 解析では個体を保存。運用上の許容性・改名/原本修正の必要性は別審査。今回原本変更は禁止 |
| Q07 | TYPRUN=SCAN、管理/セットアップ/業務JOBの区分 | 全資産の機能集合と、移行本番の実行対象集合を混同しない。最小Runtime範囲を確定する際に所有者の判断が必要 |
| Q08 | 外部データ・カタログ・GDG・MOD・通知先 | 静的に確定しない値は未確定型として受入可能。値を推測することは不可 |
| Q09 | 制御カードとCOBOL内部の意味境界 | JCLのPGMだけでは副次実行・SQL・資源操作を尽くせない。原カード注釈と必要に応じたCOBOL呼出し解析を別途レビューし、JCLだけで移行全体のIR最小性を証明したとしない |
| Q10 | 専用Golden/ゲートの承認と規則登録 | 本書は受入仕様案。新たなSYMBOLS/INTRDR等の根拠を正規レジストリーへ加えるのは次回許可後。今回はrequirements/ADR/既存Goldenも変更していない |
| Q11 | 調査中の同時変更と対象版固定 | src/jclprof/harness/{adapters,comparator,runner,trace}.py、src/jclprof/parser/adapter.py、specs/golden-schema.jsonの変更、および14ファイル追加を検出。詳細はpreservation.json。停止方針を実装担当にも適用し、次回検証前に対象版を固定する必要がある。新しいHarness等の品質監査は今回の作業へ混ぜない |

本調査では、非出現構文の一般化修正よりも、原本の正解階層・参照解決・機能証拠と受入の信頼性を優先する。以下の付録はそのsource階層を全件提示する。

## 付録A. 原本から独立に作成した全JOB/PROC→STEP→DD一覧

`name@line`は当該ファイルの物理先頭行。`∅→head[index]@line`は名前なし連結DD。実効展開前のsource構造であり、DD上書きの結果とは別。元パラメーター全値と継続行リストはinventory.json/operands.tsvにある。

### app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl

JOB CBPAUP0J。47レコード。SHA-256: `c90fbd21b8ea2b6448b8939ff4f3b47c6f73472465cd7d1e25871f7779063a86`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 24 / STEP01 | PGM=DFSRRC00 | STEPLIB@26, ∅→STEPLIB[1]@27, DFSRESLB@28, PROCLIB@29, DFSSEL@31, IMS@33, ∅→IMS[1]@34, SYSIN@36, SYSOUX@39, SYSOUT@40, SYSABOUT@41, ABENDAID@42, IEFRDER@43, IMSLOGR@44, SYSPRINT@45, SYSUDUMP@46, IMSERR@47 |

### app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl

JOB DBPAUTP0。47レコード。SHA-256: `3fabb7f3230f98fee855a8d436f70f4bd601a9e544f29c83d413a3a7a61efbcd`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 7 / STEPDEL | PGM=IEFBR14 | SYSPRINT@8, SYSUT1@9 |
| 15 / UNLOAD | PGM=DFSRRC00 | STEPLIB@18, ∅→STEPLIB[1]@19, DFSRESLB@20, IMS@21, ∅→IMS[1]@22, SYSPRINT@23, DFSURGU1@25, DDPAUTP0@31, DDPAUTX0@32, DFSVSAMP@33, DFSCTL@34, SYSUDUMP@36, RECON1@40, RECON2@41, RECON3@42, DFSWRK01@44, DFSSRT01@45 |

### app-authorization-ims-db2-mq/jcl/LOADPADB.JCL

JOB LOADPADB。51レコード。SHA-256: `9a0a88472f69236d14b36ecc89d83f35179d5c720c2c3a465af5f7ff510fb067`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 26 / STEP01 | PGM=DFSRRC00 | STEPLIB@28, ∅→STEPLIB[1]@29, ∅→STEPLIB[2]@30, DFSRESLB@31, IMS@33, ∅→IMS[1]@34, INFILE1@36, INFILE2@38, DFSVSAMP@44, IMSLOGR@46, IEFRDER@47, SYSPRINT@48, SYSUDUMP@49, IMSERR@50 |

### app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL

JOB UNLDGSAM。53レコード。SHA-256: `1da94de3db6f265578c8b7498a2371c0c7246c8409f4ac44eb8013d3f0e113b8`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 26 / STEP01 | PGM=DFSRRC00 | STEPLIB@28, ∅→STEPLIB[1]@29, ∅→STEPLIB[2]@30, DFSRESLB@31, IMS@33, ∅→IMS[1]@34, PASFILOP@36, PADFILOP@39, DDPAUTP0@42, DDPAUTX0@43, DFSVSAMP@46, IMSLOGR@48, IEFRDER@49, SYSPRINT@50, SYSUDUMP@51, IMSERR@52 |

### app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL

JOB UNLDPADB。69レコード。SHA-256: `e2c26ca546ab427d66cadeaff07345bad706c979ca396fb04e60d401dc93c66b`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 25 / STEP0 | PGM=IEFBR14 | SYSPRINT@27, SYSOUT@29, SYSDUMP@31, DD1@33, DD2@35 |
| 38 / STEP01 | PGM=DFSRRC00 | STEPLIB@40, ∅→STEPLIB[1]@41, ∅→STEPLIB[2]@42, DFSRESLB@43, IMS@45, ∅→IMS[1]@46, OUTFIL1@48, OUTFIL2@53, DDPAUTP0@58, DDPAUTX0@59, DFSVSAMP@62, IMSLOGR@64, IEFRDER@65, SYSPRINT@66, SYSUDUMP@67, IMSERR@68 |

### app-transaction-type-db2/jcl/CREADB21.jcl

JOB CREADB2。84レコード。SHA-256: `88b81b1d8530037d1661321e47600b9afb2a2cf4894c7eefeacd5aff07b87d69`。

JOBレベルDD（原本順）: `JOBLIB@32, ∅→JOBLIB[1]@33, ∅→JOBLIB[2]@34`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 40 / FREEPLN | PGM=IKJEFT01 | STEPLIB@41, ∅→STEPLIB[1]@42, SYSPRINT@43, SYSTSPRT@44, SYSUDUMP@45, SYSTSIN@46 |
| 52 / CRCRDDB | PGM=IKJEFT01 | STEPLIB@53, ∅→STEPLIB[1]@54, SYSTSPRT@55, SYSUDUMP@56, SYSPRINT@57, SYSTSIN@58, SYSIN@59 |
| 64 / LDTTYPE | PGM=IEFBR14 |  |
| 65 / RUNTEP2 | PGM=IKJEFT01 | STEPLIB@66, ∅→STEPLIB[1]@67, SYSTSPRT@68, SYSUDUMP@69, SYSPRINT@70, SYSTSIN@71, SYSIN@72 |
| 77 / LDTCCAT | PGM=IKJEFT01 | STEPLIB@78, ∅→STEPLIB[1]@79, SYSTSPRT@80, SYSUDUMP@81, SYSPRINT@82, SYSTSIN@83, SYSIN@84 |

### app-transaction-type-db2/jcl/MNTTRDB2.jcl

JOB MNTTRDB2。30レコード。SHA-256: `beaba6e4e35092c2ac7c1be7a3708303cc75d0fca00b64c65ee2d2bc1682f893`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / STEP1 | PGM=IKJEFT01 | STEPLIB@22, ∅→STEPLIB[1]@23, ∅→STEPLIB[2]@24, DBRMLIB@25, SYSTSPRT@26, INPFILE@27, SYSTSIN@28 |

### app-transaction-type-db2/jcl/TRANEXTR.jcl

JOB TRANEXTR。122レコード。SHA-256: `d4d3b99a71b91fbce9c145283642ee7ca31b5ad7fa51ddcdb3e2c0b2e530457f`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 31 / STEP10 | PGM=IEBGENER | SYSPRINT@32, SYSIN@33, SYSUT1@34, SYSUT2@35 |
| 42 / STEP20 | PGM=IEBGENER | SYSPRINT@43, SYSIN@44, SYSUT1@45, SYSUT2@46 |
| 53 / STEP30 | PGM=IEFBR14 | DD01@54, DD02@58 |
| 65 / STEP40 | PGM=IKJEFT01 | STEPLIB@66, ∅→STEPLIB[1]@67, SYSTSPRT@68, SYSPRINT@69, SYSUDUMP@70, SYSPUNCH@71, SYSREC00@72, SYSIN@75, SYSTSIN@86 |
| 95 / STEP50 | PGM=IKJEFT01 | STEPLIB@96, ∅→STEPLIB[1]@97, SYSTSPRT@98, SYSPRINT@99, SYSUDUMP@100, SYSPUNCH@101, SYSREC00@102, SYSIN@105, SYSTSIN@117 |

### jcl/ACCTFILE.jcl

JOB ACCTFILE。65レコード。SHA-256: `92ce6733ad0e3fad640e19d1224003fe30c711c2564eb7a660d53fd7f0dd6622`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 33 / STEP10 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 54 / STEP15 | PGM=IDCAMS | SYSPRINT@55, ACCTDATA@56, ACCTVSAM@58, SYSIN@60 |

### jcl/CARDFILE.jcl

JOB CARDFILE。128レコード。SHA-256: `795600a41abec0706aec8bd0dd93446b29cf01fcd8f9d2173e4ec6d5476611d0`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / CLCIFIL | PGM=SDSF | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| 33 / STEP05 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 47 / STEP10 | PGM=IDCAMS | SYSPRINT@48, SYSIN@49 |
| 68 / STEP15 | PGM=IDCAMS | SYSPRINT@69, CARDDATA@70, CARDVSAM@72, SYSIN@74 |
| 80 / STEP40 | PGM=IDCAMS | SYSPRINT@81, SYSIN@82 |
| 97 / STEP50 | PGM=IDCAMS | SYSPRINT@98, SYSIN@99 |
| 107 / STEP60 | PGM=IDCAMS | SYSPRINT@108, SYSIN@109 |
| 118 / OPCIFIL | PGM=SDSF | ISFOUT@119, CMDOUT@120, ISFIN@121 |

### jcl/CBADMCDJ.jcl

JOB CBADMCDJ。167レコード。SHA-256: `49b99c74e97d7177e558748f58b73cc418daacd93b415d908b09651393841916`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 27 / STEP1 | PGM=DFHCSDUP | STEPLIB@29, DFHCSD@30, OUTDD@31, SYSPRINT@32, SYSIN@33 |

### jcl/CBEXPORT.jcl

JOB CBEXPORT。72レコード。SHA-256: `e5d010a3209dbbcf6d9b92a3c71b7c806019ce014ad921430eed9abf1706f804`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 24 / STEP01 | PGM=IDCAMS | SYSPRINT@25, SYSIN@26 |
| 43 / STEP02 | PGM=CBEXPORT | STEPLIB@44, CUSTFILE@49, ACCTFILE@51, XREFFILE@53, TRANSACT@55, CARDFILE@57, EXPFILE@62, SYSOUT@67, SYSPRINT@68 |

### jcl/CBIMPORT.jcl

JOB CBIMPORT。68レコード。SHA-256: `9f3adc0cde9d471b0976a4e4c5bee625a65fd0cdcc1e031d9abde8f5c3e8ccf5`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP01 | PGM=CBIMPORT | STEPLIB@23, EXPFILE@28, CUSTOUT@33, ACCTOUT@38, XREFOUT@43, TRNXOUT@48, ERROUT@56, SYSOUT@64, SYSPRINT@65 |

### jcl/CLOSEFIL.jcl

JOB CLOSEFIL。34レコード。SHA-256: `e47d406dde49f06847a46559fa9a7182b80b85f0727a5f0be312286f34df9192`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / CLCIFIL | PGM=SDSF | ISFOUT@23, CMDOUT@24, ISFIN@25 |

### jcl/COMBTRAN.jcl

JOB COMBTRAN。52レコード。SHA-256: `a91649d6a927e1fd7b81fcdab39088ae26554eea52b07d5715e488c81c3f2cc2`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05R | PGM=SORT | SORTIN@23, ∅→SORTIN[1]@25, SYMNAMES@27, SYSIN@29, SYSOUT@32, SORTOUT@33 |
| 41 / STEP10 | PGM=IDCAMS | SYSPRINT@42, TRANSACT@43, TRANVSAM@45, SYSIN@47 |

### jcl/CREASTMT.JCL

JOB CREASTMT。97レコード。SHA-256: `87a18700fac7bccfffbefa5d80fed0b171fdc36caeebb575c8a3cf66e4fc3caa`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / DELDEF01 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 44 / STEP010 | PGM=SORT | SORTIN@45, SYSPRINT@46, SYSOUT@47, SORTOUT@48, SYSIN@52 |
| 56 / STEP020 | PGM=IDCAMS | SYSPRINT@57, INFILE@58, OUTFILE@59, SYSIN@60 |
| 66 / STEP030 | PGM=IEFBR14 | HTMLFILE@67, STMTFILE@72 |
| 79 / STEP040 | PGM=CBSTM03A | STEPLIB@80, SYSPRINT@81, SYSOUT@82, TRNXFILE@83, XREFFILE@84, ACCTFILE@85, CUSTFILE@86, STMTFILE@87, HTMLFILE@92 |

### jcl/CUSTFILE.jcl

JOB CUSTFILE。84レコード。SHA-256: `5fa6da4bc85866f0e08783585e7c652d312179982dbdd821866f569a083ac976`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / CLCIFIL | PGM=SDSF | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| 32 / STEP05 | PGM=IDCAMS | SYSPRINT@33, SYSIN@34 |
| 43 / STEP10 | PGM=IDCAMS | SYSPRINT@44, SYSIN@45 |
| 64 / STEP15 | PGM=IDCAMS | SYSPRINT@65, CUSTDATA@66, CUSTVSAM@68, SYSIN@70 |
| 76 / OPCIFIL | PGM=SDSF | ISFOUT@77, CMDOUT@78, ISFIN@79 |

### jcl/DALYREJS.jcl

JOB DALYREJS。32レコード。SHA-256: `ce396a6469c84577ea508d184f7ea6a42ceacd54c6a5e0fb097e626bb6361d45`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / STEP05 | PGM=IDCAMS | SYSPRINT@22, SYSIN@23 |

### jcl/DEFCUST.jcl

JOB DEFCUST。47レコード。SHA-256: `03dd2fc683ced79ec53269f6a24d48ceadb87ae4d6a5b48b65a37763046dfd58`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 32 / STEP05 | PGM=IDCAMS | SYSPRINT@33, SYSIN@34 |

### jcl/DEFGDGB.jcl

JOB DEFGDGB。63レコード。SHA-256: `4ccd135a079641b2d484b7789ea0f47955725774442283274f204480c0903f3f`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / STEP05 | PGM=IDCAMS | SYSPRINT@22, SYSIN@23 |

### jcl/DEFGDGD.jcl

JOB DEFGDGD。94レコード。SHA-256: `78c13d7e0e851aecd1acbfcedd26b60633a3a850dcd9fe38de339362be5e4830`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 24 / STEP10 | PGM=IDCAMS | SYSPRINT@25, SYSIN@26 |
| 36 / STEP20 | PGM=IEBGENER | SYSPRINT@37, SYSIN@38, SYSUT1@39, SYSUT2@40 |
| 47 / STEP30 | PGM=IDCAMS | SYSPRINT@48, SYSIN@49 |
| 59 / STEP40 | PGM=IEBGENER | SYSPRINT@60, SYSIN@61, SYSUT1@62, SYSUT2@63 |
| 70 / STEP50 | PGM=IDCAMS | SYSPRINT@71, SYSIN@72 |
| 82 / STEP60 | PGM=IEBGENER | SYSPRINT@83, SYSIN@84, SYSUT1@85, SYSUT2@86 |

### jcl/DISCGRP.jcl

JOB DISCGRP。65レコード。SHA-256: `64a250c918cc8205eddd6d51615e24a8c23585ff012ea518c6d452ebd7d71492`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 33 / STEP10 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 54 / STEP15 | PGM=IDCAMS | SYSPRINT@55, DISCGRP@56, DISCVSAM@58, SYSIN@60 |

### jcl/DUSRSECJ.jcl

JOB DUSRSECJ。92レコード。SHA-256: `71a529aab49502e9ce57abcdb268a896e34b947409d3278c5dd813f93105e33f`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 23 / PREDEL | PGM=IEFBR14 | DD01@25 |
| 32 / STEP01 | PGM=IEBGENER | SYSUT1@34, SYSUT2@46, SYSPRINT@51, SYSIN@52 |
| 58 / STEP02 | PGM=IDCAMS | SYSPRINT@60, SYSIN@61 |
| 80 / STEP03 | PGM=IDCAMS | IN@82, OUT@83, SYSOUT@84, SYSPRINT@85, SYSIN@86 |

### jcl/ESDSRRDS.jcl

JOB ESDSRRDS。124レコード。SHA-256: `9bec766029968057b831f539cc91b84e4e1d8ee22aa3de5ba6b509f8a698de77`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 24 / PREDEL | PGM=IEFBR14 | DD01@26 |
| 33 / STEP01 | PGM=IEBGENER | SYSUT1@35, SYSUT2@47, SYSPRINT@52, SYSIN@53 |
| 59 / STEP02 | PGM=IDCAMS | SYSPRINT@61, SYSIN@62 |
| 79 / STEP03 | PGM=IDCAMS | IN@81, OUT@82, SYSOUT@83, SYSPRINT@84, SYSIN@85 |
| 93 / STEP04 | PGM=IDCAMS | SYSPRINT@95, SYSIN@96 |
| 113 / STEP05 | PGM=IDCAMS | IN@115, OUT@116, SYSOUT@117, SYSPRINT@118, SYSIN@119 |

### jcl/FTPJCL.JCL

JOB FTPJCLS。42レコード。SHA-256: `10393acea782d865532700ac61c9282c0438e921b34e698ddba1a046e974899a`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 30 / STEP1 | PGM=FTP | SYSIN@32 |

### jcl/INTCALC.jcl

JOB INTCALC。44レコード。SHA-256: `b9313658a1e6fdb570a765c5e5e0e9e23d83f7062439c7d18544da986fbf108d`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP15 | PGM=CBACT04C | STEPLIB@23, SYSPRINT@25, SYSOUT@26, TCATBALF@27, XREFFILE@29, XREFFIL1@31, ACCTFILE@33, DISCGRP@35, TRANSACT@37 |

### jcl/INTRDRJ1.JCL

JOB INTRDRJ1。19レコード。SHA-256: `bc1c4427ac4d980ea01686026f7f15d1e86b060c7c3dc5c795730cea5441dd87`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 6 / IDCAMS | PGM=IDCAMS | SYSPRINT@7, IN@8, OUT@9, SYSIN@10 |
| 14 / STEP01 | PGM=IEBGENER | SYSPRINT@15, SYSIN@16, SYSUT1@17, SYSUT2@18 |

### jcl/INTRDRJ2.JCL

JOB INTRDRJ2。14レコード。SHA-256: `e89c73e8ebffa116c27e7c2e335b364467355def280c6208b7ef9d70ca66c7a8`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 7 / IDCAMS | PGM=IDCAMS | SYSPRINT@8, IN@9, OUT@10, SYSIN@11 |

### jcl/OPENFIL.jcl

JOB OPENFIL。34レコード。SHA-256: `adf1f084e330739d5b220bc6ba08b0345ab5b9083e020d6f4527d021b6838a3a`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / OPCIFIL | PGM=SDSF | ISFOUT@23, CMDOUT@24, ISFIN@25 |

### jcl/POSTTRAN.jcl

JOB POSTTRAN。45レコード。SHA-256: `a4de9f8cc5fbcaefb12e0b05fe87cb7d0b4accaa8a05f2ff6c13cf325431e2d6`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 23 / STEP15 | PGM=CBTRN02C | STEPLIB@24, SYSPRINT@26, SYSOUT@27, TRANFILE@28, DALYTRAN@30, XREFFILE@32, DALYREJS@34, ACCTFILE@39, TCATBALF@41 |

### jcl/PRTCATBL.jcl

JOB PRTCATBL。66レコード。SHA-256: `0668cd90c6092711cd173b3dfcd884887c11408e7c5c9ebc2d0332d929750cbe`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / DELDEF | PGM=IEFBR14 | THEFILE@22 |
| 29 / STEP05R | PROC=REPROC | PRC001.FILEIN@32, PRC001.FILEOUT@35 |
| 43 / STEP10R | PGM=SORT | SORTIN@44, SYMNAMES@46, SYSIN@51, SYSOUT@58, SORTOUT@59 |

### jcl/READACCT.jcl

JOB READACCT。50レコード。SHA-256: `0965badda9c801df4f86e74755b66325764d8d1a840c615e6552b660f6401f15`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / PREDEL | PGM=IEFBR14 | DD01@23, DD02@25, DD03@27 |
| 32 / STEP05 | PGM=CBACT01C | STEPLIB@33, ACCTFILE@35, OUTFILE@37, ARRYFILE@41, VBRCFILE@45, SYSOUT@49, SYSPRINT@50 |

### jcl/READCARD.jcl

JOB READCARD。31レコード。SHA-256: `2b8ef6678d477345868671ace4b6a9990e33081d6ba6b47827aad980927132b7`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=CBACT02C | STEPLIB@23, CARDFILE@25, SYSOUT@27, SYSPRINT@28 |

### jcl/READCUST.jcl

JOB READCUST。30レコード。SHA-256: `3b39d6182c5483967c63616df65c56359e13a8a10c5bf08dcff9fe98566196a9`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / STEP05 | PGM=CBCUS01C | STEPLIB@22, CUSTFILE@24, SYSOUT@26, SYSPRINT@27 |

### jcl/READXREF.jcl

JOB READXREF。31レコード。SHA-256: `09f076859afdd2a12bbe2e5eb1380bb986a656efe7bfb65a39377ad2c581db52`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=CBACT03C | STEPLIB@23, XREFFILE@25, SYSOUT@27, SYSPRINT@28 |

### jcl/REPTFILE.jcl

JOB REPTFILE。32レコード。SHA-256: `b78fd0ff11009e23d5dce60a79daa5d947990d3b9e7a04ccb346fcc90151dee0`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |

### jcl/TCATBALF.jcl

JOB TCATBALF。65レコード。SHA-256: `9ff82ea5a21fd54c3ce405a14fd0851a7c17af71ed4e27a2bb2ce1860f50692b`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 33 / STEP10 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 54 / STEP15 | PGM=IDCAMS | SYSPRINT@55, TCATBAL@56, TCATBALV@58, SYSIN@60 |

### jcl/TRANBKP.jcl

JOB TRANBKP。71レコード。SHA-256: `bd7a846799373121152a91b52427f3c668f390f448609d0eea534d49989acb9d`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 23 / STEP05R | PROC=REPROC | PRC001.FILEIN@26, PRC001.FILEOUT@29 |
| 37 / STEP05 | PGM=IDCAMS | SYSPRINT@38, SYSIN@39 |
| 51 / STEP10 | PGM=IDCAMS | SYSPRINT@52, SYSIN@53 |

### jcl/TRANCATG.jcl

JOB TRANCATG。65レコード。SHA-256: `09ad86b3c1ac0b32cee842682baead25c1ded1572c65599591b28826261de457`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 33 / STEP10 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 54 / STEP15 | PGM=IDCAMS | SYSPRINT@55, TRANCATG@56, TCATVSAM@58, SYSIN@60 |

### jcl/TRANFILE.jcl

JOB TRANFILE。125レコード。SHA-256: `c506a68f7482a971133524ec1d8b76001f593d4e1e98477c12c80ede4e4ce2db`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / CLCIFIL | PGM=SDSF | ISFOUT@23, CMDOUT@24, ISFIN@25 |
| 32 / STEP05 | PGM=IDCAMS | SYSPRINT@33, SYSIN@34 |
| 46 / STEP10 | PGM=IDCAMS | SYSPRINT@47, SYSIN@48 |
| 67 / STEP15 | PGM=IDCAMS | SYSPRINT@68, TRANSACT@69, TRANVSAM@71, SYSIN@73 |
| 79 / STEP20 | PGM=IDCAMS | SYSPRINT@80, SYSIN@81 |
| 96 / STEP25 | PGM=IDCAMS | SYSPRINT@97, SYSIN@98 |
| 106 / STEP30 | PGM=IDCAMS | SYSPRINT@107, SYSIN@108 |
| 116 / OPCIFIL | PGM=SDSF | ISFOUT@117, CMDOUT@118, ISFIN@119 |

### jcl/TRANIDX.jcl

JOB TRANIDX。58レコード。SHA-256: `ad12d5f7b4b4e37b17baf23a5b1bf208ff35945182d587a909e0208d3bd45855`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP20 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 39 / STEP25 | PGM=IDCAMS | SYSPRINT@40, SYSIN@41 |
| 49 / STEP30 | PGM=IDCAMS | SYSPRINT@50, SYSIN@51 |

### jcl/TRANREPT.jcl

JOB TRANREPT。84レコード。SHA-256: `081aad149f0a9c020440fb6e6da93f2a6cf6d1f77eead3cefea3702b13d79802`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 23 / STEP05R | PROC=REPROC | PRC001.FILEIN@26, PRC001.FILEOUT@29 |
| 37 / STEP05R | PGM=SORT | SORTIN@38, SYMNAMES@40, SYSIN@45, SYSOUT@50, SORTOUT@51 |
| 59 / STEP10R | PGM=CBTRN03C | STEPLIB@60, SYSOUT@62, SYSPRINT@63, TRANFILE@65, CARDXREF@67, TRANTYPE@69, TRANCATG@71, DATEPARM@73, TRANREPT@76 |

### jcl/TRANTYPE.jcl

JOB TRANTYPE。65レコード。SHA-256: `7993012c72041e6a9cbda9fff43549af4f8789081dc8a64b71a8a1a01f775254`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 33 / STEP10 | PGM=IDCAMS | SYSPRINT@34, SYSIN@35 |
| 54 / STEP15 | PGM=IDCAMS | SYSPRINT@55, TRANTYPE@56, TTYPVSAM@58, SYSIN@60 |

### jcl/TXT2PDF1.JCL

JOB TXT2PDF1。41レコード。SHA-256: `7b051e99abe3fdcf772d613646b39f9abf10b02e9f52422d073fa0c52908e46b`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 24 / TXT2PDF | PGM=IKJEFT1B | STEPLIB@28, SYSEXEC@31, INDD@33, SYSPRINT@35, SYSTSPRT@36, SYSTSIN@37 |

### jcl/WAITSTEP.jcl

JOB WAITSTEP。27レコード。SHA-256: `36c98a55c7701bfaa9bd6404d2aca95888880d4f908ced678840a37e2e3eac5e`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / WAIT | PGM=COBSWAIT | STEPLIB@23, SYSOUT@24, SYSIN@25 |

### jcl/XREFFILE.jcl

JOB XREFFILE。106レコード。SHA-256: `f4a24014ae9ebfdf4d36db958e1fadb76158114fa6f721e9b547d0842d556f24`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 22 / STEP05 | PGM=IDCAMS | SYSPRINT@23, SYSIN@24 |
| 36 / STEP10 | PGM=IDCAMS | SYSPRINT@37, SYSIN@38 |
| 57 / STEP15 | PGM=IDCAMS | SYSPRINT@58, XREFDATA@59, XREFVSAM@61, SYSIN@63 |
| 69 / STEP20 | PGM=IDCAMS | SYSPRINT@70, SYSIN@71 |
| 87 / STEP25 | PGM=IDCAMS | SYSPRINT@88, SYSIN@89 |
| 97 / STEP30 | PGM=IDCAMS | SYSPRINT@98, SYSIN@99 |

### proc/REPROC.prc

PROC MEMBER REPROC。32レコード。SHA-256: `cbe8a6eb2e718baf4a45d474e369dfe066e698f09e295a5ae5f8de69088c3f53`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / PRC001 | PGM=IDCAMS | SYSPRINT@22, FILEIN@23, FILEOUT@25, SYSIN@27 |

### proc/TRANREPT.prc

PROC MEMBER TRANREPT。82レコード。SHA-256: `fdbdc473dd21ba4908613c47180542ceffea8ea9a976a9413355361c6deaf103`。

| EXEC行・STEP名 | 対象 | DD（原本順） |
|---|---|---|
| 21 / STEP01R | PROC=REPROC | PRC001.FILEIN@24, PRC001.FILEOUT@27 |
| 35 / STEP05R | PGM=SORT | SORTIN@36, SYMNAMES@38, SYSIN@43, SYSOUT@48, SORTOUT@49 |
| 57 / STEP10R | PGM=CBTRN03C | STEPLIB@58, SYSOUT@60, SYSPRINT@61, TRANFILE@63, CARDXREF@65, TRANTYPE@67, TRANCATG@69, DATEPARM@71, TRANREPT@74 |

## 付録B. DCB原値の全種類

原表記を辞書順に列挙する。各出典はoperands.tsvにある。

| 原値 | 回数 |
|---|---:|
| `(*.SORTIN)` | 3 |
| `(LRECL=100,BLKSIZE=0,RECFM=FB)` | 1 |
| `(LRECL=100,BLKSIZE=800,RECFM=FB)` | 1 |
| `(LRECL=107,RECFM=FB,DSORG=PS,BLKSIZE=0)` | 1 |
| `(LRECL=110,RECFM=FB,DSORG=PS,BLKSIZE=0)` | 1 |
| `(LRECL=133,RECFM=FB,BLKSIZE=0)` | 2 |
| `(LRECL=206,BLKSIZE=0,RECFM=FB)` | 1 |
| `(LRECL=27990,RECFM=VB,BLKSIZE=0)` | 1 |
| `(LRECL=350,BLKSIZE=3500,RECFM=FB)` | 1 |
| `(LRECL=350,RECFM=FB,BLKSIZE=0)` | 3 |
| `(LRECL=40,RECFM=FB,BLKSIZE=0)` | 1 |
| `(LRECL=50,RECFM=FB,BLKSIZE=0)` | 1 |
| `(LRECL=50,RECFM=FB,BLKSIZE=500)` | 1 |
| `(LRECL=60,RECFM=FB,BLKSIZE=600)` | 4 |
| `(LRECL=80,BLKSIZE=3200,RECFM=FB)` | 1 |
| `(LRECL=80,BLKSIZE=80)` | 1 |
| `(LRECL=80,BLKSIZE=8000,RECFM=FB)` | 2 |
| `(LRECL=80,RECFM=FB,DSORG=PS,BLKSIZE=0)` | 2 |
| `(LRECL=84,RECFM=VB,DSORG=PS,BLKSIZE=0)` | 1 |
| `(RECFM=F,LRECL=350,BLKSIZE=0)` | 1 |
| `(RECFM=F,LRECL=430,BLKSIZE=0)` | 1 |
| `(RECFM=FB,LRECL=132,BLKSIZE=0)` | 1 |
| `(RECFM=FB,LRECL=300,BLKSIZE=0)` | 1 |
| `(RECFM=FB,LRECL=350,BLKSIZE=0)` | 1 |
| `(RECFM=FB,LRECL=50,BLKSIZE=0)` | 1 |
| `(RECFM=FB,LRECL=500,BLKSIZE=0)` | 1 |
| `(RECFM=FBA,LRECL=133)` | 1 |

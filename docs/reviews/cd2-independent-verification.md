# CD-2 独立再検証

実施日: 2026-11-16（Asia/Tokyo）。実施者: Codex。
対象: ClaudeによるA10、H01、H02（CardDemoのカタログPROCメンバーPEND）の修正。

## 結論

**CD-2の指定範囲の修正検証はPASS。CardDemoの正式受入れは引き続きFAIL。**

A10の末尾データ包含、H01のJOB文同一性、H02のPROCルートからのPEND到達性を、
コード差分、凍結済みCD-1期待値、独立反例、修正前コードの再実行で確認した。
3件を修正済みとする独立検証の根拠として利用可能である。
台帳のCLOSEDへの変更は今回行っていない。48件の期待値の承認も行っていない。
H02B・H03・A01〜A09の解消、汎用Parser全体の受入れ、A11の完全なCLOSED判定を意味しない。

| 検査 | 独立再実行結果 |
|---|---|
| CD-SOURCE | PASS、48/48 |
| CD-TRACE | PASS、48/48、指摘0 |
| CD-ASSURANCE | PENDING、48/48未承認 |
| CardDemo source正式受入れ | FAIL（未承認のため） |
| CD変異 | 1501/1501検出、逃避0 |
| R1階層変異 | 943/943検出、逃避0 |
| 全tests | 412 passed / 52 skipped / 9 xfailed |
| Gate A | PASS、15登録・11 OPEN |
| 汎用Gate B | FAIL、B6（FAILED 0）はPASS |
| 新規の独立反例・改変検査 | 43/43成功。後述の対象外残課題1件は別に記録 |

結果: [CD判定](../../results/cd2-independent-20261116/cd-run/acceptance.json)、
[全テスト](../../results/cd2-independent-20261116/all-tests.log)、
[Gate A/B](../../results/cd2-independent-20261116/gates.log)、
[独立反例](../../results/cd2-independent-20261116/replay-current/probes.json)。

## 版と差分

CD-1終了時の312ファイル集合SHA-256
`94adb81b77fa0e43df02f1a17bb963ced920448e3c1b1a6133511f2cbe718538`
を起点に照合した。既存ファイルの変更は9件、新規ソースはテスト1件。
全件の変更前後SHA-256は [changes-from-cd1.json](../../results/cd2-independent-20261116/changes-from-cd1.json)。

| ファイル | 内容・確認結果 |
|---|---|
| `src/jclprof/parser/parser.py` | 領域終端集約、JOB開始時の領域index記録、JOB文置換順序、メンバーPEND保持を追加。指定修正に対応 |
| `src/jclprof/parser/model.py` | 末尾の任意フィールドprocedure_end、JSONキーprocedure_end_idを追加。既存位置引数をずらさない |
| `src/jclprof/harness/hierarchy.py` | 最初のメンバーPENDの参照所有者をMEMBERとし、実リンクをtreeへ追加。検査免除なし |
| `src/jclprof/harness/carddemo_source.py` | source_viewが実procedure_endリンクをたどる。期待値・flatからPENDを補完しない |
| `tests/harness/test_hierarchy_harness.py` | 台帳ロジック用のin-memory OPEN例と、現在のCardDemo違反集合emptyへの更新。変異検査を維持 |
| `tests/harness/test_carddemo_source.py` | 実測不一致と承認状態の分離を、明示的なsource/trace FAIL入力で検証。実際のreviewsは更新しない |
| `tests/KNOWN_DEFECTS.yaml` | 3件をRESOLVED_PENDING_REVIEW、残るPROC形をH02B OPENへ分割。除外・CLOSED・承認付与なし |
| `tests/CHANGES.md` | TC-018/019。既存3テストの前提変更と新規13テスト、検査器変更を記録 |
| `CLAUDE.md` | 進捗記録をCD-2独立再検証待ちへ更新 |
| 新規 `tests/parser/test_cd2_source_fixes.py` | 13件。今回の全テスト再実行で全成功 |

ADR-031と実装報告も読んだ。source集合外の設計資料として扱い、今回の検証開始時ハッシュに含めた。
期待値・Generic Gateコード・Lexer・既存Goldenには変更がない。
このレビューでは実装、テスト、台帳、既存報告を編集せず、結果と本報告のみを追加した。

## 3修正の確認

### A10 — Job.span

close_jobはJOB開始時点のfirst_region以降の領域終端を集約し、_region_endは実データ・自身のdelimiter・全候補を対象とする。
NEXT_STATEMENTの開始行はその領域の所有終端へ含めない。
MNTTRDB2は[1,28]から[1,30]へ変わり、他の45 JOBのspanは不変。全46件が独立CD-1期待値と一致した。

独立入力ではDD *のEOF、暗黙SYSINのEOF、DD DATA内の見かけのJOB行、空データ、空delimiter、
直後の次JOB、異なる領域を持つ2 JOB、データ後のコメント/nullをJES2/JES3/UNKNOWNそれぞれで照合した（27件）。
UNDETERMINED領域の候補最大終端も別に確認した。
実装側の領域終端関数を正解計算に再利用していない。期待範囲は合成入力の物理行から明示した。

Job.spanはIBMのデータ構造ではなく、ADR-027・CA-14が定義するプロジェクトのsource範囲契約である。
データ終了のIBM規則と、このsource包含契約を区別する。
根拠はrules.yamlのJCL-DD-003〜006（SA23-1385-70、印刷p.95/97/121/159–160）、CA-14。
今回のオンライン確認では登録済み3.2 Reference PDFの取得が403となり、全文再取得はできなかった。
補足として公式の[旧版ReferenceのOmitted Data Delimiters](https://www.ibm.com/docs/en/SSLTBW_2.2.0/pdf/iea3b611.pdf)でも、
暗黙SYSINと入力終了に関する同じ規則を確認した。旧版を3.2全体の代わりにしたものではない。

### H01 — JOB statementの参照

limitations付与のreplace後の文をコンテナーとflatの双方が使う順序になった。
全46 JOBで`job.job_statement is flat_statement`が成立し、シンボル付き2 JOBの独立入力でもlimitationsを保持した。
treeのJOB文だけをlimitationsのない古いコピーへ差し替える変異はH-REF-01で引き続き検出した。
チェック器側の例外化によるPASSではない。根拠はCA-13/14の同一source文と参照一貫性であり、IBMがPythonのobject同一性を規定するわけではない。

### H02 — カタログPROCメンバーPEND

REPROC 29行、TRANREPT 79行のPENDは、実procedure_endからflatと同一の文オブジェクトへ到達する。
最後のEXECのother_statementsにもoutsideにも入らない。
PEND省略時はNone、インストリームPROCは従来のProcDefNode.pend_statementのまま。
両実資産で、リンク削除、最後のSTEPへの移動、STEPとの二重所属、異なるspanのPENDコピーへの差替えを実施し、
全8変異をCDのsource/traceのいずれかで検出した。到達行が同じでSOURCEだけでは分からない所有者異常も、TRACEの所有検査が検出した。

PROCルート所有はADR-031・ユーザー指定に沿うAST設計である。
IBMはカタログPROCのPENDを省略可能とし、プロシージャ末尾の構文としている。
[IBM z/OS 3.2 JCL User's Guide「Identification of procedure」](https://www.ibm.com/docs/SSLTBW_3.2.0/pdf/ieab500_v3r2.pdf)。
IBMがこのASTフィールドそのものを指定するわけではない。
H02Bの「インストリームPROCの最初のEXECより前の文／孤立PEND」は未修正として分離され、CardDemoに該当形がないことと整合する。

## 独立なbefore/after再実行

[probe_cd2.py](../../results/cd2-independent-20261116/probe_cd2.py) は合成入力を独立に記述した検証スクリプト。
保存済みsnapshot-startの旧Parser/Lexer/Modelを別プロセスでimportし、旧版のParserハッシュがCD-1保全記録と一致することも確認した。
旧版へ現行Modelを混在させていない。

- 修正前で実行可能な共通33項目: 18成功、15失敗。
- 現行での共通33項目と追加の実PROCリンク/改変10項目: 43成功、0失敗。
- 原本48件の旧版・現行to_dictとJOB object同一性も別々に記録。
- 原本由来の正解はCD-1の凍結済み期待値。before/afterのactual同士は影響差分を調べる目的に限り、正解データに転用していない。

実装者の「13テストを修正前に書き、12失敗だった」という作業時系列は、この場では直接観察できない。
今回の旧版再実行は独立反例による再現であり、その時系列を証明するものではない。

## 残課題・説明上の補足

### CD2-R01 — LOW: 「AST JSONが変わるのは3件」の説明が不正確

現行to_dictは全input_kindでprocedure_end_idキーを出力するため、**文字通りのJSON比較では48/48件が変更**される。
旧版に欠落していたキーをnullとみなせば、意味のある差分はMNTTRDB2のspanと2 PROCのPENDリンクの3件となる。
新規キーを除いた残りの差分はMNTTRDB2のspanだけだった。
[ast-differences.json](../../results/cd2-independent-20261116/ast-differences.json) に全48件の差分を記録した。

修正案: 実装報告に「新規nullableキーの追加を除いたAST内容の変更」と比較方法を明示する。
JSONのschema_versionは1のままであり、キー集合を厳密に固定している外部利用者には追加キーも影響する。
今回、そのような利用者の存在は確認していない。プロジェクトのCD-1/genericスイートには実測回帰がなく、CD-2の修正阻害とはしない。
検証方法: probe_cd2.pyのbefore/current ASTをリプレイして再帰比較する。IBM根拠は該当せず、シリアライズ契約上の説明事項である。

### CD2-R02 — MEDIUM、CardDemo対象外: UNDETERMINED候補のspan破損を汎用checkerが見逃す

入力（jes=UNKNOWN）:

```jcl
//J JOB
//S EXEC PGM=X
//IN DD *,DLM=AA
 D
//OTHER DD DUMMY
AA
```

ParserのJob.spanは正しく[1,6]。メモリー上で[1,3]へ縮めても、check_hierarchyは違反リスト[]を返した。
_check_spansはg.recordsと直接のdelimiterを検査するが、g.candidatesを集約しない。
**Parser修正の失敗ではなく、既存の汎用検査の感度不足**である。
今回のhierarchy.py差分はこの関数を変更しておらず、CD-2が導入した回帰とは判定しない。
CardDemoにはDLMがなく、本件はCD-2のCardDemo修正のPASSを阻害しない。A11全般の検査完全性を保証する際は残る。

証拠: [unknown-span-mutation.json](../../results/cd2-independent-20261116/unknown-span-mutation.json)。
再現スクリプト: [probe_unknown_span.py](../../results/cd2-independent-20261116/probe_unknown_span.py)。
根拠: JCL-DD-005のJES別解釈と、今回A10修正が採用する候補全体のsource包含契約。
IBMの実行意味とUNKNOWN時の候補保存方針は区別する（UNKNOWNという解析モード自体はプロジェクト設計）。
修正案: 汎用checkerで各候補のrecordsと自身のdelimiterの終端を包含検査し、候補spanだけを縮める変異テストを追加する。
検証方法: 上記変異にH-SPAN-02等を要求し、既存A02を修正済みと誤認しない。今回はコードを変更していない。

## skip・xfail・未実装と正式受入れ

- pytest skip52 = GoldenのNOT_IMPLEMENTED49 + BLOCKED2 + symlink権限1。
- pytest xfail9 = D-1〜D-3の再現。A10の旧2 xfailは通常成功へ変化。
- Golden runnerは51 PASSED / 49 NOT_IMPLEMENTED / 2 BLOCKED / FAILED0。
- 汎用pendingは5 PASSED。CD専用48件は全実行、skip/xfail/NOT_IMPLEMENTED/BLOCKED各0。
- CD期待値48件は全PENDINGのまま。CD-ASSURANCEの未承認と実測PASSを混同していない。
- 汎用Gate Bにはレビュー・承認・scope以外にも、NOT_IMPLEMENTED30、BLOCKED2、xfail9、
  未CLOSED欠陥15、階層未検査29等の阻害が残る。B6だけが改善したことを確認した。

## 保全と再現

CD-1のexpectations.jsonはSHA-256
`fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a`
のまま。reviewsは48 PENDING。既存Golden102件・195物理ファイル、原本240件をCD-1と照合し、内容変更なし。
今回の検証開始・終了間で原本のsize/mtime_ns/SHA-256も不変である。
実装者の作業前mtimeについては、この独立レビュー開始時点から遡って同じ比較を観察したわけではない。
[preservation.json](../../results/cd2-independent-20261116/preservation.json) と
[source-baseline.json](../../results/cd2-independent-20261116/source-baseline.json) に現行版を固定した。
現行ソース集合は313ファイル、SHA-256は
`b3b96a54728b9a4b74f2792a7396b47c02a2ade19c3ec603f739e7ce104f8aed`。
GitコミットIDはない。成果物は [artifact-manifest.json](../../results/cd2-independent-20261116/artifact-manifest.json) でハッシュ化する。

```powershell
.venv/Scripts/python.exe tools/carddemo_source_acceptance.py --corpus D:/projects/aws-card/aws-mainframe-modernization-carddemo/app --output results/cd2-independent-recheck/cd-run
.venv/Scripts/python.exe -m pytest tests -q -rsxX -p no:cacheprovider
.venv/Scripts/python.exe tools/quality_gate.py --gate acceptance --output results/cd2-independent-recheck/gates
.venv/Scripts/python.exe results/cd2-independent-20261116/probe_cd2.py --before --output results/cd2-independent-recheck/before
.venv/Scripts/python.exe results/cd2-independent-20261116/probe_cd2.py --output results/cd2-independent-recheck/current
```

CD専用CLIと汎用Gate Bの終了コード1は現状の受入れFAILを正しく表す。
再検証を完了し、実装・台帳・期待値・承認情報には手を加えず停止する。

# CD-1 — CardDemo Source Structure Acceptance

作業日: 2026-11-15。実施者: Codex。対象: CA-01〜03、CA-13〜14。

## 判定

**全48ファイルを再現可能に検査する仕組みは実装・検証済み。CardDemoの正式受入れはFAIL。**
実測不一致と未承認期待値は別の項目として記録した。期待値をParser出力へ合わせる修正、Parser修正、承認・封印は実施していない。

| 判定 | 結果 | 根拠 |
|---|---|---|
| CD-SOURCE | FAIL | 45 PASS / 3 FAIL。A10が1ファイル、H02が2ファイル |
| CD-TRACE | FAIL | 全48 FAIL。H01が46件、H02が2件、A10が1件の計49指摘 |
| CD-ASSURANCE | PENDING | 全48期待値が未承認。変異1501/1501検出、逃避0 |
| 正式受入れ | FAIL | 上記3ゲートの全PASSが必要 |
| Gate A | PASS | 開発健全性。既知欠陥を含むことを明示した従来判定 |
| 汎用Gate B | FAIL | 従来の正式受入れ条件・対象範囲を維持 |

機械可読な全48件の結果は [acceptance.json](../../results/cd1-20261115/run/acceptance.json)、
人向け一覧は [acceptance.md](../../results/cd1-20261115/run/acceptance.md)、
変異結果は [mutations.json](../../results/cd1-20261115/run/mutations.json) に保存した。
PENDINGは「検査未実行」でも「Parserが不合格だったため承認を取り消した状態」でもない。
検査は48件全て実行済みで、期待値に対する人の承認が未実施という状態である。

## 起点と保全

起点は前回照合の302ファイル、集合SHA-256
`86878b6588133f6f796b104f8359e5c11e0c7f48f896fe9a5f7345a64bd50b4b`。
パスと各ファイルSHA-256を用いた前回と同じ方式で照合した。Gitリポジトリーではなく、コミットIDはない。
最終的な差分・保全検査は [preservation.json](../../results/cd1-20261115/preservation.json)、
作業後のソース集合は [source-baseline.json](../../results/cd1-20261115/source-baseline.json) に記録する。

作業後は312ファイル、集合SHA-256は
`94adb81b77fa0e43df02f1a17bb963ced920448e3c1b1a6133511f2cbe718538`。
最終照合で保全対象444ファイルの変更・追加・削除はいずれも0だった。
報告書と検証成果物のハッシュは [artifact-manifest.json](../../results/cd1-20261115/artifact-manifest.json) に別記する。

- 原本全240ファイル、既存Goldenの195物理ファイル（102ケース）、Parser/Lexerの9 Pythonファイルをハッシュ照合する。
- Parser adapterを含めて変更なし。既存テスト、既存Golden期待値、既存汎用pending 5件、Gate A/Bのコード・設定も変更なし。
- 既存302ファイルの変更は変更履歴 `tests/CHANGES.md` のTC-017追記のみ。追加物は専用Harness、ツール、テスト、未承認オラクル。
- PROC Resolver、意味解析、汎用JCL機能の追加は実施していない。

## 独立期待値と対象範囲

新規スイートは [tests/golden_pending/carddemo_source](../../tests/golden_pending/carddemo_source/README.md)。
既存のsealed 102ケースと汎用pending YAML 5ケースには混ぜず、専用JSONの未封印スイートとした。
期待値の初回生成SHA-256は以下で、比較器の調整後も変更していない。

`fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a`

源泉の独立inventory.jsonのSHA-256:
`bc56e8fd040b0142d3ebcf2f7b5eec65dcada5c29934f7bebbdddbf2b4d6889e`。

| 対象 | 独立期待値と比較対象 |
|---|---|
| 48パス・内容 | 大文字小文字の拡張子を含む全46 JOB / 2 PROC。追加・欠落・内容変更はBLOCKED |
| source階層 | JOB内119 STEP + PROC内4 STEP = 123。JOB側480 DD + PROC側20 DD = 500。JOBレベルDD3件を保持 |
| 操作文 | JOB46、EXEC123、DD500、SET5、JCLLIB3、PROC2、PEND2、計681。全原表記・値・位置も照合 |
| DD連結 | 無名DD24件、19グループ。所属と順序・完全修飾名を照合 |
| インストリーム | 91件、データ635行。明示delimiter83、次のJCL文による終了7、EOF終了1。領域・所有DD・終了理由・境界を照合 |
| レコード | 3046物理レコード。原文SHA、バイト範囲、改行、役割、操作文への所属、データDDへの所属 |
| 位置 | 全トークンの全segments、名前/operation欄、全パラメーターの原表記・開始位置・再帰値構造 |
| 親子・参照 | 既存check_hierarchyも実行。既知欠陥を免除せず、treeからの全操作文到達性を独立期待値と照合 |

作者ツール [build_carddemo_source.py](../../tools/golden_authoring/build_carddemo_source.py) は標準ライブラリーのみを用い、
原本バイト列と固定済みinventoryのハッシュ・文フィールド・継続・パラメーターを再照合した。
Parser/Lexer/Harnessをimportせず、actual出力を入力する経路を持たない。既存出力ディレクトリーへの上書きも拒否する。
IBM根拠は [規則レジストリー](../../specs/rules.yaml) と
[受入契約](carddemo-acceptance-contract.md) のJCL-REC-001〜003、JCL-CONT-001、
JCL-DD-001/003/006、JCL-PROC-002/004。物理レコード、継続、DD連結・データ、PROC/PENDのsource構造を対象とする。
今回IBM仕様全体を新たに監査・実装したことを意味しない。

**独立性の限界:** inventory、期待値記述ツール、CD検査器の作者は同じCodex。
Claudeによる既存Parser/Harnessの出力から期待値を作ってはいないが、相互に同じ誤解を共有する可能性がある。
作者が既存ASTの公開形式を理解していることも、完全な盲検ではない。
自動的な正解データの記述を、人の原本レビューや正式承認の代替にしない。
48件のreviews.jsonは全てPENDING、reviewed_by/atは未設定。期待値SHAと承認を結び付けている。

[review-packet.md](../../results/cd1-20261115/review-packet.md) に全48階層・連結・データ範囲のレビュー用一覧を作成した。
これは期待値の可読表示であり、第2の独立オラクルではない。人は元の原本とIBM根拠を照合して承認する必要がある。
期待値訂正が必要なら旧版を保存し、根拠を示した別版としてレビューする。失敗結果に合わせる自動再生成は禁止する。

## Harnessへの実装

[carddemo_source.py](../../src/jclprof/harness/carddemo_source.py) は既存Comparatorのstatements/hierarchy比較と
既存階層不変条件を利用する。新たなParserや意味解決器を実装していない。
原本ハッシュ不一致は解析前にBLOCKEDとする。スコープ外の新規JCL/PROCファイルの出現も全スイートをBLOCKEDにする。
未比較項目、構文ERROR診断、欠落した比較対象を成功として扱わない。

actualの階層射影は実ASTのリンクだけをたどり、欠落PENDをflat一覧から補充しない。
汎用hierarchy_viewの連結先は正規化DD名なので、CD射影では実DDNodeのprocstepとconcat_headだけから原本の完全名へ変換した。
期待値からの補完もPROC展開も行わない。
DATA行の所有DDと、操作文/継続行の論理文所有者は別に比較する。
初期比較でこの2つの表現差に由来する誤検出を確認し、actual射影・比較側を修正した。凍結済み期待値には変更を加えていない。

CA-13について、Valueの開始位置だけでなく全文を原本と比較し、末尾までの列範囲をLexerの全segmentsで照合する。
継続STRINGを先頭だけで比較する汎用traceの残課題を修正したわけではない。CardDemoの観測構文では全セグメントを検査し、
値のraw textやsegmentの意図的な破損を検出するテストを追加した。引用符内の物理継続は本原本では0件で対象外である。

CD-SOURCE/TRACEの実測結果は承認状態と分離する。CD-ASSURANCEは変異感度が合格しても承認が不足すればPENDING。
専用CLIは3判定の全PASSのみ終了コード0。現在の終了コード1は既知不一致を隠さない意図どおりの結果である。
既知欠陥台帳やcase IDによる許容をCD検査には適用しない。

## 検出したParser欠陥とH01〜H03

| ID | 実測・再現 | CD-1への影響と修正要求 |
|---|---|---|
| A10 | `app-transaction-type-db2/jcl/MNTTRDB2.jcl`。DDは28行、データ29〜30行。期待Job.span=[1,30]、actual=[1,28] | CD-SOURCEとCD-TRACEを阻害。末尾データまでJobのsource範囲へ包含するParser修正が必要。今回修正せず |
| H01 | 46 JOB全て。`H-REF-01`: treeのjob_statementとflatのJOB文のlimitationsが不一致 | CD-TRACEを阻害。単なる実行時意味解析の未実装とは分け、同一source文のAST表現を一貫させる必要がある。台帳のLOWを理由に免除しない |
| H02 | `proc/REPROC.prc`29行、`proc/TRANREPT.prc`79行。PENDがflatには存在するがtreeから到達できない。`H-OWN-02` | CD-SOURCEとCD-TRACEを阻害。source PROCコンテナーからPENDを適切に参照可能にする修正が必要。PROC Resolverは不要 |
| H03 | 最初のJOBより前のSTEP配下DD等がtreeから欠落する問題。本48原本にはその入力形がない | **今回のCD-1では対象外**。原本固定・追加検出が前提。修正済み・汎用受入れ合格とはしない。汎用Gate Bでは引き続きOPEN |

H02のチェック器の現行メッセージには「expected under STEP」が含まれるが、これは既存不変条件の表現である。
独立期待値が要求するのはPENDのsource到達性であり、PENDを意味的に最後のEXECへ所属させる設計を承認したものではない。
修正時はPROCルートのsource所有モデルをレビューする必要がある。
これら以外の観測された値、レコード、字句位置、連結、データ境界に実測差分はなかった。
ただし未承認Goldenへの一致を正式な正しさの保証へ昇格させない。

## 意図的異常注入

[carddemo_mutations.py](../../src/jclprof/harness/carddemo_mutations.py) はメモリー上の不変ASTを置換して実施。
原本、Parser、期待値を変更しない。既存不一致のfingerprintを差し引き、**独立SOURCE期待値との新しい差分**が必要。
単にH01/A10/H02が残っていることや、TRACEだけの失敗は検出成功に数えない。

| 操作 | 注入数 | 検出数 |
|---|---:|---:|
| JOB削除 | 46 | 46 |
| JOB移動 | 46 | 46 |
| STEP削除 | 123 | 123 |
| STEP移動 | 123 | 123 |
| DD削除 | 500 | 500 |
| DD移動 | 500 | 500 |
| DD連結順序の変更 | 24 | 24 |
| データ境界の変更 | 91 | 91 |
| Job.span縮小 | 46 | 46 |
| PROCルート削除 | 2 | 2 |
| **計** | **1501** | **1501** |

全48ファイルを変異の主対象として実行済み。全原本が1 JOBずつなので、JOB移動は別ファイルへ移す異常として設計した。
STEP/DD移動も所有コンテナーの誤りを検査する。データ境界変更は領域だけでなく関連inline参照・record役割も整合させ、
単純な内部不整合だけに依存しない検出とした。A10の実不一致と同一の変更を再注入するだけのno-opは成功に数えないことも単体検証した。
これは列挙した変異への感度を示すもので、あらゆる誤ASTの完全検出を証明するものではない。

## 検証結果と再現

- 全tests: **397 passed / 52 skipped / 11 xfailed**。新規Harnessテスト23件は全成功、skip/xfailなし。
- Gate Aのruff成功、mypy 82ソースファイル成功、既存Golden定義102件とMANIFEST整合成功、規則同期成功。
- 既存sealed Golden: 49 PASSED / 2 FAILED / 2 BLOCKED / **49 NOT_IMPLEMENTED**。
- 既存汎用pending: 4 PASSED / 1 FAILED。新しい専用48件はこの5ケースの件数へ混入させていない。
- skipはHarnessのsymlink作成権限1件とAnalyzerの51件。xfailはAnalyzerの11件。
  NOT_IMPLEMENTEDはGolden runnerの状態であり、pytestのskip/xfailとは別の指標である。相互に足し合わせない。
- Gate Bは未CLOSED欠陥、11 xfail、未承認83/83、対象内NOT_IMPLEMENTED30、BLOCKED2、FAILED3、
  汎用pending5、階層未検査29、scope PROPOSED等によりFAIL。Gate AのPASSは正式受入れを意味しない。
- CD専用実行: 対象48/48、入力全MATCHED、skip0、xfail0、NOT_IMPLEMENTED0、BLOCKED0。
  構造FAIL3、traceの49指摘、期待値PENDING48をそれぞれ独立に報告した。

```powershell
.venv/Scripts/python.exe tools/carddemo_source_acceptance.py --corpus D:/projects/aws-card/aws-mainframe-modernization-carddemo/app --output results/cd1-recheck
.venv/Scripts/python.exe -m pytest tests/harness/test_carddemo_source.py -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest tests -q -rsxX -p no:cacheprovider
.venv/Scripts/python.exe tools/quality_gate.py --gate acceptance --output results/cd1-recheck-generic
.venv/Scripts/python.exe tools/carddemo_source_review_packet.py --output results/cd1-review-packet.md
```

最初と4番目のコマンドは現状で終了コード1が正しい。期待値の作者ツールを再実行する必要はない。
全テスト記録は [all-tests.log](../../results/cd1-20261115/all-tests.log)、
Gate A/Bは [generic-gates.log](../../results/cd1-20261115/generic-gates.log)。

## 残る正式受入れ阻害事項

1. A10、H01、H02のParser修正と独立再検証が必要。今回の作業では修正していない。
2. 全48期待値の原本・IBM根拠に対する人のレビューと承認が必要。全PENDINGを保持した。
3. ここでの3ゲートはCD-1のsource限定判定。CA-15の展開後trace、CD-RESOLVE、CD-SEMANTICSは未着手であり、この結果から合格とはしない。

CD-1の実装・検証はここで停止する。欠陥修正、承認情報の付与、既存Goldenへの移植・封印は実施しない。

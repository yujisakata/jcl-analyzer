# 現在ベースラインの照合結果

調査日: 2026-11-15（JST）。対象: `D:\projects\jcl-profiler`。

**判定: CONDITIONAL — CardDemo受入基準を実装する出発点として採用可能。ただし、現状をParserの受入済み版、またはA11全体の解消済み版とは扱わない。** 実装・テスト・設定の302ファイルをSHA-256で固定し、本調査中の変化がないことを確認した。Gitリポジトリは存在しないためコミットIDはない。今回Gitの初期化・コミットはしていない。

実装集合の識別値（計算法は§8）:

```text
86878b6588133f6f796b104f8359e5c11e0c7f48f896fe9a5f7345a64bd50b4b
```

本調査では原本・Parser・Harness・既存テスト・Golden期待値を編集せず、変更の取消しも行っていない。既存の検証成果物を上書きしないよう、新しい実行結果は全て [results/baseline-reconciliation-20261115](../../results/baseline-reconciliation-20261115/) に保存した。以前の監査・契約書も書き換えていない。

## 1. 調査対象と差分の確定

Q11の [preservation.json](../../results/carddemo-contract-20261115/preservation.json) は、既存6ファイル変更と15ファイル追加を記録している。追加のうち `docs/reviews/carddemo-acceptance-contract.md` はCodex自身の依頼成果物であり、除外すると**調査対象は変更6＋追加14＝20ファイル**である。

今回はその20件を全て確認した。その後もR1の作業が続いた結果、契約書調査開始時のbefore.jsonに対する**今回調査開始時点の差分は既存15変更＋22追加**だった。このうち1追加は上記Codex契約書。したがって実装担当側のR1関連差分は**15変更＋21追加＝36件**であり、Q11後の追加分は9変更＋7追加＝16件である。本書と今回の調査用成果物は、この差分集計の後に作成したものなので分母に含めない。

証拠:

- [changes-from-contract-start.json](../../results/baseline-reconciliation-20261115/changes-from-contract-start.json): 調査開始時に採取した差分一覧。
- [file-differences.json](../../results/baseline-reconciliation-20261115/file-differences.json): 全件の変更前後SHA-256、追加/削除行数、Q11対象かどうか、ファイル時刻。
- [diffs](../../results/baseline-reconciliation-20261115/diffs/): 個別のunified diff。追加ファイルは `/dev/null` との差分。
- [snapshot-start](../../results/baseline-reconciliation-20261115/snapshot-start/): 今回の実行前に保存したソース・テスト・設定・文書の内容コピー。

変更前の内容をハッシュだけから推測して差分化していない。Q11の既存6件は `jcl-profiler.7z` から結果ディレクトリへ展開した旧内容がbefore.jsonのハッシュと**全件一致**した。追加で発見した既存変更も、12件はアーカイブ、CLAUDE.mdとparser-defects-04b.mdは対象プロジェクトのClaudeファイル履歴、CHANGES.mdは追記前の完全なprefixを復元し、計15件全てbefore.jsonのSHA-256一致を確認した。原ファイルへ復元したものはない。

## 2. Q11で変更された既存6ファイル

時刻は2026-11-15のJST。操作時刻の詳細・mtime・機構は [origin-verified.json](../../results/baseline-reconciliation-20261115/origin-verified.json) を参照する。mtimeだけから作成者を決めたものではない。

| ファイル・正確な差分 | 変更前→変更後 / 機能的影響 | 関連する現行テスト・検証 | 操作時刻 |
|---|---|---|---|
| [harness/adapters.py.diff](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/adapters.py.diff) | +3/-0。AdapterOutputにinvariantsを追加。従来はview/diagnosticsだけで、木の不整合をRunnerへ渡す経路がなかった | test_hierarchy_harness::test_invariant_violation_fails_the_case_even_if_expectations_match、既存Runnerテスト | 20:51:35 |
| [harness/comparator.py.diff](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/comparator.py.diff) | +34/-0。順序付きの再帰的hierarchy比較を追加。期待値にhierarchyがなければ互換性を保ってuncheckedにする。従来の平坦比較自体は維持 | test_hierarchy_comparison_reports_paths、test_hierarchy_not_expected_is_reported_unchecked、M1〜M7 | 20:51:35 |
| [harness/runner.py.diff](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/runner.py.diff) | +15/-1。invariant違反をDifferenceとして加え、期待値の一致だけではPASSEDにしない。部分scopeのnode IDによる選別を追加 | 上記Runner検査、既存test_runner、今回の実Adapter→Runner異常注入 | 20:51:35 |
| [harness/trace.py.diff](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/trace.py.diff) | +20/-1。値の先頭1文字照合から全文照合へ強化。ただし継続STRING/LIST/KWSUBのfallbackには制約が残る（§5） | test_trace_checks_whole_value_text、test_trace_accepts_apostrophe_continuation、M5c、今回の継続後半改変 | 20:51:35〜48 |
| [parser/adapter.py.diff](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/parser/adapter.py.diff) | +58/-1。hierarchy_viewを追加し、SyntacticAdapterが木の出力とcheck_hierarchyを実行。Parser本体の構文認識・AST構築は変えていない | pending5件、test_hierarchy_harness、今回の同一削除注入、全CardDemoの比較 | 20:52:00〜09 |
| [golden-schema.json.diff](../../results/baseline-reconciliation-20261115/diffs/specs/golden-schema.json.diff) | +260/-0。hier_dd/step/proc/job/hierarchyの定義を追加し、statements viewで任意のhierarchyを許容。既存期待値を強制的に書き換える変更ではない | Golden既存102件・pending5件の定義検査、既存Loader/Comparatorテスト。新定義の全不正入力境界まで独立保証したものではない | 20:52:29 |

## 3. Q11で追加された14ファイル

全てbefore.jsonに存在せず、差分は全行追加。既存封印済み `tests/golden/` への変更とは区別する。以下の差分リンクは省略なしの内容を含む。

| ファイル・差分 | 追加内容 / 機能的影響 | 関連するテスト・検証 | 操作時刻（JST） |
|---|---|---|---|
| [harness/defects.py](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/defects.py.diff) | 119行。既知欠陥台帳の読取、署名照合、Golden/xfail ID対応。登録は欠陥修正を意味しない | test_registry_loads_and_explains_only_open_signatures、test_registry_rejects_invalid_entries、test_gates | 20:50:54 |
| [harness/hierarchy.py](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/hierarchy.py.diff) | 376行。平坦文からの所属参照モデルと、親子/順序/連結/対象/span/レコード整合性検査。誤った平坦文そのものをIBMの意味へ復元する検査ではない | test_hierarchy_harness、test_hierarchy_properties、mutation、今回の独立注入 | 20:49:07〜20:57:14 |
| [harness/mutations.py](../../results/baseline-reconciliation-20261115/diffs/src/jclprof/harness/mutations.py.diff) | 238行。メモリ上のASTにM1〜M7、整合変異M5c/M6cを適用。原本やParserは変えない | test_required_mutation_is_rejected_by_invariants_and_by_golden等、mutation report | 20:54:23〜38 |
| [KNOWN_DEFECTS.yaml](../../results/baseline-reconciliation-20261115/diffs/tests/KNOWN_DEFECTS.yaml.diff) | 120行。A01〜A11とH01〜H03。現状13 OPEN、A11だけRESOLVED_PENDING_REVIEW。Golden3失敗とxfail11を説明する台帳 | registry/gatesテスト、全Corpus違反の登録照合 | 20:51:10〜21:00:04 |
| [pending/cases/job_exec_dd.yaml](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/cases/job_exec_dd.yaml.diff) | 275行。G-HIER-001/005。複数JOB・JOBLIB・STEP/DD・PROCのsource階層期待値。draftで未封印 | pending実行、階層比較/変異テスト | 20:53:36〜48 |
| [pending/cases/dd_concatenation.yaml](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/cases/dd_concatenation.yaml.diff) | 127行。G-HIER-002。連結と先行DDのない名前なしDDを区別する期待値 | 同上 | 20:53:36〜48 |
| [pending/cases/instream_data.yaml](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/cases/instream_data.yaml.diff) | 245行。G-HIER-003/004。明示/暗黙データ、DD DATA、EOFを含む期待値。004はA10により現在FAILED | pending実行、境界/変異テスト | 20:53:36〜48 |
| [inputs/h001.jcl](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/inputs/hierarchy/h001.jcl.diff) | 12行。2 JOB、JOBLIB連結、3 STEP。M3の別JOB移動を適用可能にする合成入力 | G-HIER-001、M1〜M7 | 20:53:01 |
| [inputs/h002.jcl](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/inputs/hierarchy/h002.jcl.diff) | 10行。DD連結と新STEP先頭の名前なしDD | G-HIER-002 | 20:53:01 |
| [inputs/h003.jcl](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/inputs/hierarchy/h003.jcl.diff) | 14行。DD *、暗黙SYSIN、DD DATA中の//JOB | G-HIER-003、M6/M6c | 20:53:01 |
| [inputs/h004.jcl](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/inputs/hierarchy/h004.jcl.diff) | 5行。DD DATAのEOF。期待Job.spanは1〜5、実装は1〜3 | G-HIER-004、A10 | 20:53:01 |
| [inputs/h005.jcl](../../results/baseline-reconciliation-20261115/diffs/tests/golden_pending/inputs/hierarchy/h005.jcl.diff) | 8行。PROC/PEND、位置指定とPROC=の呼出し | G-HIER-005 | 20:53:01 |
| [make_pending_hierarchy.py](../../results/baseline-reconciliation-20261115/diffs/tools/golden_authoring/make_pending_hierarchy.py.diff) | 198行。ソース内に記述した手書き期待値からpending YAMLを書き出す。Parser呼出しによる生成はない。今回はこの生成コマンドを実行していない | pending定義検査、各階層テスト。期待値の作者がParser/Harnessと同じという独立性の制約は残る | 20:53:34〜46 |
| [hierarchy_mutation_report.py](../../results/baseline-reconciliation-20261115/diffs/tools/hierarchy_mutation_report.py.diff) | 122行。既存Golden・pending・CardDemoに変異を適用して検出率を集計。既知違反を新規検出と数えない | 品質ゲートのhierarchy-mutation、今回943変異の再実行 | 20:55:04 |

pendingの5期待値はClaude（claude-opus-5-5）が作成し、同じ担当者が実装・検査も作成したことがコード・README・R1報告に明記されている。「既存Parser出力をコードで採取して期待値にする処理」は当該authoringスクリプトにはないが、人が実測結果から影響を受けていないことまで証明できない。draftを承認済み独立Goldenとは扱わない。

## 4. Q11後に増えた変更と変更元

### 4.1 追加で確認した16件

各差分は同じdiffsディレクトリの同一相対パスに保存した。ここでも既存ファイルは全て旧ハッシュ一致の内容と比較している。

| 種別 | ファイル | 内容・関連検証 |
|---|---|---|
| 変更 | tools/quality_gate.py（+166/-77） | Gate A/B実行、台帳・pending・変異・xfail分類を追加。今回はacceptance指定でA/B両方を実行 |
| 変更 | tests/harness/test_harness_cli.py（+7/-2） | FAILED=0固定から「FAILEDは登録済みIDのみ」へ変更。CLI自体は失敗ケースがあれば終了1を検査 |
| 変更 | tests/parser/test_golden_parser.py（+13/-1） | 登録済みGoldenをstrict xfailにする。G-IS-006/007が追加xfail。skipとは別 |
| 変更 | tests/CHANGES.md（+4/-0） | TC-013〜016に判定変更・trace・pending・新テストの説明 |
| 変更 | docs/decisions.md（+21/-0） | ADR-027/028（階層とゲート分離） |
| 変更 | docs/golden-view.md（+38/-0） | hierarchy出力とJob.spanの契約 |
| 変更 | docs/requirements.md（+2/-0） | 上記2 ADRを変更履歴に追加 |
| 変更 | docs/reviews/parser-defects-04b.md（+4/-4） | 設計案のADR番号を029/030へ繰り下げ。Parser修正は未実施という状態は維持 |
| 変更 | CLAUDE.md（+7/-2） | R1レビュー待ち、Gate A/B、pending/台帳のルールを追記 |
| 追加 | src/jclprof/harness/gates.py | Gate Aの既知失敗/xfail分類、Gate BのB0〜B9判定。test_gatesが検証 |
| 追加 | tests/ACCEPTANCE_SCOPE.yaml | lexical/syntacticの受入範囲。PROPOSEDで除外は無効。CardDemo契約を反映した承認済み範囲ではない |
| 追加 | tests/harness/test_gates.py | Gate A分類、B0〜B9の判定を18ケースで検査 |
| 追加 | tests/harness/test_hierarchy_harness.py | 階層、Comparator、Runner、台帳、CardDemoへの23ケース |
| 追加 | tests/property/test_hierarchy_properties.py | 未登録違反の検査と生成した複数JOBの変異検出（2テスト、最大400/150例） |
| 追加 | tests/golden_pending/README.md | draft、同一作者、未封印、承認後の手順を明示 |
| 追加 | docs/reports/r1-harness.md | 実装担当者のR1自己報告。今回の検証結果と照合したが、自己報告だけを監査の正解にはしていない |

### 4.2 変更元と時期

同プロジェクトのローカルClaude Codeセッション記録を、関係するWrite/Edit/Bash操作に限って調べた。

- セッション: `3097c724-28db-4848-82ce-45d8cc9500a8`。
- 記録上のモデル: `claude-opus-5-5`。
- 20:43:43 JSTに、A11を対象とするR1依頼、Gate A/B分離、A01〜A10を修正しない等の制約を含むユーザーメッセージがある。一部日本語はログ内で文字化けしているが、R1の識別子・列挙・後続の操作と対応する。自然人の身元や、別セッションへ停止指示がいつ伝達されたかは不明。
- Q11の20ファイルには、§2〜3の時刻でWrite/Edit、または対象パスを更新するPythonスクリプト/生成コマンドの記録がある。例えば20:51:35のh2.pyがadapters/comparator/runner/traceを更新し、20:52:29のJSON書出しがスキーマを拡張する。20:53:01の辞書から入力5件、20:53:36/48のauthoring実行からpending YAML3件を作成している。
- R1文書・履歴等の追記は21:01〜21:03 JSTまで続く。最終自己報告のWriteは21:03:20。したがってQ11の20件は作業途中のスナップショットだったと解釈できる。

出典: [origin-verified.json](../../results/baseline-reconciliation-20261115/origin-verified.json)、保存した `origin-command-115135.txt` / `115229.txt`、[history-recovery.json](../../results/baseline-reconciliation-20261115/history-recovery.json)。ファイルの最終mtimeも別途記録したが、これは本人確認・承認の証明ではない。操作記録との対応が取れたため、以前の「変更元未確認」は**Claude Codeの上記R1セッションによる変更に対応する**という結論へ更新できる。故意の隠蔽や無断変更とは断定しない。

## 5. A11の再検証

### 5.1 前回と同じJobNode全削除

前回と同じ3行をparse_textし、`dataclasses.replace(r, jobs=())`だけをメモリ上で行った。原本・Parser・Goldenは変えていない。

```jcl
//J JOB
//S EXEC PGM=X
//D DD DUMMY
```

| 検査経路 | 現在の結果 | 判断 |
|---|---|---|
| 前回と同じto_golden_viewだけの平坦比較 | PASS | 互換経路は今も階層を見ない |
| check_traceだけ | PASS | source文字列は変えていないため。木の検査の代用にはならない |
| 新しいcheck_hierarchy | H-JOB-01、H-STEP-01、H-DD-01を検出 | 削除された木の検出は修正されている |
| 手書きの階層期待値を加えたComparator | hierarchy.jobs[0] missing | hierarchyの期待値がある経路は検出する |
| 実SyntacticAdapter→実Runner（parse_fileの戻り値だけメモリ上で差替え） | 元の結果PASSED → 削除後FAILED | 製品側の新しい検査経路にも接続されている |

再現スクリプト: [recheck_a11.py](../../results/baseline-reconciliation-20261115/recheck_a11.py)。全実測: [a11-recheck.json](../../results/baseline-reconciliation-20261115/a11-recheck.json)。階層期待値は上の3行から手で記述し、Parser出力を期待側に使っていない。

既存の変異ツールも**M1〜M7: 943/943検出、escaped 0**だった。M1のCardDemo分は46/46で、JOBを持たない2 PROCにはM1は適用されない。M3は複数JOB入力だけで適用可能。検出率100%は、全48資産の全種の変異や全JCL仕様の保証ではない。CardDemoのM1はinvariantsで検出し、Golden単独での検出は0。pending5件ではM1をinvariantsとGoldenの両方で検出した。

**A11の結論**: 中心的な「木の削除をどの製品検査も検出できない」問題は改善済み。ただし、既存Goldenの階層期待値不足29件、pending未承認5件、下記の検査制約が残る。A11全体のCLOSEDは支持せず、台帳のRESOLVED_PENDING_REVIEWを、少なくとも未完了の状態として扱う。今回は台帳を変更していない。

### 5.2 現行の制約・注意点

**R-TRACE（再現済み）**: 改善されたtraceでも、71列で継続するSTRINGは最初のレコードのprefixを確認するfallbackがある。後続レコードの`BBBB`だけを`CCCC`に変え、flat文と木を一貫して更新すると、元のraw/Lexerは不変なのにcheck_trace=PASS、check_hierarchy違反0だった。全文トレース保証には未達。現CardDemoに引用文字列を71→16列へ分割する継続は0なので、現物で発現したとは数えない。CardDemo契約CA-13の全セグメント検査を既に満たしたとは扱わない。

**R-GATE（分類関数で再現済み）**: `classify_golden`は既知Golden失敗をcase IDとFAILED状態だけで分類する。G-IS-006のreasonを「無関係なAdapterクラッシュ」に差し替えても、unexpected=[]、known={G-IS-006:A10}になる。既知ケースで別の失敗原因が加わった場合の検出までは保証しない。実Goldenの3失敗は今回実際にA10由来であることを別途確認した。Gate AのPASSを、その原因検証の代用にしない。

**モデルの限界**: check_hierarchyはParserと別の歩査だが、同じflat文を入力にする。null後の所属やDLMで文そのものが消えた場合のIBM仕様適合までは判断できない。これはコードとR1報告にも明示されている。独立原本オラクルを置き換えない。

## 6. 全テスト・品質ゲート・独立インベントリ

### 6.1 実行コマンド

Python 3.12.15、既存.venvを使用した。authoring、seal、rulesの書出しコマンドは実行していない。

```powershell
.venv/Scripts/python.exe -m pytest tests -q -rsxX -p no:cacheprovider --junitxml=results/baseline-reconciliation-20261115/all-tests.xml
.venv/Scripts/python.exe tools/quality_gate.py --gate acceptance --output results/baseline-reconciliation-20261115/gates
.venv/Scripts/python.exe results/baseline-reconciliation-20261115/recheck_a11.py
.venv/Scripts/python.exe results/baseline-reconciliation-20261115/corpus-check/inspect_corpus.py
.venv/Scripts/python.exe results/baseline-reconciliation-20261115/corpus-check/compare_inventory.py
.venv/Scripts/python.exe results/baseline-reconciliation-20261115/probes-recheck.py
```

調査用スクリプトは以前の独立版を結果ディレクトリへコピーして実行した。出力先も新しい場所にし、旧監査結果・旧インベントリを上書きしていない。

### 6.2 件数と判定

| 項目 | 結果 |
|---|---|
| 全pytest（testsを明示指定） | **374 passed、52 skipped、11 xfailed**。failed/error/XPASSは0。終了0 |
| Harness（ゲート内） | 245 passed、1 skipped |
| Analyzer（ゲート内） | 129 passed、51 skipped、11 xfailed |
| skipの内訳 | NOT_IMPLEMENTED 49、BLOCKED 2、symlink権限1。通常skip52とxfail11を別計数 |
| xfailの内訳 | A01 4、A02 2、A03 3、A10 2（G-IS-006/007）。strict=True |
| sealed Golden 102件 | **49 PASSED、2 FAILED、2 BLOCKED、49 NOT_IMPLEMENTED** |
| pending Golden 5件 | **4 PASSED、1 FAILED**。全てdraft/REFERENCE |
| Golden失敗3件 | G-IS-006、G-IS-007、G-HIER-004。H-SPAN-02、004には期待spanとの構造差分もある。A10未修正が新たな検査で可視化されたもの |
| Goldenの正式保証 | FORMAL合格0。draft一致を正式な受入とはしない |
| lint/type/定義/封印/rules同期 | ruff PASS、mypy 76ファイルPASS、既存102/pending5定義有効、既存MANIFEST一致、rules同期 |
| 既知欠陥 | 14登録、13 OPEN、A11だけRESOLVED_PENDING_REVIEW。CLOSED 0 |
| **Gate A 開発健全性** | **PASS**。既知失敗とxfailを台帳により許容するゲート |
| **Gate B Parser正式受入** | **FAIL**。acceptanceコマンド終了1 |
| 独立反例24件 | 8 PASS、16 FAIL。前回と各プローブの合否変化0。これはpytestの失敗数ではない |

JUnit XMLはxfailもskipped要素で格納するため、XMLのskipped=63を通常skip63と誤読しない。type=pytest.xfailを分けて52/11を再集計した。Goldenとpytestは同じケースを重複して含むため、別の未検証件数として足し上げない。

Gate Bの内訳:

| 判定項目 | 実測 |
|---|---|
| B0 Gate A | PASS |
| B1 未CLOSED欠陥 | FAIL:14 |
| B2 xfail | FAIL:11 |
| B3 承認済みGolden | FAIL:範囲内83/83件が未承認 |
| B4 実装済み | FAIL:範囲内NOT_IMPLEMENTED 30 |
| B5 阻害なし | FAIL:2 BLOCKED |
| B6 失敗なし | FAIL:sealed+pendingで3 FAILED |
| B7 pendingなし | FAIL:5 |
| B8 階層期待値 | FAIL:実行したsyntactic29件に階層期待値なし |
| B9 範囲承認 | FAIL:ACCEPTANCE_SCOPEはPROPOSED |

ログ: [all-tests.log](../../results/baseline-reconciliation-20261115/all-tests.log)、[all-tests.xml](../../results/baseline-reconciliation-20261115/all-tests.xml)、[gates.log](../../results/baseline-reconciliation-20261115/gates.log)、[Gate A JSON](../../results/baseline-reconciliation-20261115/gates/quality_gate.json)、[Gate B JSON](../../results/baseline-reconciliation-20261115/gates/quality_gate_acceptance.json)、[変異結果](../../results/baseline-reconciliation-20261115/gates/hierarchy_mutation.json)。

### 6.3 CardDemo独立インベントリとの比較

独立走査を原本48ファイルに再実行し、以前のinventory.jsonと**ファイル内容がバイト単位で一致**した。46 JOB・2 PROC、123 EXEC、500 DD、681論理文、3046レコード、24名前なし連結、91データ領域という観測値は有効である。

現Parserとの比較は、文頭、パラメーター原表記、継続行所属、実行対象、STEP/DD所属、JOBレベルDD、データ境界について**差分0**。Job.spanだけはMNTTRDB2:29〜30のデータがspan=[1,28]の外にあるため不適合のまま。比較は、全意味・PROC展開・全列セグメントまで合格という意味ではない。

新しい不変条件がCardDemoで認識する違反は、H01（JOB文参照のlimitations差分）46ファイル、H02（PROC末尾PENDが木から辿れない）2ファイル、A10 1ファイル。全て台帳で説明され、未登録違反0だった。これらを説明できることと修正済みであることは異なる。

証拠: [corpus-check/inventory.json](../../results/baseline-reconciliation-20261115/corpus-check/inventory.json)、[corpus-check/comparison.json](../../results/baseline-reconciliation-20261115/corpus-check/comparison.json)、[verification-summary.json](../../results/baseline-reconciliation-20261115/verification-summary.json)。

## 7. 以前の監査結果の扱い

| 以前の指摘・結論 | 現在の扱い | 根拠 |
|---|---|---|
| A01 null/JES/NULLJCL | 有効・未修正 | N1/N2再失敗、既存xfail4。CardDemoでの限定分類は契約書のまま |
| A02 UNKNOWN DLM | 有効・未修正 | N4再失敗、xfail2。現CardDemoにDLM 0 |
| A03 継続null | 有効・未修正 | N3再失敗、xfail3。現CardDemoで組合せ0 |
| A04 && DLM | 有効・未修正 | D1再失敗 |
| A05 区切り由来の偽継続 | 有効・未修正 | D2再失敗 |
| A06 DLM前方一致 | 有効・未修正 | D3再失敗 |
| A07 DLM長/空値 | 有効・未修正 | D4の4件再失敗 |
| A08 DLM EOF診断 | 有効・未修正 | D5再失敗 |
| A09 EXEC/DD制約 | 有効・未修正 | E1〜E3再失敗 |
| A10 span | 有効・未修正、現在の検査が検出する | T1再失敗、CardDemo1件、Golden3 FAILED |
| A11 階層検査経路なし | **そのまま現状へ適用するのは不正確** | 新しい経路で全JOB削除を検出。§5の通り部分解消、正式保証/全文traceは未完了 |
| 既存Golden 51合格・0失敗 | **古い実行結果** | 現在49合格・2失敗。期待値変更ではなくinvariant追加によるもの |
| 既存ゲートPASSが受入を区別しない | **再検証により更新** | Gate A/Bを分離し、正式受入をFAILにする経路が存在。Gate Aの原因分類には注意点が残る |
| check_traceは1文字しか検査しない | **部分的に更新** | 単一行値は全文チェック。継続後半の一貫改変はまだ見逃す |
| 原本240・既存Golden195不変 | 有効、今回も再確認 | before.jsonとのSHA-256差分0 |
| Q11変更元不明 | **更新可能** | R1セッションの書込み記録との対応を確認。自然人・指示の伝達状況は不明 |
| 独立CardDemo構文/階層の観測値 | 有効 | 原本再走査が前回JSONと完全一致 |

Parserのparser.py/model.py/values.pyとLexer本体は、契約書調査開始時とSHA-256一致。既存Goldenの期待値も195ファイル全て一致する。したがってA01〜A10の合否が変わらないことと整合する。今回これらの欠陥修正には着手していない。

## 8. SHA-256ベースラインと保全

採取物:

| ファイル | 用途 |
|---|---|
| [start-manifest.json](../../results/baseline-reconciliation-20261115/start-manifest.json) | 調査開始時の全対象プロジェクトファイル（当時の既存resultsも含む）、size/mtime/ctime/SHA-256 |
| [source-version.json](../../results/baseline-reconciliation-20261115/source-version.json) | 実装302ファイルの集合識別値、今回開始時との差分、Gitなしの記録 |
| [baseline-manifest.json](../../results/baseline-reconciliation-20261115/baseline-manifest.json) | 最終時点の全src/tests/config/specs/tools/docs、results内の検証成果物・今回の復元コピー・ログ等、原本240資産のSHA-256 |
| [baseline-manifest.sha256](../../results/baseline-reconciliation-20261115/baseline-manifest.sha256) | 上記manifest自体のSHA-256 |
| [stability.json](../../results/baseline-reconciliation-20261115/stability.json) | 今回開始時の既存ファイル、原本、既存Goldenへの変更有無 |

実装集合識別値は、src/tests/specs/config/tools以下と、CLAUDE.md・pyproject.toml・uv.lock・.python-version・.gitignore・workspaceファイルの計302件について、パス順に `相対パス<TAB>ファイルSHA-256<LF>` を連結したUTF-8文字列のSHA-256。新しい報告書や実行日時によって変動しない識別値である。実装時はこの集合との差分で対象版を確認する。

最終manifestは、上の実装集合だけでなく文書・全検証成果物・原本を個別に記録する。再帰的な自己参照を避けるため、manifest自身とそのchecksumファイルだけはmanifestの列挙から除外し、checksumで外側から固定する。`.venv`、`__pycache__`、pytest/mypy/ruff/Hypothesisの作業キャッシュはソース/検証成果物に含めない。Python・パッケージ版は環境情報に別記する。Git未使用でも、内容コピーと個別ハッシュから調査対象を再現・照合できる。

## 9. 採用条件と停止

CONDITIONALの条件は次の通り。

1. 上記302ファイルの識別値を現在の出発点として扱い、別の書込みがあれば再照合する。本調査で内容の取消しや再実装は行わない。
2. Gate A PASSを受入済みの意味にしない。正式受入FAIL、A01〜A10、H01〜H03、A11残項目、R-TRACE/R-GATEの制約を既知の出発条件として引き継ぐ。
3. pending5期待値とPROPOSEDな汎用STEP4B範囲を、暫定採用されたCardDemo契約の承認済みGolden/受入範囲に自動昇格しない。CardDemo専用の独立データと範囲を次回の許可作業で整える。
4. 以後の修正範囲はCardDemo契約に基づいて決める。非出現のDLM等の一括修正や汎用Parser開発を再開する承認とは解釈しない。

現状を出発点にすることは可能だが、そのままCardDemo解析完了として採用する判定はFAILである。本調査は現在状態の確定と報告だけで終了する。

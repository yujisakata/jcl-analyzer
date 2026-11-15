# R1 Report: Harness Engineering の修正（監査 A11）

- 日付: 2026-11-15
- 状態: **実施済み・独立レビュー待ち**（A11 は RESOLVED_PENDING_REVIEW）。R2 には進んでいない
- 範囲: 検証ハーネスだけを修正した。Parser の本体（`parser.py`、`model.py`、`values.py`）と Lexer は変更していない。SHA-256 が監査時の `results/audit-20261115/before.json` と一致することを確認した。変更した Parser 側のファイルは、Golden View への変換層である `parser/adapter.py` だけである
- **作成者に関する事実**: 実装（Parser、Harness）、検査、変異、期待値、本報告は、すべて同じ担当者（Claude、claude-opus-5-5）が作成した。期待値は IBM 規則から手で書いたが、独立したオラクルではない。正式な保証には第三者のレビューが必要である

## 1. 変更内容

| 要件 | 実装 |
|---|---|
| 1 階層の表現 | statements view に `hierarchy` を追加した（jobs / dds / steps / target / inline_data / procedures / outside）。Schema の定義は `specs/golden-schema.json`、規約は `docs/golden-view.md` |
| 2 平坦な view の維持 | `statements` は変更していない。既存の 102 件はすべて有効で、封印も一致している |
| 3〜5 親子・順序・所属・連結の比較 | `comparator._cmp_tree`: 順序つきで比較し、パスごとに差分（mismatch / missing / unexpected）を出す。期待値にないキーは `unchecked` に出す |
| 3〜6 期待値に依存しない検査 | `jclprof.harness.hierarchy.check_hierarchy`。平坦な文の並びから所属を独立に導き、木と突き合わせる。違反コードは H-JOB / STEP / DD / OWN / ORD / CONC / SRC / TGT / SPAN-01 / SPAN-02 / DATA / REC-01..03 / REF-01。Adapter がすべての syntactic ケースで実行し、違反があれば FAILED にする |
| 6 Job.span の包含 | H-SPAN-01（文）と H-SPAN-02（インストリームデータと区切り文） |
| トレースの強化 | `check_trace` を、値の先頭 1 文字ではなく全文で照合するようにした |
| 7 未承認と承認済みの区別 | 既存の assurance（FORMAL / REFERENCE）に加え、レビュー待ちの期待値を未封印の `tests/golden_pending/` に分離した（ADR-027） |
| 8〜10 Gate A / B | `tools/quality_gate.py --gate dev / acceptance`、判定は `jclprof.harness.gates`、既知欠陥台帳は `tests/KNOWN_DEFECTS.yaml`、受入れ範囲は `tests/ACCEPTANCE_SCOPE.yaml`（PROPOSED）（ADR-028） |
| 誤った AST の注入 | `jclprof.harness.mutations`（M1〜M7 と、整合変異 M5c / M6c）、`tools/hierarchy_mutation_report.py` |

## 2. 意図的に注入した異常と検出率

対象は、レビュー待ちケース 5 件（Golden による比較あり）、封印済み syntactic ケースのうち実行可能な 33 件、CardDemo の 48 ファイルである（`results/harness/hierarchy_mutation.md`）。「検出」とは、変異前の AST にない違反が出ること、トレース検査が失敗すること、または Golden の比較に差分が出ることを指す。既知欠陥による既存の違反は、検出に数えない。

| 注入した異常 | 変異数 | 検出 | 検出した検査 |
|---|---|---|---|
| M1 JobNode の全削除 | 84 | 84 | 不変条件（H-JOB-01）。期待値があるケースでは Golden でも |
| M2 StepNode の削除 | 164 | 164 | 不変条件（H-STEP-01、H-DD-01）、Golden |
| M3 StepNode を別の JOB へ移動 | 3 | 3 | 不変条件（H-OWN-01）、Golden。この変異は複数ジョブの入力だけに適用できる。property テストで、生成した複数ジョブの入力 150 例でも検出を確認した |
| M4 DDNode を別の STEP へ移動 | 369 | 369 | 不変条件（H-OWN-01）、Golden |
| M5 EXEC 対象のプログラム名の変更 | 163 | 163 | 不変条件（H-TGT-01）、Golden |
| M6 インストリームデータの境界の変更 | 75 | 75 | 不変条件（H-DATA-01 / H-REC-01）、Golden |
| M7 Job.span の縮小 | 85 | 85 | 不変条件（H-SPAN-01）、Golden |
| **M1〜M7 合計** | **943** | **943（100%）** | 逃れた変異 0 件 |
| M5c 対象名を文と木の両方で一貫して変更 | 154 | 154 | トレース（原文との照合）、Golden |
| M6c 境界・レコードの役割・診断を一貫して変更 | 75 | 75 | 不変条件（H-REC-03: ステップ内の非 JCL レコードは JCL-DD-006 によりデータであり、UNRECOGNIZED にならない）、Golden |

- レビュー待ちケースでは、7 種の変異すべてが、不変条件と Golden 比較の**両方**で検出された（`tests/harness/test_hierarchy_harness.py`）
- 封印済みの Golden ケースは階層の期待値を持たないため、Golden 比較では M1 / M2 / M5 / M7 を検出できない（検出数 0）。これらは不変条件だけで検出している。Gate B の B8 は、この不足を数える

## 3. 新しい検査で見つかった欠陥（Parser は修正していない）

| ID | 重大度 | 内容 | 根拠 |
|---|---|---|---|
| A10（拡大） | MEDIUM | ジョブの最後にあるインストリームデータが Job.span に入らない。CardDemo の `app-transaction-type-db2/jcl/MNTTRDB2.jcl` で発現している（データは 29〜30 行目、span の終わりは 28 行目）。property テストで、次の JOB 文で終わるデータでも同じ根本原因を確認した | `close_job()` が文の span だけから計算している |
| H01 | LOW | `JobNode.job_statement` が平坦なリストの JOB 文と異なる（limitations が欠ける）。全ジョブで発生 | `place()` が `replace()` の前に JOB のコンテナを作っている |
| H02 | LOW | 手続きのコンテナに属する文が木から辿れない。カタログ PROC メンバー末尾の `// PEND`（CardDemo の REPROC.prc、TRANREPT.prc）、インストリーム PROC の最初の EXEC より前の JCLLIB | ProcDefNode と member に、それらの文の置き場がない |
| H03 | LOW | 最初の JOB 文より前にあるステップの DD と、その他の文が辿れない（EXEC だけが outside にある） | `close_step()` がコンテナのないステップを捨てる |

いずれも `tests/KNOWN_DEFECTS.yaml` に違反の署名（コードと詳細の正規表現）で登録した。署名は狭く定義し、通常のステップで DD が欠落した場合などを隠さないようにしている。

## 4. テストとゲートの結果

| 項目 | R1 前 | R1 後 |
|---|---|---|
| Harness スイート（`uv run pytest`） | 204 passed, 1 skipped | **245 passed, 1 skipped**（skip は symlink 権限。既存のもの） |
| Analyzer スイート | 129 passed, 51 skipped, 9 xfailed | **129 passed, 51 skipped, 11 xfailed**（増えた 2 件は G-IS-006 / G-IS-007。A10 として登録済み） |
| 封印済み Golden | 51 PASSED / 0 FAILED / 2 BLOCKED / 49 NOT_IMPLEMENTED | 49 PASSED / **2 FAILED（A10、新たに検出）** / 2 BLOCKED / 49 NOT_IMPLEMENTED。期待値は変更していない |
| レビュー待ち Golden | — | 4 PASSED / 1 FAILED（G-HIER-004、A10） |
| ruff / mypy strict | PASS | PASS（76 ファイル） |
| 原本 240 ファイル | — | 作業前に取得したスナップショットと、size / mtime_ns / SHA-256 がすべて一致 |

**Gate A（開発健全性）: PASS**（OPEN の既知欠陥 13 件を明示）。12 項目すべてに合格した。FAILED 3 件と xfail 11 件は、すべて登録済みの欠陥に対応している。

**Gate B（Parser 正式受入れ）: FAIL**

| 基準 | 結果 |
|---|---|
| B0 Gate A | PASS |
| B1 範囲内の欠陥がすべて CLOSED | FAIL（14 件。HIGH: A01, A02, A04, A05, A06, A11（レビュー待ち）／ MEDIUM: A03, A07〜A10 ／ LOW: H01〜H03） |
| B2 xfail 0 | FAIL（11） |
| B3 範囲内 Golden がすべて approved | FAIL（83 件中 83 件が未承認） |
| B4 NOT_IMPLEMENTED 0 | FAIL（30） |
| B5 BLOCKED 0 | FAIL（2） |
| B6 FAILED 0 | FAIL（3） |
| B7 レビュー待ち 0 | FAIL（5） |
| B8 階層を検証している | FAIL（実行された syntactic ケース 29 件が階層の期待値を持たない） |
| B9 受入れ範囲の承認 | FAIL（PROPOSED） |

`tests/harness/test_gates.py` で、すべての基準を満たした場合に Gate B が PASS すること、各基準が単独で FAIL を起こすことを確認している。したがって、この FAIL は空振りの判定ではない。

## 5. 既存テストの判定の変更（TC-013）

新しい不変条件が A10 を検出したため、「FAILED は 0 件」を前提にしていた 2 つのテストを、「FAILED は登録済みの既知欠陥に限る」に変えた。対象は `test_harness_cli.py::test_verify_real_suite_reports_not_implemented` と、`test_golden_parser.py` の G-IS-006 / 007（strict xfail）である。期待値は変えていない。退行ではなく、欠陥を検出するようになったことによる変更として報告する。

## 6. 限界と残る課題

- 参照モデルは、Parser の現在の範囲判断を写している。例えば、Null 文の後の所属は JES2 IGNORE と同じ扱いにしている（A01 と関係する）。また、平坦な文の並びそのものが誤っている場合（例: DLM の誤りで文がデータに埋もれる A04〜A06）は、不変条件では検出できない。期待値か、IBM に基づく別のオラクルが必要である
- M3 を適用できるのは、複数ジョブの入力（レビュー待ちの 1 件と、生成入力）だけである
- レビュー待ちの期待値 5 件と受入れ範囲ファイルは、ユーザーまたは第三者のレビューを受けていない
- 封印済みの in-scope syntactic ケース（29 件）に階層の期待値を加えるには、Golden の変更として承認が必要である（B8）
- 監査で指摘された A04〜A09 には、プロジェクト内の再現テストがまだない（台帳には登録済み）

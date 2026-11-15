# CD-2 Report: CardDemo Source AST の最小修正（A10 / H01 / H02）

- 日付: 2026-11-16 / 実装: Claude（claude-opus-5-5） / 状態: **実装済み・独立再検証待ち**（3 件とも RESOLVED_PENDING_REVIEW）
- 前提資料: `docs/reviews/cd1-source-acceptance.md`、`docs/reviews/carddemo-acceptance-contract.md`、`results/cd1-20261115/`
- 指示の扱い: CD-2 の指示は「**H02：」で途切れていた。H02 の設計と範囲はユーザーに確認した（回答: PROC ルートからのリンク、CardDemo の PEND の形のみ）
- 作成者の事実: Parser の修正とテストは同じ担当者が作成した。CardDemo 側の判定には、Codex が独立に作成した CD-1 の期待値を使った（未承認）

## 1. 修正内容

| ID | 原因 | 修正 | 変更ファイル |
|---|---|---|---|
| A10 | `close_job()` が文の span だけから終端を計算していたため、最後の文の後に続くデータ（EOF まで、または次の JOB 直前まで）が漏れた | 一般則: Job.span は、ジョブの全文（コメントを含む）と、ジョブ内で開いた全データ領域の終端（データレコード、自身の区切り文、UNDETERMINED の場合は全候補の終端）の最大値までとする（`_region_end`） | `src/jclprof/parser/parser.py` |
| H01 | `place()` が `replace()`（limitations の付与）の前に JOB のコンテナを作っていたため、木と平坦な一覧が別の JOB ノードを持っていた | `replace()` の後にコンテナを作る。木と平坦な一覧が同一のオブジェクトを参照する（検証器側の免除はしていない） | `src/jclprof/parser/parser.py` |
| H02 | カタログ PROC メンバー末尾の PEND に、木の中の置き場がなかった | `ParseResult.procedure_end` を追加し、PROC ルートが所有する（最後の EXEC には所属させない。ADR-031）。AST JSON に `procedure_end_id` を追加 | `parser.py`、`model.py` |
| 検査側 | — | 汎用の参照モデルは、メンバーの PEND の所有者を PROC ルートとする。CD-1 の検査器は実際のリンク `procedure_end` を辿る（1 処理。ユーザー承認）。期待値やフラット一覧からの補完はしない | `harness/hierarchy.py`、`harness/carddemo_source.py` |

## 2. 他の JOB への影響

修正前の 48 ファイルの Job.span と AST JSON の SHA-256 を記録し、修正後と比べた。

- Job.span が変わったのは MNTTRDB2 の 1 件だけ（[1, 28] → [1, 30]）。他の 45 JOB は変わっていない
- AST JSON が変わったのは、MNTTRDB2（span）と PROC メンバー 2 件（`procedure_end_id` の追加）だけ
- 46 JOB すべての span が、CD-1 の独立期待値と一致する（`test_carddemo_job_spans_match_independent_expectations`）

## 3. テスト（修正前に作成）

`tests/parser/test_cd2_source_fixes.py`（13 件）。修正前は、A10 / H01 の 8 件と H02 の 4 件が失敗し、変化しないことを確認する対照の 1 件だけが合格した。修正後は 13 件すべて合格した。

- A10: DD * と DD DATA が EOF まで続く場合、暗黙の SYSIN の直後に次の JOB が来る場合、UNDETERMINED の領域（JES=UNKNOWN）、文で終わる場合は変化しないこと（対照）
- H01: 木の JOB を含むすべてのノードが、平坦な一覧と同一のオブジェクト（`is`）であること。limitations が木の側にもあること
- H02: メンバーの PEND が PROC ルートから辿れること、最後のステップや outside に入らないこと、リンクを外すと H-OWN-02 で検出されること、インストリーム PROC は変化しないこと、CardDemo の 2 メンバー（29 行、79 行）

## 4. 検証結果

| 項目 | 結果 |
|---|---|
| CD-1 専用判定（`results/cd2-20261116/cd-run2/acceptance.json`） | **CD-SOURCE PASS（48/48）、CD-TRACE PASS（48/48）**、CD-ASSURANCE PENDING（48 件とも未承認）、変異 1501/1501 検出。正式受入れは承認待ちのため FAIL のまま |
| 全テスト | 412 passed / 52 skipped / 9 xfailed（xfail は D-1〜D-3 の再現テスト） |
| Gate A | PASS（OPEN の既知欠陥 11 件を明示） |
| Gate B | FAIL。B6（FAILED 0）は PASS になった。B1 は 15 件が未 CLOSED（うち A10 / H01 / H02 / A11 はレビュー待ち）、B2 / B3 / B4 / B5 / B7 / B8 / B9 は従来どおり |
| 封印済み Golden | 51 PASSED / 0 FAILED / 2 BLOCKED / 49 NOT_IMPLEMENTED（G-IS-006 / 007 は xfail ではなく通常の合格） |
| 汎用 pending | 5/5 PASSED（G-HIER-004 を含む） |
| 階層の変異検出 | 943/943 |
| 保全 | 原本 240 ファイルは size / mtime_ns / SHA-256 とも作業前と同一。Golden の封印は一致。CD-1 の expectations.json は oracle-manifest の SHA と一致し、reviews.json は 48 件とも PENDING のまま |

`results/cd2-20261116/cd-run` は、A10 / H01 修正後で H02 修正前の実行結果である（REPROC と TRANREPT だけが FAIL）。

## 5. 変更記録

- `tests/CHANGES.md` の TC-018 と TC-019。R1 のテスト 2 件と CD-1 のテスト 1 件は、修正前の失敗状態を前提にしていたため現状に合わせた。いずれも意図は維持し、期待値は変更していない
- `tests/KNOWN_DEFECTS.yaml`: A10 / H01 / H02 を RESOLVED_PENDING_REVIEW にした。H02 を分割し、CardDemo にない形（インストリーム PROC の最初の EXEC より前の文、ジョブファイル内の孤立した PEND）を H02B（OPEN）とした
- `docs/decisions.md`: ADR-031

## 6. 残る事項

- 3 件の修正の独立再検証（CLOSED にする条件）
- CD-1 の 48 期待値の人によるレビューと承認（CD-ASSURANCE）
- H02B、H03、A01〜A09 は対象外として修正していない

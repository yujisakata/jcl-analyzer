# Test Change Log

テストの期待値・判定ロジックの変更はすべてここに記録する（要件 6.2 / 7.4）。
独立オラクル（`tests/acceptance/expected/*.yaml`）そのものは再生成しない。変更の理由は、承認された要件・設計変更に限る。

| ID | 日付 | 対象 | 変更内容 | 根拠 | 承認 |
|---|---|---|---|---|---|
| TC-001 | 2026-11-15 | `tests/acceptance/test_carddemo_inventory.py::test_decode_failures` → `test_encoding_status` | DATA 資産の UTF-8 デコード失敗（14件）を期待する判定から、DATA 資産全件（23件）が `ENCODING_UNDETERMINED` になることを期待する判定へ変更。オラクルの `decode_failed_utf8` は「非UTF-8ファイルはすべて DATA である」ことの検証に引き続き使用 | ADR-009（ユーザー決定 A1） | ユーザー決定 A1（2026-11-15） |
| TC-002 | 2026-11-15 | `tests/unit/test_config.py::test_missing_roots` | 期待値（ConfigError）は変えず、テスト入力の組み立て方の不具合（`roots` 引数の二重指定）を修正 | テストコードの不具合 | Step 2 報告で報告済み |
| TC-003 | 2026-11-15 | G-GD-004 | blocked → draft。DISP=MOD の期待値を RUNTIME_DEPENDENT で定義 | ADR-022 | ユーザー決定 A1（ケースは draft のまま） |
| TC-004 | 2026-11-15 | G-IS-005 | environment.jes を UNDEFINED → UNKNOWN（blocked のまま） | ADR-021 | ユーザー決定 A2 |
| TC-005 | 2026-11-15 | G-IS-006 | blocked → draft。入力の終わりまでデータを保持し、LEX-W002（WARNING）を期待 | ADR-023 | ユーザー決定 A3（ケースは draft のまま） |
| TC-006 | 2026-11-15 | G-PP-005 | rule_ids に JCL-PROC-007 を追加し、説明を「入れ子の定義」に変更（blocked のまま）。G-PP-010（入れ子の呼出し）を新規追加 | ADR-020、JCL-PROC-007 | ユーザー決定 A4 |
| TC-007 | 2026-11-15 | G-JED-006 / G-CAT-003 | PAR-E001 → PAR-W003（WARNING）、PAR-E019 → PAR-W004（WARNING） | ADR-020 | ユーザー決定 A6 |
| TC-008 | 2026-11-15 | G-CONT-009 | view none → lexical（end: NULL_STATEMENT、NULL レコードを保持） | ADR-025 | ユーザー決定 A7 |
| TC-009 | 2026-11-15 | G-CONT-004 / G-CONT-010 | validation_stage を lexical → syntactic（文の種別は Parser の出力のため） | ADR-024 | ユーザー指示 C |
| TC-010 | 2026-11-15 | 新規 13 件 | lexical view のケース G-CONT-101〜107、G-QP-101〜102、G-IF-101、G-IS-101、G-INV-101 と G-PP-010 を追加（いずれも draft） | ADR-024 | 未承認（draft） |
| TC-011 | 2026-11-15 | tests/lexer/test_lexer_spec.py（初回実行前） | テストコードの不具合 3 種を修正: tuple と list の比較、カラム 17 を意図した入力が実際はカラム 18 だった、コメント位置の手計算の誤り（37 → 41）。いずれも期待する意味は変えていない | テストコードの不具合 | Step 4a 報告で報告 |
| TC-012 | 2026-11-15 | tests/parser/test_known_defects_04b.py（新規） | Step 4b 監査の欠陥 D-1〜D-3 の再現テスト 9 件を追加。期待値は IBM 本文（SA23-1385-70 p.159-160, p.459／SA32-0992-70 p.157）から手で作成し、xfail(strict=True) とした。既存テストと Golden の期待値は変更していない。`interpretations` / `structure_status` は設計レビュー中の暫定 API | docs/reviews/parser-defects-04b.md | 未承認（設計レビュー待ち） |
| TC-013 | 2026-11-15 | `tests/harness/test_harness_cli.py::test_verify_real_suite_reports_not_implemented`、`tests/parser/test_golden_parser.py::test_golden_case` | 判定を「FAILED 0 件」から「FAILED は `tests/KNOWN_DEFECTS.yaml` の OPEN の欠陥に登録されたものに限る」に変更。test_golden_parser では、登録済みのケースを xfail(strict=True) とする。原因: 新しい階層検査（ADR-027）が既知欠陥 A10 を G-IS-006 / G-IS-007 で検出するようになった。Golden の期待値は変更していない | ADR-027, ADR-028 | ユーザー指示 R1（判定の変更は本記録で報告） |
| TC-014 | 2026-11-15 | `src/jclprof/harness/trace.py`（`check_trace`） | 値の判定を「先頭 1 文字が一致」から「値の全文が原文の位置に一致（継続する値は 71 桁まで）」に強化（監査 A11）。既存のテストは修正なしで合格 | ADR-027 | ユーザー指示 R1 |
| TC-015 | 2026-11-15 | `tests/golden_pending/`（新規 5 件 G-HIER-001〜005） | 階層の期待値を新設。すべて draft・未封印で、独立レビュー待ち。**実装・検査・期待値の作成者は同じ**（Claude）。作成中に G-HIER-004 の flat view の inline_data に `delimiter: null` が欠けていた作成誤りを、view の規約に合わせて修正した（Parser の挙動に合わせた変更ではない） | ADR-027 | 未承認（独立レビュー待ち） |
| TC-016 | 2026-11-15 | 新規テスト: `tests/harness/test_hierarchy_harness.py`（23 件）、`tests/harness/test_gates.py`（18 件）、`tests/property/test_hierarchy_properties.py`（2 件） | 誤った AST の検出（M1〜M7 と整合変異 M5c / M6c）、比較器、Runner、既知欠陥台帳、Gate A / B の判定、生成入力での階層不変条件。既存テストの期待値は変更していない | ADR-027, ADR-028 | ユーザー指示 R1 |

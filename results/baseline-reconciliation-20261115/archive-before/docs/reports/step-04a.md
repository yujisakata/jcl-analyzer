# Step 4a Report: Golden View 修正と Lexer

- 日付: 2026-11-15
- 状態: 完了。Parser 本体には着手していない
- Golden 期待値: 承認 0 件（draft 100 / blocked 2）

## A. 設計修正（ADR-020〜026）

| 決定 | 反映内容 | Golden への影響 |
|---|---|---|
| A1 MOD | `runtime_dependent{if_new, if_existing, basis}` 型を追加。JCL-DD-012（p.148）、POL-007 | G-GD-004 を blocked から draft へ |
| A2 JES | `config.environment.jes` を追加（JES2 / JES3 / UNKNOWN、既定 UNKNOWN） | G-IS-005 は UNKNOWN のまま blocked |
| A3 DD DATA | 入力の終わりまで保持し、LEX-W002 を出す（WARNING、SYNTAX_DEFINED。p.121 と p.309 による） | G-IS-006 を blocked から draft へ |
| A4 PROC | 定義の入れ子（不正、PAR-E013）と呼出しの入れ子（有効、15 段まで）を JCL-PROC-007（p.32）で区別 | G-PP-010 を追加。G-PP-005 は回復方針が未決のため blocked |
| A5 原文と正規化 | comment_raw、dsn_raw、implicit_basis、lexical view の raw / seq / 位置 | `docs/golden-view.md` |
| A6 class | 全コードに class を付与。PAR-E001 → PAR-W003、PAR-E019 → PAR-W004 | G-JED-006 と G-CAT-003（change_log あり） |
| A7 Null | `end: NULL_STATEMENT` と NULL レコードを保持し、LEX-W001。ジョブ終了かどうかは推測しない | G-CONT-009 を lexical view に変更 |

## B. レビュー資料

`docs/reviews/golden-review-packet.md`（27 件。`tools/golden_review/make_packet.py` で生成）。

## C/D. Lexer と検証

- **実装**: `src/jclprof/lexer/`（model、lexer、adapter）
- **IBM 本文から先に書いたテスト**: 30 件合格。実装前にテストの不具合 3 種を見つけて修正した（TC-011）
- **Property テスト**: 5 種（継続・空白・コメントの挿入に対する不変性とパラメータのオラクル、71→16 桁の引用符継続、73-80 桁、72 桁、欠落なしと決定性）
- **I/O**: 入力を変更しない（書込みを監視するガード付き）
- **実資産**: 48 ファイル・3,046 レコードを欠落なく字句解析し、結果は決定的。レコード種別の件数は独立オラクルと一致。診断は 0 件
- **lexical 段階の Golden**: 16 件 PASSED（すべて REFERENCE。正式な保証ではない）
- **回帰**: Harness スイート 204 件合格、1 件 skip（symlink）。Analyzer スイート 54 件合格、89 件 skip（NOT_IMPLEMENTED / BLOCKED）
- **静的検査**: ruff、mypy strict ともに合格
- **原本**: 240 ファイルが Step 1 のベースラインと同一（SHA-256 と mtime）

## 既知の制約

- DD DATA の中にある `//` レコードは STATEMENT_START と判定される。インストリームの文脈を知る後続工程で再分類する
- 独立性の限界: 仕様由来のテストと Lexer は同じ AI が作成した。正式な保証には lexical の Golden のレビューが必要

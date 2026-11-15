# Step 3 Completion Report: Golden Test と検証ハーネス

- 日付: 2026-11-15
- 状態: 完了。Step 4（Lexer / Parser）には着手していない。開始には承認が必要

## 完了条件

| # | 完了条件 | 結果 |
|---|---|---|
| 1 | 11 カテゴリについて、適用する規則と設計状況を整理 | `specs/ibm-jcl-reference.md`（規則ごとに Golden Test ID を記載）と本報告 |
| 2 | 各カテゴリに 1 件以上、仕様未確認のものを未承認として識別 | 全カテゴリ 4〜12 件。approved 0 件 |
| 3 | 重大な境界条件と失敗モードについて追加テストを設計 | boundary 27 件、invalid 22 件、unresolved 6 件 |
| 4 | 各 Golden Test から IBM 仕様または独立した根拠へ追跡可能 | 全件に rule_ids と source_reference があり、Loader が registry と一致することを検査する |
| 5 | Loader、Schema Validator、Comparator、Integrity が単体テストに合格 | tests/harness 77 件すべて合格 |
| 6 | 既存の 115 件に回帰なし | 115 件合格、1 件 skip（symlink、従来どおり） |
| 7 | ruff と mypy strict が合格 | 合格（48 ファイル） |
| 8 | symlink テストを未検証として管理 | 品質ゲートが「unverified」と明示する |
| 9 | Parser 未実装で実行できないものを NOT_IMPLEMENTED と明示 | Golden 85 件、property 3 件 |
| 10 | 原本 240 ファイルの不変を SHA-256 と mtime で確認 | 一致。Step 1 のベースラインとも同一 |

## Golden Test の内訳（89 件）

| カテゴリ | 件数 | 主な検証内容 |
|---|---|---|
| JOB_EXEC_DD | 7 | 基本構造、省略された位置パラメータ、名前の規則と 8 文字の境界、EXEC の必須パラメータ、未知の操作、位置パラメータとキーワードの順序 |
| CONTINUATION_COLUMNS | 10 | IBM 例 1/3/4、カラム 3 非空白、継続カラム 4・16・17、73-80 桁と 72 桁、継続行の間のコメント文、継続後の Null 文、コメント文の 80 桁 |
| QUOTES_PARENTHESES | 7 | `''`、引用符内のカンマと空白、2 階層の括弧、null サブパラメータ、DSN の特殊文字、未終端の引用符、括弧の不均衡、3 階層の括弧 |
| DD_CONCATENATION | 5 | 名前なし DD（構文と意味）、先頭の名前なし DD、上書き名と連結（IBM 例）、実資産 CBPAUP0J |
| GDG_DISP | 7 | FR-02 の例（構文と意味）、DISP 既定値 6 種、MOD（blocked）、世代番号の境界と不正値、実資産 TRANEXTR |
| INSTREAM_DATA | 9 | DD * の終端 3 種（/*、次の文、EOF）、DD DATA と //、DLM、JES 依存（blocked）、DD DATA の未終端（blocked）、暗黙の SYSIN、DLM の誤用 |
| PROC_PEND | 9 | インストリーム PROC、カタログ PROC（PROC 文あり／なし）、名前なし、入れ子（blocked）、PEND なし、PROC なしの PEND、禁止文、TRANREPT のラベル不一致 |
| JCLLIB_INCLUDE_SET | 12 | 構文、引用符と SET の null 化、配置違反、2 つ目の JCLLIB、15/16 ライブラリ、INCLUDE の展開と未解決、マッピングの無い DSN、`&HLQ..`、未定義シンボル（IBM 例）、実資産 TRANEXTR |
| IF_THEN_ELSE | 11 | 基本構造、IBM 例 1、¬ と NOT、AND/OR の同順位（記述順の評価）、継続、入れ子と null THEN、ENDIF 欠落、ELSE/ENDIF のみ、16 段と 15 段の入れ子、非サポートのキーワード |
| COND | 8 | 各形式、COND.procstep（IBM 例 3）、テスト数 8/9、EVEN と 8 テスト、null サブパラメータ、不正な演算子、4096 |
| INVALID_UNRESOLVED | 4 | PROC の未解決、PROC の循環、後方参照の未解決、JES2 文の識別 |

- **review_status**: approved 0 / reviewed 0 / draft 85 / blocked 4
- **case_type**: valid 34 / invalid 22 / boundary 27 / unresolved 6
- **validation_stage**: lexical 6 / syntactic 64 / semantic 9 / resolution 10
- **IBM 仕様による裏付け**: VERIFIED の IBM 規則だけに依拠するケースは 63 件。残る 26 件は、IBM が規則を定めているものの違反時の帰結を規定していないため、診断の出し方がプロジェクトの方針（POL-001〜005）に依存する
- **実資産由来**: 4 件（CBPAUP0J 24-34 行、TRANEXTR 31-38 行、TRANEXTR 25-38 行、TRANREPT.prc 1 行）

## blocked の 4 件（解除にはユーザーの判断が必要）

1. G-GD-004: DISP=MOD の既定値は実行時にしか決まらない。View に「静的に未確定」を表す値を加えるかどうかを決める必要がある
2. G-IS-005: DD *,DLM で JES2 と JES3 の挙動が異なる。Environment Profile に JES の種別が無い
3. G-IS-006: DD DATA の未終端。p.121（入力の終わりで終端する）と p.309（区切り文が必要）の記述が食い違う（SPEC_AMBIGUITY）
4. G-PP-005: PROC の入れ子に対する誤り回復の方針（後続の PEND の扱い）が決まっていない

## 規則レジストリ

- **IBM 規則**: VERIFIED 62 件（SA23-1385-70 の本文を読み、章・節・ページを記録）、PENDING 1 件（MVS-MEM-001）
- **プロジェクト方針**: PROJECT-POLICY 5 件
- **Golden Test の無い規則**: JCL-REC-002、JCL-REC-004、JCL-CONT-005、JCL-DD-011（JES 依存のため意図的に設計していない）、JCL-PROC-006（オーバーライド。Step 5 の設計時に追加が必要）、MVS-MEM-001
- **IBM 文書の記述の食い違い**:
  - DLM の文字数: p.95 は「eight-character」、p.159-160 は JES2 で 2-18 文字、JES3 で 2 文字
  - DD DATA の終端: p.121 と p.309（上記の blocked 3）

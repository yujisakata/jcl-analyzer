# Architecture Decision Records

正式要件: `docs/requirements.md` v1.0。各ADRは要件IDとの対応を明記する。

---

## ADR-001 Python 3.12.15 を uv で固定する
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: 要件 8.1 は Python 3.12系を指定し、導入時にパッチ版を固定するよう求めている。開発機の既定は Python 3.15.0（他に 3.10.11）で、3.12 は導入されていなかった。
- **決定**: `uv python install 3.12.15` で導入し、`.python-version` に `3.12.15`、`pyproject.toml` に `requires-python = "==3.12.*"` を記載する。依存関係は `uv.lock` で固定する。
- **影響**: 実行は常に `uv run`（または `.venv`）経由で行い、システムの Python 3.15 は使用しない。

## ADR-002 設定・期待値の記述に YAML（PyYAML）を使用する
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: 要件 5章の CLI は `--config profiler.yaml` を、6.2 の Golden Test は YAML を例示している。8.1 は標準ライブラリ優先を求めている。
- **決定**: YAML 読込みに限り PyYAML（`yaml.safe_load` のみ）を使用する。出力形式は JSON・CSV・SQLite・Markdown とし、いずれも標準ライブラリで生成する。
- **却下案**: TOML（tomllib）は標準ライブラリで読めるが、要件の例示と異なるため採用しない。

## ADR-003 インベントリは「物理事実」のみを扱い、JCL構文を解釈しない
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: Step 2 の時点では Lexer / Parser が存在しない。行頭の正規表現でジョブ名や文種別を抽出すると、要件 8.1「正規表現の寄せ集めに依存しない」と非推測の原則に反する。
- **決定**: インベントリが記録するのは、ファイル単位の事実（パス、サイズ、SHA-256、文字コード検査結果、改行形式、レコード数、レコード長、行頭文字種別のヒストグラム、73-80桁の使用有無）と、拡張子・パスに基づく資産種別だけとする。JOB / STEP / DD 単位の集計は Step 4 以降で Parser の出力から生成する。
- **影響**: 行頭文字種別ヒストグラムの `//` 件数は「JCL文の数」ではない。レポートにもその旨を明記する。

## ADR-004 文字コードを推測しない
- **日付**: 2026-11-15 / **状態**: 採用（ADR-009 で拡張。「推測しない」原則は維持）
- **背景**: 要件 CTX-02 は文字コードの明示指定とデコード失敗の診断記録を求めている。対象資産の `data/EBCDIC` 配下は UTF-8 としてデコードできないが、どの EBCDIC コードページ（例: IBM-037 か IBM-1047 か）かは資産から確定できない。
- **決定**: 既定の文字コードは `utf-8` の strict デコードとする。パターン単位の上書きは設定ファイルで明示した場合に限る。デコードに失敗した場合は診断 INV-W002 を記録し、資産は登録したまま `encoding_status = DECODE_FAILED` とする。ディレクトリ名から EBCDIC コードページを推定することはしない。
- **未解決**: EBCDIC データのコードページはユーザーの確認待ち（Step 2 報告の未解決事項）。

## ADR-005 識別子の生成規則
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: 要件 4章は、識別子を元ソースの内容・位置・スコープから再現可能な方法で生成するよう求めている。
- **決定**: `source_id = "SRC-" + sha256(root_id + "\0" + 相対POSIXパス)` の先頭16桁（16進）。内容の同一性は別属性 `sha256` で判定する。診断ID は `DIAG-` + sha256(code, source_id, line, 詳細) の先頭16桁とする。
- **影響**: ルートIDを変更すると source_id も変わる。ルートIDは設定ファイルで固定する。

## ADR-006 解析結果は `jcl-profiler/results/` に保存し、入力ルート配下への出力を禁止する
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: 原本不変の原則（1.5、8.4）とユーザー指示（解析対象の原本を変更・削除しない）。
- **決定**: 出力ディレクトリが入力ルートと同じか、その配下にある場合、CLI は終了コード 2 で停止する。入力ファイルは `rb` モードでのみ開く。受入テストでは、実行前後に対象全ファイルのハッシュと mtime を独立に計測して比較する。
- **補足**: OS 上は対象ファイルに書込み権限がある（envcheck で確認）。保護はツール側の規律と上記テストによって担保している。

## ADR-007 実行時刻など可変のメタデータを別ファイルに分離する
- **日付**: 2026-11-15 / **状態**: 採用
- **背景**: 要件 8.2 は、同一入力から同一結果を生成すること、可変メタデータを比較対象から分離することを求めている。
- **決定**: `inventory.json` などの決定的な成果物には実行時刻を含めない。実行時刻・ホスト名・所要時間は `run_meta.json` にのみ記録する。

## ADR-008 CLI 終了コード（v1）
- **日付**: 2026-11-15 / **状態**: 採用（位置引数に関する終了コードは ADR-013）
- 0: 完了（WARNING / INFO 診断は含みうる）
- 1: 完了したが ERROR 診断あり（読取り失敗など）
- 2: 設定・引数・安全性の違反により未実行

---

## ADR-009 JCL系とデータファイルの文字コード設定を分離し、未確定は「未確定」として扱う
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー決定 A1）/ **要件**: CTX-02
- **決定**:
  - `encoding.profiles` に名前付きの文字コードプロファイルを定義し、資産種別ごとに `encoding_profile` で参照する。値が `null` のプロファイルは「未確定」を表す
  - 解決順序: `encoding.overrides`（最初に一致したもの） > 資産種別の `encoding_profile` > `encoding.default`。`default` に null は指定できない
  - 現在の設定: `jcl_text = utf-8`（JCL / PROC / CONTROL_CARDS）、`data = null`（DATA）
  - 未確定のファイルはデコードせず、SHA-256 だけを記録する。`encoding_status = ENCODING_UNDETERMINED`、診断 INV-I004（INFO）とし、`encoding_basis` に根拠（`profile:data` など）を残す
  - IBM-037 / IBM-1047 などのコードページは推測で確定しない。確定したら、確認者と日付を注記したうえで `profiles` または `overrides` に記録する
- **影響**: 受入テストの判定を変更した（`tests/CHANGES.md` TC-001）。独立オラクルのファイル自体は変更していない
- **未確定事項**: EBCDIC データ（14ファイル）のコードページ。`data/ASCII` 配下の 9ファイルも DATA プロファイルに含まれるため、現在は未デコード

## ADR-010 データセット名とローカルフォルダの対応は明示的な設定でのみ与える
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー決定 A2）/ **要件**: CTX-03, FR-01, FR-06
- **決定**: 設定ファイルの `datasets` に `{dsn, root, path, organization: PDS|SEQ, member_suffixes, aliases, note}` を列挙する。DSN の文字列からディレクトリ名を導く処理（例: `AWS.M2.CARDDEMO.PROC` から `proc/` を導く）は実装しない
- **検証**: DSN は大文字のドット区切り表記であること、root は既知のものであること、path はルート内の相対パスであることを検査する。DSN の重複は禁止する（`tests/unit/test_dataset_mapping.py`）
- **運用**: 対応を追加するのはユーザーが確認したものだけとし、`note` に確認者と日付を残す。現時点の登録は 0 件
- **影響**: 設定にない DSN（JCLLIB ORDER や DSN 参照）は、Step 5 で ENVIRONMENT_GAP として未解決参照に記録する

## ADR-011 カタログ PROC の解決はライブラリのメンバー名または別名を基準とし、PROC ラベルは別属性とする
- **日付**: 2026-11-15 / **状態**: 採用（設計のみ。実装は Step 5）/ **要件**: CTX-03, FR-06
- **決定**:
  - カタログ PROC の識別子は (ライブラリ DSN, メンバー名) とする。別名は `datasets[].aliases` で明示されたものに限る
  - PROC 文の名前フィールド（ラベル）は `ProcedureDefinition.label` として別に保持する。メンバー名と一致しない場合は診断する（例: `proc/TRANREPT.prc` のラベルは `REPROC`）が、解決には使わない
  - 探索順序は、(1) 同じジョブ内で EXEC より前に定義されたインストリーム PROC、(2) JCLLIB ORDER に記述された順のライブラリ、(3) Environment Profile に設定したシステム PROCLIB の順とする。各段階の正確な規則は Step 3 で IBM 文献から規則ID付きで登録し、確認状況が VERIFIED になるまで解決結果に「仕様未確認」の印を付ける
  - 候補が複数ある場合は、選ばれた候補・却下された候補・選択根拠（探索順序のどの段階か）を記録する（FR-01）
- **未確定**: システム PROCLIB の構成（JES 設定）はサイト固有のため、Environment Profile での明示的な設定を待つ

## ADR-012 仕様レジストリの記録項目
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー決定 A4）/ **要件**: CTX-05
- **決定**: `specs/ibm-jcl-reference.md` の規則ごとに、Rule ID、規則の要約、公式資料の URL、版（z/OS のリリースと資料番号）、節（節名とページ/トピック）、確認状況（VERIFIED / CROSS-CHECKED / PENDING）、使用箇所（コードとテスト）を記録する
- **運用**: VERIFIED は、公式資料の該当節を実際に開いて確認した場合に限る。Golden Test は Rule ID で規則を参照する

## ADR-013 CLI の位置引数による解析対象指定と優先順位
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー決定 A5）/ **要件**: 5章
- **書式**: `jclprof inventory [PATH ...] [--config FILE] --output DIR`（`envcheck` も同じ書式）
- **優先順位**:
  1. 位置引数の PATH を指定した場合、設定ファイルの `roots` を丸ごと置き換える。それ以外の設定（分類・文字コード・datasets など）は設定ファイルから読む
  2. 設定ファイルの root と同じディレクトリを指す PATH には、その root の ID を使う（source_id を安定させるため）。それ以外の PATH の ID は `arg<N>`（N は引数の位置、1始まり）とする
  3. PATH を指定しない場合は、設定ファイルの `roots` を使う
  4. `--config` を省略した場合は、カレントディレクトリからの `config/profiler.yaml` を使う
- **終了コード 2**: PATH が存在しない、PATH が重複している、出力先が PATH の内部にある、または設定ファイルを読めない場合
- **記録**: `run_meta.json` の `roots_source`（`config` / `positional`）と、実際に使った roots
- **補足**: datasets の root は設定ファイルの root ID を参照する。位置引数で ID が変わった root を参照する対応は Step 5 で無効として報告する
- **検証**: `tests/unit/test_cli_positional.py`

## ADR-014 requirements.md を v1.0 正式ベースラインとする
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー決定 A6）
- **決定**: `docs/requirements.md` を v1.0 正式ベースラインとし、ステータス表記を更新した。以後の要件変更・解釈の確定は、ADR と requirements.md 末尾の「変更履歴」の両方に記録する

## ADR-015 仕様レジストリは rules.yaml を正とし、参照文書は生成する
- **日付**: 2026-11-15 / **状態**: 採用 / **要件**: CTX-05、Step 3 指示 3
- **決定**:
  - 規則の正本は `specs/rules.yaml` とする。記録項目は Rule ID、適用構文、要約、適用条件、文献、版、章・節、ページ（「印刷ページ (PDF ページ)」）、確認状況
  - `specs/ibm-jcl-reference.md` は `jclprof rules-render` で rules.yaml と Golden ケースから生成し、対応する Golden Test ID も載せる。両者のずれは Harness テストと品質ゲート（rules-sync）で検出する
- **一次資料**: z/OS 3.2 MVS JCL Reference（SA23-1385-70、SHA-256 91b05378…）の PDF を取得し、本文を読んで 62 規則を VERIFIED とした
- **確認状況**: VERIFIED / CROSS-CHECKED / PENDING に加えて PROJECT-POLICY を設ける。PROJECT-POLICY は、IBM が帰結を規定していない事項についてのプロジェクトの報告方針（POL-001〜005）であり、IBM の裏付けとして数えない
- **補足**: Web 検索の要約は、DISP の NEW に対する正常終了時の既定値を KEEP としていたが、一次資料は DELETE だった。このため、要約だけを根拠に VERIFIED にはしない

## ADR-016 Golden View（実装に依存しない比較用の構造）
- **日付**: 2026-11-15 / **状態**: 採用 / **要件**: 6.2、Step 3 指示 H-02
- **決定**: 期待値は Parser の内部 AST ではなく `docs/golden-view.md` の View（statements / exec_conditions / dd_resources / substitutions / effective_statements / none）で記述し、`specs/golden-schema.json`（Draft 2020-12）で検証する。Step 4/5 の解析器は、自身の出力を View に変換する `StageAdapter` を提供する
- **比較規則**: 許容する差異は、ID・時刻、キーワードパラメータの順序（重複は保持）、IF 演算子の別表記に限る。期待値に書かれていない属性は `unchecked` として明示する。診断は多重集合として比較し、期待値に無い診断が出力されても不一致とする

## ADR-017 Golden Test のライフサイクルと完全性
- **日付**: 2026-11-15 / **状態**: 採用 / **要件**: 6.2、7.4、Step 3 指示 1.2・H-04
- **review_status**: draft / reviewed / approved / blocked
  - reviewed と approved には、VERIFIED の IBM 規則が 1 つ以上必要。PENDING または CROSS-CHECKED の規則を含むケースは draft か blocked に限る（Loader が強制する）
  - approved には `approval{approved_by, approved_on}` の記録が必要。blocked には `blocked_reason` が必要
- **verification_status** は実行結果であり、定義ファイルには書けない（スキーマで拒否する）。`results/harness/golden_run.json` に記録する
- **封印**: `jclprof golden-seal --by NAME`（人が明示的に実行する操作）で `MANIFEST.json`（全ファイルとケースごとの SHA-256）と `.baseline/` を作る
  - `golden-check` は読取り専用で、変更があれば unified diff を表示して終了コード 1 を返す
  - 承認済みケースを change_log なしで変更した場合は違反として報告する
  - テストの実行中に期待値やマニフェストを更新する経路は存在しない
- **初回封印**: Step 3 の初期ベースラインとして Claude が封印した。承認ではなく、全ケースが draft または blocked のままである

## ADR-018 テストスイートの分離と結果状態
- **日付**: 2026-11-15 / **状態**: 採用 / **要件**: Step 3 指示 H-05・H-06
- **Harness スイート**: `pytest`（既定の testpaths: `tests/unit`、`tests/acceptance`、`tests/harness`）
- **Parser 検証スイート**: `tests/parser`、`tests/property`。明示的に実行する。アダプタが無い間は NOT_IMPLEMENTED（または BLOCKED）として skip する
- **結果状態**: PASSED / FAILED / BLOCKED / NOT_IMPLEMENTED / NOT_RUN を別々に集計し、単一の成功率にまとめない。アダプタが例外を出した場合は FAILED とし、隠さない
- **品質ゲート**: `tools/quality_gate.py` で ruff、mypy、Harness スイート、Golden 定義の検査、Golden の完全性、rules-sync、Golden 実行、Parser スイートを一括実行する。FAILED と Harness の失敗だけをゲートの失敗とし、NOT_IMPLEMENTED と BLOCKED は報告に留める。skip した Harness テスト（symlink）は unverified として明示する

## ADR-019 実資産由来のケースは原本を参照し、複製しない
- **日付**: 2026-11-15 / **状態**: 採用 / **要件**: Step 3 指示 1.3、原本不変
- **決定**: `input_file: corpus://<root_id>/<rel_path>` と `corpus_source{root_id, rel_path, sha256, lines}` で原本を参照し、`scope.lines` の範囲内だけを比較する
- **前提条件**: 実行時に SHA-256 を照合し、原本が無い・変わっている場合は BLOCKED とする。SHA-256 の値は Step 2 の独立オラクルと一致することを Harness テストで確認する
- **位置づけ**: 実資産由来のケースは補助的なものとし（4 件）、人工 JCL を主とする

## ADR-020 診断の class と重大度（ユーザー決定 A6）
- **日付**: 2026-11-15 / **状態**: 採用 / **関連**: POL-001（改訂）、POL-006
- **決定**: すべての診断コードに class を付ける。class が構文妥当性・解析可能性・未対応・環境依存を区別する
  - **SYNTAX**: IBM が明示している記述要件への違反。帰結が書かれていなくても ERROR（POL-001。確認済みの要件に限る）
  - **SYNTAX_DEFINED**: 要件には違反するが、IBM が処理方法も定義している。WARNING
  - **ANALYZABILITY**: 解析できなかった。原文は保持する
  - **UNSUPPORTED**: 有効な可能性がある（製品拡張など）が、ツールが対応していない。WARNING
  - **ENVIRONMENT**: 環境情報の欠如に起因する
  - **SPEC_UNCONFIRMED**: IBM の規則を確認できていない。**ERROR にはしない**
  - **ADVISORY**: 有効だが注意を要する
- **既存コードの変更**:
  - PAR-E001 を PAR-W003（UNSUPPORTED、WARNING）に置き換える。未知の操作は、不正な JCL か未対応の拡張かを区別できないため
  - PAR-E019 を PAR-W004（SPEC_UNCONFIRMED、WARNING）に置き換える。先頭の名前なし DD が不正であることを IBM は明記していないため
  - 旧コードは deprecated とし、再利用しない。Loader は Golden 期待値での使用を拒否する
- **検証**: Harness テストで、class が存在すること、SPEC_UNCONFIRMED が ERROR でないこと、LEX コードがカタログと一致することを確認する

## ADR-021 JES 種別を Environment Profile に持つ（ユーザー決定 A2）
- **日付**: 2026-11-15 / **状態**: 採用
- **決定**: 設定ファイルに `environment.jes` を追加する。値は JES2 / JES3 / UNKNOWN で、既定は UNKNOWN（現在の設定も UNKNOWN）
- **影響**: JES に依存するケース（G-IS-005）は UNKNOWN の間 blocked のままとする。Golden スキーマの値 UNDEFINED は UNKNOWN に改めた（change_log あり）

## ADR-022 実行時にしか決まらない値の型（ユーザー決定 A1）と原文の保持（A5）
- **日付**: 2026-11-15 / **状態**: 採用 / **関連**: POL-007、JCL-DD-012（SA23-1385-70 p.148）
- **A1**: DISP=MOD の既定値のように実行時にしか決まらない値は、`{runtime_dependent: {if_new, if_existing, basis}}` で表す。既存データセットの有無は推測しない。G-GD-004 を blocked から draft に戻した（change_log あり）
- **A5**: Golden View で正規化表現と原文を分ける（`docs/golden-view.md`）。対象はコメント（comment / comment_raw）、DSN（dsn / generation / dsn_raw）、暗黙の SYSIN（implicit / implicit_basis / inline_data.records）、字句（parameter_text / tokens と、records.raw / seq / 位置）

## ADR-023 DD DATA の終端欠落（ユーザー決定 A3）
- **日付**: 2026-11-15 / **状態**: 採用
- **決定**: 入力の終わりまでの原文をデータとして保持し、LEX-W002 を出す。LEX-W002 は WARNING、class は SYNTAX_DEFINED
- **重大度の根拠**: p.309 は区切り文が「must appear」としており、要件違反にあたる。一方 p.121 は入力の終わりも DD DATA の終了条件として定義しているので、処理は確定する。したがって ERROR ではなく WARNING とする
- **段階**: インストリームデータの本格的な解釈は後続の工程で行う（指示 C）。G-IS-006 の期待値は確定したが（draft）、Step 4a の Lexer ではまだ実行しない

## ADR-024 Step 4a の Lexer の範囲と分類方法
- **日付**: 2026-11-15 / **状態**: 採用
- **範囲**: 物理レコード、明示した文字コード、80 桁のカード（短い行は空白で埋めたものとして扱う）、レコードの分類、継続（パラメータ・アポストロフィ・コメント）、トークン、位置、診断
- **作らないもの**: JOB/EXEC/DD の分類、PROC の構造、インストリームデータの解釈
- **IF の扱い**: 操作フィールドが `IF` の場合だけ、THEN までをフィールドとする字句モードを使う（JCL-IF-004）。意味の解釈ではない
- **既知の制約**: レコードは先頭の文字だけで分類するため、DD DATA 内の `//` レコードは STATEMENT_START になる。後続の工程で再分類する
- **Golden の調整**: G-CONT-004 と G-CONT-010 は文の種別（Parser の出力）を期待しているため、validation_stage を syntactic に移した。字句上の事実は、新しい lexical view のケースで検証する

## ADR-025 Null 文と継続の組合せ（ユーザー決定 A7）
- **日付**: 2026-11-15 / **状態**: 採用
- **決定**: Lexer は、継続中の文が Null レコードで終わったことを `end: NULL_STATEMENT` として記録し、Null レコードは NULL のまま保持して、LEX-W001（ADVISORY、WARNING）を出す。それによってジョブが終わるかどうかは推測しない（IBM p.459 は、その Null 文をブランクのコメント欄として扱うことしか述べていない）
- **G-CONT-009**: lexical view の期待値に変更した（change_log あり）

## ADR-026 Golden の参考比較と正式な保証の区別
- **日付**: 2026-11-15 / **状態**: 採用 / **関連**: Step 4a 指示 D
- **決定**: Runner は各結果に assurance を付ける。reviewed / approved のケースは FORMAL、draft のケースは REFERENCE。報告では assurance ごとに集計を分ける
- **影響**: 現時点では全ケースが draft なので、Lexer が lexical ケースに一致しても REFERENCE に留まる。正式な検証の根拠は、IBM の本文から先に書いた tests/lexer のテストと property テストとし、その独立性に限界があることも報告に明記する

## ADR-027 Golden View の階層表現と期待値に依存しない階層検査（R1、監査 A11）
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー指示 R1） / **関連**: ADR-016, ADR-026, ADR-028
- **背景**: JobNode をすべて除いても Golden 比較とトレース検査が PASS した（監査 A11）。statements view には JOB→STEP→DD の階層がなく、`check_trace` は値の先頭 1 文字しか見ていなかった
- **決定**:
  1. statements view に任意の `hierarchy`（jobs / steps / dds / procedures / outside）を加える。平坦な statements はそのまま維持する。順序つきで比較し、期待値にないキーは `unchecked` として明示する（`docs/golden-view.md`）
  2. Job の span は「JOB 文から、次の JOB 文の前までにそのジョブが所有する最後の物理レコードまで」とする（文、コメント、インストリームデータ、区切り文を含む）
  3. Adapter は期待値と無関係に `check_hierarchy()`（`jclprof.harness.hierarchy`）を実行する。違反があればケースは FAILED になる。この検査は、平坦な文の並びから所属を独立に導き、木・レコードの役割・データ領域・原文位置と突き合わせる
  4. `check_trace` は値の全文を原文の位置と照合する
  5. レビュー前の新しい期待値は、封印済みスイートとは別の `tests/golden_pending/`（未封印）に置く。レビューと承認の後に `tests/golden/` へ移し、ユーザーが封印する
- **検証方法**: 7 種の誤った AST（`jclprof.harness.mutations`）を注入し、すべてが検出されることを確認する（`tools/hierarchy_mutation_report.py`）
- **限界**: 参照モデルは Parser の現在の範囲判断（Null 文の後の所属は JES2 IGNORE と同じ、など）を写している。実装・期待値・検査を同じ担当者が作成した

## ADR-028 品質ゲートの分離（Gate A / Gate B）と既知欠陥台帳
- **日付**: 2026-11-15 / **状態**: 採用（ユーザー指示 R1） / **関連**: ADR-017, ADR-018, ADR-026, ADR-027
- **決定**:
  1. **Gate A（開発健全性）** `tools/quality_gate.py --gate dev`（既定）。既存の検査に加え、既知欠陥台帳の妥当性、未封印の pending スイート、階層の変異検出（M1〜M7 を 100%）を確認する。FAILED と xfail は、`tests/KNOWN_DEFECTS.yaml` の OPEN の欠陥に登録されたものだけを許す。未登録のものと、登録されているのに失敗しなくなったもの（stale）は FAIL とする。PASS の表示には、OPEN の欠陥数と「受入れではない」旨を添える
  2. **Gate B（Parser 正式受入れ）** `--gate acceptance`。Gate A に加えて、B1 範囲内の欠陥がすべて CLOSED、B2 xfail が 0、B3 範囲内の Golden がすべて approved、B4 NOT_IMPLEMENTED が 0、B5 BLOCKED が 0、B6 FAILED が 0、B7 レビュー待ちのケースが 0、B8 実行された syntactic ケースがすべて階層を検証している、B9 受入れ範囲が承認済み、をすべて満たすこと
  3. 受入れ範囲は `tests/ACCEPTANCE_SCOPE.yaml` で、Adapter の実装状況とは独立に定義する。除外は status: APPROVED かつ approved_by がある場合にだけ有効とする
  4. 既知欠陥の状態は OPEN → RESOLVED_PENDING_REVIEW → CLOSED とする。CLOSED には修正、xfail の除去、独立レビューが必要である
- **影響**: `tests/harness/test_harness_cli.py` と `tests/parser/test_golden_parser.py` の判定を、「FAILED 0 件」から「FAILED は登録済みの既知欠陥に限る」に変えた（TC-013）

## ADR-031 カタログ PROC メンバーの PEND は PROC ルートが所有する（CD-2、H02）
- **日付**: 2026-11-16 / **状態**: 採用（ユーザー回答: PROC-root link） / **関連**: ADR-027、cd1-source-acceptance.md
- **番号**: ADR-029 / 030 は `docs/reviews/parser-defects-04b.md` の提案（NULLJCL、解釈ごとの解析）用に予約済みのため、031 とした
- **決定**: `ParseResult.procedure_end` に、メンバーレベルの最初の PEND（インストリーム PROC を閉じるものではない PEND）を置く。木では PROC ルート（procedure_header と同じ階層）が所有し、最後の EXEC の other_statements や outside には入れない。インストリーム PROC の PEND は従来どおり `ProcDefNode.pend_statement`
- **検査**: `check_hierarchy` の参照モデルは、このPEND の所有者を MEMBER とする。CD-1 の検査器は実際のリンクを辿る（1 処理の追加）
- **範囲外**: インストリーム PROC 定義の最初の EXEC より前の文と、ジョブファイル内の孤立した PEND は H02B（OPEN）として残す

## ADR-032 CardDemo 専用 PROC Resolver と Effective Job View（CD-4）
- **日付**: 2026-11-16 / **状態**: 採用（実装済み。Codex の独立監査待ち）/ **契約**: carddemo-acceptance-contract.md CA-04〜06、CA-15
- **層の分離**:
  - Effective Job View（`src/jclprof/resolver/`）は Source AST（ParseResult）とは別の層とする
  - Source AST の JOB / STEP / DD と原文は変更しない。呼出し STEP の子である PRC001.FILEIN / FILEOUT もそのまま残す
  - Resolver は ParseResult を読むだけで、展開結果は新しいオブジェクトとして作る
- **ライブラリーの解決**（JCL-PROC-002/003、ADR-010/011）:
  - 探索順序はインストリーム → JCLLIB ORDER → システム PROCLIB とする。システム PROCLIB は未設定のため、常に NOT_CONFIGURED になる
  - メンバーは、明示的なマッピングが指すフォルダの中だけを、メンバー名または明示された別名で探す。候補が 0 件なら NOT_FOUND、複数なら AMBIGUOUS とし、先頭の候補を選ぶことはしない
  - 先に探索する未マッピングのライブラリーがある場合、後のライブラリーで見つかっても ENVIRONMENT_GAP とする（先のライブラリーにメンバーがあるかどうかが分からないため）
  - PROC ラベルは別の属性として扱い、メンバー名と異なる場合は RES-I001 を出す
- **マッピングの出典**:
  - 本番設定（config/profiler.yaml、datasets: []）は変更しない。この設定では 4 呼出しとも ENVIRONMENT_GAP になる
  - 契約の検算用に `config/contexts/cd4-contract-context.yaml`（status: UNCONFIRMED_CONTRACT_CONTEXT）を追加した。これは PROC ライブラリーだけをマッピングする。この文脈で得た結果には basis を付け、確定した結果としては扱わない（契約 Q01）
- **上書き**（JCL-PROC-006）:
  - procstepname.ddname は名前の付いた STEP に適用する。修飾なしの上書きは、直前に名前を付けた STEP、無ければ最初の STEP に適用する
  - 既存のパラメーターは REPLACE、値なしは NULLIFY、手続き文に無いものは ADD とし、元の値・適用値・上書き元の位置・理由を記録する
  - 一致する DD が無い上書き DD は、STEP の末尾に追加する
  - 範囲外の構成（位置パラメーター／DUMMY の上書き、DCB の部分マージ、相互排他、連結や暗黙 DD の上書き、入れ子呼出し STEP の上書き、呼出し EXEC の EXEC パラメーター上書き、16 段以上の入れ子）は RES-W004 を出し、適用しない
- **シンボル**（JCL-SYM-001〜004、JCL-EXEC-003）:
  - 呼出し EXEC のキーワードのうち、Table 20 と PARMDD に無いものをシンボリックパラメーターとする
  - 優先順位は、EXEC の値 > PROC の既定値 > SET とし、入れ子では呼出し元の値を引き継ぐ
  - SET の効力は記述位置で決まる（SET より後の文にだけ適用する）
  - 未定義のシンボルは文字のまま残し（RES-W001）、SYSUID は実行環境に依存するものとして扱う（RES-I002）
  - アポストロフィ内では PARM / ACCT / AMP / PATH / SUBSYS に限って置換する。インストリームデータの中のシンボルは置換しない（CA-07）
- **出典**: 展開後のノードは SourceRef を持ち、呼出し EXEC、PROC 定義の文と DD、上書き DD とキーワード、シンボルを定義した SET / EXEC / PROC、DCB 後方参照の参照元と参照先へたどれる（CA-15）

## ADR-033 Resolver の環境未確定性・未対応入力・実行証跡（CD-4R）
- **日付**: 2026-11-16 / **状態**: 採用（実装済み。Codex の再監査待ち）/ **契機**: Codex の独立監査（a19b8ca、FAIL）の F01〜F09
- **F01 検査できないライブラリー**: マッピングはあるがフォルダを検査できない場合（root ID が不明、フォルダが無い、ディレクトリーでない、一覧の取得に失敗）は、新しい結果 UNAVAILABLE とする。UNAVAILABLE は「メンバーが無い」ことを意味しない。UNMAPPED と同じく、それより後のライブラリーで見つかっても ENVIRONMENT_GAP とし、RES-W006 を出す。実在する空フォルダは従来どおり NOT_FOUND とし、次のライブラリーへ進む
- **F02 同じ DSN の複数マッピング**: 公開ローダー（load_library_context。YAML / JSON）は重複を ConfigError で拒否する（config/profiler.yaml のローダーはもともと拒否している）。コードで直接作った LibraryContext に重複がある場合は、lookup の結果を DUPLICATE_MAPPING、呼出しを AMBIGUOUS とし、RES-W007 を出す。リストの順番を優先順位として扱わない
- **F03〜F08 対応範囲の境界**: Resolver の範囲外の入力形を `resolver.UNSUPPORTED_FORMS` に登録する（12 形）。展開の前に検出し、RES-W004 に形の ID を付けて出し、EffectiveResult.unsupported に記録する。その形を含む呼出しは UNSUPPORTED とし、展開しない（そこから実効 STEP を作らない）。PROC メンバーの単独検査で SET がある場合は、その STEP を UNSUPPORTED とする。登録表とテストの一覧が一致することをテストで確かめ、境界を機械的に判定できるようにする。次の 3 点は検出ではなく修正した:
  - F03（漏れ）: インストリーム PROC の本体にある SET を JOB のスコープに入れない
  - F05: EXEC 文・PROC 文で同じシンボルを重複して定義した場合、最初の値を使う（JCL-SYM-005、SA23-1385-70 p.36）。RES-I003 を出す
  - F07: PGM= の原表記と、シンボルの使用 → 定義の対応を EffectiveStep に保存する
- **従来の RES-W004 の扱いの変更**: CD-4 では、範囲外の上書きを「適用せずに RESOLVED のまま」出していた。CD-4R では、呼出しを UNSUPPORTED にして展開しない（TC-021）。CardDemo には該当がなく（RES-W004 は 0 件）、結果は変わらない
- **F09 実行証跡**: `tools/cd4_resolve_report.py` は `run-manifest.json` を出力する。内容は、実装（git コミット、未コミットのパス、src/jclprof の全ファイルと生成器の SHA-256）、入力（ファイル一覧、48 入力と読み込んだメンバーの SHA-256）、文脈（ファイルのパスと SHA-256、basis、マッピングと root の全体）、環境（Python、プラットフォーム、エンコーディング、JES、依存の版、uv.lock）、出力（パス、バイト数、SHA-256）、件数。`--verify` はハッシュを再計算し、不一致を一覧にする。出力は UTF-8・LF に固定し、Windows でも再生成の結果がバイト単位で一致するようにする。実装ファイルのハッシュは CRLF を LF に正規化して計算する（同じコミットを CRLF で checkout した worktree でも照合できるようにするため）。原本の入力と出力は生のバイト列で照合する
- **範囲外のまま残すもの**: 未対応形の機能実装（PROC 内 SET の位置スコープ、ネストからのインストリーム PROC 参照、シンボルを使う PROC 名・JCLLIB・DUMMY の打消し、DCB マージなど）、DSN と物理資源の対応、インストリームデータ内のシンボル

## ADR-034 証拠のバイト固定、DSN/DSNAME、manifest の検証契約、複数の未解決理由（CD-4R2）
- **日付**: 2026-11-16 / **状態**: 採用（実装済み。Codex の再監査待ち）/ **契機**: Codex の独立再監査（e848ec9、FAIL）の R01〜R04
- **R01 バイト固定**: `.gitattributes` で、manifest が生のバイト列でハッシュする 5 ファイル（`config/contexts/cd4-contract-context.yaml` と `results/resolve/` の 4 ファイル）だけを `-text` にする。全 JSON・全ソースには広げない。リポジトリ内のそれ以外のファイル（config/profiler.yaml、uv.lock、ソースコード）は、CRLF を LF に正規化してハッシュし、方式（sha256_method）を記録する。原本の入力は生のバイト列のまま照合する。凍結済みの Source Oracle の属性・ハッシュ・Git の履歴は変更しない
- **R02 DSN と DSNAME**: IBM の DSNAME パラメーターの構文では、DSN と DSNAME は同じパラメーターの別表記である。上書きの照合はこの 2 つを同一とみなし、REPLACE / NULLIFY を適用する。記録には、上書きした側の表記（param）、置き換えた手続き側の表記（original_param）、旧値、新値、両側の出典（source / original_source）を残す。1 つの DD 文に両方の表記がある場合は判断できないため、新しい未対応形 U-OVR-DSN-DUPLICATE として UNSUPPORTED にする
- **R03 manifest の検証契約**（schema_version 2）:
  - VERIFIED（再計算または再導出する事実）: 必須の入力集合（ファイル一覧から導く）、入力とメンバーのハッシュ、context の file・hash 方式・hash と inline の内容（ファイルを読み込み直して比較）、コードのファイル一覧と各ハッシュと tree、generator、git_commit の存在と、そのコミットがコードを含むかどうか（commit_contains_code を再導出して比較）、encoding と JES（出力に記録された実行条件から）、uv.lock、出力の必須集合・バイト数・ハッシュ、件数とメンバーと basis（出力から導く）
  - RECORDED_ONLY（後から確認できない情報で、保証しない）: generated_at、git_dirty_paths、code_hash（説明の文字列）、Python・実装・プラットフォーム・バイト順・PyYAML の版
  - 信頼点: manifest のファイルそのものは、HEAD の Git blob（`git hash-object --no-filters` と `git rev-parse HEAD:<path>` の一致）または外部の SHA-256（`--manifest-sha256`）で固定する。どちらも無ければ UNANCHORED と表示する
  - 実装のコミットと証拠を生成したコミットが異なっていても、コードの内容が同じなら許容する（コミットの存在と内容で判定し、HEAD との一致は求めない）
- **R04 複数の未解決理由**: 未対応形を検出した呼出しの主状態は、ライブラリーの状態にかかわらず UNSUPPORTED とする。ProcCall に search_status（探索の結果）と reasons（例: `UNSUPPORTED:U-EXEC-OVERRIDE`、`ENVIRONMENT_GAP`）を追加し、探索の根拠と環境の診断（RES-W002 / W005 / W006 / W007）を残す


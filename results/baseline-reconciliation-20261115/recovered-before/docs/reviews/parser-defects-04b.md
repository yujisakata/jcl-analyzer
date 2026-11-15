# Step 4b Parser 欠陥分析と修正設計（レビュー依頼）

- 日付: 2026-11-15
- 状態: **設計レビュー待ち**。修正コードは実装していない。Golden の期待値と既存テストは変更していない
- 対象: 独立監査で指摘された 2 件（D-1、D-2）と、その調査中に見つかった関連欠陥 1 件（D-3）
- 再現テスト: [tests/parser/test_known_defects_04b.py](../../tests/parser/test_known_defects_04b.py)（9 件、すべて `xfail(strict=True)`。TC-012）

## 1. 結論

| ID | 欠陥 | 重大度 | CardDemo への影響 |
|---|---|---|---|
| D-1 | Null 文の後の文の所属を、JES 種別と JES2 の `INPUTDEF NULLJCL=` を考慮せずに 1 通りに確定している | 高（実効構造を誤る） | 構造への影響なし（後述 5.3） |
| D-2 | JES=UNKNOWN で DD \* と DLM の終端解釈が分かれると、JES2 解釈で存在する文とステップが結果から消える。残った構造は JES3 解釈と同じで、確定済みのように見える | 高（候補が黙って失われる） | 影響なし（DLM の使用 0 件） |
| D-3 | 継続中の文の直後にある Null レコードを、ジョブ終端の候補（`null_statement_line`、`after_null`、PAR-I001）として扱っている | 中 | 影響なし（LEX-W001 は 0 件） |

3 件の根本原因は共通している。**Parser が環境依存の判断を 1 本の状態機械の中で行い、環境ごとの解釈を保持する手段がない**ことである。そのため修正は個別のパッチではなく、「環境に依存しない構文層」と「環境ごとの解釈層」を分離する設計として提案する（4 章）。

## 2. IBM 出典の確認

ローカルに保存した PDF の本文で確認した。JCL Reference の SHA-256 は `rules.yaml` の記録 `91b05378…cf86` と一致した。JES2 Init & Tuning Reference は今回取得し、SHA-256 は `1043aa40…39e6` である。

| 根拠 | 出典 | 内容（要旨） |
|---|---|---|
| N-1 | SA23-1385-70 ch.23 Null Statement, Location in the JCL, p.459 (PDF 505) | 「The system ignores statements between a null statement and the next valid JOB statement.」 |
| N-2 | 同上, Note | 「JES2 ignores a NULL statement when it is included in a job's JCL statements. JES2 processes JES2 control statements following a NULL statement as part of the job…」。処理は INPUTDEF の設定で変わる |
| N-3 | 同上 | 継続中の制御文の後の Null 文は「blank comment field」として扱われ、その文にはそれ以上のパラメータがないとみなされる（JCL-CONT-007） |
| N-4 | SA32-0992-70（z/OS 3.2 JES2 Initialization and Tuning Reference）INPUTDEF, p.157 (PDF 177) | `NULLJCL=IGNORE\|EOF`。IGNORE（既定）は「continues reading the current job」。EOF は「honor JES3 NULL JCL semantics. A NULL statement finalizes a job … All other JCL statements are skipped until the next job statement」。TEST1/TEST2 の例あり |
| N-5 | 同上 | 「This operand has no effect on a // card that is used as the delimiter for instream data sets.」 |
| N-6 | 同上, p.157 / 一覧表 | NULLJCL は MAS メンバー単位の設定で、`$T INPUTDEF` で運用中に変更できる |
| D-a | SA23-1385-70 ch.12 DLM parameter, p.159-160 (PDF 205-206) | JES2 では DD \* + DLM のデータは DLM 文字列または `//` で終わる。JES3 では DLM 文字列でのみ終わる |
| D-b | SA23-1385-70 ch.12 \* parameter, p.95 (PDF 141) | D-a と同じ（「in a JES2 system only, the // that indicates another JCL statement」） |
| D-c | SA23-1385-70 ch.12, p.97 (PDF 143)（JCL-DD-006） | DD 文なしの入力データには、システムが SYSIN の DD \* を補う |

補足（参考情報。規則の根拠には使わない）: IBM APAR OA56620 と OA55685 に、NULLJCL=EOF の挙動の修正と既知の問題が記録されている。

**N-6 の帰結**: JES 種別が JES2 と確定しても、NULLJCL の値はわからない。また運用中に変更できるので、ジョブ投入の時点で値が変わる可能性もある。したがって `environment.jes: JES2` だけで Null 文の後の所属を確定してはならない（POL-003）。

## 3. 欠陥の詳細

### D-1 Null 文と NULLJCL

**再現**（IBM N-4 の例をそのまま使用）

```
//TEST1 JOB MSGCLASS=A
//STEP1 EXEC PGM=IEFBR14
//
//STEP2 EXEC PGM=IEFBR14
//TEST2 JOB MSGCLASS=A
//STEP1 EXEC PGM=IEFBR14
```

| 環境 | IBM による期待 | 現行の出力 |
|---|---|---|
| JES3（N-1、N-4） | TEST1: [STEP1]。STEP2 は読み飛ばされる | TEST1: [STEP1, STEP2]、診断なし — **誤り** |
| JES2 NULLJCL=EOF（N-4） | TEST1: [STEP1]。STEP2 は読み飛ばされる | （NULLJCL を入力する手段がない） |
| JES2 NULLJCL=IGNORE（N-2、N-4） | TEST1: [STEP1, STEP2] | TEST1: [STEP1, STEP2] — 一致 |
| JES2（NULLJCL 未確定） | 確定できない（上の 2 通り） | [STEP1, STEP2] と確定 — **推測**（POL-003 違反） |
| UNKNOWN | 確定できない（3 通り） | [STEP1, STEP2] と確定し、INFO の PAR-I001 を出すだけ — **確定してはいけないものを確定している** |

**根本原因**

1. `place()` と `note_after_null()`（[parser.py:251-261](../../src/jclprof/parser/parser.py#L251-L261)）は、Null 文の後の文を、どの環境でも直前のジョブにつなぐ。`after_null` は印として付くだけで、所属は変わらない。
2. 環境設定に NULLJCL がない（ADR-021 で定義したのは JES 種別だけ）。
3. `after_null` は、構文上の事実（Null 文の後にある）と意味上の結論（どのジョブに属するか）を 1 つの属性にまとめている。

**現行テストとの関係**: `test_null_statement_ends_job`（[test_parser_spec.py:267](../../tests/parser/test_parser_spec.py#L267)）は、JES=UNKNOWN で J: [S, T] と確定することを期待している。この期待値は N-1 と N-6 に反するため、修正時に変更が必要である（7 章）。**今回は変更していない。**

### D-2 JES=UNKNOWN の DD \* + DLM

**再現**

```
1 //J JOB
2 //S EXEC PGM=X
3 //SYSIN DD *,DLM=AA
4  DATA
5 //S2 EXEC PGM=Y
6 //D DD DUMMY
7 AA
8 //S3 EXEC PGM=Z
```

| 環境 | IBM による期待（D-a、D-c） | 現行の出力 |
|---|---|---|
| JES2 | データは 4 行目のみ。5-6 行目は EXEC と DD。7 行目は JCL ではないので、S2 に SYSIN が補われる。ステップ: S, S2, S3 | 一致 |
| JES3 | データは 4-6 行目、7 行目が区切り文字。ステップ: S, S3 | 一致 |
| UNKNOWN | 2 通りの候補を両方保持する | ステップ: S, S3。4-7 行目はすべて UNDETERMINED。**S2 と DD D はどこにも残らない**。ジョブの構造は JES3 解釈と同じになり、確定済みのように見える |

**根本原因**

1. `data_region()`（[parser.py:490-515](../../src/jclprof/parser/parser.py#L490-L515)）は、データ領域の候補（`candidates`）だけを保持する。その候補に従ったら後続の文がどうなるかは保持しない。
2. `after_region()` と `drop_lex_in()`（[parser.py:517-557](../../src/jclprof/parser/parser.py#L517-L557)）は、両方の候補を合わせた範囲（4-7 行目）の字句文を**全体から**捨てる。JES2 解釈では文である 5-6 行目も捨てられる。
3. 領域の後の解析は、1 本の状態（現在のステップ、`last_dd`）で続く。分岐の影響は領域の中にとどまらない。例えば、JES2 解釈では現在のステップが S2 になり、7 行目で SYSIN が補われる。局所的な候補だけでは、この違いを表現できない。
4. JobNode と StepNode には「環境によって変わる」ことを示す状態がない。

### D-3 継続の直後の Null レコード

**再現**: `//D DD DSN=A.B,` の次の行が `//` で、その後に `//T EXEC PGM=Y` が続く入力。

- IBM N-3 によれば、この `//` は D 文の空白のコメント欄として扱われ、Null 文ではない。したがってジョブは終わらず、T は J の通常のステップである。
- 現行の出力: `null_statement_line=4`、T に `after_null=True`。UNKNOWN では PAR-I001 も出る。

**根本原因**: Lexer はこの状況を正しく記録している（字句文の `end: NULL_STATEMENT` と LEX-W001。ADR-025）。しかし `run()`（[parser.py:170-174](../../src/jclprof/parser/parser.py#L170-L174)）は、NULL レコードであれば必ず `null_statement()` を呼び、Lexer の記録を参照しない。

**未確定の点（Q-1）**: N-3 の主語は「the system」である。JES2 の NULLJCL=EOF の入力処理（JES の読み取り段階）が、この `//` もジョブ終端とみなすかどうかは、どちらの資料にも書かれていない（OA55685 は、EOF の下で JES2 が Null 文を誤認識した事例である）。

## 4. 修正設計

### 4.1 原則: 構文層と解釈層の分離

| 層 | 内容 | 環境依存 |
|---|---|---|
| 構文層（syntactic facts） | 物理レコード、字句文、継続、Null レコードの位置と種類（独立した Null 文か、継続の終端か）、文の候補ごとの原文と位置、DLM の値 | なし。JES=UNKNOWN でも確定する |
| 解釈層（interpretation） | レコードの役割（DATA / STATEMENT / SKIPPED_AFTER_NULL）、データ領域の終端、JOB / STEP / DD の所属、補われた SYSIN | あり。具体的な環境ごとに 1 つずつ作る |
| 統合ビュー（merged） | すべての解釈で一致する部分を「確定」とし、一致しない部分を「環境依存」として各候補を保持する | 解釈層から導く |

`after_null` は構文層の事実 `follows_null_statement: <行番号>` に置き換え、所属の判断には使わない。

### 4.2 Environment Profile の拡張（ADR-027 案）

```yaml
environment:
  jes: UNKNOWN            # JES2 | JES3 | UNKNOWN（ADR-021）
  jes2_nulljcl: UNKNOWN   # IGNORE | EOF | UNKNOWN（新規。jes が JES2 か UNKNOWN の場合だけ意味を持つ）
```

設定から、具体的な環境の集合 E を導く。

| jes | jes2_nulljcl | E |
|---|---|---|
| JES3 | （無視） | {JES3} |
| JES2 | IGNORE / EOF | {JES2-IGNORE} / {JES2-EOF} |
| JES2 | UNKNOWN | {JES2-IGNORE, JES2-EOF} |
| UNKNOWN | UNKNOWN | {JES2-IGNORE, JES2-EOF, JES3} |

既定値は UNKNOWN とし、推測はしない。CLI の `--jes` と同様に `--nulljcl` を追加する。

### 4.3 方式: 具体的な環境ごとにファイル全体を解析し、結果を統合する

1. **解釈ごとの解析**: 現行の状態機械を「具体的な環境 1 つに対して決定的に動く」ものに整理し、E の各要素について**ファイル全体**を解析する。Lexer の結果は共有して再利用する。字句文の破棄（`drop_lex_in`）は解釈ごとの処理とし、全体からは捨てない。
2. **統合**: 同一性のキーは原文の行番号とする（JOB は JOB 文の行、STEP は EXEC 文の行、DD は DD 文の行、補われた SYSIN は最初のデータ行）。
   - `statements`: すべての解釈に現れる文の和集合。各文に `present_in: [解釈ID…]` を付ける。すべての解釈に現れる文が確定である。
   - `records`: 役割が全解釈で同じならその役割。違う場合は `role: ENVIRONMENT_DEPENDENT` とし、`roles_by_interpretation` を付ける。
   - `jobs[*].structure_status`: DETERMINED か ENVIRONMENT_DEPENDENT。ステップと DD の並びが全解釈で一致する場合だけ DETERMINED とする。
   - `jobs[*].steps`（確定ビュー）: すべての解釈で同じジョブに属するステップだけを、原文の順に並べる。各候補の全体像は `interpretations` に置く。
   - `interpretations: [{id, environment: {jes, nulljcl}, jobs, records, data_regions, diagnostics}]`。E の要素が 1 つなら 1 件だけで、統合ビューと一致する。
3. **局所的な分岐ではなく全体を再解析する理由**: 分岐の影響は後続の状態（現在のステップ、連結、SYSIN の補完、Null 文の後の読み飛ばし）に伝わる（D-2 根本原因 3）。環境の次元は 2 つ、具体的な環境は最大 3 つなので、組合せが爆発しない。CardDemo 48 ファイルの解析は数秒で終わるので、3 倍になっても実用上の問題はない。今後の環境次元は 1 か所の登録表で管理し、組合せ数の上限を設ける（例: 8）。

### 4.4 解釈ごとの規則

**Null 文（D-1）**

| 解釈 | 独立した Null 文の後、次の JOB 文まで |
|---|---|
| JES2-IGNORE | 現在のジョブの読み取りを続ける（N-2、N-4）。文は通常どおりジョブに属する |
| JES2-EOF、JES3 | ジョブを確定し、後続のレコードの役割を `SKIPPED_AFTER_NULL` とする（N-1、N-4）。文は原文と位置を保持して `skipped_statements` に入れ、ジョブには属させない。データ領域の扱い（Q-3）も同じ規則に従う |

- in-stream データを終わらせた `//`（N-5）: JES2-EOF ではジョブ終端としない。JES3 については資料に明記がないので、Q-2 として判断を仰ぐ。
- 統合の結果、所属が分かれた場合は PAR-I001（ENVIRONMENT）を出す。その意味は「Null 文の後の文の所属が環境によって異なる」に改める。

**継続の直後の Null レコード（D-3）**: Lexer の字句文の `end == NULL_STATEMENT` を参照する。その NULL レコードの役割は `NULL_AS_COMMENT_FIELD`（その文の一部）とし、`null_statement()` を呼ばない。これはすべての解釈で同じ扱いとする（N-3）。ただし JES2-EOF と JES3 では、JES の読み取り段階が別の扱いをする可能性を SPEC_UNCONFIRMED（WARNING）で示す（Q-1）。

**DD \* + DLM（D-2）**: 各解釈では JES が確定しているので、終端は 1 通りに決まる（D-a）。統合ビューでは、データ領域を UNDETERMINED（候補付き）とする。これは現行のモデルを引き継ぐ。5-6 行目の文は `present_in: [JES2-*]`、7 行目は JES2 解釈では補われた SYSIN のデータ、JES3 解釈では区切り文字として残す。G-IS-005 の blocked_reason に書かれた「record 6 is stray」は、D-c により「補われた SYSIN のデータ」と読むべきである。Golden を変更するときに確認を求める（Q-4）。

### 4.5 影響を受ける成果物（すべて承認後に変更する）

| 成果物 | 変更 |
|---|---|
| `config/profiler.yaml` とスキーマ、`context/config.py` | `environment.jes2_nulljcl` を追加 |
| `docs/decisions.md` | ADR-027（NULLJCL を Environment Profile に持つ）、ADR-028（解釈ごとの解析と統合）。ADR-025 の未決事項（Null 文でジョブが終わるか）は Q-1 の決定で解消する |
| `requirements.md` の変更履歴 | ADR-014 に従って記録する |
| `specs/diagnostic-catalog.yaml` | PAR-I001 の意味の変更。新しいコード（読み飛ばし INFO、D-3 の SPEC_UNCONFIRMED WARNING） |
| `specs/rules.yaml` | N-4 と N-5 を新しい規則（例: JES2-INPUT-001/002、文書 IBM-JES2INIT-32）として追加し、md を再生成する |
| AST（`ParseResult.to_dict`） | schema_version 2: `interpretations`、`present_in`、`structure_status`、`follows_null_statement`、`skipped_statements`。`model.py` が参照している `docs/ast-schema.md` は存在しないので、このとき作成する |
| Golden スキーマ / golden-view.md | 環境依存のケースのための `interpretations` ビュー（G-IS-005 の blocked 解除の前提） |
| `tests/parser/test_parser_spec.py::test_null_statement_ends_job` | 期待値の変更（7 章、TC 記録） |

## 5. 影響範囲

### 5.1 合成入力

- D-1: Null 文の後、次の JOB 文までに文があるすべての入力。
- D-2: DD \* に DLM があり、DLM 文字列より前に `//` で始まるレコードがあり、JES=UNKNOWN の入力。
- D-3: 継続中の文の直後に Null レコードがある入力。

### 5.2 Golden（変更していない）

| ケース | 状態 | 関係 |
|---|---|---|
| G-IS-005 | blocked | D-2 の対象そのもの。修正と Golden スキーマの拡張の後に、`interpretations` ビューで blocked を解除できる（Q-4） |
| G-CONT-009 | draft（lexical） | Lexer の期待値には影響しない。notes にある未決事項「Does the null record also end the job?」は Q-1 で解消する |
| その他 | — | Null 文の後に文がある Golden ケースは存在しない（いずれの欠陥も Golden では検出されていなかった） |

### 5.3 CardDemo（48 ファイル）

- Null 文があるファイル: CARDFILE、CBADMCDJ、DEFGDGD（2 個）、DUSRSECJ、ESDSRRDS、TRANREPT の 6 ファイル。いずれも、Null 文の後にはコメント文しかない。
  - JES2-EOF と JES3 の解釈では、それらのコメントの役割が `SKIPPED_AFTER_NULL` になる。ジョブ、ステップ、DD の数（46 / 123 / 500）は、すべての解釈で変わらない見込みである。
- DLM の使用は 0 件、LEX-W001 は 0 件。したがって D-2 と D-3 の影響はない。
- 結論: 実資産で欠陥が表に出ていないのは、該当する構文がないからにすぎない。Step 5 以降でほかの資産を扱えば影響が出るので、修正は必要である。

## 6. 独立した再検証の方法

同じ AI が Parser と期待値を作成しているという独立性の限界がある（ADR-026）。そのため、出所の異なる複数のオラクルを組み合わせる。

| # | 方法 | オラクルの出所 | Parser から独立しているか |
|---|---|---|---|
| V-1 | 再現テスト 9 件の xfail を外して合格させる | IBM 本文から手で書いた期待値（N-4 の例はそのまま使用） | 高い。ただし**期待値そのものに人のレビューが必要**（特に EXPECT_IGNORE、Q-5） |
| V-2 | 参照オラクル: 終端と Null 文の規則だけを、`jclprof.parser` を import しない約 100 行の別実装として `tests/oracle/` に書く。具体的な環境ごとにレコードの役割を計算し、Parser の各解釈と比較する（差分テスト） | IBM 本文 | 中程度。コードの経路は別だが、作成者は同じ |
| V-3 | 性質テスト: (a) 各具体的環境 e について `parse(UNKNOWN).interpretations[e] == parse(e)`。(b) 確定部分は全解釈の共通部分に等しい。(c) どれかの解釈で文になる字句文は、統合結果に必ず残る（`present_in` が空でない。D-2 の不変条件）。(d) 環境を絞る（UNKNOWN → JES2 → JES2-IGNORE）と、候補は減るだけで、確定部分は増えるだけ。(e) 全レコードがどの解釈でも役割を 1 つ持つ | 規則間の関係 | 高い（期待値を Parser から取らない） |
| V-4 | 生成入力: 現行の `RECORD` 戦略に、`//` の Null、`DLM=AA` / `AA`、継続の末尾の `//` を加え、V-2 と V-3 を hypothesis で実行する | — | — |
| V-5 | CardDemo 48 ファイルを 3 つの解釈それぞれで解析する: 数の不変（46 / 123 / 500）、原本への逆追跡、決定性、未認識レコード 0、原本 240 ファイルの SHA-256 と mtime の不変 | 独立オラクル `carddemo_inventory.yaml` | 高い |
| V-6 | 回帰: 品質ゲートの全項目。期待値を変えたテストは、すべて TC に記録する | — | — |

## 7. 修正時に必要な既存期待値の変更（今回は変更しない）

| 対象 | 現行 | 提案 | 根拠 |
|---|---|---|---|
| `test_null_statement_ends_job`（JES=UNKNOWN） | J: [S, T]、`steps[1].after_null`、PAR-I001 | 確定ビューは J: [S]、K: [U]。J の `structure_status` は ENVIRONMENT_DEPENDENT。T は JES2-IGNORE 解釈でだけ J に属し、ほかの解釈では `skipped_statements`。PAR-I001 は維持（新しい意味で） | N-1、N-4、N-6 |
| G-IS-005 | blocked / view none | `interpretations` ビューの JES2 / JES3 候補（4.4）。review_status は draft | D-a、D-c、Q-4 |

## 8. 品質ゲートの 2 段階化（提案）

現行のゲートは「開発が壊れていないこと」を確認するもので、受入れの根拠にはならない。実際、今回の 9 件の xfail があっても、ゲートは **PASS** を表示した。そこで、目的の異なる 2 段階に分ける。

### Gate A: 開発健全性（`quality_gate.py --gate dev`。変更のたびに実行）

現行の 8 項目に、次の 2 項目を加える。

- **A-9 既知の欠陥の整合**: すべての xfail が `strict=True` であり、`tests/KNOWN_DEFECTS.yaml`（ID、文書、再現テスト）に登録されていること。登録されていない xfail と XPASS は失敗とする。
- **A-10 状態の表示**: xfail の件数、REFERENCE のみの合格件数、NOT_IMPLEMENTED と BLOCKED の件数を、必ず表示する。

表示は `DEV-HEALTH: PASS` とし、「受入れ」「品質保証」の語は使わない。

### Gate B: Parser 正式受入れ（`--gate acceptance`。Step 4b の完了判定に使う）

Gate A の合格に加え、次をすべて満たすこと。

| # | 基準 | 現在の見込み |
|---|---|---|
| B-1 | Parser の範囲の既知の欠陥が 0 件（Parser 範囲に xfail がない） | **未達**（D-1〜D-3） |
| B-2 | 範囲内（syntactic / lexical、IN_SCOPE カテゴリ）の Golden がすべて reviewed / approved で、封印済みであること。FORMAL の合格だけを数え、REFERENCE の合格は数えない | **未達**（承認 0 件） |
| B-3 | 範囲内の NOT_IMPLEMENTED が 0 件。または、ユーザーが承認した範囲外リスト（scope manifest）に載っていること | 要整理（49 件） |
| B-4 | BLOCKED は環境の理由によるものだけで、`interpretations` ビューで候補を検証していること | 未達（G-IS-005） |
| B-5 | 環境の解釈ごとのスイート（V-3〜V-5）が、すべての具体的環境で合格すること | 未実装 |
| B-6 | Parser が参照する規則が VERIFIED であり、出典について人の確認記録（`rules.yaml` の `reviewed_by`）があること | 未達（JCL-DD-013 / 014 は未確認） |
| B-7 | 独立したオラクルの証拠（V-2 の差分テストと、人がレビューした期待値）があること。同じ作成者であるという限界を報告に明記すること | 未達 |
| B-8 | CardDemo: 48 ファイル、逆追跡、欠落なし、未認識 0 件（または理由付き）、原本の不変 | 達成見込み |
| B-9 | Mutation テスト（requirements M4）の Parser のスコア。閾値はユーザーが決める | 未実施 |

表示は `PARSER-ACCEPTANCE: PASS | FAIL` とし、基準ごとに証拠を出力する（`results/harness/quality_gate_acceptance.json`）。現時点では **FAIL** になる（B-1、B-2 ほか）。

## 9. ご判断をお願いしたい事項

| # | 論点 | 選択肢（推奨を先頭に記載） |
|---|---|---|
| Q-1 | 継続の直後の `//`（N-3）でジョブは終わるか | (A, 推奨) N-3 により、すべての解釈で終わらないとする。ただし JES2-EOF と JES3 では SPEC_UNCONFIRMED の WARNING を出す / (B) JES2-EOF と JES3 では終わる候補も保持する |
| Q-2 | JES3 で、in-stream データを終わらせた `//` はジョブ終端か（JES2-EOF は N-5 により終端ではない） | (A, 推奨) 資料に明記がないので、終端とする候補としない候補を両方保持し、SPEC_UNCONFIRMED とする / (B) N-1 を適用して終端とする |
| Q-3 | 読み飛ばされる範囲の中にある DD \* などのデータ領域をどう扱うか | (A, 推奨) 読み飛ばされる範囲の中でも、データ領域の終端は同じ規則で決めて保持する（`//` で始まるデータが JOB 文として誤認されないようにするため） / (B) すべてのレコードを一律に SKIPPED とする |
| Q-4 | G-IS-005 の解除方法と「record 6 is stray」の読み方 | 修正後に `interpretations` ビューで draft にし、7 行目（ケースの入力では 6 行目）を補われた SYSIN のデータとして扱う（D-c） |
| Q-5 | JES2-IGNORE で、Null 文の後の文がそのジョブに属すること（EXPECT_IGNORE）は妥当か | N-2 の「JES2 ignores a NULL statement」と N-4 の「continues reading the current job」に基づく。ただし z/OS のコンバーターの段階で N-1 が適用されるかどうかは、明記されていない。レビューでのご確認をお願いしたい |
| Q-6 | ADR-027（NULLJCL）と ADR-028（解釈ごとの解析と統合）、AST schema v2、Golden スキーマの拡張、診断コードの追加 | この設計のとおり進めてよいか |
| Q-7 | 品質ゲートの 2 段階化と、B-3 / B-9 の閾値 | 8 章の案でよいか |

## 10. 今回の作業範囲

- 実施したこと: IBM 本文の確認（JCL Reference と JES2 Init & Tuning Reference）、現行の挙動の再現、再現テスト 9 件の追加（xfail strict。TC-012）、本書の作成、CLAUDE.md の承認履歴の訂正。
- 品質ゲート: PASS（Analyzer スイートは 129 passed / 51 skipped / 9 xfailed）。`--runxfail` で実行すると、9 件すべてが AssertionError で失敗し、欠陥が再現されることを確認した。
- 実施していないこと: Parser の修正、Golden と既存テストの期待値の変更、新しい機能。前回依頼の実装監査レポート（`parser-review-04b.md`）、JCL-DD-013 / 014 の出典確認、原本 240 ファイルの比較は、作業が中断されたため未実施である。

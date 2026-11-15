# Golden View Contract（schema version 1）

Golden Test の期待値は、Parser の内部 AST ではなく、実装に依存しない比較用の **Golden View** で記述する（ADR-016）。
Step 4 以降の Parser / Resolver は、自身の出力をこの View に変換する Adapter（`jclprof.harness.adapters.StageAdapter`）を提供する。
期待値の形式は `specs/golden-schema.json` で検証する。

## 共通事項

- 行番号は入力ファイルの物理レコード番号（1始まり）。`span` は論理文を構成する最初と最後の物理レコード `[first, last]` で、継続行を含む
- 論理文の継続の間に置かれたコメント文は独立した文として扱い、開始行の順に並べる
- 比較しない項目: `id`、`node_id`、`diag_id`、`source_id`、`timestamp`、`generated_at`、`elapsed`（Comparator が実際の出力側から取り除く）
- 期待値に書かれていない文の属性は比較しない。比較しなかった属性は、結果に `unchecked` として明示する
- 演算子の別表記（`>` と `GT`、`¬` と `NOT`、`&` と `AND`、`|` と `OR` など）は非本質的な差異として正規化してから比較する（JCL-IF-002）

## view: statements（lexical / syntactic）

```yaml
- kind: DD               # JOB EXEC DD PROC PEND JCLLIB INCLUDE SET IF ELSE ENDIF OUTPUT COMMENT NULL DELIMITER JES2 UNKNOWN
  span: [3, 6]
  name: TRANSACT         # 名前なしは null。上書き用の名前は "STEP.DD" のように原文どおり
  positional: ["*"]      # 位置パラメータ。省略された位置パラメータは null
  keywords:              # [キーワード, 値] の並び。順序は比較しない（多重集合として比較。JCL-FMT-004）
    - [DISP, [NEW, CATLG, DELETE]]
  comment: ["MY INPUT DATA SET"]   # 物理レコードごとのコメント欄（前後の空白を除く）。無ければ null
  inline_data: {records: [5, 7], terminator: DELIMITER, delimiter: "/*"}
  implicit: true          # システムが補う DD（JCL-DD-006）の場合のみ。span は null
  condition: {...}        # IF 文のみ
  operation: "EXCE"       # UNKNOWN の場合のみ、原文の操作フィールド
```

**Value の表現**

| JCL の記述 | Value |
|---|---|
| `SYSDA` | `"SYSDA"`（数値も文字列のまま） |
| `'O''NEIL'` | `{q: "O'NEIL"}`（囲みのアポストロフィを除き、二重のアポストロフィは 1 文字に戻す） |
| `(CYL,(1,1),RLSE)` | `["CYL", ["1", "1"], "RLSE"]` |
| `(,CATLG)` | `[null, "CATLG"]` |
| `(RECFM=FB,LRECL=80)` | `[{kw: [RECFM, FB]}, {kw: [LRECL, "80"]}]` |
| `VOLUME=SER=339023` | キーワード `VOLUME`、値 `{kw: [SER, "339023"]}` |
| `ACCT=`（値なし） | `null` |
| `DSN=APP.SYSTRAN(+1)` | `"APP.SYSTRAN(+1)"`（データセット名の括弧は Table 12 により名前の一部として扱う。世代番号の解釈は semantic 段階） |

`EXEC PGM=X` と `PROC=X` は、構文の形（K=V）に従って keywords に置く。IBM はこれらを位置パラメータに分類しているが（JCL-EXEC-001）、その判定は semantic 段階の責務とする。
symbol（`&HLQ.` など）は statements view では原文のまま保持する。

**inline_data.terminator**: `DELIMITER`（`/*` または DLM 文字）、`NEXT_STATEMENT`（次の `//` 文、DD * のみ）、`EOF`

**blocks**（任意）: `{kind: PROC|IF, name, start, else, end}`。対応する終了文が無い場合、end は null

**condition**（IF の関係式）:

- 比較: `{op: GT, left: X, right: Y}`
- 論理: `{op: AND|OR, args: [A, B]}`。左結合の二分木とする。AND と OR は同じ優先度で、記述順に評価される（JCL-IF-002）
- 否定: `{op: NOT, arg: X}`
- 被演算子: `{kw: RC, step: STEP1, procstep: null}`、`{num: 8}`

## view: exec_conditions（semantic）

```yaml
- step: STP4
  line: 5
  conds:
    - {qualifier: PAID, even: true, only: false, tests: [{code: 20, op: LT, step: null, procstep: null}]}
```

## view: dd_resources（semantic）

各 DD（連結の構成要素ごと）について、`step`、`ddname`（連結の先頭の名前）、`concat_index`、`line`、`dsn`、`generation`（整数または null）、`disp` を持つ。
`disp` は `{status, normal, abnormal, defaulted: [...]}` で、`defaulted` には JCL-DD-008 の既定値で補った項目を列挙する。DISP が意味を持たない DD（SYSOUT など）は null とする。

## view: substitutions / effective_statements（resolution）

- `substitutions`: `{line, keyword, before, after, status: RESOLVED|UNDEFINED_LEFT_LITERAL}`
- `effective_statements`: INCLUDE などを展開した後の文の並び `{kind, name, origin: {file, line}}`

## expected_diagnostics

`{mode: exact, items: [{code, severity, line, column?, file?}]}`。
期待値と実際の出力を多重集合として比較し、期待値に無い診断が出力された場合も不一致とする。
`column` は期待値に書いた場合だけ比較する。`file` を省略した場合は入力ファイルを指す。
`scope.lines` を指定したケース（実資産から一部の範囲を採ったもの）は、その範囲に収まる文と診断だけを比較する。

## 原文と正規化表現の分離（ADR-022, ADR-025。ユーザー決定 A5）

Golden View の値は原則として **正規化表現** とし、原本の情報は次の **原文** フィールドで保持する。比較は、期待値に書かれたフィールドについてだけ行う。

| 対象 | 正規化表現 | 原文 |
|---|---|---|
| コメント欄 | `comment`: 各レコードのコメント欄の前後空白を除いたテキスト | `comment_raw`: `{line, column, text}`。テキストは最初の非空白から最後の非空白まで（内部の空白はそのまま） |
| DSN | `dd_resources.dsn`（世代番号を除く名前）、`generation`（整数） | `dsn_raw`: 原文のとおり（例 `APP.SYSTRAN(+1)`、`&HLQ..X`）。statements view の値も原文のままとする |
| 暗黙の SYSIN DD | `implicit: true`、名前 `SYSIN`、`positional: ["*"]` | `implicit_basis`（例 `JCL-DD-006`）。実体の物理レコードは無いため `span: null` とし、データの物理範囲は `inline_data.records` で保持する |
| 字句（lexical view） | `parameter_text`（継続を連結した論理テキスト）、`tokens` | `records[].raw`（物理レコードの全文）、`seq`（73-80 桁）、各フィールドの `line` / `column` |

## 静的に確定できない値（ADR-022。ユーザー決定 A1）

`dd_resources.disp.normal` と `abnormal` には、固定値の代わりに次の形を書ける。

```yaml
normal: {runtime_dependent: {if_new: DELETE, if_existing: KEEP, basis: "JCL-DD-008 + JCL-DD-012"}}
```

既存データセットの有無は推測しない。

## Environment（ADR-021。ユーザー決定 A2）

`environment.jes` の値は `JES2` / `JES3` / `UNKNOWN`。`UNKNOWN` の場合、JES に依存する期待値は確定しない（ケースは blocked）。

## view: lexical（Step 4a。lexical 段階）

```yaml
view: lexical
records:                       # すべての物理レコード（欠落なし）
  - {line: 3, kind: STATEMENT_START, continues: PARAMETER, seq: "00030000", raw: "..."}
lexical_statements:            # STATEMENT_START とその継続レコードから成る字句上の文
  - span: [3, 5]               # 最初と最後のレコード
    lines: [3, 5]              # 文に属するレコード（間に挟まるコメント文は含まない）
    name: {text: DD1, line: 3, column: 3}      # 解釈しない。名前の妥当性は Parser が判定する
    operation: {text: DD, line: 3, column: 12} # 原文のまま。JOB/EXEC/DD の分類はしない
    parameter_text: "DSN=A.B,DISP=SHR"
    comments: [{line: 3, column: 40, text: "..."}]
    tokens: [[WORD, DSN], [EQUALS, "="], [STRING, "O'NEIL"], ...]   # STRING は値（二重アポストロフィを解除したもの）
    end: COMPLETE | NULL_STATEMENT | MISSING_CONTINUATION | END_OF_INPUT
```

- **records.kind**: STATEMENT_START、CONTINUATION、COMMENT、NULL、DELIMITER（`/*` の後が空白）、JES2（`/*` の後が非空白）、OTHER（上記以外。原文のまま保持し、データか不正かは後続の工程が判定する）
- **continues**: PARAMETER、QUOTED（アポストロフィ内で 71 桁に達した）、COMMENT（72 桁が非空白）
- **IF 文の扱い**: 関係式に空白を含むため、操作フィールドが `IF` のときに限り、字句規則として THEN までを parameter とする（JCL-IF-004）。parameter_text はレコード間を空白 1 つで連結する
- **Step 4a の制約**: レコードは先頭の文字だけで分類する。DD DATA の中にある `//` レコードは STATEMENT_START と判定されるため、インストリームの文脈を知る後続工程で再分類する

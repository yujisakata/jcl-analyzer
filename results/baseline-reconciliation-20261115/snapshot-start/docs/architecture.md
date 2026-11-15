# JCL Profiler Architecture

正式要件: [requirements.md](requirements.md)。設計判断: [decisions.md](decisions.md)。IBM規則: [../specs/ibm-jcl-reference.md](../specs/ibm-jcl-reference.md)。

## レイヤー構成（Context / Harness / Loop Engineering）

```
                 +-------------------------------+
                 |          Loop Layer           |  (Step 3以降: 失敗分類・改善FSM)
                 +---------------+---------------+
                                 | 失敗/結果
+----------------+   +-----------v-----------+   +-------------------+
| Context Layer  |-->| Deterministic Analyzer|-->|   Harness Layer   |
| config, rules, |   | inventory → lexer →   |   | pytest, golden,   |
| source registry|   | parser → resolver ... |   | acceptance, envck |
+----------------+   +-----------------------+   +-------------------+
        ^                        |
        |                        v
  入力資産（読取専用）     results/（解析結果）
```

## モジュール配置（現時点）

| パス | レイヤー | 責務 | 状態 |
|---|---|---|---|
| `config/profiler.yaml` | Context | ルート、分類規則、除外規則、文字コード | Step 2 |
| `specs/ibm-jcl-reference.md` | Context | Specification Registry（ルールID ⇔ IBM文献） | Step 2 |
| `src/jclprof/context/config.py` | Context | 設定ファイルの読込み・検証 | Step 2 |
| `src/jclprof/context/globmatch.py` | Context | `**` 付き glob の決定的なマッチング | Step 2 |
| `src/jclprof/diagnostics.py` | 共通 | 診断コード体系・Diagnostic 型 | Step 2 |
| `src/jclprof/ids.py` | 共通 | 再現可能な識別子の生成 | Step 2 |
| `src/jclprof/inventory/model.py` | Analyzer | SourceFile 等の型付きモデル | Step 2 |
| `src/jclprof/inventory/collector.py` | Analyzer | 資産収集・分類・ハッシュ・物理統計 | Step 2 |
| `src/jclprof/inventory/writers.py` | Analyzer | JSON / CSV / SQLite / Markdown 出力 | Step 2 |
| `src/jclprof/envcheck.py` | Harness | 開発環境と入力への読取りアクセスの検査 | Step 1 |
| `src/jclprof/cli.py` | 共通 | `jclprof envcheck` / `jclprof inventory` | Step 1-2 |
| `tests/unit/` | Harness | 単体テスト（合成フィクスチャ） | Step 1-2 |
| `tests/acceptance/` | Harness | 実資産に対する受入テスト（独立に計測した期待値） | Step 2 |
| `specs/rules.yaml` / `specs/diagnostic-catalog.yaml` / `specs/golden-schema.json` | Context | 規則レジストリ（正本）、診断コード体系、Golden 定義のスキーマ | Step 3 |
| `docs/golden-view.md` | Context | Golden View（比較用の構造）の契約 | Step 3 |
| `src/jclprof/harness/registry.py` / `loader.py` | Harness | H-01 規則・診断カタログの読込み、Golden Loader とスキーマ・意味の検証 | Step 3 |
| `src/jclprof/harness/comparator.py` | Harness | H-02 構造比較と診断比較 | Step 3 |
| `src/jclprof/harness/adapters.py` | Harness | 解析器との接続点（StageAdapter）。Step 3 では空 | Step 3 |
| `src/jclprof/harness/jclgen.py` / `strategies.py` | Harness | H-03 構文上許される変形の生成と Hypothesis 戦略 | Step 3 |
| `src/jclprof/harness/integrity.py` | Harness | H-04 マニフェストと baseline による変更検出（封印は手動のみ） | Step 3 |
| `src/jclprof/harness/runner.py` | Harness | H-05 実行と 5 状態の報告 | Step 3 |
| `src/jclprof/harness/render.py` | Context | ibm-jcl-reference.md の生成 | Step 3 |
| `tools/quality_gate.py` | Harness/Loop | H-06 品質ゲートの一括実行 | Step 3 |
| `tools/golden_authoring/` | Harness | Golden 入力の桁の固定と source_reference の挿入（作成補助。オラクルではない） | Step 3 |
| `tests/harness/` | Harness | Harness 自体のテスト | Step 3 |
| `tests/golden/` | Harness | Golden Test 89 件（cases、inputs、libs、MANIFEST.json） | Step 3 |
| `tests/parser/` / `tests/property/` | Harness | Parser 検証スイート（Step 4 以降。現在は NOT_IMPLEMENTED） | Step 3 |
| `src/jclprof/lexer/` | Analyzer | Step 4a Lexer: 物理レコード、カラム、継続、引用符、括弧、トークン、位置、字句診断。JOB/EXEC/DD の分類はしない（ADR-024） | Step 4a |
| `src/jclprof/lexer/adapter.py` | Harness | Lexer を lexical 段階の Golden に接続する | Step 4a |
| `tests/lexer/` | Analyzer テスト | IBM 本文から先に書いた Lexer のテスト、I/O の安全性、全実資産の欠落なし | Step 4a |
| `tests/property/test_lexer_properties.py` | Analyzer テスト | 継続・引用符・カラム境界の property テスト、欠落なし、決定性 | Step 4a |
| `tools/golden_review/make_packet.py` | Harness | 独立レビュー資料の生成（docs/reviews/） | Step 4a |
| `tests/regression/` | Harness | Loop Layer で使う予定 | 未着手 |

## データフロー（Step 2）

1. `config.load()` で設定を読み込み、検証する（ルートの存在、出力先がルート外であること）
2. `collector.collect()` が各ルートを相対パス順に再帰走査する
   - 除外規則に一致したファイルは `excluded` に規則IDとともに記録する（黙って捨てない）
   - 分類規則を順に評価し、最初に一致した規則で資産種別を決める（規則IDを証拠として保持）
   - バイト列から SHA-256 を計算し、設定した文字コードで strict デコードを試みる
   - デコードできたファイルについて物理レコード統計を取る
3. `writers` が `results/inventory/` に決定的な成果物を、`run_meta.json` に可変メタデータを書き出す

## 不変条件

- 入力ファイルは `rb` でのみ開く。書込み・削除・属性変更は行わない
- 出力先は入力ルートの外にあること（違反時は終了コード 2）
- 成果物の並び順は (root順, 相対パス) で固定する
- 対象ファイルは必ず `source_files` か `excluded` のどちらかに現れる（登録率100%）

## 文字コードの解決（ADR-009）

```
encoding.overrides（パターン, 最初に一致したもの）
        │ 一致しない
        ▼
asset_types.<種別>.encoding_profile → encoding.profiles.<名前>
        │ 指定なし
        ▼
encoding.default
```

解決した値が null の場合は ENCODING_UNDETERMINED とし、デコードしない（INV-I004）。
判定の根拠は `encoding_basis`（`override:<pattern>` / `profile:<name>` / `default`）としてすべての SourceFile に記録する。

## Environment Profile（ADR-010, ADR-011。Step 5 で実装）

| 要素 | 定義元 | 状態 |
|---|---|---|
| データセット名 → ローカルフォルダの対応 | `config/profiler.yaml` の `datasets` | スキーマと検証は実装済み。登録 0件（ユーザーの確認待ち） |
| PROC の別名 | `datasets[].aliases` | スキーマは実装済み |
| システム PROCLIB の探索順序 | Environment Profile（未定義） | 未確定 |
| EBCDIC コードページ | `encoding.profiles.data` | 未確定（null） |

### PROC 解決の設計（ADR-011）

- 識別子は (ライブラリ DSN, メンバー名) とする。別名は明示的に設定されたものに限る
- `ProcedureDefinition.label`（PROC 文の名前フィールド）は別の属性として保持し、解決には使わない。メンバー名と一致しない場合は診断する
- 探索順序: インストリーム PROC → JCLLIB ORDER の順 → システム PROCLIB。各段階に対応する IBM 規則IDを Step 3 で登録する
- 未登録の DSN、見つからないメンバー、候補が複数ある場合は、いずれも Dependency の status（RESOLVED / UNRESOLVED / AMBIGUOUS / ENVIRONMENT_GAP）として記録し、推測では補完しない

## CLI（ADR-008, ADR-013）

`jclprof {envcheck|inventory} [PATH ...] [--config FILE] --output DIR`
位置引数の PATH は設定ファイルの roots を置き換える。設定ファイルの root と同じディレクトリを指す場合は、その root の ID を引き継ぐ。

## Harness のデータフロー（Step 3）

```
specs/rules.yaml ──┐
diagnostic-catalog ┼─> Loader（スキーマ + 意味の検査）─> GoldenCase[] ─> Runner ─> golden_run.json / .md
golden-schema.json ┘            ^                                        │   （5 状態を別々に集計）
tests/golden/cases/*.yaml ──────┘                                        v
                                                         StageAdapter（Step 4/5 で登録）
                                                                         │ Golden View
                                                                         v
                                                                    Comparator
MANIFEST.json + .baseline ─> Integrity（読取り専用）。封印は `golden-seal --by` による手動操作のみ
```

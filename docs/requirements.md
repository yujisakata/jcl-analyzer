# JCL Profiler 実装要件定義書
**Version:** 1.0  
**Status:** 正式ベースライン v1.0（2026-11-15 ユーザー承認。以後の変更は ADR と末尾の変更履歴に記録する）  
**Implementation Language:** Python 3.12系（導入時にサポート状況を確認し、パッチ版を固定）  
**Architecture:** Context / Harness / Loop Engineering  
**Primary Objective:** 対象JCL資産に必要なBatch IRの最小機能集合を実証的に決定する

---

## 1. 目的とスコープ

### 1.1 目的

本システムは、メインフレーム環境で使用されるJCL資産を静的に解析し、実際に使用されている構文、パラメータ、実行制御、データセット操作、依存関係を網羅的に収集・分類する。

解析結果を根拠として、Javaバッチへのモダナイゼーションで必要となる中間表現（Batch IR）の機能範囲、変換難易度、実装優先順位を決定する。

### 1.2 必須成果物

1. **JCL Inventory**：ジョブ、STEP、DD、構文、パラメータの一覧
2. **JCL AST**：物理行と論理文の対応を保持した構文木
3. **Effective Job Model**：PROC展開とシンボル解決後の実効ジョブモデル
4. **Dependency Graph**：JOB、PROC、PGM、DD、データセット間の依存関係
5. **Semantic Capability Matrix**：必要な実行意味と対応状況
6. **IR Candidate Catalog**：Batch IR候補とその必要性を示す証拠
7. **Verification Evidence**：検証結果、未解析箇所、既知の制約

### 1.3 対象範囲

初期段階ではz/OS MVS JCLを対象とし、主に以下を解析する。

- JOB、EXEC、DD
- PROC、PEND、JCLLIB、INCLUDE、SET
- IF、THEN、ELSE、ENDIF、COND
- DSN、DISP、DCB、SPACE、UNIT、SYSOUT
- DD連結、GDG相対世代、STEPLIB、JOBLIB
- DD *、DD DATA、DLMによるインストリームデータ
- JES固有文、製品固有拡張、未知構文の検出

未知構文についても、元の記述と出現位置を保存し、無視して正常終了扱いにしてはならない。

### 1.4 対象外

初期版では、JCLからBash等への本番用コード生成、Javaバッチの実行、VSAM実データの内容解析、JESによる実ジョブ投入は行わない。

COBOLソースとの照合は拡張ポイントを定義するが、初期版の必須機能とはしない。

### 1.5 設計原則

- 原本不変：JCLファイルは読み取り専用で扱う。
- 証拠追跡：解析結果から元ファイル、行、列まで逆引きできる。
- 非推測：未解決の環境依存要素を推測値で補完しない。
- 意味分離：構文認識、参照解決、実行意味分類を独立させる。
- 決定論：同一入力・同一設定・同一バージョンでは同一結果を生成する。
- 機能限定：IR候補は実資産に現れた実行意味から導出する。
- 検証独立：解析器自身の出力を正解として採用しない。

---

## 2. システムアーキテクチャ

### 2.1 Context Layer

解析の根拠となる情報を管理する。

**構成要素**

- Source Registry：入力ファイル、文字コード、SHA-256、取得元、版
- Specification Registry：IBM仕様の版、規則ID、適用条件
- Symbol Context：JCLシンボルと解決スコープ
- Procedure Context：PROC定義、参照先、呼出し階層
- Environment Profile：JES、JCLLIB探索順序、サイト固有設定
- Dependency Registry：外部参照と解決状況
- Analysis History：解析設定、ツールバージョン、過去の結果

**要件 CTX-01**

すべての解析結果には、元ファイルの識別子、物理行番号、列範囲、関連する論理文IDを付与する。

**要件 CTX-02**

入力文字コードを明示的に指定できること。UTF-8および対象環境で必要なEBCDICコードページを扱い、デコード失敗は診断情報として残す。

**要件 CTX-03**

PROCおよびINCLUDEの検索は、設定された探索順序と参照元コンテキストに従い、未解決参照を別状態として記録する。

**要件 CTX-04**

未定義シンボル、環境依存シンボル、実行時にしか確定しない値を区別し、解決不能な値を暗黙に空文字へ変換しない。

**要件 CTX-05**

IBM仕様への対応関係をルールIDで管理する。解析規則を変更した場合、影響を受けるテストと資産を追跡できること。

### 2.2 Deterministic Analyzer

Pythonで実装する中核解析系。次の責務を独立したモジュールとする。

**Lexer**

物理レコードからJCLトークンを抽出する。継続行、引用符、コメント、桁位置、インストリームデータを識別する。

**Parser**

トークン列から構文木を構築する。JOB、STEP、DD、PROC、IFブロック等の親子関係を表現する。

**Resolver**

PROC、INCLUDE、シンボル、オーバーライドを解決し、実効ジョブ構造を復元する。原本のASTは変更せず、別モデルを生成する。

**Semantic Classifier**

実行対象、資源割当、条件制御、データセット世代、入出力などの意味的機能を分類する。

**Inventory Aggregator**

構文・パラメータ・値・組合せの出現頻度、利用ジョブ数、未解決件数を計算する。

**Capability Analyzer**

ジョブごとに必要な実行機能を列挙し、IRで表現すべき操作の候補集合を生成する。

### 2.3 Harness Layer

解析器の正しさを評価する独立した検証基盤。

入力フィクスチャ、期待結果、比較ルール、失敗再現手順、テスト実行履歴、品質ゲートを管理する。

本番JCL原本の更新権限を持たず、解析結果と検証結果は別ディレクトリに保存する。

### 2.4 Loop Layer

検証結果から改善対象を抽出する反復実装の制御基盤。

失敗の分類、再現ケースの縮小、修正候補の生成、限定試験、全回帰試験、承認の各段階を明示する。

LLM利用は任意とし、LLMが存在しなくても解析・検証・レポート生成が動作すること。

---

## 3. 機能要件

### FR-01 入力資産収集

指定ディレクトリ以下のJCL、PROC、INCLUDEライブラリを再帰的に収集する。

複数のルートディレクトリ、拡張子、ファイル名パターン、探索除外条件を設定できること。

同一名のPROCが複数存在する場合、探索順序に従って解決し、候補と選択根拠を記録する。

### FR-02 物理行・論理文解析

以下を正しく認識する。

- 標準的なJCL文の開始
- オペランド継続
- カラム規則と継続標識
- 引用文字列と引用符のエスケープ
- カンマを含む括弧内パラメータ
- コメント文
- インストリームデータと終了区切り
- 空文、区切り文、未知文

例えば次の記述を、1つのDD文として解析する。

```jcl
//TRANSACT DD DISP=(NEW,CATLG,DELETE),
//         UNIT=SYSDA,
//         SPACE=(CYL,(1,1),RLSE),
//         DSN=APP.SYSTRAN(+1)
```

単純なカンマ分割によって括弧内部のパラメータを誤分割してはならない。

### FR-03 AST生成

ASTは、JOB、STEP、Statement、Operand、ParameterValue、ConditionalBlock、ProcedureDefinition、InlineDataなどの型付きノードで構成する。

各ノードにID、種類、親ID、原文、位置情報、診断情報を保持する。

解析不能箇所が存在しても、可能な範囲で後続の独立した文の解析を継続する。ただし、信頼できない領域は明示的にマークする。

### FR-04 EXEC解析

EXEC PGM、EXEC PROC、位置指定のPROC呼出しを識別する。

PARM、COND、TIME、REGION等のオペランドを保存し、STEPと実行対象を関連付ける。

プログラム名からJavaプログラム名を推測する機能は設けない。

### FR-05 DD解析

DD名、属性、連結関係、リソース参照形式を解析する。

最低限、以下を識別する。

- DSNによるデータセット参照
- GDG相対世代指定
- DISPの割当・正常終了・異常終了時指定
- DCBのレコード属性
- SYSOUT
- DUMMY
- DD *、DD DATA
- DD名参照
- 名前なしDDによる連結
- PATHによるUSSファイル参照

データセット種別がDSNだけでは確定しない場合はUNKNOWNとし、カタログメタデータから補完可能な拡張インターフェースを設ける。

### FR-06 PROC・INCLUDE解決

PROC呼出しとINCLUDEによる参照関係を解決する。

PROCパラメータ、STEP修飾付きオーバーライド、DDオーバーライド、ネストした参照を扱う。

展開結果は元の定義と呼出し箇所の両方へ追跡できること。

循環参照、参照先欠落、許容範囲を超える展開は診断情報を出力し、安全に終了する。

### FR-07 実行条件解析

IF / ELSE / ENDIFとCONDを解析し、条件式ASTを生成する。

戻りコード、ABEND、条件演算子、論理演算子、STEP参照を識別する。

**静的解析時に実際の実行経路を一意に決められない場合、条件式を保持し、経路を確定したかのように出力しない。**

### FR-08 実効ジョブモデル

JOBとSTEPの一覧、実行対象、条件、論理資源、解決済み・未解決の依存関係を統一形式で生成する。

原本ASTと実効ジョブモデルを別々に永続化する。

### FR-09 構文・意味インベントリ

以下の粒度で集計する。

1. 文種別
2. オペランド名
3. パラメータ値
4. 正規化したパラメータ組合せ
5. STEP構成パターン
6. ジョブ単位の機能集合
7. 未対応・未解決の構文
8. 実行意味上の依存関係

異なるDSN文字列だけで別パターンとみなさず、値の型と操作意味に基づく正規化を行う。

### FR-10 Capability Analysis

各STEP・JOBについて、必要な実行機能を特定する。

初期候補は以下とする。

- ProgramExecution
- ParameterPassing
- ResourceBinding
- DatasetAllocation
- DatasetConcatenation
- DatasetDisposition
- GenerationResolution
- ConditionalExecution
- ProcedureExpansion
- InlineDataBinding
- OutputRouting

これらは固定仕様ではなく、実資産解析により追加・分割・統合する候補である。

Capabilityには、根拠となるJCL構文と解析規則IDを付与する。

### FR-11 IR候補抽出

Capabilityの組合せからIRの型候補、属性候補、利用ジョブ数を出力する。

各候補には以下を付与する。

- 必要とするJCL資産
- 出現頻度
- 利用ジョブ数
- 意味解析の確度
- 必要なRuntime機能
- 検証済みか否か
- 未解決の設計判断

### FR-12 出力

JSON、CSV、SQLiteへの出力を必須とする。

人間向けにMarkdownレポートを生成する。HTML可視化は追加機能とする。

---

## 4. データモデル要件

少なくとも以下のエンティティを保持する。

| Entity | 主な属性 |
|---|---|
| SourceFile | ID、path、hash、encoding、version |
| PhysicalRecord | source ID、line、raw bytes reference |
| LogicalStatement | statement ID、kind、source spans |
| ASTNode | ID、type、parent、attributes |
| Job | ID、name、source |
| Step | ID、job ID、name、program/procedure |
| DDDefinition | ID、step ID、ddname、parameters |
| ResourceReference | kind、name、generation、attributes |
| SymbolReference | name、scope、resolution status |
| ProcedureInvocation | caller、target、overrides |
| Dependency | source、target、kind、status |
| Capability | capability ID、scope、evidence |
| Diagnostic | code、severity、location、message |
| VerificationResult | test ID、expected、actual、status |

識別子は、元ソースの内容・位置・スコープから再現可能な方法で生成する。表示順序や実行環境に依存するランダムIDを、同一性判定の基準にしてはならない。

---

## 5. CLI要件

以下のコマンド体系を提供する。

```bash
jclprof inventory ./corpus --config profiler.yaml

jclprof parse ./corpus --output results/ast

jclprof resolve ./corpus --config profiler.yaml

jclprof analyze ./corpus --output results

jclprof capabilities results/analysis.db

jclprof report results/analysis.db --format markdown

jclprof verify --suite tests/fixtures

jclprof diff baseline/analysis.db candidate/analysis.db
```

`analyze`は収集、パース、参照解決、分類、集計のパイプラインを実行する。

`verify`は独立したテストハーネスを実行する。

`diff`は修正前後における構文認識率、意味分類結果、未解決参照、Capability集合の差分を出力する。

解析結果の形式とCLI終了コードをバージョン付きで固定する。

---

## 6. 検証ハーネス要件

### 6.1 検証の基本原則

検証は、単にパース時の例外が発生しないことを確認する作業ではない。

次の5段階を独立して検証する。

1. 字句認識が正しい
2. 構文木が正しい
3. 参照解決が正しい
4. 意味分類が正しい
5. 資産全体の集計が正しい

解析器自身が生成した期待値と解析結果を比較する自己確認だけでは合格としない。

### 6.2 Golden Test

IBM仕様から手作業で設計した例、レビュー済みの実資産例、正常系・異常系の人工JCLを入力として準備する。

期待AST、依存関係、Capability集合を解析器とは独立に作成する。

例：

```yaml
test_id: JCL-DD-001
description: GDG output allocation
input: fixtures/gdg_output.jcl

expected:
  statement_count: 2
  job_count: 1
  step_count: 1
  dd_count: 1
  capabilities:
    - ProgramExecution
    - DatasetAllocation
    - DatasetDisposition
    - GenerationResolution
```

Goldenの更新はレビュー承認を必須とし、テスト失敗を解消する目的で自動的に期待値を書き換えてはならない。

### 6.3 Property-Based Test

Hypothesisを使用し、構文上有効な入力のバリエーションを自動生成する。

検証する性質の例：

- 許容される継続行の分割位置を変えても意味ASTが一致する。
- コメントの挿入によって実行意味分類が変わらない。
- DSNを別の有効な名前へ変更してもCapability種別は不変である。
- DDの属性順序が仕様上交換可能な場合、意味モデルが一致する。
- 単純なPGM実行からPROC呼出しへ等価変形した場合、実効ステップの必要機能が一致する。

前提条件を満たさない入力には、性質の不変性を仮定しない。

### 6.4 Metamorphic Test

単独の完全な正解を求めにくい場合でも、入力と出力の関係を検証する。

具体例：

- 空白・継続行の合法的な変更
- PROCの同等なインライン展開
- 論理的に等価な条件式への変換
- 独立したジョブの追加
- 同一ファイルの重複読込み防止

### 6.5 Differential Test

利用可能な場合、z/OSのJCLチェック機能や公式に評価可能な参照実装と比較する。

対象はJCLの受理可否、展開結果、条件制御などとし、環境固有機能や取得可能な情報の制約を明示する。

参照実装との一致を、すべての実行意味が等価であることの証明と取り違えない。

### 6.6 Mutation Test

解析器のコードへ意図的な変更を加え、テストが異常を検出できるかを測定する。

例：

- DD連結の検出条件を逆転する
- PROCオーバーライドの優先順位を変更する
- DISPの正常終了指定を無視する
- IF条件の比較演算子を反転する
- GDG世代符号を反転する

Mutation Scoreを測定し、重要な変異が生存した場合は追加テストを要求する。

### 6.7 実資産を用いた検証

実JCLから層化抽出したサンプルを、人手で精査する。

層化軸は文種別、PROC利用有無、条件制御、DD種類、複雑度、解析警告の有無とする。

頻出パターンだけでなく、低頻度・高リスクの構文を必ず含める。

### 6.8 異常系・安全性テスト

以下を必須とする。

- 不正な継続行
- 閉じられていない引用符
- 不均衡な括弧
- 未終端のインストリームデータ
- PROC循環参照
- 未定義シンボル
- 不正な文字コード
- 巨大なJCLファイル
- 異常に深いネスト
- 解決不能なINCLUDE

プロファイラはJCLを**実行せず**、解析対象に含まれる制御文やプログラム呼出しをOSコマンドとして評価してはならない。

---

## 7. Loop Engineering要件

### 7.1 改善ループ

以下の有限状態機械で管理する。

```text
COLLECT_FAILURES
       |
       v
CLASSIFY_FAILURES
       |
       v
SELECT_FIX_TARGET
       |
       v
PROPOSE_CHANGE
       |
       v
RUN_FOCUSED_TESTS
       |
       v
RUN_REGRESSION
       |
       v
EVALUATE_GATE
   |       |
 PASS     FAIL
   |       |
   v       v
REVIEW   RETRY / ESCALATE
   |
   v
ACCEPT / REJECT
```

### 7.2 失敗分類

- LEXICAL_ERROR：字句認識の誤り
- PARSE_ERROR：構文構造の誤り
- RESOLUTION_ERROR：PROC等の参照解決誤り
- SEMANTIC_ERROR：実行意味の誤分類
- COVERAGE_GAP：未対応構文
- SPEC_AMBIGUITY：仕様上の解釈不確定
- ENVIRONMENT_GAP：環境情報不足
- TEST_ORACLE_ISSUE：期待値自体の問題
- PERFORMANCE_REGRESSION：性能劣化

### 7.3 修正対象の選定

修正候補は以下を基準に優先順位を決める。

- 影響を受けるジョブ数
- 重要業務への影響
- 構文・意味解析の誤りの重大性
- 実装コスト
- 検証方法の独立性
- 現在のIR検討への寄与

### 7.4 自動改善の制約

LLMが提案する修正は、独立した作業領域に適用する。

次を禁止する。

- Golden期待値の無承認変更
- 検証対象テストの無断削除
- 失敗を警告へ格下げするだけの修正
- 解析不能箇所を成功扱いする変更
- テスト結果を利用した正解データの自動再生成

### 7.5 ループ停止条件

以下のいずれかで停止する。

- 事前定義した品質ゲートを満たす
- 最大反復回数に達する
- 同一原因の失敗が解消しない
- 重要な回帰不具合が発生する
- 仕様不明のため外部確認が必要
- 実装範囲変更の承認が必要

デフォルトの自動修正反復上限を5回とし、上限値を設定可能にする。

---

## 8. 非機能要件

### 8.1 技術選択

- Python 3.12系
- 標準ライブラリを優先
- 型付きデータモデル
- SQLiteによる構造化結果保存
- JSON Schemaによる外部出力検証
- pytestによるテスト
- Hypothesisによる性質ベーステスト
- Ruff、mypyによる静的品質管理
- 必要に応じてmutmut等でMutation Test

パーサーは構文・字句処理の責務を明確化し、正規表現の寄せ集めに依存しない。

### 8.2 再現性

同一入力、同一設定、同一バージョンで解析結果が一致すること。

結果の並び順、ハッシュ、識別子を安定化し、実行時刻等の可変メタデータを比較対象から分離する。

### 8.3 性能

初期性能目標は、10万物理行を含むJCL資産について、8 vCPU・16 GBメモリの基準環境で解析処理60秒以内とする。

ただし、この数値は採用前に実資産を使ってベースラインを測定し、正式なSLOを確定する。

### 8.4 セキュリティ

- 原本は読み取り専用
- JCLやSYSINを実行しない
- 外部コマンド実行は禁止
- PROC参照は許可されたライブラリ内に限定
- 解析時に原本を外部LLMへ送信しないことを初期設定とする
- LLM利用時は機密区分と送信可能範囲を明示する
- ログとレポートでは機密情報を必要に応じてマスキングする

### 8.5 診断可能性

すべての解析警告とエラーに、コード、重大度、ファイル、行、列、原因、推奨対処を付与する。

収集・解析・解決・意味分類の各段階の処理件数、時間、失敗件数を記録する。

---

## 9. 受入基準

### 9.1 正確性

- 合意済みの必須Golden Test：100%合格
- 特定した重大な意味解析誤り：0件
- 主要なProperty / Metamorphic Test：100%合格
- 重要なMutationの生存：0件
- 未解決の重大な仕様解釈：0件（リリース対象範囲内）

### 9.2 網羅性

- 入力ファイル登録率：100%
- 物理行の分類・帰属率：100%
- 未認識文の原文保存率：100%
- PROC/INCLUDEの未解決参照を全件報告
- 対象資産の全ジョブについてCapability評価結果または阻害理由を出力

物理行の分類ができたことは、意味解析が完了したことを意味しない。

### 9.3 集計整合性

ジョブ、STEP、DD、構文出現数について、独立に計測した検査値と一致すること。

ジョブ・STEP・DD間の参照整合性をチェックする。

### 9.4 IR候補としての有用性

少なくとも以下が説明できること。

- 対象ジョブに必要な実行意味は何か
- 各意味機能は何ジョブに使われているか
- 実装すると何ジョブが追加で対象になるか
- 未対応のために移行できないジョブはどれか
- 各IR機能候補の根拠となるJCLはどれか

---

## 10. 開発マイルストーン

### M0：仕様・テストベースライン

IBM JCL仕様の適用範囲、環境設定、初期フィクスチャ、品質ゲートを確定する。

**完了条件**：独立したGolden Test群と診断コード体系が完成。

### M1：Lexer / Parser

JOB、EXEC、DD、継続行、コメント、インストリームデータを実装する。

**完了条件**：該当Golden Testに100%合格し、原文位置情報を保持。

### M2：Resolver

PROC、INCLUDE、シンボル、条件制御、DD連結を実装する。

**完了条件**：実効ジョブ構造を独立した期待結果と比較して検証。

### M3：Inventory / Capability Analysis

構文・意味パターンの分類、SQLite保存、集計、レポートを実装する。

**完了条件**：実資産の各ジョブについてCapability集合または阻害理由が確認可能。

### M4：検証とIR範囲決定

実資産の層化サンプルを使い、回帰・Mutation・差分検証を実施する。

**完了条件**：IR候補、対応範囲、未解決課題、優先順位についてレビュー承認を取得。

---

## 11. 最終的なDoneの定義

本プロジェクトの完了は、「JCLをすべて読めること」ではない。

次の条件を満たした段階を、IR設計に進むための正式な完了条件とする。

**対象資産に実際に必要な実行意味の集合を、元JCLに追跡可能な証拠をもって提示できること。**

**それらの意味を表現するために必要なBatch IRの候補を特定し、対象ジョブの対応可能性と未解決の差分を定量的に示せること。**

**その判断が、独立した検証ハーネスによって裏付けられていること。**

この3条件を満たした後、次工程としてBatch IR仕様の確定と、IRからPOSIX Shell等へのコード生成器開発を開始する。

---

## 変更履歴

本書を v1.0 正式ベースラインとした後の要件変更・解釈の確定は、ここに記録する。詳細な根拠は `docs/decisions.md` の ADR を参照。

| 日付 | 版 | 内容 | ADR |
|---|---|---|---|
| 2026-11-15 | 1.0 | 「実装ベースライン案」を v1.0 正式ベースラインとして承認（ユーザー決定 A6） | ADR-014 |
| 2026-11-15 | 1.0 | CTX-02 の具体化: JCL/PROC 系とデータファイルの文字コード設定を分離する。未確定のコードページは推測せず、「未確定」として記録する（A1） | ADR-009 |
| 2026-11-15 | 1.0 | CTX-03 / FR-06 の具体化: データセット名とローカルフォルダの対応は明示的な設定でのみ与える（A2）。カタログ PROC はライブラリのメンバー名または別名で解決し、PROC 文のラベルは別属性とする。JCLLIB ORDER の探索順序に対応する（A3） | ADR-010, ADR-011 |
| 2026-11-15 | 1.0 | CTX-05 の具体化: 仕様レジストリに、規則ごとの公式URL・版・節・確認状況を記録する（A4） | ADR-012 |
| 2026-11-15 | 1.0 | 5章 CLI の具体化: 位置引数で解析対象を指定でき、設定ファイルの指定も維持する。両方を指定した場合の優先順位を定義する（A5） | ADR-013 |
| 2026-11-15 | 1.0 | 6 章（検証）の具体化: Golden View に JOB→STEP→DD の階層表現を加え、期待値に依存しない階層検査を導入する。レビュー待ちの期待値は未封印の別スイートに置く（R1） | ADR-027 |
| 2026-11-15 | 1.0 | 品質ゲートを Gate A（開発健全性）と Gate B（Parser 正式受入れ）に分け、既知欠陥台帳と受入れ範囲ファイルを導入する（R1） | ADR-028 |

# JCL Profiler Step 4b 独立品質監査

監査日: 2026-11-15（JST）。対象: `D:\projects\jcl-profiler`。

**判定: Step 4b の完了承認は推奨しない。** 既存ゲートは PASS するが、構造・データ境界を誤る高重大度の欠陥が残る。独立プローブ24件中、正常系8件は合格、反例16件は要件不適合。これは16種類の欠陥という意味ではなく、以下の指摘に集約する。修正は行っていない。

## 監査範囲と方法

最初に CLAUDE.md、docs/requirements.md、docs/architecture.md、specs/rules.yaml を読んだ。目的は、実JCLから必要最小限のBatch IR機能を証拠付きで導くこと。原本不変、非推測、解析段階の分離、位置への逆引き、独立検証が主要な制約である。

Parser・値パーサー・モデル・Adapter、Lexerの関連処理、HarnessのLoader・Comparator・Runner・Integrity・Trace、既存spec/property/corpusテスト、Golden定義102件の一覧と期待値、品質ゲートを調査した。既知欠陥文書を結論の根拠にはせず、D-1〜D-3も独立入力で再現した。IBM資料はオンラインの公式本文・公式PDFの検索取得本文と照合した。z/OS 3.2のDLM本文は取得できたが、登録済み3.2 PDFはHTTP 403で直接取得できず、全体のSHA-256・全ページを再検証したとは主張しない。補足として3.1の公式本文を使用した箇所は明示する。

PROC展開、INCLUDE展開、シンボル解決、IF/COND意味解析の未実装は、Step 4bの明示的な範囲外として区別した。本監査はz/OS上でのジョブ投入試験ではない。

## 実行証拠

Python 3.12.15、既存 .venv を使用。以下はプロジェクトルートから実行する。

```powershell
.venv/Scripts/python.exe tools/quality_gate.py --output results/audit-20261115/gate-full
.venv/Scripts/python.exe results/audit-20261115/probes.py
```

| 検査 | 実測 |
|---|---|
| ruff | PASS |
| mypy | 67ファイル、PASS |
| Harness既存スイート | 204 passed、1 skipped（symlink権限） |
| Golden定義・封印整合性・rules同期 | 102件、すべてPASS |
| Golden実行 | 51 PASSED、0 FAILED、2 BLOCKED、49 NOT_IMPLEMENTED |
| Goldenの保証区分 | 全件REFERENCE。FORMALの実行合格0件 |
| Analyzer既存スイート | 129 passed、51 skipped、9 xfailed |
| 独立プローブ | 8 passed、16 failed、計24件 |
| 階層破壊への感度確認 | メモリ上で全JobNodeを除去してもGolden比較・check_traceがPASS |

初回ゲートは既存の `%TEMP%/pytest-of-yujis` へのアクセス拒否でHarness 128 errors、Analyzer 1 errorとなった。権限制限外で再実行した結果が上表。初回の環境エラーを製品欠陥には数えない。初回・再実行のログは両方保存した。

## 指摘一覧

| ID | 重大度 | 内容 | 対応プローブ |
|---|---|---|---|
| A01 | 高 | null後の所属をJES/NULLJCLにかかわらず確定 | N1、N2（既知D-1） |
| A02 | 高 | UNKNOWNでDLM解釈が分かれると構造候補が失われる | N4（既知D-2） |
| A03 | 中 | 継続直後のnullをジョブ終端候補として扱う | N3（既知D-3） |
| A04 | 高 | DLMの二重アンパサンドを復元せず後続STEPを飲み込む | D1 |
| A05 | 高 | DLM区切りコメントからの偽の継続で後続DDが消える | D2 |
| A06 | 高 | DLM文字列の前方一致だけでデータを打ち切る | D3 |
| A07 | 中 | JES別DLM文字数・空値制約を検査しない | D4の4件 |
| A08 | 中 | DD * + DLMの必須区切り欠落を診断しない | D5 |
| A09 | 中 | EXEC対象・DD位置パラメーターの構文制約不足 | E1〜E3 |
| A10 | 中 | EOFまでのインラインデータがJob.spanに入らない | T1 |
| A11 | 高 | Golden/Traceが階層破壊を検出せず、ゲートPASSが完了を保証しない | hierarchy-check.json、既存ゲート |

以下の入力は合成JCLであり、CardDemo原本の引用・変更ではない。完全な入力、期待、実測のSTEP/DD/文/診断/RecordRoleは `probe-results.json` に保存した。

## A01 — nullとJES2 NULLJCL（高、既知D-1の再確認）

場所: `src/jclprof/parser/parser.py:246` のnull_statement、251のnote_after_nullとplace。

再現: JES3で次をparse_textに渡す。UNKNOWNでも試す。

```jcl
//J JOB
//S EXEC PGM=X
//
//T EXEC PGM=Y
```

実測: JES3でもJ.steps=[S,T]、診断なし。UNKNOWNでは同じ所属にINFO PAR-I001が加わるだけ。JES2のNULLJCL設定を指定するAPIもない。

根拠: [IBM JES2 INPUTDEFの説明](https://www.ibm.com/docs/en/zos/3.1.0?topic=crs-d-inputdef-display-options-controlling-jes2-input-processing)はNULLJCL=IGNOREとEOFの違いを定義する。JES3/EOFでは後続の有効JOBまで読み飛ばす。JES2という指定だけでIGNOREを仮定できない。JCL-STMT-NULL、POL-003、要件1.5。

修正案: NULLJCLを環境入力に加え、確定環境では正しい所属を作る。未確定時は候補構造と未確定状態を保持する。原文を残しつつ、読み飛ばしと有効文を区別する。

検証: N1/N2に加え、JES2のIGNORE/EOF、UNKNOWN、次の有効JOBへの復帰、null後のDD/データの所属を独立オラクルで検査する。

## A02 — UNKNOWNのDLM候補消失（高、既知D-2の再確認）

場所: `parser.py:490` data_region、517 after_region。

再現（jes=UNKNOWN）:

```jcl
//J JOB
//S EXEC PGM=X
//D DD *,DLM=AA
 DATA
//T EXEC PGM=Y
AA
//U EXEC PGM=Z
```

実測: data_regionsにはJES2/JES3の境界候補があるが、Job.stepsは[S,U]のみ。TはRecordRole=UNDETERMINEDの範囲に埋まり、候補のStatement/Stepとして存在せず、Job自体に構造未確定の状態もない。原文は残るため、バイト消失ではなく構造候補の消失である。

根拠: [IBM z/OS 3.2 DLM parameter](https://www.ibm.com/docs/en/zos/3.2.0?topic=statement-dlm-parameter)はDD * + DLMでJES2のみ//による終了を認める。POL-003と要件FR-03により、未確定の所属を一方の構造に固定できない。

修正案: 境界候補から先の構文解釈も候補として保持するか、共通構造と条件付き構造を明示する。

検証: N4と同じ入力をJES2/JES3で別々に解析し、UNKNOWNの候補が両方を表せることを確認する。候補境界の一致・不一致、後続JOBの有無も検査する。

## A03 — 継続中のnullを終端にする（中、既知D-3の再確認）

場所: `parser.py:246`。Lexerはend=NULL_STATEMENTを保持しているがParserが利用しない。

再現: A01のnull直前に `//D DD DSN=A,` を挿入。

実測: null_statement_line=4、T.after_null=True。期待は両方とも非終端。

根拠: [IBM JCL Reference、Chapter 23 Null statement（3.1公式PDF）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)は、継続中の制御文直後のnullを空のコメント欄として扱う。JCL-CONT-007、ADR-025。

修正案: lexical statementの終了理由と直前の継続状態を参照し、通常のnull終端処理から除外する。Lexer原本の分類を上書きする必要はない。

検証: N3をJES2/JES3/UNKNOWNで実行し、null終端・after_null・PAR-I001が付かないことを確認する。

## A04 — DLMの&&を復元しない（高、新規）

場所: `parser.py:420`付近のDLM取り出し。STRINGのvalueをそのまま終端文字列にする。

再現（JES2）:

```jcl
//J JOB
//S EXEC PGM=X
//D DD DATA,DLM='&&@'
 DATA
&@
//T EXEC PGM=Y
```

実測: DLMを`&&@`の3文字とみなし、4〜6行目をデータにする。Tがなくなり、LEX-W002のみ。期待は5行目で終了、TをSTEPとして認識。

根拠: [IBM JCL Reference、DD DLM / Syntax（3.1公式PDF）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)ではDLM内の二重アンパサンド・二重アポストロフィは各1文字を表す。通常文字列の保持と、DLM照合用の復元値を区別する必要がある。

修正案: 原表記を保存し、DLM専用の復元値を作って照合する。シンボル解決とは切り分ける。

検証: D1、二重アポストロフィ、`&&`を含む2/18文字境界、同じ表記を通常PARMに使う対照例で確認する。

## A05 — 区切り行に由来する継続で後続DDを落とす（高、新規）

場所: `parser.py:550` drop_lex_in。境界をまたいだLexer文の残りをUNRECOGNIZEDにし、再解析しない。

再現（JES2）:

```jcl
//J JOB
//S EXEC PGM=X
//D DD DATA,DLM='//'
 DATA
// DD DSN=A,
//         DD DSN=B
//T EXEC PGM=Y
```

5行目は区切り`//`とコメントであり、末尾カンマにも継続の意味はない。6行目は独立した名前なしDD。

実測: 6行目がPAR-W006・UNRECOGNIZEDとなり、Statement/DDNodeが作られない。警告はあるので完全に無通知ではないが、有効な後続DDの復旧に失敗している。

根拠: [IBM JCL Reference、Chapter 14 Delimiter statement（3.1公式PDF）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)は区切り文の継続を禁止する。JCL-CONT-005、FR-03の後続独立文への復帰。

修正案: インライン境界確定後、境界をまたいだLexer文の後半を新しい文脈で字句・構文解析する。単に警告へ置き換えない。

検証: D2。区切りコメントのカンマ有無で後続DDが一致すること、後続EXEC/JOB・引用符を含むコメントでも復帰できることを確認する。

## A06 — DLM前方一致だけで終了する（高、新規）

場所: `parser.py:474` のraw.startswith(dlm)。

再現: JES2、DD DATA,DLM=AAの後に `AAXYZ`、`AA`、`//T EXEC PGM=Y`。

実測: AAXYZの行をDELIMITERとし、データを0件にする。次のAAには暗黙SYSINを作ってしまう。期待はAAXYZをデータとして保存し、単独AAの行で終了。

根拠: [IBM JCL Reference、Delimiter statement / Comments field（3.1公式PDF）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)は、JES2で区切り文字の後に空白を要求する。JES3のコメント規則とは区別する必要がある。

修正案: JES別のdelimiter record判定関数を作り、長さ・後続空白・短いレコードの空白補完を扱う。UNKNOWNで判定が分かれる場合も未確定にする。

検証: D3、`AA`、`AA COMMENT`、`AAX`、18文字DLMと直後の空白/非空白で検査する。

## A07 — DLM文字数と空値を検査しない（中、新規）

場所: `parser.py:367` place_dd〜data_region。

再現: ジョブ内の通常DD DATAでDLMを `''`、`A`、19文字にする。JES3で`AAA`も実行。

実測: いずれもERRORなし。空文字は全レコードの前方一致となり、最初のデータ行を区切りにする。

根拠: [IBM DD Parameter field](https://www.ibm.com/docs/en/zos/3.1.0?topic=d-parameter-field-2)と公式JCL ReferenceのDLM / Invalid delimitersはJES2の2〜18文字、JES3の2文字を定義する。DLMのnull値は手続きDDの追加・オーバーライドという別の許容文脈があるため、無条件に禁止する修正も不適切。

修正案: 復元後の文字数と使用文脈を検査し、不正な入力を成功したDETERMINED領域として出さない。

検証: D4の4件に加えて、2文字/18文字の正常境界、手続きオーバーライドのnull化、未解決シンボルを検査する。

## A08 — DD * + DLMのEOF欠落診断（中、新規）

場所: `parser.py:508`付近。EOF警告をmode==DATAだけに限定している。

再現: `//D DD *,DLM=AA` の後にデータ1行だけでEOF。

実測: terminator=EOFだが診断なし。DD DATAでは同じ必須区切り欠落をLEX-W002で報告する。

根拠: [IBM z/OS 3.2 DLM parameter](https://www.ibm.com/docs/en/zos/3.2.0?topic=statement-dlm-parameter)はDLMによる終端の必要性を明示する。JCL-STMT-DELIM、要件1.3。EOF後のデータ保存は正しいが、診断の有無は別問題。警告コードの再利用はプロジェクト方針による修正案であり、IBM自身がLEX-W002を定義しているわけではない。

修正案: 「DD DATAまたはDLM指定あり」の区切り要求を共通化する。

検証: D5。DLMなしDD *のEOFには誤警告を出さない対照例も加える。

## A09 — EXEC/DDの文固有制約不足（中、新規）

場所: `parser.py:353` exec_target、367 place_dd。一般値パーサーだけでは文固有制約を検査できない。

再現: `EXEC PGM=X,PROC=Y`、`EXEC PGM=(X,Y)`、`DD DUMMY,DATA`。

実測: すべて診断なし。最初のEXECはPGM=Xに固定し、2つ目はリスト表記をそのままPGM対象にする。

根拠: [IBM EXECの位置パラメーター](https://www.ibm.com/docs/en/zos-basic-skills?topic=do-jcl-exec-statements-positional-frequently-used-parameters)、[IBM EXEC Parameter field](https://www.ibm.com/docs/en/zos/3.1.0?topic=d-parameter-field-3)、[IBM DD Parameter field](https://www.ibm.com/docs/en/zos/3.1.0?topic=d-parameter-field-2)。EXECの対象形式は1つ、PGMは所定形式、DDの位置パラメーターは最大1つ。POL-001に従い、確定した構文違反にはERRORが必要。

修正案: 一般トークン/値の保存後に、EXEC対象の排他性・型・位置とDD位置パラメーターの個数を検査する。未対応パラメーター全般を推測して検査する必要はない。

検証: E1〜E3、正しいPGM/PROC/裸手続き名、PGM後方参照、キーワード順序の正常例・異常例を組み合わせる。

## A10 — Job.spanがデータ末尾を含まない（中、新規、プロジェクト要件）

場所: `parser.py:446` close_job。lastをStatement.spanの最大値だけで計算する。

再現: JOB、EXEC、DD DATA、データ2行でEOF（T1）。

実測: data regionは4〜5行目だがJob.span=[1,3]。既存check_traceはPASSする。原文とデータ領域の行番号は保存されているため、全面的なトレース不能ではなく親領域の範囲不整合。

根拠: 要件CTX-01、FR-03、9.3。Job.spanの意味と検証はプロジェクトの契約であり、IBMがPython ASTのspanを定義しているわけではない。IBMのEOFまでデータであるという規則と、プロジェクトの親子範囲が整合していない。

修正案: ジョブが所有する文・データ・区切りの範囲からspanを算出する。spanをJOBカードだけの範囲と定義するのであれば、現在の可変終端を改め別名のジョブ全体範囲を提供する。

検証: T1、空データ、区切りあり、次JOBあり、PROC内データで、子の全物理範囲が親に包含されることを確認する。

## A11 — 階層のGolden不在と受入ゲートの不足（高、検証設計）

場所: `parser/model.py:225` to_golden_view、`parser/adapter.py:27` scope_gap、`harness/trace.py:23`、`tools/quality_gate.py:68`。

再現1: 正常なJOB/EXEC/DDを解析し、dataclasses.replace(r, jobs=())でメモリ上の結果だけ変更。ソースや期待値は変更していない。変更前後のto_golden_viewをcompare_structureに渡してもok=True、check_traceもPASS（hierarchy-check.json）。

再現2: 既存ゲートを実行すると、既知重大欠陥が未修正でもGATE: PASS。9件はxfail(strict=True)であり、失敗の再現を維持できる一方、欠陥の解消は要求していない。

実装の評価: RunnerはFAILED/BLOCKED/NOT_IMPLEMENTEDを区別し、REFERENCEも表示する。Adapter例外はFAILEDになり、封印検査も機能している。**未実装がPASSEDに偽装されている事実や、意図的な隠蔽は認めない。** ただしゲートはこれらの残存を許容する開発用ゲートであり、Step 4b完了の受入ゲートとしては不足する。

Goldenの妥当性:

- 全102件がdraft/blockedであり、封印一致は内容の正しさやレビュー承認を意味しない。
- 51合格の内訳はlexical 16、syntactic 35。syntacticは35合格/2 BLOCKED/30 NOT_IMPLEMENTED。残りsemantic 9、resolution 10は未実装である。
- JOB/EXEC/DDやDD DATAの代表例は独立正常系でも確認できた。しかしstatements viewにJOB→STEP→DD階層がなく、期待ASTとしてFR-03全体を保証しない。
- `tests/parser/test_parser_spec.py`のtest_null_statement_ends_jobはUNKNOWNで[S,T]を期待しており、A01と同じ誤った確定を固定する。これはGolden YAMLではなく既存の通常テストの期待値の問題。
- G-CONT-009は継続nullのlexical事実として整合するが、Parserの終端誤りは検査しない。G-IS-005のBLOCKEDはPOL-003通りだが、UNKNOWNの保守的な構造出力の正しさを保証しない。
- G-IS-005のblocked_reasonにあるJES2で6行目AAを「stray」とする説明は、実装が採用する暗黙SYSIN規則との整合を再レビューすべき。実行されていない説明文なので、合格結果の不一致とは数えない。
- 新規反例に対応するDLMの復元・文字数・前方一致・区切り境界と、EXEC排他性の期待値が不足している。
- check_traceはValueの最初の1文字などを検査するが、値全体の出典範囲・階層参照・親子包含は検査しない。CardDemoテストも48ファイルの決定性・原文対応を検査するもので、意味的な階層正解を独立照合していない。
- Adapterは期待診断コードの実装有無でケース全体をNOT_IMPLEMENTEDにするため、コード削除がFAILから未実装へ移るリスクがある。今回の49件は報告上、範囲外カテゴリ/未登録段階によるもので、この経路が実際に発動したと断定しない。
- 既存のmutationは主にComparator等の自己検査であり、Parser階層の破壊を殺す受入試験にはなっていない。

根拠: 要件6.1/6.2/6.6/9.1/9.3、ADR-018/026。ゲートの名称・合格条件はプロジェクトの判断であり、IBM仕様の直接違反ではない。

修正案: 開発用の健全性ゲートを残し、別途Step 4b対象ケースと既知重大欠陥を固定した受入ゲートを設ける。対象内のNOT_IMPLEMENTED/BLOCKED/xfail、重大欠陥残存を承認なしに許容しない。期待値内の診断から実装範囲を逆算せず、対象契約を独立に定義する。階層・所属・候補状態・トレースを独立オラクルで比較し、同一担当が書いた期待値への第三者レビューを行う。

検証: JobNode/StepNode/DDNodeの削除・付け替え、target変更、data境界変更をメモリ上で注入し、対応する独立検査が必ず失敗することを確認する。合格数だけでなく対象内の未検証一覧と承認状態も受入条件として判定する。

## CardDemoへの適用と保全

原本app配下のJCL/PROC系48ファイルにDLM=の使用は0件。したがってDLM固有の反例をCardDemoでの既発現と断定しない。既存Corpusテストは全48ファイルを読み、ハッシュ・レコード数・トレース・決定性を確認して合格した。これは一般のJCLに対する仕様適合を保証しない。

`before.json`にはsrc 40、tests 225、specs 4、CardDemo app 240、計509ファイルのSHA-256を保存した（__pycache__除外）。監査末尾の`preservation.json`では509件すべて一致し、追加0・削除0・内容変更0だった。成果物はresults/audit-20261115配下のみ。依頼で禁止されたソース、Golden期待値、既存テスト、CardDemo原本の変更は行っていない。このディレクトリにはGitリポジトリがないため、コミットIDではなく当該ハッシュ一覧を対象版の証拠とする。

既知D-1〜D-3と新規指摘を実装担当へ返し、修正・承認済み期待値・独立再検証が揃うまでStep 4bの完了承認を保留する。本監査は報告をもって終了し、修正や次工程には進まない。

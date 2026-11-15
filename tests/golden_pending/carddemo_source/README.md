# CD-1 source oracle — 全48件PENDING

このディレクトリはCardDemo専用のsource構造期待値である。既存のsealed 102件、および
汎用pending YAML 5件とは別の、バージョン1の専用JSONスイートとして扱う。
既存のGolden Loader/SchemaやGate A/Bの意味は変更していない。

## 出所・独立性

- 入力は `results/carddemo-contract-20261115/inventory.json` と原本48ファイルのバイト列。
- `tools/golden_authoring/build_carddemo_source.py` はstdlibだけを使用し、Parser/Lexer/Harnessを
  importしない。原本のハッシュ、文フィールド、引用符・括弧・継続、パラメーター原表記を
  インベントリと再照合してから値・位置・階層・連結・データ境界を記述した。
- 参照規則は `specs/rules.yaml` のJCL-REC-001〜003、JCL-CONT-001、JCL-DD-001/003/006、
  JCL-PROC-002/004。正式な版・節・IBM公式URLは同レジストリーとCardDemo受入契約にある。
  今回IBM PDF全ページを再検証したという意味ではない。
- 著者はCodex。Claude作成の実装とは経路・担当が異なるが、独立インベントリ、変換器、
  CD検査器の著者は同じCodexである。共通誤解の可能性は残り、人による原本レビューが必要。
- **自動記述と正式承認は別**。reviews.jsonの48件は全てPENDINGであり、生成/実行では更新しない。
  既存Parser/Harnessのactual JSONから正解データを作る経路はない。
- expectations.jsonは最初の生成以降変更していない。比較中に実装の挙動へ合わせて調整していない。

## 表現

`expected_structure`は既存Comparatorのstatements/hierarchy比較を使う。Job.spanには
データ・コメントも含めた最終物理行を指定するため、MNTTRDB2は1〜30である。
`hierarchy.reachable_lines`はtreeが参照すべき全681操作文の先頭行であり、PROC末尾のPENDも含む。
missingなPENDをflat一覧からtreeへ補うことはしない。

DDのname/concat_headは原本の完全な名前を使い、PRC001.FILEIN等の修飾を保持する。
汎用hierarchy_viewが使う正規化ddnameとは表現が異なるので、CDのactual射影は
**実DDNodeのprocstepとconcat_headだけから**完全名に変換する。期待値から補完しない。
この変換はPROC Resolverではない。

`trace.records[].statement_line`は操作文/継続行が属する論理操作文の先頭行を表す。
DATA、COMMENT、NULL、DELIMITERではnull。DATA/DELIMITERの所有DDは別のdata_dd_lineで検査する。
特殊文のASTリンクは既存check_hierarchyでも検査する。
全3046レコードの原文SHA-256、バイト範囲、改行、全字句トークンのsegments、全値の原表記と
開始位置・子要素を原本に照合する。値の末尾列はLexerの全セグメント経由で追跡する。
現在のValueモデルに新しい位置フィールドを追加したものではない。

## 実行と判定

```powershell
.venv/Scripts/python.exe tools/carddemo_source_acceptance.py --corpus D:/projects/aws-card/aws-mainframe-modernization-carddemo/app --output results/carddemo_source
```

- CD-SOURCE: 全48件の原本ハッシュ・全source構造・パラメーター・連結・境界との比較。
- CD-TRACE: 全レコード/トークン/値の位置と、既存の階層不変条件。既知欠陥も抑制しない。
- CD-ASSURANCE: 期待値の完全性、異常注入検出、人の承認状況。未承認ならPENDING。
- 正式受入: 3判定が全てPASSの時だけPASS。現状の実不一致はFAILとして独立に報告する。
- 入力欠落/変更や新しいJCL/PROCの追加はBLOCKEDで明示し、正式受入はFAIL。
- 既存のFAILがあるだけでは異常注入を検出したと数えない。
  各変異で、独立期待値とのsource比較に**新しい差分**が必要。traceだけの検出も数えない。

## レビュー手順

1. レビュー担当者が各ファイルのハッシュと原本を確認し、JOB/PROC→STEP→DD、連結24、境界91、
   値/位置とPROC末尾を照合する。review-packet.mdは読みやすい案内であり別オラクルではない。
2. 疑問点は差分と原本/IBM根拠で解決する。実装に合わせた期待値修正や自動再生成は禁止。
   期待値の訂正が必要なら旧版を保存し、理由・根拠・独立レビューを経て別版として提案する。
3. 人が承認する時だけreviews.jsonの当該行をAPPROVEDにし、reviewed_by/atを記入する。
   reviewsはexpectationsのSHA-256に結び付いており、別版への承認流用はできない。
4. oracle-manifest.jsonは改ざん/意図しない変更の検出用であり、承認済みの封印ではない。
   既存tests/golden/MANIFEST.jsonへ移したりgolden-sealしたりする作業は今回含まない。

Human approvalを設定するCLIは提供していない。現在48件全てPENDINGのまま保持する。

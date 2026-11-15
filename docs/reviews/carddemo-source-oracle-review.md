# CD-3 — CardDemo Source Oracleの独立受入審査

実施日: 2026-11-16（Asia/Tokyo）。実施者: Codex。
対象: CD-1の固定済み48ファイルのsource期待値。A10/H01/H02はCD-2で独立検証済みとして扱う。

## 1. 結論

**SOURCE構造に限定した正式判断の候補として、条件付きで利用可能。現在の正式承認は保留。**

原本から別方式で導出した観測と、凍結済み期待値は全48ファイルで一致した。
今回の対象内で、期待値を訂正すべき実測不一致は発見していない。
ただし、期待値作者と今回の自動照合担当はいずれもCodexであり、人または別担当による独立承認の代わりにはならない。
本書は承認申請に必要な証拠とレビュー対象をそろえたもので、FORMALへの変更・承認操作ではない。

| 項目 | 結果 |
|---|---|
| 原本と別方式の照合 | **48/48 MATCH**、不一致0、未実行0 |
| JOB/PROC→STEP→DD | 46 JOB + 2 PROC、119+4 STEP、480+20 DD、全件一致 |
| DD連結 | 無名DD24件・19グループ、所属・順序・連結先が一致 |
| インストリーム | 91領域・635データ行、83 DELIMITER / 7 NEXT_STATEMENT / 1 EOF、一致 |
| 元位置 | 3046レコード、681操作文、5280 token、1229最上位パラメーターを照合 |
| 継続・コメント | 181継続文・282継続行、1358 comment文、特殊inlineコメント1件を確認 |
| 自動照合方式の自己検証 | 合成カード10確認 + in-memory改変8確認、計18/18成功 |
| 人の期待値承認 | **48件ともPENDINGを維持** |
| 正式承認の可否 | **現時点では不可（承認保留）。§7の証拠・人の審査・スコープ合意後に可能** |

機械結果: [comparison.json](../../results/cd3-20261116/comparison.json)。
人向けの全構造: [source-structure-ledger.md](../../results/cd3-20261116/source-structure-ledger.md)。
重点レビュー票: [human-review-packet.md](../../results/cd3-20261116/human-review-packet.md)（全45項目PENDING）。
今回Parser/Harness/Gate A/Bの再実行や変更は行っていない。CD-2の実装検証と、今回の期待値審査を区別する。

## 2. 対象版と承認する命題

凍結対象: `tests/golden_pending/carddemo_source/expectations.json`。
SHA-256:
`fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a`。
oracle-manifestと一致。reviews.jsonも同じ期待値SHAを参照し、48件のreviewed_by/atは未設定のまま。
原本は `D:/projects/aws-card/aws-mainframe-modernization-carddemo/app` の48 JCL/PROCファイル。
全240資産を保全対象とした。48件の各SHAはsource-ledger.jsonと全構造台帳に記載する。

承認する命題は「**このハッシュの原本に、記述したsource文・所属・順序・値の原表記・データ境界・元位置が存在する**」である。
原本が全てIBMの実行可能なJCLであること、参照が解決すること、Javaバッチへそのまま変換可能であることは承認しない。

CA-01〜03 / CA-13〜14を対象とし、CA-15の展開後trace、PROC/INCLUDE解決、COND/IFや資源の実行意味を含めない。
PROCルートの4 STEPを呼出しJOBへ展開した件数に置き換えない。
PGM/PROC、シンボル、GDG、DSN(member)、DD修飾名、DCB後方参照はsourceとして保存する。
ライブラリー探索、上書き結果、実世代、外部状態を確定したとはしない。

## 3. 期待値作成時とは異なる照合方法

検証スクリプト: [review_oracle.py](../../results/cd3-20261116/review_oracle.py)。
原本観測台帳: [source-ledger.json](../../results/cd3-20261116/source-ledger.json)。
これは今回の審査用検査であり、稼働Parserへの機能追加や、新しい承認済みGoldenの作成ではない。

CD-1作成時は、inventoryの逐次走査結果を作者ツールで期待値へ変換していた。
今回はinventoryも、その走査スクリプトも、作者ツールも実行/importしていない。
Parser/Lexer/Harness/CD検査器のactualも使用していない。標準ライブラリーだけを使い、次の経路で原本を検査した。

1. **原本カード表を先に確定**: 拡張子を大小文字区別なく列挙。LFバイト境界から行・CRLF/LF・末尾改行なし・バイト範囲を求め、全raw行をSHA化。
2. **操作欄を原本から抽出**: 正規表現で7種のoperationとname欄を抽出。comma継続の物理行を対応付け、引用文字列と非引用空白を区別する正規表現でoperand/commentを分離。
3. **所属を関係演算で求める**: SQLiteの行表へ操作文を登録。DDに先行する最大のEXEC行、window関数の直前operationと最後の名前付きDDから所有者・連結先・indexを導出。STEP名をキーにしない。
4. **データは区間として照合**: 各DD *の最後の物理行以降で、原本の列1–2が//または/*となる最初の行を求める。sentinel不在ならEOF。境界行とデータ行を分離。
5. **値・元位置を照合**: 正規表現token列とtoken括弧構造から値を記述し、全原表記・開始行列・全segments・再帰値を照合。本文位置はカードの実列から得る。
6. **観測完了後だけ期待値を読む**: 全48観測を作り終えてから凍結JSONを読み、R1〜R6を完全比較。存在しない項目を期待値から補わない。

| 方法ID | 全48件に適用する検査 | 対応するcomparison.jsonのキー |
|---|---|---|
| R1 | 全パス集合、SHA、入力型、現在のバイト列のUTF-8読取 | identity |
| R2 | JOB範囲、STEP/DD所属・順序、連結、PROCヘッダー、PENDを含む操作文到達行 | hierarchy |
| R3 | 全文種、論理span、name、位置/keyword値、コメント、inline_data | flat_values_comments |
| R4 | DD所属、全データ行、終了理由・行、mode | boundaries |
| R5 | 全レコード役割、操作文/データDD所属、raw SHA、byte範囲、改行 | records |
| R6 | 操作欄位置、論理文の全物理行、operand全文、全token/segments、全再帰値/開始位置 | tokens_values_positions |

**観測形式への制限:** 固定コーパスの1ルート/ファイル、7操作種、comma継続、DD *・DLMなしを検証する。
未知カード、未分類行、引用符内の物理継続、DD DATA/DLMなど、今回未観測の形は成功へ推測しない。
新しいコーパスに対する汎用JCL適合性を証明するツールではない。

### 独立性とその限界

- 入力経路と所属/境界の導出アルゴリズムはCD-1作者ツールとは異なる。inventory.jsonも入力しない。
- 今回はSQLの所属演算・regex token grammarを用い、作者ツールの関数を転用しなかった。
- 同じGolden View仕様を表現するため、正規化形式・行列の定義・IBM規則は共有する。形式を知った上での審査であり、盲検ではない。
- **期待値作者、前段inventory作者、今回検査作者は同じCodex**。別方式の一致は共通誤解を減らす材料になるが、人・別主体の独立承認を成立させない。
- 正規化値の表現とIBM実行意味は別。WORD/COMPOUND等の分類はプロジェクトのview形式であり、IBMの意味解析済み型ではない。

### 照合方式自体の検証

[check_review_method.py](../../results/cd3-20261116/check_review_method.py) で、JOBレベル連結、JOBLIBラベルのJCLLIB、
commentで終了するDD *、EOF、同名STEP、引用内comma/空白、NULL副要素、継続コメント、PROC/PEND、CRLF/末尾改行なしを確認。
さらにメモリー上のコピーでroot/STEP削除、DD移動、連結逆順、データ境界、byte開始、token終端列、operand破損を確認した。
計18/18成功、skipなし。固定期待値・原本へ変異は加えていない。
初回自己検証で合成fixtureのbyte長を誤って80と仮定した検査1件が失敗した。
その仮定を除き、別のliteral byte長検査を維持して再実行した。初回記録も保存した。凍結期待値の訂正はない。

## 4. 全48ファイルの記録

全行にR1〜R6を適用し、いずれもMATCH。これは機械照合の結果であり、レビューstatusはPENDINGのまま。
全ファイル共通の未検証事項を次の通り定義する。

- **U1**: 人による原本/一次仕様/レビュー手法の承認、期待値作者以外の独立した判断。
- **U2**: JOB実行可能性、JES/NULLJCLの実行終了、同名STEPの参照解決、制御入力・資源の意味。
- **U3**: PROC/INCLUDE・シンボル・DSN探索・GDG/DCB参照等の解決、展開後trace。
- **U4**: 固定48件にない構文・非ASCIIの一般的文字コード判定・歴史的なmainframe取得時encoding。

48件の全バイトはASCII範囲内で、現在のファイルをUTF-8で可逆読取できることを確認した。
これを原取得時のencoding推定や、非ASCII資産の文字コード保証へ拡張しない。
「基本確認のみ」の行も承認済みではなく、重点EX票に追加する異常な形式がないという意味である。

| File | STEP | DD | 無名DD | Data領域 | 継続行 | 照合 | 人の承認 / 未検証 |
|---|---:|---:|---:|---:|---:|---|---|
| app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl | 1 | 17 | 2 | 1 | 2 | R1–R6 MATCH | PENDING; U1–U4; EX-001, EX-002, EX-003 |
| app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl | 2 | 19 | 2 | 1 | 9 | R1–R6 MATCH | PENDING; U1–U4; EX-004, EX-005, EX-006, EX-007 |
| app-authorization-ims-db2-mq/jcl/LOADPADB.JCL | 1 | 14 | 3 | 0 | 3 | R1–R6 MATCH | PENDING; U1–U4; EX-008, EX-009 |
| app-authorization-ims-db2-mq/jcl/UNLDGSAM.JCL | 1 | 16 | 3 | 0 | 5 | R1–R6 MATCH | PENDING; U1–U4; EX-010, EX-011 |
| app-authorization-ims-db2-mq/jcl/UNLDPADB.JCL | 2 | 21 | 3 | 0 | 11 | R1–R6 MATCH | PENDING; U1–U4; EX-012, EX-013 |
| app-transaction-type-db2/jcl/CREADB21.jcl | 5 | 30 | 6 | 0 | 1 | R1–R6 MATCH | PENDING; U1–U4; EX-014, EX-015, EX-016, EX-017, EX-018, EX-019 |
| app-transaction-type-db2/jcl/MNTTRDB2.jcl | 1 | 7 | 2 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; EX-020, EX-021 |
| app-transaction-type-db2/jcl/TRANEXTR.jcl | 5 | 28 | 2 | 4 | 17 | R1–R6 MATCH | PENDING; U1–U4; EX-022, EX-023 |
| jcl/ACCTFILE.jcl | 3 | 8 | 0 | 3 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/CARDFILE.jcl | 8 | 20 | 0 | 8 | 3 | R1–R6 MATCH | PENDING; U1–U4; EX-024 |
| jcl/CBADMCDJ.jcl | 1 | 5 | 0 | 1 | 2 | R1–R6 MATCH | PENDING; U1–U4; EX-025 |
| jcl/CBEXPORT.jcl | 2 | 11 | 0 | 1 | 8 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/CBIMPORT.jcl | 1 | 9 | 0 | 0 | 23 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/CLOSEFIL.jcl | 1 | 3 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/COMBTRAN.jcl | 2 | 10 | 1 | 3 | 9 | R1–R6 MATCH | PENDING; U1–U4; EX-026, EX-027 |
| jcl/CREASTMT.JCL | 5 | 22 | 0 | 3 | 19 | R1–R6 MATCH | PENDING; U1–U4; EX-028 |
| jcl/CUSTFILE.jcl | 5 | 14 | 0 | 5 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/DALYREJS.jcl | 1 | 2 | 0 | 1 | 0 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/DEFCUST.jcl | 2 | 4 | 0 | 2 | 1 | R1–R6 MATCH | PENDING; U1–U4; EX-029 |
| jcl/DEFGDGB.jcl | 1 | 2 | 0 | 1 | 0 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/DEFGDGD.jcl | 6 | 18 | 0 | 3 | 9 | R1–R6 MATCH | PENDING; U1–U4; EX-030 |
| jcl/DISCGRP.jcl | 3 | 8 | 0 | 3 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/DUSRSECJ.jcl | 4 | 12 | 0 | 3 | 5 | R1–R6 MATCH | PENDING; U1–U4; EX-031 |
| jcl/ESDSRRDS.jcl | 6 | 19 | 0 | 5 | 5 | R1–R6 MATCH | PENDING; U1–U4; EX-032 |
| jcl/FTPJCL.JCL | 1 | 1 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; EX-033 |
| jcl/INTCALC.jcl | 1 | 9 | 0 | 0 | 11 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/INTRDRJ1.JCL | 2 | 8 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/INTRDRJ2.JCL | 1 | 4 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/OPENFIL.jcl | 1 | 3 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/POSTTRAN.jcl | 1 | 9 | 0 | 0 | 11 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/PRTCATBL.jcl | 3 | 8 | 0 | 2 | 15 | R1–R6 MATCH | PENDING; U1–U4; EX-034, EX-035 |
| jcl/READACCT.jcl | 2 | 10 | 0 | 0 | 15 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/READCARD.jcl | 1 | 4 | 0 | 0 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/READCUST.jcl | 1 | 4 | 0 | 0 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/READXREF.jcl | 1 | 4 | 0 | 0 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/REPTFILE.jcl | 1 | 2 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TCATBALF.jcl | 3 | 8 | 0 | 3 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TRANBKP.jcl | 3 | 6 | 0 | 2 | 7 | R1–R6 MATCH | PENDING; U1–U4; EX-036 |
| jcl/TRANCATG.jcl | 3 | 8 | 0 | 3 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TRANFILE.jcl | 8 | 20 | 0 | 8 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TRANIDX.jcl | 3 | 6 | 0 | 3 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TRANREPT.jcl | 3 | 16 | 0 | 2 | 22 | R1–R6 MATCH | PENDING; U1–U4; EX-037, EX-038, EX-039, EX-040, EX-041 |
| jcl/TRANTYPE.jcl | 3 | 8 | 0 | 3 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/TXT2PDF1.JCL | 1 | 6 | 0 | 1 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/WAITSTEP.jcl | 1 | 3 | 0 | 1 | 1 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| jcl/XREFFILE.jcl | 6 | 14 | 0 | 6 | 3 | R1–R6 MATCH | PENDING; U1–U4; 基本確認のみ |
| proc/REPROC.prc | 1 | 4 | 0 | 0 | 3 | R1–R6 MATCH | PENDING; U1–U4; EX-042 |
| proc/TRANREPT.prc | 3 | 16 | 0 | 2 | 21 | R1–R6 MATCH | PENDING; U1–U4; EX-043, EX-044, EX-045 |

各件のSHA、STEPごとの全DD順序、91境界の全一覧は [全構造台帳](../../results/cd3-20261116/source-structure-ledger.md)。
181文/282継続行の全文は [継続台帳](../../results/cd3-20261116/continuation-ledger.md)。
列72または73–80が非空白の行は [列レビュー台帳](../../results/cd3-20261116/column-review-ledger.md) に原表記付きで記録した。

## 5. 人が判断すべき重点例外

45票を [human-review-packet.md](../../results/cd3-20261116/human-review-packet.md) に作成した。
全票に、原本パス/行、原文抜粋、固定JSONのPointerと直接の抜粋、レビューする命題、規則/契約根拠、確認項目を付けた。
sourceから導いた所属の表示と、凍結JSONそのものの引用も区別した。判定・reviewer・日付は未記入。

| 区分 | 人が確認する原本と期待値 | 判定する点 |
|---|---|---|
| JOBLIB DD | CREADB21 32–34行、最初のEXEC40行。JOB側DDはJOBLIB→無名→無名の3件 | SET28–30行を挟む配置を含むsource所属と順序。実行可否をここで決めない |
| JOBLIBラベルのJCLLIB | PRTCATBL / TRANBKP / TRANREPT 各19行、operation=JCLLIB | name=JOBLIBをDD名と誤解しない。JCLLIB ORDERの文字列保存のみ |
| PROC/PEND | REPROC 1/29行、TRANREPT.prc 1/79行 | JOBと別ルート。PENDはsource終端。最後のEXECの所有にしない |
| 無名DD連結 | 全19グループ24件、EX票に全件掲載 | 同じDSNも削らず、先行DD、所有先、連結index・順序を確認 |
| EOFデータ | MNTTRDB2 28行DD *、29–30行data、Job.span=[1,30] | 架空delimiterなし、最終2行を含む、実ファイル末尾を照合 |
| 次文で終了 | 全7件、EX票と91境界台帳 | 列1–2の//で終わり、境界文/コメントをデータに含めない |
| 同名STEP | DEFCUST STEP05 22/32行、TRANREPT STEP05R 23/37行 | 2個体を保持し、各DD所属が分かれること。参照の一意性を承認しない |
| 継続 | 全181文/282継続行 | 先頭行、接続順、operand全文、NULL/quote/DSN括弧、全segments。注目箇所以外も継続台帳で確認 |
| 特殊コメント欄 | CREASTMT 87–91行のSTMTFILE DD | 90行34列comma、35列blank、36列から`00,RECFM=FB), ATA.VSAM.KSDS`はコメント。91行DSNを継続 |
| 末尾の//* | DBPAUTP0 45行 | 右端の//*は73列以降。新しいcomment文にしない。通常operandへ入れない |
| データ右端の//Date | TRANREPT.jcl 43–44行、TRANREPT.prc 41–42行 | データ内の右端表記をJCLコメントや継続扱いにせず、raw全体を保持 |
| NULL/末尾コメント | 6ファイルのNULL7行および末尾comment | source役割・範囲を保持することと、JESでの実行終了解釈を分離 |

補足:

- 非空白の列72は20レコード（comment16・data4）で、操作文/継続の列72継続指示は0件。
  commentの装飾文字やdataの右端文字を「通常JCLの継続指示」とみなさない。
- 73–80列非空白は104レコード。通常操作文48、継続5、comment45、data5、delimiter1で、役割ごとに扱いを分ける。
- 継続の間に挟まる独立comment文は本コーパスでは0件。一般仕様のその形式を今回承認する根拠にはしない。
- CREASTMTのコメント欄には見かけ上operandに似た文字列がある。原本の意図を推定して削除/修正する承認ではない。
- 同名STEPはsource個体を保持した。一意名によるrestart/COND/overrideの意味をこの期待値から保証しない。

## 6. IBM根拠と未解決の解釈

一次版の正本はspecs/rules.yamlのIBM-JCLREF-32（SA23-1385-70、z/OS 3.2）とする。
次の規則と内部契約を承認時に確認する。IBM規則とASTの独自モデルを混同しない。

| 根拠 | 確認対象 |
|---|---|
| JCL-REC-001〜003、JCL-FMT-002/007 | 文識別、operation欄、1–71/73–80列、comment欄。印刷p.13/15 |
| JCL-CONT-001 | comma継続と次レコードのoperand位置。レジストリーの該当節・頁 |
| JCL-DD-001/003/013 | name省略連結、DD *の終端、JOB/STEP所属。p.75/92/95、各該当節 |
| JCL-PROC-002/004 | カタログPROCとPEND。p.25、549–550 |
| JCL-EXEC-001、EXEC Name field | EXECがSTEP開始であることと、同名STEPの参照上の注意 |
| CA-03/13/14、ADR-027/031 | source範囲、完全なレコード保存、個体識別、PROCルートPEND。IBM固有のAST型と称さない |

オンラインで照合したIBM一次ページ:

- パラメーターの後のblank区切りコメントは、パラメーター継続時にも存在できる。
  列範囲の説明も確認した。[JCL statement fields（3.1）](https://www.ibm.com/docs/SSLTBW_3.1.0/com.ibm.zos.v3r1.ieab600/iea3b6_JCL_statement_fields.htm)
- DD *のDLMなし終端は/*、別JCLを示す//、入力EOF。
  [* Parameter（3.1）](https://www.ibm.com/docs/en/zos/3.1.0?topic=statement-parameter)
- JOBLIBはJOB後・最初のEXEC前のライブラリー指定。
  [Private library（3.2）](https://www.ibm.com/docs/en/zos/3.2.0?topic=library-private)
- 同名STEPを参照する場合の曖昧さはsource個体保存とは別の問題。
  [EXEC Name field（3.1 Reference）](https://www.ibm.com/docs/en/SSLTBW_3.1.0/pdf/ieab600_v3r1.pdf)

このオンライン照合は検索索引の本文を含む。直接取得には403となったページがあり、3.2 Referenceの全該当頁を今回改めて全文確認したとはしない。
人の正式審査では登録済み3.2一次資料の該当頁を開き、参照版/取得日/必要ならPDF SHAを記録する。
別版の補助確認を、3.2規則全体の再検証へ読み替えない。

未解決の意味解釈はU2/U3として残す。特にJOBLIBの具体的配置とジョブ有効性、同名参照、NULL後の実行所属、
PROC呼出し4件の展開と修飾DD上書き、SET/シンボル、COND、DCB参照、GDG、DFSORT/IDCAMS/FTP/SQL等のデータ中制御言語はSOURCE承認と切り離す。
このうち本文に構文が存在しないINCLUDEを「解決成功0件」と称して対応完了へ数えない。

## 7. 正式承認の条件と変更管理

以下は今後の承認手順の提案であり、今回その操作を実施したものではない。

### 承認スコープ

承認名を **CardDemo Source Oracle v1 / CA-01〜03・CA-13〜14 / 固定48パス** とし、期待値SHA・原本SHA集合・
Golden View版・ADR-031のPROCルート所有モデルを明記する。
SOURCEとしての原表記と階層だけを承認し、実行意味、Resolver、非対象構文、汎用Gate Bの合格とは別にする。

JSONオラクルは汎用YAML Goldenのreview_statusスキーマへ自動登録されない。
専用reviews.jsonのAPPROVEDと、汎用runnerのFORMALを同一操作・同一範囲と扱わない。
専用スイートでの正式利用方法を明示して承認する必要がある。既存102 Goldenへの移植・封印を暗黙に実施しない。

### 必要な証拠と人の確認

1. JCLと一次仕様を確認できる人（または別担当）が、原本48件のハッシュ・全構造台帳・方式R1〜R6を確認する。
   Codex自身の「MATCH」のみを承認理由にしない。レビュー担当・承認者と期待値作者の役割を記録する。
2. 全48件のJOB/PROCルート、STEP/DD所属・順序、全91データ領域の開始/終了、継続台帳を確認する。
   全5280 tokenの人による1文字ずつの再走査を必須とはしないが、自動検査の証拠と手法への納得が必要。
   サンプリングする項目は対象・選定理由・残余リスクを記録する。
3. 45の重点EX票を原本・固定JSON・IBM一次規則と照合し、各確認命題へ明示的な結論を記録する。
   「実行時解釈は未確定だがsource事実は確認」の結論は可能。source事実自体が未確定ならそのケースはPENDINGを維持する。
4. 固定期待値のSHA、全パス/SHA、比較結果0不一致、method-checks18/18、CD-2独立報告とCD検査感度証拠をそろえる。
   既存の1501/1501変異成功はCD-2の証拠として添付できるが、今回再実行したとは記載しない。
5. 人の承認は、明示された48パスと期待値SHAへの判断として記録する。全件一括承認する場合も、その一覧と未承認例外の有無を特定する。
   曖昧な了承、沈黙、コード修正の承認から期待値承認を推定しない。
6. 実際の承認状態更新は、その人の明示承認後の別作業とする。承認済み期待値SHAに対してreviewed_by/atを記録し、
   tests/CHANGES.md、必要なADR/要件履歴、seal方針を適用する。今回のPENDINGは更新しない。
7. 承認時点のParser/Harness/checker SHAを固定し、CD-SOURCE/TRACEと変異を再実行する。
   全48実行、対象内skip/xfail/NOT_IMPLEMENTED/BLOCKED/uncheckedは0、実測不一致0、全変異検出を要求する。
   CD-ASSURANCEの承認状態と実測結果を分離したまま、専用の最終判断を残す。

### 期待値単体では表現しきらない点

- PENDは期待値のflat文・reachable_linesにはあるが、`procedure_end`という親edgeを専用属性で固定していない。
  PROCルート所有の保証にはADR-031と固定版check_hierarchyの所有検査も必要。人の承認対象にこの依存を含める。
- record全文はraw SHAとbyte範囲で証拠化される。期待値JSONが元データ全バイトを内包するわけではないため、原本48件を一緒に保存する。
- NULL副要素は幅0の欠落位置なので個別文字spanを持たない。隣接comma token・親リスト・NULL順序が根拠になる。
  全ノードへ独立した位置属性があるという保証にはしない。
- 構造比較でid/timestamp等を無視する既存view方針と、path/先頭行/SHAによるsource個体識別を承認する。
  実装のID文字列そのものを独立期待値で証明したとはしない。
- 専用loaderはreviewer/dateの存在を検証するが、文字列の入力者が承認権者かを暗号学的に認証する仕組みではない。
  人の明示承認記録と変更監査を別に保持する。

### 再承認条件

| 変更 | 必要な対応 |
|---|---|
| 原本の1 byte、改行、encoding、パス、48件への追加/削除 | 別原本版。旧承認を流用せず、影響する期待値とコーパス全体スコープを再審査 |
| expectations.jsonの変更 | 旧版/旧SHAを保存。理由・原本/IBM根拠・差分・影響ケースを提示し、別SHAに対して再レビュー。actualへ合わせた自動修正は禁止 |
| 規則版・Golden View・正規化・PROC/PEND所有・traceの意味変更 | 影響範囲を独立評価し、承認契約を改訂。比較で無視する属性の追加も審査対象 |
| Parserのみの修正 | 正解事実の承認を自動失効させる必要はないが、旧実装の受入れ結果を流用しない。CD全件・感度試験を再実行 |
| Harness/比較/trace/ゲートの変更 | 検証証拠の独立再検証が必要。意味・検出範囲が変わるなら承認範囲も再確認。無条件の既承認移行は不可 |
| Resolver/意味解析/新しい構文の追加 | 別段階の契約・独立期待値・承認。SOURCEの承認で代用しない |
| 承認情報や担当者の訂正 | 履歴を残し、変更者・理由・権限根拠を記録。未実施の承認を遡及作成しない |

## 8. 残余リスクと保全

主要な残余リスクは、同一Codexによる共通誤解、人の一次資料確認の未了、sourceモデルと実行意味の混同、
PEND親edge等のchecker依存、固定コーパス外の未検証形式である。
CD2-R02（JES未確定/DLM候補のspan破損を汎用checkerが見逃す問題）は本原本に該当せず、今回の期待値の不一致ではないが、汎用保証には残る。
Oracle MATCHを、未解決事項の不存在・汎用Parser完成・Batch IR決定完了とはしない。

原本240件、Parser/Harness、既存Golden、CD-1の期待値・reviewsを変更していない。
開始時の全ソース/テスト/設定/資料と原本のsize・mtime・SHAを固定し、終了時にも照合する。
保全結果: [preservation.json](../../results/cd3-20261116/preservation.json)。
成果物ハッシュ: [artifact-manifest.json](../../results/cd3-20261116/artifact-manifest.json)。

再現コマンド（原本・期待値・承認状態を書き換えない）:

```powershell
.venv/Scripts/python.exe results/cd3-20261116/review_oracle.py
.venv/Scripts/python.exe results/cd3-20261116/check_review_method.py
.venv/Scripts/python.exe results/cd3-20261116/make_review_materials.py
```

本審査はここで終了する。正式承認は人の判断待ちとし、Parser等の変更やFORMAL化へ進まない。

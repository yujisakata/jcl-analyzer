# CD-4 Report: CardDemo 専用 PROC Resolver（Effective Job View）

- 日付: 2026-11-16 / ブランチ: `claude/cd4-resolver`（作業開始時の HEAD は 356ff90。作業中に 16a4519「fix: preserve frozen oracle bytes across worktrees」が入った。変更は .gitattributes のみで、本作業のファイルとは重ならない。最終確認は 16a4519 の上で実施した）
- コミット: 未実施。変更は worktree に未コミットのまま残している（コミットの指示待ち）
- 契約: `docs/reviews/carddemo-acceptance-contract.md` の CA-04〜06、CA-15
- 状態: 実装とテストは完了。**正式な完了ではない**（実装者以外による監査、つまり Codex の独立監査が必要）

## 1. 変更ファイルと設計判断

| 種別 | ファイル |
|---|---|
| 新規 | `src/jclprof/resolver/{__init__,model,library,symbols,resolver}.py`、`tests/resolver/{test_resolver_spec,test_resolver_carddemo,test_resolver_codes}.py`、`config/contexts/cd4-contract-context.yaml`、`tools/cd4_resolve_report.py`、本報告 |
| 変更 | `specs/rules.yaml`（JCL-SYM-003/004、JCL-EXEC-003 を追加。いずれも SA23-1385-70 の本文を確認した VERIFIED）、`specs/diagnostic-catalog.yaml`（RES-E005、RES-W003〜W005、RES-I002 を追加）、`specs/ibm-jcl-reference.md`（生成物）、`tools/quality_gate.py`（analyzer-suite に tests/resolver を追加）、`docs/decisions.md`（ADR-032）、`tests/CHANGES.md`（TC-020） |
| 変更していない | Source AST と Parser、既存の Golden とその封印、Source Oracle（`tests/acceptance/expected`、`tests/golden_pending`）、`config/profiler.yaml`、`.gitattributes`、Git 設定、main、Codex の worktree |

設計判断の全文は ADR-032 にある。要点は次のとおり。

- Effective View は Source AST とは別の層とし、元の AST は読むだけにする
- マッピングは明示したものだけを使う。本番設定は datasets: [] のままとする。契約の検算には、未確認であることを明記した文脈ファイルを使う
- 候補が複数ある場合（AMBIGUOUS）、先に探索するライブラリーが未マッピングの場合（ENVIRONMENT_GAP）、システム PROCLIB を探す必要がある場合（未設定）は、いずれも未解決として扱う
- PROC ラベルとメンバー名は区別する。TRANREPT.prc のラベル REPROC を理由に、REPROC メンバーとして扱うことはしない

## 2. 実装済みと未実装

**実装済み**

- 探索順序（インストリーム → JCLLIB → システム）と探索の根拠の記録
- メンバー名と明示的な別名による解決、ラベルの区別
- STEP と DD の展開
- DD の上書き（REPLACE / ADD / NULLIFY）と追加。修飾なしの上書きの適用先規則を含む
- シンボル: 呼出し EXEC のシンボリックパラメーター、PROC の既定値、SET（記述位置によるスコープ）、入れ子での継承、未定義シンボルを文字のまま残すこと、SYSUID の環境依存の扱い
- PROC 内からの PROC 呼出し（15 段まで）と循環の検出
- DCB / DSN の後方参照の解決
- 全ノードへの出典の付与

**未実装**（出現した場合は RES-W004 を出して適用しない）

- 呼出し EXEC での EXEC パラメーター上書き（例: COND.step=）
- DUMMY・位置パラメーターによる上書き、DCB の部分マージ、相互排他パラメーターの処理
- 上書きの後に続く連結 DD・暗黙 DD
- 入れ子の呼出し STEP そのものの上書き
- 16 段以上の入れ子
- その他（範囲外）: インストリームデータ内のシンボル（CA-07）、DSN と物理資源の対応付け、COND / DISP / GDG の意味解析、Batch IR

## 3. PROC 呼出し 4 件と上書き 8 件

| 呼出し | 本番設定 | 契約文脈（UNCONFIRMED） |
|---|---|---|
| jcl/PRTCATBL.jcl:29 STEP05R | ENVIRONMENT_GAP（JCLLIB AWS.M2.CARDDEMO.PROC が UNMAPPED、根拠は 19 行目） | RESOLVED: proc/REPROC.prc（SHA-256 cbe8a6eb…）、ラベル一致 |
| jcl/TRANBKP.jcl:23 STEP05R | 同上 | 同上 |
| jcl/TRANREPT.jcl:23 STEP05R | 同上 | 同上 |
| proc/TRANREPT.prc:21 STEP01R（入れ子） | 文脈を指定しない単独検査では NO_LIBRARY_CONTEXT、文脈を指定すると UNMAPPED | 文脈 AWS.M2.CARDDEMO.PROC を指定して RESOLVED |

8 件の上書き（FILEIN 4 件、FILEOUT 4 件）は、契約文脈では全件が適用された（パラメーター操作は計 24 件）。

- **FILEIN**: DISP は REPLACE（SHR → SHR）、DSN は REPLACE（NULLFILE → 呼出し側の DSN）
- **FILEOUT**: DISP は REPLACE（SHR → (NEW,CATLG,DELETE)）、UNIT・DCB・SPACE は ADD、DSN は REPLACE（NULLFILE → …BKUP(+1)）

各記録は、上書き元の行（例: PRTCATBL の 32/33、35〜39）と PROC 定義の DD（REPROC.prc の 23 / 25）を参照する。全件の一覧は `results/resolve/report.md` にある。

**計数**（46 JOB ファイル）:

- 本番設定: プログラム STEP 116、未解決の呼出し STEP 3、DD 474（480 から適用待ちの上書き DD 6 を除いた数）
- 契約文脈: プログラム STEP 119、DD 486（JOB レベル 3 を含む）。契約 CA-05 の条件付き検算値 119 / 486 と一致した
- TRANREPT メンバー（文脈を指定）: 3 STEP / 18 DD。契約の値と一致した

## 4. Effective View の例（契約文脈、PRTCATBL STEP05R → REPROC.PRC001）

```
step PRC001  call_path=(STEP05R, PRC001)  program=IDCAMS  exec_origin=proc/REPROC.prc:21
  call: REPROC RESOLVED basis=UNCONFIRMED_CONTRACT_CONTEXT at jcl/PRTCATBL.jcl:29
        search: JCLLIB AWS.M2.CARDDEMO.PROC FOUND [proc/REPROC.prc] (evidence jcl/PRTCATBL.jcl:19)
  DD SYSPRINT origin proc/REPROC.prc:22   SYSOUT=*
  DD FILEIN   origin proc/REPROC.prc:23   override_statement jcl/PRTCATBL.jcl:32
      DISP=SHR (src PRTCATBL:32)  DSN=AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS (src PRTCATBL:33)
      override DISP REPLACE "SHR"->"SHR"; DSN REPLACE "NULLFILE"->"AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS"
  DD FILEOUT  origin proc/REPROC.prc:25   override_statement jcl/PRTCATBL.jcl:35
      DISP=(NEW,CATLG,DELETE) DSN=AWS.M2.CARDDEMO.TCATBALF.BKUP(+1) UNIT=SYSDA
      DCB=(LRECL=50,RECFM=FB,BLKSIZE=0) SPACE=(CYL,(1,1),RLSE)
  DD SYSIN    origin proc/REPROC.prc:27
      DSN raw "&CNTLLIB(REPROCT)" -> "AWS.M2.CARDDEMO.CNTL(REPROCT)" (src REPROC.prc:28;
          CNTLLIB RESOLVED, defined by jcl/PRTCATBL.jcl:30)
```

Source AST 側では、PRC001.FILEIN / FILEOUT は引き続き STEP05R の子として残っている（test_source_ast_unchanged_and_source_counts で確認）。

## 5. テスト結果と既知の失敗

| 対象 | 結果 |
|---|---|
| Harness スイート（既定の pytest） | 268 passed、1 skipped（symlink）。基準時点と同じ |
| Analyzer スイート（lexer / parser / property / resolver） | 181 passed、51 skipped、9 xfailed。基準時点は 144 passed で、resolver の 37 件が増えた。xfail はすべて登録済みの既知欠陥 A01〜A03 |
| Resolver | spec 25 件、CardDemo 11 件、codes 1 件。すべて合格 |
| ruff / mypy strict | 合格（92 ファイル） |
| Gate A（開発の健全性） | PASS（既知欠陥 OPEN 11 件を明示）。hierarchy-mutation 943/943 |
| Gate B（Parser の正式受入） | FAIL（B3 / B4 / B5 / B7 / B8 / B9: 未承認の Golden、NOT_IMPLEMENTED、BLOCKED、レビュー待ち、範囲が未承認）。CD-4 の前から同じ状態で、CD-4 の対象外 |
| テストの修正 | 1 件（TC-020）。symbols_defined の範囲についての、自作テストの不具合 |

## 6. Source Oracle と原本のハッシュ

- **原本 240 ファイル**: SHA-256 は Step 1 のベースラインと同一。mtime も前回の確認時から変わっていない
- **Source Oracle と既存 Golden**: 内容の変更なし（`git diff --ignore-cr-at-eol` で差分 0）。worktree 上の 204 件の modified はすべて CRLF 変換によるもので、本作業の前からある（Codex が担当）。SHA-256 の不一致を理由に期待値を変更することはしていない
- **Golden の完全性**: golden-check は OK（MANIFEST と一致）

## 7. 未解決の参照

| 参照 | 状態 | 必要なもの |
|---|---|---|
| AWS.M2.CARDDEMO.PROC → app/proc | 本番設定では UNMAPPED（契約 Q01） | 資産所有者によるマッピングの確認 |
| システム PROCLIB | NOT_CONFIGURED | Environment Profile での定義 |
| AWS.M2.CARDDEMO.CNTL(REPROCT) | SYSIN の DSN として値は算出した。物理資源への対応付けは範囲外（候補が 2 か所ある。Q02） | CNTL ライブラリーのマッピングと探索順の確認 |
| &SYSUID（45 件） | ENVIRONMENT_DEPENDENT | 実行環境（値は推測しない） |
| &SYUID（READCUST:2） | UNDEFINED のまま文字として残す（RES-W001） | 所有者の判断（Q05） |
| REPROC メンバーの単独検査 | &CNTLLIB は呼出し元が無いため UNDEFINED（想定どおり） | なし |

## 8. Codex に独立検証してほしい項目

1. 上書き 8 件と計数 119 / 486、3 STEP / 18 DD を、原本と IBM の規則（p.27〜29）から実装とは独立に検算する
2. マッピングが未確定の場合や、先のライブラリーが未マッピングの場合に、RESOLVED にならないこと（推測していないこと）
3. 修飾なしの上書き、追加 DD、NULLIFY の規則が JCL-PROC-006 と合っていること
4. シンボルの優先順位（EXEC > PROC の既定値 > SET）、SET の記述位置によるスコープ、入れ子での継承、アポストロフィ内で置換する対象（p.43、p.48、p.566）
5. 呼出し EXEC のシンボリックパラメーターを判定するキーワード一覧（Table 20 + PARMDD）が漏れなく正しいこと
6. Source AST が変化しないこと、48 ファイルの source 構造（123 STEP / 500 DD）に回帰が無いこと
7. 出典（CA-15）が全ノードでたどれること、DCB 後方参照 3 件の参照元と参照先
8. RES-W004 の範囲外検出が、黙って成功として扱っていないこと（変異を入れて確かめる: 上書きの欠落、DSN の置換間違い、ラベルによる解決、AMBIGUOUS での先頭候補の選択などを、出力に注入すること）
9. 契約文脈ファイル（UNCONFIRMED）を受入の根拠として扱ってよいかどうかの判断

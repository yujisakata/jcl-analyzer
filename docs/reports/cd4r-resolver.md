# CD-4R Report: PROC Resolver の独立監査指摘への対応

- 日付: 2026-11-16 / ブランチ: `claude/cd4r-resolver`（a19b8ca から作成。CD-5 のブランチとは別）
- 監査: `docs/reviews/cd4-independent-audit.md`（Codex、a19b8ca、FAIL）。監査用 worktree は読んだだけで、変更していない
- 状態: 修正とテストは完了。**正式な合格ではない**（Codex の再監査が必要）。Source Oracle 48 件は引き続き PENDING で、承認・封印はしていない
- 設計判断: ADR-033 / テストの変更記録: TC-021

## 1. 指摘ごとの対応

| 指摘 | 対応 | 結果 |
|---|---|---|
| F01 先行ライブラリーを検査できない | 新しい結果 UNAVAILABLE（root ID が不明、フォルダが無い、ディレクトリーでない、一覧の取得に失敗）。後のライブラリーで見つかっても ENVIRONMENT_GAP。RES-W006 | 修正 |
| F02 同じ DSN の複数マッピング | 公開ローダー（YAML / JSON）は ConfigError で拒否。直接作った LibraryContext では DUPLICATE_MAPPING → 呼出しは AMBIGUOUS。RES-W007 | 修正 |
| F03 PROC 内の SET | 呼出し先の本体に SET があれば U-PROC-SET → 呼出しは UNSUPPORTED。メンバーの単独検査では STEP を UNSUPPORTED。未呼出しのインストリーム PROC の SET が JOB に漏れる問題は修正 | 漏れは修正、位置スコープは未対応として検出 |
| F04 ネストからのインストリーム PROC | JOB がインストリーム PROC として定義した名前を PROC 内から呼ぶ場合は U-NESTED-INSTREAM → UNSUPPORTED | 未対応として検出 |
| F05 重複シンボル | EXEC 文・PROC 文の重複は最初の値（JCL-SYM-005、p.36 を確認）。RES-I003 | 修正 |
| F06 シンボルによる PROC 名・JCLLIB | U-SYMBOLIC-PROC / U-SYMBOLIC-JCLLIB → UNSUPPORTED（探索の記録には SYMBOLIC_NOT_SUPPORTED） | 未対応として検出 |
| F07 PGM のシンボル置換の出典 | EffectiveStep.program_raw と program_substitutions（使用 → 定義）を保存 | 修正 |
| F08 DUMMY のベース DD の上書き | U-OVR-BASE-POSITIONAL → UNSUPPORTED。呼出し側の DUMMY は U-OVR-POSITIONAL | 未対応として検出 |
| F09 実行証跡 | `run-manifest.json`（実装・入力・文脈・環境・出力の SHA-256 と件数）と `--verify` | 修正 |

### 対応範囲の境界（機械的に判定できる）

`jclprof.resolver.UNSUPPORTED_FORMS` に 12 の形を登録した。U-EXEC-OVERRIDE、U-OVR-POSITIONAL、U-OVR-BASE-POSITIONAL、U-OVR-DCB-MERGE、U-OVR-MUTEX、U-OVR-CONCAT、U-OVR-NESTED-STEP、U-DEPTH、U-PROC-SET、U-NESTED-INSTREAM、U-SYMBOLIC-PROC、U-SYMBOLIC-JCLLIB の 12 件。

- どの形も展開の前に検出し、RES-W004 に `[形の ID]` を付けて出す。記録は `EffectiveResult.unsupported` に残り、limitations に `UNSUPPORTED_FORMS_PRESENT` が付く
- その形を含む呼出しは UNSUPPORTED になり、展開しない。UNSUPPORTED の呼出しの中から実効 STEP が作られないことをテストで確かめている
- `test_every_registered_form_has_a_case` は、登録表とテストの入力一覧が一致することを確かめる。形を足すとテストも足す必要がある
- 判定方法: 結果の `unsupported` が空で、呼出しがすべて RESOLVED なら対応範囲内。それ以外は、RESOLVED 以外の状態と、形または環境の診断が必ず付く

## 2. 変更ファイル

| 種別 | ファイル |
|---|---|
| 変更 | `src/jclprof/resolver/{library,model,resolver,__init__}.py`、`tools/cd4_resolve_report.py`、`tests/resolver/test_resolver_spec.py`（1 件、TC-021）、`specs/rules.yaml`（JCL-SYM-005）、`specs/diagnostic-catalog.yaml`（RES-W006 / W007 / I003、RES-W004 の題名）、`specs/ibm-jcl-reference.md`（生成物）、`docs/decisions.md`（ADR-033）、`tests/CHANGES.md`（TC-021） |
| 新規 | `src/jclprof/resolver/manifest.py`、`tests/resolver/test_resolver_env_counterexamples.py`、`tests/resolver/test_resolver_unsupported_forms.py`、`tests/resolver/test_resolver_manifest.py`、`results/cd4r/`（修正前後のテスト記録、CD-SOURCE の結果）、本報告 |
| 再生成（別コミット） | `results/resolve/{official,contract}/effective.json`、`report.md`、`run-manifest.json` |
| 変更していない | Parser と Source AST、既存の Golden と封印、Source Oracle（`tests/acceptance/expected`、`tests/golden_pending`）、`config/`、CardDemo の原本、`.gitattributes`、Git の設定、main、Codex の worktree、CD-5 のブランチ |

## 3. テスト結果

| 確認項目 | 結果 |
|---|---|
| 1. 先行ライブラリーの不在 / 実在する空のライブラリー | 修正前: 不在・ファイル・公開ローダーの 3 形で誤って RESOLVED、一覧の取得失敗で例外（PermissionError）。root ID が不明な形は修正前も ENVIRONMENT_GAP だった（結果名が UNMAPPED だったことだけが失敗の理由）。修正後: すべて ENVIRONMENT_GAP（UNAVAILABLE）。空のライブラリーは修正前も後も NOT_FOUND → 次で RESOLVED |
| 2. 同じ DSN の重複と、定義順の逆転 | 修正前: どちらの順でも先頭を RESOLVED。修正後: どちらの順でも AMBIGUOUS（DUPLICATE_MAPPING、候補 2 件を表示）。root が異なる場合も同じ |
| 3. 公開ローダーへの異常な設定 | 修正前: YAML / JSON とも受理。修正後: 4 通り（YAML / JSON × 記述順 / 逆順）すべて ConfigError |
| 4. F03〜F08 の未対応の検出と停止 | 12 形すべてで検出・UNSUPPORTED・展開なし。F03 の漏れ、F05、F07 は修正を確認 |
| 5. CardDemo の 4 呼出し・8 DD 上書き | 既存の CardDemo テスト 11 件が合格。契約文脈で 4 件 RESOLVED、本番設定で 4 件 ENVIRONMENT_GAP |
| 6. 全 46 JOB の 119 STEP・486 DD | 契約文脈で 119 / 486、本番設定で 116 + 未解決 3 / 474（manifest の件数とテストで確認） |
| 7. Source AST の不変性 | 既存テスト（合成と CardDemo 48 ファイル）が合格 |
| 8. CD-SOURCE・CD-TRACE の回帰 | CD-SOURCE PASS、CD-TRACE PASS、変異 1501/1501 を検出（`results/cd4r/cd-source/`）。正式な受入れは Source Oracle が未承認のため FAIL のまま（監査時と同じ） |
| 9. run-manifest と再生成結果の対応 | 2 回の再生成でバイト単位で一致し、LF であること。manifest の全ハッシュが一致すること。出力・入力・文脈を改ざんすると検出されること（`test_resolver_manifest.py` 4 件） |

| スイート | 結果 |
|---|---|
| Resolver（tests/resolver） | 75 passed（CD-4 の 37 件 + 新規 38 件） |
| Analyzer（lexer / parser / property / resolver） | 219 passed、51 skipped、9 xfailed（xfail は登録済みの既知欠陥） |
| Harness（既定の pytest） | 268 passed、1 skipped（symlink）。CD-4 時点と同じ |
| ruff / mypy strict | 合格（96 ファイル） |
| Gate A | PASS（既知欠陥 OPEN 11 件を明示）。golden-check OK |
| 修正前の記録 | `results/cd4r/pre-fix-counterexamples.log`（12 failed / 2 passed） |
| 修正後の記録 | `results/cd4r/post-fix-counterexamples.log`（14 passed）、`results/cd4r/resolver-tests.log` |

テストの感度: 呼出しを UNSUPPORTED にする処理を変異で無効にすると、未対応形のテストのうち 8 件が失敗した。漏れの修正も無効にすると 13 件が失敗した（変異は戻してある）。

## 4. CardDemo の結果の維持

新しいコードで results/resolve を再生成し、コミット済みの結果と比較した。追加したフィールド（`unsupported`、`reason`、`program_raw`、`program_substitutions`）を除くと、official と contract のどちらも全 48 ファイルで内容が一致した。CardDemo での未対応形の検出は 0 件、PGM のシンボル置換も 0 件である。report.md の差分は「unsupported forms detected: 0」の 2 行と、例示 JSON に新しいフィールドが入ったことだけである。

## 5. 既知の未対応事項

- 未対応形 12 件の機能そのもの（検出して UNSUPPORTED にするだけ）: PROC 内 SET の位置スコープ、ネストからのインストリーム PROC 参照、シンボルを使う PROC 名 / JCLLIB、DUMMY のベース DD・位置パラメーター・DCB のマージ・相互排他・連結の上書き、入れ子の呼出し STEP の上書き、呼出し EXEC の EXEC パラメーター上書き、16 段以上の入れ子
- U-NESTED-INSTREAM は名前が一致すれば一律に UNSUPPORTED にする。定義位置による可視性の判定は実装していない
- ProcCall から PROC ヘッダー文への直接の SourceRef（監査 §5 の指摘）は追加していない（member path・SHA・ラベルからはたどれる）
- DSN と物理資源の対応（CNTL、REPROCT の 2 候補など）とインストリームデータ内のシンボルは範囲外のまま（後続の段階で管理）
- 既知欠陥台帳（tests/KNOWN_DEFECTS.yaml）は scope が STEP4B / OUT_OF_SCOPE に限られており、Resolver の指摘を登録するには Harness の変更が要るため、登録していない。F01〜F09 の状態は本報告と ADR-033 で管理する
- Codex の audit_probes.py は監査用 worktree に書き込むため実行していない。F03〜F08 については、監査側の期待値（例: PARM=LOCAL）とは結果が異なる。完全な実装ではなく UNSUPPORTED として止める方針をとったためである

## 6. 人の判断・環境条件が残るもの

Q01（PROC の DSN の実環境でのマッピング）、Q02（REPROCT などの資源の対応）、SYUID、JES の実行時の意味、Source Oracle 48 件の承認。本作業はこれらに承認を与えていない。

## 7. Codex に再検証してほしい項目

1. F01 / F02 の独立反例（監査の fixture と公開ローダー）が RESOLVED にならないこと
2. UNSUPPORTED_FORMS の 12 形の検出と、UNSUPPORTED の呼出しから実効値が出ないこと。登録外の未対応の形が残っていないか
3. F05（最初の値）、F07（PGM の使用 → 定義）、F03 の漏れの修正
4. run-manifest の内容で、結果と実装版・入力・文脈・環境が一意に対応すること（`--verify`）
5. CardDemo の 4 呼出し・8 上書き・3 後方参照、119 / 486、Source AST の不変性、CD-SOURCE / CD-TRACE が維持されていること

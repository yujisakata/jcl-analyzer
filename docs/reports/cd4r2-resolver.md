# CD-4R2 Report: 独立再監査の残件 R01〜R04 の解消

- 日付: 2026-11-16 / ブランチ: `claude/cd4r2-resolver`（`claude/cd4r-resolver` の e848ec9 から作成。CD-5 とは別）
- 再監査: `docs/reviews/cd4r-independent-reaudit.md`（Codex、e848ec9、FAIL）。Codex の監査用 worktree と成果物は読んだだけで、変更していない
- 状態: R01〜R04 の修正とテストは完了。**正式な合格ではない**（Codex の再監査が必要）。Source Oracle 48 件は PENDING のまま
- 設計判断: ADR-034 / テストの変更記録: TC-022
- コミット: d8b9747（コード・テスト・ADR）、0add9bf（results/resolve の再生成、d8b9747 のクリーンな状態から）、本報告と検証記録のコミット

## 1. 対応

| 指摘 | 対応 |
|---|---|
| R01 新規 checkout 直後の検証 | `.gitattributes` に `-text` を 5 パスだけ追加した（`config/contexts/cd4-contract-context.yaml` と `results/resolve/` の 4 ファイル）。全 JSON・全ソースには広げていない。manifest に載るその他のリポジトリ内ファイル（config/profiler.yaml、uv.lock、ソースコード）は LF 正規化でハッシュし、方式（sha256_method）を記録する。原本の入力は生のバイト列で照合する。凍結 Source Oracle の属性・ハッシュ・Git の履歴は変更していない |
| R02 DSN / DSNAME | 上書きの照合で DSN と DSNAME を同じパラメーターとして扱い、REPLACE / NULLIFY を適用する。OverrideRecord に original_param（手続き側の表記）と original_source（手続き側の位置）を追加した。旧値・新値・上書きした側の位置（source）も保持する。1 つの DD 文に両方の表記がある場合は、新しい未対応形 U-OVR-DSN-DUPLICATE として UNSUPPORTED にする |
| R03 検証の契約 | manifest を schema 2 にした。`verification` 欄に VERIFIED（再導出する事実 20 群）、RECORDED_ONLY（保証しない 8 項目）、信頼点を記録する。`--verify` は、必須の入力・出力の集合、context の内容（ファイルを読み直して比較）、コードとそのコミット（commit_contains_code を再導出）、encoding / JES（出力に記録した実行条件から）、件数・メンバー・basis（出力から）を検証する。manifest そのものは HEAD の Git blob、または `--manifest-sha256` で与えた外部の SHA-256 で固定し、どちらも無ければ UNANCHORED と表示する |
| R04 複数の未解決理由 | 未対応形を検出した呼出しは、ライブラリーの状態にかかわらず UNSUPPORTED とする。ProcCall に search_status と reasons（例 `UNSUPPORTED:U-EXEC-OVERRIDE`, `ENVIRONMENT_GAP`）を追加し、環境の診断（RES-W002 / W005 / W006 / W007）も残す |

## 2. 修正前の反例と修正後の結果

| 確認 | 修正前（e848ec9） | 修正後 |
|---|---|---|
| R01 属性（5 パスが -text、他は無指定） | 5 件失敗 | 合格。属性を広げていないことの確認 4 件は修正前も合格 |
| R02 ベース DSN + 上書き DSNAME / その逆 / 空の DSNAME | 3 件とも失敗（併存して RESOLVED、NULLIFY の原値が null） | REPLACE / NULLIFY。DSN 系のパラメーターは 1 つだけ残り、元の位置に置かれる。旧値・新値・両側の出典を保持 |
| R02 1 文に両方の表記（上書き側 / 手続き側） | 失敗 | UNSUPPORTED（U-OVR-DSN-DUPLICATE）、実効 STEP 0 |
| R04 EXEC 上書き × ライブラリー（正常 / 未登録 / 利用不可 / 重複） | 4 件失敗 | 4 件とも UNSUPPORTED。search_status は RESOLVED / ENVIRONMENT_GAP / ENVIRONMENT_GAP / AMBIGUOUS。環境の診断を保持し、未解決 1、実効 STEP 0 |
| R04 対照（EXEC 上書きなし × 4 状態） | 失敗（search_status が無い） | 主状態は探索の結果と同じ。UNSUPPORTED の理由は付かない |
| R03 manifest の改変 18 種 | 旧 API で **1/18** を検出（`results/cd4r2/pre-fix-manifest-mutations.json`） | 18/18 を検出 |
| R03 全フィールドの改変（各リストは先頭要素） | — | VERIFIED に属するフィールドはすべて検出。分類されないフィールドは 0。RECORDED_ONLY は改変しても PASS で、保証しないことを明示 |
| R03 信頼点 | — | 正しい外部 digest で PASS、誤った digest で FAIL |

修正前の記録は `results/cd4r2/pre-fix.log` にある（45 件中 40 件が失敗）。R03 の 21 件は、旧 API に引数が無いため TypeError で失敗している。そのため、改変の検出率は同じ改変表を旧 API に通して別に記録した。

## 3. 新規 checkout 直後の検証（R01 の受入条件）

記録: `results/cd4r2/fresh-checkout-verification.log`

1. 0add9bf の新しい detached worktree（system の core.autocrlf=true）。一度も再生成せずに `--verify` を実行し、**PASS**。trust point は HEAD の Git blob。証拠ファイルは `-text` で LF のまま checkout され、config/profiler.yaml と uv.lock は CRLF で checkout されたが、LF 正規化のハッシュで一致した
2. 同じ worktree で、正しい外部 digest を与えると PASS、誤った digest を与えると FAIL（終了コード 1）
3. 同じ worktree から別のディレクトリーに再生成し、その manifest も PASS。3 つの出力はコミット済みのファイルとバイト単位で一致
4. `core.autocrlf=false` で作った 2 つ目の新しい worktree でも PASS

検証後、上記 2 つの一時 worktree は削除した（Codex の worktree は触っていない）。

## 4. 回帰

| 確認項目 | 結果 |
|---|---|
| CardDemo の 4 呼出し・8 DD 上書き | 既存の CardDemo テストが合格。再生成した結果は、追加したフィールド（search_status、reasons、original_param、original_source、run_conditions）を除くと、コミット済みの結果と全 48 ファイルで一致 |
| 119 STEP / 486 DD | 契約文脈で 119 / 486。本番設定で 116 + 未解決 3 / 474（manifest の件数は出力から再導出して一致） |
| 本番設定の未解決 | 4 呼出しとも ENVIRONMENT_GAP のまま（search_status も同じ） |
| CardDemo の DSN 表記 | 8 上書きはすべて DSN 表記で、表記の違う上書きは 0 件 |
| Source AST・Golden・Source Oracle・原本 | a19b8ca 以降、tests/acceptance/expected・tests/golden・tests/golden_pending・Parser・Lexer の差分 0。golden-check OK。原本 240 件の SHA-256 は Step 1 のベースラインと一致し、mtime も変わっていない |
| CD-SOURCE / CD-TRACE | PASS / PASS、変異 1501/1501（`results/cd4r2/cd-source/`）。CD-ASSURANCE は PENDING のまま |
| 全テスト（pytest tests） | 534 passed、52 skipped、9 xfailed（再監査時の 488 に新規 46 件が加わった） |
| Harness / Analyzer スイート | 268 passed・1 skipped / 266 passed・51 skipped・9 xfailed |
| ruff / mypy strict | 合格（97 ファイル） |
| Gate A | PASS（既知欠陥 OPEN 11 件） |

## 5. 変更ファイル

- **コード**: `src/jclprof/resolver/{manifest,model,resolver}.py`、`tools/cd4_resolve_report.py`、`.gitattributes`（5 パス）
- **テスト**: `tests/resolver/test_resolver_cd4r2.py`（新規 45 件）。`tests/resolver/test_resolver_unsupported_forms.py`（未対応形の表に 1 件追加）と `tests/resolver/test_resolver_manifest.py`（ハッシュ方式）は TC-022 として変更した
- **記録**: `docs/decisions.md`（ADR-034）、`tests/CHANGES.md`（TC-022）、本報告
- **証拠**: `results/resolve/`（再生成。schema 2）、`results/cd4r2/`（修正前の記録、改変の検出、新規 checkout の検証、CD-SOURCE）

R01〜R04 以外の機能は追加していない。U-OVR-DSN-DUPLICATE は R02 の「混在の検出」にあたる。

## 6. 未解決事項

- RECORDED_ONLY の 8 項目（生成日時、生成時の未コミットのパス、Python・OS・PyYAML の版など）は、後から確かめられないため保証しない。生成時の状態は、commit_contains_code（再導出する）とコミット済みのコードとの照合で間接的に確かめる
- 信頼点は HEAD の Git blob または外部の digest。manifest が HEAD 以外のコミットにある場合は、`--manifest-sha256` で digest を与える必要がある
- uv.lock は「現在の uv.lock が記録と一致すること」を検証する。uv.lock を更新すると、その時点で古い証拠は FAIL になる（再生成が必要）
- 原本の入力は、絶対パス（config/profiler.yaml の root）で照合する。別のマシンでは root の設定が同じである必要がある
- 監査 §5 の 22 入力中の残り（定義位置による在インストリーム PROC の可視性など）と、延期を認められた機能（PROC 内 SET の完全なスコープ、シンボルによる PROC / JCLLIB、EXEC パラメーターの上書きなど）は、検出して止めるだけのまま
- ProcCall から PROC ヘッダー文への直接の SourceRef、JOB 単位の complete 集約は未対応（後続の設計）
- Q01 / Q02、SYSUID / SYUID、JES の実行時の意味、Source Oracle 48 件の承認は人の判断を待つ

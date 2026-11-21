# Gitベースライン修正 — 凍結Oracleのバイト同一性

実施日: 2026-11-16（Asia/Tokyo）。結果: **PASS**。

## コミットと反映

- 追加コミット: `16a45190fb33a8abdcb8ddaff537f75dd2b4c2bd`
- 親コミット: `356ff90b3e97fd542e303b4646d5adf79a2ea623`（変更なし）
- メッセージ: `fix: preserve frozen oracle bytes across worktrees`
- コミットしたファイルは **`.gitattributes` 1件だけ**。Oracle、Golden、Parser、Harness、Resolver、レビュー状態はコミット差分に含まない。
- `main`で追加コミット後、両作業ブランチをこのコミットへfast-forward。ブランチ名は維持。他ブランチのコードをmainへ統合していない。

| worktree | ブランチ | HEAD | 状態 |
|---|---|---|---|
| `D:/projects/jcl-profiler` | main | 16a45190fb33a8abdcb8ddaff537f75dd2b4c2bd | 既存CD-3変更と調査証拠を未コミットで保全 |
| `D:/projects/jcl-profiler-codex` | codex/cd3-oracle | 同上 | clean |
| `D:/projects/jcl-profiler-claude` | claude/cd4-resolver | 同上 | 属性検証時はclean。その後CD-4編集中の差分あり |

詳細: [final-verification.json](final-verification.json)、[branch-updates.json](branch-updates.json)。

## 原因と正本

修正前は`.gitattributes`がなく、text/eol/filter属性はunspecified。
システムGit設定の`core.autocrlf=true`により、checkout時にLFがCRLFへ変換された。
この設定自体は変更していない。

| 対象 | 修正前Oracle SHA-256 |
|---|---|
| HEADのblob、main実ファイル、manifest記載値 | `fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a` |
| Codex / Claude実ファイル | `eda07b7ef531a7c92d61b06fbb5605e8be553b8e441e53c52b88ef37ba0e430f` |

HEADのblobが指定された正本と一致していた。mainとの差は0バイト。
両worktreeとの差はCRLF/LFだけで、改行以外の内容差がないことをバイト比較で確認した。
Oracleに加え、保護対象204パスについてmain実バイトとHEADの一致、他worktreeとの改行以外の差がないことも事前確認した。
[before.json](before.json) に各worktreeのHEAD、初期差分、全登録ファイル等のSHAを記録した。

## 最小限の属性方針

次の検証データだけを`-text`とした。Python全体、JSON全体をバイナリ扱いする指定はない。

```gitattributes
/.gitattributes text eol=lf
/tests/golden/cases/** -text
/tests/golden/inputs/** -text
/tests/golden/libs/** -text
/tests/golden/.baseline/** -text
/tests/acceptance/expected/** -text
/tests/golden_pending/cases/** -text
/tests/golden_pending/inputs/** -text
/tests/golden_pending/carddemo_source/expectations.json -text
```

対象は現行204ファイル。封印済みGoldenの実payload97件と保存baseline97件、独立inventory期待値1件、
汎用pendingのcase/input8件、Source Oracle1件である。
MANIFEST・oracle-manifest・reviews等のJSONメタデータは記載値を変えず、既存のテキスト方針を維持した。
既存Golden全195物理ファイルについてmainの修正前後SHAが一致し、現在の設定での新規worktreeでも同じ195 SHAを確認した。

## 安全な実checkout

1. 3 worktreeの未コミット変更・index状態・ファイルSHAを記録した。対象204パスはいずれも修正前Git-cleanで、HEADとの改行以外の差がないことを確認した。
2. 各worktreeの未登録だった`.gitattributes`へ今回の方針を適用した。
3. 既存パスへの直接checkout-indexでは旧statキャッシュのためバイト列が更新されなかったので、新規出力先への実checkoutへ切り替えた。
4. 開発者のindexをコピーした一時indexに属性だけを登録し、`git checkout-index --prefix=<新規出力先>`でGit自身に展開させた。
5. 展開した全204 SHAをHEADの正本と照合。反映直前にも実ファイルが事前記録と同一であることを確認し、明示した対象だけをatomic replaceで反映した。
6. 旧CRLFサイズを保持したindexのstat情報に由来する変更表示は、HEADと同一SHAであることを確認した対象だけを再addして解消した。
   この処理でindexの内容差分が0のままであることを検証した。開発者の変更をstageしていない。
7. 属性反映の検証時点で、非対象の既存ファイルは全て初期SHAと一致。既存のCD-3成果物、CD-4用ソース・テストへ変更を加えていない。その後のClaude側の並列開発は下記の終了時状態へ別記した。

両作業ブランチへの反映前に、今回作成した未追跡属性ファイルのバイト同一性と変更の保全を再確認した。
その属性ファイルだけを一時的に取り除いて、fast-forwardでコミット済みの同一ファイルを再現した。
元から存在した未コミットファイルを削除・上書きしていない。reset --hard、clean -fdは使用していない。

手順・検査: [repair_and_validate.py](repair_and_validate.py)、
[checkout-existing.json](checkout-existing.json)、[index-stat-refresh.json](index-stat-refresh.json)。
作業用一時indexと展開コピーは、今回作成したパスだけを確認して削除した。

## 一時worktreeでの再現

コミット前には旧HEADの一時worktreeへ属性を適用し、実checkoutと回帰を検証した。
コミット後にはその一時worktreeをclean確認後に削除し、**修正コミットから新しく作り直した**。

新規checkout後は、属性の手動コピーやOracleの修復を一切せずに次を確認した。

- Source Oracle: 指定SHAと一致。
- 属性対象204ファイル: 全SHA一致。
- Golden: 全195物理ファイルがmainの修正前SHAと一致。manifest内payload97件の整合も成功。
- CD-SOURCE / CD-TRACE: 各48/48 PASS、変異1501/1501検出。
- worktree: clean。

記録: [temporary-fresh-checkout.json](temporary-fresh-checkout.json)。
検証用の`D:/projects/jcl-profiler-bytecheck-20261116`はclean確認後、forceを使わず`git worktree remove`で削除した。
最終的な登録worktreeは元の3つだけである。

## 回帰・保全

| 検査 | 結果 |
|---|---|
| 3 worktreeのOracle SHA | 全て `fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a` |
| Oracle manifest整合 | 全て成功 |
| 原本240ファイル | size・mtime_ns・SHA-256が全て修正前と一致 |
| main既存Golden | 195/195ファイルのSHA一致 |
| 3 worktreeと新規一時worktreeのGolden | manifest payload97/97一致、保護データ204/204一致 |
| CD回帰 | 3 worktree、コミット前一時worktree、コミット後新規worktreeの計5実行、全てSOURCE/TRACE 48/48 PASS |
| 変異 | 5実行とも1501/1501検出、逃避0 |
| 承認状態 | 48件ともPENDING、変更なし |
| 正式受入れ | FAILのまま。CD-ASSURANCE PENDINGを正しく保持 |

各CD実行はそのworktreeのsrcをPYTHONPATHで選び、import実パスも記録した。mainの実装だけを5回検査したわけではない。
専用CLIの終了コード1は未承認による正式受入れFAILを表し、SOURCE/TRACEの回帰ではない。
ParserやHarnessの機能変更はなく、今回は汎用Gate A/Bや全pytestを追加実行していない。

## 未コミット変更と所有者

mainには、従来の次の変更をそのまま残している。

- `docs/reviews/carddemo-source-oracle-review.md`、`results/cd3-20261116/finalize.py`の既存変更（CodexのCD-3審査）。
- CD-3の末尾証拠ファイル、前回`results/git-baseline-20261116/`の調査記録（Codex）。
- 今回の`results/git-byte-preservation-20261116/`の検証結果・スクリプト・本報告（Codex）。

これらは今回の属性コミットへ混入させていない。未コミット成果物があるため、mainをcleanとは報告しない。
Codexのworktreeはclean。Claude側も属性反映・回帰検証時点ではcleanだったが、最終確認でCD-4の編集が始まった。
観測した差分は`specs/diagnostic-catalog.yaml`、`specs/rules.yaml`、未追跡の`config/contexts/`、`tests/resolver/`である。
所有者は専用worktreeからClaude Codeと判断する（OSレベルの作者認証ではない）。これらは今回の修正で編集・stageしていない。
回帰成功は属性修正の検証時点のコードに対するもので、以降に追加された未コミットCD-4実装の検証済みを意味しない。
CD-4コード・テストの編集、他ブランチのmainへの統合、Oracle承認、FORMAL化、封印は実施していない。
属性コミットIDはGitのバイト再現性修正の共通ベースラインであり、未コミットCD-3成果物全ての収録やCardDemo正式受入れを意味しない。

各worktreeの検証直後の状態は `*-status-after.txt`、最終観測は`*-status-final.txt`とfinal-verification.jsonの`latest_observed_worktrees`を参照。
最後の観測でも3 worktreeのOracle SHAと48件PENDINGは全て一致した。
作業を完了し、ここで停止する。

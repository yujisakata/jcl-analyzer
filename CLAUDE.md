# JCL Profiler — 開発ルール

正式要件は `docs/requirements.md`。アーキテクチャは `docs/architecture.md`、設計判断は `docs/decisions.md`、IBM規則の出典は `specs/ibm-jcl-reference.md` を参照する。

## 解析対象
- `D:\projects\aws-card\aws-mainframe-modernization-carddemo\app`（読取専用。変更・削除・ファイル追加をしない）

## 開発順序（各段階の完了条件を満たし、ユーザーの承認を得てから次へ進む）
1. 環境と解析対象への読取りアクセスの確認 — 完了
2. 全資産インベントリ（Python）— 完了（2026-11-15 条件付き承認）
3. Golden Test と pytest 検証ハーネス — 受入済み（Golden 期待値は未承認: draft / blocked）
4. JCL Lexer / Parser — 4a Lexer 完了。4b Parser は実装済みだが、正式受入れは不合格（Codex 独立監査 A01〜A11、`results/audit-20261115/report.md`）。R1（Harness 修正、A11）実施済み・レビュー待ち（`docs/reports/r1-harness.md`）。CD-1（Codex、CardDemo source 受入検査）実施済み。CD-2（A10 / H01 / H02 の最小修正）実施済み・独立再検証待ち（`docs/reports/cd2-source-fixes.md`）。その他の Parser 修正は未着手。D-1〜D-3 の修正設計もレビュー待ち（`docs/reviews/parser-defects-04b.md`）
5. PROC / INCLUDE / 条件制御 / 依存関係
6. 全JCLのプロファイリング、Batch IR候補と未対応領域の報告

## 規則
- 要件変更は ADR（`docs/decisions.md`）と requirements.md 末尾の「変更履歴」に記録する（ADR-014）
- テストの期待値・判定の変更は `tests/CHANGES.md` に記録する。独立オラクルは再生成しない
- 文字コード、DSN とフォルダの対応、PROC の探索順序は推測しない（ADR-009〜011）
- 規則は `specs/rules.yaml` を正本とし、md は生成する（ADR-015）。Golden の期待値を変えたら `golden-check` の差分を確認し、ユーザーの承認後に封印する（ADR-017）
- Context / Harness / Loop Engineering の構成をとる
- 各段階でテストを先に設計し、実装後に検証する
- Golden Test の期待値を自動的に変更しない（変更にはユーザーのレビュー承認が必要）
- 不明な JCL 構文を推測で処理しない（原文と位置を保存し、診断を出す）
- JCL 原本を外部 LLM へ一括投入しない
- 生成したコードと結果は `jcl-profiler` 配下に保存する（出力先は `results/`）
- 重要な構文規則は `specs/ibm-jcl-reference.md` にルールIDと出典を記録する

## コマンド
```
uv run jclprof envcheck --config config/profiler.yaml
uv run jclprof inventory --output results/inventory              # 設定ファイルの roots を使う
uv run jclprof inventory <PATH> --output results/inventory       # 位置引数が roots を置き換える（ADR-013）
uv run pytest                                   # Harness スイート
uv run pytest tests/lexer tests/parser tests/property  # Analyzer スイート（Lexer と Parser 検証）
uv run jclprof golden-check                     # Golden 定義の検査と完全性
uv run jclprof verify                           # Golden 実行（results/harness）
uv run jclprof rules-render [--check]           # ibm-jcl-reference.md の生成と同期確認
uv run jclprof golden-seal --by NAME            # 承認済み期待値の封印（人だけが実行する）
uv run python tools/quality_gate.py             # Gate A 開発健全性（既知欠陥を明示して PASS 可。ADR-028）
uv run python tools/quality_gate.py --gate acceptance  # Gate B Parser 正式受入れ
uv run python tools/hierarchy_mutation_report.py # 誤った AST（M1〜M7）の検出率
uv run jclprof verify --suite tests/golden_pending --output results/harness/pending  # レビュー待ち Golden
uv run ruff check src tests
uv run mypy
```
Python は 3.12.15 に固定している（ADR-001）。システムの Python 3.15 は使用しない。

## Step 4a の注意
- Lexer は JOB/EXEC/DD の分類、PROC の構造、インストリームデータの解釈を生成しない（ADR-024）
- 未承認の Golden に一致しても REFERENCE であり、正式な保証ではない（ADR-026）
- 既知欠陥は `tests/KNOWN_DEFECTS.yaml` に登録する。xfail と FAILED は登録済みのものだけを Gate A で許す（ADR-028）
- 新しい期待値は `tests/golden_pending/`（未封印）に置き、独立レビュー後に `tests/golden/` へ移す（ADR-027）
- 独立レビュー資料は `uv run python tools/golden_review/make_packet.py` で再生成する

--- CD-1/CLAUDE.md
+++ CD-2/CLAUDE.md
@@ -9,7 +9,7 @@
 1. 環境と解析対象への読取りアクセスの確認 — 完了
 2. 全資産インベントリ（Python）— 完了（2026-11-15 条件付き承認）
 3. Golden Test と pytest 検証ハーネス — 受入済み（Golden 期待値は未承認: draft / blocked）
-4. JCL Lexer / Parser — 4a Lexer 完了。4b Parser は実装済みだが、正式受入れは不合格（Codex 独立監査 A01〜A11、`results/audit-20261115/report.md`）。R1（Harness 修正、A11）実施済み・レビュー待ち（`docs/reports/r1-harness.md`）。R2 以降（Parser 修正）は未着手。D-1〜D-3 の修正設計もレビュー待ち（`docs/reviews/parser-defects-04b.md`）
+4. JCL Lexer / Parser — 4a Lexer 完了。4b Parser は実装済みだが、正式受入れは不合格（Codex 独立監査 A01〜A11、`results/audit-20261115/report.md`）。R1（Harness 修正、A11）実施済み・レビュー待ち（`docs/reports/r1-harness.md`）。CD-1（Codex、CardDemo source 受入検査）実施済み。CD-2（A10 / H01 / H02 の最小修正）実施済み・独立再検証待ち（`docs/reports/cd2-source-fixes.md`）。その他の Parser 修正は未着手。D-1〜D-3 の修正設計もレビュー待ち（`docs/reviews/parser-defects-04b.md`）
 5. PROC / INCLUDE / 条件制御 / 依存関係
 6. 全JCLのプロファイリング、Batch IR候補と未対応領域の報告
 

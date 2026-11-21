# JCL → Batch IR 変換手順

JCL Profiler で CardDemo の JCL を中間表現（Batch IR）に変換し、同じ入力から同じ IR をバイト単位で再生成する手順です。

> **最初に確認すること：IR 生成器は `main` にありません**
>
> | 項目 | 値 |
> |---|---|
> | IR 生成器のあるブランチ | `claude/carddemo-batchir`（コミット `00b2534`） |
> | このチェックアウトのブランチ | `main`（コミット `52dea5d`、CD-4 終了時点。`src/jclprof/batchir/` が無い） |
> | ブランチの作業ツリー | `D:\projects\jcl-profiler-claude`（この PC だけにある） |
> | リモート | ローカルの追跡参照は `origin/main` だけで、`origin` に `claude/carddemo-batchir` は無い |
> | 状態 | 期待値は PENDING（未承認）。Codex の独立監査は未実施（ADR-037） |
>
> この文書のコマンドとパスはすべて **コミット `00b2534` のファイル**を指します。`main` のままでは動きません。

---

## 1. 概要

### 入力
- CardDemo の JCL（`*.jcl`）と PROC メンバー（`*.prc`）。読取り専用で、変更しません
- 設定ファイル `config/profiler.yaml`（解析対象のルートと文字コード）
- PROC ライブラリーの対応表（任意）。`config/contexts/cd4-contract-context.yaml`

### 処理の流れ
```
JCL テキスト ─▶ Lexer ─▶ Parser（Source AST）─▶ Resolver（Effective View：PROC 展開・記号置換）─▶ Batch IR builder ─▶ JSON
```
各段階は前の段階の結果を読むだけで、変更しません。IR 生成器は Resolver をメモリ上で直接呼びます。`results/resolve/` の JSON は読みません。

### 出力（Batch IR）
JOB ごとに 1 つの JSON（`schema: "jclprof.batch-ir"`）を出力します。内容は次のとおりです。
- STEP、DD の割当て、制御文の命令、データ集合への作用（effect）
- 実行時に観測すべき項目（観測義務 O1〜O6）
- 分からないこと（Gap）と仮定（Assumption）
- すべての節点から原本の物理行への逆引き表（`line_index`）

**IR は JCL を静的に解析した結果です。** z/OS で実行した結果（RC、ABEND、カタログの状態、GDG の絶対世代など）は含みません。そうした値は `UNKNOWN` と Gap で表します（§7、§9）。

---

## 2. クイックスタート（Windows PowerShell）

前提：
- `git`、`uv` 0.13 以降（検証は 0.13.0）
- CardDemo が `D:\projects\aws-card\aws-mainframe-modernization-carddemo\app` にあること。このパスは `config/profiler.yaml` に固定されています

コミット `00b2534` を作業用フォルダーに書き出し、新しい仮想環境で DUSRSECJ の IR を生成します。リポジトリと既存の作業ツリーには何も書き込みません。

```powershell
$Repo = "D:\projects\jcl-profiler"
$Work = "$env:TEMP\jcl-to-ir"
New-Item -ItemType Directory -Force $Work | Out-Null

# 1. IR 生成器のあるコミットを書き出す（git の状態は変わらない）
git -C $Repo archive --format=zip -o "$Work\batchir-00b2534.zip" 00b2534
Expand-Archive "$Work\batchir-00b2534.zip" -DestinationPath "$Work\src" -Force
Set-Location "$Work\src"

# 2. 仮想環境を作る（Python 3.12.15 は .python-version と uv.lock で固定）
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
uv sync --frozen

# 3. 単一 JOB（DUSRSECJ）の IR を生成する
uv run python tools/cd6a_batch_ir.py --job DUSRSECJ --out "$Work\out\DUSRSECJ"

# 4. 再生成がバイト単位で一致することを確かめる（PASS / 終了コード 0）
uv run python tools/cd6a_batch_ir.py --job DUSRSECJ --check --out "$Work\out\DUSRSECJ"
```

期待される出力（2026-11-19 に実行して確認）：
```
wrote ...\out\DUSRSECJ\batch-ir.json
wrote ...\out\DUSRSECJ\obligations.md
cd6a batch-ir: PASS (outputs reproduce byte for byte)
```
`batch-ir.json` の SHA-256 は `890fa0dbb8bd8c2861c1e31d59ef39758adf39ec2c0494cab8b8c4d218cf9964` です。これはブランチにコミットされた `results/batchir/DUSRSECJ/batch-ir.json` と同じ値です。

> この PC では、既存の作業ツリー `D:\projects\jcl-profiler-claude` で同じコマンドを実行する方法もあります。ただし `--out` を省略すると、コミット済みの正式成果物 `results/batchir/...` を上書きします。正式成果物を守るため、必ず `--out` で別のフォルダーを指定してください。この方法は今回の検証では実行していません。

---

## 3. コマンドリファレンス

IR 生成は `jclprof` のサブコマンドではありません。`tools/` の 2 つのスクリプトで行います。`jclprof parse` が出力するのは AST で、IR ではありません（§3.4）。

### 3.1 `tools/cd6a_batch_ir.py` — 単一 JOB の IR（CD-6A / CD-7）

```
uv run python tools/cd6a_batch_ir.py [--job {COMBTRAN,DUSRSECJ}] [--out DIR] [--check]
```

| 引数 | 既定値 | 意味 |
|---|---|---|
| `--job` | `DUSRSECJ` | 対象の JOB。指定できるのは `DUSRSECJ` と `COMBTRAN` だけ（コード内の固定表 `JOBS`） |
| `--out DIR` | `results/batchir/<JOB>` | 出力先。**省略すると正式成果物を上書きします** |
| `--check` | — | ファイルを書かずにメモリ上で生成し、`DIR` 内のファイルとバイト単位で比較する |

- 出力：`batch-ir.json`、`obligations.md`（UTF-8、改行は LF）
- プロファイル：DUSRSECJ は `CD6A-DUSRSECJ-MVP`、COMBTRAN は `CD7-COMBTRAN-MVP`。どちらも `schema_version` は `0.1-cd6a`
- 設定は `config/profiler.yaml`（固定。`datasets: []` のため PROC ライブラリーの対応なし）。文字コードは `utf-8`、JES は `UNKNOWN`（どちらもコード内で固定）
- CD-5 の設計文書（`D:\projects\jcl-profiler-cd5-design-20261117\docs\design\*.md`）が、IR に記録した SHA-256 から変わっていると `NOTE design document changed since CD-6A` を出力します。生成は続行します

### 3.2 `tools/carddemo_batch_ir.py` — CardDemo 全件の IR（CARDDEMO-BATCH-IR）

```
uv run python tools/carddemo_batch_ir.py [--out DIR] [--check]
```

| 引数 | 既定値 | 意味 |
|---|---|---|
| `--out DIR` | `results/batchir/carddemo` | 出力先。**省略すると正式成果物を上書きします** |
| `--check` | — | メモリ上で全件を生成して比較する。余分なファイルも `EXTRA` として報告する |

- 対象：`tests/acceptance/expected/carddemo_inventory.yaml` の `jcl_family_files` にある 48 ファイル（46 JOB、2 PROC メンバー）。対象を変える引数はありません
- 2 つの文脈で生成します

| 文脈 | 設定 | 対象 | PROC 呼出しの扱い |
|---|---|---|---|
| `official` | `config/profiler.yaml`（`datasets: []`） | 48 ファイル全部 | 展開しない。`UNRESOLVED_CALL` の placeholder と Gap G15 |
| `contract` | `config/contexts/cd4-contract-context.yaml`（`UNCONFIRMED_CONTRACT_CONTEXT`） | PROC 呼出しのある 4 ファイル（PRTCATBL、TRANBKP、TRANREPT.jcl、proc/TRANREPT.prc） | 展開する。展開に基づく主張はすべて仮定 A03 と Gap G24 付き |

- `proc/TRANREPT.prc` は `AWS.M2.CARDDEMO.PROC` の文脈で、`proc/REPROC.prc` は文脈なしの単独メンバーとして解析します
- 出力：54 ファイル、約 6.9 MB

```
DIR/
  official/<元のパス>.json   # 48 個（例: official/jcl/TRANREPT.jcl.json）
  contract/<元のパス>.json   # 4 個
  index.json                 # ファイルごとの入力・出力の SHA-256、件数、Gap、仮定
  summary.md                 # 文脈ごとの集計表
```
- プロファイル：`CARDDEMO-BATCH-IR`、`schema_version` は `0.2-carddemo`

### 3.3 同じ JOB に 2 つのプロファイルがある

DUSRSECJ と COMBTRAN は、§3.1 と §3.2 のどちらでも生成されます。プロファイルとスキーマの版が違うため、出力は**別物**です（例：DUSRSECJ の SHA-256 は §3.1 が `890fa0db…`、§3.2 が `14b18aa1…`）。比較するときは、同じプロファイルどうしを比べてください。

### 3.4 関連する CLI（IR は出力しない）

| コマンド | 出力 | 備考 |
|---|---|---|
| `uv run jclprof parse FILE... --output DIR [--config] [--encoding utf-8] [--jes] [--input-kind auto\|job\|proc_member]` | `DIR/<ファイル名>.ast.json`（Source AST） | PROC、INCLUDE、記号は展開しない。`main` にもある |
| `uv run python tools/cd4_resolve_report.py` | `results/resolve/`（Effective View と run-manifest） | CD-4 の正式成果物。IR の生成では使わない（今回は実行していない） |
| `uv run jclprof envcheck --config config/profiler.yaml` | Python と入力ルートの確認 | 実行前の確認に使う |

`jclprof` のサブコマンドは `envcheck, inventory, golden-check, golden-seal, verify, parse, rules-render` です（`uv run jclprof --help` で確認済み）。

### 3.5 任意の JCL ファイル（Python API、CLI ではない）

固定リスト以外の JCL を変換するコマンドはありません。次のスクリプトは、§3.2 の生成器と同じ API を同じ引数で呼びます。

```python
# one_jcl.py — 使い方: uv run python one_jcl.py <ルートからの相対パス> <出力JSON>
import json, sys
from pathlib import Path
from jclprof.batchir.corpus import build_corpus_ir
from jclprof.context.config import load_config
from jclprof.resolver import LibraryContext, Resolver

rel, out = sys.argv[1], Path(sys.argv[2])
cfg = load_config(Path("config/profiler.yaml"))
root = cfg.roots[0]
res = Resolver(LibraryContext.from_config(cfg), encoding="utf-8", jes="UNKNOWN") \
    .resolve_file(root.path / rel, rel, root.id)
text = json.dumps(build_corpus_ir(res), ensure_ascii=False, indent=1) + "\n"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(text.encode("utf-8"))
```

`jcl/DUSRSECJ.jcl`、`jcl/COMBTRAN.jcl`、`jcl/TRANREPT.jcl` で実行し、§3.2 の `official/` の出力とバイト単位で一致することを確認しました。このスクリプトはリポジトリにはありません（検証用に作ったもの）。

---

## 4. 入力資産の準備

| 資産 | 配置 | 参照のされ方 |
|---|---|---|
| CardDemo の原本 | `D:\projects\aws-card\aws-mainframe-modernization-carddemo\app` | `config/profiler.yaml` の `roots[0]`（id `carddemo`）。IR の `source.file` はこのルートからの相対パス |
| 対象ファイルの一覧 | `tests/acceptance/expected/carddemo_inventory.yaml` の `jcl_family_files` | §3.2 が読む。SHA-256 と行数も記録されている |
| 本番設定 | `config/profiler.yaml` | `datasets: []`。DSN からフォルダーへの対応が 1 つも無い（ADR-010） |
| 契約文脈 | `config/contexts/cd4-contract-context.yaml` | `AWS.M2.CARDDEMO.PROC` → `app/proc`（`.prc`）だけを対応づける。資産の所有者の確認はまだ（Q01） |

### PROC の探索順序
Resolver は IBM の規則 JCL-PROC-003 に従い、次の順に探します。
1. インストリーム PROC
2. `JCLLIB ORDER` に書かれたライブラリー（順に）
3. システムライブラリー

ライブラリーの DSN は、`datasets` に明示した対応がある場合だけローカルのフォルダーとして調べます。DSN からパスを推測することはしません。システムライブラリーは設定されていないため、いつも `NOT_CONFIGURED` です。

探索の各段階の結果は IR の `steps[].call.search[]` に記録されます（`FOUND`、`NOT_FOUND`、`UNMAPPED`、`AMBIGUOUS`、`UNAVAILABLE`、`DUPLICATE_MAPPING`、`NOT_CONFIGURED`）。

### INCLUDE
`INCLUDE` 文は展開しません。CardDemo の JCL と PROC には INCLUDE 文がありません（`grep` で確認済み）。挙動は §8 を参照してください。

### 文字コードと JES
入力は UTF-8 として読みます（`profiles.jcl_text: utf-8`）。JES は `UNKNOWN` に固定です。EBCDIC への対応は推測しません（ADR-009）。

---

## 5. 実行例（CardDemo、2026-11-19）

実行環境：Windows 11、uv 0.13.0、Python 3.12.15。コミット `00b2534` を `git archive` で書き出し、新しく作った `.venv` で実行しました。出力先はすべて一時フォルダーです。正式成果物との比較は、作業ツリー `D:\projects\jcl-profiler-claude`（未変更、`git status` は空）にコミットされたファイルを読むだけで行いました。

### 5.1 DUSRSECJ（PROC なし、IEFBR14 / IEBGENER / IDCAMS）

```powershell
uv run python tools/cd6a_batch_ir.py --job DUSRSECJ --out "$Work\out\DUSRSECJ"          # exit 0
uv run python tools/cd6a_batch_ir.py --job DUSRSECJ --check `
    --out D:\projects\jcl-profiler-claude\results\batchir\DUSRSECJ                       # PASS, exit 0
```

| 入力 | `app/jcl/DUSRSECJ.jcl` |
|---|---|
| 出力 | `batch-ir.json`（136,647 バイト、sha256 `890fa0db…9964`）、`obligations.md`（sha256 `30c8ba84…9831`） |
| 内容 | STEP 4（PREDEL、STEP01、STEP02、STEP03）、作用 16、観測義務 28、Gap G01〜G11、仮定 A01、UNSUPPORTED 0 |
| 検証 | 正式成果物と一致（`--check` PASS、SHA-256 一致） |

SYSUT1 のインストリームデータ（利用者 ID とパスワード状の値）は、行番号で参照するだけで、IR にも `obligations.md` にも本文を書き写しません（Gap G05）。

### 5.2 COMBTRAN（GDG 相対世代、SORT、IDCAMS REPRO）

```powershell
uv run python tools/cd6a_batch_ir.py --job COMBTRAN --out "$Work\out\COMBTRAN"          # exit 0
uv run python tools/cd6a_batch_ir.py --job COMBTRAN --check `
    --out D:\projects\jcl-profiler-claude\results\batchir\COMBTRAN                       # PASS, exit 0
```

| 入力 | `app/jcl/COMBTRAN.jcl` |
|---|---|
| 出力 | `batch-ir.json`（126,993 バイト、sha256 `6868fc2a…d7e8`）、`obligations.md`（sha256 `31871d20…d7d9`） |
| 内容 | STEP 2（STEP05R SORT、STEP10 IDCAMS）、作用 17、観測義務 28、Gap 10（G13 GDG の対応、G14 SORT 製品を含む）、仮定 A02（GDGBIAS=JOB）、UNSUPPORTED 0 |
| 検証 | 正式成果物と一致 |

### 5.3 TRANREPT（JCLLIB + PROC 呼出し、未解決ライブラリー）

TRANREPT は `//JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')` と `EXEC PROC=REPROC` を含みます。§3.1 では扱えないため、§3.2 の全件生成で出力します。

```powershell
uv run python tools/carddemo_batch_ir.py --out "$Work\out\carddemo"                     # wrote 54 files, exit 0
uv run python tools/carddemo_batch_ir.py --check `
    --out D:\projects\jcl-profiler-claude\results\batchir\carddemo                       # PASS (54 files), exit 0
```

| 文脈 | 出力ファイル | STEP | 呼出しの結果 | 主な Gap / 仮定 |
|---|---|---|---|---|
| official | `official/jcl/TRANREPT.jcl.json`（sha256 `f7d12210…1845`） | `STEP05R`（`UNRESOLVED_CALL`）、`STEP05R`（SORT）、`STEP10R` | `call.search = [{order 1, JCLLIB, AWS.M2.CARDDEMO.PROC, UNMAPPED}]`、`call_status ENVIRONMENT_GAP`。展開後の STEP は `UNKNOWN`。`PRC001.FILEIN` / `FILEOUT` の上書きは `pending_overrides` に原文の行として残る | G15（PROC ライブラリー）、診断 RES-W002 / RES-W005 / RES-I002 |
| contract | `contract/jcl/TRANREPT.jcl.json`（sha256 `2937fe45…5b40`） | `PRC001`（REPROC を展開）、`STEP05R`、`STEP10R` | `library_basis: UNCONFIRMED_CONTRACT_CONTEXT` | A03、G24（対応の確認待ち）、G16（外部の制御メンバー） |

全件の集計（`summary.md`）：official は 46 JOB のプログラム STEP 116、未解決の呼出し 3、DD 474、作用 796、UNSUPPORTED 0。正式成果物 58 ファイル（§5.1、§5.2 の 4 つと carddemo の 54 個）の SHA-256 がすべて一致しました。

### 5.4 テスト

```powershell
uv run pytest tests/batchir -q -p no:cacheprovider      # 68 passed, exit 0
```

---

## 6. IR の構造

**JSON Schema はありません**（バックログ BL-006）。`schema_version` は文字列で表すだけで、形はテスト（`tests/batchir/`）で検査しています。設計の正本は CD-5 の設計文書 `batch-ir-minimal-spec.md` です。この文書は Codex の作業ツリー `D:\projects\jcl-profiler-cd5-design-20261117\docs\design\` にあり、**どのブランチにもコミットされていません**（BL-007）。IR の `basis.design` に記録した SHA-256 は `1688deff…` で、2026-11-19 の時点のファイルと一致しています。実装の正本は `src/jclprof/batchir/builder.py` と `corpus.py`、判断の記録は ADR-035〜037（ブランチの `docs/decisions.md`）です。

### トップレベル

| フィールド | 意味 |
|---|---|
| `schema` / `schema_version` / `profile` | `jclprof.batch-ir`、版（`0.1-cd6a` / `0.2-carddemo`）、プロファイル名 |
| `status` | 固定の文 `static IR; expectations PENDING (ADR-027)` |
| `basis` | 入力の原本（`source.file`、`sha256`）、Source AST と Effective View の SHA-256、`library_basis`（`CONFIG` / `UNCONFIRMED_CONTRACT_CONTEXT`）、`run_conditions`（encoding、jes）、Resolver の制限事項（`effective_limitations`）と診断コード（`effective_diagnostics`） |
| `rules` | この IR が使った規則 ID（`JCL-*` は `specs/rules.yaml` の規則、`BIR-*` は builder 内の PENDING の規則） |
| `job` | JOB 名、`mode`（`RUN_ELIGIBLE` / `SCAN_ONLY` / `NOT_A_JOB`）、属性 |
| `resources` | データ集合などの論理資源。GDG の相対世代は参照ごとに別の資源（`GDG_GENERATION`） |
| `steps[]` | STEP の出現。`program`、`run_guard`（COND）、`result`、`bindings[]`（DD：`allocation`、`disp`、`program_access`）、`control_plan`（IDCAMS / SORT などの命令）。未解決の呼出しは `kind: "UNRESOLVED_CALL"` と `call`、`pending_overrides`、`expanded_steps` を持つ |
| `effects[]` | 順序付きの作用。`phase`（ALLOCATION → PROGRAM / COMMAND → DISPOSITION）、`kind`、`target`、`guard`、`origin`、`acts_on`、`outcome` |
| `obligations[]` | 観測義務。`area`（O1 STEP の結果と RC、O2 ファイルの内容、O3 カタログと DISP、O4 SYSOUT と外部 IF、O5 ABEND と再実行、O6 入力と環境）、`required_evidence`、`status` は常に `OPEN` |
| `gaps[]` / `assumptions[]` | 分からないこと（`id`、`kind`、`needs`、`role`、`affects`）と、置いた仮定（`id`、`statement`） |
| `unsupported[]` | 解釈しなかった形（原文と位置。CardDemo では 0 件） |
| `line_index` | `"<file>:<行>"` → その行を出典とする節点 ID |

すべての節点は `source`（`file`、`sha256`、`lines`、`statement_id`）を持ち、原本の物理行に戻れます。

### 事実・導出・仮定・不明・未解決の区別

値はすべて Claim `{value, status, evidence, rules, assumptions, gaps}` で表します。

| status | 意味 | 例 |
|---|---|---|
| `FACT` | 原文に書かれたそのもの | `PGM=MYPROG`、DSN の文字列、TRANREPT の `job.mode` |
| `DERIVED` | 規則を適用して導いた値。`rules` が必須。`BIR-*` の規則を使った値には Gap G02（IBM の資料で未確認）も付く | DISP の省略時の補完、SORT のキー |
| `ASSUMPTION` | 仮定に基づく値。`assumptions` が必須 | A01 同じ DSN は同じデータ集合、A02 GDGBIAS=JOB、A03 契約文脈の PROC ライブラリー |
| `UNKNOWN` | `value` は `null`。Gap が必須 | STEP の RC、GDG の絶対世代、未解決の呼出しの展開結果 |

**未解決の参照**は Claim とは別に記録します。PROC 呼出しの場合は `steps[].kind = "UNRESOLVED_CALL"` と `call.search[]`、`call.reasons`、Gap G15 で表し、`basis.effective_diagnostics` にも RES-W002 / RES-W005 が入ります。

主な Gap：G01 初期のカタログ状態、G02 規則の出典が未確認、G03 実行時の値（RC / ABEND）、G13 GDG の世代の対応、G14 SORT 製品、G15 PROC ライブラリー、G16 外部の制御メンバー、G18 業務プログラムの契約、G24 契約文脈の対応の確認待ち（全一覧は各 IR の `gaps[]`）。

### `obligations.md`（§3.1 のみ）
`batch-ir.json` から作った人が読むための表です（作用、O1〜O6、Gap、仮定）。IR の正本は JSON です。

---

## 7. 出力結果の確認

| 確認 | 方法 | 成功の条件 |
|---|---|---|
| 生成できたか | 終了コードと `wrote ...` の行 | 終了コード 0。§3.1 は 2 ファイル、§3.2 は `wrote 54 files` |
| 再生成が一致するか | 同じ `--out` に対して `--check` | `PASS`、終了コード 0。差があると `DIFFERS <名前>` / `EXTRA <名前>` が出て、終了コード 1 |
| 正式成果物と一致するか | ブランチの `results/batchir/...` に対して `--check`（読むだけ） | `PASS` |
| ファイルごとの一致 | `index.json` の `output_sha256` と `Get-FileHash` | 値が同じ |
| 形と不変条件 | `uv run pytest tests/batchir` | 68 passed |
| 未解決や不明の確認 | IR の `gaps`、`unsupported`、`basis.effective_diagnostics`、`basis.effective_limitations`、`summary.md` の Gaps / Uns. 列 | — （内容を読んで判断する） |

`--check` は「この版のコードと入力から同じバイト列が出る」ことだけを確かめます。IR の内容が正しいかどうかは確かめません。期待値（`tests/golden_pending/cd6a_dusrsecj/`、`cd7_combtran/`、`carddemo_batchir/`）は PENDING で、承認されていません（ADR-026 / 027）。

### 終了コード

| スクリプト | 0 | 1 | 2 |
|---|---|---|---|
| `cd6a_batch_ir.py` | 生成成功 / `--check` PASS | `--check` FAIL、または例外 | 引数の誤り（例：`--job TRANREPT` → `invalid choice`、確認済み） |
| `carddemo_batch_ir.py` | 生成成功 / `--check` PASS | `--check` FAIL、または例外 | 引数の誤り |
| §3.5 の API スクリプト | 生成成功 | 例外（例：入力ファイルが無い → `FileNotFoundError`、確認済み） | — |

`jclprof` CLI の終了コード（ADR-008）は、0 が正常、1 がエラーありで完了、2 が設定・引数・安全性の違反です。IR 生成スクリプトは JCL の診断（RES-W* など）を IR の中に記録するだけで、終了コードには反映しません。

---

## 8. 制約事項

### 実装済み（CardDemo に現れる形だけ）
- JOB / EXEC / DD の構造、名前なし DD の連結、JOBLIB、インストリームデータ（区切り、次の文、EOF）
- PROC の展開（インストリーム → JCLLIB → システムの順の探索、記号パラメーター、DD の上書きと追加、15 段までの入れ子、DCB / DSN の後方参照）。ただし対応表がある文脈に限る
- COND（(0,NE)、(4,LT)）、TYPRUN=SCAN、DISP の 9 形式と省略時の補完、GDG の相対世代
- IDCAMS（DEFINE CLUSTER / GDG / AIX / PATH、DELETE、REPRO、BLDINDEX、SET、IF ... THEN SET）、SORT（FIELDS、INCLUDE COND、OUTREC、SYMNAMES）、IEBGENER、IEFBR14、TSO / DSN、DSNTIAUL、IMS、SDSF、DFHCSDUP、FTP（動詞のみ）
- 業務プログラムは不透明なプログラムとして扱い、DD の向きは `UNKNOWN`（G18）

### 未対応・対象外
- **任意の JCL を変換する CLI が無い**：§3.1 は 2 JOB、§3.2 は固定の 48 ファイルだけ。他の JCL は §3.5 の API で変換できますが、CardDemo にない形は保証しません
- **INCLUDE 文は展開しない**：§3.5 で INCLUDE と JCLLIB を含む JCL（自作）を変換すると、終了コード 0 で IR ができます。INCLUDE の内容は IR に入らず、`basis.effective_limitations` に `INCLUDE_NOT_EXPANDED` が残るだけです。INCLUDE に専用の Gap は付きません
- PROC ライブラリーの本番の対応が無い（`datasets: []`）。本番文脈の 3 つの呼出しは展開されません。契約文脈は未確認の対応です
- Resolver が対象外とする形（`UNSUPPORTED_FORMS`：呼出し側 EXEC の COND など、位置パラメーターの上書き、DCB の結合、PROC 内の SET、記号で書かれた PROC 名や JCLLIB など）。見つかると、その呼出しは展開されません
- IF / THEN / ELSE / ENDIF 文の意味
- 文字コードは UTF-8、JES は UNKNOWN に固定。EBCDIC のバイト列は扱いません（G04）
- `BIR-*` の規則（ユーティリティーの規約）は IBM の資料で未確認です（PENDING、G02）
- JSON Schema が無い（BL-006）。設計文書が未コミット（BL-007）

### 静的な IR と実行の意味の違い
IR を生成できても、JCL の実行の意味を再現したことにはなりません。IR には次の情報がありません。
- 各 STEP の RC と ABEND、COND の評価結果
- 実行時のカタログの状態、GDG の絶対世代と GDGBIAS
- 実際に読み込まれるロードモジュールと PROC ライブラリー
- 業務プログラムの入出力、Db2 / IMS / CICS の状態、外部システムの応答
- SORT 製品の既定値（同じキーの順序、照合順序）

これらは `UNKNOWN` と Gap、または観測義務（すべて `OPEN`）として残っています。値を確定するには、z/OS で実行した証拠が必要です。

---

## 9. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `can't open file ... tools/cd6a_batch_ir.py`、`No module named 'jclprof.batchir'` | `main`（`52dea5d`）で実行している | §2 の手順でコミット `00b2534` を使う |
| `warning: VIRTUAL_ENV=... does not match the project environment path` | 別の仮想環境の `VIRTUAL_ENV` が残っている | 動作には影響しない。`Remove-Item Env:VIRTUAL_ENV` で消せる |
| Python 3.15 が使われる、`requires-python` のエラー | システムの Python を使っている | `uv sync --frozen` / `uv run` を使う（3.12.15 に固定、ADR-001） |
| `FileNotFoundError: ... aws-mainframe-modernization-carddemo\app\...` | CardDemo が設定のパスに無い | `config/profiler.yaml` の `roots[0].path` に CardDemo を置く。パスを変えると出力が変わる場合があるので、`--check` で確かめる |
| `invalid choice: 'XXX'` | `--job` は DUSRSECJ / COMBTRAN だけ | 他の JOB は §3.2 の出力（`official/jcl/XXX.jcl.json`）を使う |
| `DIFFERS ...` / `EXTRA ...` で FAIL | 出力先のファイルが、この版のコードと入力から作ったものと違う。または余分なファイルがある | 比べている版（コミット、CardDemo の SHA-256 は `index.json` の `source_sha256`）を確かめる。新しく生成し直すときは空のフォルダーを使う |
| `NOTE design document changed since CD-6A` | CD-5 の設計文書が変わった | 生成は続く。IR の `basis.design` の SHA-256 は古い版のまま |
| 正式成果物の `git status` に差分が出た | `--out` を省略して既定の出力先に書いた | `git restore results/batchir`（変更を捨てる操作なので、対象を確かめてから実行する）。以後は `--out` を必ず指定する |
| PROC 呼出しが `UNRESOLVED_CALL` になる | 本番設定に PROC ライブラリーの対応が無い（仕様） | 契約文脈（`contract/`）を見る。ただし未確認の対応（A03 / G24）であることに注意する |

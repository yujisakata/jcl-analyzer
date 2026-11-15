"""Render a human review index of the independent CD-1 oracle; never run an analyzer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def label(dd: dict[str, Any]) -> str:
    name = dd["name"] or f"unnamed->{dd['concat_head']}[{dd['concat_index']}]"
    return f"{name}@{dd['line']}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    oracle = json.loads((ROOT / "tests/golden_pending/carddemo_source/expectations.json")
                        .read_text(encoding="utf-8"))
    lines = ["# CD-1 原本照合レビュー索引", "", "全48件PENDING。生成・検査の実行は承認ではない。",
             "この索引も同じ期待値から描画したものであり、第二の独立オラクルではない。",
             "各原本を確認し、階層・全パラメーター・連結・データ範囲・行列をレビューする。",
             "詳細な全トークン/値のセグメントはexpectations.jsonを参照する。", ""]
    for f in oracle["files"]:
        hierarchy = f["expected_structure"]["hierarchy"]
        lines += ["## " + f["path"], "", "SHA-256: `" + f["sha256"] + "`。レビュー: PENDING。", ""]
        steps = []
        for job in hierarchy["jobs"]:
            lines += [f"JOB {job['name']}@{job['line']}、期待span {job['span']}。", "",
                      "JOB DD: " + ", ".join(label(d) for d in job["dds"]), ""]
            steps += job["steps"]
        if "procedure_steps" in hierarchy:
            lines += ["PROC header: " + str(hierarchy["procedure_header"]), ""]
            steps += hierarchy["procedure_steps"]
        lines += ["| STEP/行 | 対象 | DD (原本順) |", "|---|---|---|"]
        for st in steps:
            lines.append(f"| {st['name']}@{st['line']} | {st['target']} | "
                         + ", ".join(label(d) for d in st["dds"]) + " |")
        lines += ["", "tree参照必須の操作文先頭行: " + str(hierarchy["reachable_lines"]), "",
                  "| DD先頭行 | データ行 | 終端 / 行 |", "|---|---|---|"]
        for region in f["data_regions"]:
            records = region["lines"]
            lines.append(f"| {region['dd_line']} | "
                         f"{[records[0], records[-1]] if records else None} | "
                         f"{region['terminator']} / {region['terminator_line']} |")
        lines.append("")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

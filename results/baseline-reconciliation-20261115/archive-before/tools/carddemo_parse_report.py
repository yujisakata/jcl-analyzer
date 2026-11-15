"""Parse all CardDemo JCL/PROC files and report per-file statistics (Step 4b instruction 5).

usage: uv run python tools/carddemo_parse_report.py [--output results/parse]

Writes results/parse/carddemo_parse.json, carddemo_parse.md and one AST JSON per file under
results/parse/ast/. Inputs are opened read-only. "Parsed without an exception" is NOT treated as
success: the report lists diagnostics, unrecognized records, undetermined in-stream regions and
the semantic analyses that were not performed (limitations).

Cross-check: a context-free regex count of records that look like EXEC / DD statements is shown
next to the Parser counts. Differences must be explained by context (in-stream data, comment
statements), and each one is listed.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import load_config
from jclprof.parser import ParseResult, parse_file

ROOT = Path(__file__).resolve().parents[1]
RE_EXEC = re.compile(r"^//[^*\s]*\s+EXEC(\s|$)")
RE_DD = re.compile(r"^//[^*\s]*\s+DD(\s|$)")


def all_steps(r: ParseResult) -> list[Any]:
    out = list(r.procedure_steps)
    for j in r.jobs:
        out += list(j.steps)
        for p in j.procedures:
            out += list(p.steps)
    return out


def analyze(rel: str, path: Path, jes: str) -> tuple[dict[str, Any], ParseResult]:
    kind = "proc_member" if rel.lower().endswith((".prc", ".proc")) else "job"
    r = parse_file(path, encoding="utf-8", jes=jes, input_kind=kind)
    steps = all_steps(r)
    job_dds = [d for j in r.jobs for d in j.job_level_dds]
    step_dds = [d for s in steps for d in s.dds]
    lines = [x.raw for x in r.lex.records]
    regex_exec = [i + 1 for i, ln in enumerate(lines) if RE_EXEC.match(ln)]
    regex_dd = [i + 1 for i, ln in enumerate(lines) if RE_DD.match(ln)]
    parser_exec = sorted(s.span[0] for s in r.statements if s.kind == "EXEC" and s.span)
    parser_dd = sorted(s.span[0] for s in r.statements if s.kind == "DD" and s.span)
    roles = {rr.line: rr.role for rr in r.records}
    diff_exec = sorted(set(regex_exec) ^ set(parser_exec))
    diff_dd = sorted(set(regex_dd) ^ set(parser_dd))
    unexplained = [n for n in diff_exec + diff_dd if roles.get(n) not in ("DATA", "UNDETERMINED")]
    regions = r.data_regions
    info = {
        "file": rel, "input_kind": kind, "sha256": r.lex.sha256, "records": len(r.records),
        "jobs": len(r.jobs), "steps": len(steps),
        "steps_in_instream_procs": sum(len(p.steps) for j in r.jobs for p in j.procedures),
        "dds": len(job_dds) + len(step_dds), "job_level_dds": len(job_dds),
        "implicit_dds": sum(1 for d in step_dds if d.implicit),
        "concatenated_dds": sum(1 for d in job_dds + step_dds if d.concat_index > 0),
        "statement_kinds": dict(sorted(Counter(s.kind for s in r.statements).items())),
        "unknown_statements": [{"line": s.span[0] if s.span else None, "operation": s.operation}
                               for s in r.statements if s.kind == "UNKNOWN"],
        "syntax_errors": [{"code": d.code, "line": d.line, "message": d.message}
                          for d in r.diagnostics if d.severity == "ERROR"],
        "diagnostics": [{"code": d.code, "severity": d.severity, "class": d.cls, "line": d.line,
                         "message": d.message} for d in r.diagnostics],
        "instream": [{"dd_statement": g.statement_id, "mode": g.mode, "dlm": g.dlm,
                      "status": g.status, "records": list(g.records) if g.records else None,
                      "terminator": g.terminator} for g in regions],
        "data_records": sum(1 for rr in r.records if rr.role == "DATA"),
        "unrecognized_records": [rr.line for rr in r.records if rr.role == "UNRECOGNIZED"],
        "undetermined_records": [rr.line for rr in r.records if rr.role == "UNDETERMINED"],
        "limitations": list(r.limitations),
        "procedure_calls": sorted({s.target[1] for s in steps
                                   if s.target and s.target[0] == "PROC"}),
        "cross_check": {"regex_exec": len(regex_exec), "parser_exec": len(parser_exec),
                        "regex_dd": len(regex_dd), "parser_dd": len(parser_dd),
                        "differences_explained_by_data": [n for n in diff_exec + diff_dd
                                                          if n not in unexplained],
                        "unexplained_differences": unexplained},
    }
    return info, r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="results/parse")
    args = ap.parse_args()
    cfg = load_config(ROOT / "config" / "profiler.yaml")
    root = cfg.roots[0].path
    oracle = yaml.safe_load((ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                            .read_text(encoding="utf-8"))
    out = ROOT / args.output
    (out / "ast").mkdir(parents=True, exist_ok=True)
    files = []
    for rel in sorted(oracle["jcl_family_files"]):
        info, r = analyze(rel, root / rel, cfg.jes)
        files.append(info)
        (out / "ast" / (rel.replace("/", "__") + ".ast.json")).write_text(
            json.dumps(r.to_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    totals: dict[str, Any] = {
        "files": len(files), "records": sum(f["records"] for f in files),
        "jobs": sum(f["jobs"] for f in files), "steps": sum(f["steps"] for f in files),
        "dds": sum(f["dds"] for f in files),
        "files_with_instream": sum(1 for f in files if f["instream"]),
        "data_regions": sum(len(f["instream"]) for f in files),
        "undetermined_regions": sum(1 for f in files for g in f["instream"]
                                    if g["status"] == "UNDETERMINED"),
        "data_records": sum(f["data_records"] for f in files),
        "unknown_statements": sum(len(f["unknown_statements"]) for f in files),
        "syntax_errors": sum(len(f["syntax_errors"]) for f in files),
        "diagnostics_by_code": dict(sorted(Counter(d["code"] for f in files
                                                   for d in f["diagnostics"]).items())),
        "unrecognized_records": sum(len(f["unrecognized_records"]) for f in files),
        "limitations": dict(sorted(Counter(x for f in files for x in f["limitations"]).items())),
        "unexplained_cross_check_differences": sum(len(f["cross_check"]["unexplained_differences"])
                                                   for f in files),
        "jes": cfg.jes,
    }
    (out / "carddemo_parse.json").write_text(json.dumps({"totals": totals, "files": files},
                                                        ensure_ascii=False, indent=1) + "\n",
                                             encoding="utf-8")
    L = ["# CardDemo Parse Report (Step 4b)", "",
         f"JES type: {cfg.jes}. A file parsing without an exception is not counted as success; see "
         "the diagnostics, unrecognized/undetermined records and limitations.", "",
         "## Totals", "", "| Item | Value |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in totals.items()]
    L += ["", "## Per file", "",
          "| File | Kind | Jobs | Steps | DDs | In-stream (records) | Unknown stmts | Errors | "
          "Diagnostics | Unrecognized recs | EXEC regex/parser | DD regex/parser | Limitations |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in files:
        ins = f"{len(f['instream'])} ({f['data_records']})" if f["instream"] else "-"
        diags = ", ".join(f"{d['code']}@{d['line']}" for d in f["diagnostics"]) or "-"
        cc = f["cross_check"]
        L.append(f"| {f['file']} | {f['input_kind']} | {f['jobs']} | {f['steps']} | {f['dds']} | "
                 f"{ins} | {len(f['unknown_statements'])} | {len(f['syntax_errors'])} | {diags} | "
                 f"{len(f['unrecognized_records'])} | {cc['regex_exec']}/{cc['parser_exec']} | "
                 f"{cc['regex_dd']}/{cc['parser_dd']} | {', '.join(f['limitations']) or '-'} |")
    (out / "carddemo_parse.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(totals, indent=1))


if __name__ == "__main__":
    main()

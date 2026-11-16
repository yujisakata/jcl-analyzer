"""CD-4 report: resolve all CardDemo JCL under (a) the production config and (b) the UNCONFIRMED
contract context, and write results/resolve/ (JSON per context + report.md).

usage: uv run python tools/cd4_resolve_report.py
Inputs are read-only. Results under (b) are conditional on the unconfirmed mapping (CA-05).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import load_config
from jclprof.resolver import EffectiveResult, LibraryContext, Resolver, load_library_context

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "resolve"


def run(ctx: LibraryContext, root: Path, files: list[str]) -> dict[str, EffectiveResult]:
    r = Resolver(ctx)
    out = {f: r.resolve_file(root / f, f, "carddemo") for f in files
           if not f.lower().endswith(".prc")}
    out["proc/TRANREPT.prc"] = r.resolve_member(root / "proc/TRANREPT.prc", "proc/TRANREPT.prc",
                                                "carddemo", ("AWS.M2.CARDDEMO.PROC",))
    out["proc/REPROC.prc"] = r.resolve_member(root / "proc/REPROC.prc", "proc/REPROC.prc",
                                              "carddemo", None)
    return out


def main() -> None:
    cfg = load_config(ROOT / "config" / "profiler.yaml")
    root = cfg.roots[0].path
    files = sorted(yaml.safe_load((ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                                  .read_text(encoding="utf-8"))["jcl_family_files"])
    contexts = {
        "official": LibraryContext.from_config(cfg),
        "contract": load_library_context(ROOT / "config/contexts/cd4-contract-context.yaml",
                                         {"carddemo": root}),
    }
    L = ["# CD-4 Resolver Report", "",
         "`official` = config/profiler.yaml (datasets: []). `contract` = "
         "config/contexts/cd4-contract-context.yaml, status **UNCONFIRMED_CONTRACT_CONTEXT** "
         "(owner confirmation pending, contract Q01). Contract results are conditional.", ""]
    for name, ctx in contexts.items():
        res = run(ctx, root, files)
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "effective.json").write_text(json.dumps({f: r.to_dict() for f, r in res.items()},
                                                     ensure_ascii=False, indent=1, default=str)
                                          + "\n", encoding="utf-8")
        jobs = [res[f] for f in files if not f.lower().endswith(".prc")]
        c = {k: sum(r.counts()[k] for r in jobs) for k in jobs[0].counts()}
        L += [f"## Context `{name}` (basis {ctx.basis})", "",
              f"- 46 JOB files: program steps {c['program_steps']}, unresolved call steps "
              f"{c['unresolved_call_steps']}, DDs {c['dds']} (job-level {c['job_level_dds']})",
              f"- proc/TRANREPT.prc with context AWS.M2.CARDDEMO.PROC: "
              f"{res['proc/TRANREPT.prc'].counts()}", "",
              "| File | Call line | Requested | Status | Search | Member | Label match |",
              "|---|---|---|---|---|---|---|"]
        for f, r in res.items():
            for call in r.calls:
                srch = "; ".join(f"{s.kind}:{s.library or '-'}={s.result}" for s in call.search)
                L.append(f"| {f} | {call.call.line} | {call.requested} | {call.status} | {srch} "
                         f"| {call.member_path or '-'} | {call.label_matches_member} |")
        L += ["", "| File | Override line | DD | Param | Action | Original | Applied |",
              "|---|---|---|---|---|---|---|"]
        for f, r in res.items():
            for s in [s for j in r.jobs for s in j.steps] + list(r.steps):
                for dd in s.dds:
                    for o in dd.overrides:
                        L.append(f"| {f} | {o.source.line} | {s.name}.{dd.ddname} | {o.param} | "
                                 f"{o.action} | `{json.dumps(o.original)}` | "
                                 f"`{json.dumps(o.applied)}` |")
        diag_counts: dict[str, int] = {}
        for r in res.values():
            for x in r.diagnostics:
                diag_counts[x.code] = diag_counts.get(x.code, 0) + 1
        L += ["", f"Diagnostics: {json.dumps(dict(sorted(diag_counts.items())))}", ""]
        if name == "contract":
            ex = res["jcl/PRTCATBL.jcl"]
            step = next(s for s in ex.jobs[0].steps if s.name == "PRC001")
            sample: dict[str, Any] = asdict(step)
            L += ["### Effective View example: jcl/PRTCATBL.jcl STEP05R -> REPROC.PRC001", "",
                  "```json", json.dumps(sample, ensure_ascii=False, indent=1, default=str)[:12000],
                  "```", ""]
    (OUT / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'report.md'}")


if __name__ == "__main__":
    main()

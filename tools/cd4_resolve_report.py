"""CD-4 report: resolve all CardDemo JCL under (a) the production config and (b) the UNCONFIRMED
contract context, and write results/resolve/ (JSON per context + report.md + run-manifest.json).

usage: uv run python tools/cd4_resolve_report.py [--out DIR]
       uv run python tools/cd4_resolve_report.py --verify [--out DIR] [--manifest-sha256 HEX]
Inputs are read-only. Results under (b) are conditional on the unconfirmed mapping (CA-05).
Outputs are UTF-8 with LF line ends. run-manifest.json (CD-4R F09) records the code version,
inputs, contexts, environment and output hashes; --verify re-derives every VERIFIED fact, lists
the RECORDED_ONLY fields it does not guarantee, and reports the manifest's trust point (its Git
blob in HEAD, or the external SHA-256 given with --manifest-sha256). See manifest.py (R03).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import load_config
from jclprof.resolver import EffectiveResult, LibraryContext, Resolver, load_library_context
from jclprof.resolver.manifest import build_manifest, verify_report

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "resolve"
CONFIG = ROOT / "config" / "profiler.yaml"
CONTRACT = ROOT / "config" / "contexts" / "cd4-contract-context.yaml"
FILE_LIST = ROOT / "tests" / "acceptance" / "expected" / "carddemo_inventory.yaml"
ENCODING, JES = "utf-8", "UNKNOWN"


def write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def run(ctx: LibraryContext, root: Path, files: list[str]) -> dict[str, EffectiveResult]:
    r = Resolver(ctx, encoding=ENCODING, jes=JES)
    out = {f: r.resolve_file(root / f, f, "carddemo") for f in files
           if not f.lower().endswith(".prc")}
    out["proc/TRANREPT.prc"] = r.resolve_member(root / "proc/TRANREPT.prc", "proc/TRANREPT.prc",
                                                "carddemo", ("AWS.M2.CARDDEMO.PROC",))
    out["proc/REPROC.prc"] = r.resolve_member(root / "proc/REPROC.prc", "proc/REPROC.prc",
                                              "carddemo", None)
    return out


def main(out: Path = OUT) -> Path:
    cfg = load_config(CONFIG)
    root = cfg.roots[0].path
    files = sorted(yaml.safe_load(FILE_LIST.read_text(encoding="utf-8"))["jcl_family_files"])
    contexts = {
        "official": LibraryContext.from_config(cfg),
        "contract": load_library_context(CONTRACT, {cfg.roots[0].id: root}),
    }
    context_files = {"official": (CONFIG, "config"), "contract": (CONTRACT, "overlay")}
    outputs: list[Path] = []
    members: dict[str, str] = {}
    all_counts: dict[str, Any] = {}
    L = ["# CD-4 Resolver Report", "",
         "`official` = config/profiler.yaml (datasets: []). `contract` = "
         "config/contexts/cd4-contract-context.yaml, status **UNCONFIRMED_CONTRACT_CONTEXT** "
         "(owner confirmation pending, contract Q01). Contract results are conditional.", ""]
    for name, ctx in contexts.items():
        res = run(ctx, root, files)
        eff = out / name / "effective.json"
        write_lf(eff, json.dumps({f: r.to_dict() for f, r in res.items()},
                                 ensure_ascii=False, indent=1, default=str) + "\n")
        outputs.append(eff)
        for r in res.values():
            for call in r.calls:
                if call.member_path and call.member_sha256:
                    members[call.member_path] = call.member_sha256
        jobs = [res[f] for f in files if not f.lower().endswith(".prc")]
        c = {k: sum(r.counts()[k] for r in jobs) for k in jobs[0].counts()}
        all_counts[name] = {
            "jobs_46": c,
            "unsupported_forms": sum(len(r.unsupported) for r in res.values()),
            "calls": sorted(f"{f}:{call.call.line}:{call.status}"
                            for f, r in res.items() for call in r.calls)}
        L += [f"## Context `{name}` (basis {ctx.basis})", "",
              f"- 46 JOB files: program steps {c['program_steps']}, unresolved call steps "
              f"{c['unresolved_call_steps']}, DDs {c['dds']} (job-level {c['job_level_dds']})",
              f"- proc/TRANREPT.prc with context AWS.M2.CARDDEMO.PROC: "
              f"{res['proc/TRANREPT.prc'].counts()}",
              f"- unsupported forms detected: {all_counts[name]['unsupported_forms']}", "",
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
    report = out / "report.md"
    write_lf(report, "\n".join(L) + "\n")
    outputs.append(report)
    manifest = build_manifest(
        project=ROOT, generator=Path(__file__).resolve(), root_id=cfg.roots[0].id, root=root,
        file_list=FILE_LIST, files=files, members=members,
        contexts={n: (c, *context_files[n]) for n, c in contexts.items()}, out_dir=out,
        outputs=outputs, encoding=ENCODING, jes=JES, counts=all_counts)
    mpath = out / "run-manifest.json"
    write_lf(mpath, json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {report} and {mpath}")
    return mpath


def verify(out: Path = OUT, expected_sha256: str | None = None) -> dict[str, Any]:
    mpath = out / "run-manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    return verify_report(manifest, ROOT, manifest_path=mpath, expected_sha256=expected_sha256)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CD-4 resolver report and run manifest")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--manifest-sha256", default=None)
    a = ap.parse_args()
    if a.verify:
        rep = verify(a.out, a.manifest_sha256)
        for prob in rep["problems"]:
            print(f"PROBLEM {prob}")
        print(f"trust point: {rep['trust']}")
        for n in rep["not_verified"]:
            print(f"NOT VERIFIED {n}")
        print("recorded only (not guaranteed): " + ", ".join(rep["recorded_only"]))
        print("run-manifest: " + ("FAIL" if rep["problems"] else
                                  f"PASS ({len(rep['verified'])} verified fact groups)"))
        sys.exit(1 if rep["problems"] else 0)
    main(a.out)

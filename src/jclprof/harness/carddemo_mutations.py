"""CD-1 single-fault AST mutations, including PROC members and cross-file ownership.

Every detector compares to the independent oracle. A baseline failure is NOT a detection:
the mutant must introduce a new source-comparison difference on an affected file.
"""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from jclprof.harness.carddemo_source import check_case
from jclprof.parser import ParseResult
from jclprof.parser.model import DDNode, StatementNode, StepNode

Site = tuple[str, int, int]


@dataclass(frozen=True)
class Mutation:
    operator: str
    target: str
    changes: dict[str, ParseResult]


def _steps(r: ParseResult) -> Iterator[tuple[int, tuple[StepNode, ...]]]:
    for i, job in enumerate(r.jobs):
        yield i, job.steps
    if r.input_kind == "proc_member":
        yield -1, r.procedure_steps


def _set_steps(r: ParseResult, job: int, steps: tuple[StepNode, ...]) -> ParseResult:
    if job == -1:
        return replace(r, procedure_steps=steps)
    jobs = list(r.jobs)
    jobs[job] = replace(jobs[job], steps=steps)
    return replace(r, jobs=tuple(jobs))


def _sites(r: ParseResult) -> Iterator[tuple[Site, tuple[DDNode, ...]]]:
    for ji, job in enumerate(r.jobs):
        yield ("JOB", ji, -1), job.job_level_dds
        for si, step in enumerate(job.steps):
            yield ("STEP", ji, si), step.dds
    for si, step in enumerate(r.procedure_steps):
        yield ("MEMBER", -1, si), step.dds


def _set_dds(r: ParseResult, site: Site, dds: tuple[DDNode, ...]) -> ParseResult:
    kind, ji, si = site
    if kind == "MEMBER":
        steps = list(r.procedure_steps)
        steps[si] = replace(steps[si], dds=dds)
        return replace(r, procedure_steps=tuple(steps))
    jobs = list(r.jobs)
    job = jobs[ji]
    if kind == "JOB":
        jobs[ji] = replace(job, job_level_dds=dds)
    else:
        steps = list(job.steps)
        steps[si] = replace(steps[si], dds=dds)
        jobs[ji] = replace(job, steps=tuple(steps))
    return replace(r, jobs=tuple(jobs))


def _replace_statement(r: ParseResult, new: StatementNode) -> ParseResult:
    def dd(d: DDNode) -> DDNode:
        return replace(d, statement=new) if d.statement.id == new.id else d

    def step(s: StepNode) -> StepNode:
        return replace(s, exec_statement=new if s.exec_statement.id == new.id else s.exec_statement,
                       dds=tuple(dd(d) for d in s.dds))

    jobs = tuple(replace(j, job_statement=new if j.job_statement.id == new.id else j.job_statement,
                         job_level_dds=tuple(dd(d) for d in j.job_level_dds),
                         steps=tuple(step(s) for s in j.steps)) for j in r.jobs)
    return replace(r, statements=tuple(new if s.id == new.id else s for s in r.statements),
                   jobs=jobs, procedure_steps=tuple(step(s) for s in r.procedure_steps))


def mutations(parsed: dict[str, ParseResult]) -> Iterator[Mutation]:
    jobs = [(path, ji, job) for path, r in parsed.items() for ji, job in enumerate(r.jobs)]
    step_sites = [(path, ji, steps) for path, r in parsed.items() for ji, steps in _steps(r)]
    dd_sites = [(path, site, dds) for path, r in parsed.items() for site, dds in _sites(r)]
    for path, r in parsed.items():
        for ji, job in enumerate(r.jobs):
            others = r.jobs[:ji] + r.jobs[ji + 1:]
            yield Mutation("delete_job", f"{path}:{job.id}", {path: replace(r, jobs=others)})
            dest_path, _, _ = next(x for x in jobs if x[0] != path)
            dest = parsed[dest_path]
            yield Mutation("move_job", f"{path}:{job.id}->{dest_path}",
                           {path: replace(r, jobs=others),
                            dest_path: replace(dest, jobs=(*dest.jobs, job))})
            js = list(r.jobs)
            js[ji] = replace(job, span=(job.span[0], job.span[1] - 1))
            yield Mutation("shrink_span", f"{path}:{job.id}", {path: replace(r, jobs=tuple(js))})
        if r.input_kind == "proc_member":
            yield Mutation("delete_proc_root", path,
                           {path: replace(r, procedure_header=None, procedure_steps=())})
        for ji, steps in _steps(r):
            for si, step in enumerate(steps):
                removed = _set_steps(r, ji, steps[:si] + steps[si + 1:])
                yield Mutation("delete_step", f"{path}:{step.id}", {path: removed})
                dest_path, dest_ji, dest_steps = next(x for x in step_sites if x[0] != path)
                dest = _set_steps(parsed[dest_path], dest_ji, (*dest_steps, step))
                yield Mutation("move_step", f"{path}:{step.id}->{dest_path}",
                               {path: removed, dest_path: dest})
        for site, dds in _sites(r):
            for di, dd in enumerate(dds):
                removed = _set_dds(r, site, dds[:di] + dds[di + 1:])
                yield Mutation("delete_dd", f"{path}:{dd.statement.id}", {path: removed})
                # Use another actual step, including empty steps; a JOB-level DD may not
                # silently migrate to the first EXEC's scope.
                dest_path, dest_site, dest_dds = next(
                    x for x in dd_sites if x[1][0] != "JOB"
                    and (x[0] != path or x[1] != site))
                dest = _set_dds(removed if dest_path == path else parsed[dest_path],
                                dest_site, (*dest_dds, dd))
                changed = {path: removed, dest_path: dest}
                yield Mutation("move_dd", f"{path}:{dd.statement.id}->{dest_path}:{dest_site}",
                               changed)
                if dd.concat_index > 0:
                    swapped = list(dds)
                    swapped[di - 1], swapped[di] = swapped[di], swapped[di - 1]
                    yield Mutation("reorder_concat", f"{path}:{dd.statement.id}",
                                   {path: _set_dds(r, site, tuple(swapped))})
        for region in r.data_regions:
            assert region.records is not None
            lo, hi = region.records
            new = replace(region, records=(lo, hi - 1) if hi > lo else None)
            owner = next(s for s in r.statements if s.id == region.statement_id)
            changed_r = _replace_statement(r, replace(owner, inline=new))
            changed_r = replace(changed_r,
                                data_regions=tuple(new if g.id == region.id else g
                                                   for g in r.data_regions),
                                records=tuple(replace(rec, role="UNRECOGNIZED", statement_id=None,
                                                      region_id=None) if rec.line == hi else rec
                                              for rec in r.records))
            yield Mutation("data_boundary", f"{path}:{region.id}", {path: changed_r})


def _fingerprints(issues: list[dict[str, Any]]) -> set[str]:
    return {json.dumps(d, sort_keys=True, ensure_ascii=False) for d in issues}


def mutation_report(oracle: dict[str, Any], parsed: dict[str, ParseResult],
                    corpus: Path, baseline: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {f["path"]: f for f in oracle["files"]}
    raw = {path: (corpus / path).read_bytes() for path in parsed}
    source_base = {r["path"]: _fingerprints(r["source_differences"]) for r in baseline}
    rows: dict[str, dict[str, Any]] = {}
    escaped = []
    primary: Counter[str] = Counter()
    total = detected = 0
    for mutant in mutations(parsed):
        total += 1
        delta: list[dict[str, Any]] = []
        for path, result in mutant.changes.items():
            checked = check_case(expected[path], result, raw[path])
            new = _fingerprints(checked["source_differences"]) - source_base[path]
            delta.extend({"path": path, "difference": json.loads(d)} for d in sorted(new))
        hit = bool(delta)
        detected += hit
        row = rows.setdefault(mutant.operator, {"total": 0, "detected": 0, "examples": []})
        row["total"] += 1
        row["detected"] += hit
        primary[next(iter(mutant.changes))] += 1
        detail = {"operator": mutant.operator, "target": mutant.target,
                  "affected_files": list(mutant.changes), "new_source_differences": len(delta)}
        if len(row["examples"]) < 2:
            row["examples"].append({**detail, "sample": delta[:2]})
        if not hit:
            escaped.append(detail)
    required = {"delete_job", "delete_proc_root", "move_job", "delete_step", "move_step",
                "delete_dd", "move_dd", "reorder_concat", "data_boundary", "shrink_span"}
    missing = sorted(required - set(rows))
    if missing:
        escaped.append({"missing_operators": missing})
    unexecuted = sorted(set(expected) - set(parsed))
    if unexecuted:
        escaped.append({"unexecuted_files": unexecuted})
    return {"total": total, "detected": detected, "escaped": escaped, "operators": rows,
            "primary_files": dict(primary),
            "criterion": "NEW difference from the independent SOURCE oracle; existing A10/H01/H02 "
                         "failures alone do not count; trace-only detection does not count"}

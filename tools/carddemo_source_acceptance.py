"""Run CD-1 without changing Gate A, generic Gate B, Parser or Golden expectations."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from jclprof.harness.carddemo_mutations import mutation_report
from jclprof.harness.carddemo_source import DEFAULT_ORACLE, decisions, load_oracle, run_cases


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    ap.add_argument("--output", type=Path, default=Path("results/carddemo_source"))
    args = ap.parse_args()
    if args.output.resolve().is_relative_to(args.corpus.resolve()):
        ap.error("output must be outside the read-only corpus")
    oracle, reviews = load_oracle(args.oracle)
    results, parsed = run_cases(oracle, args.corpus)
    mutations = mutation_report(oracle, parsed, args.corpus, results)
    gates = decisions(results, reviews, mutations)
    review_by_path = {r["path"]: r for r in reviews["files"]}
    for result in results:
        result["review_status"] = review_by_path[result["path"]]["status"]
    report = {"schema_version": 1, "suite": "CD-1", "run_at": datetime.now(UTC).isoformat(),
              "baseline_source_sha256": oracle["baseline_source_sha256"],
              "provenance": oracle["provenance"], "gates": gates, "files": results}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "mutations.json").write_text(
        json.dumps(mutations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# CD-1 Source Structure Acceptance", "",
             "Review status is independent of measured verification status.", "",
             "| Gate | Status |", "|---|---|"]
    for name in ("CD-SOURCE", "CD-TRACE", "CD-ASSURANCE"):
        lines.append(f"| {name} | {gates[name]['status']} |")
        print(f"{name}: {gates[name]['status']}")
    lines += ["", f"Formal acceptance: {gates['formal_acceptance']}", "",
              f"Mutations: {mutations['detected']}/{mutations['total']} newly detected; "
              f"escaped: {len(mutations['escaped'])}", "",
              "| File | Input | Source | Trace | Review |", "|---|---|---|---|---|"]
    for result in results:
        lines.append(f"| {result['path']} | {result['input_status']} | "
                     f"{result['source_status']} | {result['trace_status']} | "
                     f"{result['review_status']} |")
    (args.output / "acceptance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"mutations: {mutations['detected']}/{mutations['total']}; "
          f"escaped: {len(mutations['escaped'])}")
    print(f"formal acceptance: {gates['formal_acceptance']}")
    return 0 if gates["formal_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

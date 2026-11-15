"""H-06 CI quality gate: one command that runs every check and reports each result separately.

usage: uv run python tools/quality_gate.py [--output results/harness]

Checks (in order):
  1. ruff             lint (src, tests, tools)
  2. mypy             strict type check
  3. harness-suite    pytest tests/unit tests/acceptance tests/harness (Harness self-tests)
  4. golden-defs      Golden definition schema + semantic validation
  5. golden-integrity Golden files match MANIFEST.json (no unsealed change)
  6. rules-sync       specs/ibm-jcl-reference.md matches specs/rules.yaml + Golden suite
  7. golden-run       Golden suite through registered adapters (FAILED fails the gate;
                      NOT_IMPLEMENTED / BLOCKED are reported, not failures)
  8. analyzer-suite   pytest tests/lexer tests/parser tests/property: Lexer spec/property/IO tests
                      plus the parser verification suite (skips = NOT_IMPLEMENTED / BLOCKED;
                      failures or errors fail the gate)
Parser absence is never counted as a Harness failure, and statuses are never merged into one rate.
This tool runs development tooling as subprocesses; it never executes JCL (requirements 8.4).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    data: dict[str, object] = field(default_factory=dict)


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", check=False)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _pytest_counts(out: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    for n, word in re.findall(r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed|deselected)",
                              tail):
        counts[word.rstrip("s") if word.startswith("error") else word] = int(n)
    return counts


def _skip_reasons(out: str) -> dict[str, int]:
    reasons: dict[str, int] = {}
    for line in out.splitlines():
        m = re.match(r"SKIPPED \[(\d+)\] [^:]+(?::\d+)?: (.*)", line)
        if m:
            key = m.group(2).split(":", 1)[0].strip()
            reasons[key] = reasons.get(key, 0) + int(m.group(1))
    return reasons


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="results/harness")
    args = ap.parse_args(argv)
    py = sys.executable
    checks: list[Check] = []

    rc, out = _run([py, "-m", "ruff", "check", "src", "tests", "tools"])
    checks.append(Check("ruff", rc == 0, out.strip().splitlines()[-1] if out.strip() else ""))

    rc, out = _run([py, "-m", "mypy"])
    checks.append(Check("mypy", rc == 0, out.strip().splitlines()[-1] if out.strip() else ""))

    rc, out = _run([py, "-m", "pytest", "-q", "-rs", "tests/unit", "tests/acceptance",
                    "tests/harness"])
    counts = _pytest_counts(out)
    reasons = _skip_reasons(out)
    checks.append(Check("harness-suite", rc == 0, out.strip().splitlines()[-1],
                        {"counts": counts, "skips": reasons,
                         "unverified": [r for r in reasons if "symlink" in r.lower()]}))

    rc, out = _run([py, "-m", "jclprof", "golden-check"])
    defs_ok = "case(s) valid" in out
    checks.append(Check("golden-defs", defs_ok, next(
        (ln for ln in out.splitlines() if ln.startswith("golden definitions")), out[-300:])))
    checks.append(Check("golden-integrity", rc == 0 and defs_ok, next(
        (ln for ln in out.splitlines() if ln.startswith("golden integrity")), out[-300:])))

    rc, out = _run([py, "-m", "jclprof", "rules-render", "--check"])
    checks.append(Check("rules-sync", rc == 0, out.strip()))

    rc, out = _run([py, "-m", "jclprof", "verify", "--output", args.output])
    run_counts: dict[str, int] = {}
    report = ROOT / args.output / "golden_run.json"
    for line in out.splitlines():
        m = re.match(r"^(PASSED|FAILED|BLOCKED|NOT_IMPLEMENTED|NOT_RUN): (\d+)$", line)
        if m:
            run_counts[m.group(1)] = int(m.group(2))
    by_assurance: dict[str, object] = {}
    if report.is_file():
        by_assurance = json.loads(report.read_text(encoding="utf-8")).get("counts_by_assurance", {})
    checks.append(Check("golden-run", rc == 0, json.dumps(run_counts),
                        {"counts": run_counts, "by_assurance": by_assurance}))

    rc, out = _run([py, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", "tests/lexer",
                    "tests/parser", "tests/property"])
    pcounts = _pytest_counts(out)
    checks.append(Check("analyzer-suite", rc == 0 and not pcounts.get("failed")
                        and not pcounts.get("error"),
                        out.strip().splitlines()[-1] if out.strip() else "",
                        {"counts": pcounts, "skips": _skip_reasons(out)}))

    passed = all(c.ok for c in checks)
    out_dir = ROOT / args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "quality_gate.json").write_text(json.dumps({
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "gate": "PASS" if passed else "FAIL",
        "checks": [asdict(c) for c in checks],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    width = max(len(c.name) for c in checks)
    for c in checks:
        print(f"{'PASS' if c.ok else 'FAIL'}  {c.name.ljust(width)}  {c.detail}")
    print(f"NOTE  golden-run by assurance (REFERENCE = draft expectations, not formal QA): "
          f"{json.dumps(checks[6].data.get('by_assurance'))}")
    unverified = checks[2].data.get("unverified")
    if unverified:
        print(f"NOTE  unverified (skipped) harness tests: {unverified}")
    print(f"GATE: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

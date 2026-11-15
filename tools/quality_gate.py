"""H-06 quality gates (ADR-028): Gate A = development health, Gate B = Parser formal acceptance.

usage: uv run python tools/quality_gate.py [--gate dev|acceptance] [--output results/harness]

Gate A (dev, default) -- "nothing is broken that is not a registered, visible known defect":
  1. ruff               lint (src, tests, tools)
  2. mypy               strict type check
  3. harness-suite      pytest tests/unit tests/acceptance tests/harness
  4. golden-defs        sealed Golden definitions valid
  5. golden-integrity   sealed Golden files match MANIFEST.json
  6. rules-sync         specs/ibm-jcl-reference.md matches specs/rules.yaml
  7. known-defects      tests/KNOWN_DEFECTS.yaml valid; listed Golden cases exist
  8. golden-run         sealed suite: every FAILED case is listed under an OPEN known defect;
                        a listed case that no longer fails is stale (fails the gate)
  9. pending-defs       tests/golden_pending definitions valid (review pending, unsealed)
 10. pending-run        review-pending suite: same rule as 8
 11. analyzer-suite     pytest tests/lexer tests/parser tests/property: no failure or error;
                        every XFAIL registered under an OPEN known defect; no XPASS
 12. hierarchy-mutation every required AST mutation (M1-M7) is detected
Gate A prints the OPEN known defects; a PASS never means "accepted".

Gate B (acceptance) -- Gate A plus B1-B9 (jclprof.harness.gates.acceptance_checks): no in-scope
defect that is not CLOSED, no xfail, every in-scope Golden case approved, implemented, unblocked
and passing, no review-pending case, every executed syntactic case asserts the hierarchy, and an
approved acceptance scope (tests/ACCEPTANCE_SCOPE.yaml).
This tool runs development tooling as subprocesses; it never executes JCL (requirements 8.4).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jclprof.harness.defects import RegistryError, load_known_defects  # noqa: E402
from jclprof.harness.gates import (  # noqa: E402
    Check,
    acceptance_checks,
    classify_golden,
    classify_xfails,
    load_scope,
)


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", check=False)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _last(out: str) -> str:
    return out.strip().splitlines()[-1] if out.strip() else ""


def _pytest_counts(out: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for n, word in re.findall(r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed|deselected)",
                              _last(out)):
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


def _report_ids(out: str, word: str) -> list[str]:
    return sorted({m.group(1).replace("\\", "/") for m in
                   re.finditer(rf"^{word} (\S+)", out, re.MULTILINE)})


def _golden(py: str, suite: str, output: str) -> tuple[bool, str, list[dict[str, Any]]]:
    _, out = _run([py, "-m", "jclprof", "golden-check", "--suite", suite])
    defs_ok = "case(s) valid" in out
    defs = next((ln for ln in out.splitlines() if ln.startswith("golden definitions")),
                out[-300:])
    _run([py, "-m", "jclprof", "verify", "--suite", suite, "--output", output])
    report = ROOT / output / "golden_run.json"
    results = json.loads(report.read_text(encoding="utf-8"))["results"] if report.is_file() else []
    return defs_ok, defs, results


def gate_a(py: str, output: str) -> tuple[list[Check], dict[str, Any]]:
    checks: list[Check] = []
    ctx: dict[str, Any] = {}
    rc, out = _run([py, "-m", "ruff", "check", "src", "tests", "tools"])
    checks.append(Check("ruff", rc == 0, _last(out)))
    rc, out = _run([py, "-m", "mypy"])
    checks.append(Check("mypy", rc == 0, _last(out)))
    rc, out = _run([py, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", "tests/unit",
                    "tests/acceptance", "tests/harness"])
    reasons = _skip_reasons(out)
    checks.append(Check("harness-suite", rc == 0, _last(out),
                        {"counts": _pytest_counts(out), "skips": reasons,
                         "unverified": [r for r in reasons if "symlink" in r.lower()]}))
    rc, out = _run([py, "-m", "jclprof", "golden-check"])
    defs_ok = "case(s) valid" in out
    checks.append(Check("golden-defs", defs_ok, next(
        (ln for ln in out.splitlines() if ln.startswith("golden definitions")), out[-300:])))
    checks.append(Check("golden-integrity", rc == 0 and defs_ok, next(
        (ln for ln in out.splitlines() if ln.startswith("golden integrity")), out[-300:])))
    rc, out = _run([py, "-m", "jclprof", "rules-render", "--check"])
    checks.append(Check("rules-sync", rc == 0, out.strip()))

    try:
        defects = load_known_defects()
        reg_err = ""
    except (RegistryError, OSError) as e:
        defects, reg_err = [], str(e)
    ctx["defects"] = defects

    _, _, golden = _golden(py, "tests/golden", output)
    p_ok, p_defs, pending = _golden(py, "tests/golden_pending", f"{output}/pending")
    ctx["golden"], ctx["pending"] = golden, pending
    known_ids = {r["test_id"] for r in golden + pending}
    listed = {c for d in defects for c in d.golden_cases}
    missing_cases = sorted(listed - known_ids)
    checks.append(Check("known-defects", not reg_err and not missing_cases,
                        reg_err or (f"{len(defects)} registered, "
                                    f"{sum(d.open for d in defects)} OPEN" +
                                    (f"; unknown Golden ids {missing_cases}"
                                     if missing_cases else ""))))
    for name, res in (("golden-run", golden), ("pending-run", pending)):
        unexpected, known, stale = classify_golden(res, defects)
        counts: dict[str, int] = {}
        for r in res:
            counts[r["verification_status"]] = counts.get(r["verification_status"], 0) + 1
        detail = json.dumps(counts)
        if known:
            detail += f"; known-defect FAILED {known}"
        if unexpected:
            detail += f"; UNEXPECTED FAILED {unexpected}"
        if stale:
            detail += f"; STALE (registered, not failing) {stale}"
        checks.append(Check(name, not unexpected and not stale, detail,
                            {"counts": counts, "known": known, "unexpected": unexpected,
                             "stale": stale}))
        if name == "golden-run":
            checks.append(Check("pending-defs", p_ok, p_defs + " (unsealed by design)"))

    rc, out = _run([py, "-m", "pytest", "-q", "-rsxX", "-p", "no:cacheprovider", "tests/lexer",
                    "tests/parser", "tests/property"])
    pc = _pytest_counts(out)
    xfailed, xpassed = _report_ids(out, "XFAIL"), _report_ids(out, "XPASS")
    unreg, registered, unseen = classify_xfails(xfailed, xpassed, defects)
    ctx["xfailed"] = xfailed
    ok = rc == 0 and not pc.get("failed") and not pc.get("error") and not unreg and not unseen
    detail = _last(out)
    if unreg:
        detail += f"; UNREGISTERED xfail/xpass {unreg}"
    if unseen:
        detail += f"; registered xfail not reported {unseen}"
    checks.append(Check("analyzer-suite", ok, detail,
                        {"counts": pc, "skips": _skip_reasons(out),
                         "xfail_by_defect": registered}))

    rc, out = _run([py, "tools/hierarchy_mutation_report.py", "--output", output])
    checks.append(Check("hierarchy-mutation", rc == 0,
                        next((ln for ln in out.splitlines() if ln.startswith("required")),
                             _last(out))))
    return checks, ctx


def _print(title: str, checks: list[Check]) -> bool:
    width = max(len(c.name) for c in checks)
    print(f"== {title}")
    for c in checks:
        print(f"{'PASS' if c.ok else 'FAIL'}  {c.name.ljust(width)}  {c.detail}")
    return all(c.ok for c in checks)


def _write(path: Path, gate: str, passed: bool, checks: list[Check],
           extra: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"), "gate": gate,
        "result": "PASS" if passed else "FAIL", "checks": [asdict(c) for c in checks], **extra,
    }, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", choices=["dev", "acceptance"], default="dev")
    ap.add_argument("--output", default="results/harness")
    args = ap.parse_args(argv)
    py = sys.executable
    checks, ctx = gate_a(py, args.output)
    dev_ok = _print("Gate A: development health", checks)
    defects = ctx["defects"]
    open_list = [f"{d.id} {d.severity} {d.status}: {d.title}" for d in defects
                 if d.status != "CLOSED"]
    for line in open_list:
        print(f"KNOWN {line}")
    unverified = checks[2].data.get("unverified")
    if unverified:
        print(f"NOTE  unverified (skipped) harness tests: {unverified}")
    n_open = sum(d.open for d in defects)
    note = f" (with {n_open} OPEN known defects; not an acceptance)" if dev_ok else ""
    print(f"DEV-HEALTH: {'PASS' if dev_ok else 'FAIL'}{note}")
    out_dir = ROOT / args.output
    _write(out_dir / "quality_gate.json", "A (development health)", dev_ok, checks,
           {"known_defects_not_closed": open_list})
    if args.gate == "dev":
        return 0 if dev_ok else 1
    b = acceptance_checks(dev_ok=dev_ok, defects=defects, golden=ctx["golden"],
                          pending=ctx["pending"], xfailed=ctx["xfailed"], scope=load_scope())
    acc_ok = _print("Gate B: Parser formal acceptance", b)
    print(f"PARSER-ACCEPTANCE: {'PASS' if acc_ok else 'FAIL'}")
    _write(out_dir / "quality_gate_acceptance.json", "B (Parser formal acceptance)", acc_ok, b,
           {})
    return 0 if acc_ok else 1


if __name__ == "__main__":
    sys.exit(main())

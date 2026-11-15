"""Generate the independent Golden review packet (Step 4a instruction B).

For each representative case: Test ID, full input JCL (with a column ruler), the expected Golden
View, the IBM basis (URL, edition, section, page, rule summary, verification status), the reason
the expectation is defined that way, and the open/unconfirmed/environment-dependent points.
The packet is generated from the sealed definitions, so it cannot drift from them. It never
changes review_status.

usage: uv run python tools/golden_review/make_packet.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import load_config
from jclprof.harness.loader import GoldenCase, load_suite
from jclprof.harness.registry import RuleRegistry, load_catalog, load_rules

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "reviews" / "golden-review-packet.md"

# Representatives: different syntax rules first (continuation, quotes, in-stream, IF, PROC),
# then one or more per remaining category. Includes cases changed by decisions A1-A7.
SELECTION: list[tuple[str, str]] = [
    ("G-CONT-002", "Continuation: comment continuation by column 72 after parameter continuation (IBM example 3)"),
    ("G-CONT-102", "Continuation: the same input in the Lexer's lexical view"),
    ("G-CONT-003", "Continuation: apostrophe-enclosed value split at column 71, resumed at column 16 (IBM example 4)"),
    ("G-CONT-104", "Continuation: column 3 not blank where a continuation was expected"),
    ("G-CONT-009", "Continuation + null statement (decision A7)"),
    ("G-QP-001", "Quotes: doubled apostrophe, comma and blank inside apostrophes"),
    ("G-QP-101", "Quotes: lexical tokens for the same rules"),
    ("G-QP-005", "Quotes: unterminated apostrophe"),
    ("G-IS-003", "In-stream: DD DATA containing // records"),
    ("G-IS-008", "In-stream: implicit SYSIN DD (raw vs normalized, decision A5)"),
    ("G-IS-006", "In-stream: DD DATA without delimiter (decision A3)"),
    ("G-IS-005", "In-stream: JES-dependent DLM on DD * (decision A2, blocked)"),
    ("G-IF-004", "IF: AND/OR same priority, evaluated in coded order"),
    ("G-IF-005", "IF: continued relational expression"),
    ("G-IF-101", "IF: lexical tokens of a continued relational expression"),
    ("G-PP-001", "PROC: in-stream procedure definition and call"),
    ("G-PP-010", "PROC: nested INVOCATION, valid (decision A4)"),
    ("G-PP-005", "PROC: nested DEFINITION, invalid (decision A4, blocked)"),
    ("G-PP-009", "PROC: CardDemo label/member mismatch (real asset)"),
    ("G-JED-001", "JOB/EXEC/DD: minimal job"),
    ("G-JED-006", "JOB/EXEC/DD: unrecognized operation (decision A6)"),
    ("G-CAT-002", "Concatenation: semantic view"),
    ("G-GD-003", "DISP defaults"),
    ("G-GD-004", "DISP=MOD as RUNTIME_DEPENDENT (decision A1)"),
    ("G-JIS-011", "Symbols: undefined symbol left literal (IBM example)"),
    ("G-CD-002", "COND: COND.procstep on a calling EXEC"),
    ("G-INV-002", "Unresolved: cyclic procedure calls"),
]

def ruler() -> str:
    tens = "".join(str((i // 10) % 10) if i % 10 == 0 else " " for i in range(1, 81))
    ones = "".join(str(i % 10) for i in range(1, 81))
    return f"      {tens}\n      {ones}"


def input_text(case: GoldenCase, corpus: dict[str, Path]) -> tuple[str, str]:
    p = case.resolve_input(corpus)
    if p is None or not p.is_file():
        return "(input not available)", ""
    lines = p.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    lo, hi = 1, len(lines)
    note = ""
    if case.is_corpus_input:
        lo, hi = case.raw["corpus_source"]["lines"]
        cs = case.raw["corpus_source"]
        note = (f"Original file `{cs['root_id']}:{cs['rel_path']}` (SHA-256 `{cs['sha256']}`), "
                f"records {lo}-{hi} only. The file is referenced, not copied.")
    body = "\n".join(f"{n:4d}  {lines[n - 1]}" for n in range(lo, hi + 1))
    return ruler() + "\n" + body, note


def basis(case: GoldenCase, reg: RuleRegistry) -> list[str]:
    out = ["| Rule | Status | Summary | Source |", "|---|---|---|---|"]
    for rid in case.rule_ids:
        r = reg.rules[rid]
        d = reg.documents[r.doc]
        src = f"{d.title}, {d.edition}, {r.chapter} > {r.section}, p.{r.pages}<br>{d.url}"
        out.append(f"| {rid} | {r.status} | {r.summary.replace('|', '/')} | {src.replace('|', '/')} |")
    return out


def open_points(case: GoldenCase, reg: RuleRegistry, catalog: dict[str, Any]) -> list[str]:
    pts: list[str] = []
    if case.review_status == "blocked":
        pts.append(f"**BLOCKED**: {case.raw['blocked_reason']}")
    weak = [r for r in case.rule_ids if reg.rules[r].status not in ("VERIFIED", "PROJECT-POLICY")]
    if weak:
        pts.append(f"Rules not verified against the primary source: {', '.join(weak)}")
    pol = [r for r in case.rule_ids if reg.rules[r].status == "PROJECT-POLICY"]
    if pol:
        pts.append(f"Depends on project policy, not IBM: {', '.join(pol)}. The reviewer should "
                   "confirm the policy itself.")
    env = case.raw.get("environment")
    if env:
        pts.append(f"Environment assumptions: `{env}`")
    for d in case.raw["expected_diagnostics"]["items"]:
        spec = catalog[d["code"]]
        pts.append(f"Diagnostic {d['code']} ({spec['severity']}, class {spec.get('class', '-')}): "
                   f"{spec['title']}")
    if case.raw.get("notes"):
        pts.append(f"Notes: {case.raw['notes']}")
    return pts or ["None recorded."]


def main() -> None:
    reg = load_rules(ROOT / "specs" / "rules.yaml")
    catalog = load_catalog(ROOT / "specs" / "diagnostic-catalog.yaml")
    res = load_suite(ROOT / "tests" / "golden", reg, catalog)
    if res.errors:
        raise SystemExit("golden definitions invalid; fix before generating the packet")
    by_id = {c.test_id: c for c in res.cases}
    try:
        corpus = {r.id: r.path for r in load_config(ROOT / "config" / "profiler.yaml").roots}
    except Exception:
        corpus = {}
    L = [
        "# Golden Test Independent Review Packet",
        "",
        "Generated by `tools/golden_review/make_packet.py` from `tests/golden/cases/`. Regenerate it after any change.",
        "",
        "**Purpose**: an independent review of representative Golden expectations. Every case below is "
        "`draft` or `blocked`; nothing has been approved. The reviewer checks each case against the "
        "cited IBM text, not against any implementation output.",
        "",
        "**How to record a review**: write the result (agree / disagree + reason) per case. Only a "
        "reviewer's explicit decision may change `review_status`, recorded in the case together with "
        "an `approval` record, and the suite is then resealed with `jclprof golden-seal --by <name>`.",
        "",
        "**Notation**: the expected view format is defined in `docs/golden-view.md`. The column ruler "
        "above each input marks columns 1-80 (tens digit every 10 columns).",
        "",
        "## Contents",
        "",
    ]
    L += [f"{i}. [{tid}](#{tid.lower()}): {why}" for i, (tid, why) in enumerate(SELECTION, 1)]
    for tid, why in SELECTION:
        c = by_id[tid]
        text, note = input_text(c, corpus)
        L += ["", "---", "", f"## {tid}", "",
              f"**Why selected**: {why}", "",
              f"- Category: {c.category} / Case type: {c.raw['case_type']} / Stage: {c.stage} / "
              f"Review status: **{c.review_status}**",
              f"- Description: {c.raw['description']}",
              f"- Input: `{c.input_file}` ({c.raw['input_kind']})", ""]
        if note:
            L += [note, ""]
        L += ["### Input JCL (full text)", "", "```", text, "```", "",
              "### Expected Golden View", "", "```yaml",
              yaml.safe_dump({"expected_structure": c.raw["expected_structure"],
                              "expected_diagnostics": c.raw["expected_diagnostics"]},
                             sort_keys=False, allow_unicode=True, width=110).rstrip(),
              "```", "",
              "### IBM basis", ""]
        L += basis(c, reg)
        L += ["", "### Why the expectation is defined this way", "",
              f"- {c.raw['description']}",
              f"- Oracle method: {c.raw['oracle_method']}",
              f"- Oracle author: {c.raw['oracle_author']}"]
        for ch in c.raw.get("change_log", []):
            L.append(f"- Changed {ch['date']}: {ch['reason']} (basis: {ch['basis']})")
        L += ["", "### Unconfirmed / environment-dependent points", ""]
        L += [f"- {p}" for p in open_points(c, reg, catalog)]
        L += ["", "### Reviewer result", "", "- [ ] agree  - [ ] disagree  — reason:", ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({len(SELECTION)} cases)")


if __name__ == "__main__":
    main()

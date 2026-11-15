"""CD-1 oracle authoring from frozen independent inventory and original bytes ONLY.

No jclprof import, subprocess, Parser, Lexer, Harness, or actual-result input is permitted.
This deliberately supports only the already observed CardDemo forms. Generation is not approval.
Refuses to overwrite any existing oracle. Never use it to repair a failed comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "86878b6588133f6f796b104f8359e5c11e0c7f48f896fe9a5f7345a64bd50b4b"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def groups(text: str) -> list[tuple[int, int]]:
    """Top-level comma ranges, keeping empty positional elements."""
    out = []
    start = depth = i = 0
    quoted = False
    while i < len(text):
        char = text[i]
        if char == "'":
            if quoted and text[i:i + 2] == "''":
                i += 2
                continue
            quoted = not quoted
        elif not quoted:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                out.append((start, i))
                start = i + 1
        assert depth >= 0
        i += 1
    assert depth == 0 and not quoted
    return [*out, (start, len(text))] if text else []


def value(text: str, locations: list[list[int]]) -> dict[str, Any]:
    spec: dict[str, Any] = {"text": text, "segments": segments(locations)}
    if locations:
        spec["line"], spec["column"] = locations[0]
    if not text:
        spec.update(kind="NULL", view=None)
    elif text.startswith("'") and text.endswith("'"):
        spec.update(kind="STRING", view={"q": text[1:-1].replace("''", "'")})
    elif text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        items = [value(inner[a:b], locations[a + 1:b + 1]) for a, b in groups(inner)]
        spec.update(kind="LIST", items=items, view=[x["view"] for x in items])
    elif match := re.match(r"^([A-Z][A-Z0-9.]*)=(.*)$", text):
        at = len(match[1]) + 1
        sub = value(text[at:], locations[at:]) if text[at:] else None
        spec.update(kind="KWSUB", keyword=match[1], sub=sub,
                    view={"kw": [match[1], sub["view"] if sub else None]})
    elif not any(c in text for c in "(),='"):
        spec.update(kind="WORD", view=text)
    else:
        spec.update(kind="COMPOUND", view=text)
    return spec


def segments(points: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for line, col in points:
        if out and out[-1][0] == line and out[-1][2] + 1 == col:
            out[-1][2] = col
        else:
            out.append([line, col, col])
    return out


def lexical(text: str, points: list[list[int]]) -> list[dict[str, Any]]:
    out = []
    i = 0
    punctuation = {"(": "LPAREN", ")": "RPAREN", ",": "COMMA", "=": "EQUALS"}
    while i < len(text):
        start = i
        if text[i] in punctuation:
            kind, decoded = punctuation[text[i]], text[i]
            i += 1
        elif text[i] == "'":
            i += 1
            while i < len(text):
                if text[i:i + 2] == "''":
                    i += 2
                elif text[i] == "'":
                    i += 1
                    break
                else:
                    i += 1
            kind, decoded = "STRING", text[start + 1:i - 1].replace("''", "'")
        else:
            while i < len(text) and text[i] not in "(),='":
                i += 1
            kind, decoded = "WORD", text[start:i]
        out.append({"type": kind, "text": text[start:i], "value": decoded,
                    "line": points[start][0], "column": points[start][1],
                    "segments": segments(points[start:i])})
    return out


def parameter_source(stmt: dict[str, Any], lines: list[str]) -> tuple[str, list[list[int]], int]:
    text = ""
    points: list[list[int]] = []
    operation_column = 0
    for index, n in enumerate(stmt["lines"]):
        line = lines[n - 1][:71]
        if index == 0:
            pattern = (r"^//(?P<name>[^ ]+) +(?P<op>[A-Z]+)(?: +(?P<payload>.*))?$"
                       if stmt["name"] else r"^// +(?P<op>[A-Z]+)(?: +(?P<payload>.*))?$")
            match = re.match(pattern, line)
            assert match and match["op"] == stmt["operation"], (stmt, line)
            if stmt["name"]:
                assert match["name"] == stmt["name"]
            operation_column = match.start("op") + 1
            start = match.start("payload") if match["payload"] is not None else len(line)
        else:
            assert line.startswith("// ")
            start = 2 + len(line[2:]) - len(line[2:].lstrip(" "))
            assert 3 <= start <= 15
        q = False
        pos = start
        while pos < len(line):
            ch = line[pos]
            if ch == "'":
                if q and line[pos:pos + 2] == "''":
                    text += "''"
                    points.extend([[n, pos + 1], [n, pos + 2]])
                    pos += 2
                    continue
                q = not q
            elif ch == " " and not q:
                break
            text += ch
            points.append([n, pos + 1])
            pos += 1
        assert not q, "Quoted physical continuation was not observed in this frozen corpus"
    assert text == stmt["parameter_text"], (stmt, text)
    assert [text[a:b] for a, b in groups(text)] == stmt["parameters"]
    return text, points, operation_column


def dd_view(dd: dict[str, Any], regions: dict[int, dict[str, Any]]) -> dict[str, Any]:
    out = {"name": dd["name"], "line": dd["line"], "concat_head": dd["concat_head"],
           "concat_index": dd["concat_index"]}
    if dd["line"] in regions:
        data = regions[dd["line"]]
        out["inline_data"] = {"records": [data["lines"][0], data["lines"][-1]]
                              if data["lines"] else None, "terminator": data["terminator"]}
    return out


def build_file(file: dict[str, Any], corpus: Path) -> dict[str, Any]:
    raw = (corpus / file["path"]).read_bytes()
    assert digest(raw) == file["sha256"]
    physical = raw.decode("utf-8").splitlines(keepends=True)
    lines = [s.rstrip("\r\n") for s in physical]
    assert len(lines) == file["record_count"]
    regions = {r["dd_line"]: r for r in file["data_regions"]}
    heads = {s["line"]: s for s in file["statements"]}
    stmt_owner = {n: s["line"] for s in file["statements"] for n in s["lines"]}
    data_owner = {n: r["dd_line"] for r in file["data_regions"] for n in r["lines"]}
    data_owner.update({r["terminator_line"]: r["dd_line"] for r in file["data_regions"]
                       if r["terminator"] == "DELIMITER"})
    statements = []
    records = []
    source_specs = []
    offset = 0
    for role, line, physical_line in zip(file["roles"], lines, physical, strict=True):
        n = role["line"]
        encoded = physical_line.encode("utf-8")
        term = physical_line[len(line):]
        records.append({"line": n, "role": role["role"], "statement_line": stmt_owner.get(n),
                        "data_dd_line": data_owner.get(n), "byte_start": offset,
                        "byte_end": offset + len(encoded), "raw_sha256": digest(line.encode()),
                        "terminator": term})
        offset += len(encoded)
        if n in heads:
            s = heads[n]
            text, locations, opcol = parameter_source(s, lines)
            positional, keywords, sources = [], [], []
            for a, b in groups(text):
                part = text[a:b]
                if match := re.match(r"^([A-Z][A-Z0-9.]*)=(.*)$", part):
                    at = a + len(match[1]) + 1
                    v = value(text[at:b], locations[at:b]) if text[at:b] else None
                    keywords.append([match[1], v["view"] if v else None])
                    sources.append({"keyword": match[1], "line": locations[a][0],
                                    "column": locations[a][1], "value": v})
                else:
                    v = value(part, locations[a:b])
                    positional.append(v["view"])
                    sources.append({"keyword": None, "value": v})
            view = {"kind": s["operation"], "span": [n, max(s["lines"])], "name": s["name"],
                    "positional": positional, "keywords": keywords,
                    "comment": [c["text"] for c in s["comments"]] or None}
            if n in regions:
                r = regions[n]
                assert r["mode"] == "*"
                view["inline_data"] = {"records": [r["lines"][0], r["lines"][-1]]
                                       if r["lines"] else None,
                                       "terminator": r["terminator"],
                                       "delimiter": "/*" if r["terminator"] == "DELIMITER" else None}
            statements.append(view)
            source_specs.append({"line": n, "lines": s["lines"], "name": s["name"],
                                 "operation": s["operation"], "operation_column": opcol,
                                 "parameter_text": text, "parameters": sources,
                                 "tokens": lexical(text, locations)})
        elif role["role"] == "COMMENT":
            assert line.startswith("//*")
            statements.append({"kind": "COMMENT", "span": [n, n],
                               "comment": [line[3:80].strip(" ")]})
        elif role["role"] in ("NULL", "DELIMITER"):
            assert line.startswith("//") if role["role"] == "NULL" else line.startswith("/*")
            statements.append({"kind": role["role"], "span": [n, n]})
        else:
            assert role["role"] in ("DATA", "CONTINUATION")
    steps = [{"name": s["name"], "line": s["line"],
              "target": [s["target_kind"], s["target"]],
              "dds": [dd_view(d, regions) for d in s["dds"]]} for s in file["steps"]]
    hierarchy: dict[str, Any] = {"jobs": [], "outside": [],
                                "reachable_lines": sorted(heads)}
    if file["job"]:
        j = file["job"]
        hierarchy["jobs"] = [{"name": j["name"], "line": j["line"],
                              "span": [j["line"], len(lines)],
                              "dds": [dd_view(d, regions) for d in file["job_level_dds"]],
                              "steps": steps, "procedures": []}]
    else:
        header = next(s for s in file["statements"] if s["operation"] == "PROC")
        hierarchy.update(procedure_steps=steps,
                         procedure_header={"name": header["name"], "line": header["line"]})
    return {"path": file["path"], "sha256": file["sha256"], "encoding": "utf-8",
            "input_kind": "job" if file["job"] else "proc_member",
            "expected_structure": {"view": "statements", "statements": statements,
                                   "hierarchy": hierarchy},
            "trace": {"records": records, "statements": source_specs},
            "data_regions": file["data_regions"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.resolve().is_relative_to(args.corpus.resolve()), "Read-only corpus"
    assert not args.output.exists(), "Never overwrite an oracle; review any change separately"
    invpath = ROOT / "results/carddemo-contract-20261115/inventory.json"
    raw = invpath.read_bytes()
    inventory = json.loads(raw)
    files = [build_file(f, args.corpus) for f in inventory["files"]]
    assert len(files) == 48
    doc = {"schema_version": 1, "suite": "CD-1", "baseline_source_sha256": BASELINE,
           "provenance": {"inventory_path": invpath.relative_to(ROOT).as_posix(),
                          "inventory_sha256": digest(raw),
                          "author": "Codex, independent of Claude's Parser and Harness",
                          "method": "Frozen independent inventory, reconciled with original bytes; "
                                    "value/location oracle derived from source fields only",
                          "limitation": "Inventory, conversion, and CD checks share Codex authorship; "
                                        "no human approval is implied by generation",
                          "rule_ids": ["JCL-REC-001", "JCL-REC-002", "JCL-REC-003",
                                       "JCL-CONT-001", "JCL-DD-001", "JCL-DD-003", "JCL-DD-006",
                                       "JCL-PROC-002", "JCL-PROC-004"]},
           "counts": inventory["summary"], "files": files}
    data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.mkdir(parents=True)
    (args.output / "expectations.json").write_bytes(data)
    (args.output / "oracle-manifest.json").write_text(json.dumps(
        {"schema_version": 1, "expectations_sha256": digest(data)}, indent=2) + "\n",
        encoding="utf-8")
    (args.output / "reviews.json").write_text(json.dumps(
        {"schema_version": 1, "expectations_sha256": digest(data),
         "files": [{"path": f["path"], "status": "PENDING", "reviewed_by": None,
                    "reviewed_at": None} for f in files]}, indent=2) + "\n", encoding="utf-8")
    print(f"48 source-only expectations written; SHA-256 {digest(data)}; review PENDING")


if __name__ == "__main__":
    main()

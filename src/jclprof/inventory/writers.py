"""Inventory outputs: JSON, CSV, SQLite, Markdown (FR-12) plus volatile run_meta.json (ADR-007).

Files in DETERMINISTIC_FILES are byte-identical for identical input/config/version.
"""

from __future__ import annotations

import csv
import io
import json
import os
import platform
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jclprof import SCHEMA_VERSION, __version__
from jclprof.diagnostics import CODES
from jclprof.inventory.model import InventoryResult
from jclprof.inventory.physical import PREFIX_KEYS

DETERMINISTIC_FILES = (
    "inventory.json",
    "source_files.csv",
    "excluded.csv",
    "diagnostics.csv",
    "duplicate_members.csv",
    "inventory_report.md",
)

SOURCE_COLUMNS = (
    "source_id", "root_id", "rel_path", "top_dir", "asset_type", "classification_rule",
    "size_bytes", "sha256", "encoding", "encoding_basis", "encoding_status", "record_count",
    "line_terminator",
    "ends_with_terminator", "max_record_length", "records_over_80", "seq_area_records",
    *(f"prefix_{k}" for k in PREFIX_KEYS),
    "member_name", "member_name_valid",
)
DIAG_COLUMNS = ("diag_id", "code", "severity", "root_id", "rel_path", "source_id", "line",
                "column", "message", "remedy", "rule_id")
EXCL_COLUMNS = ("root_id", "rel_path", "rule_id", "reason")
DUP_COLUMNS = ("asset_type", "member_name", "identical_content", "rel_paths")


def _source_rows(res: InventoryResult) -> list[dict[str, Any]]:
    rows = []
    for s in res.source_files:
        p = s.physical
        row: dict[str, Any] = {
            "source_id": s.source_id, "root_id": s.root_id, "rel_path": s.rel_path,
            "top_dir": s.top_dir, "asset_type": s.asset_type,
            "classification_rule": s.classification_rule, "size_bytes": s.size_bytes,
            "sha256": s.sha256, "encoding": s.encoding, "encoding_basis": s.encoding_basis,
            "encoding_status": s.encoding_status,
            "record_count": p.record_count if p else None,
            "line_terminator": p.line_terminator if p else None,
            "ends_with_terminator": p.ends_with_terminator if p else None,
            "max_record_length": p.max_record_length if p else None,
            "records_over_80": p.records_over_80 if p else None,
            "seq_area_records": p.seq_area_records if p else None,
            "member_name": s.member_name, "member_name_valid": s.member_name_valid,
        }
        for k in PREFIX_KEYS:
            row[f"prefix_{k}"] = p.prefix_counts[k] if p else None
        rows.append(row)
    return rows


def _dup_rows(res: InventoryResult) -> list[dict[str, Any]]:
    return [{"asset_type": d.asset_type, "member_name": d.member_name,
             "identical_content": d.identical_content, "rel_paths": ";".join(d.rel_paths)}
            for d in res.duplicate_members]


def _csv_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(columns)
    for r in rows:
        w.writerow([_csv_value(r[c]) for c in columns])
    _write_text(path, buf.getvalue())


def _sql_value(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    return v


def _write_sqlite(path: Path, res: InventoryResult) -> None:
    tmp = path.with_suffix(".db.tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    try:
        def table(name: str, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
            cols = ", ".join(f'"{c}"' for c in columns)
            con.execute(f'CREATE TABLE "{name}" ({cols})')
            marks = ", ".join("?" for _ in columns)
            con.executemany(f'INSERT INTO "{name}" ({cols}) VALUES ({marks})',
                            [[_sql_value(r[c]) for c in columns] for r in rows])

        table("meta", ("key", "value"), [
            {"key": "schema_version", "value": str(SCHEMA_VERSION)},
            {"key": "tool_version", "value": __version__},
        ])
        table("roots", ("id", "path"), [{"id": r.id, "path": r.path} for r in res.roots])
        table("source_files", SOURCE_COLUMNS, _source_rows(res))
        table("excluded", EXCL_COLUMNS, [e.to_dict() for e in res.excluded])
        table("diagnostics", DIAG_COLUMNS, [d.to_dict() for d in res.diagnostics])
        table("duplicate_members", DUP_COLUMNS, _dup_rows(res))
        con.commit()
    finally:
        con.close()
    os.replace(tmp, path)


def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(_csv_value(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return out


def render_report(res: InventoryResult) -> str:
    s = res.summary()
    L: list[str] = ["# JCL Profiler — Asset Inventory", ""]
    L += [f"- Tool version: {__version__} / schema {SCHEMA_VERSION}"]
    L += [f"- Root `{r.id}`: `{r.path}`" for r in res.roots]
    L += [
        f"- Files seen: {s['files_seen']} (registered {s['files_registered']}, "
        f"excluded {s['files_excluded']})",
        f"- Total bytes: {s['total_bytes']}",
        f"- Diagnostics: {sum(s['diagnostic_counts'].values())} "
        f"({', '.join(f'{k}={v}' for k, v in s['severity_counts'].items()) or 'none'})",
        "",
        "## Asset types",
        "",
    ]
    L += _md_table(["Asset type", "Files"], [[k, v] for k, v in s["asset_type_counts"].items()])

    L += ["", "## Asset types by top-level directory", ""]
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for f in res.source_files:
        matrix[f.top_dir or "(root)"][f.asset_type] += 1
    types = sorted(s["asset_type_counts"])
    L += _md_table(["Top dir", *types, "Total"],
                   [[d, *[matrix[d][t] or "" for t in types], sum(matrix[d].values())]
                    for d in sorted(matrix)])

    L += ["", "## Encoding status", ""]
    L += _md_table(["Status", "Files"], [[k, v] for k, v in s["encoding_status_counts"].items()])

    L += ["", "## JCL-family physical records", "",
          "Record-prefix counts are physical facts, not JCL statement counts: records inside "
          "in-stream data can also begin with `//` (ADR-003). Statement-level inventory "
          "requires the Lexer/Parser (Step 4).", ""]
    jfam = [f for f in res.source_files if f.asset_type in ("JCL", "PROC") and f.physical]
    tot: Counter[str] = Counter()
    for f in jfam:
        assert f.physical is not None
        tot.update(f.physical.prefix_counts)
        tot["records"] += f.physical.record_count
        tot["seq_area"] += f.physical.seq_area_records
        tot["over_80"] += f.physical.records_over_80
    L += _md_table(
        ["Files", "Records", *PREFIX_KEYS, "Cols 73-80 used", ">80 cols"],
        [[len(jfam), tot["records"], *[tot[k] for k in PREFIX_KEYS], tot["seq_area"],
          tot["over_80"]]],
    )

    L += ["", "## Duplicate member names", ""]
    if res.duplicate_members:
        L += _md_table(["Asset type", "Member", "Identical", "Locations"],
                       [[d.asset_type, d.member_name, d.identical_content,
                         "<br>".join(d.rel_paths)] for d in res.duplicate_members])
    else:
        L.append("None.")

    L += ["", "## Excluded files", ""]
    if res.excluded:
        L += _md_table(["Root", "Path", "Rule", "Reason"],
                       [[e.root_id, e.rel_path, e.rule_id, e.reason] for e in res.excluded])
    else:
        L.append("None.")

    L += ["", "## Diagnostics by code", ""]
    if s["diagnostic_counts"]:
        L += _md_table(["Code", "Severity", "Count", "Meaning"],
                       [[k, CODES[k].severity, v, CODES[k].title]
                        for k, v in s["diagnostic_counts"].items()])
        L += ["", "## Diagnostics", ""]
        L += _md_table(["Code", "Location", "Message"],
                       [[d.code,
                         f"{d.root_id}:{d.rel_path}"
                         + (f":{d.line}" if d.line else "")
                         + (f":{d.column}" if d.column else ""),
                         d.message] for d in res.diagnostics])
    else:
        L.append("None.")
    return "\n".join(L) + "\n"


def write_outputs(res: InventoryResult, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_text(out_dir / "inventory.json",
                json.dumps(res.to_dict(), ensure_ascii=False, indent=2) + "\n")
    _write_csv(out_dir / "source_files.csv", SOURCE_COLUMNS, _source_rows(res))
    _write_csv(out_dir / "excluded.csv", EXCL_COLUMNS, [e.to_dict() for e in res.excluded])
    _write_csv(out_dir / "diagnostics.csv", DIAG_COLUMNS, [d.to_dict() for d in res.diagnostics])
    _write_csv(out_dir / "duplicate_members.csv", DUP_COLUMNS, _dup_rows(res))
    _write_text(out_dir / "inventory_report.md", render_report(res))
    _write_sqlite(out_dir / "inventory.db", res)
    return [out_dir / n for n in (*DETERMINISTIC_FILES, "inventory.db")]


def write_run_meta(out_dir: Path, extra: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta: dict[str, Any] = {
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "tool_version": __version__,
        "schema_version": SCHEMA_VERSION,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
    }
    meta.update(extra)
    path = out_dir / "run_meta.json"
    _write_text(path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    return path

"""Output writers (FR-12, ADR-007): JSON / CSV / SQLite / Markdown consistency and determinism."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

from conftest import make_config_dict, write_tree
from jclprof.context.config import config_from_dict
from jclprof.inventory.collector import collect
from jclprof.inventory.model import InventoryResult
from jclprof.inventory.writers import DETERMINISTIC_FILES, write_outputs, write_run_meta

FILES = {
    "jcl/JOBA.jcl": b"//JOBA JOB\r\n//* hi\r\n",
    "jcl/BAD.jcl": b"\xff\r\n",
    "proc/P1.prc": b"//P1 PROC\r\n",
    "misc/x.xyz": b"?\n",
    "a/D.jcl": b"d\n",
    "b/D.jcl": b"d\n",
}


def _result(tmp_path: Path) -> InventoryResult:
    root = tmp_path / "root"
    write_tree(root, FILES)
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    return collect(cfg)


def test_all_formats_written_and_consistent(tmp_path: Path) -> None:
    res = _result(tmp_path)
    out = tmp_path / "out"
    write_outputs(res, out)
    for name in DETERMINISTIC_FILES:
        assert (out / name).is_file(), name
    assert (out / "inventory.db").is_file()

    doc = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
    assert doc["schema_version"] == 1
    assert len(doc["source_files"]) == len(FILES)
    assert doc["summary"]["files_seen"] == len(FILES)

    with (out / "source_files.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(FILES)
    assert {"source_id", "root_id", "rel_path", "asset_type", "sha256", "encoding_status",
            "record_count", "member_name"} <= set(rows[0])
    assert [r["rel_path"] for r in rows] == [s.rel_path for s in res.source_files]

    with (out / "diagnostics.csv").open(encoding="utf-8", newline="") as f:
        drows = list(csv.DictReader(f))
    assert len(drows) == len(res.diagnostics)

    con = sqlite3.connect(out / "inventory.db")
    try:
        assert con.execute("select count(*) from source_files").fetchone()[0] == len(FILES)
        assert con.execute("select count(*) from diagnostics").fetchone()[0] == len(
            res.diagnostics
        )
        assert con.execute("select count(*) from duplicate_members").fetchone()[0] == 1
        assert con.execute("select count(*) from excluded").fetchone()[0] == 0
        row = con.execute(
            "select asset_type, encoding_status from source_files where rel_path='jcl/BAD.jcl'"
        ).fetchone()
        assert row == ("JCL", "DECODE_FAILED")
    finally:
        con.close()


def test_no_volatile_metadata_in_deterministic_outputs(tmp_path: Path) -> None:
    res = _result(tmp_path)
    out1, out2 = tmp_path / "o1", tmp_path / "o2"
    write_outputs(res, out1)
    write_outputs(_result(tmp_path), out2)
    for name in DETERMINISTIC_FILES:
        assert (out1 / name).read_bytes() == (out2 / name).read_bytes(), name
    text = (out1 / "inventory.json").read_text(encoding="utf-8")
    for volatile in ("generated_at", "started_at", "hostname", "elapsed"):
        assert volatile not in text


def test_sqlite_content_deterministic(tmp_path: Path) -> None:
    res = _result(tmp_path)
    dumps = []
    for d in ("o1", "o2"):
        write_outputs(res, tmp_path / d)
        con = sqlite3.connect(tmp_path / d / "inventory.db")
        dumps.append("\n".join(con.iterdump()))
        con.close()
    assert dumps[0] == dumps[1]


def test_rewrite_replaces_existing_db(tmp_path: Path) -> None:
    res = _result(tmp_path)
    out = tmp_path / "o"
    write_outputs(res, out)
    write_outputs(res, out)
    con = sqlite3.connect(out / "inventory.db")
    assert con.execute("select count(*) from source_files").fetchone()[0] == len(FILES)
    con.close()


def test_run_meta_separate(tmp_path: Path) -> None:
    out = tmp_path / "o"
    write_run_meta(out, {"command": "inventory", "elapsed_seconds": 0.1})
    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert "started_at" in meta and "tool_version" in meta and "python_version" in meta
    assert meta["command"] == "inventory"


def test_markdown_report(tmp_path: Path) -> None:
    res = _result(tmp_path)
    out = tmp_path / "o"
    write_outputs(res, out)
    md = (out / "inventory_report.md").read_text(encoding="utf-8")
    assert "# JCL Profiler — Asset Inventory" in md
    assert "| JCL | 4 |" in md  # jcl/JOBA, jcl/BAD, a/D, b/D
    assert "INV-W002" in md
    assert "INV-W003" in md
    # ADR-003: must warn that '//' record counts are not statement counts
    assert "not JCL statement counts" in md

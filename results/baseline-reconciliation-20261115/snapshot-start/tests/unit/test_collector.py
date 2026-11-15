"""Inventory collector (FR-01, CTX-01/02, ADR-003..006) on synthetic trees."""

from __future__ import annotations

import builtins
import hashlib
import io
import os
from pathlib import Path
from typing import Any

import pytest

from conftest import make_config_dict, snapshot, write_tree
from jclprof.context.config import config_from_dict
from jclprof.inventory import collector
from jclprof.inventory.collector import collect
from jclprof.inventory.model import InventoryResult, SourceFile


def _run(tmp_path: Path, files: dict[str, bytes], **cfg_kw: Any) -> InventoryResult:
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    write_tree(root, files)
    cfg = config_from_dict(make_config_dict([("r1", root)], **cfg_kw), base_dir=tmp_path)
    return collect(cfg)


def _by_path(res: InventoryResult) -> dict[str, SourceFile]:
    return {s.rel_path: s for s in res.source_files}


def _codes(res: InventoryResult, rel_path: str) -> list[str]:
    return sorted(d.code for d in res.diagnostics if d.rel_path == rel_path)


BASIC = {
    "jcl/JOBA.jcl": b"//JOBA JOB\r\n",
    "proc/P1.prc": b"//P1 PROC\r\n",
    "jcl/JOBB.JCL": b"//JOBB JOB\n",
    "cbl/PGM.cbl": b"       ID DIVISION.\n",
    "misc/notes.xyz": b"hello\n",
}


def test_basic_collection_order_types_hashes(tmp_path: Path) -> None:
    res = _run(tmp_path, BASIC)
    assert [s.rel_path for s in res.source_files] == [
        "cbl/PGM.cbl",
        "jcl/JOBA.jcl",
        "jcl/JOBB.JCL",
        "misc/notes.xyz",
        "proc/P1.prc",
    ]
    by = _by_path(res)
    assert by["jcl/JOBA.jcl"].asset_type == "JCL"
    assert by["jcl/JOBA.jcl"].classification_rule == "CLS-010"
    assert by["jcl/JOBB.JCL"].asset_type == "JCL"
    assert by["proc/P1.prc"].asset_type == "PROC"
    assert by["cbl/PGM.cbl"].asset_type == "COBOL"
    assert by["misc/notes.xyz"].asset_type == "UNKNOWN"
    assert by["misc/notes.xyz"].classification_rule is None
    assert _codes(res, "misc/notes.xyz") == ["INV-W001"]
    for rel, data in BASIC.items():
        assert by[rel].sha256 == hashlib.sha256(data).hexdigest()
        assert by[rel].size_bytes == len(data)
        assert by[rel].root_id == "r1"
        assert by[rel].encoding_status == "OK"
    assert by["jcl/JOBA.jcl"].top_dir == "jcl"


def test_member_names(tmp_path: Path) -> None:
    res = _run(tmp_path, BASIC)
    by = _by_path(res)
    assert by["jcl/JOBA.jcl"].member_name == "JOBA"
    assert by["jcl/JOBB.JCL"].member_name == "JOBB"
    assert by["proc/P1.prc"].member_name == "P1"
    assert by["misc/notes.xyz"].member_name is None
    assert by["misc/notes.xyz"].member_name_valid is None


def test_source_id_is_reproducible_from_root_and_path(tmp_path: Path) -> None:
    res = _run(tmp_path, BASIC)
    expected = "SRC-" + hashlib.sha256(b"r1\x00jcl/JOBA.jcl").hexdigest()[:16]
    assert _by_path(res)["jcl/JOBA.jcl"].source_id == expected


def test_decode_failure_is_diagnosed_with_location(tmp_path: Path) -> None:
    res = _run(tmp_path, {"jcl/BAD.jcl": b"OK\r\nA\xffB\r\n"})
    s = _by_path(res)["jcl/BAD.jcl"]
    assert s.encoding_status == "DECODE_FAILED"
    assert s.physical is None
    assert s.sha256 == hashlib.sha256(b"OK\r\nA\xffB\r\n").hexdigest()
    (d,) = [d for d in res.diagnostics if d.code == "INV-W002"]
    assert (d.line, d.column, d.severity) == (2, 2, "WARNING")


def test_explicit_encoding_override(tmp_path: Path) -> None:
    enc = {"default": "utf-8", "overrides": [{"pattern": "data/**", "encoding": "cp037"}]}
    res = _run(tmp_path, {"data/X.PS": b"\xc1\xc2\xc3\x25"}, encoding=enc)
    s = _by_path(res)["data/X.PS"]
    assert (s.encoding, s.encoding_status) == ("cp037", "OK")
    assert s.physical is not None
    assert (s.physical.record_count, s.physical.line_terminator) == (1, "LF")


def test_exclusion_is_recorded_not_dropped(tmp_path: Path) -> None:
    excl = [{"id": "EX-1", "pattern": "**/*.bak", "reason": "backup copy"}]
    res = _run(tmp_path, {"jcl/A.jcl": b"//A JOB\n", "jcl/A.jcl.bak": b"x"}, exclude=excl)
    assert [s.rel_path for s in res.source_files] == ["jcl/A.jcl"]
    assert [(e.rel_path, e.rule_id, e.reason) for e in res.excluded] == [
        ("jcl/A.jcl.bak", "EX-1", "backup copy")
    ]
    assert res.summary()["files_seen"] == 2


def test_duplicate_members(tmp_path: Path) -> None:
    res = _run(
        tmp_path,
        {
            "jcl/DUP.jcl": b"X\n",
            "alt/DUP.jcl": b"X\n",
            "alt2/dup.jcl": b"Y\n",
            "jcl/TRANREPT.jcl": b"//T JOB\n",
            "proc/TRANREPT.prc": b"//T PROC\n",
        },
    )
    assert len(res.duplicate_members) == 1
    dup = res.duplicate_members[0]
    assert (dup.asset_type, dup.member_name) == ("JCL", "DUP")
    assert dup.rel_paths == ("r1:alt/DUP.jcl", "r1:alt2/dup.jcl", "r1:jcl/DUP.jcl")
    assert dup.identical_content is False
    for p in ("alt/DUP.jcl", "alt2/dup.jcl", "jcl/DUP.jcl"):
        assert "INV-W003" in _codes(res, p)
    assert "INV-W003" not in _codes(res, "jcl/TRANREPT.jcl")


def test_identical_duplicate_flagged_identical(tmp_path: Path) -> None:
    res = _run(tmp_path, {"a/X.jcl": b"same\n", "b/X.jcl": b"same\n"})
    assert res.duplicate_members[0].identical_content is True


@pytest.mark.parametrize(
    ("filename", "member", "valid"),
    [
        ("TOOLONGNAME.jcl", "TOOLONGNAME", False),
        ("1ABC.jcl", "1ABC", False),
        ("@ABC.jcl", "@ABC", True),
        ("AB-C.jcl", "AB-C", False),
        ("abc.jcl", "ABC", True),
        ("ABCDEFGH.jcl", "ABCDEFGH", True),
    ],
)
def test_member_name_validity(tmp_path: Path, filename: str, member: str, valid: bool) -> None:
    rel = f"jcl/{filename}"
    res = _run(tmp_path, {rel: b"//X JOB\n"})
    s = _by_path(res)[rel]
    assert (s.member_name, s.member_name_valid) == (member, valid)
    assert ("INV-I001" in _codes(res, rel)) is (not valid)


def test_multiple_roots(tmp_path: Path) -> None:
    r1, r2 = tmp_path / "a", tmp_path / "b"
    write_tree(r1, {"jcl/A.jcl": b"1\n"})
    write_tree(r2, {"jcl/A.jcl": b"2\n"})
    cfg = config_from_dict(make_config_dict([("r1", r1), ("r2", r2)]), base_dir=tmp_path)
    res = collect(cfg)
    assert [(s.root_id, s.rel_path) for s in res.source_files] == [
        ("r1", "jcl/A.jcl"),
        ("r2", "jcl/A.jcl"),
    ]
    assert res.source_files[0].source_id != res.source_files[1].source_id
    assert res.duplicate_members[0].rel_paths == ("r1:jcl/A.jcl", "r2:jcl/A.jcl")


def test_too_large_is_hashed_not_decoded(tmp_path: Path) -> None:
    data = b"//X JOB\n" * 3
    res = _run(tmp_path, {"jcl/BIG.jcl": data}, limits={"max_decode_bytes": 10})
    s = _by_path(res)["jcl/BIG.jcl"]
    assert s.encoding_status == "SKIPPED_TOO_LARGE"
    assert s.sha256 == hashlib.sha256(data).hexdigest()
    assert s.physical is None
    assert _codes(res, "jcl/BIG.jcl") == ["INV-W004"]


def test_fixed_format_checks(tmp_path: Path) -> None:
    text = b"//A JOB\n" + b"X" * 81 + b"\n//B\tC\n"
    res = _run(tmp_path, {"jcl/F.jcl": text, "cbl/F.cbl": text})
    w = sorted(
        (d.code, d.line, d.column) for d in res.diagnostics if d.rel_path == "jcl/F.jcl"
    )
    # "//B\tC": '/'=1 '/'=2 'B'=3 TAB=4
    assert w == [("INV-W005", 2, 81), ("INV-W006", 3, 4)]
    # COBOL has no fixed_record_length in this config -> no column diagnostics
    assert _codes(res, "cbl/F.cbl") == []


def test_mixed_terminators_info(tmp_path: Path) -> None:
    res = _run(tmp_path, {"jcl/M.jcl": b"//A JOB\r\n//B\n"})
    assert _codes(res, "jcl/M.jcl") == ["INV-I003"]


def test_empty_file(tmp_path: Path) -> None:
    res = _run(tmp_path, {"jcl/EMPTY.jcl": b""})
    s = _by_path(res)["jcl/EMPTY.jcl"]
    assert s.encoding_status == "OK"
    assert s.physical is not None and s.physical.record_count == 0


def test_read_failure_continues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = collector.read_source_bytes

    def flaky(p: Path) -> bytes:
        if p.name == "LOCKED.jcl":
            raise PermissionError("denied")
        return real(p)

    monkeypatch.setattr(collector, "read_source_bytes", flaky)
    res = _run(tmp_path, {"jcl/LOCKED.jcl": b"x", "jcl/OK.jcl": b"//A JOB\n"})
    by = _by_path(res)
    assert by["jcl/LOCKED.jcl"].encoding_status == "READ_FAILED"
    assert by["jcl/LOCKED.jcl"].sha256 is None
    assert _codes(res, "jcl/LOCKED.jcl") == ["INV-E001"]
    assert by["jcl/OK.jcl"].encoding_status == "OK"
    assert res.has_errors() is True


def test_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "root"
    write_tree(root, BASIC)
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    assert collect(cfg).to_dict() == collect(cfg).to_dict()


def test_source_tree_is_never_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "root"
    write_tree(root, BASIC)
    before = snapshot(root)
    real_open = builtins.open
    root_str = str(root.resolve()).lower()

    def guarded_open(file: Any, mode: str = "r", *a: Any, **kw: Any) -> Any:
        if isinstance(file, (str, os.PathLike)):
            target = str(Path(file).resolve()).lower()
            if target.startswith(root_str) and any(c in mode for c in "wax+"):
                raise AssertionError(f"write attempted on source: {file} mode={mode}")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(io, "open", guarded_open)
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    collect(cfg)
    monkeypatch.undo()
    assert snapshot(root) == before


def test_symlink_not_followed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    write_tree(root, {"jcl/A.jcl": b"//A JOB\n"})
    try:
        os.symlink(root / "jcl" / "A.jcl", root / "jcl" / "L.jcl")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    res = collect(cfg)
    assert [s.rel_path for s in res.source_files] == ["jcl/A.jcl"]
    assert [(e.rel_path, e.rule_id) for e in res.excluded] == [("jcl/L.jcl", "SYMLINK")]


def test_summary_counts(tmp_path: Path) -> None:
    res = _run(tmp_path, BASIC)
    s = res.summary()
    assert s["files_seen"] == 5
    assert s["files_registered"] == 5
    assert s["files_excluded"] == 0
    assert s["asset_type_counts"] == {"COBOL": 1, "JCL": 2, "PROC": 1, "UNKNOWN": 1}
    assert s["encoding_status_counts"] == {"OK": 5}
    assert s["diagnostic_counts"] == {"INV-W001": 1}

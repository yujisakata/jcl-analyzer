"""ADR-009: encoding for JCL-family text and data files are configured separately.

Resolution order: encoding.overrides (first match) > asset type encoding_profile > encoding.default.
A profile or override value of null means "undetermined": the file is hashed but not decoded,
status ENCODING_UNDETERMINED, diagnostic INV-I004. Nothing is guessed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from conftest import make_config_dict, write_tree
from jclprof.context.config import ConfigError, config_from_dict
from jclprof.inventory.collector import collect
from jclprof.inventory.model import InventoryResult

EBCDIC_BYTES = b"\xc1\xc2\xc3\x25"


def _cfg(root: Path, tmp_path: Path, **enc: Any) -> Any:
    d = make_config_dict([("r1", root)])
    d["encoding"] = {"default": "utf-8", "profiles": {"jcl_text": "utf-8", "data": None},
                     "overrides": [], **enc}
    d["asset_types"]["JCL"]["encoding_profile"] = "jcl_text"
    d["asset_types"]["DATA"]["encoding_profile"] = "data"
    return config_from_dict(d, base_dir=tmp_path)


def _run(tmp_path: Path, **enc: Any) -> InventoryResult:
    root = tmp_path / "root"
    write_tree(root, {
        "jcl/A.jcl": b"//A JOB\r\n",
        "data/EBCDIC/X.PS": EBCDIC_BYTES,
        "data/ASCII/y.txt": b"abc\r\n",
        "cbl/P.cbl": b" X\n",
    })
    return collect(_cfg(root, tmp_path, **enc))


def test_profiles_resolve_per_asset_type(tmp_path: Path) -> None:
    res = _run(tmp_path)
    by = {s.rel_path: s for s in res.source_files}
    a = by["jcl/A.jcl"]
    assert (a.encoding, a.encoding_basis, a.encoding_status) == ("utf-8", "profile:jcl_text", "OK")
    x = by["data/EBCDIC/X.PS"]
    assert (x.encoding, x.encoding_basis, x.encoding_status) == (
        None, "profile:data", "ENCODING_UNDETERMINED")
    assert x.sha256 == hashlib.sha256(EBCDIC_BYTES).hexdigest()
    assert x.physical is None
    p = by["cbl/P.cbl"]
    assert (p.encoding, p.encoding_basis) == ("utf-8", "default")
    codes = sorted((d.rel_path, d.code) for d in res.diagnostics)
    assert codes == [("data/ASCII/y.txt", "INV-I004"), ("data/EBCDIC/X.PS", "INV-I004")]
    assert all(d.severity == "INFO" for d in res.diagnostics)


def test_override_beats_profile(tmp_path: Path) -> None:
    res = _run(tmp_path, overrides=[{"pattern": "data/ASCII/**", "encoding": "utf-8"}])
    y = {s.rel_path: s for s in res.source_files}["data/ASCII/y.txt"]
    assert (y.encoding, y.encoding_basis, y.encoding_status) == (
        "utf-8", "override:data/ASCII/**", "OK")


def test_override_can_mark_undetermined(tmp_path: Path) -> None:
    res = _run(tmp_path, overrides=[{"pattern": "jcl/**", "encoding": None}])
    a = {s.rel_path: s for s in res.source_files}["jcl/A.jcl"]
    assert a.encoding_status == "ENCODING_UNDETERMINED"
    assert a.encoding_basis == "override:jcl/**"


def test_explicit_ebcdic_override_decodes(tmp_path: Path) -> None:
    res = _run(tmp_path, overrides=[{"pattern": "data/EBCDIC/**", "encoding": "cp037"}])
    x = {s.rel_path: s for s in res.source_files}["data/EBCDIC/X.PS"]
    assert (x.encoding, x.encoding_status) == ("cp037", "OK")


def test_unknown_profile_reference_rejected(tmp_path: Path) -> None:
    d = make_config_dict([("r1", tmp_path)])
    d["asset_types"]["JCL"]["encoding_profile"] = "nope"
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)


def test_invalid_profile_encoding_rejected(tmp_path: Path) -> None:
    d = make_config_dict([("r1", tmp_path)])
    d["encoding"] = {"default": "utf-8", "profiles": {"x": "no-such-codec"}}
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)


def test_default_cannot_be_null(tmp_path: Path) -> None:
    d = make_config_dict([("r1", tmp_path)])
    d["encoding"] = {"default": None}
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)

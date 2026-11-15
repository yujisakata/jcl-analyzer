"""ADR-010: dataset name -> local folder mapping is explicit configuration only.

Nothing in the tool derives a physical path from a DSN. Unmapped DSNs stay unresolved (Step 5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import PROJECT_ROOT, make_config_dict
from jclprof.context.config import ConfigError, config_from_dict, load_config


def _cfg(tmp_path: Path, datasets: list[dict[str, Any]]) -> Any:
    d = make_config_dict([("r1", tmp_path)])
    d["datasets"] = datasets
    return config_from_dict(d, base_dir=tmp_path)


def test_valid_mapping(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, [{
        "dsn": "AWS.M2.CARDDEMO.PROC", "root": "r1", "path": "proc",
        "organization": "PDS", "member_suffixes": [".prc"],
        "aliases": {"ALIASP": "REPROC"}, "note": "confirmed by user",
    }])
    (m,) = cfg.datasets
    assert (m.dsn, m.root, m.path, m.organization) == ("AWS.M2.CARDDEMO.PROC", "r1", "proc", "PDS")
    assert m.member_suffixes == (".prc",)
    assert m.aliases == {"ALIASP": "REPROC"}
    assert cfg.dataset("AWS.M2.CARDDEMO.PROC") is m
    assert cfg.dataset("AWS.M2.CARDDEMO.OTHER") is None


@pytest.mark.parametrize(
    "bad",
    [
        {"dsn": "A.B", "root": "nope", "path": "proc", "organization": "PDS"},
        {"dsn": "a.b", "root": "r1", "path": "proc", "organization": "PDS"},
        {"dsn": "A.B", "root": "r1", "path": "../x", "organization": "PDS"},
        {"dsn": "A.B", "root": "r1", "path": "/abs", "organization": "PDS"},
        {"dsn": "A.B", "root": "r1", "path": "proc", "organization": "VSAM"},
        {"dsn": "A.B", "root": "r1", "path": "proc", "organization": "PDS", "colour": 1},
        {"dsn": "A.B", "root": "r1", "path": "p", "organization": "PDS",
         "aliases": {"bad": "X"}},
    ],
)
def test_invalid_mapping_rejected(tmp_path: Path, bad: dict[str, Any]) -> None:
    with pytest.raises(ConfigError):
        _cfg(tmp_path, [bad])


def test_duplicate_dsn_rejected(tmp_path: Path) -> None:
    e = {"dsn": "A.B", "root": "r1", "path": "proc", "organization": "PDS"}
    with pytest.raises(ConfigError):
        _cfg(tmp_path, [e, dict(e, path="other")])


def test_repository_config_has_no_unconfirmed_mapping() -> None:
    # Mappings are added only after explicit user confirmation (ADR-010).
    cfg = load_config(PROJECT_ROOT / "config" / "profiler.yaml")
    assert cfg.datasets == ()

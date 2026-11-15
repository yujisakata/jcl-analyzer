from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import PROJECT_ROOT, make_config_dict
from jclprof.context.config import (
    ConfigError,
    config_from_dict,
    load_config,
    validate_output_dir,
)


def test_repository_config_loads() -> None:
    cfg = load_config(PROJECT_ROOT / "config" / "profiler.yaml")
    assert [r.id for r in cfg.roots] == ["carddemo"]
    assert cfg.default_encoding == "utf-8"
    assert cfg.encoding_overrides == ()
    ids = [r.id for r in cfg.classification]
    assert ids[0] == "CLS-001"
    assert len(ids) == len(set(ids))
    assert "JCL" in cfg.asset_types
    assert cfg.asset_types["JCL"].member_like is True
    assert cfg.asset_types["JCL"].fixed_record_length == 80


def _bad(tmp_path: Path, **kw: Any) -> None:
    d = make_config_dict([("r1", tmp_path)], **kw)
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)


def test_unknown_asset_type_in_rule(tmp_path: Path) -> None:
    _bad(tmp_path, classification=[{"id": "X", "pattern": "*", "asset_type": "NOPE"}])


def test_duplicate_rule_id(tmp_path: Path) -> None:
    rule = {"id": "X", "pattern": "*", "asset_type": "JCL"}
    _bad(tmp_path, classification=[rule, dict(rule)])


def test_missing_roots(tmp_path: Path) -> None:
    d = make_config_dict([])
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)


def test_duplicate_root_id(tmp_path: Path) -> None:
    d = make_config_dict([("r1", tmp_path), ("r1", tmp_path / "x")])
    with pytest.raises(ConfigError):
        config_from_dict(d, base_dir=tmp_path)


def test_wrong_version(tmp_path: Path) -> None:
    _bad(tmp_path, version=2)


def test_unknown_top_level_key(tmp_path: Path) -> None:
    _bad(tmp_path, colour="blue")


def test_invalid_encoding(tmp_path: Path) -> None:
    _bad(tmp_path, encoding={"default": "no-such-codec", "overrides": []})


def test_invalid_override_encoding(tmp_path: Path) -> None:
    _bad(
        tmp_path,
        encoding={"default": "utf-8", "overrides": [{"pattern": "**", "encoding": "nope"}]},
    )


def test_exclude_requires_id_and_reason(tmp_path: Path) -> None:
    _bad(tmp_path, exclude=[{"pattern": "**/*.bak"}])


def test_relative_root_resolved_against_base_dir(tmp_path: Path) -> None:
    d = make_config_dict([("r1", Path("corpus"))])
    cfg = config_from_dict(d, base_dir=tmp_path)
    assert cfg.roots[0].path == (tmp_path / "corpus").resolve()


def test_output_dir_inside_root_rejected(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    with pytest.raises(ConfigError):
        validate_output_dir(cfg, root / "results")
    with pytest.raises(ConfigError):
        validate_output_dir(cfg, root)
    validate_output_dir(cfg, tmp_path / "results")  # sibling: allowed


# ---- ADR-021 (user decision A2): JES type in the Environment Profile, default UNKNOWN
def test_jes_defaults_to_unknown(tmp_path: Path) -> None:
    cfg = config_from_dict(make_config_dict([("r1", tmp_path)]), base_dir=tmp_path)
    assert cfg.jes == "UNKNOWN"


@pytest.mark.parametrize("jes", ["JES2", "JES3", "UNKNOWN"])
def test_jes_explicit(tmp_path: Path, jes: str) -> None:
    d = make_config_dict([("r1", tmp_path)], environment={"jes": jes})
    assert config_from_dict(d, base_dir=tmp_path).jes == jes


def test_jes_invalid(tmp_path: Path) -> None:
    _bad(tmp_path, environment={"jes": "JES4"})
    _bad(tmp_path, environment={"jes": "JES2", "colour": 1})


def test_repository_config_jes_unknown() -> None:
    assert load_config(PROJECT_ROOT / "config" / "profiler.yaml").jes == "UNKNOWN"

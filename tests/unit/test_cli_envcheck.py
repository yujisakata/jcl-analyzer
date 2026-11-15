"""CLI exit codes (ADR-008) and environment check (Step 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import make_config_dict, snapshot, write_tree
from jclprof import cli
from jclprof.context.config import config_from_dict
from jclprof.envcheck import run_envcheck
from jclprof.inventory import collector


def _cfg_file(tmp_path: Path, root: Path) -> Path:
    p = tmp_path / "profiler.yaml"
    p.write_text(yaml.safe_dump(make_config_dict([("r1", root)])), encoding="utf-8")
    return p


@pytest.fixture
def root(tmp_path: Path) -> Path:
    r = tmp_path / "corpus"
    write_tree(r, {"jcl/A.jcl": b"//A JOB\r\n", "proc/P.prc": b"//P PROC\r\n", "x.cbl": b" \n"})
    return r


def test_inventory_success(tmp_path: Path, root: Path) -> None:
    out = tmp_path / "results"
    rc = cli.main(["inventory", "--config", str(_cfg_file(tmp_path, root)), "--output", str(out)])
    assert rc == 0
    assert (out / "inventory.json").is_file()
    assert (out / "run_meta.json").is_file()


def test_inventory_output_inside_root_refused(tmp_path: Path, root: Path) -> None:
    before = snapshot(root)
    rc = cli.main(
        ["inventory", "--config", str(_cfg_file(tmp_path, root)), "--output", str(root / "out")]
    )
    assert rc == 2
    assert snapshot(root) == before
    assert not (root / "out").exists()


def test_inventory_missing_config(tmp_path: Path) -> None:
    rc = cli.main(["inventory", "--config", str(tmp_path / "nope.yaml"), "--output", "x"])
    assert rc == 2


def test_inventory_missing_root(tmp_path: Path) -> None:
    rc = cli.main(
        [
            "inventory",
            "--config",
            str(_cfg_file(tmp_path, tmp_path / "missing")),
            "--output",
            str(tmp_path / "o"),
        ]
    )
    assert rc == 2


def test_inventory_with_read_error_returns_1(
    tmp_path: Path, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(p: Path) -> bytes:
        raise PermissionError("denied")

    monkeypatch.setattr(collector, "read_source_bytes", fail)
    rc = cli.main(
        ["inventory", "--config", str(_cfg_file(tmp_path, root)), "--output", str(tmp_path / "o")]
    )
    assert rc == 1


def test_unknown_command() -> None:
    with pytest.raises(SystemExit) as e:
        cli.main(["frobnicate"])
    assert e.value.code == 2


def test_envcheck_report(tmp_path: Path, root: Path) -> None:
    before = snapshot(root)
    cfg = config_from_dict(make_config_dict([("r1", root)]), base_dir=tmp_path)
    rep = run_envcheck(cfg)
    assert rep["python"]["version"].startswith("3.12.")
    assert rep["python"]["ok"] is True
    for pkg in ("PyYAML", "pytest", "hypothesis", "ruff", "mypy"):
        assert rep["packages"][pkg]["installed"] is True, pkg
    (r,) = rep["roots"]
    assert r["exists"] is True and r["is_dir"] is True
    assert r["file_count"] == 3
    assert r["readable_count"] == 3
    assert r["unreadable"] == []
    assert r["total_bytes"] == 9 + 10 + 2
    assert rep["ok"] is True
    assert snapshot(root) == before


def test_envcheck_missing_root(tmp_path: Path) -> None:
    cfg = config_from_dict(make_config_dict([("r1", tmp_path / "missing")]), base_dir=tmp_path)
    rep = run_envcheck(cfg)
    assert rep["roots"][0]["exists"] is False
    assert rep["ok"] is False


def test_envcheck_cli(tmp_path: Path, root: Path) -> None:
    out = tmp_path / "env"
    rc = cli.main(["envcheck", "--config", str(_cfg_file(tmp_path, root)), "--output", str(out)])
    assert rc == 0
    rep = json.loads((out / "envcheck.json").read_text(encoding="utf-8"))
    assert rep["ok"] is True
    rc2 = cli.main(
        ["envcheck", "--config", str(_cfg_file(tmp_path, tmp_path / "missing"))]
    )
    assert rc2 == 1

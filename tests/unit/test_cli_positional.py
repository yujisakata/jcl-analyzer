"""ADR-013: positional analysis targets on the CLI, with the config file still supported.

Precedence (tested here):
1. Positional PATHs, when given, replace config ``roots`` entirely; all other config sections
   (classification, encoding, datasets, ...) still come from the config file.
2. A positional PATH that resolves to the same directory as a config root reuses that root's id
   (so source ids stay stable); otherwise its id is ``arg<N>`` (1-based argument position).
3. Without positional PATHs, config ``roots`` are used.
4. ``--config`` defaults to ``config/profiler.yaml`` relative to the current directory.
Duplicate, missing or output-overlapping positional PATHs -> exit code 2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import make_config_dict, write_tree
from jclprof import cli


@pytest.fixture
def env(tmp_path: Path) -> dict[str, Path]:
    cfg_root = tmp_path / "cfgroot"
    other = tmp_path / "other"
    other2 = tmp_path / "other2"
    write_tree(cfg_root, {"jcl/C.jcl": b"//C JOB\n"})
    write_tree(other, {"jcl/O.jcl": b"//O JOB\n"})
    write_tree(other2, {"jcl/Q.jcl": b"//Q JOB\n"})
    cfg = tmp_path / "profiler.yaml"
    cfg.write_text(yaml.safe_dump(make_config_dict([("main", cfg_root)])), encoding="utf-8")
    return {"cfg": cfg, "cfg_root": cfg_root, "other": other, "other2": other2,
            "out": tmp_path / "out"}


def _roots_and_paths(out: Path) -> tuple[list[str], list[tuple[str, str]]]:
    inv: Any = json.loads((out / "inventory.json").read_text(encoding="utf-8"))
    roots = [r["id"] for r in inv["roots"]]
    files = [(s["root_id"], s["rel_path"]) for s in inv["source_files"]]
    return roots, files


def test_config_roots_used_without_positional(env: dict[str, Path]) -> None:
    rc = cli.main(["inventory", "--config", str(env["cfg"]), "--output", str(env["out"])])
    assert rc == 0
    assert _roots_and_paths(env["out"]) == (["main"], [("main", "jcl/C.jcl")])


def test_positional_replaces_config_roots(env: dict[str, Path]) -> None:
    rc = cli.main(["inventory", str(env["other"]), "--config", str(env["cfg"]),
                   "--output", str(env["out"])])
    assert rc == 0
    assert _roots_and_paths(env["out"]) == (["arg1"], [("arg1", "jcl/O.jcl")])


def test_positional_matching_config_root_reuses_id(env: dict[str, Path]) -> None:
    rc = cli.main(["inventory", str(env["cfg_root"]), str(env["other"]),
                   "--config", str(env["cfg"]), "--output", str(env["out"])])
    assert rc == 0
    assert _roots_and_paths(env["out"]) == (
        ["main", "arg2"], [("main", "jcl/C.jcl"), ("arg2", "jcl/O.jcl")])


def test_multiple_positional_in_argument_order(env: dict[str, Path]) -> None:
    rc = cli.main(["inventory", str(env["other2"]), str(env["other"]),
                   "--config", str(env["cfg"]), "--output", str(env["out"])])
    assert rc == 0
    assert _roots_and_paths(env["out"])[0] == ["arg1", "arg2"]


def test_duplicate_positional_rejected(env: dict[str, Path]) -> None:
    p = str(env["other"])
    rc = cli.main(["inventory", p, p, "--config", str(env["cfg"]), "--output", str(env["out"])])
    assert rc == 2
    assert not env["out"].exists()


def test_missing_positional_rejected(env: dict[str, Path], tmp_path: Path) -> None:
    rc = cli.main(["inventory", str(tmp_path / "missing"), "--config", str(env["cfg"]),
                   "--output", str(env["out"])])
    assert rc == 2


def test_output_inside_positional_root_rejected(env: dict[str, Path]) -> None:
    rc = cli.main(["inventory", str(env["other"]), "--config", str(env["cfg"]),
                   "--output", str(env["other"] / "out")])
    assert rc == 2
    assert not (env["other"] / "out").exists()


def test_default_config_path(env: dict[str, Path], tmp_path: Path,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "profiler.yaml").write_text(
        env["cfg"].read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["inventory", str(env["other"]), "--output", str(env["out"])])
    assert rc == 0
    assert _roots_and_paths(env["out"])[0] == ["arg1"]


def test_default_config_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["inventory", str(tmp_path), "--output", str(tmp_path / "o")])
    assert rc == 2


def test_run_meta_records_root_source(env: dict[str, Path]) -> None:
    cli.main(["inventory", str(env["other"]), "--config", str(env["cfg"]),
              "--output", str(env["out"])])
    meta = json.loads((env["out"] / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["roots_source"] == "positional"


def test_envcheck_accepts_positional(env: dict[str, Path], tmp_path: Path) -> None:
    rc = cli.main(["envcheck", str(env["other"]), "--config", str(env["cfg"]),
                   "--output", str(tmp_path / "env")])
    assert rc == 0
    rep = json.loads((tmp_path / "env" / "envcheck.json").read_text(encoding="utf-8"))
    assert [r["id"] for r in rep["roots"]] == ["arg1"]

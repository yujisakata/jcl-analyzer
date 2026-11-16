"""CD-4R F09: run manifest ties resolver outputs to code, inputs, contexts and environment.

Regenerates the CardDemo resolver outputs into tmp directories (the committed results/resolve is
not touched), checks that two runs give byte-identical outputs, that every hash in the manifest
matches what is on disk, and that tampering with an output or a recorded hash is detected.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

from conftest import PROJECT_ROOT
from jclprof.resolver.manifest import repo_hash, sha256_file, verify_manifest

pytestmark = pytest.mark.corpus

ORACLE = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                        .read_text(encoding="utf-8"))
REPROC_SHA = ORACLE["jcl_family_files"]["proc/REPROC.prc"]["sha256"]
TRANREPT_SHA = ORACLE["jcl_family_files"]["proc/TRANREPT.prc"]["sha256"]


def _tool() -> ModuleType:
    path = PROJECT_ROOT / "tools" / "cd4_resolve_report.py"
    spec = importlib.util.spec_from_file_location("cd4_resolve_report", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, dict[str, Any]]:
    tool = _tool()
    try:
        a = tool.main(tmp_path_factory.mktemp("run_a"))
        b = tool.main(tmp_path_factory.mktemp("run_b"))
    except FileNotFoundError as exc:  # pragma: no cover - corpus absent
        pytest.skip(f"CardDemo corpus not available: {exc}")
    return a, b, json.loads(a.read_text(encoding="utf-8"))


def test_outputs_are_reproducible_and_lf(runs: tuple[Path, Path, dict[str, Any]]) -> None:
    a, b, m = runs
    for out in m["outputs"]:
        name = Path(out["path"]).relative_to(a.parent).as_posix()
        pa, pb = a.parent / name, b.parent / name
        assert sha256_file(pa) == sha256_file(pb) == out["sha256"], name
        assert b"\r\n" not in pa.read_bytes(), name


def test_manifest_hashes_match_disk(runs: tuple[Path, Path, dict[str, Any]]) -> None:
    _, _, m = runs
    assert verify_manifest(m, PROJECT_ROOT) == []


def test_manifest_content(runs: tuple[Path, Path, dict[str, Any]]) -> None:
    _, _, m = runs
    code = m["code"]
    assert code["git_commit"] is None or re.fullmatch(r"[0-9a-f]{40}", code["git_commit"])
    assert "src/jclprof/resolver/resolver.py" in code["src_files"]
    assert code["generator"]["path"] == "tools/cd4_resolve_report.py"
    env = m["environment"]
    assert (env["encoding"], env["jes"]) == ("utf-8", "UNKNOWN") and env["python"]
    inp = m["inputs"]
    assert len(inp["files"]) == 48
    assert {x["path"]: x["sha256"] for x in inp["files"]} == {
        f: v["sha256"] for f, v in ORACLE["jcl_family_files"].items()}
    assert {x["path"]: x["sha256"] for x in inp["members_read"]} == {
        "proc/REPROC.prc": REPROC_SHA}  # TRANREPT.prc is an input, not a called member
    assert TRANREPT_SHA in {x["sha256"] for x in inp["files"]}
    ctxs = m["contexts"]
    assert ctxs["official"]["file"] == "config/profiler.yaml"
    assert ctxs["official"]["mappings"] == [] and ctxs["official"]["basis"] == "CONFIG"
    assert ctxs["contract"]["file"] == "config/contexts/cd4-contract-context.yaml"
    assert ctxs["contract"]["basis"] == "UNCONFIRMED_CONTRACT_CONTEXT"
    assert [x["dsn"] for x in ctxs["contract"]["mappings"]] == ["AWS.M2.CARDDEMO.PROC"]
    for c in ctxs.values():  # TC-022: hash method per file (raw for -text files, else LF)
        assert c["sha256"] == repo_hash(PROJECT_ROOT / c["file"], c["file"])
    assert (ctxs["official"]["sha256_method"], ctxs["contract"]["sha256_method"]) == ("lf", "raw")
    counts = m["counts"]
    assert counts["official"]["jobs_46"] == {"program_steps": 116, "unresolved_call_steps": 3,
                                             "dds": 474, "job_level_dds": 3}
    assert counts["contract"]["jobs_46"] == {"program_steps": 119, "unresolved_call_steps": 0,
                                             "dds": 486, "job_level_dds": 3}
    assert counts["official"]["unsupported_forms"] == counts["contract"]["unsupported_forms"] == 0


def test_tampering_is_detected(runs: tuple[Path, Path, dict[str, Any]], tmp_path: Path) -> None:
    _, _, m = runs
    copy = json.loads(json.dumps(m))
    copy["contexts"]["contract"]["sha256"] = "0" * 64
    copy["inputs"]["files"][0]["sha256"] = "1" * 64
    problems = verify_manifest(copy, PROJECT_ROOT)
    assert any(p.startswith("context contract") for p in problems)
    assert any(p.startswith("input") for p in problems)
    # an edited output no longer matches
    target = Path(m["outputs"][-1]["path"])
    edited = tmp_path / "report.md"
    edited.write_bytes(target.read_bytes() + b"tampered\n")
    copy2 = json.loads(json.dumps(m))
    copy2["outputs"] = [dict(m["outputs"][-1], path=str(edited))]
    assert any(p.startswith("output") for p in verify_manifest(copy2, PROJECT_ROOT))


def test_code_identity_ignores_line_endings(tmp_path: Path) -> None:
    from jclprof.resolver.manifest import sha256_text_lf
    lf, crlf = tmp_path / "lf.py", tmp_path / "crlf.py"
    lf.write_bytes(b"a = 1\nb = 2\n")
    crlf.write_bytes(b"a = 1\r\nb = 2\r\n")
    assert sha256_text_lf(lf) == sha256_text_lf(crlf)
    assert sha256_file(lf) != sha256_file(crlf)

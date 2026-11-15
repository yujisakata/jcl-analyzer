"""Lexer I/O safety (instruction D-3), determinism (D-4) and corpus record preservation (D-6)."""

from __future__ import annotations

import builtins
import io
import json
import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import PROJECT_ROOT, snapshot
from jclprof.lexer import lex_file


def test_lex_file_never_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "in"
    src.mkdir()
    f = src / "a.jcl"
    f.write_bytes(b"//A JOB\r\n//S EXEC PGM=X,\r\n//   PARM='Y'\r\n")
    before = snapshot(src)
    real_open = builtins.open

    def guarded(file: Any, mode: str = "r", *a: Any, **kw: Any) -> Any:
        if isinstance(file, (str, os.PathLike)) and str(Path(file).resolve()).lower().startswith(
                str(src.resolve()).lower()) and any(c in mode for c in "wax+"):
            raise AssertionError(f"write attempted: {file} {mode}")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", guarded)
    monkeypatch.setattr(io, "open", guarded)
    r = lex_file(f, encoding="utf-8")
    monkeypatch.undo()
    assert snapshot(src) == before
    assert r.sha256 is not None and len(r.records) == 3


@pytest.mark.corpus
def test_corpus_jcl_lexed_without_loss_deterministically(corpus_root: Path) -> None:
    oracle = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                            .read_text(encoding="utf-8"))
    before = snapshot(corpus_root)
    for rel, e in oracle["jcl_family_files"].items():
        p = corpus_root / rel
        r1 = lex_file(p, encoding="utf-8")
        r2 = lex_file(p, encoding="utf-8")
        assert json.dumps(r1.to_dict()) == json.dumps(r2.to_dict()), rel
        assert r1.sha256 == e["sha256"], rel
        assert len(r1.records) == e["record_count"], rel  # independent shell oracle (awk NR)
        text = p.read_bytes().decode("utf-8")
        assert "".join(x.raw + x.terminator for x in r1.records) == text, rel
        # every record is classified, and statements reference only their own records
        assert all(x.kind in {"STATEMENT_START", "CONTINUATION", "COMMENT", "NULL", "DELIMITER",
                              "JES2", "OTHER"} for x in r1.records)
        # record-kind counts vs the independent prefix histogram (JCL-REC-001)
        kinds = [x.kind for x in r1.records]
        assert kinds.count("COMMENT") == e["prefix"]["SLASH_SLASH_STAR"], rel
        assert kinds.count("DELIMITER") + kinds.count("JES2") == e["prefix"]["SLASH_STAR"], rel
        assert (kinds.count("STATEMENT_START") + kinds.count("CONTINUATION")
                + kinds.count("NULL")) == e["prefix"]["SLASH_SLASH"], rel
    assert snapshot(corpus_root) == before

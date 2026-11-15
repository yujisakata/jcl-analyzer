"""Parser on all 48 CardDemo JCL/PROC files: no record lost, trace-back, determinism, read-only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import PROJECT_ROOT, snapshot
from jclprof.harness.trace import check_trace
from jclprof.parser import parse_file

pytestmark = pytest.mark.corpus


def _kind(rel: str) -> str:
    return "proc_member" if rel.lower().endswith((".prc", ".proc")) else "job"


def test_corpus_parse_trace_and_determinism(corpus_root: Path) -> None:
    oracle = yaml.safe_load((PROJECT_ROOT / "tests/acceptance/expected/carddemo_inventory.yaml")
                            .read_text(encoding="utf-8"))
    before = snapshot(corpus_root)
    for rel, e in oracle["jcl_family_files"].items():
        p = corpus_root / rel
        r = parse_file(p, encoding="utf-8", input_kind=_kind(rel))
        assert r.lex.sha256 == e["sha256"], rel
        assert len(r.records) == e["record_count"], rel
        text = p.read_bytes().decode("utf-8")
        check_trace(r, text)
        again = parse_file(p, encoding="utf-8", input_kind=_kind(rel))
        assert json.dumps(r.to_dict()) == json.dumps(again.to_dict()), rel
        # lexical statements dropped by the parser must lie entirely inside data regions
        data = {rr.line for rr in r.records if rr.role in ("DATA", "DELIMITER", "UNDETERMINED")}
        for i in r.dropped_lex_statements:
            assert r.lex.statements[i].span[0] in data, (rel, i)
    assert snapshot(corpus_root) == before

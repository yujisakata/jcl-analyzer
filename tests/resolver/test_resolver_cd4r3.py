"""CD-4R3 (N01, docs/reviews/cd4r2-independent-final-audit.md): DSN and DSNAME on one DD statement.

A procedure call whose called procedure or caller codes both spellings on a single DD statement
is UNSUPPORTED (U-OVR-DSN-DUPLICATE) and not expanded, on all four paths:
1. a procedure DD that is overridden        2. a procedure DD that is not overridden
3. a caller override of an existing DD      4. a caller DD added to a procedure step
Inputs are written by the implementer, independently of the Codex audit fixtures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jclprof.context.config import DatasetMapping
from jclprof.resolver import LibraryContext, Resolver


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _resolve(tmp: Path, proc: str, text: str) -> Any:
    root = tmp / "root"
    (root / "lib").mkdir(parents=True)
    (root / "lib" / "PX.prc").write_text(proc, encoding="utf-8")
    job = root / "jcl" / "J.jcl"
    job.parent.mkdir(parents=True)
    job.write_text(text, encoding="utf-8")
    ctx = LibraryContext((DatasetMapping("T.LIB", "r", "lib", "PDS", (".prc",), {}),),
                         {"r": root}, "TEST", "cd4r3")
    return Resolver(ctx).resolve_file(job, "jcl/J.jcl", "r")


CALL = ("//J JOB", "//L JCLLIB ORDER=(T.LIB)", "//C EXEC PX")
NORMAL = J("//PX PROC", "//S1 EXEC PGM=IEFBR14", "//D1 DD DISP=SHR,DSN=BASE.NAME,UNIT=3390",
           "// PEND")
BOTH = NORMAL.replace("DSN=BASE.NAME", "DSN=BASE.NAME,DSNAME=OTHER.NAME")

# path -> (procedure, caller statements after the call, (file, line) of the duplicate DD)
PATHS: dict[str, tuple[str, tuple[str, ...], tuple[str, int]]] = {
    "proc-dd-overridden": (BOTH, ("//S1.D1 DD DSN=NEW.NAME",), ("lib/PX.prc", 3)),
    "proc-dd-not-overridden": (BOTH, (), ("lib/PX.prc", 3)),
    "caller-override": (NORMAL, ("//S1.D1 DD DSN=A.NAME,DSNAME=B.NAME",), ("jcl/J.jcl", 4)),
    "caller-added-dd": (NORMAL, ("//S1.NEW DD DSN=FIRST,DSNAME=SECOND",), ("jcl/J.jcl", 4)),
}


@pytest.mark.parametrize("path", sorted(PATHS))
def test_n01_duplicate_spelling_stops_the_call(tmp_path: Path, path: str) -> None:
    proc, extra, (file, line) = PATHS[path]
    res = _resolve(tmp_path, proc, J(*CALL, *extra))
    (c,) = res.calls
    assert c.status == "UNSUPPORTED"
    assert "UNSUPPORTED:U-OVR-DSN-DUPLICATE" in c.reasons
    counts = res.counts()
    assert (counts["program_steps"], counts["unresolved_call_steps"]) == (0, 1)
    assert not [s for j in res.jobs for s in j.steps if c.id in s.call_chain]
    (u,) = [u for u in res.unsupported if u.form == "U-OVR-DSN-DUPLICATE"]
    assert u.call_id == c.id
    assert (u.source.file, u.source.line) == (file, line)  # the statement in the original
    assert u.source.sha256 and u.source.statement_id is not None
    assert any("[U-OVR-DSN-DUPLICATE]" in d.message for d in res.diagnostics
               if d.code == "RES-W004")


def test_n01_control_without_duplicate_resolves(tmp_path: Path) -> None:
    res = _resolve(tmp_path, NORMAL, J(*CALL, "//S1.NEW DD DSN=FIRST,DISP=SHR"))
    assert [c.status for c in res.calls] == ["RESOLVED"] and res.unsupported == ()
    assert res.counts()["program_steps"] == 1

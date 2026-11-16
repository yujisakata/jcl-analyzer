"""CD-4R: library-environment counterexamples for audit findings F01 and F02.

Written by the implementer before the fix, from the contract (CA-04: never pick from an uncertain
or contradictory search basis; POL-005) and JCL-PROC-003 (JCLLIB ORDER is searched in order).
The inputs are minimal and synthetic, built independently of the Codex audit fixtures. Only the
public API (LibraryContext, load_library_context, Resolver) is used, so the same file runs against
the code before the fix (where the F01/F02 cases are expected to fail).

F01: an earlier library whose local folder cannot be inspected (missing, a regular file, listing
     fails, or the root id is unknown) must not count as "member not found". The call must not
     become RESOLVED from a later library. An existing empty folder is different: it is a known
     NOT_FOUND, and the search correctly continues to the next library.
F02: two mappings for the same DSN must never resolve silently to the first one, in either order,
     through the dataclass or through the public YAML / JSON loader.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from jclprof.context.config import ConfigError, DatasetMapping, config_from_dict
from jclprof.resolver import LibraryContext, Resolver, load_library_context

MEMBER_1 = "//P1 PROC\n//ONE EXEC PGM=PGMONE\n//DD1 DD DSN=X.ONE,DISP=SHR\n// PEND\n"
MEMBER_2 = "//P1 PROC\n//TWO EXEC PGM=PGMTWO\n//DD1 DD DSN=X.TWO,DISP=SHR\n// PEND\n"
CALL_AB = "//JOBX JOB\n//LIBS JCLLIB ORDER=(LIB.FIRST,LIB.SECOND)\n//RUN EXEC PROC=P1\n"
CALL_A = "//JOBX JOB\n//LIBS JCLLIB ORDER=(LIB.FIRST)\n//RUN EXEC PROC=P1\n"


def _m(dsn: str, folder: str, root: str = "r") -> DatasetMapping:
    return DatasetMapping(dsn, root, folder, "PDS", (".prc",), {})


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _run(tmp: Path, ctx: LibraryContext, text: str) -> Any:
    _write(tmp / "root", "jcl/JOBX.jcl", text)
    return Resolver(ctx).resolve_file(tmp / "root" / "jcl/JOBX.jcl", "jcl/JOBX.jcl", "r")


def _ctx(tmp: Path, *maps: DatasetMapping, roots: dict[str, Path] | None = None) -> LibraryContext:
    return LibraryContext(tuple(maps), roots or {"r": tmp / "root"}, "TEST", "cd4r")


def _second_has_member(tmp: Path) -> None:
    _write(tmp / "root", "second/P1.prc", MEMBER_2)


# ------------------------------------------------------------------------------------- F01
def _first_missing(tmp: Path) -> None:
    pass  # LIB.FIRST -> root/first does not exist


def _first_is_file(tmp: Path) -> None:
    _write(tmp / "root", "first", "this is a regular file, not a library folder\n")


@pytest.mark.parametrize("prepare", [_first_missing, _first_is_file], ids=["missing", "file"])
def test_f01_uninspectable_earlier_library_blocks_resolution(tmp_path: Path, prepare: Any) -> None:
    prepare(tmp_path)
    _second_has_member(tmp_path)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", "first"), _m("LIB.SECOND", "second"))
    res = _run(tmp_path, ctx, CALL_AB)
    (c,) = res.calls
    assert c.status != "RESOLVED", "picked LIB.SECOND although LIB.FIRST could not be inspected"
    assert c.status == "ENVIRONMENT_GAP"
    assert c.member_path is None
    first = c.search[0]
    assert (first.library, first.result) == ("LIB.FIRST", "UNAVAILABLE")
    assert res.jobs[0].steps[0].status == "UNRESOLVED_CALL"


def test_f01_listing_error_blocks_resolution(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "root" / "first").mkdir(parents=True)
    _second_has_member(tmp_path)
    blocked = tmp_path / "root" / "first"
    real_iterdir = Path.iterdir

    def iterdir(self: Path) -> Any:
        if self == blocked:
            raise PermissionError(13, "Permission denied", str(self))
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", iterdir)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", "first"), _m("LIB.SECOND", "second"))
    (c,) = _run(tmp_path, ctx, CALL_AB).calls
    assert c.status == "ENVIRONMENT_GAP"
    assert c.search[0].result == "UNAVAILABLE"


def test_f01_unknown_root_id_blocks_resolution(tmp_path: Path) -> None:
    _second_has_member(tmp_path)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", "first", root="nosuchroot"), _m("LIB.SECOND", "second"))
    (c,) = _run(tmp_path, ctx, CALL_AB).calls
    assert c.status == "ENVIRONMENT_GAP"
    assert c.search[0].result == "UNAVAILABLE"


def test_f01_existing_empty_library_is_not_found_and_search_continues(tmp_path: Path) -> None:
    (tmp_path / "root" / "first").mkdir(parents=True)  # exists, holds no member
    _second_has_member(tmp_path)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", "first"), _m("LIB.SECOND", "second"))
    res = _run(tmp_path, ctx, CALL_AB)
    (c,) = res.calls
    assert [(s.library, s.result) for s in c.search] == [("LIB.FIRST", "NOT_FOUND"),
                                                         ("LIB.SECOND", "FOUND")]
    assert (c.status, c.member_path) == ("RESOLVED", "second/P1.prc")
    assert res.jobs[0].steps[0].program == "PGMTWO"


def test_f01_public_loader_missing_folder(tmp_path: Path) -> None:
    _second_has_member(tmp_path)
    ctxfile = tmp_path / "ctx.yaml"
    ctxfile.write_text(
        "schema_version: 1\nstatus: TEST_CD4R\ndatasets:\n"
        "  - {dsn: LIB.FIRST, root: r, path: first, organization: PDS, member_suffixes: ['.prc']}\n"
        "  - {dsn: LIB.SECOND, root: r, path: second, organization: PDS,"
        " member_suffixes: ['.prc']}\n", encoding="utf-8")
    ctx = load_library_context(ctxfile, {"r": tmp_path / "root"})
    (c,) = _run(tmp_path, ctx, CALL_AB).calls
    assert c.status == "ENVIRONMENT_GAP"
    assert c.search[0].result == "UNAVAILABLE"


# ------------------------------------------------------------------------------------- F02
def _two_libraries(tmp: Path) -> None:
    _write(tmp / "root", "one/P1.prc", MEMBER_1)
    _write(tmp / "root", "two/P1.prc", MEMBER_2)


@pytest.mark.parametrize("order", [("one", "two"), ("two", "one")], ids=["one-two", "two-one"])
def test_f02_duplicate_mapping_never_resolves_to_a_candidate(tmp_path: Path,
                                                             order: tuple[str, str]) -> None:
    _two_libraries(tmp_path)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", order[0]), _m("LIB.FIRST", order[1]))
    res = _run(tmp_path, ctx, CALL_A)
    (c,) = res.calls
    assert c.status != "RESOLVED", f"silently picked {c.member_path}"
    assert c.status == "AMBIGUOUS" and c.member_path is None
    assert c.search[0].result == "DUPLICATE_MAPPING"
    assert sorted(c.search[0].candidates) == ["r:one", "r:two"]
    assert res.jobs[0].steps[0].status == "UNRESOLVED_CALL"


def test_f02_duplicate_mapping_with_different_roots(tmp_path: Path) -> None:
    _write(tmp_path / "root", "one/P1.prc", MEMBER_1)
    _write(tmp_path / "other", "one/P1.prc", MEMBER_2)
    ctx = _ctx(tmp_path, _m("LIB.FIRST", "one"), _m("LIB.FIRST", "one", root="o"),
               roots={"r": tmp_path / "root", "o": tmp_path / "other"})
    (c,) = _run(tmp_path, ctx, CALL_A).calls
    assert c.status == "AMBIGUOUS" and c.member_path is None


_DUP = [{"dsn": "LIB.FIRST", "root": "r", "path": "one", "organization": "PDS",
         "member_suffixes": [".prc"]},
        {"dsn": "LIB.FIRST", "root": "r", "path": "two", "organization": "PDS",
         "member_suffixes": [".prc"]}]


@pytest.mark.parametrize("fmt", ["yaml", "json"])
@pytest.mark.parametrize("reverse", [False, True], ids=["as-written", "reversed"])
def test_f02_public_loader_rejects_duplicate_dsn(tmp_path: Path, fmt: str, reverse: bool) -> None:
    _two_libraries(tmp_path)
    data = {"schema_version": 1, "status": "TEST_CD4R",
            "datasets": list(reversed(_DUP)) if reverse else _DUP}
    p = tmp_path / f"ctx.{fmt}"
    if fmt == "json":
        p.write_text(json.dumps(data), encoding="utf-8")
    else:
        import yaml
        p.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate"):
        load_library_context(p, {"r": tmp_path / "root"})


def test_f02_main_config_loader_already_rejects_duplicate_dsn() -> None:
    import yaml

    from conftest import PROJECT_ROOT
    data = yaml.safe_load((PROJECT_ROOT / "config" / "profiler.yaml").read_text(encoding="utf-8"))
    rid = data["roots"][0]["id"]
    data["datasets"] = [dict(d, root=rid) for d in _DUP]
    with pytest.raises(ConfigError, match="duplicate"):
        config_from_dict(data, base_dir=PROJECT_ROOT / "config")

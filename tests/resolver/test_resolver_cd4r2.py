"""CD-4R2: counterexamples for the re-audit findings R01-R04 (Codex re-audit of e848ec9).

Written by the implementer before the fix, from IBM rules and the audit's acceptance conditions,
with inputs built independently of the audit's cases.json. Run against e848ec9 first to record
the failures (results/cd4r2/pre-fix.log).

R01: hash-fixed evidence must keep its exact bytes in any checkout (.gitattributes -text for the
     contract context and results/resolve only).
R02: DSN and DSNAME are two spellings of one DD parameter (SA23-1385-70, DSNAME parameter
     syntax). An override with the other spelling replaces or nullifies the procedure value; it
     never leaves both side by side in a RESOLVED expansion.
R03: --verify checks every fact it claims; facts it cannot check are listed as recorded-only.
R04: an unsupported form and an unresolved library together: the call is UNSUPPORTED, both reasons
     are kept, and no effective step is produced.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from conftest import PROJECT_ROOT
from jclprof.context.config import DatasetMapping
from jclprof.resolver import LibraryContext, Resolver
from jclprof.resolver.manifest import verify_manifest


def J(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _resolve(tmp: Path, maps: list[DatasetMapping], members: dict[str, str], text: str) -> Any:
    root = tmp / "root"
    for rel, body in members.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    job = root / "jcl" / "J.jcl"
    job.parent.mkdir(parents=True, exist_ok=True)
    job.write_text(text, encoding="utf-8")
    ctx = LibraryContext(tuple(maps), {"r": root}, "TEST", "cd4r2")
    return Resolver(ctx).resolve_file(job, "jcl/J.jcl", "r")


def _m(dsn: str, folder: str) -> DatasetMapping:
    return DatasetMapping(dsn, "r", folder, "PDS", (".prc",), {})


# ------------------------------------------------------------------------------------ R01
HASH_FIXED = ["config/contexts/cd4-contract-context.yaml",
              "results/resolve/official/effective.json",
              "results/resolve/contract/effective.json",
              "results/resolve/report.md",
              "results/resolve/run-manifest.json"]


def _attr(path: str) -> str:
    out = subprocess.run(["git", "check-attr", "text", "--", path], cwd=PROJECT_ROOT,
                         capture_output=True, text=True, check=True).stdout
    return out.strip().rsplit(": ", 1)[-1]


@pytest.mark.parametrize("path", HASH_FIXED)
def test_r01_hash_fixed_evidence_is_byte_exact(path: str) -> None:
    assert _attr(path) == "unset"  # "-text": checked out exactly as the Git blob


@pytest.mark.parametrize("path", ["config/profiler.yaml", "uv.lock",
                                  "src/jclprof/resolver/resolver.py",
                                  "results/cd4r/resolver-tests.log"])
def test_r01_attribute_is_not_widened(path: str) -> None:
    assert _attr(path) == "unspecified"


# ------------------------------------------------------------------------------------ R02
BASE_DSN = J("//PX PROC", "//S1 EXEC PGM=IEFBR14", "//D1 DD DISP=SHR,DSN=BASE.NAME,UNIT=3390",
             "// PEND")
BASE_DSNAME = BASE_DSN.replace("DSN=BASE.NAME", "DSNAME=BASE.NAME")
CALL = ("//J JOB", "//L JCLLIB ORDER=(T.LIB)", "//C EXEC PX")


def _dd(res: Any) -> Any:
    (c,) = res.calls
    assert c.status == "RESOLVED"
    (st,) = res.jobs[0].steps
    return next(d for d in st.dds if d.ddname == "D1")


def _names(dd: Any) -> list[tuple[str, Any]]:
    return [(p.name, p.value) for p in dd.params if p.name in ("DSN", "DSNAME")]


@pytest.mark.parametrize(("base", "over"), [(BASE_DSN, "DSNAME=NEW.NAME"),
                                            (BASE_DSNAME, "DSN=NEW.NAME")],
                         ids=["base-DSN_override-DSNAME", "base-DSNAME_override-DSN"])
def test_r02_other_spelling_replaces(tmp_path: Path, base: str, over: str) -> None:
    res = _resolve(tmp_path, [_m("T.LIB", "lib")], {"lib/PX.prc": base},
                   J(*CALL, f"//S1.D1 DD {over}"))
    dd = _dd(res)
    new_name = over.split("=")[0]
    assert _names(dd) == [(new_name, "NEW.NAME")]  # exactly one data set name, the new one
    (rec,) = [o for o in dd.overrides if o.param in ("DSN", "DSNAME")]
    assert (rec.action, rec.original, rec.applied) == ("REPLACE", "BASE.NAME", "NEW.NAME")
    assert rec.param == new_name and rec.original_param == ("DSNAME" if new_name == "DSN"
                                                            else "DSN")
    assert (rec.source.file, rec.source.line) == ("jcl/J.jcl", 4)
    assert (rec.original_source.file, rec.original_source.line) == ("lib/PX.prc", 3)
    assert [p.name for p in dd.params] == ["DISP", new_name, "UNIT"]  # position kept
    assert res.unsupported == ()


def test_r02_null_other_spelling_nullifies(tmp_path: Path) -> None:
    res = _resolve(tmp_path, [_m("T.LIB", "lib")], {"lib/PX.prc": BASE_DSN},
                   J(*CALL, "//S1.D1 DD DSNAME="))
    dd = _dd(res)
    assert _names(dd) == []
    (rec,) = [o for o in dd.overrides if o.param in ("DSN", "DSNAME")]
    assert (rec.action, rec.original, rec.applied) == ("NULLIFY", "BASE.NAME", None)
    assert (rec.original_param, rec.original_source.line) == ("DSN", 3)


@pytest.mark.parametrize(("base", "over"), [(BASE_DSN, "DSN=A.NAME,DSNAME=B.NAME"),
                                            (BASE_DSN.replace("DSN=BASE.NAME",
                                                              "DSN=BASE.NAME,DSNAME=X.NAME"),
                                             "DSN=NEW.NAME")],
                         ids=["override-both", "base-both"])
def test_r02_both_spellings_on_one_statement_is_unsupported(tmp_path: Path, base: str,
                                                            over: str) -> None:
    res = _resolve(tmp_path, [_m("T.LIB", "lib")], {"lib/PX.prc": base},
                   J(*CALL, f"//S1.D1 DD {over}"))
    (c,) = res.calls
    assert c.status == "UNSUPPORTED"
    assert "U-OVR-DSN-DUPLICATE" in {u.form for u in res.unsupported}
    assert res.counts()["program_steps"] == 0


def test_r02_same_spelling_still_replaces(tmp_path: Path) -> None:
    res = _resolve(tmp_path, [_m("T.LIB", "lib")], {"lib/PX.prc": BASE_DSN},
                   J(*CALL, "//S1.D1 DD DSN=NEW.NAME"))
    (rec,) = [o for o in _dd(res).overrides if o.param == "DSN"]
    assert (rec.action, rec.original_param, rec.original_source.line) == ("REPLACE", "DSN", 3)


# ------------------------------------------------------------------------------------ R04
PLAIN = J("//PX PROC", "//S1 EXEC PGM=IEFBR14", "// PEND")
EXEC_OVR = J("//J JOB", "//L JCLLIB ORDER=(T.LIB)", "//C EXEC PX,COND=(0,NE)")


def _lib_state(tmp: Path, state: str) -> tuple[list[DatasetMapping], dict[str, str]]:
    if state == "normal":
        return [_m("T.LIB", "lib")], {"lib/PX.prc": PLAIN}
    if state == "unmapped":
        return [], {"lib/PX.prc": PLAIN}
    if state == "unavailable":
        return [_m("T.LIB", "no-such-folder")], {}
    if state == "duplicate":
        return [_m("T.LIB", "lib"), _m("T.LIB", "lib2")], {"lib/PX.prc": PLAIN,
                                                           "lib2/PX.prc": PLAIN}
    raise AssertionError(state)


# state -> (search status, environment diagnostic codes expected besides RES-W004)
STATES = {"normal": ("RESOLVED", set()),
          "unmapped": ("ENVIRONMENT_GAP", {"RES-W002", "RES-W005"}),
          "unavailable": ("ENVIRONMENT_GAP", {"RES-W006", "RES-W005"}),
          "duplicate": ("AMBIGUOUS", {"RES-W007"})}


@pytest.mark.parametrize("state", sorted(STATES))
def test_r04_unsupported_and_library_state_keep_both_reasons(tmp_path: Path, state: str) -> None:
    maps, members = _lib_state(tmp_path, state)
    res = _resolve(tmp_path, maps, members, EXEC_OVR)
    (c,) = res.calls
    search, env_codes = STATES[state]
    assert c.status == "UNSUPPORTED"  # primary status: an unsupported form was detected
    assert c.search_status == search  # the library evidence is kept, not replaced
    assert "UNSUPPORTED:U-EXEC-OVERRIDE" in c.reasons
    if search != "RESOLVED":
        assert search in c.reasons
    codes = {d.code for d in res.diagnostics}
    assert "RES-W004" in codes and env_codes <= codes
    assert [u.form for u in res.unsupported] == ["U-EXEC-OVERRIDE"]
    counts = res.counts()
    assert (counts["program_steps"], counts["unresolved_call_steps"]) == (0, 1)
    assert all(st.status != "RESOLVED" for st in res.jobs[0].steps)


@pytest.mark.parametrize("state", sorted(STATES))
def test_r04_without_unsupported_form_status_is_the_search_status(tmp_path: Path,
                                                                  state: str) -> None:
    maps, members = _lib_state(tmp_path, state)
    res = _resolve(tmp_path, maps, members, EXEC_OVR.replace(",COND=(0,NE)", ""))
    (c,) = res.calls
    assert c.status == STATES[state][0] == c.search_status
    assert not [r for r in c.reasons if r.startswith("UNSUPPORTED")]


# ------------------------------------------------------------------------------------ R03
def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "cd4_resolve_report_r2", PROJECT_ROOT / "tools" / "cd4_resolve_report.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fresh(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    mpath = _tool().main(tmp_path_factory.mktemp("r2run"))
    return mpath, json.loads(mpath.read_text(encoding="utf-8"))


def _problems(m: dict[str, Any], mpath: Path) -> list[str]:
    return verify_manifest(m, PROJECT_ROOT, manifest_path=mpath)


def _mut(m: dict[str, Any], fn: Any) -> dict[str, Any]:
    c: dict[str, Any] = json.loads(json.dumps(m))
    fn(c)
    return c


def _set(path: list[Any], value: Any) -> Any:
    def f(c: dict[str, Any]) -> None:
        cur: Any = c
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value
    return f


# every mutation must be detected (the facts --verify guarantees)
DETECTED = {
    "git_commit_zero": _set(["code", "git_commit"], "0" * 40),
    "jes_changed": _set(["environment", "jes"], "JES3"),
    "encoding_changed": _set(["environment", "encoding"], "cp037"),
    "uv_lock_zero": _set(["environment", "uv_lock_sha256"], "0" * 64),
    "contract_mappings_empty": _set(["contexts", "contract", "mappings"], []),
    "contract_basis_confirmed": _set(["contexts", "contract", "basis"], "CONFIRMED"),
    "official_roots_changed": _set(["contexts", "official", "roots"], {"carddemo": "X:/elsewhere"}),
    "context_missing": lambda c: c["contexts"].pop("contract"),
    "src_tree_zero": _set(["code", "src_tree_sha256"], "0" * 64),
    "src_file_dropped": lambda c: c["code"]["src_files"].pop("src/jclprof/resolver/resolver.py"),
    "output_bytes_zero": lambda c: c["outputs"][0].__setitem__("bytes", 0),
    "outputs_removed": _set(["outputs"], []),
    "output_one_removed": lambda c: c["outputs"].pop(),
    "inputs_removed": _set(["inputs", "files"], []),
    "input_one_removed": lambda c: c["inputs"]["files"].pop(),
    "members_removed": _set(["inputs", "members_read"], []),
    "counts_changed": _set(["counts", "contract", "jobs_46", "program_steps"], 120),
    "schema_changed": _set(["schema_version"], 1),
}


def test_r03_unmutated_manifest_verifies(fresh: tuple[Path, dict[str, Any]]) -> None:
    mpath, m = fresh
    assert _problems(m, mpath) == []


@pytest.mark.parametrize("name", sorted(DETECTED))
def test_r03_mutation_detected(fresh: tuple[Path, dict[str, Any]], name: str) -> None:
    mpath, m = fresh
    assert _problems(_mut(m, DETECTED[name]), mpath), name


def test_r03_recorded_only_fields_are_declared(fresh: tuple[Path, dict[str, Any]]) -> None:
    from jclprof.resolver.manifest import RECORDED_ONLY, VERIFIED
    mpath, m = fresh
    contract = m["verification"]
    assert set(contract["verified"]) == set(VERIFIED)
    assert set(contract["recorded_only"]) == set(RECORDED_ONLY)
    assert not set(VERIFIED) & set(RECORDED_ONLY)
    # changing a recorded-only field does not fail --verify, and is declared as not guaranteed
    for path in (["code", "git_dirty_paths"], ["generated_at"], ["environment", "python"],
                 ["environment", "platform"]):
        assert ".".join(path) in RECORDED_ONLY
        assert _problems(_mut(m, _set(path, "edited")), mpath) == []


def test_r03_manifest_trust_point(fresh: tuple[Path, dict[str, Any]]) -> None:
    from jclprof.resolver.manifest import manifest_digest
    mpath, m = fresh
    good = manifest_digest(mpath)
    assert _problems(m, mpath) == []
    assert verify_manifest(m, PROJECT_ROOT, manifest_path=mpath, expected_sha256=good) == []
    bad = verify_manifest(m, PROJECT_ROOT, manifest_path=mpath, expected_sha256="0" * 64)
    assert any(p.startswith("manifest digest") for p in bad)


def _leaves(x: Any, path: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    if isinstance(x, dict):
        return [p for k, v in x.items() for p in _leaves(v, (*path, k))] or [path]
    if isinstance(x, list):
        return _leaves(x[0], (*path, 0)) if x else [path]  # first element of each list
    return [path]


def _dotted(path: tuple[Any, ...]) -> str:
    return ".".join(str(p) for p in path if not isinstance(p, int))


def _classified(path: tuple[Any, ...]) -> str | None:
    from jclprof.resolver.manifest import RECORDED_ONLY, VERIFIED
    d = _dotted(path)
    for group, names in (("recorded", RECORDED_ONLY), ("verified", VERIFIED)):
        if any(d == n or d.startswith(n + ".") for n in names):
            return group
    return None


def _change(v: Any) -> Any:
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + 1
    if isinstance(v, str):
        return v + "X"
    return "X" if v is None else ["X"]  # an empty list or dict becomes non-empty


def test_r03_every_manifest_field_is_detected_or_declared(
        fresh: tuple[Path, dict[str, Any]]) -> None:
    mpath, m = fresh
    unclassified, escaped = [], []
    for path in _leaves(m):
        group = _classified(path)
        if group is None:
            unclassified.append(_dotted(path))
            continue
        mutated = _mut(m, lambda c, p=path: _assign(c, p))
        if group == "verified" and not _problems(mutated, mpath):
            escaped.append(".".join(map(str, path)))
    assert unclassified == []
    assert escaped == []


def _assign(c: Any, path: tuple[Any, ...]) -> None:
    cur = c
    for k in path[:-1]:
        cur = cur[k]
    if not path:
        return
    cur[path[-1]] = _change(cur[path[-1]])

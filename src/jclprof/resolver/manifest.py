"""Run manifest for resolver outputs (CD-4R F09, verification contract CD-4R2 R03).

A manifest ties one generated result set to the implementation, inputs, library contexts and run
conditions. ``verify_report`` separates three kinds of statement:

* VERIFIED       facts that --verify re-derives or recomputes; any difference is a problem
* RECORDED_ONLY  facts stored for information that cannot be checked after the fact (when and
                 where the run happened, the dirty state at that moment); never claimed verified
* trust point    the manifest file itself is anchored by its Git blob in HEAD or by an external
                 SHA-256 (``expected_sha256``); without either it is reported UNANCHORED

Hash methods (R01): files that .gitattributes keeps byte-exact (``-text``: the contract context
and results/resolve) and the read-only corpus inputs are hashed as raw bytes. Other repository
files (config/profiler.yaml, uv.lock, source code) are hashed with CRLF normalised to LF, so a
checkout with either line ending has the same identity.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from jclprof.context.config import load_config
from jclprof.resolver.library import LibraryContext, load_library_context

SCHEMA_VERSION = 2
KIND = "resolver-run"
CODE_DIRS = ("src/jclprof",)
DIRTY_PATHS = ("src", "tools", "config", "specs", "tests")
# Repository files kept byte-exact by .gitattributes (-text); hashed raw (R01).
RAW_HASH_FILES = frozenset({"config/contexts/cd4-contract-context.yaml"})
RAW_HASH_DIRS = ("results/resolve/",)

VERIFIED = (
    "schema_version", "kind", "verification",
    "inputs.root_id", "inputs.root", "inputs.file_list", "inputs.files", "inputs.members_read",
    "contexts", "code.src_files", "code.src_tree_sha256", "code.generator", "code.git_commit",
    "code.commit_contains_code",
    "environment.encoding", "environment.jes", "environment.uv_lock_sha256",
    "output_dir", "outputs", "counts",
)
RECORDED_ONLY = (
    "generated_at", "code.git_dirty_paths", "code.code_hash", "environment.python",
    "environment.implementation", "environment.platform", "environment.byteorder",
    "environment.pyyaml",
)
TRUST_POINT = ("the manifest file is trusted through its Git blob in HEAD "
               "(git hash-object == git rev-parse HEAD:<path>) or an external SHA-256 digest")


# ------------------------------------------------------------------------------------ hashing
def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text_lf(path: Path) -> str:
    """SHA-256 with CRLF normalised to LF (same identity for either checkout line ending)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _lf_bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def manifest_digest(path: Path) -> str:
    return sha256_file(path)


def hash_method(rel: str) -> str:
    return "raw" if rel in RAW_HASH_FILES or rel.startswith(RAW_HASH_DIRS) else "lf"


def repo_hash(path: Path, rel: str) -> str:
    return sha256_file(path) if hash_method(rel) == "raw" else sha256_text_lf(path)


def _rel(p: Path, project: Path) -> str:
    try:
        return Path(p).resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return Path(p).resolve().as_posix()


def _abs(rel: str, project: Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else project / p


def _git(project: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=project, capture_output=True, check=False,
                           timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


# ------------------------------------------------------------------------------------ building
def _code_files(project: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for d in CODE_DIRS:
        for p in sorted((project / d).rglob("*.py")):
            files[p.relative_to(project).as_posix()] = sha256_text_lf(p)
    return files


def _tree(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(files.items()))
                          .encode()).hexdigest()


def _git_blobs(project: Path, commit: str, rels: list[str]) -> dict[str, bytes | None]:
    """Contents of commit:rel for every rel, read through one `git cat-file --batch`."""
    req = "".join(f"{commit}:{r}\n" for r in rels).encode()
    try:
        r = subprocess.run(["git", "cat-file", "--batch"], cwd=project, input=req,
                           capture_output=True, check=False, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return dict.fromkeys(rels)
    out, pos = r.stdout, 0
    res: dict[str, bytes | None] = {}
    for rel in rels:
        end = out.find(b"\n", pos)
        if end < 0:
            res[rel] = None
            continue
        header = out[pos:end].split()
        pos = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            res[rel] = out[pos:pos + size]
            pos += size + 1
        else:
            res[rel] = None
    return res


def commit_contains(project: Path, commit: str, files: dict[str, str]) -> bool:
    """True when every recorded file (LF-normalised) is identical at the given commit."""
    blobs = _git_blobs(project, commit, sorted(files))
    return all(blobs[rel] is not None and _lf_bytes_hash(blobs[rel] or b"") == want
               for rel, want in files.items())


def code_identity(project: Path, generator: Path) -> dict[str, Any]:
    files = _code_files(project)
    gen_rel = _rel(generator, project)
    head = _git(project, "rev-parse", "HEAD")
    status = _git(project, "status", "--porcelain", "--untracked-files=all", "--", *DIRTY_PATHS)
    dirty = sorted(line[3:].strip() for line in (status or "").splitlines() if line.strip())
    gen_sha = sha256_text_lf(generator)
    commit = head.strip() if head else None
    return {"git_commit": commit,
            "commit_contains_code": (commit_contains(project, commit, {**files, gen_rel: gen_sha})
                                     if commit else None),
            "git_dirty_paths": dirty if status is not None else None,
            "generator": {"path": gen_rel, "sha256": gen_sha},
            "code_hash": "sha256 of bytes with CRLF normalised to LF",
            "src_tree_sha256": _tree(files), "src_files": files}


def environment(encoding: str, jes: str, project: Path) -> dict[str, Any]:
    lock = project / "uv.lock"
    return {"python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(), "byteorder": sys.byteorder,
            "encoding": encoding, "jes": jes, "pyyaml": getattr(yaml, "__version__", None),
            "uv_lock_sha256": sha256_text_lf(lock) if lock.exists() else None}


def _inline(ctx: LibraryContext) -> dict[str, Any]:
    rec = {"basis": ctx.basis, "note": ctx.note, "mappings": [asdict(m) for m in ctx.mappings],
           "roots": {k: Path(v).as_posix() for k, v in sorted(ctx.roots.items())}}
    return dict(json.loads(json.dumps(rec)))  # the JSON form, as stored in the manifest


def context_record(ctx: LibraryContext, file: Path, loader: str, project: Path) -> dict[str, Any]:
    rel = _rel(file, project)
    return {"loader": loader, "file": rel, "sha256_method": hash_method(rel),
            "sha256": repo_hash(file, rel), **_inline(ctx)}


def build_manifest(*, project: Path, generator: Path, root_id: str, root: Path,
                   file_list: Path, files: list[str], members: dict[str, str],
                   contexts: dict[str, tuple[LibraryContext, Path, str]],
                   out_dir: Path, outputs: list[Path], encoding: str, jes: str,
                   counts: dict[str, Any]) -> dict[str, Any]:
    """contexts: name -> (context, file, loader) with loader "config" or "overlay"."""
    fl = _rel(file_list, project)
    return {
        "schema_version": SCHEMA_VERSION, "kind": KIND,
        "verification": {"verified": list(VERIFIED), "recorded_only": list(RECORDED_ONLY),
                         "trust_point": TRUST_POINT},
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code": code_identity(project, generator),
        "environment": environment(encoding, jes, project),
        "inputs": {"root_id": root_id, "root": Path(root).as_posix(),
                   "file_list": {"path": fl, "sha256_method": hash_method(fl),
                                 "sha256": repo_hash(file_list, fl)},
                   "files": [{"path": f, "sha256": sha256_file(root / f)} for f in files],
                   "members_read": [{"path": k, "sha256": v} for k, v in sorted(members.items())]},
        "contexts": {n: context_record(c, f, ld, project) for n, (c, f, ld) in contexts.items()},
        "output_dir": _rel(out_dir, project),
        "outputs": [{"path": _rel(p, project), "bytes": p.stat().st_size,
                     "sha256": sha256_file(p)} for p in outputs],
        "counts": counts,
    }


def counts_from_outputs(per_context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Counts as the generator reports them, re-derived from parsed effective.json files."""
    out: dict[str, Any] = {}
    for name, data in per_context.items():
        jobs = [v for f, v in data.items() if not f.lower().endswith(".prc")]
        keys = ("program_steps", "unresolved_call_steps", "dds", "job_level_dds")
        out[name] = {
            "jobs_46": {k: sum(v["counts"][k] for v in jobs) for k in keys},
            "unsupported_forms": sum(len(v.get("unsupported", [])) for v in data.values()),
            "calls": sorted(f"{f}:{c['call']['line']}:{c['status']}"
                            for f, v in data.items() for c in v["calls"]),
        }
    return out


# ------------------------------------------------------------------------------------ verifying
def verify_report(manifest: dict[str, Any], project: Path, *, manifest_path: Path | None = None,
                  expected_sha256: str | None = None) -> dict[str, Any]:
    problems: list[str] = []
    not_verified: list[str] = []

    def check(label: str, path: Path, want: Any, method: str = "raw") -> None:
        if not isinstance(want, str):
            problems.append(f"{label}: no sha256 recorded for {path}")
        elif not path.is_file():
            problems.append(f"{label}: missing {path}")
        elif (sha256_file(path) if method == "raw" else sha256_text_lf(path)) != want:
            problems.append(f"{label}: sha256 differs for {path}")

    def guard(label: str, fn: Any) -> None:
        try:
            fn()
        except (KeyError, TypeError, AttributeError, ValueError, OSError) as exc:
            problems.append(f"{label}: malformed or unreadable ({type(exc).__name__}: {exc})")

    # -- schema and contract
    if manifest.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version: {manifest.get('schema_version')!r} != {SCHEMA_VERSION}")
    if manifest.get("kind") != KIND:
        problems.append(f"kind: {manifest.get('kind')!r} != {KIND!r}")
    ver = manifest.get("verification") or {}
    if (ver.get("verified") != list(VERIFIED) or ver.get("recorded_only") != list(RECORDED_ONLY)
            or ver.get("trust_point") != TRUST_POINT):
        problems.append("verification: contract section differs from this verifier")

    # -- contexts: file hash and the inline record re-derived by loading the file
    official_roots: dict[str, str] = {}

    def contexts() -> None:
        ctxs = manifest["contexts"]
        if set(ctxs) != {"official", "contract"}:
            problems.append(f"contexts: expected official and contract, got {sorted(ctxs)}")
        cfg_rec = ctxs.get("official")
        cfg = None
        if cfg_rec is not None:
            path = _abs(cfg_rec["file"], project)
            check("context official", path, cfg_rec.get("sha256"), hash_method(cfg_rec["file"]))
            cfg = load_config(path)
            official_roots.update({r.id: Path(r.path).as_posix() for r in cfg.roots})
        for name, rec in ctxs.items():
            if rec.get("sha256_method") != hash_method(rec["file"]):
                problems.append(f"context {name}: sha256_method must be "
                                f"{hash_method(rec['file'])}")
            path = _abs(rec["file"], project)
            if name != "official":
                check(f"context {name}", path, rec.get("sha256"), hash_method(rec["file"]))
            if rec.get("loader") == "config":
                derived = _inline(LibraryContext.from_config(cfg or load_config(path)))
            elif rec.get("loader") == "overlay":
                derived = _inline(load_library_context(path, {k: Path(v) for k, v
                                                              in official_roots.items()}))
            else:
                problems.append(f"context {name}: unknown loader {rec.get('loader')!r}")
                continue
            for k, v in derived.items():
                if rec.get(k) != v:
                    problems.append(f"context {name}.{k}: differs from the loaded file")
    guard("contexts", contexts)

    # -- inputs: required set from the (hash-checked) file list, every hash
    def inputs() -> None:
        inp = manifest["inputs"]
        fl = inp["file_list"]
        if fl.get("sha256_method") != hash_method(fl["path"]):
            problems.append(f"file_list: sha256_method must be {hash_method(fl['path'])}")
        check("file_list", _abs(fl["path"], project), fl.get("sha256"), hash_method(fl["path"]))
        if official_roots and official_roots.get(inp["root_id"]) != inp["root"]:
            problems.append("inputs.root: differs from the root in the official config")
        root = Path(inp["root"])
        want = set(yaml.safe_load(_abs(fl["path"], project).read_text(encoding="utf-8"))
                   ["jcl_family_files"])
        have = [x["path"] for x in inp["files"]]
        if len(have) != len(set(have)) or set(have) != want:
            problems.append(f"inputs.files: {len(set(have))} recorded, {len(want)} required "
                            f"(missing {sorted(want - set(have))[:5]})")
        for x in inp["files"]:
            check("input", root / x["path"], x.get("sha256"))
        for x in inp["members_read"]:
            check("member", root / x["path"], x.get("sha256"))
    guard("inputs", inputs)

    # -- code: recompute files and tree; the recorded commit must contain the same code
    def code() -> None:
        code = manifest["code"]
        gen = code["generator"]
        check("generator", _abs(gen["path"], project), gen.get("sha256"), "lf")
        files = code["src_files"]
        now = _code_files(project)
        for rel in sorted(set(files) | set(now)):
            if rel not in now:
                problems.append(f"code: {rel} recorded but not present")
            elif rel not in files:
                problems.append(f"code: {rel} present but not recorded")
            elif files[rel] != now[rel]:
                problems.append(f"code: sha256 differs for {rel}")
        if code.get("src_tree_sha256") != _tree(files):
            problems.append("code.src_tree_sha256: does not match src_files")
        commit = code.get("git_commit")
        if _git(project, "rev-parse", "--git-dir") is None:
            not_verified.append("code.git_commit (no Git repository)")
        elif not isinstance(commit, str) or _git(project, "cat-file", "-e",
                                                 f"{commit}^{{commit}}") is None:
            problems.append(f"code.git_commit: {commit!r} is not a commit in this repository")
        else:
            actual = commit_contains(project, commit, {**files, gen["path"]: gen.get("sha256")})
            if code.get("commit_contains_code") is not actual:
                problems.append(f"code.commit_contains_code: recorded "
                                f"{code.get('commit_contains_code')!r}, re-derived {actual!r} "
                                f"for {commit[:12]}")
            if not actual:
                not_verified.append(f"code is not the content of {commit[:12]} "
                                    "(generated from uncommitted code)")
    guard("code", code)

    # -- environment facts that can be re-derived
    def env() -> None:
        e = manifest["environment"]
        lock = project / "uv.lock"
        want = sha256_text_lf(lock) if lock.exists() else None
        if e.get("uv_lock_sha256") != want:
            problems.append("environment.uv_lock_sha256: differs from uv.lock")
    guard("environment", env)

    # -- outputs: required set, bytes, hashes; counts / members / run conditions re-derived
    def outputs() -> None:
        out_dir = (manifest_path.parent if manifest_path is not None
                   else _abs(manifest["output_dir"], project))
        if _rel(out_dir, project) != manifest["output_dir"]:
            problems.append("output_dir: does not match the manifest location")
        names = sorted(manifest["contexts"])
        required = {f"{n}/effective.json" for n in names} | {"report.md"}
        rec = {}
        for x in manifest["outputs"]:
            p = _abs(x["path"], project)
            try:
                rec[p.resolve().relative_to(out_dir.resolve()).as_posix()] = (p, x)
            except ValueError:
                problems.append(f"outputs: {x['path']} is outside the output directory")
        if set(rec) != required:
            problems.append(f"outputs: recorded {sorted(rec)}, required {sorted(required)}")
        for _rel_name, (p, x) in sorted(rec.items()):
            check("output", p, x.get("sha256"))
            if p.is_file() and p.stat().st_size != x.get("bytes"):
                problems.append(f"output: bytes differ for {p}")
        if problems or set(rec) != required:
            return  # re-derivation needs the exact, verified outputs
        data = {n: json.loads(rec[f"{n}/effective.json"][0].read_text(encoding="utf-8"))
                for n in names}
        if counts_from_outputs(data) != manifest["counts"]:
            problems.append("counts: differ from the counts re-derived from the outputs")
        members = {(c["member_path"], c["member_sha256"]) for d in data.values()
                   for v in d.values() for c in v["calls"] if c.get("member_path")}
        recorded = {(x["path"], x["sha256"]) for x in manifest["inputs"]["members_read"]}
        if members != recorded:
            problems.append("inputs.members_read: differ from the members in the outputs")
        conds = {(v["run_conditions"]["encoding"], v["run_conditions"]["jes"])
                 for d in data.values() for v in d.values()}
        e = manifest["environment"]
        if conds != {(e.get("encoding"), e.get("jes"))}:
            problems.append(f"environment.encoding/jes: outputs were produced with {conds}")
        basis = {n: {v["library_basis"] for v in d.values()} for n, d in data.items()}
        for n in names:
            if basis[n] != {manifest["contexts"][n]["basis"]}:
                problems.append(f"context {n}.basis: outputs carry {sorted(basis[n])}")
    guard("outputs", outputs)

    # -- trust point for the manifest file itself
    trust = "UNANCHORED"
    if expected_sha256 is not None:
        if manifest_path is None or manifest_digest(manifest_path) != expected_sha256:
            problems.append("manifest digest: differs from the expected SHA-256")
        else:
            trust = f"EXTERNAL_SHA256 {expected_sha256}"
    elif manifest_path is not None:
        rel = _rel(manifest_path, project)
        head = _git(project, "rev-parse", f"HEAD:{rel}")
        obj = _git(project, "hash-object", "--no-filters", str(manifest_path))
        if head and obj and head.strip() == obj.strip():
            trust = f"GIT_BLOB HEAD:{rel} {head.strip()}"
    if trust == "UNANCHORED":
        not_verified.append("manifest file (no Git blob in HEAD and no external digest)")
    return {"problems": problems, "verified": list(VERIFIED),
            "recorded_only": list(RECORDED_ONLY), "not_verified": not_verified,
            "trust": trust}


def verify_manifest(manifest: dict[str, Any], project: Path, output_base: Path | None = None,
                    *, manifest_path: Path | None = None,
                    expected_sha256: str | None = None) -> list[str]:
    """Problems only (empty = every VERIFIED fact holds). output_base is kept for API
    compatibility; output locations come from the manifest (or manifest_path)."""
    del output_base
    problems: list[str] = verify_report(manifest, project, manifest_path=manifest_path,
                                        expected_sha256=expected_sha256)["problems"]
    return problems

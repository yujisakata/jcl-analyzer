"""Run manifest for resolver outputs (CD-4R F09).

A manifest ties one generated result set to everything needed to reproduce and audit it:
implementation (git commit, dirty paths, SHA-256 of every src/jclprof file and of the generator),
inputs (file list, every JCL / PROC input and every member read, by SHA-256), library contexts
(file path and SHA-256, basis, the full mapping and root table), environment (Python, platform,
encoding, JES type, dependency versions, uv.lock) and outputs (path, bytes, SHA-256).

verify_manifest() recomputes the hashes and returns every mismatch; an empty list means the
outputs, inputs, contexts and implementation on disk are the ones the manifest describes.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from jclprof.resolver.library import LibraryContext

SCHEMA_VERSION = 1
CODE_DIRS = ("src/jclprof",)
DIRTY_PATHS = ("src", "tools", "config", "specs", "tests")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text_lf(path: Path) -> str:
    """SHA-256 of a source file with CRLF normalised to LF, so the same commit checked out with
    either line ending (Windows worktrees, .gitattributes) has the same code identity."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(project: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True,
                           check=False, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def code_identity(project: Path, generator: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    for d in CODE_DIRS:
        for p in sorted((project / d).rglob("*.py")):
            files[p.relative_to(project).as_posix()] = sha256_text_lf(p)
    tree = hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in files.items()).encode()).hexdigest()
    head = _git(project, "rev-parse", "HEAD")
    status = _git(project, "status", "--porcelain", "--untracked-files=all", "--", *DIRTY_PATHS)
    dirty = sorted(line[3:].strip() for line in (status or "").splitlines() if line.strip())
    return {"git_commit": head.strip() if head else None,
            "git_dirty_paths": dirty if status is not None else None,
            "generator": {"path": generator.relative_to(project).as_posix(),
                          "sha256": sha256_text_lf(generator)},
            "code_hash": "sha256 of bytes with CRLF normalised to LF",
            "src_tree_sha256": tree, "src_files": files}


def environment(encoding: str, jes: str, project: Path) -> dict[str, Any]:
    lock = project / "uv.lock"
    return {"python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(), "byteorder": sys.byteorder,
            "encoding": encoding, "jes": jes, "pyyaml": getattr(yaml, "__version__", None),
            "uv_lock_sha256": sha256_file(lock) if lock.exists() else None}


def context_record(ctx: LibraryContext, file: Path | None, project: Path) -> dict[str, Any]:
    rec: dict[str, Any] = {"basis": ctx.basis, "note": ctx.note,
                           "mappings": [asdict(m) for m in ctx.mappings],
                           "roots": {k: str(v) for k, v in sorted(ctx.roots.items())}}
    if file is not None:
        rec["file"] = _rel(file, project)
        rec["sha256"] = sha256_file(file)
    return rec


def _rel(p: Path, project: Path) -> str:
    try:
        return Path(p).resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return str(p)


def build_manifest(*, project: Path, generator: Path, root_id: str, root: Path,
                   file_list: Path, files: list[str], members: dict[str, str],
                   contexts: dict[str, tuple[LibraryContext, Path | None]],
                   outputs: list[Path], encoding: str, jes: str,
                   counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "kind": "resolver-run",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code": code_identity(project, generator),
        "environment": environment(encoding, jes, project),
        "inputs": {"root_id": root_id, "root": str(root),
                   "file_list": {"path": _rel(file_list, project),
                                 "sha256": sha256_file(file_list)},
                   "files": [{"path": f, "sha256": sha256_file(root / f)} for f in files],
                   "members_read": [{"path": k, "sha256": v} for k, v in sorted(members.items())]},
        "contexts": {name: context_record(c, f, project) for name, (c, f) in contexts.items()},
        "outputs": [{"path": _rel(p, project), "bytes": p.stat().st_size,
                     "sha256": sha256_file(p)} for p in outputs],
        "counts": counts,
    }


def verify_manifest(manifest: dict[str, Any], project: Path,
                    output_base: Path | None = None) -> list[str]:
    """Recompute every hash recorded in the manifest; return the mismatches (empty = match)."""
    problems: list[str] = []

    def check(label: str, path: Path, want: str, text: bool = False) -> None:
        if not path.is_file():
            problems.append(f"{label}: missing {path}")
        elif (sha256_text_lf(path) if text else sha256_file(path)) != want:
            problems.append(f"{label}: sha256 differs for {path}")

    if manifest.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version {manifest.get('schema_version')!r}")
    inp = manifest["inputs"]
    root = Path(inp["root"])
    check("file_list", project / inp["file_list"]["path"], inp["file_list"]["sha256"])
    for x in inp["files"]:
        check("input", root / x["path"], x["sha256"])
    for x in inp["members_read"]:
        check("member", root / x["path"], x["sha256"])
    for name, c in manifest["contexts"].items():
        if "file" in c:
            check(f"context {name}", project / c["file"], c["sha256"])
    code = manifest["code"]
    check("generator", project / code["generator"]["path"], code["generator"]["sha256"], True)
    now = {p.relative_to(project).as_posix() for d in CODE_DIRS
           for p in (project / d).rglob("*.py")}
    for rel, want in code["src_files"].items():
        check("code", project / rel, want, True)
    for extra in sorted(now - set(code["src_files"])):
        problems.append(f"code: file not in manifest {extra}")
    base = output_base or project
    for x in manifest["outputs"]:
        check("output", base / x["path"], x["sha256"])
    return problems

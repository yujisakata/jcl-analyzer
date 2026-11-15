"""Step 1: development environment and read-access check (Harness layer).

Reads every input file in binary mode to prove readability. Never writes to, renames or
changes attributes of input files. ``os.access(W_OK)`` is only *queried* to report whether
the OS would permit writes (protection then relies on the tool's discipline, ADR-006).
"""

from __future__ import annotations

import os
import platform
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from jclprof import __version__
from jclprof.context.config import ProfilerConfig

REQUIRED_PYTHON = (3, 12)
REQUIRED_PACKAGES = ("PyYAML", "pytest", "hypothesis", "ruff", "mypy")


def _check_root(root_id: str, path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "id": root_id, "path": path.as_posix(), "exists": path.exists(), "is_dir": path.is_dir(),
        "file_count": 0, "readable_count": 0, "unreadable": [], "total_bytes": 0,
        "os_write_permitted_count": 0,
    }
    if not info["is_dir"]:
        return info
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            info["file_count"] += 1
            try:
                with open(p, "rb") as f:
                    n = 0
                    while chunk := f.read(1024 * 1024):
                        n += len(chunk)
                info["readable_count"] += 1
                info["total_bytes"] += n
            except OSError as e:
                info["unreadable"].append(f"{p.relative_to(path).as_posix()}: {e}")
            if os.access(p, os.W_OK):
                info["os_write_permitted_count"] += 1
    return info


def run_envcheck(cfg: ProfilerConfig) -> dict[str, Any]:
    py_ok = sys.version_info[:2] == REQUIRED_PYTHON
    packages: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_PACKAGES:
        try:
            packages[name] = {"installed": True, "version": metadata.version(name)}
        except metadata.PackageNotFoundError:
            packages[name] = {"installed": False, "version": None}
    roots = [_check_root(r.id, r.path) for r in cfg.roots]
    ok = (
        py_ok
        and all(p["installed"] for p in packages.values())
        and all(r["is_dir"] and not r["unreadable"] for r in roots)
    )
    return {
        "tool_version": __version__,
        "python": {
            "version": platform.python_version(),
            "required": ".".join(map(str, REQUIRED_PYTHON)) + ".x",
            "executable": sys.executable,
            "ok": py_ok,
        },
        "platform": platform.platform(),
        "packages": packages,
        "config": cfg.source_path.as_posix() if cfg.source_path else None,
        "roots": roots,
        "ok": ok,
    }

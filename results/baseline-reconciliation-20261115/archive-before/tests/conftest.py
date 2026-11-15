"""Shared helpers for the jclprof test suite.

Test fixtures are synthetic and built per test under ``tmp_path``. The real corpus is only
read by ``tests/acceptance`` (marked ``corpus``).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import pytest

from jclprof.harness.registry import RuleRegistry

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CARDDEMO_ROOT = Path(
    os.environ.get(
        "JCLPROF_CARDDEMO_ROOT",
        "D:/projects/aws-card/aws-mainframe-modernization-carddemo/app",
    )
)


def write_tree(root: Path, files: dict[str, bytes]) -> None:
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    """Independent (non-jclprof) snapshot of every file: size, mtime_ns, sha256."""
    snap: dict[str, tuple[int, int, str]] = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = Path(dirpath) / name
            st = p.stat()
            snap[p.relative_to(root).as_posix()] = (
                st.st_size,
                st.st_mtime_ns,
                hashlib.sha256(p.read_bytes()).hexdigest(),
            )
    return snap


BASE_ASSET_TYPES: dict[str, dict[str, Any]] = {
    "JCL": {"member_like": True, "fixed_record_length": 80},
    "PROC": {"member_like": True, "fixed_record_length": 80},
    "COBOL": {"member_like": True},
    "DATA": {"member_like": False},
    "PLACEHOLDER": {"member_like": False},
}

BASE_RULES: list[dict[str, Any]] = [
    {"id": "CLS-001", "pattern": "**/.gitkeep", "asset_type": "PLACEHOLDER"},
    {"id": "CLS-002", "pattern": "**/data/**", "asset_type": "DATA"},
    {"id": "CLS-010", "pattern": "**/*.jcl", "asset_type": "JCL"},
    {"id": "CLS-011", "pattern": "**/*.prc", "asset_type": "PROC"},
    {"id": "CLS-020", "pattern": "**/*.cbl", "asset_type": "COBOL"},
]


def make_config_dict(roots: list[tuple[str, Path]], **overrides: Any) -> dict[str, Any]:
    d: dict[str, Any] = {
        "version": 1,
        "roots": [{"id": rid, "path": str(p)} for rid, p in roots],
        "encoding": {"default": "utf-8", "overrides": []},
        "limits": {"max_decode_bytes": 1_000_000},
        "follow_symlinks": False,
        "exclude": [],
        "asset_types": {k: dict(v) for k, v in BASE_ASSET_TYPES.items()},
        "classification": [dict(r) for r in BASE_RULES],
    }
    d.update(overrides)
    return d


@pytest.fixture
def corpus_root() -> Path:
    if not CARDDEMO_ROOT.is_dir():
        pytest.skip(f"CardDemo corpus not found at {CARDDEMO_ROOT}")
    return CARDDEMO_ROOT


# ---------------------------------------------------------------- Harness self-test fixtures
@pytest.fixture(scope="session")
def registry() -> RuleRegistry:
    from jclprof.harness.registry import load_rules

    return load_rules(PROJECT_ROOT / "specs" / "rules.yaml")


@pytest.fixture(scope="session")
def catalog() -> dict[str, Any]:
    from jclprof.harness.registry import load_catalog

    return load_catalog(PROJECT_ROOT / "specs" / "diagnostic-catalog.yaml")

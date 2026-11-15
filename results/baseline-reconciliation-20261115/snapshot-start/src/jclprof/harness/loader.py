"""H-01 Golden Loader: reads case files, validates them by JSON Schema and by semantic checks.

Invalid definitions are reported as LoadError (never silently skipped); the CLI rejects the suite.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from jclprof.harness.registry import RuleRegistry

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "specs" / "golden-schema.json"
CORPUS_SCHEME = "corpus://"

STAGE_VIEWS: dict[str, set[str]] = {
    "lexical": {"lexical", "none"},
    "syntactic": {"statements", "none"},
    "semantic": {"exec_conditions", "dd_resources", "none"},
    "resolution": {"substitutions", "effective_statements", "none"},
}


@dataclass(frozen=True)
class LoadError:
    file: str
    test_id: str | None
    message: str


@dataclass(frozen=True)
class GoldenCase:
    raw: dict[str, Any]
    file: Path
    suite_dir: Path

    @property
    def test_id(self) -> str:
        return str(self.raw["test_id"])

    @property
    def category(self) -> str:
        return str(self.raw["category"])

    @property
    def rule_ids(self) -> list[str]:
        return list(self.raw["rule_ids"])

    @property
    def input_file(self) -> str:
        return str(self.raw["input_file"])

    @property
    def is_corpus_input(self) -> bool:
        return self.input_file.startswith(CORPUS_SCHEME)

    @property
    def input_path(self) -> Path:
        """Path of a suite-local input. Corpus inputs are resolved by the runner instead."""
        if self.is_corpus_input:
            raise ValueError(f"{self.test_id}: corpus input must be resolved via corpus roots")
        return self.suite_dir / self.input_file

    def resolve_input(self, corpus_roots: dict[str, Path]) -> Path | None:
        if not self.is_corpus_input:
            return self.input_path
        root_id, _, rel = self.input_file[len(CORPUS_SCHEME):].partition("/")
        root = corpus_roots.get(root_id)
        return None if root is None else Path(root) / rel

    @property
    def stage(self) -> str:
        return str(self.raw["validation_stage"])

    @property
    def review_status(self) -> str:
        return str(self.raw["review_status"])

    @property
    def scope(self) -> tuple[int, int] | None:
        s = self.raw.get("scope")
        return (int(s["lines"][0]), int(s["lines"][1])) if s else None


@dataclass
class LoadResult:
    cases: list[GoldenCase] = field(default_factory=list)
    errors: list[LoadError] = field(default_factory=list)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_document(doc: Any) -> list[str]:
    return sorted(
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in _validator().iter_errors(doc)
    )


def _record_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _semantic_checks(c: dict[str, Any], file_category: str, suite: Path,
                     registry: RuleRegistry, catalog: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if c["category"] != file_category:
        errs.append(f"category {c['category']} does not match file category {file_category}")
    unknown = [r for r in c["rule_ids"] if r not in registry.rules]
    errs += [f"unknown rule id {r}" for r in unknown]
    if not unknown:
        refs = {r["rule_id"]: r for r in c["source_reference"]}
        if set(refs) != set(c["rule_ids"]):
            errs.append("source_reference must have exactly one entry per rule_id")
        for rid, ref in refs.items():
            if rid in registry.rules and ref != registry.source_reference(rid):
                errs.append(f"source_reference for {rid} does not match specs/rules.yaml")
        statuses = {registry.rules[r].status for r in c["rule_ids"]}
        if c["review_status"] in ("reviewed", "approved"):
            weak = [r for r in c["rule_ids"]
                    if registry.rules[r].status in ("PENDING", "CROSS-CHECKED")]
            if weak:
                errs.append(f"rules {weak} are PENDING/CROSS-CHECKED: "
                            "case must be draft or blocked")
            if "VERIFIED" not in statuses:
                errs.append("reviewed/approved case needs at least one VERIFIED IBM rule")
    if c["input_file"].startswith(CORPUS_SCHEME):
        cs: dict[str, Any] = c.get("corpus_source") or {}
        expected_ref = f"{CORPUS_SCHEME}{cs['root_id']}/{cs['rel_path']}" if cs else None
        if c["input_file"] != expected_ref:
            errs.append("corpus:// input_file requires a matching corpus_source")
        elif "scope" in c and not (cs["lines"][0] <= c["scope"]["lines"][0]
                                   <= c["scope"]["lines"][1] <= cs["lines"][1]):
            errs.append("scope must lie within corpus_source.lines")
    elif not (suite / c["input_file"]).is_file():
        errs.append(f"input_file not found: {c['input_file']}")
    elif "scope" in c:
        inp = suite / c["input_file"]
        lo, hi = c["scope"]["lines"]
        n = _record_count(inp)
        if not (1 <= lo <= hi <= n):
            errs.append(f"scope {lo}-{hi} outside input ({n} records)")
    for d in c["expected_diagnostics"]["items"]:
        spec = catalog.get(d["code"])
        if spec is None:
            errs.append(f"unknown diagnostic code {d['code']}")
        elif spec.get("deprecated"):
            errs.append(f"{d['code']} is deprecated (use {spec.get('replaced_by')})")
        elif spec["severity"] != d["severity"]:
            errs.append(f"{d['code']}: severity {d['severity']} != catalog {spec['severity']}")
    view = c["expected_structure"]["view"]
    if view not in STAGE_VIEWS[c["validation_stage"]]:
        errs.append(f"view {view!r} is not valid for stage {c['validation_stage']!r}")
    for ds in c.get("environment", {}).get("datasets", []):
        if not (suite / ds["path"]).is_dir():
            errs.append(f"environment library not found: {ds['path']}")
    return errs


def load_suite(suite_dir: Path, registry: RuleRegistry, catalog: dict[str, Any]) -> LoadResult:
    suite_dir = Path(suite_dir)
    res = LoadResult()
    seen: dict[str, str] = {}
    for f in sorted((suite_dir / "cases").glob("*.yaml")):
        rel = f.relative_to(suite_dir).as_posix()
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            res.errors.append(LoadError(rel, None, f"invalid YAML: {e}"))
            continue
        schema_errs = validate_document(doc)
        if schema_errs:
            res.errors += [LoadError(rel, None, f"schema: {m}") for m in schema_errs]
            continue
        for c in doc["cases"]:
            tid = c["test_id"]
            errs = _semantic_checks(c, doc["category"], suite_dir, registry, catalog)
            if tid in seen:
                errs.append(f"duplicate test_id (also in {seen[tid]})")
            seen.setdefault(tid, rel)
            if errs:
                res.errors += [LoadError(rel, tid, m) for m in errs]
            else:
                res.cases.append(GoldenCase(c, f, suite_dir))
    res.cases.sort(key=lambda c: c.test_id)
    return res

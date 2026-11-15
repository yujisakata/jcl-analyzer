"""Profiler configuration (schema version 1). Strictly validated; unknown keys are errors.

See config/profiler.yaml and ADR-002 / ADR-004 / ADR-006.
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

RESERVED_ASSET_TYPES = frozenset({"UNKNOWN"})
RESERVED_RULE_IDS = frozenset({"SYMLINK"})
_ID_RE = re.compile(r"\A[A-Za-z0-9_.-]{1,64}\Z")


class ConfigError(ValueError):
    """Invalid configuration or unsafe run parameters (CLI exit code 2)."""


@dataclass(frozen=True)
class Root:
    id: str
    path: Path


@dataclass(frozen=True)
class AssetType:
    name: str
    member_like: bool
    fixed_record_length: int | None = None
    description: str = ""
    encoding_profile: str | None = None


@dataclass(frozen=True)
class DatasetMapping:
    """Explicit DSN -> local folder mapping (ADR-010). Never derived from the DSN itself."""

    dsn: str
    root: str
    path: str
    organization: str  # PDS | SEQ
    member_suffixes: tuple[str, ...] = ()
    aliases: dict[str, str] = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True)
class ClassificationRule:
    id: str
    pattern: str
    asset_type: str


@dataclass(frozen=True)
class ExcludeRule:
    id: str
    pattern: str
    reason: str


@dataclass(frozen=True)
class EncodingOverride:
    pattern: str
    encoding: str | None  # None = undetermined (ADR-009)


@dataclass(frozen=True)
class ProfilerConfig:
    roots: tuple[Root, ...]
    default_encoding: str
    encoding_overrides: tuple[EncodingOverride, ...]
    max_decode_bytes: int
    follow_symlinks: bool
    exclude: tuple[ExcludeRule, ...]
    asset_types: dict[str, AssetType]
    classification: tuple[ClassificationRule, ...]
    version: int = 1
    source_path: Path | None = field(default=None, compare=False)
    encoding_profiles: dict[str, str | None] = field(default_factory=dict)
    datasets: tuple[DatasetMapping, ...] = ()
    roots_source: str = "config"  # config | positional (ADR-013)
    jes: str = "UNKNOWN"  # JES2 | JES3 | UNKNOWN (ADR-021); never assumed

    def dataset(self, dsn: str) -> DatasetMapping | None:
        return next((d for d in self.datasets if d.dsn == dsn), None)


def _keys(
    obj: Any, where: str, required: set[str], optional: frozenset[str] | set[str] = frozenset()
) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise ConfigError(f"{where}: expected a mapping, got {type(obj).__name__}")
    keys = set(obj)
    missing = required - keys
    unknown = keys - required - set(optional)
    if missing:
        raise ConfigError(f"{where}: missing key(s) {sorted(missing)}")
    if unknown:
        raise ConfigError(f"{where}: unknown key(s) {sorted(unknown)}")
    return obj


def _list(obj: Any, where: str) -> list[Any]:
    if not isinstance(obj, list):
        raise ConfigError(f"{where}: expected a list")
    return obj


def _id(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise ConfigError(f"{where}: invalid id {value!r}")
    return value


def _str(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{where}: expected a non-empty string")
    return value


def _encoding(value: Any, where: str) -> str:
    name = _str(value, where)
    try:
        codecs.lookup(name)
    except LookupError as e:
        raise ConfigError(f"{where}: unknown encoding {name!r}") from e
    return name


def config_from_dict(
    data: Any, *, base_dir: Path, source_path: Path | None = None
) -> ProfilerConfig:
    top = _keys(
        data,
        "config",
        {"version", "roots", "asset_types", "classification"},
        {"encoding", "limits", "follow_symlinks", "exclude", "datasets", "environment"},
    )
    if top["version"] != 1:
        raise ConfigError(f"config: unsupported version {top['version']!r} (expected 1)")

    roots: list[Root] = []
    for i, r in enumerate(_list(top["roots"], "roots")):
        rr = _keys(r, f"roots[{i}]", {"id", "path"})
        p = Path(_str(rr["path"], f"roots[{i}].path"))
        if not p.is_absolute():
            p = base_dir / p
        roots.append(Root(_id(rr["id"], f"roots[{i}].id"), p.resolve()))
    if not roots:
        raise ConfigError("roots: at least one root is required")
    if len({r.id for r in roots}) != len(roots):
        raise ConfigError("roots: duplicate root id")

    enc = _keys(top.get("encoding", {"default": "utf-8"}), "encoding", {"default"},
                {"overrides", "profiles"})
    default_encoding = _encoding(enc["default"], "encoding.default")
    profiles_raw = enc.get("profiles", {})
    if not isinstance(profiles_raw, dict):
        raise ConfigError("encoding.profiles: expected a mapping")
    profiles: dict[str, str | None] = {
        _id(k, "encoding.profiles"): _opt_encoding(v, f"encoding.profiles.{k}")
        for k, v in profiles_raw.items()
    }
    overrides_list: list[EncodingOverride] = []
    for i, x in enumerate(_list(enc.get("overrides", []), "encoding.overrides")):
        o = _keys(x, f"encoding.overrides[{i}]", {"pattern", "encoding"})
        overrides_list.append(EncodingOverride(
            _str(o["pattern"], f"encoding.overrides[{i}].pattern"),
            _opt_encoding(o["encoding"], f"encoding.overrides[{i}].encoding"),
        ))
    overrides = tuple(overrides_list)

    limits = _keys(top.get("limits", {}), "limits", set(), {"max_decode_bytes"})
    max_decode = limits.get("max_decode_bytes", 16 * 1024 * 1024)
    if not isinstance(max_decode, int) or isinstance(max_decode, bool) or max_decode < 0:
        raise ConfigError("limits.max_decode_bytes: expected a non-negative integer")

    follow = top.get("follow_symlinks", False)
    if not isinstance(follow, bool):
        raise ConfigError("follow_symlinks: expected a boolean")
    if follow:
        raise ConfigError("follow_symlinks: true is not supported in schema version 1")

    asset_types: dict[str, AssetType] = {}
    at_raw = top["asset_types"]
    if not isinstance(at_raw, dict) or not at_raw:
        raise ConfigError("asset_types: expected a non-empty mapping")
    for name, spec in at_raw.items():
        name = _id(name, "asset_types")
        if name in RESERVED_ASSET_TYPES:
            raise ConfigError(f"asset_types: {name} is reserved")
        s = _keys(spec, f"asset_types.{name}", {"member_like"},
                  {"fixed_record_length", "description", "encoding_profile"})
        if not isinstance(s["member_like"], bool):
            raise ConfigError(f"asset_types.{name}.member_like: expected a boolean")
        frl = s.get("fixed_record_length")
        if frl is not None and (not isinstance(frl, int) or isinstance(frl, bool) or frl <= 0):
            raise ConfigError(f"asset_types.{name}.fixed_record_length: expected positive int")
        prof = s.get("encoding_profile")
        if prof is not None and prof not in profiles:
            raise ConfigError(f"asset_types.{name}.encoding_profile: unknown profile {prof!r}")
        asset_types[name] = AssetType(name, s["member_like"], frl,
                                      str(s.get("description", "")), prof)

    rules: list[ClassificationRule] = []
    for i, r in enumerate(_list(top["classification"], "classification")):
        rr = _keys(r, f"classification[{i}]", {"id", "pattern", "asset_type"})
        at = rr["asset_type"]
        if at not in asset_types:
            raise ConfigError(f"classification[{i}]: unknown asset_type {at!r}")
        rules.append(ClassificationRule(
            _id(rr["id"], f"classification[{i}].id"),
            _str(rr["pattern"], f"classification[{i}].pattern"),
            at,
        ))

    excludes: list[ExcludeRule] = []
    for i, r in enumerate(_list(top.get("exclude", []), "exclude")):
        rr = _keys(r, f"exclude[{i}]", {"id", "pattern", "reason"})
        rid = _id(rr["id"], f"exclude[{i}].id")
        if rid in RESERVED_RULE_IDS:
            raise ConfigError(f"exclude[{i}]: rule id {rid} is reserved")
        excludes.append(ExcludeRule(rid, _str(rr["pattern"], f"exclude[{i}].pattern"),
                                    _str(rr["reason"], f"exclude[{i}].reason")))

    all_ids = [r.id for r in rules] + [e.id for e in excludes]
    if len(set(all_ids)) != len(all_ids):
        raise ConfigError("classification/exclude: duplicate rule id")

    env = _keys(top.get("environment", {}), "environment", set(), {"jes"})
    jes = env.get("jes", "UNKNOWN")
    if jes not in ("JES2", "JES3", "UNKNOWN"):
        raise ConfigError("environment.jes: expected JES2, JES3 or UNKNOWN")

    root_ids = {r.id for r in roots}
    datasets: list[DatasetMapping] = []
    for i, x in enumerate(_list(top.get("datasets", []), "datasets")):
        datasets.append(_dataset(x, f"datasets[{i}]", root_ids))
    if len({d.dsn for d in datasets}) != len(datasets):
        raise ConfigError("datasets: duplicate dsn")

    return ProfilerConfig(
        roots=tuple(roots),
        default_encoding=default_encoding,
        encoding_overrides=overrides,
        max_decode_bytes=max_decode,
        follow_symlinks=follow,
        exclude=tuple(excludes),
        asset_types=asset_types,
        classification=tuple(rules),
        version=1,
        source_path=source_path,
        encoding_profiles=profiles,
        datasets=tuple(datasets),
        jes=jes,
    )


# DSN text as written in JCL: uppercase qualifiers separated by '.', no symbol resolution here.
# Full IBM data set name rules are registered for Step 3 (rule registry); this check is
# deliberately structural only.
_DSN_TEXT_RE = re.compile(r"\A[A-Z0-9@#$-]+(?:\.[A-Z0-9@#$-]+)*\Z")
_MEMBER_KEY_RE = re.compile(r"\A[A-Z@#$][A-Z0-9@#$]{0,7}\Z")


def _dataset(x: Any, where: str, root_ids: set[str]) -> DatasetMapping:
    d = _keys(x, where, {"dsn", "root", "path", "organization"},
              {"member_suffixes", "aliases", "note"})
    dsn = _str(d["dsn"], f"{where}.dsn")
    if not _DSN_TEXT_RE.match(dsn):
        raise ConfigError(f"{where}.dsn: expected uppercase dotted name, got {dsn!r}")
    root = _str(d["root"], f"{where}.root")
    if root not in root_ids:
        raise ConfigError(f"{where}.root: unknown root id {root!r}")
    path = _str(d["path"], f"{where}.path").replace("\\", "/")
    if path.startswith("/") or re.match(r"\A[A-Za-z]:", path) or ".." in path.split("/"):
        raise ConfigError(f"{where}.path: must be a relative path inside the root")
    org = d["organization"]
    if org not in ("PDS", "SEQ"):
        raise ConfigError(f"{where}.organization: expected PDS or SEQ")
    suffixes = tuple(_str(s, f"{where}.member_suffixes")
                     for s in _list(d.get("member_suffixes", []), f"{where}.member_suffixes"))
    aliases_raw = d.get("aliases", {})
    if not isinstance(aliases_raw, dict):
        raise ConfigError(f"{where}.aliases: expected a mapping")
    aliases: dict[str, str] = {}
    for k, v in aliases_raw.items():
        if not (isinstance(k, str) and _MEMBER_KEY_RE.match(k)
                and isinstance(v, str) and _MEMBER_KEY_RE.match(v)):
            raise ConfigError(f"{where}.aliases: invalid alias {k!r} -> {v!r}")
        aliases[k] = v
    return DatasetMapping(dsn, root, path, org, suffixes, aliases, str(d.get("note", "")))


def _opt_encoding(value: Any, where: str) -> str | None:
    return None if value is None else _encoding(value, where)


def apply_cli_roots(cfg: ProfilerConfig, paths: list[str], cwd: Path) -> ProfilerConfig:
    """ADR-013: positional targets replace config roots; matching paths keep their root id."""
    if not paths:
        return cfg
    by_path = {r.path: r.id for r in cfg.roots}
    roots: list[Root] = []
    for n, raw in enumerate(paths, start=1):
        p = Path(raw)
        p = (p if p.is_absolute() else cwd / p).resolve()
        if not p.is_dir():
            raise ConfigError(f"analysis target is not an existing directory: {raw}")
        if any(r.path == p for r in roots):
            raise ConfigError(f"analysis target given more than once: {raw}")
        roots.append(Root(by_path.get(p, f"arg{n}"), p))
    if len({r.id for r in roots}) != len(roots):
        raise ConfigError("analysis targets produce duplicate root ids")
    return replace(cfg, roots=tuple(roots), roots_source="positional")


def load_config(path: Path) -> ProfilerConfig:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"cannot read config {path}: {e}") from e
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid YAML in {path}: {e}") from e
    return config_from_dict(data, base_dir=path.resolve().parent, source_path=path.resolve())


def validate_roots_exist(cfg: ProfilerConfig) -> None:
    for r in cfg.roots:
        if not r.path.is_dir():
            raise ConfigError(f"root {r.id!r} is not an existing directory: {r.path}")


def validate_output_dir(cfg: ProfilerConfig, output: Path) -> Path:
    """Refuse any output location that overlaps an input root (ADR-006)."""
    out = Path(output).resolve()
    for r in cfg.roots:
        if out == r.path or r.path in out.parents:
            raise ConfigError(f"output {out} is inside input root {r.id!r} ({r.path}); refused")
        if out in r.path.parents:
            raise ConfigError(f"output {out} contains input root {r.id!r} ({r.path}); refused")
    return out

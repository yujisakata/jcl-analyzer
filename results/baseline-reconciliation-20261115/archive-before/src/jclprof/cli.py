"""Command-line interface. Exit codes (ADR-008): 0 ok, 1 completed with errors / check failed,
2 configuration, argument or safety violation (nothing executed)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from jclprof import __version__
from jclprof.context.config import (
    ConfigError,
    ProfilerConfig,
    apply_cli_roots,
    load_config,
    validate_output_dir,
    validate_roots_exist,
)
from jclprof.envcheck import run_envcheck
from jclprof.inventory.collector import collect
from jclprof.inventory.writers import write_outputs, write_run_meta

EXIT_OK, EXIT_ERRORS, EXIT_CONFIG = 0, 1, 2
DEFAULT_CONFIG = "config/profiler.yaml"


def _load(args: argparse.Namespace) -> ProfilerConfig:
    """ADR-013: config file (default config/profiler.yaml) + optional positional targets."""
    cfg = load_config(Path(args.config))
    return apply_cli_roots(cfg, list(args.targets), Path.cwd())


def _cmd_envcheck(args: argparse.Namespace) -> int:
    try:
        cfg = _load(args)
        out = validate_output_dir(cfg, Path(args.output)) if args.output else None
    except ConfigError as e:
        print(f"jclprof: config error: {e}", file=sys.stderr)
        return EXIT_CONFIG
    rep = run_envcheck(cfg)
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        rep_out = dict(rep, checked_at=datetime.now(UTC).isoformat(timespec="seconds"))
        (out / "envcheck.json").write_text(
            json.dumps(rep_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"python {rep['python']['version']} (required {rep['python']['required']}): "
          f"{'OK' if rep['python']['ok'] else 'NG'}")
    for name, p in rep["packages"].items():
        print(f"package {name}: {p['version'] if p['installed'] else 'MISSING'}")
    for r in rep["roots"]:
        print(f"root {r['id']}: exists={r['exists']} files={r['file_count']} "
              f"readable={r['readable_count']} unreadable={len(r['unreadable'])} "
              f"bytes={r['total_bytes']}")
    print("envcheck:", "OK" if rep["ok"] else "FAILED")
    return EXIT_OK if rep["ok"] else EXIT_ERRORS


def _cmd_inventory(args: argparse.Namespace) -> int:
    started = datetime.now(UTC)
    t0 = time.perf_counter()
    try:
        cfg = _load(args)
        validate_roots_exist(cfg)
        out = validate_output_dir(cfg, Path(args.output))
    except ConfigError as e:
        print(f"jclprof: config error: {e}", file=sys.stderr)
        return EXIT_CONFIG
    res = collect(cfg)
    write_outputs(res, out)
    s = res.summary()
    write_run_meta(out, {
        "command": "inventory",
        "started_at": started.isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.perf_counter() - t0, 3),
        "config": cfg.source_path.as_posix() if cfg.source_path else None,
        "roots_source": cfg.roots_source,
        "roots": [{"id": r.id, "path": r.path.as_posix()} for r in cfg.roots],
        "output": out.as_posix(),
        "summary": s,
    })
    print(f"files seen={s['files_seen']} registered={s['files_registered']} "
          f"excluded={s['files_excluded']} bytes={s['total_bytes']}")
    for k, v in s["asset_type_counts"].items():
        print(f"  {k}: {v}")
    print(f"diagnostics: {s['diagnostic_counts'] or 'none'}")
    print(f"output: {out}")
    return EXIT_ERRORS if res.has_errors() else EXIT_OK


def _harness_paths() -> tuple[Path, Path, Path]:
    from jclprof.harness.loader import SCHEMA_PATH

    root = SCHEMA_PATH.parents[1]
    return root, root / "specs" / "rules.yaml", root / "specs" / "diagnostic-catalog.yaml"


def _load_golden(suite: Path):  # type: ignore[no-untyped-def]
    from jclprof.harness.loader import load_suite
    from jclprof.harness.registry import load_catalog, load_rules

    _, rules_p, cat_p = _harness_paths()
    registry = load_rules(rules_p)
    res = load_suite(suite, registry, load_catalog(cat_p))
    for e in res.errors:
        print(f"golden: {e.file} {e.test_id or ''}: {e.message}", file=sys.stderr)
    return registry, res


def _cmd_golden_check(args: argparse.Namespace) -> int:
    from jclprof.harness.integrity import check_integrity

    suite = Path(args.suite)
    _, res = _load_golden(suite)
    if res.errors:
        print(f"golden definitions: {len(res.errors)} error(s); suite rejected")
        return EXIT_CONFIG
    print(f"golden definitions: {len(res.cases)} case(s) valid")
    rep = check_integrity(suite)
    if not rep.ok or rep.approved_violations:
        print(f"golden integrity: CHANGED ({rep.summary()})")
        for m in rep.modified:
            print(m.diff)
        return EXIT_ERRORS
    print("golden integrity: OK (matches MANIFEST.json)")
    return EXIT_OK


def _cmd_golden_seal(args: argparse.Namespace) -> int:
    from jclprof.harness.integrity import seal

    suite = Path(args.suite)
    _, res = _load_golden(suite)
    if res.errors:
        print("refusing to seal: golden definitions are invalid", file=sys.stderr)
        return EXIT_CONFIG
    out = seal(suite, sealed_by=args.by)
    print(f"sealed {len(res.cases)} case(s) -> {out}")
    return EXIT_OK


def _cmd_verify(args: argparse.Namespace) -> int:
    from jclprof.harness.adapters import registered_adapters
    from jclprof.harness.runner import run_suite, write_report

    suite = Path(args.suite)
    _, res = _load_golden(suite)
    if res.errors:
        return EXIT_CONFIG
    corpus: dict[str, Path] = {}
    try:
        cfg = load_config(Path(args.config))
        corpus = {r.id: r.path for r in cfg.roots}
    except ConfigError as e:
        print(f"jclprof: corpus roots unavailable ({e}); corpus cases will be BLOCKED",
              file=sys.stderr)
    rep = run_suite(res.cases, adapters=registered_adapters(), corpus_roots=corpus)
    write_report(rep, Path(args.output))
    for k, v in rep.counts().items():
        print(f"{k}: {v}")
    print(f"report: {Path(args.output) / 'golden_run.md'}")
    return EXIT_ERRORS if rep.counts()["FAILED"] else EXIT_OK


def _cmd_rules_render(args: argparse.Namespace) -> int:
    from jclprof.harness.render import render_reference

    root, _, _ = _harness_paths()
    registry, res = _load_golden(Path(args.suite))
    if res.errors:
        return EXIT_CONFIG
    text = render_reference(registry, res.cases)
    target = root / "specs" / "ibm-jcl-reference.md"
    if args.check:
        same = target.is_file() and target.read_text(encoding="utf-8") == text
        print("rules reference:", "in sync" if same else "OUT OF SYNC (run jclprof rules-render)")
        return EXIT_OK if same else EXIT_ERRORS
    target.write_text(text, encoding="utf-8", newline=chr(10))
    print(f"wrote {target}")
    return EXIT_OK


def _cmd_parse(args: argparse.Namespace) -> int:
    """Parse JCL files and write one AST JSON per file (Step 4b; read-only on inputs)."""
    from jclprof.parser import parse_file

    try:
        cfg = load_config(Path(args.config))
    except ConfigError as e:
        print(f"jclprof: config error: {e}", file=sys.stderr)
        return EXIT_CONFIG
    jes = args.jes or cfg.jes
    out = Path(args.output)
    for r in cfg.roots:
        if out.resolve() == r.path or r.path in out.resolve().parents:
            print(f"jclprof: output {out} is inside input root {r.id}; refused", file=sys.stderr)
            return EXIT_CONFIG
    out.mkdir(parents=True, exist_ok=True)
    errors = 0
    for f in args.files:
        path = Path(f)
        kind = args.input_kind
        if kind == "auto":
            kind = "proc_member" if path.suffix.lower() in (".prc", ".proc") else "job"
        res = parse_file(path, encoding=args.encoding, jes=jes, input_kind=kind)
        target = out / (path.name + ".ast.json")
        target.write_text(json.dumps(res.to_dict(), ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        n_err = sum(1 for d in res.diagnostics if d.severity == "ERROR")
        errors += n_err
        print(f"{path.name}: jobs={len(res.jobs)} statements={len(res.statements)} "
              f"diagnostics={len(res.diagnostics)} errors={n_err} -> {target}")
    return EXIT_ERRORS if errors else EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jclprof", description="Static JCL profiler")
    p.add_argument("--version", action="version", version=f"jclprof {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("envcheck", help="check environment and read access to input roots")
    e.add_argument("targets", nargs="*", metavar="PATH",
                   help="analysis target directories (override config roots)")
    e.add_argument("--config", default=DEFAULT_CONFIG,
                   help=f"profiler config (default: {DEFAULT_CONFIG})")
    e.add_argument("--output", help="directory for envcheck.json (optional)")
    e.set_defaults(func=_cmd_envcheck)

    i = sub.add_parser("inventory", help="register every asset under the configured roots")
    i.add_argument("targets", nargs="*", metavar="PATH",
                   help="analysis target directories (override config roots)")
    i.add_argument("--config", default=DEFAULT_CONFIG,
                   help=f"profiler config (default: {DEFAULT_CONFIG})")
    i.add_argument("--output", required=True)
    i.set_defaults(func=_cmd_inventory)

    g = sub.add_parser("golden-check", help="validate Golden definitions and integrity")
    g.add_argument("--suite", default="tests/golden")
    g.set_defaults(func=_cmd_golden_check)

    s = sub.add_parser("golden-seal", help="record reviewed Golden files in MANIFEST.json (manual)")
    s.add_argument("--suite", default="tests/golden")
    s.add_argument("--by", required=True, help="name of the person sealing the suite")
    s.set_defaults(func=_cmd_golden_seal)

    v = sub.add_parser("verify", help="run the Golden suite against registered analyzer adapters")
    v.add_argument("--suite", default="tests/golden")
    v.add_argument("--config", default=DEFAULT_CONFIG)
    v.add_argument("--output", default="results/harness")
    v.set_defaults(func=_cmd_verify)

    pa = sub.add_parser("parse", help="parse JCL files into AST JSON (Step 4b)")
    pa.add_argument("files", nargs="+", metavar="FILE")
    pa.add_argument("--config", default=DEFAULT_CONFIG)
    pa.add_argument("--encoding", default="utf-8")
    pa.add_argument("--jes", choices=["JES2", "JES3", "UNKNOWN"],
                    help="override environment.jes from the config")
    pa.add_argument("--input-kind", choices=["auto", "job", "proc_member"], default="auto")
    pa.add_argument("--output", required=True)
    pa.set_defaults(func=_cmd_parse)

    r = sub.add_parser("rules-render", help="generate specs/ibm-jcl-reference.md")
    r.add_argument("--suite", default="tests/golden")
    r.add_argument("--check", action="store_true", help="only check that the file is in sync")
    r.set_defaults(func=_cmd_rules_render)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rc: int = args.func(args)
    return rc

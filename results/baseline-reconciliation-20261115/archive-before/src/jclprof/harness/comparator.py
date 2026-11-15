"""H-02 Golden Comparator (docs/golden-view.md).

Structural comparison of an expected Golden View with an adapter's actual view.
Non-essential differences that are tolerated -- and ONLY these:
  * keys in IGNORED_KEYS (ids, timestamps) on the actual side
  * order of keyword parameters (compared as a multiset, duplicates preserved; JCL-FMT-004)
  * operator spelling aliases in IF conditions (JCL-IF-002)
Everything else is significant. Attributes produced by the adapter but not specified in the
expected value are reported as `unchecked` (visible, not silently ignored).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

IGNORED_KEYS = frozenset({"id", "node_id", "diag_id", "source_id", "timestamp", "generated_at",
                          "elapsed"})

OP_ALIASES = {
    ">": "GT", "<": "LT", "¬>": "NG", "¬<": "NL", "=": "EQ", "¬=": "NE", ">=": "GE", "<=": "LE",
    "&": "AND", "|": "OR", "¬": "NOT",
}

VIEW_LIST_KEYS = {
    "statements": "statements", "exec_conditions": "exec_conditions",
    "dd_resources": "dd_resources", "substitutions": "substitutions",
    "effective_statements": "effective_statements",
}


@dataclass(frozen=True)
class Difference:
    path: str
    kind: str  # mismatch | missing | unexpected | invalid_expected
    expected: Any = None
    actual: Any = None


@dataclass
class Comparison:
    differences: list[Difference] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.differences


def _strip_ignored(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _strip_ignored(x) for k, x in v.items() if k not in IGNORED_KEYS}
    if isinstance(v, list):
        return [_strip_ignored(x) for x in v]
    return v


def _contains_ignored(v: Any) -> str | None:
    if isinstance(v, dict):
        for k, x in v.items():
            if k in IGNORED_KEYS:
                return str(k)
            found = _contains_ignored(x)
            if found:
                return found
    elif isinstance(v, list):
        for x in v:
            found = _contains_ignored(x)
            if found:
                return found
    return None


def _norm_cond(c: Any) -> Any:
    if isinstance(c, dict):
        out = {k: _norm_cond(v) for k, v in c.items()}
        if isinstance(out.get("op"), str):
            out["op"] = OP_ALIASES.get(out["op"], out["op"].upper())
        return out
    if isinstance(c, list):
        return [_norm_cond(x) for x in c]
    return c


def _canon(v: Any) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def _cmp_value(path: str, exp: Any, act: Any, out: list[Difference]) -> None:
    if _canon(exp) != _canon(act):
        out.append(Difference(path, "mismatch", exp, act))


def _cmp_keywords(path: str, exp: list[Any], act: Any, out: list[Difference]) -> None:
    if not isinstance(act, list):
        out.append(Difference(path, "mismatch", exp, act))
        return
    e, a = Counter(_canon(x) for x in exp), Counter(_canon(x) for x in act)
    for k in sorted((e - a).elements()):
        out.append(Difference(path, "missing", json.loads(k), None))
    for k in sorted((a - e).elements()):
        out.append(Difference(path, "unexpected", None, json.loads(k)))


def _cmp_statement(path: str, exp: dict[str, Any], act: dict[str, Any], out: list[Difference],
                   unchecked: list[str], ignore_spans: bool) -> None:
    for key, ev in exp.items():
        if key == "span" and ignore_spans:
            continue
        if key not in act:
            out.append(Difference(f"{path}.{key}", "missing", ev, None))
        elif key == "keywords":
            _cmp_keywords(f"{path}.keywords", ev, act[key], out)
        elif key == "condition":
            _cmp_value(f"{path}.condition", _norm_cond(ev), _norm_cond(act[key]), out)
        else:
            _cmp_value(f"{path}.{key}", ev, act[key], out)
    for key in act:
        if key not in exp and not (key == "span" and ignore_spans):
            unchecked.append(f"{path}.{key}")


def _in_scope(span: Any, scope: tuple[int, int] | None) -> bool:
    if scope is None:
        return True
    if not isinstance(span, list) or len(span) != 2:
        return False
    return bool(scope[0] <= span[0] and span[1] <= scope[1])


def compare_structure(expected: dict[str, Any], actual: dict[str, Any], *,
                      scope: tuple[int, int] | None = None, ignore_spans: bool = False,
                      ignore_kinds: frozenset[str] | set[str] = frozenset()) -> Comparison:
    res = Comparison()
    bad = _contains_ignored(expected)
    if bad:
        res.differences.append(Difference(bad, "invalid_expected", "non-essential key in expected"))
        return res
    act = _strip_ignored(actual)
    view = expected.get("view")
    if view == "none":
        # No structure is asserted (reason recorded in the case); whatever the adapter produced
        # is reported as unchecked, never compared.
        if act.get("view") not in (None, "none"):
            res.unchecked.append("view")
        return res
    if view != act.get("view"):
        res.differences.append(Difference("view", "mismatch", view, act.get("view")))
        return res
    if view == "lexical":
        for key in ("records", "lexical_statements"):
            exp_l: list[Any] = list(expected.get(key, []))
            act_l: list[Any] = [x for x in act.get(key, []) if isinstance(x, dict)]
            if scope is not None:
                act_l = [x for x in act_l if _in_scope(x.get("span") or [x.get("line"),
                                                                         x.get("line")], scope)]
            for i, (e, a) in enumerate(zip(exp_l, act_l, strict=False)):
                _cmp_statement(f"{key}[{i}]", e, a, res.differences, res.unchecked, ignore_spans)
            for i in range(len(act_l), len(exp_l)):
                res.differences.append(Difference(f"{key}[{i}]", "missing", exp_l[i], None))
            for i in range(len(exp_l), len(act_l)):
                res.differences.append(Difference(f"{key}[{i}]", "unexpected", None, act_l[i]))
        return res
    key = VIEW_LIST_KEYS[str(view)]
    exp_items: list[Any] = list(expected.get(key, []))
    act_items: list[Any] = list(act.get(key, []))
    if view == "statements":
        def keep(s: Any, use_scope: bool) -> bool:
            if not isinstance(s, dict) or s.get("kind") in ignore_kinds:
                return False
            return not use_scope or _in_scope(s.get("span"), scope)

        exp_items = [s for s in exp_items if keep(s, False)]
        act_items = [s for s in act_items if keep(s, True)]
        for i, (e, a) in enumerate(zip(exp_items, act_items, strict=False)):
            if not isinstance(a, dict):
                res.differences.append(Difference(f"statements[{i}]", "mismatch", e, a))
                continue
            _cmp_statement(f"statements[{i}]", e, a, res.differences, res.unchecked, ignore_spans)
        for i in range(len(act_items), len(exp_items)):
            res.differences.append(Difference(f"statements[{i}]", "missing", exp_items[i], None))
        for i in range(len(exp_items), len(act_items)):
            res.differences.append(Difference(f"statements[{i}]", "unexpected", None, act_items[i]))
        if "blocks" in expected:
            _cmp_value("blocks", expected["blocks"], act.get("blocks"), res.differences)
        elif "blocks" in act:
            res.unchecked.append("blocks")
    else:
        if scope is not None:
            act_items = [x for x in act_items if isinstance(x, dict)
                         and isinstance(x.get("line"), int) and scope[0] <= x["line"] <= scope[1]]
        _cmp_value(key, exp_items, act_items, res.differences)
    return res


def _diag_key(d: dict[str, Any], with_column: bool) -> str:
    k = {"code": d.get("code"), "severity": d.get("severity"), "line": d.get("line"),
         "file": d.get("file")}
    if with_column:
        k["column"] = d.get("column")
    return _canon(k)


def compare_diagnostics(expected: list[dict[str, Any]], actual: list[dict[str, Any]], *,
                        scope: tuple[int, int] | None = None) -> Comparison:
    """Multiset comparison; extra actual diagnostics are differences (warnings are contract)."""
    res = Comparison()
    acts = [_strip_ignored(a) for a in actual]
    if scope is not None:
        acts = [a for a in acts if a.get("file") is None and isinstance(a.get("line"), int)
                and scope[0] <= a["line"] <= scope[1]]
    remaining = list(acts)
    for e in expected:
        with_col = "column" in e
        ek = _diag_key(e, with_col)
        match = next((a for a in remaining if _diag_key(a, with_col) == ek), None)
        if match is None:
            res.differences.append(Difference("diagnostics", "missing", e, None))
        else:
            remaining.remove(match)
    for a in remaining:
        res.differences.append(Difference("diagnostics", "unexpected", None, a))
    return res

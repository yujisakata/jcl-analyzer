"""H-02 Golden Comparator: structural comparison that ignores non-essential differences only."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from jclprof.harness.comparator import compare_diagnostics, compare_structure

EXPECTED: dict[str, Any] = {
    "view": "statements",
    "statements": [
        {"kind": "JOB", "span": [1, 1], "name": "J", "positional": [], "keywords": []},
        {"kind": "DD", "span": [2, 4], "name": "TRANSACT", "positional": [],
         "keywords": [["DISP", ["NEW", "CATLG", "DELETE"]], ["UNIT", "SYSDA"],
                      ["SPACE", ["CYL", ["1", "1"], "RLSE"]], ["DSN", "APP.SYSTRAN(+1)"]]},
    ],
}


def _actual() -> dict[str, Any]:
    a = copy.deepcopy(EXPECTED)
    # non-essential: ids/timestamps and keyword order
    a["generated_at"] = "2026-11-15T00:00:00Z"
    for i, s in enumerate(a["statements"]):
        s["node_id"] = f"N{i}"
        s["comment"] = None
    a["statements"][1]["keywords"].reverse()
    return a


def test_equal_modulo_ids_timestamps_keyword_order() -> None:
    r = compare_structure(EXPECTED, _actual())
    assert r.ok, r.differences
    # 'comment' was produced but not specified -> reported as unchecked, not silently dropped
    assert "statements[0].comment" in r.unchecked


def test_meaningful_difference_detected() -> None:
    a = _actual()
    a["statements"][1]["keywords"][0] = ["DSN", "APP.SYSTRAN(-1)"]  # generation sign flipped
    r = compare_structure(EXPECTED, a)
    assert not r.ok
    assert any("keywords" in d.path for d in r.differences)


def test_subparameter_order_is_significant() -> None:
    a = _actual()
    for kw in a["statements"][1]["keywords"]:
        if kw[0] == "DISP":
            kw[1] = ["NEW", "DELETE", "CATLG"]
    assert not compare_structure(EXPECTED, a).ok


def test_duplicate_keyword_not_collapsed() -> None:
    a = _actual()
    a["statements"][1]["keywords"].append(["UNIT", "SYSDA"])
    assert not compare_structure(EXPECTED, a).ok


def test_statement_count_and_kind() -> None:
    a = _actual()
    a["statements"].append({"kind": "NULL", "span": [5, 5]})
    assert not compare_structure(EXPECTED, a).ok
    b = _actual()
    b["statements"][1]["kind"] = "EXEC"
    assert not compare_structure(EXPECTED, b).ok


def test_span_difference_detected() -> None:
    a = _actual()
    a["statements"][1]["span"] = [2, 3]
    assert not compare_structure(EXPECTED, a).ok


def test_ignore_spans_option_for_metamorphic_use() -> None:
    a = _actual()
    a["statements"][1]["span"] = [7, 9]
    assert compare_structure(EXPECTED, a, ignore_spans=True).ok


def test_ignore_kinds_option() -> None:
    a = _actual()
    a["statements"].insert(1, {"kind": "COMMENT", "span": [2, 2], "comment": ["x"]})
    assert compare_structure(EXPECTED, a, ignore_kinds={"COMMENT"}, ignore_spans=True).ok


def test_condition_operator_aliases_normalized() -> None:
    exp: dict[str, Any] = {"view": "statements", "statements": [
        {"kind": "IF", "span": [1, 1], "condition": {
            "op": "OR", "args": [{"kw": "ABEND", "step": None, "procstep": None},
                                 {"op": "GT",
                                  "left": {"kw": "RC", "step": "STEP1", "procstep": None},
                                  "right": {"num": 8}}]}}]}
    act = copy.deepcopy(exp)
    act["statements"][0]["condition"]["op"] = "|"
    act["statements"][0]["condition"]["args"][1]["op"] = ">"
    assert compare_structure(exp, act).ok
    act["statements"][0]["condition"]["args"][1]["op"] = "<"
    assert not compare_structure(exp, act).ok


def test_scope_filters_statements_by_line_range() -> None:
    exp = {"view": "statements", "statements": [EXPECTED["statements"][1]]}
    r = compare_structure(exp, _actual(), scope=(2, 4))
    assert r.ok, r.differences


def test_ignored_key_in_expected_is_rejected() -> None:
    exp = copy.deepcopy(EXPECTED)
    exp["statements"][0]["node_id"] = "X"
    r = compare_structure(exp, _actual())
    assert not r.ok


def test_other_views_exact() -> None:
    exp: dict[str, Any] = {"view": "dd_resources", "dd_resources": [
        {"step": "S1", "ddname": "D", "concat_index": 0, "line": 3, "dsn": "A.B", "generation": 1,
         "disp": {"status": "NEW", "normal": "CATLG", "abnormal": "DELETE", "defaulted": []}}]}
    act = copy.deepcopy(exp)
    assert compare_structure(exp, act).ok
    act["dd_resources"][0]["generation"] = -1
    assert not compare_structure(exp, act).ok


def test_view_mismatch() -> None:
    assert not compare_structure(EXPECTED, {"view": "dd_resources", "dd_resources": []}).ok


def test_diagnostics_multiset_exact() -> None:
    exp = [{"code": "LEX-E002", "severity": "ERROR", "line": 2, "column": 3}]
    act = [{"code": "LEX-E002", "severity": "ERROR", "line": 2, "column": 3,
            "diag_id": "DIAG-1", "message": "no continuation found"}]
    assert compare_diagnostics(exp, act).ok
    # extra diagnostic -> failure (warnings are part of the contract)
    act2 = [*act, {"code": "PAR-W001", "severity": "WARNING", "line": 5}]
    assert not compare_diagnostics(exp, act2).ok
    # wrong line -> failure
    assert not compare_diagnostics(exp, [dict(act[0], line=3)]).ok
    # column compared only when expected specifies it
    assert compare_diagnostics([{"code": "LEX-E002", "severity": "ERROR", "line": 2}],
                               [dict(act[0], column=9)]).ok


def test_diagnostics_scope_and_file() -> None:
    exp = [{"code": "RES-E001", "severity": "ERROR", "line": 4}]
    act = [{"code": "RES-E001", "severity": "ERROR", "line": 4},
           {"code": "RES-W002", "severity": "WARNING", "line": 40}]
    assert compare_diagnostics(exp, act, scope=(1, 10)).ok
    assert not compare_diagnostics(exp, act).ok
    assert not compare_diagnostics(
        [{"code": "RES-E001", "severity": "ERROR", "line": 4, "file": "libs/a/X.jcl"}], act[:1]).ok


# ---- Step 4a: view none and lexical view
LEX_EXP: dict[str, Any] = {
    "view": "lexical",
    "records": [{"line": 1, "kind": "STATEMENT_START", "continues": "PARAMETER"},
                {"line": 2, "kind": "CONTINUATION"}],
    "lexical_statements": [{"span": [1, 2], "parameter_text": "A=1,B=2",
                            "tokens": [["WORD", "A"], ["EQUALS", "="]]}],
}


def _lex_act() -> dict[str, Any]:
    a = copy.deepcopy(LEX_EXP)
    a["records"][1]["continues"] = None
    a["records"][0]["raw"] = "//X DD A=1,"
    return a


def test_view_none_does_not_compare_structure() -> None:
    r = compare_structure({"view": "none", "reason": "x"}, _lex_act())
    assert r.ok and r.unchecked == ["view"]


def test_lexical_view_equal_with_unchecked_extras() -> None:
    r = compare_structure(LEX_EXP, _lex_act())
    assert r.ok, r.differences
    assert "records[0].raw" in r.unchecked


def test_lexical_view_detects_differences() -> None:
    mutations: list[Callable[[dict[str, Any]], object]] = [
        lambda a: a["records"][1].__setitem__("kind", "OTHER"),
        lambda a: a["records"][0].__setitem__("continues", "COMMENT"),
        lambda a: a["records"].pop(),
        lambda a: a["records"].append({"line": 3, "kind": "OTHER"}),
        lambda a: a["lexical_statements"][0].__setitem__("parameter_text", "A=1,B=3"),
        lambda a: a["lexical_statements"][0].__setitem__("tokens", [["WORD", "A"]]),
        lambda a: a["lexical_statements"][0].__setitem__("span", [1, 1]),
        lambda a: a["lexical_statements"].append({"span": [3, 3]}),
    ]
    for mutate in mutations:
        a = _lex_act()
        mutate(a)
        assert not compare_structure(LEX_EXP, a).ok

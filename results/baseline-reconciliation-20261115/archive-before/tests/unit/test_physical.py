"""Physical record statistics (rules JCL-REC-001/003/004). No JCL statement semantics."""

from __future__ import annotations

from jclprof.inventory.physical import compute_physical


def test_crlf() -> None:
    s = compute_physical("A\r\nB\r\n")
    assert (s.record_count, s.line_terminator, s.ends_with_terminator) == (2, "CRLF", True)
    assert s.max_record_length == 1


def test_lf_without_final_newline() -> None:
    s = compute_physical("A\nB")
    assert (s.record_count, s.line_terminator, s.ends_with_terminator) == (2, "LF", False)


def test_empty() -> None:
    s = compute_physical("")
    assert (s.record_count, s.line_terminator, s.ends_with_terminator) == (0, "NONE", False)
    assert s.max_record_length == 0


def test_single_record_no_terminator() -> None:
    s = compute_physical("ABC")
    assert (s.record_count, s.line_terminator, s.max_record_length) == (1, "NONE", 3)


def test_mixed_and_cr() -> None:
    assert compute_physical("A\r\nB\n").line_terminator == "MIXED"
    s = compute_physical("A\rB\r")
    assert (s.record_count, s.line_terminator) == (2, "CR")


def test_only_cr_lf_split_records() -> None:
    # str.splitlines() would also split on FF, NEL, U+2028 — records must not.
    s = compute_physical("A\x0cB\x85C\u2028D\n")
    assert s.record_count == 1
    assert s.max_record_length == 7


def test_prefix_histogram() -> None:
    lines = ["//* c", "//STEP1 EXEC PGM=X", "/*", "   ", "", "DATA", "/ *x", "//"]
    s = compute_physical("\n".join(lines) + "\n")
    assert s.prefix_counts == {
        "SLASH_SLASH_STAR": 1,
        "SLASH_SLASH": 2,
        "SLASH_STAR": 1,
        "BLANK": 2,
        "OTHER": 2,
    }
    assert sum(s.prefix_counts.values()) == s.record_count


def test_sequence_area() -> None:
    with_seq = "//X".ljust(72) + "00010000"
    blank_seq = "//Y".ljust(80)
    short = "//Z".ljust(72)
    s = compute_physical("\r\n".join([with_seq, blank_seq, short]) + "\r\n")
    assert s.seq_area_records == 1
    assert s.max_record_length == 80


def test_over_80_and_tabs_reported_with_line_numbers() -> None:
    text = "//A\n" + "X" * 81 + "\n//B\tC\n" + "Y" * 80 + "\n"
    s = compute_physical(text)
    assert s.over_80_lines == (2,)
    assert s.tab_lines == (3,)
    assert s.records_over_80 == 1

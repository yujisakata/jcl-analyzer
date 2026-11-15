"""Glob semantics used by classification/exclusion rules.

Supported: ``**`` (any number of path segments, including zero), ``*`` (within one segment),
``?`` (one non-separator character). Every other character is literal (no ``[]`` classes).
"""

from __future__ import annotations

import pytest

from jclprof.context.globmatch import glob_match


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("**/*.jcl", "jcl/A.jcl", True),
        ("**/*.jcl", "A.jcl", True),
        ("**/*.jcl", "a/b/c/A.JCL", True),
        ("**/*.jcl", "a/A.jcl.bak", False),
        ("**/data/**", "data/x.txt", True),
        ("**/data/**", "app/data/EBCDIC/X.PS", True),
        ("**/data/**", "database/x", False),
        ("**/data/**", "mydata/x", False),
        ("*.jcl", "jcl/A.jcl", False),
        ("*.jcl", "A.jcl", True),
        ("jcl/?.jcl", "jcl/A.jcl", True),
        ("jcl/?.jcl", "jcl/AB.jcl", False),
        ("jcl/?.jcl", "jcl//.jcl", False),
        ("**/.gitkeep", "data/EBCDIC/.gitkeep", True),
        ("a+b/*.x", "a+b/c.x", True),
        ("[ab].x", "[ab].x", True),
        ("[ab].x", "a.x", False),
        ("catlg/*.txt", "catlg/LISTCAT.txt", True),
        ("catlg/*.txt", "x/catlg/LISTCAT.txt", False),
    ],
)
def test_glob_match_case_insensitive(pattern: str, path: str, expected: bool) -> None:
    assert glob_match(pattern, path) is expected


def test_glob_match_case_sensitive_option() -> None:
    assert glob_match("**/*.jcl", "A.JCL", case_insensitive=False) is False
    assert glob_match("**/*.JCL", "A.JCL", case_insensitive=False) is True

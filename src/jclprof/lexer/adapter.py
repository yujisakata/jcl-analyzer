"""Harness adapter for the Step 4a Lexer (stage 'lexical', Golden View 'lexical')."""

from __future__ import annotations

from pathlib import Path

from jclprof.harness.adapters import AdapterOutput
from jclprof.harness.loader import GoldenCase
from jclprof.lexer.lexer import lex_file


class LexicalAdapter:
    stage = "lexical"

    def __init__(self, encoding: str = "utf-8") -> None:
        # Golden inputs and CardDemo JCL are UTF-8 (jcl_text profile, ADR-009).
        # The encoding is explicit, never guessed.
        self.encoding = encoding

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        r = lex_file(input_path, encoding=self.encoding)
        return AdapterOutput(view=r.to_golden_view(), diagnostics=r.golden_diagnostics())

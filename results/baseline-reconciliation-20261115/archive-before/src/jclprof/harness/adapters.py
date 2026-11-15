"""Adapter interface between future analyzers and the Harness (H-02).

Step 4 (Lexer/Parser) and Step 5 (Resolver) will each provide a StageAdapter that converts their
own output into the Golden View (docs/golden-view.md). Stages without an adapter are reported as
NOT_IMPLEMENTED -- never as PASSED and never as a harness failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from jclprof.harness.loader import GoldenCase


@dataclass
class AdapterOutput:
    view: dict[str, Any]
    diagnostics: list[dict[str, Any]] = field(default_factory=list)


class StageAdapter(Protocol):
    stage: str

    def run(self, case: GoldenCase, input_path: Path) -> AdapterOutput:
        """Analyze input_path (with case.raw['environment'] if any) and return the Golden View.

        input_path is resolved by the runner: a file under the suite, or the original corpus file
        for corpus:// inputs (never a copy)."""
        ...


def registered_adapters() -> dict[str, StageAdapter]:
    """Adapters available in this build. Step 4b: lexical and syntactic (with an explicit scope);
    semantic and resolution stay NOT_IMPLEMENTED until their analyzers exist."""
    from jclprof.lexer.adapter import LexicalAdapter
    from jclprof.parser.adapter import SyntacticAdapter

    return {"lexical": LexicalAdapter(), "syntactic": SyntacticAdapter()}

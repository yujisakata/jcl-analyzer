"""Diagnostic code registry (requirements §8.5).

Every diagnostic carries a code, severity, location, message and recommended remedy.
Codes are stable: never reuse or renumber a published code.

Prefixes: INV = inventory (Step 2). Later stages add LEX / PAR / RES / SEM.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from jclprof.ids import diagnostic_id

Severity = Literal["ERROR", "WARNING", "INFO"]


@dataclass(frozen=True)
class DiagnosticCode:
    code: str
    severity: Severity
    title: str
    remedy: str
    rule_id: str | None = None


CODES: dict[str, DiagnosticCode] = {
    c.code: c
    for c in (
        DiagnosticCode(
            "INV-E001", "ERROR", "Source file could not be read",
            "Check file permissions/locks; the file is registered but has no hash or content.",
        ),
        DiagnosticCode(
            "INV-W001", "WARNING", "File matched no classification rule (asset type UNKNOWN)",
            "Add a classification rule to the config, or an exclude rule with a reason.",
        ),
        DiagnosticCode(
            "INV-W002", "WARNING", "File could not be decoded with the configured encoding",
            "Specify the correct encoding for this path in encoding.overrides "
            "(e.g. the EBCDIC code page). The encoding is never guessed (ADR-004).",
        ),
        DiagnosticCode(
            "INV-W003", "WARNING", "Same member name appears more than once for an asset type",
            "Define the library search order (Step 5) so references resolve deterministically.",
        ),
        DiagnosticCode(
            "INV-W004", "WARNING", "File exceeds limits.max_decode_bytes; hashed but not decoded",
            "Raise limits.max_decode_bytes if this file must be analyzed.",
        ),
        DiagnosticCode(
            "INV-W005", "WARNING", "Record longer than the fixed record length of its asset type",
            "Columns beyond the fixed length do not exist on z/OS; check the transfer.",
            "JCL-REC-004",
        ),
        DiagnosticCode(
            "INV-W006", "WARNING", "TAB character in a fixed-column asset",
            "Column positions are significant in JCL; TABs make column rules ambiguous.",
            "JCL-REC-001",
        ),
        DiagnosticCode(
            "INV-I001", "INFO", "Derived member name is not a valid PDS member name",
            "Rule MVS-MEM-001 is PENDING verification; informational only.",
            "MVS-MEM-001",
        ),
        DiagnosticCode(
            "INV-I003", "INFO", "Non-CRLF/LF line terminators (CR-only or mixed)",
            "Confirm how the file was transferred from the host.",
        ),
        DiagnosticCode(
            "INV-I004", "INFO", "Encoding undetermined by configuration; file not decoded",
            "Record the confirmed code page in encoding.profiles / overrides (ADR-009). "
            "Until then the file is registered and hashed only.",
        ),
    )
}


@dataclass(frozen=True)
class Diagnostic:
    diag_id: str
    code: str
    severity: Severity
    root_id: str
    rel_path: str
    source_id: str
    line: int | None
    column: int | None
    message: str
    remedy: str
    rule_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_diagnostic(
    code: str,
    *,
    root_id: str,
    rel_path: str,
    source_id: str,
    message: str,
    line: int | None = None,
    column: int | None = None,
) -> Diagnostic:
    c = CODES[code]
    return Diagnostic(
        diag_id=diagnostic_id(code, source_id, line, column, message),
        code=code,
        severity=c.severity,
        root_id=root_id,
        rel_path=rel_path,
        source_id=source_id,
        line=line,
        column=column,
        message=message,
        remedy=c.remedy,
        rule_id=c.rule_id,
    )

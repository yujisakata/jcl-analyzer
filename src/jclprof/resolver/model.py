"""Effective Job View model (CD-4). A separate layer over the immutable Source AST.

Every effective node carries SourceRef provenance: the calling EXEC, the procedure definition
(statement / step / DD), the overriding DD and the SET / EXEC / PROC statement that defined each
substituted symbol (contract CA-15). Nothing here replaces or edits the Source AST.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceRef:
    file: str  # root-relative path, e.g. "jcl/PRTCATBL.jcl"
    sha256: str | None
    statement_id: str | None
    line: int | None
    column: int | None = None
    span: tuple[int, int] | None = None


@dataclass(frozen=True)
class SymbolDef:
    name: str
    value: str | None  # None = nullified
    scope: str  # SET | EXEC | PROC_DEFAULT
    defined_by: SourceRef
    derivation: tuple[SymbolUse, ...] = ()  # symbols used to compute this value


@dataclass(frozen=True)
class SymbolUse:
    name: str
    status: str  # RESOLVED | UNDEFINED | ENVIRONMENT_DEPENDENT | NULLIFIED
    value: str | None
    defined_by: SourceRef | None
    used_at: SourceRef


@dataclass(frozen=True)
class SearchStep:
    order: int
    kind: str  # INSTREAM | JCLLIB | SYSTEM | CONTEXT
    library: str | None
    result: str  # FOUND | NOT_FOUND | UNMAPPED | AMBIGUOUS | NOT_CONFIGURED
    candidates: tuple[str, ...] = ()
    evidence: SourceRef | None = None


@dataclass(frozen=True)
class ProcCall:
    id: str
    requested: str
    call: SourceRef
    status: str  # RESOLVED | ENVIRONMENT_GAP | AMBIGUOUS | NO_LIBRARY_CONTEXT | CYCLE | UNSUPPORTED
    search: tuple[SearchStep, ...]
    member_path: str | None = None
    member_sha256: str | None = None
    alias_of: str | None = None
    label: str | None = None
    label_matches_member: bool | None = None
    basis: str = ""  # library context basis (CONFIG / UNCONFIRMED_CONTRACT_CONTEXT / ...)
    depth: int = 1
    parent_call: str | None = None


@dataclass(frozen=True)
class EffectiveParam:
    name: str
    value: Any  # Golden-view style value after symbol substitution
    raw: str  # source text of the value as coded
    source: SourceRef
    substitutions: tuple[SymbolUse, ...] = ()


@dataclass(frozen=True)
class OverrideRecord:
    param: str
    action: str  # REPLACE | ADD | NULLIFY
    original: Any
    applied: Any
    source: SourceRef  # the overriding DD keyword
    reason: str


@dataclass(frozen=True)
class BackRef:
    param: str
    text: str
    status: str  # RESOLVED | UNRESOLVED
    target_dd_id: str | None
    source: SourceRef


@dataclass(frozen=True)
class EffectiveDD:
    id: str
    ddname: str | None
    concat_index: int
    params: tuple[EffectiveParam, ...]
    origin: SourceRef  # DD statement that defines it (procedure DD, job DD or added override DD)
    positional: tuple[EffectiveParam, ...] = ()
    overrides: tuple[OverrideRecord, ...] = ()
    override_statement: SourceRef | None = None
    added_by_override: bool = False
    unapplied_overrides: tuple[SourceRef, ...] = ()
    backrefs: tuple[BackRef, ...] = ()
    level: str = "STEP"  # JOB | STEP


@dataclass(frozen=True)
class EffectiveStep:
    id: str
    name: str | None
    call_path: tuple[str | None, ...]
    status: str  # RESOLVED | UNRESOLVED_CALL
    program: str | None
    exec_origin: SourceRef  # EXEC with PGM= (or the unresolved calling EXEC)
    call_chain: tuple[str, ...] = ()  # ProcCall ids from the job down to this step
    exec_params: tuple[EffectiveParam, ...] = ()
    dds: tuple[EffectiveDD, ...] = ()
    pending_overrides: tuple[SourceRef, ...] = ()  # override DDs of an unresolved call
    source_step_id: str | None = None


@dataclass(frozen=True)
class EffectiveJob:
    id: str
    name: str | None
    source: SourceRef
    job_level_dds: tuple[EffectiveDD, ...]
    steps: tuple[EffectiveStep, ...]
    job_symbol_uses: tuple[SymbolUse, ...] = ()


@dataclass(frozen=True)
class ResolveDiagnostic:
    code: str
    severity: str
    cls: str
    file: str
    line: int | None
    message: str


@dataclass(frozen=True)
class EffectiveResult:
    source: Any  # the Source ParseResult (unchanged)
    file: str
    sha256: str | None
    library_basis: str
    jobs: tuple[EffectiveJob, ...]
    steps: tuple[EffectiveStep, ...]  # procedure member expanded in an explicit context
    calls: tuple[ProcCall, ...]
    symbols_defined: tuple[SymbolDef, ...]
    diagnostics: tuple[ResolveDiagnostic, ...]
    limitations: tuple[str, ...] = field(default=())

    def counts(self) -> dict[str, int]:
        steps = [s for j in self.jobs for s in j.steps] + list(self.steps)
        return {
            "program_steps": sum(1 for s in steps if s.status == "RESOLVED"),
            "unresolved_call_steps": sum(1 for s in steps if s.status == "UNRESOLVED_CALL"),
            "dds": sum(len(s.dds) for s in steps) + sum(len(j.job_level_dds) for j in self.jobs),
            "job_level_dds": sum(len(j.job_level_dds) for j in self.jobs),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1, "file": self.file, "sha256": self.sha256,
            "library_basis": self.library_basis,
            "jobs": [asdict(j) for j in self.jobs], "steps": [asdict(s) for s in self.steps],
            "calls": [asdict(c) for c in self.calls],
            "symbols_defined": [asdict(s) for s in self.symbols_defined],
            "diagnostics": [asdict(d) for d in self.diagnostics],
            "limitations": list(self.limitations), "counts": self.counts(),
        }

"""CD-4 PROC Resolver for the CardDemo PROC constructs (contract CA-04..06, CA-15).

Builds an Effective Job View from the Source AST without modifying it.
Implemented: explicit library search (in-stream -> JCLLIB ORDER -> system library, JCL-PROC-003),
member/alias resolution with label kept separate (JCL-PROC-002, ADR-011), expansion of PROC steps
and DDs, DD overrides and additions by procstepname.ddname (JCL-PROC-006), symbolic parameters
on the calling EXEC, PROC defaults and SET with positional scope (JCL-EXEC-003, JCL-SYM-001..004),
nested procedure calls up to 15 levels (JCL-PROC-007), DCB/DSN backward references (JCL-SYN-004).
Out of scope: every form listed in UNSUPPORTED_FORMS. A detected form is reported RES-W004 with its
form id and recorded in EffectiveResult.unsupported; the affected call becomes UNSUPPORTED and is
not expanded, so no value that depends on it is reported as RESOLVED (CD-4R). Unresolved, ambiguous
or uninspectable libraries stay unresolved (never guessed, CD-4R F01/F02).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from jclprof.parser import DDNode, ParseResult, StatementNode, StepNode, Value, parse_file
from jclprof.resolver.library import LibraryContext
from jclprof.resolver.model import (
    BackRef,
    EffectiveDD,
    EffectiveJob,
    EffectiveParam,
    EffectiveResult,
    EffectiveStep,
    OverrideRecord,
    ProcCall,
    ResolveDiagnostic,
    SearchStep,
    SourceRef,
    SymbolDef,
    SymbolUse,
    UnsupportedForm,
)
from jclprof.resolver.symbols import Lookup, Scope, substitute

# Resolver diagnostic codes; must equal specs/diagnostic-catalog.yaml (checked by a test).
RESOLVE_CODES: dict[str, tuple[str, str, str]] = {
    "RES-E003": ("ERROR", "SYNTAX", "Cyclic procedure or INCLUDE reference"),
    "RES-E004": ("ERROR", "SYNTAX", "Backward reference target not found"),
    "RES-E005": ("ERROR", "SYNTAX",
                 "Override names a procedure step that the called procedure does not contain"),
    "RES-W001": ("WARNING", "ADVISORY", "Undefined symbol left as literal text"),
    "RES-W002": ("WARNING", "ENVIRONMENT", "Library DSN has no dataset mapping (ENVIRONMENT_GAP)"),
    "RES-W003": ("WARNING", "ENVIRONMENT",
                 "Member has more than one local candidate in a mapped library"),
    "RES-W004": ("WARNING", "UNSUPPORTED",
                 "Construct outside the CD-4 resolver scope; not applied"),
    "RES-W005": ("WARNING", "ENVIRONMENT", "Procedure search cannot complete"),
    "RES-W006": ("WARNING", "ENVIRONMENT",
                 "Mapped library folder cannot be inspected; later libraries are not used"),
    "RES-W007": ("WARNING", "ENVIRONMENT", "Library DSN is mapped more than once; not resolved"),
    "RES-I001": ("INFO", "ADVISORY", "PROC label differs from the member name"),
    "RES-I003": ("INFO", "ADVISORY",
                 "Duplicate symbol on one EXEC or PROC statement; the first value is used"),
    "RES-I002": ("INFO", "ENVIRONMENT",
                 "System symbol whose value depends on the execution environment"),
}

# JCL-EXEC-003 (Table 20 + PARMDD): anything else on a calling EXEC is a symbolic parameter.
EXEC_KEYWORDS = frozenset({
    "ABDISPCC", "ACCT", "ADDRSPC", "CCSID", "CONCURRENTRW", "COND", "DSKEYLBL", "DYNAMNBR",
    "FREEVOL", "GDGORDER", "KEYENCD1", "KEYENCD2", "KEYLABL1", "KEYLABL2", "MEMLIMIT", "PARM",
    "PARMDD", "PERFORM", "RD", "REGION", "REGIONX", "RLSTMOUT", "ROACCESS", "SYMBOLS", "SYMLIST",
    "TIME", "TVSAMCOM", "TVSMSG", "VOL", "PGM", "PROC",
})
QUOTED_SUBSTITUTION = frozenset({"PARM", "ACCT", "AMP", "PATH", "SUBSYS"})  # JCL-SYM-003
MUTUALLY_EXCLUSIVE = (frozenset({"SYSOUT"}), frozenset({"DSN", "DSNAME", "DISP"}))
MAX_DEPTH = 15  # JCL-PROC-007

# Input forms outside the resolver scope (CD-4R). Each is detected before expansion; the call that
# contains it becomes UNSUPPORTED (not expanded). Anything not listed here and not diagnosed
# otherwise is in scope. Audit finding ids in brackets.
UNSUPPORTED_FORMS: dict[str, str] = {
    "U-EXEC-OVERRIDE": "EXEC parameter (e.g. COND, REGION.step) coded on a calling EXEC",
    "U-OVR-POSITIONAL": "override DD with positional parameters (DUMMY, *, DATA)",
    "U-OVR-BASE-POSITIONAL": "override of a procedure DD coded with positional parameters "
                             "such as DUMMY [F08]",
    "U-OVR-DCB-MERGE": "override needing a DCB subparameter merge",
    "U-OVR-MUTEX": "override that mixes mutually exclusive parameters (SYSOUT with DSN/DISP)",
    "U-OVR-DSN-DUPLICATE": "DSN and DSNAME both coded on the overriding or the procedure DD "
                           "[R02]",
    "U-OVR-CONCAT": "concatenated or implicit DD after a procedure call",
    "U-OVR-NESTED-STEP": "override of a nested procedure call step",
    "U-DEPTH": f"procedure nesting deeper than {MAX_DEPTH} levels",
    "U-PROC-SET": "SET statement inside a procedure body [F03]",
    "U-NESTED-INSTREAM": "nested call of a name the job defines as an in-stream procedure [F04]",
    "U-SYMBOLIC-PROC": "procedure name given by a symbol [F06]",
    "U-SYMBOLIC-JCLLIB": "JCLLIB ORDER data set name given by a symbol [F06]",
}


@dataclass(frozen=True)
class _Doc:
    rel: str
    sha: str | None
    parsed: ParseResult


@dataclass(frozen=True)
class _Lib:
    dsn: str
    evidence: SourceRef | None


@dataclass
class _Run:
    file: str
    diags: list[ResolveDiagnostic] = field(default_factory=list)
    calls: list[ProcCall] = field(default_factory=list)
    defs: list[SymbolDef] = field(default_factory=list)
    seen: set[tuple[str, str, int | None, str]] = field(default_factory=set)
    unsupported: list[UnsupportedForm] = field(default_factory=list)
    job_instream: frozenset[str] = frozenset()


class Resolver:
    def __init__(self, library: LibraryContext, encoding: str = "utf-8",
                 jes: str = "UNKNOWN") -> None:
        self.library = library
        self.encoding = encoding
        self.jes = jes
        self._members: dict[Path, ParseResult] = {}

    # ------------------------------------------------------------------ entry points
    def resolve_file(self, path: Path, rel: str, root_id: str,
                     input_kind: str | None = None) -> EffectiveResult:
        kind = input_kind or ("proc_member" if Path(path).suffix.lower() in (".prc", ".proc")
                              else "job")
        parsed = parse_file(path, encoding=self.encoding, jes=self.jes, input_kind=kind)
        if kind == "proc_member":
            return self._resolve_member_parsed(parsed, rel, root_id, None)
        return self.resolve_parsed(parsed, rel, root_id)

    def resolve_member(self, path: Path, rel: str, root_id: str,
                       context_libraries: tuple[str, ...] | None) -> EffectiveResult:
        parsed = parse_file(path, encoding=self.encoding, jes=self.jes, input_kind="proc_member")
        return self._resolve_member_parsed(parsed, rel, root_id, context_libraries)

    def resolve_parsed(self, parsed: ParseResult, rel: str, root_id: str) -> EffectiveResult:
        doc = _Doc(rel, parsed.lex.sha256, parsed)
        run = _Run(rel)
        jobs = [self._job(doc, run, j) for j in parsed.jobs]
        return self._result(doc, run, tuple(jobs), ())

    # ------------------------------------------------------------------ helpers
    def ref(self, doc: _Doc, stmt: StatementNode | None, line: int | None = None,
            column: int | None = None) -> SourceRef:
        if stmt is None:
            return SourceRef(doc.rel, doc.sha, None, line, column)
        first = stmt.span[0] if stmt.span else line
        return SourceRef(doc.rel, doc.sha, stmt.id, line if line is not None else first, column,
                         stmt.span)

    def diag(self, run: _Run, code: str, file: str, line: int | None, detail: str = "") -> None:
        key = (code, file, line, detail)
        if key in run.seen:
            return
        run.seen.add(key)
        sev, cls, title = RESOLVE_CODES[code]
        run.diags.append(ResolveDiagnostic(code, sev, cls, file, line,
                                           title + (f": {detail}" if detail else "")))

    def form(self, run: _Run, form: str, call_id: str | None, at: SourceRef, detail: str) -> None:
        if form not in UNSUPPORTED_FORMS:
            raise KeyError(form)
        run.unsupported.append(UnsupportedForm(form, call_id, at, detail))
        self.diag(run, "RES-W004", at.file, at.line, f"[{form}] {detail}")

    def note_uses(self, run: _Run, uses: list[SymbolUse]) -> None:
        for u in uses:
            if u.status == "UNDEFINED":
                self.diag(run, "RES-W001", u.used_at.file, u.used_at.line, f"&{u.name}")
            elif u.status == "ENVIRONMENT_DEPENDENT":
                self.diag(run, "RES-I002", u.used_at.file, u.used_at.line, f"&{u.name}")

    def view(self, v: Value | None, kw: str | None, look: Lookup, at: SourceRef,
             uses: list[SymbolUse]) -> Any:
        if v is None or v.kind == "NULL":
            return None
        if v.kind in ("WORD", "COMPOUND"):
            text, u = substitute(v.text if v.kind == "COMPOUND" else (v.value or ""), look, at)
            uses += u
            return text
        if v.kind == "STRING":
            if kw in QUOTED_SUBSTITUTION:
                text, u = substitute(v.value or "", look, at)
                uses += u
                return {"q": text}
            return {"q": v.value}
        if v.kind == "LIST":
            return [self.view(i, kw, look, at, uses) for i in v.items]
        if v.kind == "KWSUB":
            return {"kw": [v.keyword, self.view(v.sub, v.keyword, look, at, uses)]}
        return v.text

    def param(self, doc: _Doc, run: _Run, stmt: StatementNode, name: str, v: Value | None,
              line: int, column: int, look: Lookup) -> EffectiveParam:
        at = self.ref(doc, stmt, line, column)
        uses: list[SymbolUse] = []
        val = self.view(v, name, look, at, uses)
        self.note_uses(run, uses)
        return EffectiveParam(name, val, v.text if v is not None else "", at, tuple(uses))

    def params_of(self, doc: _Doc, run: _Run, stmt: StatementNode, look: Lookup,
                  skip: frozenset[str] = frozenset()) -> tuple[list[EffectiveParam],
                                                              list[EffectiveParam]]:
        kws = [self.param(doc, run, stmt, k.name, k.value, k.line, k.column, look)
               for k in stmt.keywords if k.name not in skip]
        pos = [self.param(doc, run, stmt, "", p, p.line, p.column, look) for p in stmt.positional]
        return kws, pos

    # ------------------------------------------------------------------ job
    def _job(self, doc: _Doc, run: _Run, job: Any) -> EffectiveJob:
        scope = Scope()
        lo, hi = job.span
        sts = [s for s in doc.parsed.statements if s.span and lo <= s.span[0] <= hi]
        bodies = [_proc_span(pd, hi) for pd in job.procedures]
        run.job_instream = frozenset(pd.name for pd in job.procedures if pd.name)
        libs: list[_Lib] = []
        for s in sts:
            sline = s.span[0] if s.span else 0
            if s.kind == "SET" and any(a <= sline <= b for a, b in bodies):
                continue  # belongs to an in-stream procedure body, not to the job (CD-4R F03)
            if s.kind == "SET":
                for k in s.keywords:
                    at = self.ref(doc, s, k.line, k.column)
                    uses: list[SymbolUse] = []
                    if k.value is None:
                        val = None
                    else:
                        raw = k.value.value if k.value.kind == "STRING" else k.value.text
                        val, uses = substitute(raw or "", scope.lookup_at(sline), at)
                    self.note_uses(run, uses)
                    d = SymbolDef(k.name, val, "SET", at, tuple(uses))
                    scope.add_set(sline, d)
                    run.defs.append(d)
            elif s.kind == "JCLLIB":
                for k in s.keywords:
                    if k.name != "ORDER" or k.value is None:
                        continue
                    items = k.value.items if k.value.kind == "LIST" else (k.value,)
                    for it in items:
                        dsn = it.value if it.kind in ("STRING", "WORD") else it.text
                        libs.append(_Lib(dsn or "", self.ref(doc, s, it.line, it.column)))
        js = job.job_statement
        juses: list[SymbolUse] = []
        jlook = scope.lookup_at(js.span[0])
        for k in js.keywords:
            self.view(k.value, k.name, jlook, self.ref(doc, js, k.line, k.column), juses)
        for p in js.positional:
            self.view(p, None, jlook, self.ref(doc, js, p.line, p.column), juses)
        self.note_uses(run, juses)
        job_dds = tuple(self.source_dd(doc, run, d, scope.lookup_at(d.statement.span[0]),
                                       f"{doc.rel}#{d.statement.id}", "JOB")
                        for d in job.job_level_dds)
        steps: list[EffectiveStep] = []
        for st in job.steps:
            steps += self.expand(doc, run, st, scope, tuple(libs), job.procedures, (), (), 0, (),
                                 None)
        self.backrefs(run, steps)
        return EffectiveJob(f"{doc.rel}#{job.id}", job.name, self.ref(doc, js), job_dds,
                            tuple(steps), tuple(juses))

    # ------------------------------------------------------------------ DDs
    def source_dd(self, doc: _Doc, run: _Run, d: DDNode, look: Lookup, did: str,
                  level: str = "STEP") -> EffectiveDD:
        kws, pos = self.params_of(doc, run, d.statement, look)
        return EffectiveDD(did, d.ddname, d.concat_index, tuple(kws), self.ref(doc, d.statement),
                           tuple(pos), level=level)

    def merge(self, run: _Run, base: EffectiveDD, pdoc: _Doc, ovr: DDNode, cdoc: _Doc,
              clook: Lookup) -> EffectiveDD:
        # Unsupported override forms were rejected by call_forms() before expansion.
        st = ovr.statement
        oref = self.ref(cdoc, st)
        params = list(base.params)
        records: list[OverrideRecord] = []
        for k in st.keywords:
            new = self.param(cdoc, run, st, k.name, k.value, k.line, k.column, clook)
            key = _dsn_alias(k.name)  # DSN and DSNAME are one parameter (R02)
            idx = next((i for i, p in enumerate(params) if _dsn_alias(p.name) == key), None)
            old = params[idx] if idx is not None else None
            oname = old.name if old is not None else None
            osrc = old.source if old is not None else None
            if k.value is None:
                if idx is not None:
                    params.pop(idx)
                records.append(OverrideRecord(k.name, "NULLIFY", old.value if old else None, None,
                                              new.source, "JCL-PROC-006: keyword coded without a "
                                              "value removes the procedure parameter",
                                              oname, osrc))
            elif idx is not None and old is not None:
                records.append(OverrideRecord(k.name, "REPLACE", old.value, new.value,
                                              new.source, "JCL-PROC-006: overriding parameter "
                                              "replaces the procedure parameter", oname, osrc))
                params[idx] = new
            else:
                records.append(OverrideRecord(k.name, "ADD", None, new.value, new.source,
                                              "JCL-PROC-006: parameter not on the procedure "
                                              "statement is added"))
                params.append(new)
        return EffectiveDD(base.id, base.ddname, base.concat_index, tuple(params), base.origin,
                           base.positional, base.overrides + tuple(records), oref, False,
                           base.unapplied_overrides, base.backrefs, base.level)

    # ------------------------------------------------------------------ steps / calls
    def program_step(self, doc: _Doc, run: _Run, st: StepNode, look: Lookup,
                     call_path: tuple[str | None, ...], chain: tuple[str, ...],
                     dds: list[EffectiveDD] | None = None) -> EffectiveStep:
        e = st.exec_statement
        sid = "/".join([doc.rel + "#" + e.id, *chain])
        exec_kws, _ = self.params_of(doc, run, e, look, frozenset({"PGM"}))
        prog = raw = None
        uses: list[SymbolUse] = []
        if st.target and st.target[0] == "PGM":
            raw = st.target[1]
            prog, uses = substitute(raw, look, self.ref(doc, e))
            self.note_uses(run, uses)
        if dds is None:
            dds = [self.source_dd(doc, run, d, look, f"{sid}/{d.statement.id}") for d in st.dds]
        return EffectiveStep(sid, st.name, (*call_path, st.name),
                             "RESOLVED" if prog else "NO_PROGRAM", prog, self.ref(doc, e), chain,
                             tuple(exec_kws), tuple(dds), (), st.id, raw, tuple(uses))

    def placeholder(self, doc: _Doc, run: _Run, st: StepNode, look: Lookup,
                    call_path: tuple[str | None, ...], chain: tuple[str, ...]) -> EffectiveStep:
        e = st.exec_statement
        sid = "/".join([doc.rel + "#" + e.id, *chain])
        exec_kws, _ = self.params_of(doc, run, e, look, frozenset({"PROC"}))
        return EffectiveStep(sid, st.name, (*call_path, st.name), "UNRESOLVED_CALL", None,
                             self.ref(doc, e), chain, tuple(exec_kws), (),
                             tuple(self.ref(doc, d.statement) for d in st.dds), st.id)

    def search(self, run: _Run, doc: _Doc, name: str, libs: tuple[_Lib, ...] | None,
               instream: tuple[Any, ...], call_line: int) -> tuple[str, list[SearchStep], Any]:
        steps: list[SearchStep] = []
        order = 1
        for pd in instream:
            if pd.name == name and pd.proc_statement.span and pd.proc_statement.span[0] < call_line:
                steps.append(SearchStep(order, "INSTREAM", None, "FOUND",
                                        evidence=self.ref(doc, pd.proc_statement)))
                return "RESOLVED", steps, ("INSTREAM", pd)
        if libs is None:
            return "NO_LIBRARY_CONTEXT", steps, None
        unknown = False  # an earlier library could hold the member (UNMAPPED / UNAVAILABLE)
        for lib in libs:
            kind = "JCLLIB" if lib.evidence else "CONTEXT"
            if "&" in lib.dsn:  # CD-4R F06: symbolic library names are not substituted
                steps.append(SearchStep(order, kind, lib.dsn, "SYMBOLIC_NOT_SUPPORTED", (),
                                        lib.evidence))
                return "UNSUPPORTED", steps, None
            look = self.library.lookup(lib.dsn, name)
            steps.append(SearchStep(order, kind, lib.dsn, look.result, look.candidates,
                                    lib.evidence, look.reason))
            order += 1
            ev_file = lib.evidence.file if lib.evidence else doc.rel
            ev_line = lib.evidence.line if lib.evidence else call_line
            if look.result == "UNMAPPED":
                unknown = True
                if lib.evidence:
                    self.diag(run, "RES-W002", ev_file, ev_line, lib.dsn)
                continue
            if look.result == "UNAVAILABLE":  # CD-4R F01: not a known absence
                unknown = True
                self.diag(run, "RES-W006", ev_file, ev_line, f"{lib.dsn}: {look.reason}")
                continue
            if look.result == "DUPLICATE_MAPPING":  # CD-4R F02: never pick by list order
                self.diag(run, "RES-W007", ev_file, ev_line,
                          f"{lib.dsn}: {', '.join(look.candidates)}")
                return ("ENVIRONMENT_GAP" if unknown else "AMBIGUOUS"), steps, None
            if look.result == "FOUND":
                return ("ENVIRONMENT_GAP" if unknown else "RESOLVED"), steps, ("MEMBER", look)
            if look.result == "AMBIGUOUS":
                return ("ENVIRONMENT_GAP" if unknown else "AMBIGUOUS"), steps, None
        if not unknown:
            steps.append(SearchStep(order, "SYSTEM", None, "NOT_CONFIGURED"))
        return "ENVIRONMENT_GAP", steps, None

    def load_member(self, path: Path) -> ParseResult:
        if path not in self._members:
            self._members[path] = parse_file(path, encoding=self.encoding, jes=self.jes,
                                             input_kind="proc_member")
        return self._members[path]

    def expand(self, doc: _Doc, run: _Run, st: StepNode, scope: Scope,
               libs: tuple[_Lib, ...] | None,
               instream: tuple[Any, ...], call_path: tuple[str | None, ...],
               chain: tuple[str, ...], depth: int, active: tuple[str, ...],
               parent: str | None) -> list[EffectiveStep]:
        e = st.exec_statement
        line = e.span[0] if e.span else 0
        look = scope.lookup_at(line)
        if not (st.target and st.target[0] == "PROC"):
            return [self.program_step(doc, run, st, look, call_path, chain)]
        name = st.target[1]
        cid = f"{doc.rel}#{e.id}@{parent or 'ROOT'}"
        cref = self.ref(doc, e)
        if depth + 1 > MAX_DEPTH:
            self.form(run, "U-DEPTH", cid, cref, f"nesting deeper than {MAX_DEPTH} levels")
            run.calls.append(ProcCall(cid, name, cref, "UNSUPPORTED", (), basis=self.library.basis,
                                      depth=depth + 1, parent_call=parent,
                                      reasons=("UNSUPPORTED:U-DEPTH",)))
            return [self.placeholder(doc, run, st, look, call_path, chain)]
        if "&" in name:  # CD-4R F06
            self.form(run, "U-SYMBOLIC-PROC", cid, cref, f"PROC={name}")
            run.calls.append(ProcCall(cid, name, cref, "UNSUPPORTED", (), basis=self.library.basis,
                                      depth=depth + 1, parent_call=parent,
                                      reasons=("UNSUPPORTED:U-SYMBOLIC-PROC",)))
            return [self.placeholder(doc, run, st, look, call_path, chain)]
        if parent is not None and name in run.job_instream:  # CD-4R F04
            self.form(run, "U-NESTED-INSTREAM", cid, cref,
                      f"{name} is an in-stream procedure of the job, called from a procedure")
            run.calls.append(ProcCall(cid, name, cref, "UNSUPPORTED", (), basis=self.library.basis,
                                      depth=depth + 1, parent_call=parent,
                                      reasons=("UNSUPPORTED:U-NESTED-INSTREAM",)))
            return [self.placeholder(doc, run, st, look, call_path, chain)]
        others = [k for k in e.keywords if k.name != "PROC" and k.name.split(".")[0]
                  in EXEC_KEYWORDS]
        if others:
            self.form(run, "U-EXEC-OVERRIDE", cid, cref, ",".join(k.name for k in others))
        status, steps, found = self.search(run, doc, name, libs, instream, line)
        search_status = status
        if status == "UNSUPPORTED":
            ev = steps[-1].evidence or cref
            self.form(run, "U-SYMBOLIC-JCLLIB", cid, ev, f"ORDER item {steps[-1].library}")
        member_rel = member_sha = alias_of = label = None
        matches = None
        mdoc: _Doc | None = None
        proc_steps: tuple[StepNode, ...] = ()
        header: StatementNode | None = None
        if found and found[0] == "MEMBER" and status == "RESOLVED":
            lk = found[1]
            member_rel, alias_of = lk.rel, lk.alias_of
            parsed = self.load_member(lk.path)
            mdoc = _Doc(lk.rel, parsed.lex.sha256, parsed)
            member_sha = parsed.lex.sha256
            header = parsed.procedure_header
            proc_steps = parsed.procedure_steps
            label = header.name.text if header and header.name else None
            matches = label == (alias_of or name) if label else None
            if label and not matches:
                self.diag(run, "RES-I001", member_rel, 1,
                          f"label {label!r}, member {alias_of or name!r}")
        elif found and found[0] == "INSTREAM":
            pd = found[1]
            mdoc, header, proc_steps = doc, pd.proc_statement, pd.steps
            label = pd.name
            matches = True
        if status == "RESOLVED" and mdoc is not None:
            body = None
            if found and found[0] == "INSTREAM":
                body = _proc_span(found[1], doc.parsed.jobs[0].span[1] if doc.parsed.jobs else 0)
            self.call_forms(run, cid, doc, st, mdoc, proc_steps, body)
        key = member_rel or (f"{doc.rel}:INSTREAM:{name}" if mdoc is doc else None)
        if status == "RESOLVED" and key in active:
            status = "CYCLE"
            self.diag(run, "RES-E003", doc.rel, line, " -> ".join([*active, key or name]))
        # R04: an unsupported form makes the call UNSUPPORTED whatever the library state; the
        # search result and every reason are kept.
        forms = sorted({u.form for u in run.unsupported if u.call_id == cid})
        reasons = tuple(f"UNSUPPORTED:{f}" for f in forms)
        if status not in ("RESOLVED", "UNSUPPORTED"):
            reasons += (status,)
        if forms:
            status = "UNSUPPORTED"
        run.calls.append(ProcCall(cid, name, cref, status, tuple(steps), member_rel, member_sha,
                                  alias_of, label, matches, self.library.basis, depth + 1, parent,
                                  search_status, reasons))
        if status != "RESOLVED" or mdoc is None:
            if search_status in ("ENVIRONMENT_GAP", "NO_LIBRARY_CONTEXT"):
                self.diag(run, "RES-W005", doc.rel, line, f"{name}: {search_status}")
            elif search_status == "AMBIGUOUS" and steps[-1].result == "AMBIGUOUS":
                self.diag(run, "RES-W003", doc.rel, line,
                          f"{name}: {', '.join(steps[-1].candidates)}")
            return [self.placeholder(doc, run, st, look, call_path, chain)]
        # procedure scope: PROC defaults, then the calling EXEC's symbolic assignments
        pscope = Scope(parent=look)
        if header is not None:
            seen_hdr: set[str] = set()
            for k in header.keywords:
                at = self.ref(mdoc, header, k.line, k.column)
                if k.name in seen_hdr:  # first value wins on a PROC statement (p.36)
                    self.diag(run, "RES-I003", at.file, at.line, f"PROC {k.name}")
                    continue
                seen_hdr.add(k.name)
                uses: list[SymbolUse] = []
                val = None
                if k.value is not None:
                    raw = k.value.value if k.value.kind == "STRING" else k.value.text
                    val, uses = substitute(raw or "", look, at)
                d = SymbolDef(k.name, val, "PROC_DEFAULT", at, tuple(uses))
                pscope.define(d)
                run.defs.append(d)
        seen_exec: set[str] = set()
        for k in e.keywords:
            if k.name == "PROC" or k.name.split(".")[0] in EXEC_KEYWORDS:
                continue
            at = self.ref(doc, e, k.line, k.column)
            if k.name in seen_exec:  # first value wins on an EXEC statement (p.36)
                self.diag(run, "RES-I003", at.file, at.line, f"EXEC {k.name}")
                continue
            seen_exec.add(k.name)
            uses2: list[SymbolUse] = []
            val2 = None
            if k.value is not None:
                raw2 = k.value.value if k.value.kind == "STRING" else k.value.text
                val2, uses2 = substitute(raw2 or "", look, at)
            self.note_uses(run, uses2)
            d2 = SymbolDef(k.name, val2, "EXEC", at, tuple(uses2))
            pscope.define(d2)
            run.defs.append(d2)
        # overrides / additions following the calling EXEC (JCL-PROC-006)
        names = [p.name for p in proc_steps]
        per: dict[str | None, list[DDNode]] = {n: [] for n in names}
        current = names[0] if names else None
        for dn in st.dds:
            dline = dn.statement.span[0] if dn.statement.span else line
            if dn.ddname is None or dn.implicit:
                continue  # unreachable: U-OVR-CONCAT makes the call UNSUPPORTED
            target = dn.procstep or current
            if target not in per:
                self.diag(run, "RES-E005", doc.rel, dline, f"{target}.{dn.ddname}")
                continue
            current = target
            per[target].append(dn)
        plook = pscope.lookup_at(None)
        out: list[EffectiveStep] = []
        sub_chain = (*chain, cid)
        for ps in proc_steps:
            ovr = per.get(ps.name, [])
            if ps.target and ps.target[0] == "PROC":
                out += self.expand(mdoc, run, ps, pscope, libs, (), (*call_path, st.name),
                                   sub_chain, depth + 1, (*active, key or name), cid)
                continue
            sid = "/".join([mdoc.rel + "#" + ps.exec_statement.id, *sub_chain])
            dds: list[EffectiveDD] = []
            pending = list(ovr)
            for pd in ps.dds:
                base = self.source_dd(mdoc, run, pd, plook, f"{sid}/{pd.statement.id}")
                match = next((o for o in pending if o.ddname == pd.ddname and pd.ddname), None)
                if match is not None:
                    pending.remove(match)
                    base = self.merge(run, base, mdoc, match, doc, look)
                dds.append(base)
            for o in pending:  # additions
                kws, pos = self.params_of(doc, run, o.statement, look)
                dds.append(EffectiveDD(f"{sid}/{o.statement.id}", o.ddname, 0, tuple(kws),
                                       self.ref(doc, o.statement), tuple(pos),
                                       override_statement=self.ref(doc, o.statement),
                                       added_by_override=True))
            out.append(self.program_step(mdoc, run, ps, plook, (*call_path, st.name), sub_chain,
                                         dds))
        return out

    # ------------------------------------------------------------------ backward references
    def backrefs(self, run: _Run, steps: list[EffectiveStep]) -> None:
        for i, s in enumerate(steps):
            new_dds = []
            for d in s.dds:
                refs = []
                for p in d.params:
                    for text in _ref_texts(p.value):
                        target = _find_ref(text, steps, i)
                        status = "RESOLVED" if target else "UNRESOLVED"
                        if not target:
                            self.diag(run, "RES-E004", p.source.file, p.source.line, text)
                        refs.append(BackRef(p.name, text, status, target, p.source))
                new_dds.append(replace(d, backrefs=tuple(refs)) if refs else d)
            steps[i] = replace(s, dds=tuple(new_dds))

    # ------------------------------------------------------------------ members / results
    def _resolve_member_parsed(self, parsed: ParseResult, rel: str, root_id: str,
                               context: tuple[str, ...] | None) -> EffectiveResult:
        doc = _Doc(rel, parsed.lex.sha256, parsed)
        run = _Run(rel)
        header = parsed.procedure_header
        member = Path(rel).name.split(".")[0].upper()
        if header and header.name and header.name.text != member:
            self.diag(run, "RES-I001", rel, header.span[0] if header.span else 1,
                      f"label {header.name.text!r}, member {member!r}")
        scope = Scope()
        if header is not None:
            seen_hdr: set[str] = set()
            for k in header.keywords:
                at = self.ref(doc, header, k.line, k.column)
                if k.name in seen_hdr:  # first value wins on a PROC statement (p.36)
                    self.diag(run, "RES-I003", at.file, at.line, f"PROC {k.name}")
                    continue
                seen_hdr.add(k.name)
                val = None
                if k.value is not None:
                    val = k.value.value if k.value.kind == "STRING" else k.value.text
                d = SymbolDef(k.name, val, "PROC_DEFAULT", at)
                scope.define(d)
                run.defs.append(d)
        libs = None if context is None else tuple(_Lib(x, None) for x in context)
        steps: list[EffectiveStep] = []
        for st in parsed.procedure_steps:
            steps += self.expand(doc, run, st, scope, libs, (), (), (), 0, (member,), None)
        body_sets = [s for s in parsed.statements if s.kind == "SET"]
        for s in body_sets:  # CD-4R F03: positional SET inside a procedure is not modelled
            self.form(run, "U-PROC-SET", None, self.ref(doc, s), "SET in a standalone member view")
        if body_sets:
            steps = [replace(x, status="UNSUPPORTED") if x.status == "RESOLVED" else x
                     for x in steps]
        self.backrefs(run, steps)
        return self._result(doc, run, (), tuple(steps))

    def _result(self, doc: _Doc, run: _Run, jobs: tuple[EffectiveJob, ...],
                steps: tuple[EffectiveStep, ...]) -> EffectiveResult:
        lims = set(doc.parsed.limitations)
        unresolved = any(c.status != "RESOLVED" for c in run.calls)
        lims.discard("SYMBOLS_NOT_RESOLVED")
        if not unresolved:
            lims.discard("PROC_NOT_EXPANDED")
        lims.add("SYMBOLS_IN_INSTREAM_DATA_NOT_RESOLVED")
        lims.add("DSN_TO_RESOURCE_MAPPING_NOT_ATTEMPTED")
        if run.unsupported:
            lims.add("UNSUPPORTED_FORMS_PRESENT")
        diags = sorted(run.diags, key=lambda d: (d.file, d.line or 0, d.code, d.message))
        return EffectiveResult(doc.parsed, doc.rel, doc.sha, self.library.basis, jobs, steps,
                               tuple(run.calls), tuple(run.defs), tuple(diags),
                               tuple(sorted(lims)), tuple(run.unsupported), self.encoding,
                               self.jes)

    # ------------------------------------------------------------------ unsupported forms
    def call_forms(self, run: _Run, cid: str, doc: _Doc, st: StepNode, mdoc: _Doc,
                   proc_steps: tuple[StepNode, ...], body: tuple[int, int] | None) -> None:
        """Detect UNSUPPORTED_FORMS that need the called definition, before any expansion."""
        sets = ([s for s in mdoc.parsed.statements
                 if s.kind == "SET" and s.span and body[0] <= s.span[0] <= body[1]]
                if body is not None else
                [s for s in mdoc.parsed.statements if s.kind == "SET"])
        for s in sets:
            self.form(run, "U-PROC-SET", cid, self.ref(mdoc, s), "SET inside the called procedure")
        names = [p.name for p in proc_steps]
        per: dict[str | None, list[DDNode]] = {n: [] for n in names}
        current = names[0] if names else None
        for dn in st.dds:
            if dn.ddname is None or dn.implicit:
                self.form(run, "U-OVR-CONCAT", cid, self.ref(doc, dn.statement),
                          "concatenated or implicit DD after a procedure call")
                continue
            target = dn.procstep or current
            if target not in per:
                continue  # RES-E005 is reported during expansion
            current = target
            per[target].append(dn)
        for ps in proc_steps:
            ovr = per.get(ps.name, [])
            if not ovr:
                continue
            if ps.target and ps.target[0] == "PROC":
                self.form(run, "U-OVR-NESTED-STEP", cid, self.ref(doc, ovr[0].statement),
                          f"override of nested procedure call step {ps.name}")
                continue
            for o in ovr:
                oref = self.ref(doc, o.statement)
                if o.statement.positional:
                    self.form(run, "U-OVR-POSITIONAL", cid, oref,
                              f"{ps.name}.{o.ddname} coded with positional parameters")
                base = next((pd for pd in ps.dds if pd.ddname == o.ddname), None)
                if base is None:
                    continue  # an addition
                if base.statement.positional:
                    self.form(run, "U-OVR-BASE-POSITIONAL", cid, oref,
                              f"procedure DD {ps.name}.{o.ddname} is coded with "
                              f"{' '.join(p.text for p in base.statement.positional)}")
                for dd_st, who in ((o.statement, "overriding"), (base.statement, "procedure")):
                    if {"DSN", "DSNAME"} <= {k.name for k in dd_st.keywords}:
                        self.form(run, "U-OVR-DSN-DUPLICATE", cid, self.ref(
                            doc if who == "overriding" else mdoc, dd_st),
                            f"{who} DD {ps.name}.{o.ddname} codes both DSN and DSNAME")
                names_o = {_dsn_alias(k.name) for k in o.statement.keywords}
                have = {_dsn_alias(k.name) for k in base.statement.keywords}
                if "DCB" in names_o and "DCB" in have:
                    self.form(run, "U-OVR-DCB-MERGE", cid, oref, f"{ps.name}.{o.ddname}")
                if any((names_o & a and have & b) or (names_o & b and have & a)
                       for a, b in [MUTUALLY_EXCLUSIVE]):
                    self.form(run, "U-OVR-MUTEX", cid, oref, f"{ps.name}.{o.ddname}")


def _proc_span(pd: Any, job_end: int) -> tuple[int, int]:
    lo = pd.proc_statement.span[0] if pd.proc_statement.span else 0
    end = pd.pend_statement.span[1] if pd.pend_statement and pd.pend_statement.span else job_end
    return lo, end


def _dsn_alias(name: str) -> str:
    return "DSN" if name == "DSNAME" else name


def _ref_texts(v: Any) -> list[str]:
    if isinstance(v, str):
        return [v] if v.startswith("*.") else []
    if isinstance(v, list):
        return [t for x in v for t in _ref_texts(x)]
    if isinstance(v, dict) and "kw" in v:
        return _ref_texts(v["kw"][1])
    return []


def _find_ref(text: str, steps: list[EffectiveStep], i: int) -> str | None:
    parts = text[2:].split(".")
    if len(parts) == 1:  # *.ddname in the same step
        return next((d.id for d in steps[i].dds if d.ddname == parts[0]), None)
    if len(parts) == 2:  # *.stepname.ddname in an earlier step (closest previous)
        for s in reversed(steps[:i]):
            if s.name == parts[0] and len(s.call_path) == 1:
                return next((d.id for d in s.dds if d.ddname == parts[1]), None)
        return None
    if len(parts) == 3:  # *.stepname.procstepname.ddname
        for s in reversed(steps[: i + 1]):
            if s.call_path[:1] == (parts[0],) and s.name == parts[1]:
                return next((d.id for d in s.dds if d.ddname == parts[2]), None)
    return None

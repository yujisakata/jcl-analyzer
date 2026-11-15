"""Independent audit probes. No production, Golden or existing test mutation.
Run: .venv/Scripts/python.exe results/audit-20261115/probes.py
FAIL means a hand-written audit requirement is violated, not an expected xfail.
"""
from dataclasses import asdict
from pathlib import Path
import json
from jclprof.parser import parse_text
from jclprof.harness.trace import check_trace

BASE = ["//J JOB", "//S EXEC PGM=X"]
results = []

def steps(r):
    return [s.name for j in r.jobs for s in j.steps]

def errors(r):
    return any(d.severity == "ERROR" for d in r.diagnostics)

def probe(name, lines, predicate, expected, jes="JES2"):
    text = "\n".join(lines) + "\n"
    try:
        r = parse_text(text, jes=jes)
        ok = bool(predicate(r))
        trace = "PASS"
        try:
            check_trace(r, text)
        except AssertionError:
            trace = "FAIL"
        actual = {
            "steps": steps(r),
            "jobs": [{"name": j.name, "span": j.span,
                      "null_line": j.null_statement_line,
                      "dds": [[d.ddname for d in s.dds] for s in j.steps]} for j in r.jobs],
            "statements": [{"kind": s.kind, "span": s.span, "raw": s.raw} for s in r.statements],
            "regions": [asdict(d) for d in r.data_regions],
            "diagnostics": [asdict(d) for d in r.diagnostics],
            "roles": [asdict(rr) for rr in r.records],
            "limitations": r.limitations,
            "existing_trace_check": trace,
        }
    except Exception as e:
        ok, actual = False, {"exception": repr(e)}
    results.append({"id": name, "jes": jes, "input": text, "expected": expected,
                    "status": "PASS" if ok else "FAIL", "actual": actual})

probe("N1-null-JES3", BASE+["//", "//T EXEC PGM=Y"],
      lambda r: steps(r)==["S"], "JES3: T is ignored after null", "JES3")
probe("N2-null-UNKNOWN", BASE+["//", "//T EXEC PGM=Y"],
      lambda r: getattr(r.jobs[0], "structure_status", None)=="ENVIRONMENT_DEPENDENT"
      or bool(getattr(r, "interpretations", ())),
      "UNKNOWN must preserve competing memberships, not determine [S,T]", "UNKNOWN")
probe("N3-continued-null", BASE+["//D DD DSN=A,", "//", "//T EXEC PGM=Y"],
      lambda r: r.jobs[0].null_statement_line is None and not r.jobs[0].steps[-1].after_null,
      "Null after continued DD is a blank comments field, not a job terminator", "JES3")
dlm = BASE+["//D DD *,DLM=AA", " DATA", "//T EXEC PGM=Y", "AA", "//U EXEC PGM=Z"]
probe("N4-DLM-UNKNOWN", dlm,
      lambda r: bool(getattr(r, "interpretations", ()))
      or getattr(r.jobs[0], "structure_status", None)=="ENVIRONMENT_DEPENDENT",
      "Competing job structures must remain explicitly environment-dependent", "UNKNOWN")
probe("D1-escaped-ampersand", BASE+["//D DD DATA,DLM='&&@'", " DATA", "&@", "//T EXEC PGM=Y"],
      lambda r: steps(r)==["S","T"] and r.data_regions[0].terminator_line==5,
      "Doubled && counts as one &: &@ terminates at line 5")
probe("D2-delimiter-continuation-boundary", BASE+["//D DD DATA,DLM='//'", " DATA",
      "// DD DSN=A,", "//         DD DSN=B", "//T EXEC PGM=Y"],
      lambda r: any(s.kind=="DD" and s.span==(6,6) for s in r.statements),
      "Line 5 is a delimiter with comment; line 6 starts an independent unnamed DD")
probe("D3-delimiter-prefix", BASE+["//D DD DATA,DLM=AA", "AAXYZ", "AA", "//T EXEC PGM=Y"],
      lambda r: r.data_regions[0].records==(4,4) and r.data_regions[0].terminator_line==5,
      "JES2 delimiter must be followed by a blank; AAXYZ remains data")
for name, value, jes in [("empty", "''", "JES2"), ("one", "A", "JES2"),
                         ("nineteen", "ABCDEFGHIJKLMNOPQRS", "JES2"), ("JES3-three", "AAA", "JES3")]:
    probe("D4-invalid-length-"+name, BASE+["//D DD DATA,DLM="+value," DATA"],
          errors, "Invalid DLM length must produce syntax ERROR", jes)
probe("D5-star-DLM-EOF", BASE+["//D DD *,DLM=AA", " DATA"],
      lambda r: any(d.code=="LEX-W002" for d in r.diagnostics),
      "Missing required DLM delimiter must be diagnosed, consistently with DD DATA")
probe("E1-EXEC-two-targets", ["//J JOB", "//S EXEC PGM=X,PROC=Y"], errors,
      "EXEC accepts only one of PGM=, PROC=, bare procedure")
probe("E2-EXEC-list-target", ["//J JOB", "//S EXEC PGM=(X,Y)"], errors,
      "PGM is a program name or allowed backward reference, not a list")
probe("E3-DD-two-positionals", BASE+["//D DD DUMMY,DATA"], errors,
      "DD permits at most one positional parameter")
probe("T1-job-data-span", BASE+["//D DD DATA", " DATA1", " DATA2"],
      lambda r: r.jobs[0].span[1]>=5,
      "Job source interval must include its owned inline records through EOF")

# Positive controls: supported ordinary syntax and known JES-specific boundaries.
probe("C1-JOB-EXEC-DD", BASE+["//D DD DSN=A.B,DISP=SHR"],
      lambda r: not r.diagnostics and r.jobs[0].steps[0].dds[0].ddname=="D",
      "Ordinary JOB/EXEC/DD parses without diagnostics")
probe("C2-DD-concat", BASE+["//D DD DSN=A", "// DD DSN=B"],
      lambda r: r.jobs[0].steps[0].dds[1].concat_head=="D"
      and r.jobs[0].steps[0].dds[1].concat_index==1,
      "Unnamed DD joins preceding DD")
probe("C3-DATA-keeps-JCL", BASE+["//D DD DATA", "//INNER JOB", "/*", "//T EXEC PGM=Y"],
      lambda r: len(r.jobs)==1 and steps(r)==["S","T"] and r.data_regions[0].records==(4,4),
      "DD DATA preserves // records as data")
probe("C4-STAR-next-statement", BASE+["//D DD *", " DATA", "//T EXEC PGM=Y"],
      lambda r: steps(r)==["S","T"] and r.data_regions[0].terminator_line==5,
      "DD * without DLM ends on //")
probe("C5-STAR-DLM-JES3", dlm,
      lambda r: steps(r)==["S","U"] and r.data_regions[0].terminator_line==6,
      "JES3: // stays in data until AA", "JES3")
probe("C6-invalid-JOB-name", ["//1BAD JOB"], errors,
      "JOB name must start alphabetic or national")
probe("C7-invalid-EXEC-missing-target", ["//J JOB","//S EXEC TIME=1"], errors,
      "EXEC without a target produces syntax ERROR")
probe("C8-DLM-without-data", BASE+["//D DD DSN=A,DLM=AA"], errors,
      "DLM without * or DATA produces syntax ERROR")

dest=Path(__file__).with_name("probe-results.json")
dest.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for item in results:
    print(f'{item["status"]:4} {item["id"]}: {item["expected"]}')
print(f'{sum(x["status"]=="PASS" for x in results)} passed, '
      f'{sum(x["status"]=="FAIL" for x in results)} failed, {len(results)} total')

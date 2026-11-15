"""Compare production output to independently established source facts; read-only inputs."""
import json
import re
from collections import Counter
from pathlib import Path
from jclprof.parser import parse_file

BASE=Path(__file__).parent
evidence=json.loads((BASE/'inventory.json').read_text(encoding='utf-8'))
root=Path(evidence['root'])
raw_counts=Counter()
differences=[]
spans=[]
diagnostics=[]
for f in evidence['files']:
    for line in (root/f['path']).read_text(encoding='utf-8').splitlines():
        m=re.match(r'^//(?:[^\s*]+\s+|\s+)(JOB|EXEC|DD|SET|JCLLIB|PROC|PEND)(?=\s|$)',line)
        if m:
            raw_counts[m[1]]+=1
    result=parse_file(root/f['path'],encoding='utf-8',input_kind='job' if f['job'] else 'proc_member')
    actual=list(result.jobs[0].steps) if result.jobs else list(result.procedure_steps)
    expected=[(s['line'],s['name'],s['target_kind'],s['target'],
               [(d['line'],d['name'],d['concat_index']) for d in s['dds']]) for s in f['steps']]
    got=[(s.exec_statement.span[0],s.name,s.target[0],s.target[1],
          [(d.statement.span[0],d.statement.name.text if d.statement.name else None,d.concat_index)
           for d in s.dds]) for s in actual]
    if expected!=got:
        differences.append({'path':f['path'],'type':'hierarchy','expected':expected,'actual':got})
    eheads=[(s['line'],s['operation'],s['name']) for s in f['statements']]
    aheads=[(s.span[0],s.operation,s.name.text if s.name else None) for s in result.statements if s.operation]
    if eheads!=aheads:
        differences.append({'path':f['path'],'type':'statement heads'})
    byline={s.span[0]:s for s in result.statements if s.operation}
    for s in f['statements']:
        actual_s=byline[s['line']]
        params=[v.text for v in actual_s.positional]+[
            k.name+'='+(k.value.text if k.value else '') for k in actual_s.keywords]
        if params!=s['parameters']:
            differences.append({'path':f['path'],'line':s['line'],'type':'raw parameters',
                                'expected':s['parameters'],'actual':params})
        if tuple(s['lines'])!=actual_s.lines:
            differences.append({'path':f['path'],'line':s['line'],'type':'continuation ownership'})
    ejobdds=[(d['line'],d['name'],d['concat_index']) for d in f['job_level_dds']]
    ajobdds=[(d.statement.span[0],d.ddname,d.concat_index)
             for j in result.jobs for d in j.job_level_dds]
    if ejobdds!=ajobdds:
        differences.append({'path':f['path'],'type':'job DD hierarchy'})
    eregions=[(d['dd_line'],d['lines'],d['terminator'],d['terminator_line']) for d in f['data_regions']]
    aregions=[(next(s.span[0] for s in result.statements if s.id==d.statement_id),
               list(range(d.records[0],d.records[1]+1)) if d.records else [],
               d.terminator,d.terminator_line) for d in result.data_regions]
    if eregions!=aregions:
        differences.append({'path':f['path'],'type':'data boundaries'})
    for d in result.data_regions:
        if d.records and result.jobs and d.records[1]>result.jobs[0].span[1]:
            spans.append({'path':f['path'],'job_span':result.jobs[0].span,'region':d.records})
    if result.diagnostics:
        diagnostics.append({'path':f['path'],'diagnostics':[(d.code,d.line) for d in result.diagnostics]})
out={'independent_raw_regex_counts':dict(raw_counts),
     'independent_scanner_counts':evidence['summary']['operations'],
     'checked':['statement heads','raw parameter spelling','continuation ownership',
                'step targets and DD membership','JOB-level DD membership','data boundaries'],
     'source_fact_differences':differences,'job_span_does_not_cover_data':spans,
     'parser_diagnostics':diagnostics}
(BASE/'comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))

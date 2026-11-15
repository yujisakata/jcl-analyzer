"""Independent CD-2 probes; source fixtures and assertions authored from contract, not actuals."""
import argparse,sys,json,hashlib
from pathlib import Path
from dataclasses import replace
ap=argparse.ArgumentParser();ap.add_argument('--before',action='store_true');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
ROOT=Path(__file__).resolve().parents[2]
if args.before:
 sys.path.insert(0,str(ROOT/'results/baseline-reconciliation-20261115/snapshot-start/src'))
from jclprof.parser import parse_text,parse_file
from jclprof.harness.hierarchy import check_hierarchy

def J(*lines):return '\n'.join(lines)+'\n'
rows=[]
def record(name,passed,details=None):rows.append({'name':name,'passed':bool(passed),'detail':details})
for jes in ['JES2','JES3','UNKNOWN']:
 fixtures=[
 ('star_eof',J('//J JOB','//S EXEC PGM=X','//IN DD *',' D1',' D2'),[(1,5)]),
 ('implicit_eof',J('//J JOB','//S EXEC PGM=X',' D1',' D2'),[(1,4)]),
 ('data_job_is_data',J('//J JOB','//S EXEC PGM=X','//IN DD DATA','//K JOB',' D2'),[(1,5)]),
 ('star_empty_eof',J('//J JOB','//S EXEC PGM=X','//IN DD *'),[(1,3)]),
 ('empty_delimiter',J('//J JOB','//S EXEC PGM=X','//IN DD *','/*'),[(1,4)]),
 ('empty_before_next_job',J('//J JOB','//S EXEC PGM=X','//IN DD *','//K JOB'),[(1,3),(4,4)]),
 ('two_jobs_distinct_regions',J('//J JOB','//S EXEC PGM=X','//IN DD *',' D1','/*','//K JOB','//T EXEC PGM=Y',' D2',' D3'),[(1,5),(6,9)]),
 ('data_delimited_then_job',J('//J JOB','//S EXEC PGM=X','//IN DD DATA','//FAKE JOB','/*','//K JOB','//T EXEC PGM=Y'),[(1,5),(6,7)]),
 ('trailing_comment_and_null',J('//J JOB','//S EXEC PGM=X','//IN DD *',' D','/*','//*LAST','//'),[(1,7)]),
 ]
 for name,text,want in fixtures:
  r=parse_text(text,jes=jes);got=[list(j.span) for j in r.jobs]
  record(name+'/'+jes,got==[list(x) for x in want],{'expected':want,'actual':got})
r=parse_text(J('//J JOB','//S EXEC PGM=X','//IN DD *,DLM=AA',' D','//OTHER DD DUMMY','AA'),jes='UNKNOWN')
record('unknown_union_owns_delimiter',r.jobs[0].span==(1,6),{'span':r.jobs[0].span,'regions':[{'status':g.status,'candidates':[(c.records,c.terminator,c.terminator_line) for c in g.candidates]} for g in r.data_regions]})
r=parse_text(J('//J JOB NOTIFY=&U','//S EXEC PGM=X','//K JOB CLASS=A,NOTIFY=&V','//T EXEC PGM=Y'))
flat={s.id:s for s in r.statements}
record('two_symbolic_jobs_share_flat_objects',all(j.job_statement is flat[j.job_statement.id] and 'SYMBOLS_NOT_RESOLVED' in j.job_statement.limitations for j in r.jobs),[j.job_statement.limitations for j in r.jobs])
# References must still detect a stale copy after the parser fix.
bad=replace(r,jobs=(replace(r.jobs[0],job_statement=replace(r.jobs[0].job_statement,limitations=())),*r.jobs[1:]))
record('h01_stale_copy_still_rejected',any(v.code=='H-REF-01' for v in check_hierarchy(bad)))
corpus=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
inv=json.loads((ROOT/'results/carddemo-contract-20261115/inventory.json').read_text())
# use frozen independent path list; no reconstruction of expectations from parser
oracle=json.loads((ROOT/'tests/golden_pending/carddemo_source/expectations.json').read_text())
asts={};corpus_rows=[]
for case in oracle['files']:
 p=corpus/case['path'];r=parse_file(p,encoding=case['encoding'],input_kind=case['input_kind'])
 asts[case['path']]=r.to_dict()
 corpus_rows.append({'path':case['path'],'spans':[list(j.span) for j in r.jobs],'job_identity':all(j.job_statement is next(s for s in r.statements if s.id==j.job_statement.id) for j in r.jobs),'pend_line':getattr(r,'procedure_end',None).span[0] if getattr(r,'procedure_end',None) else None})
 if not args.before and case['input_kind']=='proc_member':
  from jclprof.harness.carddemo_source import check_case
  pend=r.procedure_end
  record(case['path']+'/root_pend_identity',pend is next(s for s in r.statements if s.kind=='PEND') and all(pend.id not in st.other_statements for st in r.procedure_steps) and pend.id not in r.outside_statements)
  variants={'missing_link':replace(r,procedure_end=None),
   'moved_to_last_step':replace(r,procedure_end=None,procedure_steps=(*r.procedure_steps[:-1],replace(r.procedure_steps[-1],other_statements=(*r.procedure_steps[-1].other_statements,pend.id)))),
   'duplicate_in_last_step':replace(r,procedure_steps=(*r.procedure_steps[:-1],replace(r.procedure_steps[-1],other_statements=(*r.procedure_steps[-1].other_statements,pend.id)))),
   'stale_pend_copy':replace(r,procedure_end=replace(pend,span=(pend.span[0]-1,pend.span[1]-1)))}
  for name,bad in variants.items():
   checked=check_case(case,bad,p.read_bytes());violations=check_hierarchy(bad)
   record(case['path']+'/'+name,checked['source_status']=='FAIL' or checked['trace_status']=='FAIL',{'source':checked['source_status'],'trace':checked['trace_status'],'codes':[v.code for v in violations]})
# Explicit source/member optional PEND and unchanged in-stream PEND: no universal acceptance claim.
for text,where in [(J('//P PROC','//S EXEC PGM=X'),None),(J('//P PROC','//S EXEC PGM=X','// PEND'),3)]:
 r=parse_text(text,input_kind='proc_member');e=getattr(r,'procedure_end',None)
 record('optional_pend/'+str(where),(e.span[0] if e else None)==where)
r=parse_text(J('//J JOB','//P PROC','//S EXEC PGM=X','// PEND','//T EXEC P'))
record('in_stream_owns_its_pend',r.jobs[0].procedures[0].pend_statement.span==(4,4) and getattr(r,'procedure_end',None) is None)
args.output.mkdir(parents=True,exist_ok=True)
(args.output/'asts.json').write_text(json.dumps(asts,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
report={'parser_module':sys.modules['jclprof.parser.parser'].__file__,'before':args.before,'checks':rows,'passed':sum(x['passed'] for x in rows),'failed':sum(not x['passed'] for x in rows),'corpus':corpus_rows}
(args.output/'probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'before':args.before,'passed':report['passed'],'failed':report['failed'],'failed_names':[x['name'] for x in rows if not x['passed']]},indent=2))
if not args.before and report['failed']:
 raise SystemExit(1)

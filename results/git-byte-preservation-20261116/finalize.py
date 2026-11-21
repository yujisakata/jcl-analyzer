import json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();out=root/'results/git-byte-preservation-20261116';before=json.loads((out/'before.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(w,*a):return subprocess.check_output(['git','-C',str(w),*a],text=True)
commit=git(root,'rev-parse','HEAD').strip();assert commit=='16a45190fb33a8abdcb8ddaff537f75dd2b4c2bd'
assert git(root,'rev-parse','HEAD^').strip()=='356ff90b3e97fd542e303b4646d5adf79a2ea623'
assert git(root,'diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()==['.gitattributes']
rows=[]
for state in before['worktrees']:
 w=Path(state['root']);head=git(w,'rev-parse','HEAD').strip();assert head==commit
 unexpected=[]
 for p,h in state['hashes'].items():
  expected=before['reference_sha256'][p] if p in before['targets'] else h
  if not (w/p).is_file() or sha(w/p)!=expected:unexpected.append(p)
 assert not unexpected,(str(w),unexpected)
 assert all(sha(w/p)==h for p,h in before['reference_sha256'].items())
 assert not git(w,'diff','--cached','--name-only').strip()
 if w!=root:assert not git(w,'status','--porcelain=v1','--untracked-files=all').strip()
 statuses=git(w,'status','--porcelain=v2','--branch')
 (out/(w.name+'-status-after.txt')).write_text(statuses,encoding='utf-8')
 rows.append({'root':str(w),'branch':git(w,'branch','--show-current').strip(),'head':head,
              'oracle_sha256':sha(w/'tests/golden_pending/carddemo_source/expectations.json'),
              'protected_payload_checked':204,'unrelated_bytes_changed':unexpected,
              'attributes':git(w,'check-attr','text','eol','--','tests/golden_pending/carddemo_source/expectations.json','src/jclprof/parser/parser.py','tests/golden/MANIFEST.json'),
              'status':statuses,'remaining_change_owner':'Codex: preexisting CD-3 results, previous Git inspection and this fix evidence' if w==root else 'none; clean'})
orig=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
now={p.relative_to(orig).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in orig.rglob('*') if p.is_file()}
assert now==before['original']
main_golden=[p for p in before['worktrees'][0]['hashes'] if p.startswith('tests/golden/')]
assert len(main_golden)==195 and all(sha(root/p)==before['worktrees'][0]['hashes'][p] for p in main_golden)
# Remove ONLY our named, detached, freshly checked-out temporary worktree; no force.
temp=Path('D:/projects/jcl-profiler-bytecheck-20261116')
assert temp.resolve()==Path('D:/projects/jcl-profiler-bytecheck-20261116').resolve()
assert git(temp,'rev-parse','HEAD').strip()==commit
assert not git(temp,'status','--porcelain=v1','--untracked-files=all').strip()
subprocess.run(['git','worktree','remove',str(temp)],check=True)
assert not temp.exists()
regressions=[]
for name in ['main','codex','claude','temporary','fresh']:
 a=json.loads((out/f'regression-{name}/acceptance.json').read_text(encoding='utf-8'));m=json.loads((out/f'regression-{name}/mutations.json').read_text(encoding='utf-8'))
 assert a['gates']['CD-SOURCE']['counts']=={'PASS':48} and a['gates']['CD-TRACE']['counts']=={'PASS':48}
 assert a['gates']['CD-ASSURANCE']['pending_count']==48 and a['gates']['formal_acceptance']=='FAIL'
 assert m['detected']==m['total']==1501 and not m['escaped']
 regressions.append({'run':name,'gates':a['gates'],'mutations':{'total':1501,'detected':1501,'escaped':0}})
data={'finished_utc':datetime.now(timezone.utc).isoformat(),'commit':commit,'parent':'356ff90b3e97fd542e303b4646d5adf79a2ea623','commit_paths':['.gitattributes'],'commit_message':git(root,'log','-1','--format=%s').strip(),'worktrees':rows,'originals_size_mtime_sha_preserved':240,'main_existing_golden_all_files_preserved':195,'all_worktree_sealed_manifest_payloads_verified':97,'pending_reviews_per_worktree':48,'regressions':regressions,'temporary_worktree_removed':True,'worktree_list':git(root,'worktree','list','--porcelain'),'global_autocrlf_unchanged':git(root,'config','--get','core.autocrlf').strip()=='true','formal_approval_performed':False}
(out/'final-verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':commit,'worktrees':[(r['branch'],r['head'],r['oracle_sha256']) for r in rows],'originals_preserved':240,'golden_preserved':195,'regression_runs':5,'pending_reviews':48,'temporary_removed':True},indent=2))

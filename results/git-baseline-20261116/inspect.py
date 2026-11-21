import subprocess,json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();out=root/'results/git-baseline-20261116'
def git(*args):return subprocess.check_output(['git',*args])
def sha(data):return hashlib.sha256(data).hexdigest()
status=git('status','--porcelain=v1','--untracked-files=all','-z').decode('utf-8').split('\0')
candidates=[{'status':s[:2],'path':s[3:]} for s in status if s]
tracked=git('ls-files','-z').decode('utf-8').split('\0')[:-1]
all_paths=sorted(set(tracked)|{x['path'] for x in candidates})
origroot=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
orig={p.relative_to(origroot).as_posix():sha(p.read_bytes()) for p in origroot.rglob('*') if p.is_file()}
previous=json.loads((root/'results/cd3-20261116/start.json').read_text(encoding='utf-8'))
orig_changed=[p for p in sorted(set(orig)|set(previous['original'])) if orig.get(p)!=previous['original'].get(p,{}).get('sha256')]
protected=json.loads((root/'results/cd1-20261115/protected-before.json').read_text(encoding='utf-8'))
golden_changed=[p for p,h in protected.items() if Path(p).is_relative_to(root/'tests/golden') and sha(Path(p).read_bytes())!=h]
base=json.loads((root/'results/cd2-independent-20261116/source-baseline.json').read_text(encoding='utf-8'))
base_changed=[f['path'] for f in base['files'] if sha((root/f['path']).read_bytes())!=f['sha256']]
source={f['path']:sha((root/f['path']).read_bytes()) for f in base['files']}
source_digest=sha(''.join(f'{p}\t{source[p]}\n' for p in sorted(source)).encode())
patterns={'aws_access_key':re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
'github_token':re.compile(rb'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b'),
'openai_key':re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b'),
'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=\r\n]{50,}'),
'url_credentials':re.compile(rb'https?://[^\s/:@]+:[^\s/@]+@')}
rows=[];hits=[];copies=[]
orig_hashes={v:k for k,v in orig.items()}
for p in all_paths:
 raw=(root/p).read_bytes();h=sha(raw)
 rows.append({'path':p,'bytes':len(raw),'sha256':h,'tracked':p in tracked,'candidate_status':next((x['status'] for x in candidates if x['path']==p),None)})
 if h in orig_hashes:copies.append({'project':p,'original':orig_hashes[h]})
 for rule,pat in patterns.items():
  for m in pat.finditer(raw):hits.append({'path':p,'line':raw[:m.start()].count(b'\n')+1,'rule':rule})
filtered=[]
for p in ['tests/golden_pending/carddemo_source/expectations.json','tests/golden_pending/carddemo_source/reviews.json','tests/golden/MANIFEST.json']:
 raw=(root/p).read_bytes();blob=git('cat-file','blob','HEAD:'+p);checkout=git('cat-file','--filters','--path='+p,'HEAD:'+p)
 filtered.append({'path':p,'worktree_sha256':sha(raw),'head_blob_sha256':sha(blob),'checkout_filtered_sha256':sha(checkout),'checkout_preserves_bytes':raw==checkout})
expect=root/'tests/golden_pending/carddemo_source'
reviews=json.loads((expect/'reviews.json').read_text(encoding='utf-8'))
worktrees=[]
for wt in git('worktree','list','--porcelain').decode().split('\n\n'):
 if not wt.strip():continue
 data=dict(x.split(' ',1) for x in wt.splitlines() if ' ' in x)
 p=Path(data['worktree'])/'tests/golden_pending/carddemo_source/expectations.json'
 data['oracle_sha256']=sha(p.read_bytes()) if p.exists() else None;worktrees.append(data)
info={'inspected_utc':datetime.now(timezone.utc).isoformat(),'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'history_commits':int(git('rev-list','--count','HEAD')),'worktrees':worktrees,'tracked_files':len(tracked),'candidate_changes':candidates,'high_confidence_secret_hits':hits,'secret_scan_limitations':'Pattern scan only; no external scanners or proof of absence of all secrets. Matched values never logged.','exact_original_copies':copies,'original_count':len(orig),'original_content_changes':orig_changed,'sealed_golden_changed':golden_changed,'cd2_source_changes':base_changed,'current_source_set_sha256':source_digest,'checkout_filter_results':filtered,'pending_reviews':sum(r['status']=='PENDING' for r in reviews['files']),'commit_performed':False,'blocking_issue':'core.autocrlf=true changes immutable oracle bytes on checkout; both existing linked worktrees already have the transformed SHA','review_task_truncated_after':'3. 特'}
(out/'inspection.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'registration-inventory.json').write_text(json.dumps({'files':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'status-before.txt').write_bytes(git('status','--porcelain=v2','--branch'))
(out/'git-config.txt').write_bytes(subprocess.run(['git','config','--show-origin','--get-regexp',r'core\.(autocrlf|eol|safecrlf)'],capture_output=True).stdout)
print(json.dumps({'head':info['head'],'tracked':len(tracked),'candidates':len(candidates),'original_changed':orig_changed,'golden_changed':golden_changed,'source_changes':base_changed,'source_digest':source_digest,'secret_hits':hits,'exact_original_copies':copies,'pending_reviews':info['pending_reviews']},indent=2))

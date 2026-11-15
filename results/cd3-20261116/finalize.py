import ast,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();out=root/'results/cd3-20261116';corpus=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
start=json.loads((out/'start.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[{'path':p,'before':h,'after':sha(root/p) if (root/p).is_file() else None} for p,h in start['project'].items() if not (root/p).is_file() or sha(root/p)!=h]
now={p.relative_to(corpus).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in corpus.rglob('*') if p.is_file()}
orig_changes=[p for p in sorted(set(now)|set(start['original'])) if now.get(p)!=start['original'].get(p)]
assert not changed,changed
assert not orig_changes,orig_changes
frozen=root/'tests/golden_pending/carddemo_source/expectations.json'
assert sha(frozen)=='fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a'
review=json.loads((frozen.parent/'reviews.json').read_text(encoding='utf-8'))
assert len(review['files'])==48 and all(r['status']=='PENDING' and not r['reviewed_by'] and not r['reviewed_at'] for r in review['files'])
old=json.loads((root/'results/cd2-independent-20261116/source-baseline.json').read_text(encoding='utf-8'))
old_changes=[p['path'] for p in old['files'] if not (root/p['path']).is_file() or sha(root/p['path'])!=p['sha256']]
assert not old_changes,old_changes
comparison=json.loads((out/'comparison.json').read_text(encoding='utf-8'))
assert comparison['summary']['matched']==48 and comparison['summary']['mismatched']==0
assert all(set(f['checks'])=={'identity','hierarchy','flat_values_comments','boundaries','records','tokens_values_positions'} and all(not v for v in f['checks'].values()) for f in comparison['files'])
items=json.loads((out/'human-review-items.json').read_text(encoding='utf-8'))
assert len(items['items'])==45 and all(x['status']=='PENDING' and x['reviewer'] is None for x in items['items'])
# Recheck every displayed oracle extract using its JSON Pointer. Review claims are separate.
oracle=json.loads(frozen.read_text(encoding='utf-8'))
for item in items['items']:
 for extract in item['oracle_evidence']:
  value=oracle
  for part in extract['pointer'].split('/')[1:]:value=value[int(part)] if isinstance(value,list) else value[part]
  assert value==extract['value'],extract['pointer']
imports=[]
for n in ast.walk(ast.parse((out/'review_oracle.py').read_text(encoding='utf-8'))):
 if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
 if isinstance(n,ast.ImportFrom):imports.append(n.module)
assert all(not s.startswith('jclprof') for s in imports)
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'project_existing_files':len(start['project']),'project_existing_changes':changed,'original_files':len(now),'original_size_mtime_sha_changes':orig_changes,'cd2_source_baseline_sha256':old['source_set_sha256'],'cd2_source_files_changed':old_changes,'oracle_sha256':sha(frozen),'pending_reviews':48,'pending_review_items':45,'direct_oracle_extracts_verified':sum(len(i['oracle_evidence']) for i in items['items']),'checker_imports':imports,'formal_approval_performed':False}
(out/'preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd()
out=root/'results/cd1-20261115'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(n,d): (out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
start=json.loads((out/'protected-before.json').read_text(encoding='utf-8'))
changes=[{'path':p,'before':h,'after':sha(Path(p)) if Path(p).is_file() else None} for p,h in start.items() if not Path(p).is_file() or sha(Path(p))!=h]
protected_groups={}
for name,folder in [('parser','src/jclprof/parser'),('lexer','src/jclprof/lexer'),('golden','tests/golden')]:
 expected={Path(p).resolve() for p in start if Path(p).is_relative_to(root/folder)}
 current={p.resolve() for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 protected_groups[name]={'before':len(expected),'after':len(current),'added':sorted(str(p) for p in current-expected),'removed':sorted(str(p) for p in expected-current)}
corpus=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
expected={Path(p).resolve() for p in start if Path(p).is_relative_to(corpus)}
current={p.resolve() for p in corpus.rglob('*') if p.is_file()}
protected_groups['original']={'before':len(expected),'after':len(current),'added':sorted(str(p) for p in current-expected),'removed':sorted(str(p) for p in expected-current)}
manifest=json.loads((root/'results/baseline-reconciliation-20261115/baseline-manifest.json').read_text())
old={x['path']:x['sha256'] for x in manifest['files'] if x['namespace']=='project' and x['path'].split('/')[0] not in ('docs','results') and x['path']!='jcl-profiler.7z'}
print('old source count',len(old))
assert len(old)==302
old_digest=hashlib.sha256(''.join(f'{p}\t{old[p]}\n' for p in sorted(old)).encode()).hexdigest()
assert old_digest=='86878b6588133f6f796b104f8359e5c11e0c7f48f896fe9a5f7345a64bd50b4b',old_digest
changed=[{'path':p,'before':h,'after':sha(root/p) if (root/p).is_file() else None} for p,h in old.items() if not (root/p).is_file() or sha(root/p)!=h]
excluded={'.venv','__pycache__','.hypothesis','.pytest_cache','.mypy_cache','.ruff_cache','.git'}
now={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and not excluded.intersection(p.relative_to(root).parts) and p.relative_to(root).parts[0] not in ('docs','results') and p.name!='jcl-profiler.7z'}
added=sorted(set(now)-set(old))
digest=hashlib.sha256(''.join(f'{p}\t{now[p]}\n' for p in sorted(now)).encode()).hexdigest()
oracle=root/'tests/golden_pending/carddemo_source/expectations.json'
assert sha(oracle)=='fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a'
reviews=json.loads((oracle.parent/'reviews.json').read_text())
assert all(x['status']=='PENDING' and not x['reviewed_by'] and not x['reviewed_at'] for x in reviews['files'])
preservation={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'baseline_source_sha256':old_digest,'protected_count':len(start),'protected_changed':changes,'protected_sets':protected_groups,'existing_302_changed':changed,'added_source_paths':added,'oracle_sha256':sha(oracle),'oracle_review_pending':len(reviews['files'])}
assert not changes
assert all(not v['added'] and not v['removed'] for v in protected_groups.values())
assert [x['path'] for x in changed]==['tests/CHANGES.md']
emit('preservation.json',preservation)
emit('source-baseline.json',{'method':'SHA-256 of sorted path<TAB>file SHA-256<LF>; source/test/spec/config/tool and root metadata','baseline_start_sha256':old_digest,'source_set_sha256':digest,'source_file_count':len(now),'git_commit':None,'git_reason':'not a Git repository; no git init or commit performed','files':[{'path':p,'sha256':now[p]} for p in sorted(now)]})
print(json.dumps({'preserved':len(start),'groups':protected_groups,'changed':changed,'added':added,'new_count':len(now),'new_digest':digest},indent=2))

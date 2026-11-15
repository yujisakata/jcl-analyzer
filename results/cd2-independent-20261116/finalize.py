import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();out=root/'results/cd2-independent-20261116'
start=json.loads((out/'start.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[p for p,h in start['project'].items() if not (root/p).is_file() or sha(root/p)!=h]
corpus=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
now={p.relative_to(corpus).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in corpus.rglob('*') if p.is_file()}
original_changed=[p for p in sorted(set(start['original'])|set(now)) if start['original'].get(p)!=now.get(p)]
protected=json.loads((root/'results/cd1-20261115/protected-before.json').read_text())
pinned={p:h for p,h in protected.items() if Path(p).is_relative_to(corpus) or Path(p).is_relative_to(root/'tests/golden')}
protected_changed=[p for p,h in pinned.items() if not Path(p).is_file() or sha(Path(p))!=h]
assert not changed,changed
assert not original_changed,original_changed
assert not protected_changed,protected_changed
oracle=root/'tests/golden_pending/carddemo_source'
assert sha(oracle/'expectations.json')=='fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a'
reviews=json.loads((oracle/'reviews.json').read_text())
assert len(reviews['files'])==48 and all(x['status']=='PENDING' and not x['reviewed_by'] and not x['reviewed_at'] for x in reviews['files'])
source={p:h for p,h in start['project'].items() if p.split('/')[0]!='docs'}
assert len(source)==313,len(source)
digest=hashlib.sha256(''.join(f'{p}\t{source[p]}\n' for p in sorted(source)).encode()).hexdigest()
def emit(name,data):(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
emit('source-baseline.json',{'captured_utc':datetime.now(timezone.utc).isoformat(),'method':'SHA-256 of sorted path<TAB>file SHA-256<LF>; source/test/spec/config/tool and root metadata','source_file_count':len(source),'source_set_sha256':digest,'git_commit':None,'files':[{'path':p,'sha256':source[p]} for p in sorted(source)]})
emit('preservation.json',{'checked_utc':datetime.now(timezone.utc).isoformat(),'existing_project_changed_during_review':changed,'original_count':len(now),'original_size_mtime_sha_changed_during_review':original_changed,'cd1_original_and_sealed_golden_pinned_count':len(pinned),'cd1_pinned_content_changed':protected_changed,'oracle_sha256':sha(oracle/'expectations.json'),'review_pending_count':48,'current_source_set_sha256':digest})
a=json.loads((out/'replay-before/asts.json').read_text());b=json.loads((out/'replay-current/asts.json').read_text())
normalized_changed=[p for p,v in a.items() if dict(v,procedure_end_id=None)!=b[p]]
diffs=json.loads((out/'ast-differences.json').read_text());diffs['missing_procedure_end_id_normalized_to_null_changed_files']=normalized_changed
emit('ast-differences.json',diffs)
probes=json.loads((out/'replay-current/probes.json').read_text());assert probes['failed']==0 and probes['passed']==43
accept=json.loads((out/'cd-run/acceptance.json').read_text());assert accept['gates']['CD-SOURCE']['counts']=={'PASS':48} and accept['gates']['CD-TRACE']['counts']=={'PASS':48}
print('preserved original and Golden:',len(pinned),'project existing changed:',len(changed),'current source count:',len(source),'sha256:',digest)
print('AST differences ignoring missing nullable key:',normalized_changed)

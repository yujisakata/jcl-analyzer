import json,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd();out=root/'results/git-byte-preservation-20261116'
roots=[root,Path('D:/projects/jcl-profiler-codex'),Path('D:/projects/jcl-profiler-claude')]
def git(w,*a):return subprocess.check_output(['git','-C',str(w),*a])
def sha(b):return hashlib.sha256(b).hexdigest()
excluded={'.git','.venv','venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.hypothesis'}
states=[]
for w in roots:
 tracked=git(w,'ls-files','-z').decode().split('\0')[:-1]
 status=git(w,'status','--porcelain=v1','--untracked-files=all','-z').decode().split('\0')
 pending=[{'status':s[:2],'path':s[3:]} for s in status if s]
 untracked=[x['path'] for x in pending if x['status']=='??']
 paths=sorted(set(tracked)|set(untracked))
 hashes={p:sha((w/p).read_bytes()) for p in paths if (w/p).is_file()}
 oracle='tests/golden_pending/carddemo_source/expectations.json'
 b=git(w,'cat-file','blob','HEAD:'+oracle);actual=(w/oracle).read_bytes()
 states.append({'root':str(w),'head':git(w,'rev-parse','HEAD').decode().strip(),'branch':git(w,'branch','--show-current').decode().strip(),'status':pending,'hashes':hashes,'oracle_blob_sha256':sha(b),'oracle_worktree_sha256':sha(actual),'only_newline_difference':b.replace(b'\r\n',b'\n')==actual.replace(b'\r\n',b'\n'),'attributes_exists':(w/'.gitattributes').exists(),'attributes':git(w,'check-attr','text','eol','filter','--',oracle).decode()})
 assert sha(b)=='fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a'
 assert not (w/'.gitattributes').exists()
origroot=Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
original={p.relative_to(origroot).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in origroot.rglob('*') if p.is_file()}
# Exact directory scope: immutable sealed payload/baseline and dedicated pending test data.
prefixes=['tests/golden/cases/','tests/golden/inputs/','tests/golden/libs/','tests/golden/.baseline/','tests/golden_pending/cases/','tests/golden_pending/inputs/','tests/acceptance/expected/']
targets=[p for p in git(root,'ls-files','-z').decode().split('\0')[:-1] if any(p.startswith(pre) for pre in prefixes)]
targets.append('tests/golden_pending/carddemo_source/expectations.json');targets=sorted(targets)
references={}
for p in targets:
 b=git(root,'cat-file','blob','HEAD:'+p);references[p]=sha(b)
 assert sha((root/p).read_bytes())==sha(b),(p,'main bytes differ from HEAD; stop')
 for w in roots:
  actual=(w/p).read_bytes()
  assert actual.replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'),(str(w),p,'non-EOL change; stop')
  assert not git(w,'status','--porcelain=v1','--',p).strip(),(str(w),p,'preexisting Git modification; stop')
manifest=json.loads((root/'tests/golden/MANIFEST.json').read_text(encoding='utf-8'))
for p,rec in manifest['files'].items():assert references['tests/golden/'+p]==rec['sha256']
data={'captured_utc':datetime.now(timezone.utc).isoformat(),'worktrees':states,'original':original,'targets':targets,'reference_sha256':references,'manifest_sha256':json.loads((root/'tests/golden_pending/carddemo_source/oracle-manifest.json').read_text(encoding='utf-8'))['expectations_sha256']}
(out/'before.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('targets',len(targets),'sealed_manifest_payload',len(manifest['files']),'originals',len(original))
print([(s['root'],s['oracle_worktree_sha256'],s['only_newline_difference'],len(s['status'])) for s in states])

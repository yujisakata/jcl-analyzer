"""Explicit checkout of verified-clean data only; never discards developer changes."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent
ROOT = OUT.parents[1]
BEFORE = json.loads((OUT/'before.json').read_text(encoding='utf-8'))
POLICY = (ROOT/'.gitattributes').read_bytes()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(w, *args, data=None):
    return subprocess.check_output(['git', '-C', str(w), *args], input=data)


def validate(w):
    failures = [p for p,h in BEFORE['reference_sha256'].items() if sha((w/p).read_bytes()) != h]
    assert not failures, (str(w), failures)
    manifest = json.loads((w/'tests/golden/MANIFEST.json').read_text(encoding='utf-8'))
    assert all(sha((w/'tests/golden'/p).read_bytes()) == v['sha256'] for p,v in manifest['files'].items())
    m = json.loads((w/'tests/golden_pending/carddemo_source/oracle-manifest.json').read_text(encoding='utf-8'))
    oracle = sha((w/'tests/golden_pending/carddemo_source/expectations.json').read_bytes())
    assert oracle == m['expectations_sha256'] == BEFORE['manifest_sha256']
    reviews = json.loads((w/'tests/golden_pending/carddemo_source/reviews.json').read_text(encoding='utf-8'))
    assert len(reviews['files']) == 48 and all(r['status'] == 'PENDING' for r in reviews['files'])
    return {'root': str(w), 'oracle_sha256': oracle, 'sealed_payload_checked':len(manifest['files']),
            'all_protected_checked':len(BEFORE['targets']), 'pending_reviews':48}


def checkout(w, initial=None):
    # Under old attributes these targets were Git-clean; also require the exact initial raw
    # bytes immediately before checkout so an intervening developer edit is never overwritten.
    if initial:
        assert git(w, 'rev-parse', 'HEAD').decode().strip() == initial['head']
        assert all(sha((w/p).read_bytes()) == initial['hashes'][p] for p in BEFORE['targets'])
    else:
        for p in BEFORE['targets']:
            raw = (w/p).read_bytes()
            assert sha(raw) == BEFORE['reference_sha256'][p] or sha(raw.replace(b'\r\n', b'\n')) == BEFORE['reference_sha256'][p]
    attrs = w/'.gitattributes'
    if attrs.exists():
        assert attrs.read_bytes() == POLICY
    else:
        attrs.write_bytes(POLICY)
    # checkout-index explicitly materializes bytes even when status thinks a file is clean.
    paths = ('\0'.join(BEFORE['targets'])+'\0').encode()
    attr_result = git(w, 'check-attr', '-z', '--stdin', 'text', data=paths).split(b'\0')
    assert all(attr_result[i] == b'unset' for i in range(2, len(attr_result)-1, 3))
    # checkout-index can retain an existing path whose cached stat still matches. Materialize
    # to NEW paths instead. A temporary index includes the proposed attributes without staging
    # anything in a developer's actual index. Verify every byte, then install atomically.
    index_path = Path(git(w, 'rev-parse', '--git-path', 'index').decode().strip())
    if not index_path.is_absolute():
        index_path = w/index_path
    materialized = Path(tempfile.mkdtemp(prefix=w.name+'-checkout-', dir=OUT)).resolve()
    assert materialized.is_relative_to(OUT.resolve())
    temp_index = OUT/(w.name+'-checkout.index')
    shutil.copyfile(index_path, temp_index)
    env = os.environ.copy()
    env['GIT_INDEX_FILE'] = str(temp_index.resolve())
    subprocess.run(['git', '-C', str(w), 'add', '--', '.gitattributes'], env=env, check=True)
    subprocess.run(['git', '-C', str(w), 'checkout-index', '--force', '-z', '--stdin',
                    '--prefix='+materialized.as_posix()+'/'], input=paths, env=env, check=True)
    assert all(sha((materialized/p).read_bytes()) == h for p,h in BEFORE['reference_sha256'].items())
    for p in BEFORE['targets']:
        live, staged = w/p, materialized/p
        if initial:
            assert sha(live.read_bytes()) == initial['hashes'][p], (str(w),p,'concurrent edit')
        assert live.resolve().is_relative_to(w.resolve()) and staged.resolve().is_relative_to(materialized)
        os.replace(staged, live)
    result = validate(w)
    result['checkout_command'] = 'git checkout-index --prefix=<new directory> --force -z --stdin; validate SHA; atomic install of 204 explicitly verified-clean data paths'
    result['temporary_index_only'] = True
    return result


if __name__ == '__main__':
    rows = [checkout(Path(s['root']), s) for s in BEFORE['worktrees']]
    # No non-target byte changes, including existing CD-3 files and all CD-4 sources/tests.
    for state in BEFORE['worktrees']:
        w = Path(state['root'])
        changes = [p for p,h in state['hashes'].items() if p not in BEFORE['targets'] and
                   (not (w/p).is_file() or sha((w/p).read_bytes()) != h)]
        assert not changes, (str(w), changes)
    (OUT/'checkout-existing.json').write_text(json.dumps({'checked_utc':datetime.now(timezone.utc).isoformat(),
                                                        'worktrees':rows},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,indent=2))

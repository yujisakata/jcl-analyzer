"""Independent checks of the CD-3 observations, not production tests or Golden edits."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

OUT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('cd3_review', OUT/'review_oracle.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks = []


def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})


with tempfile.TemporaryDirectory(prefix='method-check-', dir=OUT) as folder:
    m.CORPUS = Path(folder).resolve()

    def observe(text):
        p = m.CORPUS/'sample.jcl'
        p.write_bytes(text)
        return m.observe(p)

    a = observe(b'//J JOB\r\n//JOBLIB DD DSN=A\r\n// DD DSN=B\r\n//S EXEC PGM=X\r\n//D DD DUMMY')
    check('job_level_dds_and_concatenation', len(a['hierarchy']['jobs'][0]['dds']) == 2 and
          a['hierarchy']['jobs'][0]['dds'][1]['concat_index'] == 1 and
          a['dd_relations'][-1]['owner'] == 4)
    check('crlf_and_no_final_newline', a['records'][0]['terminator'] == '\r\n' and
          a['records'][-1]['terminator'] == '')
    # The fixture is not an 80-byte record; compare its literal byte extent separately.
    check('byte_extent_matches_fixture', a['records'][-1]['byte_end'] == len(b'//J JOB\r\n//JOBLIB DD DSN=A\r\n// DD DSN=B\r\n//S EXEC PGM=X\r\n//D DD DUMMY'))
    b = observe(b'//J JOB\n//JOBLIB JCLLIB ORDER=(A,B)\n//S EXEC PGM=X\n//D DD *\n A\n//* end\n//D2 DD DUMMY\n')
    check('joblib_label_is_not_dd', b['special']['jcllib_named_joblib'] == [2] and not b['hierarchy']['jobs'][0]['dds'])
    check('comment_in_column_one_ends_star_data', b['regions'] == [{'dd_line':4,'mode':'*','lines':[5],'terminator':'NEXT_STATEMENT','terminator_line':6}])
    c = observe(b'//J JOB\n//S EXEC PGM=X\n//D DD *\n X\n Y')
    check('eof_data_and_span', c['regions'][0]['lines'] == [4,5] and c['hierarchy']['jobs'][0]['span'] == [1,5])
    d = observe(b'//J JOB\n//S EXEC PGM=X\n//D DD DUMMY\n//S EXEC PGM=Y\n//E DD DUMMY\n')
    check('same_named_steps_keep_distinct_owners', [x['owner'] for x in d['dd_relations']] == [2,4])
    e = observe(b"//J JOB\n//S EXEC PGM=X,PARM='A, B',\n// MSGLEVEL=(1,,2) inline\n")
    params = e['logical'][1]['parameters']
    check('quoted_comma_and_space', params[1]['value']['view'] == {'q':'A, B'})
    check('continued_null_subparameter_and_comment', params[2]['value']['view'] == ['1',None,'2'] and e['flat'][1]['comment'] == ['inline'])
    f = observe(b'//P PROC\n//S EXEC PGM=X\n//D DD DUMMY\n// PEND\n')
    check('proc_root_and_pend_reachable', f['hierarchy']['procedure_header'] == {'name':'P','line':1} and f['hierarchy']['reachable_lines'] == [1,2,3,4])

# Deliberately alter COPIES of the oracle. The frozen file is never written.
oracle = json.loads((OUT.parents[1]/'tests/golden_pending/carddemo_source/expectations.json').read_text())
ledger = {f['path']:f for f in json.loads((OUT/'source-ledger.json').read_text())}
cases = {f['path']:f for f in oracle['files']}
p = 'app-transaction-type-db2/jcl/CREADB21.jcl'
base = cases[p]['expected_structure']['hierarchy']
for name, mutate in [
    ('removed_root', lambda h: h['jobs'].clear()),
    ('removed_step', lambda h: h['jobs'][0]['steps'].pop()),
    ('moved_dd_to_step', lambda h: h['jobs'][0]['steps'][0]['dds'].append(h['jobs'][0]['dds'].pop())),
    ('swapped_concat_order', lambda h: h['jobs'][0]['dds'].reverse()),
]:
    bad = copy.deepcopy(base)
    mutate(bad)
    check('copy_mutation/'+name, bool(m.differences(bad,ledger[p]['hierarchy'])))
for name, part, mutate in [
    ('data_boundary', 'regions', lambda v: v[0]['lines'].pop()),
    ('record_byte_start', 'records', lambda v: v[0].update(byte_start=1)),
    ('token_end_column', 'logical', lambda v: v[0]['tokens'][0]['segments'][0].__setitem__(2,99)),
    ('raw_parameter', 'logical', lambda v: v[0].update(parameter_text='BROKEN')),
]:
    p = 'app-transaction-type-db2/jcl/MNTTRDB2.jcl'
    bad = copy.deepcopy(ledger[p][part])
    mutate(bad)
    check('copy_mutation/'+name, bool(m.differences(bad,ledger[p][part])))

report = {'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'checks':checks}
(OUT/'method-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(1 if report['failed'] else 0)

"""Independent in-memory A11 regression probes; no production/Golden mutation."""
import json
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from jclprof.parser import parse_text
from jclprof.parser.adapter import SyntacticAdapter, hierarchy_view
from jclprof.harness.comparator import compare_structure
from jclprof.harness.hierarchy import check_hierarchy
from jclprof.harness.trace import check_trace
from jclprof.harness.runner import run_case
from jclprof.harness.loader import GoldenCase
from jclprof.harness.gates import classify_golden
from jclprof.harness.defects import load_known_defects

BASE=Path(__file__).parent
TEXT='//J JOB\n//S EXEC PGM=X\n//D DD DUMMY\n'
(BASE/'a11-original.jcl').write_text(TEXT,encoding='utf-8')
r=parse_text(TEXT)
mutated=replace(r,jobs=())
def traced(x,text):
    try:
        check_trace(x,text)
        return 'PASS'
    except AssertionError:
        return 'FAIL'

# Identical to the earlier audit, deliberately retain the legacy flat-view path.
out={'input':TEXT,'mutation':'dataclasses.replace(r,jobs=())',
     'legacy_flat_comparison_ok':compare_structure(r.to_golden_view(),mutated.to_golden_view()).ok,
     'trace_result':traced(mutated,TEXT),
     'new_invariant_violations':[asdict(x) for x in check_hierarchy(mutated)]}

# Hierarchy expectation is handwritten from the three source records, not Parser output.
expected={'view':'statements','statements':[
    {'kind':'JOB','span':[1,1],'name':'J'},
    {'kind':'EXEC','span':[2,2],'name':'S'},
    {'kind':'DD','span':[3,3],'name':'D'}],
    'hierarchy':{'jobs':[{'name':'J','line':1,'span':[1,3],'dds':[],
       'steps':[{'name':'S','line':2,'target':['PGM','X'],
                 'dds':[{'name':'D','line':3,'concat_head':'D','concat_index':0}]}],
       'procedures':[]}],'outside':[]}}
v=mutated.to_golden_view();v['hierarchy']=hierarchy_view(mutated)
out['hierarchical_comparison_differences']=[asdict(d) for d in compare_structure(expected,v).differences]
raw={'test_id':'AUDIT-A11-SAME','category':'JOB_EXEC_DD','validation_stage':'syntactic',
     'review_status':'draft','input_kind':'job','input_file':'a11-original.jcl',
     'expected_structure':expected,'expected_diagnostics':{'mode':'exact','items':[]}}
case=GoldenCase(raw=raw,file=BASE/'audit-case.json',suite_dir=BASE)
for label,value in [('original',r),('mutated',mutated)]:
    with patch('jclprof.parser.adapter.parse_file',return_value=value):
        result=run_case(case,{'syntactic':SyntacticAdapter()}, {})
    out['real_adapter_runner_'+label]=result.to_dict()

# Full-value trace still has a continuation-prefix-only fallback. Alter the later segment
# consistently in flat and tree statements while preserving the unchanged raw source and Lexer.
prefix="//S EXEC PGM=X,PARM='"
continued='//J JOB\n'+prefix+'A'*(71-len(prefix))+'\n'+'//'+' '*13+"BBBB'\n"
c=parse_text(continued)
ex=c.jobs[0].steps[0].exec_statement
kws=tuple(replace(k,value=replace(k.value,text=k.value.text.replace('BBBB','CCCC'),
                                value=k.value.value.replace('BBBB','CCCC')))
          if k.name=='PARM' else k for k in ex.keywords)
ex2=replace(ex,keywords=kws)
step2=replace(c.jobs[0].steps[0],exec_statement=ex2)
c2=replace(c,statements=tuple(ex2 if s.id==ex.id else s for s in c.statements),
           jobs=(replace(c.jobs[0],steps=(step2,)),))
out['continued_string_mutation']={'input':continued,'change':'PARM later segment BBBB -> CCCC',
    'trace_result':traced(c2,continued),
    'invariant_violations':[asdict(x) for x in check_hierarchy(c2)],
    'raw_source_unchanged':c.lex==c2.lex}

# A known-failing case is classified by id/status, even if its reason changes.
out['gate_a_case_id_allowance']={
    'injected_result':{'test_id':'G-IS-006','verification_status':'FAILED',
                       'reason':'unrelated adapter crash injected in memory'},
    'classification':classify_golden([{'test_id':'G-IS-006','verification_status':'FAILED',
                       'reason':'unrelated adapter crash injected in memory'}],load_known_defects())}
(BASE/'a11-recheck.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('real_adapter_runner_original',
      'real_adapter_runner_mutated')},ensure_ascii=False,indent=2))
print('Adapter/Runner:',out['real_adapter_runner_original']['verification_status'],'->',
      out['real_adapter_runner_mutated']['verification_status'])

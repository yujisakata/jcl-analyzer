"""Read-only CardDemo inventory, independently implemented; never imports jclprof.
Restricted to observed source forms. Ambiguity is an error, not guessed recovery.
Outputs investigation evidence, not approved Golden expectations.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re

ROOT = Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
OUT = Path(__file__).parent

def fields(card):
    body = card.ljust(80)[2:71]
    if body[0] == ' ':
        m = re.match(r'\s+(\S+)(?:\s+(.*))?$', body)
        assert m, repr(card)
        return None, m[1], m[2] or ''
    m = re.match(r'(\S+)\s+(\S+)(?:\s+(.*))?$', body)
    assert m, repr(card)
    return m[1], m[2], m[3] or ''

def param_piece(s, quoted=False):
    i=0
    while i < len(s):
        c=s[i]
        if c=="'":
            if quoted and i+1<len(s) and s[i+1]=="'":
                i+=2
                continue
            quoted=not quoted
        elif c==' ' and not quoted:
            return s[:i],False,s[i:].strip()
        i+=1
    return s,quoted,''

def split_params(s):
    out=[]
    q=False
    depth=0
    start=0
    i=0
    while i<len(s):
        c=s[i]
        if c=="'":
            if q and i+1<len(s) and s[i+1]=="'":
                i+=2
                continue
            q=not q
        elif not q:
            if c=='(':
                depth+=1
            elif c==')':
                depth-=1
                assert depth>=0,s
            elif c==',' and depth==0:
                out.append(s[start:i])
                start=i+1
        i+=1
    assert not q and depth==0,s
    out.append(s[start:])
    return out if s else []

all_files=[]
for path in sorted(p for p in ROOT.rglob('*') if p.suffix.lower() in ('.jcl','.prc','.proc')):
    rel=path.relative_to(ROOT).as_posix()
    raw=path.read_bytes()
    lines=raw.decode('utf-8').splitlines()
    statements=[]
    roles=[]
    regions=[]
    current=None
    pending=None
    indata=None
    def finish():
        global current,pending,indata
        if current is None:
            return
        current['parameters']=split_params(current['parameter_text'])
        statements.append(current)
        if current['operation']=='DD' and current['parameters'] and current['parameters'][0] in ('*','DATA'):
            assert not any(x.startswith('DLM=') for x in current['parameters']),rel
            indata={'dd_line':current['line'],'mode':current['parameters'][0], 'lines':[]}
            regions.append(indata)
        current=None
        pending=None
    for n,line in enumerate(lines,1):
        # Complete the prior logical statement before classifying the next record.
        if current and pending is None:
            finish()
        if indata:
            if line.startswith('/*'):
                indata.update(terminator='DELIMITER',terminator_line=n)
                indata=None
                roles.append({'line':n,'role':'DELIMITER'})
                continue
            if line.startswith('//') and indata['mode']=='*':
                indata.update(terminator='NEXT_STATEMENT',terminator_line=n)
                indata=None
            else:
                indata['lines'].append(n)
                roles.append({'line':n,'role':'DATA'})
                continue
        if line.startswith('//*'):
            roles.append({'line':n,'role':'COMMENT'})
            continue
        if line.startswith('//') and not line.ljust(80)[2:72].strip():
            assert not pending,(rel,n,'continued null')
            finish()
            roles.append({'line':n,'role':'NULL'})
            continue
        if current and pending:
            assert line.startswith('// ') and 4<=len(line)-len(line[2:].lstrip())+1<=16,(rel,n,'continuation',line)
            piece=line.ljust(80)[15:71] if pending=='QUOTED' else line.ljust(80)[2:71].lstrip()
            text,q,comment=param_piece(piece,pending=='QUOTED')
            current['parameter_text']+=text
            current['lines'].append(n)
            if comment:
                current['comments'].append({'line':n,'text':comment})
            roles.append({'line':n,'role':'CONTINUATION','mode':pending})
            pending='QUOTED' if q else 'PARAMETER' if text.endswith(',') else None
            continue
        assert line.startswith('//'),(rel,n,'unclassified',line)
        name,op,payload=fields(line)
        text,q,comment=param_piece(payload)
        current={'line':n,'lines':[n],'name':name,'operation':op,'parameter_text':text,
                 'comments':[{'line':n,'text':comment}] if comment else []}
        roles.append({'line':n,'role':'STATEMENT'})
        pending='QUOTED' if q else 'PARAMETER' if text.endswith(',') else None
    assert not pending,(rel,'unfinished continuation')
    finish()
    if indata:
        indata.update(terminator='EOF',terminator_line=None)
    job=None
    step=None
    jobdds=[]
    steps=[]
    concat=None
    for s in statements:
        op=s['operation']
        if op=='JOB':
            assert job is None,rel
            job={'line':s['line'],'name':s['name']}
        elif op=='EXEC':
            p=s['parameters'][0]
            if p.startswith('PGM='):
                kind,target='PGM',p[4:]
            elif p.startswith('PROC='):
                kind,target='PROC',p[5:]
            else:
                kind,target='PROC',p
            step={'line':s['line'],'name':s['name'],'target_kind':kind,'target':target,'dds':[]}
            steps.append(step)
            concat=None
        elif op=='DD':
            dd={'line':s['line'],'lines':s['lines'],'name':s['name'],'parameters':s['parameters']}
            if s['name']:
                dd.update(concat_head=s['name'],concat_index=0)
            else:
                assert concat,(rel,s['line'],'orphan concat')
                dd.update(concat_head=concat['concat_head'],concat_index=concat['concat_index']+1)
            (step['dds'] if step else jobdds).append(dd)
            concat=dd
        else:
            concat=None
    all_files.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
        'record_count':len(lines),'job':job,'steps':steps,'job_level_dds':jobdds,
        'statements':statements,'roles':roles,'data_regions':regions,
        'record_anomalies':{'over80':[n for n,l in enumerate(lines,1) if len(l)>80],
          'tabs':[n for n,l in enumerate(lines,1) if '\t' in l],
          'column72_nonblank':[n for n,l in enumerate(lines,1) if l[71:72].strip()],
          'sequence_nonblank':[n for n,l in enumerate(lines,1) if l[72:80].strip()]}})

operations=Counter(s['operation'] for f in all_files for s in f['statements'])
roles=Counter(r['role'] for f in all_files for r in f['roles'])
operands=defaultdict(lambda:defaultdict(list))
for f in all_files:
    for s in f['statements']:
        for p in s['parameters']:
            m=re.match(r'^([A-Z][A-Z0-9.]*)=(.*)$',p)
            key,value=(m[1],m[2]) if m else ('<POSITIONAL>',p)
            operands[s['operation']][key].append({'path':f['path'],'line':s['line'],'value':value})
summary={'files':len(all_files),'job_files':sum(f['job'] is not None for f in all_files),
    'proc_files':sum(f['job'] is None for f in all_files),'records':sum(f['record_count'] for f in all_files),
    'operations':dict(operations),'roles':dict(roles),
    'steps':sum(len(f['steps']) for f in all_files),'dds':operations['DD'],
    'job_level_dds':sum(len(f['job_level_dds']) for f in all_files),
    'unnamed_dds':sum(d['name'] is None for f in all_files for s in f['steps'] for d in s['dds'])
                  +sum(d['name'] is None for f in all_files for d in f['job_level_dds']),
    'data_regions':sum(len(f['data_regions']) for f in all_files),
    'region_terminators':dict(Counter(r['terminator'] for f in all_files for r in f['data_regions'])),
    'exec_targets':dict(Counter(s['target_kind']+'='+s['target'] for f in all_files for s in f['steps'])),
    'continuation_modes':dict(Counter(r['mode'] for f in all_files for r in f['roles'] if r['role']=='CONTINUATION'))}
evidence={'method':'independent restricted source scanner; no jclprof import; not approved Golden',
          'root':str(ROOT),'summary':summary,'operands':operands,'files':all_files}
(OUT/'inventory.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (OUT/'operands.tsv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.writer(stream,delimiter='\t')
    writer.writerow(['operation','operand','raw_value','path','statement_line'])
    for op,keys in operands.items():
        for key,values in keys.items():
            for item in values:
                writer.writerow([op,key,item['value'],item['path'],item['line']])
print(json.dumps(summary,ensure_ascii=False,indent=2))
for op,keys in sorted(operands.items()):
    for key,vals in sorted(keys.items()):
        counts=Counter(x['value'] for x in vals)
        print(op,key,len(vals),len(counts),dict(counts) if len(counts)<20 else '[see operands.tsv]')

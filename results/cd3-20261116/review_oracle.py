"""CD-3 source-only verification: card relations + SQL ownership + regex token grammar.

Does not import/invoke jclprof, inventory scanner, oracle author, or CD Harness.
Original observations are completed BEFORE loading the oracle. No approval/oracle writes.
Limited to observed forms; an unrecognized card/continuation fails, never guessed recovery.
"""
import bisect
import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
CORPUS = Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
HEADER = re.compile(r'^//(?:(?P<name>[^ ]+) +| +)(?P<op>JOB|EXEC|DD|SET|JCLLIB|PROC|PEND)(?= |$)')
FIELD = re.compile(r"(?:'(?:[^']|'')*'|[^ '])+")
TOKEN = re.compile(r"'(?:[^']|'')*'|[(),=]|[^(),=']+")
PUNCT = {'(': 'LPAREN', ')': 'RPAREN', ',': 'COMMA', '=': 'EQUALS'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ranges(points):
    # Group by equal (line, column-index). An independent representation of contiguous spans.
    groups = []
    for index, (line, column) in enumerate(points):
        key = (line, column - index)
        if groups and groups[-1][0] == key:
            groups[-1][2] = column
        else:
            groups.append([key, column, column])
    return [[key[0], lo, hi] for key, lo, hi in groups]


def tokenize(text, points):
    result = []
    cursor = 0
    for m in TOKEN.finditer(text):
        assert m.start() == cursor
        cursor = m.end()
        coded = m.group()
        kind = PUNCT.get(coded, 'STRING' if coded.startswith("'") else 'WORD')
        result.append({'type': kind, 'text': coded,
                       'value': coded[1:-1].replace("''", "'") if kind == 'STRING' else coded,
                       'line': points[m.start()][0], 'column': points[m.start()][1],
                       'segments': ranges(points[m.start():m.end()]),
                       'start': m.start(), 'end': m.end()})
    assert cursor == len(text)
    return result


def partitions(tokens, lo, hi):
    if lo == hi:
        return []
    depth = 0
    cuts = [lo]
    for i in range(lo, hi):
        if tokens[i]['type'] == 'LPAREN':
            depth += 1
        elif tokens[i]['type'] == 'RPAREN':
            depth -= 1
        elif tokens[i]['type'] == 'COMMA' and depth == 0:
            cuts.append(i + 1)
        assert depth >= 0
    assert depth == 0
    return [(a, b - 1) for a, b in zip(cuts, cuts[1:])] + [(cuts[-1], hi)]


def expression(tokens, lo, hi, text, points):
    if lo == hi:
        return {'text': '', 'segments': [], 'kind': 'NULL', 'view': None}
    a, b = tokens[lo]['start'], tokens[hi - 1]['end']
    coded = text[a:b]
    value = {'text': coded, 'segments': ranges(points[a:b]),
             'line': points[a][0], 'column': points[a][1]}
    kinds = [t['type'] for t in tokens[lo:hi]]
    if kinds == ['STRING']:
        value.update(kind='STRING', view={'q': tokens[lo]['value']})
    elif kinds[0] == 'LPAREN' and kinds[-1] == 'RPAREN':
        # Only a complete balanced parenthesized expression is a LIST.
        pairs = partitions(tokens, lo + 1, hi - 1)
        items = [expression(tokens, x, y, text, points) for x, y in pairs]
        value.update(kind='LIST', items=items, view=[v['view'] for v in items])
    elif len(kinds) >= 2 and kinds[:2] == ['WORD', 'EQUALS']:
        keyword = tokens[lo]['text']
        sub = expression(tokens, lo + 2, hi, text, points) if lo + 2 < hi else None
        value.update(kind='KWSUB', keyword=keyword, sub=sub,
                     view={'kw': [keyword, sub['view'] if sub else None]})
    elif kinds == ['WORD']:
        value.update(kind='WORD', view=coded)
    else:
        value.update(kind='COMPOUND', view=coded)
    return value


def observe(path):
    raw = path.read_bytes()
    # Use LF byte separators, not the author's unicode splitlines(keepends=True).
    cards = raw.split(b'\n')
    if cards[-1] == b'':
        cards.pop()
    physical = []
    offset = 0
    for i, card in enumerate(cards, 1):
        has_lf = offset + len(card) < len(raw)
        cr = card.endswith(b'\r') and has_lf
        body = card[:-1] if cr else card
        physical.append({'line': i, 'raw': body.decode('utf-8'), 'bytes': body,
                         'byte_start': offset, 'byte_end': offset + len(card) + int(has_lf),
                         'terminator': '\r\n' if cr else '\n' if has_lf else ''})
        offset += len(card) + int(has_lf)
    assert offset == len(raw)
    lines = [r['raw'] for r in physical]
    assert all('\t' not in s for s in lines), 'tabs need separate review'
    heads = {}
    continuations = []
    comments = {}
    base_roles = {}
    for r in physical:
        n, card = r['line'], r['raw']
        if card.startswith('//*'):
            base_roles[n] = 'COMMENT'
        elif card.startswith('//') and not card[2:71].strip():
            base_roles[n] = 'NULL'
        elif card.startswith('/*'):
            base_roles[n] = 'DELIMITER'
        elif (m := HEADER.match(card[:71])):
            heads[n] = {'line': n, 'name': m['name'], 'operation': m['op'],
                        'operation_column': m.start('op') + 1,
                        'lines': [n], 'payload_at': m.end()}
            base_roles[n] = 'STATEMENT'
        elif card.startswith('// '):
            continuations.append(n)
            base_roles[n] = 'CONTINUATION'
        else:
            base_roles[n] = 'OTHER'
    header_lines = sorted(heads)
    for n in continuations:
        at = bisect.bisect_left(header_lines, n) - 1
        assert at >= 0, 'continuation without header'
        heads[header_lines[at]]['lines'].append(n)
    logical = []
    for n, s in heads.items():
        fragments, points, comment_parts = [], [], []
        for j, line in enumerate(s['lines']):
            card = lines[line - 1][:71]
            start = s['payload_at'] if j == 0 else 2
            while start < len(card) and card[start] == ' ':
                start += 1
            if j:
                assert 3 <= start <= 15
                assert fragments[-1].endswith(','), 'not an observed comma continuation'
                assert all(base_roles[k] == 'COMMENT' for k in range(s['lines'][j - 1] + 1, line))
            m = FIELD.match(card, start)
            piece = m.group() if m else ''
            end = m.end() if m else start
            assert end == len(card) or card[end] == ' '
            if card[end:].strip():
                comment_parts.append({'line': line, 'column': end + 1,
                                      'text': card[end:].strip()})
            fragments.append(piece)
            points += [(line, col + 1) for col in range(start, end)]
        text = ''.join(fragments)
        ts = tokenize(text, points)
        params = []
        for lo, hi in partitions(ts, 0, len(ts)):
            kw = hi - lo >= 2 and ts[lo]['type'] == 'WORD' and ts[lo + 1]['type'] == 'EQUALS'
            if kw:
                v = expression(ts, lo + 2, hi, text, points) if lo + 2 < hi else None
                params.append({'keyword': ts[lo]['text'], 'line': ts[lo]['line'],
                               'column': ts[lo]['column'], 'value': v})
            else:
                params.append({'keyword': None, 'value': expression(ts, lo, hi, text, points)})
        logical.append({k: v for k, v in s.items() if k != 'payload_at'} |
                       {'parameter_text': text, 'parameters': params,
                        'tokens': [{k: v for k, v in t.items() if k not in ('start', 'end')} for t in ts]})
        comments[n] = comment_parts
    # Independent interval construction: first raw sentinel, no inventory state machine.
    regions = []
    for s in logical:
        if s['operation'] != 'DD':
            continue
        assert not any(p['keyword'] == 'DLM' for p in s['parameters']), 'DLM outside review forms'
        pos = [p for p in s['parameters'] if p['keyword'] is None]
        if pos and pos[0]['value']['text'] in ('*', 'DATA'):
            assert pos[0]['value']['text'] == '*', 'DD DATA outside frozen forms'
            start = s['lines'][-1] + 1
            sentinels = [r['line'] for r in physical if r['line'] >= start and
                         (r['raw'].startswith('//') or r['raw'].startswith('/*'))]
            term_line = min(sentinels) if sentinels else None
            term = ('DELIMITER' if lines[term_line - 1].startswith('/*') else 'NEXT_STATEMENT') if term_line else 'EOF'
            regions.append({'dd_line': s['line'], 'mode': '*',
                            'lines': list(range(start, term_line or len(lines) + 1)),
                            'terminator': term, 'terminator_line': term_line})
    roles = dict(base_roles)
    data_owner = {}
    for region in regions:
        for n in region['lines']:
            assert n not in data_owner
            data_owner[n] = region['dd_line']
            roles[n] = 'DATA'
        if region['terminator'] == 'DELIMITER':
            data_owner[region['terminator_line']] = region['dd_line']
    assert all(roles[n] != 'OTHER' for n in roles), 'unclassified record'
    assert not any(s['line'] in data_owner for s in logical)
    owner = {n: s['line'] for s in logical for n in s['lines']}
    records = [{'line': r['line'], 'role': roles[r['line']],
                'statement_line': owner.get(r['line']), 'data_dd_line': data_owner.get(r['line']),
                'byte_start': r['byte_start'], 'byte_end': r['byte_end'],
                'raw_sha256': digest(r['bytes']), 'terminator': r['terminator']} for r in physical]
    # SQL nearest-predecessor queries, not the oracle author's mutable step/last_dd walk.
    db = sqlite3.connect(':memory:')
    db.execute('create table s(line integer primary key, op text, name text)')
    db.executemany('insert into s values(?,?,?)', [(s['line'], s['operation'], s['name']) for s in logical])
    rows = db.execute('''select line,op,name,
        (select max(p.line) from s p where p.op='EXEC' and p.line<=s.line) as step,
        lag(op) over(order by line) as prev_op,
        max(case when op!='DD' or name is not null then line end) over(order by line) as head
        from s order by line''').fetchall()
    root = [s for s in logical if s['operation'] in ('JOB', 'PROC')]
    assert len(root) == 1 and root[0]['line'] == logical[0]['line']
    root = root[0]
    pend = [s['line'] for s in logical if s['operation'] == 'PEND']
    assert (len(pend) == 1 and pend[0] == logical[-1]['line']) if root['operation'] == 'PROC' else not pend
    by_line = {s['line']: s for s in logical}
    region_map = {r['dd_line']: r for r in regions}
    steps, dds = [], []
    for line, op, name, step, prev_op, head in rows:
        if op == 'EXEC':
            ps = by_line[line]['parameters']
            first = ps[0]
            target = [first['keyword'], first['value']['text']] if first['keyword'] in ('PGM', 'PROC') else ['PROC', first['value']['text']]
            steps.append({'name': name, 'line': line, 'target': target, 'dds': []})
        if op == 'DD':
            assert name is not None or prev_op == 'DD', 'unnamed DD has no adjacent operational DD'
            index = db.execute("select count(*)-1 from s where op='DD' and line between ? and ?", (head, line)).fetchone()[0]
            dd = {'name': name, 'line': line, 'concat_head': by_line[head]['name'], 'concat_index': index}
            if line in region_map:
                g = region_map[line]
                dd['inline_data'] = {'records': [g['lines'][0], g['lines'][-1]] if g['lines'] else None,
                                     'terminator': g['terminator']}
            dds.append({'owner': step or root['line'], 'owner_kind': 'STEP' if step else root['operation'], **dd})
            if step:
                next(x for x in steps if x['line'] == step)['dds'].append(dd)
    hierarchy = {'jobs': [], 'outside': [], 'reachable_lines': sorted(heads)}
    if root['operation'] == 'JOB':
        hierarchy['jobs'] = [{'name': root['name'], 'line': root['line'], 'span': [root['line'], len(lines)],
                              'dds': [{k: v for k, v in d.items() if k not in ('owner', 'owner_kind')} for d in dds if d['owner_kind'] == 'JOB'],
                              'steps': steps, 'procedures': []}]
    else:
        hierarchy.update(procedure_header={'name': root['name'], 'line': root['line']}, procedure_steps=steps)
    flat = []
    for rec in records:
        n, role = rec['line'], rec['role']
        if role == 'STATEMENT':
            s = by_line[n]
            flat.append({'kind': s['operation'], 'span': [n, s['lines'][-1]], 'name': s['name'],
                         'positional': [p['value']['view'] for p in s['parameters'] if p['keyword'] is None],
                         'keywords': [[p['keyword'], p['value']['view'] if p['value'] else None] for p in s['parameters'] if p['keyword'] is not None],
                         'comment': [c['text'] for c in comments[n]] or None})
            if n in region_map:
                g = region_map[n]
                flat[-1]['inline_data'] = {'records': [g['lines'][0], g['lines'][-1]] if g['lines'] else None,
                                           'terminator': g['terminator'], 'delimiter': '/*' if g['terminator'] == 'DELIMITER' else None}
        elif role == 'COMMENT':
            flat.append({'kind': 'COMMENT', 'span': [n, n], 'comment': [lines[n - 1][3:80].strip()]})
        elif role in ('NULL', 'DELIMITER'):
            flat.append({'kind': role, 'span': [n, n]})
    duplicate_names = db.execute("select name,group_concat(line) from s where op='EXEC' group by name having count(*)>1").fetchall()
    special = {'job_level_dds': [d for d in dds if d['owner_kind'] == 'JOB'],
               'jcllib_named_joblib': [s['line'] for s in logical if s['operation'] == 'JCLLIB' and s['name'] == 'JOBLIB'],
               'proc_pend': [root['line'], *pend] if root['operation'] == 'PROC' else [],
               'unnamed_dds': [d for d in dds if d['name'] is None],
               'duplicates': [{'name': name, 'lines': [int(x) for x in ns.split(',')]} for name, ns in duplicate_names],
               'continuations': [{'line': s['line'], 'lines': s['lines']} for s in logical if len(s['lines']) > 1],
               'inline_comments': [{'statement': n, **c} for n, cs in comments.items() for c in cs],
               'comment_between_continuations': [{'statement': s['line'], 'line': n} for s in logical for n in range(s['line'],s['lines'][-1]+1) if roles[n]=='COMMENT'],
               'nonblank_72': [r['line'] for r in physical if len(r['raw']) >= 72 and r['raw'][71] != ' '],
               'nonblank_73_80': [r['line'] for r in physical if r['raw'][72:80].strip()],
               'post_80': [r['line'] for r in physical if r['raw'][80:].strip()],
               'non_ascii': [r['line'] for r in physical if any(c>127 for c in r['bytes'])]}
    db.close()
    return {'path': path.relative_to(CORPUS).as_posix(), 'sha256': digest(raw), 'encoding': 'utf-8',
            'input_kind': 'job' if root['operation']=='JOB' else 'proc_member',
            'records': records, 'logical': logical, 'hierarchy': hierarchy,
            'flat': flat, 'regions': regions, 'dd_relations': dds, 'special': special}


def differences(a, b, path=''):
    if type(a) is not type(b):
        return [{'path': path, 'oracle': a, 'source_observation': b}]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:
                out.append({'path': path+'.'+k, 'oracle': a.get(k, '<MISSING>'), 'source_observation': b.get(k, '<MISSING>')})
            else:
                out.extend(differences(a[k], b[k], path+'.'+k))
        return out
    if isinstance(a, list):
        out = [] if len(a)==len(b) else [{'path': path+'.length', 'oracle':len(a), 'source_observation':len(b)}]
        for i, (x,y) in enumerate(zip(a,b)):
            out.extend(differences(x,y,f'{path}[{i}]'))
        return out
    return [] if a==b else [{'path':path,'oracle':a,'source_observation':b}]


def main():
    paths = sorted(p for p in CORPUS.rglob('*') if p.is_file() and p.suffix.lower() in ('.jcl','.prc','.proc'))
    observations = [observe(p) for p in paths]  # NO oracle read before this point.
    oracle_path = ROOT/'tests/golden_pending/carddemo_source/expectations.json'
    oracle_raw = oracle_path.read_bytes()
    assert digest(oracle_raw) == 'fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a'
    oracle = json.loads(oracle_raw)
    expected = {f['path']: f for f in oracle['files']}
    assert set(expected) == {f['path'] for f in observations} and len(observations)==48
    results = []
    for obs in observations:
        e = expected[obs['path']]
        checks = {'identity': differences({k:e[k] for k in ('path','sha256','encoding','input_kind')}, {k:obs[k] for k in ('path','sha256','encoding','input_kind')}),
                  'hierarchy': differences(e['expected_structure']['hierarchy'],obs['hierarchy']),
                  'flat_values_comments': differences(e['expected_structure']['statements'],obs['flat']),
                  'boundaries': differences(e['data_regions'],obs['regions']),
                  'records': differences(e['trace']['records'],obs['records']),
                  'tokens_values_positions': differences(e['trace']['statements'],obs['logical'])}
        results.append({'path':obs['path'],'status':'MATCH' if not any(checks.values()) else 'MISMATCH',
                        'checks':checks,'records':len(obs['records']),'steps':sum(s['operation']=='EXEC' for s in obs['logical']),
                        'dds':len(obs['dd_relations']),'regions':len(obs['regions']),'special':obs['special'],
                        'review_status':'PENDING','unverified':['human independent approval','runtime validity and semantics','PROC/INCLUDE resolution']})
    summary = {'files':len(results),'matched':sum(x['status']=='MATCH' for x in results),
               'mismatched':sum(x['status']!='MATCH' for x in results),
               'records':sum(x['records'] for x in results),'steps':sum(x['steps'] for x in results),
               'dds':sum(x['dds'] for x in results),'regions':sum(x['regions'] for x in results),
               'unnamed_dds':sum(len(x['special']['unnamed_dds']) for x in results)}
    (OUT/'source-ledger.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'comparison.json').write_text(json.dumps({'method':'CD3-card-relations-SQL-regex-grammar-v1','oracle_sha256':digest(oracle_raw),'summary':summary,'files':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    for r in results:
        if r['status'] != 'MATCH':
            print(r['path'],{k:v[:3] for k,v in r['checks'].items() if v})
    raise SystemExit(0 if summary['mismatched']==0 else 1)


if __name__ == '__main__':
    main()

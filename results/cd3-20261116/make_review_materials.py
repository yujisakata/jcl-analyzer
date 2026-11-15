"""Render CD-3 review evidence; never updates expectations, reviews, or approval metadata."""
import collections
import json
from pathlib import Path

OUT = Path(__file__).parent
ROOT = OUT.parents[1]
CORPUS = Path('D:/projects/aws-card/aws-mainframe-modernization-carddemo/app')
ledger = json.loads((OUT/'source-ledger.json').read_text())
oracle = json.loads((ROOT/'tests/golden_pending/carddemo_source/expectations.json').read_text())
expected = {x['path']: (i,x) for i,x in enumerate(oracle['files'])}
items = []


def item(category, f, lines, claim, basis, decision):
    ident = f'EX-{len(items)+1:03d}'
    index, case = expected[f['path']]
    selected = set(lines)
    evidence = [{'pointer':f'/files/{index}/expected_structure/statements/{j}', 'value':s}
                for j,s in enumerate(case['expected_structure']['statements']) if s['span'][0] in selected]
    evidence += [{'pointer':f'/files/{index}/data_regions/{j}', 'value':g}
                 for j,g in enumerate(case['data_regions']) if g['dd_line'] in selected or selected.intersection(g['lines'])]
    items.append({'id':ident,'category':category,'path':f['path'],'source_lines':sorted(set(lines)),
                  'oracle_pointer':f'/files/{index}',
                  'oracle_hierarchy_pointer':f'/files/{index}/expected_structure/hierarchy',
                  'oracle_evidence':evidence,'review_claim':claim,'basis':basis,
                  'human_decision':decision,'status':'PENDING','reviewer':None,'reviewed_at':None})


for f in ledger:
    s = f['special']
    if s['job_level_dds']:
        item('JOBLIB-DD',f,[28,29,30,32,33,34,40],s['job_level_dds'],
             'JCL-DD-001/013、CA-03。JOB開始と最初のEXECの間にあるDDはJOB側。',
             'JOBLIB32と無名33/34をJOB側の順序付き3 DDとして確認。SETとの配置の実行妥当性は別判断とし、SOURCE所属だけを承認するか。')
    for n in s['jcllib_named_joblib']:
        item('JOBLIB-LABEL-JCLLIB',f,[n],next(x for x in f['logical'] if x['line']==n),
             'JCL-REC-001、JCL-FMT-002、JCL-JCLLIB-001。文種はoperation欄。',
             'JOBLIBはname欄、operationはJCLLIB。DDやロードライブラリーへ誤分類しないか。ORDER文字列の保存と参照解決を分けるか。')
    if s['proc_pend']:
        item('PROC-PEND',f,s['proc_pend'],{'header':f['hierarchy']['procedure_header'],'pend_line':s['proc_pend'][-1],
                                         'steps':f['hierarchy']['procedure_steps'],
                                         'reachable_lines':f['hierarchy']['reachable_lines']},
             'JCL-PROC-002/004、ADR-031、CA-14。',
             'PROCをJOBへ変換せず、PENDをPROCルートのsource終端として確認するか。PENDの親はoracle単体の専用edgeではなくADR-031と固定checkerの検査も必要。')
    groups = collections.defaultdict(list)
    for d in s['unnamed_dds']:
        groups[d['owner'],d['concat_head']].append(d)
    for (owner, head), ds in groups.items():
        full = [d for d in f['dd_relations'] if d['owner']==owner and d['concat_head']==head]
        lines = [n for d in full for n in next(x['lines'] for x in f['logical'] if x['line']==d['line'])]
        item('CONCATENATION',f,lines,full,'JCL-DD-001、CA-03。name省略が直前DDへの連結、順序保持。',
             '名前なしDDの個数・順序・所有STEP/JOBと完全な連結先名を確認するか。DSN重複を除去していないか。')
    for g in f['regions']:
        if g['terminator']!='DELIMITER':
            lines = [g['dd_line'],*g['lines'][:1],*g['lines'][-1:]]
            if g['terminator_line']:
                lines.append(g['terminator_line'])
            item('EOF-DATA' if g['terminator']=='EOF' else 'NEXT-STATEMENT',f,lines,
                 {'region':g,'job_span':f['hierarchy']['jobs'][0]['span'] if f['input_kind']=='job' else None},
                 'JCL-DD-003、CA-13/14。DLMなしDD *は列1–2の//または/*、またはEOFで終了。',
                 '最終データ行を欠かさず、NEXT_STATEMENT行をデータへ含めていないか。EOFに架空のdelimiterを追加していないか。')
    for dup in s['duplicates']:
        steps = [x for x in (f['hierarchy']['jobs'][0]['steps'] if f['input_kind']=='job' else f['hierarchy']['procedure_steps']) if x['line'] in dup['lines']]
        item('SAME-NAMED-STEPS',f,dup['lines'],steps,'CA-14、JCL-EXEC-001。source個体は(path,先頭行)で識別。',
             '同名を統合せず別々のEXEC・DD所属を承認するか。名前参照の一意性・restart/COND解決やジョブ実行可能性は未承認として残すか。')
    for c in s['inline_comments']:
        stmt = next(x for x in f['logical'] if x['line']==c['statement'])
        flat = next(x for x in f['flat'] if x['span'][0]==c['statement'])
        item('COMMENT-AFTER-COMMA',f,stmt['lines'],{'span':flat['span'],'parameter_text':stmt['parameter_text'],
                                               'comment':flat['comment'],'comment_nonblank_start_column':36},
             'JCL-FMT-007、JCL-CONT-001。コメント欄は空白で区切り、パラメーター継続と共存可能。',
             '90行のカンマは34列、35列は空白、36列からの00,RECFM=FB), ATA.VSAM.KSDSはコメント欄。91行のDSNを同じDDへ接続する読取りを承認するか。原本の誤植訂正やパラメーター化はしないか。')
    if f['path']=='app-authorization-ims-db2-mq/jcl/DBPAUTP0.jcl':
        item('SEQUENCE-LOOKS-LIKE-COMMENT',f,[45],next(x for x in f['flat'] if x['span'][0]==45),
             'JCL-REC-002/003。通常JCLのoperandは71列以内。',
             '45行末の//*は列73以降で、別comment文でもoperandでもないか。rawレコードは末尾もハッシュで保持しているか。')
    date_lines=[r['line'] for r in f['records'] if r['role']=='DATA' and r['line'] in s['nonblank_72']]
    if date_lines:
        item('DATA-TRAILING-SLASHES',f,date_lines,
             {'role':'DATA','lines':date_lines,'raw_sha256':[f['records'][n-1]['raw_sha256'] for n in date_lines]},
             'JCL-REC-001の適用はデータ外。DD *のsentinelはレコード先頭。',
             '右端の//DateをJCL文/コメント/継続として扱わず、データの全バイトを保持するか。DFSORT制御入力の意味解釈はここで承認しないか。')
    nulls=[r['line'] for r in f['records'] if r['role']=='NULL']
    if nulls:
        item('NULL-SOURCE-ONLY',f,nulls,{'kind':'NULL','lines':nulls,'span':f['hierarchy']['jobs'][0]['span']},
             'JCL-REC-001、CA-14、残るA01/A03。',
             '原本NULL行をsource役割として保存することを承認し、JES/NULLJCLによる実行終了・後続文の扱いまで承認しないか。')

(OUT/'human-review-items.json').write_text(json.dumps({'status':'PENDING','oracle_sha256':'fd1fbf86c50857decdebd6ec722470252f250840145615098a6499315d44402a','items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

packet=['# CD-3 人間向け重点レビュー票','',
        '**全項目PENDING。機械MATCHは人の承認を意味しない。** 原本は読取専用。source行番号は1起点。',
        '各項目は原本の該当行・期待値箇所・IBM規則/内部契約・承認する命題を分けている。',
        '規則の版・頁・一次URLは本体報告の出典表とspecs/rules.yamlを参照。',
        'EX票だけの確認では全48件承認にならない。各ファイルの基本レビューも必要。','']
for i in items:
    packet += [f"## {i['id']} — {i['category']}",'',f"原本: `{i['path']}`、行 {', '.join(map(str,i['source_lines']))}",
               f"期待値JSON Pointerの起点: `{i['oracle_pointer']}`。階層: `{i['oracle_hierarchy_pointer']}`。",'',
               '```text']
    lines=(CORPUS/i['path']).read_text().splitlines()
    packet += [f'{n:4d} | {lines[n-1]}' for n in i['source_lines']]
    packet += ['```','','レビューする命題（sourceから導いた所属等を含む。原JSONそのものとは区別）:','','```json',json.dumps(i['review_claim'],ensure_ascii=False,indent=2),'```','',
               '凍結期待値の抜粋（原JSONから直接引用、Pointer付き）:','','```json',json.dumps(i['oracle_evidence'],ensure_ascii=False,indent=2),'```','',
               f"根拠: {i['basis']}",'',f"判定項目: {i['human_decision']}",'',
               '判定: **PENDING**。Reviewer: 未記入。Date: 未記入。理由/参照頁: 未記入。','']
(OUT/'human-review-packet.md').write_text('\n'.join(packet)+'\n',encoding='utf-8')

structures=['# CD-3 全48ファイル source構造レビュー台帳','','原本から独立導出した観測表。新しいGoldenでも承認記録でもない。','']
for f in ledger:
    h=f['hierarchy']; jobs=h['jobs']; steps=jobs[0]['steps'] if jobs else h['procedure_steps']
    structures += [f"## {f['path']}",'',f"SHA-256: `{f['sha256']}`。型: `{f['input_kind']}`。",
                   f"JOB範囲: `{jobs[0]['span'] if jobs else 'PROCメンバー; JOBへ変換しない'}`。PEND: `{f['special']['proc_pend'][-1:]}`。",'',
                   '| Owner先頭行 | STEP名 | EXEC target | DD名@先頭行（無名DDはhead/index） |','|---:|---|---|---|']
    if jobs and jobs[0]['dds']:
        structures.append('| JOB | — | — | '+', '.join(f"{d['name'] or '(無名)'}@{d['line']} [{d['concat_head']}/{d['concat_index']}]" for d in jobs[0]['dds'])+' |')
    for s in steps:
        structures.append(f"| {s['line']} | {s['name']} | {'='.join(s['target'])} | "+', '.join(f"{d['name'] or '(無名)'}@{d['line']} [{d['concat_head']}/{d['concat_index']}]" for d in s['dds'])+' |')
    structures += ['', '| DD行 | データ行 | 終了理由 | 終了行（データには含めない） |','|---:|---|---|---:|']
    structures += [f"| {g['dd_line']} | {g['lines'][0] if g['lines'] else 'なし'}–{g['lines'][-1] if g['lines'] else 'なし'} | {g['terminator']} | {g['terminator_line']} |" for g in f['regions']]
    structures += ['']
(OUT/'source-structure-ledger.md').write_text('\n'.join(structures)+'\n',encoding='utf-8')

cont=['# CD-3 継続181文・282継続行の照合台帳','','原文から導出。全segmentsはsource-ledger.json / comparison.jsonで照合。','',
      '| File | 論理文の物理行 | 原本パラメーター連結結果 |','|---|---|---|']
cols=['# CD-3 列72・73–80の重点確認台帳','','通常JCL・comment文・dataで列の扱いを混同しない。末尾を削除せず全rawのSHAとbyte範囲を照合済み。','',
      '| File | 行 | 役割 | 1–71列 | 72列 | 73–80列 |','|---|---:|---|---|---|---|']
for f in ledger:
    lines=(CORPUS/f['path']).read_text().splitlines()
    for s in f['logical']:
        if len(s['lines'])>1:
            cont.append(f"| {f['path']} | {','.join(map(str,s['lines']))} | `{s['parameter_text'].replace('|','&#124;')}` |")
    for n in sorted(set(f['special']['nonblank_72'])|set(f['special']['nonblank_73_80'])):
        raw=lines[n-1]
        pieces=[raw[:71],raw[71:72],raw[72:80]]
        cols.append(f"| {f['path']} | {n} | {f['records'][n-1]['role']} | "+' | '.join('`'+v.replace('|','&#124;')+'`' for v in pieces)+' |')
(OUT/'continuation-ledger.md').write_text('\n'.join(cont)+'\n',encoding='utf-8')
(OUT/'column-review-ledger.md').write_text('\n'.join(cols)+'\n',encoding='utf-8')

table=['| File | STEP | DD | 無名DD | Data領域 | 継続行 | 照合 | 人の承認 / 未検証 |','|---|---:|---:|---:|---:|---:|---|---|']
mapping={}
for f in ledger:
    ids=[i['id'] for i in items if i['path']==f['path']]
    mapping[f['path']]=ids
    table.append(f"| {f['path']} | {sum(s['operation']=='EXEC' for s in f['logical'])} | {len(f['dd_relations'])} | {len(f['special']['unnamed_dds'])} | {len(f['regions'])} | {sum(len(s['lines'])-1 for s in f['logical'])} | R1–R6 MATCH | PENDING; U1–U4; {', '.join(ids) or '基本確認のみ'} |")
(OUT/'file-review-table.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
(OUT/'review-index.json').write_text(json.dumps({'items':len(items),'categories':dict(collections.Counter(i['category'] for i in items)),
                                                'file_items':mapping},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'human_items':len(items),'categories':dict(collections.Counter(i['category'] for i in items))},indent=2))

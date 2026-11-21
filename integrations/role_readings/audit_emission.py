"""Compare the actual signed clause instances and the three compiler templates with Lean output.

Run from the patched NABT root with PYTHONPATH=src:. and Lake on PATH.
"""
import argparse,json,subprocess,tempfile
from pathlib import Path
from tools.grammar_catalog import masdar_frames as frames, named_matrix as matrix

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True,help="Directory containing fresh gateway replay folders")
parser.add_argument("--suite",choices=("retained","event"),default="event")
args=parser.parse_args()
w=args.output.resolve()
here=Path(__file__).resolve().parent
repo=here.parents[1]
catalog=[json.loads(line)["id"] for line in (here/(args.suite+".jsonl")).read_text().splitlines()]
wires=[]; metadata=[]
def append(binding,idx,wire,where):
    wires.append((binding,idx,wire))
    metadata.append(where)

for role in frames.ROLE_NAMES:
    env=dict(r="قراءة_اختبار",n="قراءة_اسم",x="عين_اختبار",g="نوع_اختبار",p="صفة_اختبار")
    binding=dict(role=role,reading=env['r'],noun=env['n'],entity=env['x'],genus=env['g'],trait=env['p'])
    for index,label in enumerate(('تحقق','انتفاء_الجنس','انتفاء_الخاصية')):
        [(rule,head,body)]=[row for row in frames.RULES if row[0]==label+'_الدور_'+role]
        def wire(s): return list(matrix.instantiate(s.split(),env))
        append(binding,index,[wire(head),[wire(v) for v in body]],'schema:'+role)

for key in catalog:
    receipt=json.loads((w/key/'receipt.json').read_text())
    m=receipt['execution']['owner_result']['named_matrix']
    for row in m['rule_instances']:
        if not row['head'][0].lstrip('!').startswith('صالح_'):continue
        head,body=row['head'],row['body']
        role=head[0].lstrip('!')[len('صالح_'):]
        labels=['تحقق_الدور_'+role,'انتفاء_الجنس_الدور_'+role,'انتفاء_الخاصية_الدور_'+role]
        b=dict(role=role,reading=head[1],noun=body[0][2],entity=head[2],genus=body[2][2],trait=body[3][2])
        append(b,labels.index(row['rule']),[head,body],key)

with tempfile.TemporaryDirectory() as d:
    path=Path(d)/'bindings.json';path.write_text(json.dumps([x[0] for x in wires],ensure_ascii=False))
    proc=subprocess.run(['lake','env','lean','--run','../integrations/usul_ledger/MasdarSlots.lean',str(path)],
                        cwd=repo/'formal',capture_output=True,text=True,check=True)
    results=json.loads(proc.stdout.splitlines()[-1])
    assert len(results)==len(wires)
    for i,((_,index,actual),result) in enumerate(zip(wires,results,strict=True)):
        assert result[index]==actual,(metadata[i],result[index],actual)
report={'all_matched':True,'templates':sum(x.startswith('schema:') for x in metadata),
        'receipt_instances':sum(not x.startswith('schema:') for x in metadata),
        'scenes_with_ground_slot_rules':len({x for x in metadata if not x.startswith('schema:')}),
        'roles':list(frames.ROLE_NAMES)}
(w/'emission_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))

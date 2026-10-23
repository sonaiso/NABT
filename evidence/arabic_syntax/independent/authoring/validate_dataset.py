from pathlib import Path
import json,hashlib
P=Path('/tmp/nabt-syntax-independent'); R=Path('/workspace/scratch/6e4178bfef09/nabt_integration/NABT')
assert hashlib.sha256((P/'episodes.json').read_bytes()).hexdigest()=='5b6c2a56b511065eb0cf1683cf9af63425501def33026b50cfc77b72997e5682'
assert hashlib.sha256((P/'real_excerpts.json').read_bytes()).hexdigest()=='15cf499465cc37fca126319243e6d9d113aaccb6f633a23b41fa8b500879981f'
assert hashlib.sha256((P/'scope_episodes.json').read_bytes()).hexdigest()=='a7ae71feba70c84cb86e1bea71c9b6ec473fc5504fd660d1fdf1a53f01adcfb9'
books={n:(R/f'src/nabt/data/source_evidence/{n}.txt').read_bytes() for n in ('qatr','alfiyya','sibawayhi')}
real=json.loads((P/'real_excerpts.json').read_text())['examples']
for e in real:
    b=books[e['source_id']]; raw=b[e['byte_start']:e['byte_end']]
    assert hashlib.sha256(b).hexdigest()==e['source_sha256']
    assert raw.decode()==e['raw_text']
    assert hashlib.sha256(raw).hexdigest()==e['excerpt_sha256']
    assert b[:e['byte_start']].count(b'\n')+1==e['source_line_1based']
    assert b[e['context_byte_start']:e['context_byte_end']].decode()==e['context_text']
# Previously public twelve intervals from TEXT_EVALUATION.md, not evaluator code.
old={'qatr':[(1452,1515),(1681,1785),(3822,3958),(3548,3819)],'alfiyya':[(2029,2115),(3256,3342),(12439,12536),(2996,3085)],'sibawayhi':[(9391,9520),(26150,26385),(522895,523141),(493166,493229)]}
assert all(not (e['byte_start']<end and start<e['byte_end']) for e in real for start,end in old[e['source_id']])
checks={'frozen_hashes_match':True,'source_hashes_match':True,'raw_intervals_match':True,'line_numbers_match':True,'parent_context_matches':True,'disjoint_previous_twelve_intervals':True,'real_count':len(real),'main_cases':40,'scope_cases':12}
(P/'dataset_validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks))

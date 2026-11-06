"""Bind existing i'rab rows to lower traces, scoped temporal premises and proofs.

This records applications and open bridge obligations; it does not manufacture
source-to-theorem fidelity or a general CertifiedBridge from collected reports.
"""
from collections import Counter
from copy import deepcopy

from nabt.errors import NabtError
from nabt.machine import Machine
from tools.arabic_training.unit_composition import execute, wire
from tools.evidence_lifecycle_v1 import ResourceLimit, _encoded
from tools.entropy_framework.reuse import current_catalog
from . import irab,temporal
from .operations import ROOT,source_snapshot,digest

CONTRACTS={
 'cell_identity':('Nabt.Sequence.codec_bijective','src/nabt/codec.py'),
 'effect':('Nabt.Machine.effect_append','src/nabt/machine.py'),
 'count':('Nabt.Count.count_eq_enumeration_length','src/nabt/machine.py'),
 'rank':('Nabt.Count.rank_unrankSpec','src/nabt/machine.py'),
 'inflection':('Nabt.InflectionEvidence.activation_exact','src/nabt/inflection_reader.py'),
 'construction':('Nabt.ConstructionEvidence.construction_activation_exact','src/nabt/construction_reader.py'),
 'qualifiers':('Nabt.DiscourseEvidence.projected_claim_keeps_qualifiers','src/nabt/discourse_reader.py'),
 'temporal':('Nabt.TemporalContext.check_confirmed_iff','tools/grammar_catalog/temporal.py'),
 'bridge':('Nabt.RecursiveSourceBridge.certified_bridge_realization','tools/recursive_bridge.py'),
}
BRIDGE=('sourceLicense','hostInventory','hostLicenses','grammarLicense','realizationAligned')


def proof_links():
    catalog,path,_,inputs=current_catalog(ROOT)
    declarations={r['name']:r for r in catalog['theorems']}
    rows=[]
    for operation,(name,owner) in CONTRACTS.items():
        d=declarations[name]
        rows.append({'operation':operation,'owner_path':owner,
                     'declaration':{k:d[k] for k in ('name','module','statement_sha256','source_path','source_sha256','range','proof_dependencies','type_dependencies')},
                     'relation':'EXPLICIT_SCOPED_EXECUTION_CONTRACT_REFERENCE',
                     'formal_application_established':False,'source_translation_fidelity_established':False})
    return {'catalog_path':path,'catalog_sha256':inputs[path],'links':rows,
            'authority':'EXISTING_COMPILED_CATALOG_NAVIGATION_NOT_PREMISE_DISCHARGE'}


def analyze(request):
    temporal.fields(request,('text',),('source_id','context','lexical_text','query','limit','mode','count_weight'))
    _encoded(request,2*1048576)
    text=request['text']
    if type(text) is not str or not text:raise ValueError('Exact nonempty source text required')
    if len(text.encode())>8192:raise ResourceLimit('Application source budget exceeded')
    source_id=temporal.label(request.get('source_id','input'))
    mode=request.get('mode','wasl')
    if type(mode) is not str or mode not in ('wasl','waqf'):raise ValueError('Unknown ending mode')
    weight=request.get('count_weight',1)
    if type(weight) is not int or weight<0:raise ValueError('Count weight must be a natural integer')
    if weight>2:raise ResourceLimit('Application count-weight budget exceeded')
    reference,time,legacy=temporal.context_envelope(request.get('context'))
    owner_request={k:deepcopy(request[k]) for k in ('text','lexical_text','query','limit') if k in request}
    owner_request.update(source_id=source_id,context=reference)
    try:grammar=irab.analyze(owner_request)
    except NabtError as exc:
        if exc.code=='RESOURCE_LIMIT':raise ResourceLimit(exc.message) from exc
        raise
    lower=execute({'op':'source','text':text,'source_id':source_id,'mode':mode})
    timing=temporal.evaluate({'text':text,'source_id':source_id,'temporal':time})
    links=proof_links();snapshot,_=source_snapshot()
    runs=lower['result'].get('written_runs',[])
    scopes=timing.get('scopes',[])
    scope_index={s['id']:s for s in scopes}
    def scope_depth(scope):
        depth=0
        while scope['parent'] is not None:
            scope=scope_index[scope['parent']];depth+=1
        return depth
    source_hash=grammar['source_sha256']
    if source_hash!=timing['source_sha256'] or (lower['result'].get('source_sha256',source_hash)!=source_hash):
        raise ValueError('Application owners refer to different source occurrences')
    rows=[]
    for index,row in enumerate(grammar['rows']):
        sp=row['span'];a,b=sp['start'],sp['end']
        if sp['source_id']!=source_id or sp['source_sha256']!=source_hash or text.encode()[a:b].decode()!=row['surface']:
            raise ValueError('Grammar assignment occurrence differs from the independent source')
        related=[i for i,r in enumerate(runs) if max(a,r['source_span']['start'])<min(b,r['source_span']['end'])]
        containing=[s for s in scopes if s['span'][0]<=a<b<=s['span'][1]]
        selected=max(containing,key=scope_depth) if containing else None
        lower_states=[]
        for i in related:
            words=runs[i]['owner_result']['words']
            lower_states.extend(w.get('native_receipt',{}).get('sound_shape_accepted') for w in words)
        record={'row_index':index,'owner':row['owner'],'frame_id':row['frame_id'],'reading_id':row['reading_id'],
                'source_span':deepcopy(sp),'irab_row_id':row['row_id'],'lower_run_indices':related,
                'lower_sound_shape_results':lower_states,'scope_id':selected['id'] if selected else None,
                'scope':deepcopy(selected),'source_relative_owner_accepted':row['licensed'],
                'role':row['actual_role'],'case_domain':row['assignment'].get('case_domain'),
                'temporal_node_ids':[n['id'] for n in timing['nodes'] if selected and n['scope_id']==selected['id'] and
                                     max(a,n['span'][0])<min(b,n['span'][1])],
                'premise_records':deepcopy(row['supports']),
                'progressive_license_status':'DEFER','missing_bridge_obligations':list(BRIDGE),
                'world_truth_established':False}
        record['application_id']=temporal.identity(record);rows.append(record)
    machine=Machine(mode);count=machine.count(weight)
    edges=[]
    for rank in sorted({0,count-1}) if count else []:
        cells=machine.unrank(weight,rank)
        restored=machine.rank(cells)
        if restored!=rank:raise ValueError('Count/rank/unrank owner disagreement')
        edges.append({'rank':rank,'cells':list(cells),'restored_rank':restored})
    source_rules={r['rule_key']:r for c in irab.catalog()['cards'] for r in c['rules']}
    report={'schema':'nabt.context-application.v1','status':'RECORDED_CONDITIONAL_APPLICATIONS' if rows else 'DEFER',
        'reason':None if rows else 'NO_OWNER_ASSIGNMENT_OCCURRENCES',
        'request_sha256':temporal.identity(request),'source_id':source_id,'source_sha256':source_hash,
        'execution_snapshot_sha256':digest(snapshot),'legacy_context_adapted':legacy,
        'context_schema':'nabt.discourse-context.v2','irab':grammar,'lower':lower,'temporal':timing,
        'applications':rows,'proof_links':links,
        'source_rule_links':[{'rule_key':key,'theorem_names':r['theorem_names'],
                             'status':'EXPLICIT_REFERENCES_ONLY' if r['theorem_names'] else 'SOURCE_TO_THEOREM_LINK_OPEN'}
                            for key,r in sorted(source_rules.items())],
        'counts':{'domain':'OWNER_EMITTED_ASSIGNMENT_OCCURRENCES','unit_identity':'OWNER_FRAME_READING_ROW_INDEX',
                  'total':len(rows),'accepted_by_owner':sum(r['source_relative_owner_accepted'] for r in rows),
                  'not_accepted_by_owner':sum(not r['source_relative_owner_accepted'] for r in rows),
                  'by_owner':dict(Counter(r['owner'] for r in rows)),'all_emitted_rows_retained':True,
                  'complete_for_arabic':False},
        'shape_count':{'count_domain':'A116_LICENSED_WORD_SHAPES','alphabet_id':'nabt.a116.v1',
                       'law_id':'nabt-sound-shape-v1','mode':mode,'weight':weight,'entry':0,'count':count,
                       'boundary_ranks':edges,'budget':{'maximum_weight':2},'search_complete':True,
                       'native_count_executed_here':False,'full_python_lean_refinement_claimed':False},
        'bridge':{'status':'DEFER','missing':list(BRIDGE),'application_license_granted':False},
        'retrieval_prunes_candidates':False,'neural_mastery_established':False,'world_truth_established':False}
    wire(report)
    return report


def verify(report,*,expected_request):
    return {'valid':wire(report)==wire(analyze(expected_request)),
            'verification':'INDEPENDENT_SOURCE_CONTEXT_LOWER_AND_OWNER_REPLAY','application_license_granted':False}

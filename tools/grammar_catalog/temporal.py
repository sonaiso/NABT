"""Source-bound, supplied S/R/E readings over closed Gregorian-day intervals.

Native checks establish arithmetic under these premises, never text meaning or
event actuality. No current clock, implicit reference time, or scope inheritance.
"""
from copy import deepcopy
from datetime import date
from hashlib import sha256
from itertools import product
from pathlib import Path
import subprocess
import tempfile

from nabt.discourse_context import read_context
from tools.arabic_training.unit_composition import read_json, wire
from tools.evidence_lifecycle_v1 import ResourceLimit, _encoded

ROOT=Path(__file__).resolve().parents[2]
SCHEMA='nabt.temporal-context.v1'
LAW='nabt.temporal-context.v1'
RELATIONS=('before','after','equals','intersects','contains','within')
MAX_ITEMS=32


def fields(value,required,optional=()):
    if type(value) is not dict or not set(required)<=value.keys() or set(value)-set(required)-set(optional):
        raise ValueError('Missing or unexpected temporal fields')


def identity(value): return sha256(wire(value).encode()).hexdigest()


def label(value):
    if type(value) is not str or not value or len(value.encode())>128:
        raise ValueError('Expected a bounded temporal identity')
    return value


def collection(value):
    if type(value) is not list: raise ValueError('Expected temporal record array')
    if len(value)>MAX_ITEMS: raise ResourceLimit('Temporal record budget exceeded')
    result={}
    for row in value:
        if type(row) is not dict: raise ValueError('Expected temporal record')
        key=label(row.get('id'))
        if key in result: raise ValueError('Duplicate temporal identity')
        result[key]=row
    return result


def span(raw, value):
    if type(value) is not list or len(value)!=2 or any(type(i) is not int for i in value):
        raise ValueError('Temporal spans use two byte offsets')
    a,b=value
    if not 0<=a<b<=len(raw): raise ValueError('Temporal span outside source')
    return raw[a:b].decode('utf-8')


def interval(value):
    fields(value,('first','last'))
    out={}
    for key in ('first','last'):
        if type(value[key]) is not str: raise ValueError('Dates use canonical YYYY-MM-DD')
        d=date.fromisoformat(value[key])
        if d.isoformat()!=value[key]: raise ValueError('Noncanonical date')
        out[key]=d.toordinal()
    if out['first']>out['last']: raise ValueError('Reversed temporal interval')
    return out


def dates(value):
    try: return {k:date.fromordinal(v).isoformat() for k,v in value.items()}
    except ValueError as exc: raise ResourceLimit('Result outside Gregorian calendar range 1..9999') from exc


def context_envelope(value):
    """Explicit v2 adaptation; legacy reader receives only its own premises."""
    if type(value) is dict and value.get('schema')=='nabt.discourse-context.v2':
        fields(value,('schema','reference','temporal'))
        read_context(value['reference'])
        return deepcopy(value['reference']),deepcopy(value['temporal']),False
    read_context(value)
    return deepcopy(value),None,True


def native(requests):
    if len(requests)>512: raise ResourceLimit('Temporal native check budget exceeded')
    if not requests:return {'available':True,'executed':False,'binary_sha256':None,'calls':[]}
    executable=ROOT/'formal/.lake/build/bin/temporalContextProbe'
    try: before=sha256(executable.read_bytes()).hexdigest()
    except FileNotFoundError:
        return {'available':False,'executed':False,'binary_sha256':None,'calls':[]}
    # Preserve ProbeJson's unsigned-number contract. Signed arithmetic inputs
    # use the canonical string convention of existing evidence/time owners.
    transport=[]
    for request in requests:
        r=deepcopy(request)
        for key in ('left','right','interval'):
            if r.get(key) is not None:
                if any(type(v) is not int for v in r[key].values()):
                    raise ValueError('Native temporal coordinates must be integers')
                r[key]={k:str(v) for k,v in r[key].items()}
        if 'days' in r:
            if type(r['days']) is not int:raise ValueError('Native temporal offset must be an integer')
            r['days']=str(r['days'])
        transport.append(r)
    encoded=(''.join(wire(r)+'\n' for r in transport)).encode()
    if len(encoded)>1048576:raise ResourceLimit('Temporal native input budget exceeded')
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
        try:
            result=subprocess.run([str(executable)],input=encoded,stdout=out,stderr=err,timeout=30,check=False)
        except subprocess.TimeoutExpired as exc: raise ResourceLimit('Temporal native time budget exceeded') from exc
        except FileNotFoundError:
            return {'available':False,'executed':False,'binary_sha256':None,'calls':[]}
        out.seek(0);raw=out.read(4*1048576+1);err.seek(0);errors=err.read(4096)
    if len(raw)>4*1048576:raise ResourceLimit('Temporal native output budget exceeded')
    if result.returncode or errors or sha256(executable.read_bytes()).hexdigest()!=before:
        raise ValueError('Temporal native process or binary identity failed')
    lines=raw.splitlines()
    if len(lines)!=len(requests):raise ValueError('Temporal response count mismatch')
    calls=[]
    for request,native_request,line in zip(requests,transport,lines):
        reply=read_json(line)
        if (reply.get('law_id')!=LAW or reply.get('status')!='OK' or
            wire(reply.get('request'))!=wire(native_request) or reply.get('scope')!='SUPPLIED_INTEGER_DAY_INTERVALS' or
            reply.get('world_truth_established') is not False):
            raise ValueError('Temporal native reply binding failed')
        if request['op']=='check' and reply.get('verdict') not in ('CONFIRMED','CONFLICT','UNKNOWN'):
            raise ValueError('Unknown temporal native verdict')
        if request['op']=='shift':
            expected={k:v+request['days'] for k,v in request['interval'].items()}
            if wire(reply.get('interval'))!=wire(expected) or reply.get('valid') is not True:
                raise ValueError('Native shift differs from exact supplied interval')
        calls.append({'request':deepcopy(request),'native_request':native_request,'response':reply})
    return {'available':True,'executed':True,'binary_sha256':before,'calls':calls}


def evaluate(request):
    fields(request,('text','temporal'),('source_id',))
    _encoded(request,262144)
    text=request['text']
    if type(text) is not str or not text:raise ValueError('Exact source text required')
    raw=text.encode()
    if len(raw)>8192:raise ResourceLimit('Temporal source budget exceeded')
    source_id=label(request.get('source_id','input'))
    value=request['temporal']
    if value is None:
        return {'schema':SCHEMA,'status':'UNKNOWN','source_id':source_id,'source_sha256':sha256(raw).hexdigest(),
                'reason':'NO_TEMPORAL_PREMISES','nodes':[],'relations':[],'native_checked':False,
                'world_truth_established':False,'implicit_speech_time_added':False}
    fields(value,('schema','scopes','evidence','nodes','relations'))
    if value['schema']!=SCHEMA:raise ValueError('Unknown temporal contract')
    scopes,evidence,nodes,relations=(collection(value[k]) for k in ('scopes','evidence','nodes','relations'))
    if not scopes:raise ValueError('At least one scope is required')
    roots=[]
    for key,row in scopes.items():
        fields(row,('id','parent','span','force','polarity'))
        span(raw,row['span'])
        if row['force'] not in ('assertion','quotation','conditional','question','command','possible'):
            raise ValueError('Unknown speech force')
        if row['polarity'] not in ('positive','negative'):raise ValueError('Unknown polarity')
        if row['parent'] is not None and type(row['parent']) is not str:
            raise ValueError('Scope parent must be an identity or null')
    for key,row in scopes.items():
        parent=row['parent']
        if parent is None:roots.append(key)
        elif parent not in scopes:raise ValueError('Unknown parent scope')
        seen={key}
        while parent is not None:
            if type(parent) is not str or parent not in scopes:raise ValueError('Unknown parent scope')
            if parent in seen:raise ValueError('Cyclic scope')
            seen.add(parent);p=scopes[parent]
            if not p['span'][0]<=row['span'][0]<row['span'][1]<=p['span'][1]:
                raise ValueError('Child scope crosses its parent')
            parent=p['parent']
    if len(roots)!=1 or scopes[roots[0]]['span']!=[0,len(raw)]:raise ValueError('One root scope must cover the exact source')
    for a,b in product(scopes.values(),repeat=2):
        if a['id']<b['id'] and a['parent']==b['parent'] and max(a['span'][0],b['span'][0])<min(a['span'][1],b['span'][1]):
            raise ValueError('Sibling scopes overlap')
    for row in evidence.values():
        fields(row,('id','kind','active'),('span','text','value'))
        if type(row['active']) is not bool:raise ValueError('Evidence activity must be Boolean')
        if row['kind']=='text':
            fields(row,('id','kind','active','span','text'))
            if span(raw,row['span'])!=row['text']:raise ValueError('Temporal witness differs from source bytes')
        elif row['kind']=='context':fields(row,('id','kind','active','value'))
        else:raise ValueError('Unknown temporal evidence kind')
    def support(ids,scope_id):
        if type(ids) is not list or not ids or any(type(k) is not str or k not in evidence for k in ids) or len(ids)!=len(set(ids)):
            raise ValueError('Distinct existing evidence IDs required')
        a,b=scopes[scope_id]['span']
        for key in ids:
            e=evidence[key]
            if e['kind']=='text' and not a<=e['span'][0]<e['span'][1]<=b:
                raise ValueError('Witness outside its scope')
        return all(evidence[k]['active'] for k in ids)
    values={key:[] for key in nodes}
    speech_scopes=set()
    for key,row in nodes.items():
        fields(row,('id','scope_id','role','span','anchors'))
        sid=label(row['scope_id'])
        if sid not in scopes or row['role'] not in ('S','R','E'):raise ValueError('Unknown node role or scope')
        a,b=scopes[sid]['span'];span(raw,row['span'])
        if not a<=row['span'][0]<row['span'][1]<=b:raise ValueError('Node outside its scope')
        if row['role']=='S':
            if sid in speech_scopes:raise ValueError('One speech node per scope; use alternative anchors')
            speech_scopes.add(sid)
        if type(row['anchors']) is not list or len(row['anchors'])>16:raise ValueError('Use at most 16 explicit anchors')
        for anchor in row['anchors']:
            fields(anchor,('interval','evidence_ids'))
            iv=interval(anchor['interval'])
            if support(anchor['evidence_ids'],sid):
                values[key].append({'interval':iv,'evidence_ids':sorted(anchor['evidence_ids']),'via':[]})
    incoming={k:[] for k in nodes}
    for key,row in relations.items():
        fields(row,('id','left','right','relation','evidence_ids'),('days',))
        if any(type(row[k]) is not str or row[k] not in nodes for k in ('left','right')):raise ValueError('Unknown relation node')
        if nodes[row['left']]['scope_id']!=nodes[row['right']]['scope_id']:raise ValueError('No implicit cross-scope temporal relation')
        support(row['evidence_ids'],nodes[row['left']]['scope_id'])
        if row['relation']=='offset_days':
            if type(row.get('days')) is not int:raise ValueError('Day offset must be an integer')
            if abs(row['days'])>36600:raise ResourceLimit('Day offset budget exceeded')
            incoming[row['left']].append(row)
        elif row['relation'] not in RELATIONS or 'days' in row:raise ValueError('Unknown temporal relation or unexpected offset')
    order=[];visiting=set();visited=set()
    def visit(key):
        if key in visiting:raise ValueError('Temporal derivation cannot justify itself')
        if key in visited:return
        visiting.add(key)
        for r in incoming[key]:visit(r['right'])
        visiting.remove(key);visited.add(key);order.append(key)
    for key in nodes:visit(key)
    shifts=[];shift_indices={key:[] for key in relations}
    for key in order:
        for r in incoming[key]:
            if not support(r['evidence_ids'],nodes[key]['scope_id']):continue
            for source in values[r['right']]:
                iv={k:v+r['days'] for k,v in source['interval'].items()};dates(iv)
                shift_indices[r['id']].append(len(shifts))
                shifts.append({'op':'shift','interval':source['interval'],'days':r['days']})
                values[key].append({'interval':iv,'evidence_ids':sorted(set(source['evidence_ids']+r['evidence_ids'])),
                                    'via':source['via']+[r['id']]})
                if len(values[key])>64:raise ResourceLimit('Temporal alternative budget exceeded')
    checks=[];groups=[]
    for key,r in relations.items():
        active=support(r['evidence_ids'],nodes[r['left']]['scope_id'])
        start=len(checks)
        if active and r['relation']!='offset_days':
            for a,b in product(values[r['left']] or [None],values[r['right']] or [None]):
                checks.append({'op':'check','relation':r['relation'],
                               'left':a['interval'] if a else None,'right':b['interval'] if b else None})
                if len(checks)+len(shifts)>512:raise ResourceLimit('Temporal alternative-pair budget exceeded')
        groups.append((key,active,start,len(checks)))
    receipt=native(shifts+checks)
    replies=receipt['calls'][len(shifts):]
    results=[]
    for key,active,a,b in groups:
        r=relations[key]
        if not active:status='WITHDRAWN'
        elif not receipt['available']:status='DEFER'
        elif r['relation']=='offset_days':status='DERIVED' if values[r['right']] else 'UNKNOWN'
        else:
            states={x['response']['verdict'] for x in replies[a:b]}
            status=next(iter(states)) if len(states)==1 else 'AMBIGUOUS'
        indices=shift_indices[key] if r['relation']=='offset_days' else list(range(len(shifts)+a,len(shifts)+b))
        results.append({**deepcopy(r),'status':status,'native_call_indices':indices})
    output_nodes=[]
    for key,row in nodes.items():
        output_nodes.append({**deepcopy(row),'candidates':[dict(v,dates=dates(v['interval'])) for v in values[key]],
                             'absolute_time_known':bool(values[key]),'event_occurrence_established':False})
    statuses={r['status'] for r in results}
    ambiguous=any(len({wire(c['interval']) for c in v})>1 for v in values.values())
    status=('DEFER' if not receipt['available'] else 'CONFLICT' if 'CONFLICT' in statuses else
            'PARTIAL' if ambiguous or not receipt['executed'] or statuses & {'UNKNOWN','AMBIGUOUS','WITHDRAWN'} or any(not v for v in values.values()) else 'CHECKED')
    return {'schema':SCHEMA,'law_id':LAW,'status':status,'source_id':source_id,'source_sha256':sha256(raw).hexdigest(),
        'request_sha256':identity(request),'scopes':deepcopy(list(scopes.values())),'evidence':deepcopy(list(evidence.values())),
        'nodes':output_nodes,'relations':results,'native_receipt':receipt,'native_checked':receipt['executed'],
        'authority':'CONDITIONAL_ON_SUPPLIED_SOURCE_INTERPRETATIONS','calendar':'proleptic_gregorian_integer_days',
        'world_truth_established':False,'empirical_causality_established':False,'implicit_speech_time_added':False,
        'unanchored_constraint_network_complete':False,'arabic_time_interpretation_acquired':False}


def verify(report,*,expected_request):
    return {'valid':wire(report)==wire(evaluate(expected_request)),
            'verification':'FRESH_SOURCE_CONTEXT_AND_NATIVE_REPLAY','world_truth_established':False}

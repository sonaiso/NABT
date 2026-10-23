"""Independent, frozen-data comparisons; imports no NABT implementation."""
from __future__ import annotations
from hashlib import sha256

def atom_key(atom, *, variable_names=False):
    assert type(atom['positive']) is bool
    args=tuple('?x' if variable_names and x.startswith('?') else x for x in atom['args'])
    return atom['predicate'],args,atom['positive']

def rule_key(rule):
    # The manual universal gold uses one variable only. A runtime rule with two
    # distinct variables cannot be collapsed into the one-variable oracle.
    vars_={x for a in [*rule['body'],rule['head']] for x in a['args'] if x.startswith('?')}
    if len(vars_)>1: return ('multi_variable_not_in_gold',str(rule))
    return tuple(sorted(atom_key(a,variable_names=True) for a in rule['body'])),atom_key(rule['head'],variable_names=True)

def check_span(span,raw,source_id):
    assert span['source_id']==source_id
    assert span['source_sha256']==sha256(raw).hexdigest()
    start,end=span['start'],span['end']
    assert type(start) is int and type(end) is int and 0<=start<end<=len(raw)
    part=raw[start:end]; part.decode('utf-8')
    assert span['span_sha256']==sha256(part).hexdigest()
    return part

def restore_segments(parsed,raw,source_id):
    offset=0; restored=b''
    for s in parsed['segments']:
        assert s['span']['start']==offset
        part=check_span(s['span'],raw,source_id)
        restored+=part; offset=s['span']['end']
    assert restored==raw
    return True

def substitute(atom,binding):
    result={'predicate':atom['predicate'],'positive':atom['positive'],'args':[binding.get(x,x) for x in atom['args']]}
    assert all(not x.startswith('?') for x in result['args'])
    return result

def independent_certificate(certificate,active_sources,scope,manual_oracle):
    """Replay known source clauses and substitutions against hand-authored gold.

    This verifies exact evidence and the finite certificate, not the correctness
    of an unrestricted Arabic interpretation or external truth. Source-wide gold
    carries interpretation; spans must still be exact and contain all literal
    names used in a fact. The oracle never invokes the production verifier.
    """
    assert certificate['scope']==scope
    assert certificate['world_truth']=='NOT_ESTABLISHED'
    steps=certificate['steps']; derived=[]
    assert type(certificate['conclusion']) is int and steps
    for step in steps:
        clause=step['clause']; source_id=clause['source_id']
        raw=active_sources[source_id].encode('utf-8')
        gold=manual_oracle[sha256(raw).hexdigest()]
        assert clause['scope']==scope and clause['source_sha256']==sha256(raw).hexdigest()
        span_bytes=check_span(clause['span'],raw,source_id)
        for part in clause['component_spans']:
            check_span(part,raw,source_id)
            assert clause['span']['start']<=part['start']<part['end']<=clause['span']['end']
        if 'atom' in clause:
            assert atom_key(clause['atom']) in {atom_key(a) for a in gold['facts']}
            assert step['premises']==[] and step['binding']=={}
            result=clause['atom']
            # Every data name must appear inside this precise statement; an
            # unrelated same-source sentence cannot certify this fact.
            for label in [result['predicate'],*result['args']]:
                assert label.encode('utf-8') in span_bytes
        else:
            rule={'body':clause['body'],'head':clause['head']}
            assert rule_key(rule) in {rule_key(r) for r in gold['rules']}
            binding=step['binding']; premises=step['premises']
            assert len(premises)==len(rule['body'])
            for premise,idx in zip(rule['body'],premises):
                assert type(idx) is int and 0<=idx<len(derived)
                assert atom_key(substitute(premise,binding))==atom_key(derived[idx])
            result=substitute(rule['head'],binding)
        assert atom_key(result)==atom_key(step['atom'])
        derived.append(result)
    idx=certificate['conclusion']; assert 0<=idx<len(derived)
    assert atom_key(derived[idx])==atom_key(certificate['query'])
    return True

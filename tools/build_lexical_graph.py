"""Compile a sense-specific graph from NABT's pinned lexical interpretation.

References and licensed Horn rules remain separate. Compilation does not parse
glosses, invent roots, resolve speaker intent or establish outside facts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from tools.lexical_completion import CompletionEngine, CATALOG_SHA, canonical, replay, sha
from tools.lexical_testimony import _native, _strict_json

FOLDER = Path('evidence/lexical_graph_v1')
REFERENCES_SHA = '03d4475545ef82a1a4042af9cbbdf7c43bf890416d97f51a87e91d8a04aebf02'
LAW = 'nabt.lexical-graph.v1'
SCOPE = 'authored-lexical-interpretation.v2'


def source_id(citation):
    return 'source:' + sha(canonical(citation).encode())


def compile_graph(completion):
    catalogue = completion.catalogue
    raw = (completion.root / FOLDER / 'reference_edges.json').read_bytes()
    if sha(raw) != REFERENCES_SHA:
        raise ValueError('REFERENCE_LEDGER_CHANGED')
    references = _strict_json(raw)
    if references['catalogue_sha256'] != CATALOG_SHA:
        raise ValueError('REFERENCE_CATALOGUE_CHANGED')
    nodes, rules, refs, entries, sources, unresolved = [], [], [], {}, {}, []
    by_sense = {s['id']: s for s in catalogue['senses']}

    def node(identifier, sense, component, kind):
        nodes.append({'id': identifier, 'sense_id': sense['id'], 'component': component,
                      'scope': SCOPE, 'kind': kind, 'entry': sense['root']})

    def source(citation):
        replay(citation, completion.sources)
        identifier = source_id(citation)
        sources[identifier] = citation
        return identifier

    def rule(identifier, sense, dimension, body, head, target, citation, operation):
        rules.append({'id': identifier, 'source': source(citation), 'dimension': dimension,
                      'body': body, 'head': head, 'operation': operation,
                      'license': {'sense_id': sense['id'], 'entry': sense['root'],
                                  'target': target, 'indication': dimension},
                      'interpretation_status': 'AUTHORED_NOT_INDEPENDENTLY_ADJUDICATED'})

    for sense in catalogue['senses']:
        sid = sense['id']
        entries.setdefault(sense['root'], []).append(sid)
        whole = 'sense:' + sid
        node(whole, sense, 'WHOLE_INTERPRETATION', 'interpreted_whole')
        source(sense['citation'])
        components = sense['components']
        if not components:
            unresolved.append(sid)
            continue
        if len(components) != len(set(components)):
            raise ValueError('DUPLICATE_COMPONENT_INTERPRETATION')
        component_ids = []
        for i, component in enumerate(components):
            cid = f'component:{sid}:{i}'
            component_ids.append(cid)
            node(cid, sense, component, 'conceptual_component')
            rule(f'projection:{sid}:{i}', sense, 'mutabaqa' if len(components) == 1 else 'tadammun',
                 [whole], cid, [component], sense['citation'], 'whole_to_component')
        rule('composition:' + sid, sense, 'mutabaqa', component_ids, whole,
             components, sense['citation'], 'all_components_to_defined_whole')

    for i, necessity in enumerate(catalogue['necessities']):
        sense = by_sense[necessity['sense_id']]
        if necessity['kind'] != 'mental' or not sense['components']:
            raise ValueError('UNSUPPORTED_NECESSITY')
        nid = f'necessity:{sense["id"]}:{i}'
        node(nid, sense, necessity['target'], 'mental_condition_not_world_fact')
        rule('necessity-rule:' + str(i), sense, 'iltizam', ['sense:' + sense['id']], nid,
             [necessity['target']], necessity['citation'], 'declared_mental_necessity')

    for ref in references['edges']:
        if (ref['kind'] != 'opposition_reference' or ref['entailment_rule'] is not False
                or ref['world_fact'] is not False):
            raise ValueError('REFERENCE_AUTHORITY_CHANGED')
        start, end = by_sense[ref['source_sense_id']], by_sense[ref['target_sense_id']]
        if canonical(ref['citation']) != canonical(start['citation']):
            raise ValueError('REFERENCE_SOURCE_DIFFERS')
        refs.append({'id': ref['id'], 'source': source(ref['citation']),
                     'dimension': ref['kind'], 'body': ['sense:' + start['id']],
                     'head': 'sense:' + end['id'], 'inference_authority': False,
                     'alignment_status': ref['alignment_status']})
    return {'schema': LAW, 'catalogue_sha256': CATALOG_SHA, 'reference_ledger_sha256': REFERENCES_SHA,
            'nodes': nodes, 'rules': rules, 'references': refs, 'entries': entries,
            'sources': sources, 'unresolved_senses': unresolved,
            'whole_interpretation': 'conjunction of the declared conceptual components at this sense and scope',
            'assumptions_are_world_facts': False, 'transmission_type': 'UNASSESSED',
            'python_compiler_refinement_proved': False, 'all_arabic_complete': False}


def audit_licenses(graph, completion):
    """Actual existing native indication checks, not a Python-only authority."""
    exe = completion.exe
    binary_sha = sha(exe.read_bytes())
    if canonical(_native(exe)) != canonical(completion.exported()):
        raise ValueError('NATIVE_CATALOGUE_DIFFERS')
    cache, checked = {}, []
    for rule in graph['rules']:
        license = rule['license']
        request = {'slots': [{'entry': license['entry'], 'target': license['target']}]}
        key = canonical(request)
        if key not in cache:
            actual = _native(exe, request)
            if canonical(actual) != canonical(completion.expected_native(request['slots'])):
                raise ValueError('NATIVE_INDICATION_RESULT_DIFFERS')
            cache[key] = actual
        readings = cache[key]['slots'][0]['readings']
        row = next(r for r in readings if r['sense_id'] == license['sense_id'])
        if license['indication'] not in row['indications']:
            raise ValueError('EDGE_WITHOUT_NATIVE_INDICATION')
        checked.append({'rule_id': rule['id'], 'sense_id': license['sense_id'],
                        'target': license['target'], 'indication': license['indication'],
                        'native_request': request, 'native_reading': row})
    if sha(exe.read_bytes()) != binary_sha:
        raise ValueError('NATIVE_CHANGED_DURING_LICENSE_AUDIT')
    return {'schema': 'nabt.lexical-graph-license-audit.v1', 'native_sha256': binary_sha,
            'native_executions': len(cache) + 1, 'checked_rules': checked,
            'compiler_refinement_proved': False, 'whole_arabic_complete': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--audit-output', type=Path)
    args = parser.parse_args()
    completion = CompletionEngine()
    graph = compile_graph(completion)
    path = ROOT / FOLDER / 'graph.json'
    encoded = json.dumps(graph, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if path.read_text() != encoded:
            raise ValueError('GENERATED_GRAPH_DRIFT')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded)
    audit = audit_licenses(graph, completion)
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        args.audit_output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'nodes': len(graph['nodes']), 'rules': len(graph['rules']),
                      'references': len(graph['references']), 'graph_sha256': sha(path.read_bytes()),
                      'native_license_checks': len(audit['checked_rules'])}))


if __name__ == '__main__':
    main()

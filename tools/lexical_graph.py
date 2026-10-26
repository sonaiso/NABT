"""Source-bound semantic graph, with explicit hypothetical interpretation seeds.

Lean computes the least installed Horn closure. Reference cycles are visible
but cannot supply premises. This is not free-text understanding or world truth.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from tools.lexical_completion import CompletionEngine, canonical, sha
from tools.lexical_testimony import _native, _strict_json
from tools.build_lexical_graph import LAW, FOLDER, compile_graph, audit_licenses

GRAPH_SHA = '9f4c49364e8682057212cf080df5bd97ff71f4601b0146aa507872227c027bbb'
SEMANTIC_DIMENSIONS = {'mutabaqa', 'tadammun', 'iltizam'}
DISCLAIMER = ('الإغلاق بالنسبة إلى الرسم المثبت والمقدمات الافتراضية المعلنة؛ '
              'الإحالة المعجمية ليست استلزامًا، والنتيجة لا تثبت المراد أو الواقع أو اكتمال العربية.')


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

class GraphError(ValueError):
    pass


def validate(request):
    if type(request) is not dict or set(request) != {'assumed_senses', 'targets', 'budget'}:
        raise GraphError('INVALID_INPUT')
    if type(request['budget']) is not int or request['budget'] < 0:
        raise GraphError('INVALID_INPUT')
    if request['budget'] > 512:
        raise GraphError('RESOURCE_LIMIT')
    for name, limit in [('assumed_senses', 42), ('targets', 256)]:
        items = request[name]
        if type(items) is not list:
            raise GraphError('INVALID_INPUT')
        if len(items) > limit:
            raise GraphError('RESOURCE_LIMIT')
        for item in items:
            if type(item) is not str or not item.strip() or any(ord(c) < 32 for c in item):
                raise GraphError('INVALID_INPUT')
            try:
                encoded = item.encode('utf-8')
            except UnicodeError as error:
                raise GraphError('INVALID_INPUT') from error
            if len(encoded) > 128:
                raise GraphError('RESOURCE_LIMIT')
        if len(items) != len(set(items)):
            raise GraphError('INVALID_INPUT')


def strong_components(node_ids, pairs):
    """All-edge iterative SCC analysis; structural information, not inference."""
    forward = {n: set() for n in node_ids}
    reverse = {n: set() for n in node_ids}
    for start, end in pairs:
        forward[start].add(end)
        reverse[end].add(start)
    seen, order = set(), []
    for first in sorted(forward):
        if first in seen:
            continue
        stack = [(first, False)]
        while stack:
            node, finished = stack.pop()
            if finished:
                order.append(node)
            elif node not in seen:
                seen.add(node)
                stack.append((node, True))
                stack.extend((child, False) for child in sorted(forward[node], reverse=True) if child not in seen)
    seen, components = set(), []
    for first in reversed(order):
        if first in seen:
            continue
        stack, component = [first], []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            component.append(node)
            stack.extend(reverse[node] - seen)
        if len(component) > 1 or first in forward[first]:
            components.append(sorted(component))
    return sorted(components)


def reverse_dependencies(graph, targets):
    """Return every conditional prerequisite, without treating it as acquired."""
    by_head = {}
    for rule in graph['rules']:
        by_head.setdefault(rule['head'], []).append(rule)
    reports = []
    for target in targets:
        todo, nodes, rules = [target], set(), set()
        while todo:
            node = todo.pop()
            if node in nodes:
                continue
            nodes.add(node)
            for rule in by_head.get(node, []):
                rules.add(rule['id'])
                todo.extend(rule['body'])
        reports.append({'target': target, 'node_ids': sorted(nodes), 'rule_ids': sorted(rules),
                        'authority': 'PREREQUISITE_INSPECTION_NOT_A_PROOF'})
    return reports


def expected_native(request):
    """Transport cross-check; the independent tests use all-model intersection."""
    nodes = {n['id']: n for n in request['nodes']}
    active, inactive = [], []
    for rule in request['rules']:
        head = nodes[rule['head']]
        reason = ('REFERENCE_ONLY' if rule['dimension'] not in SEMANTIC_DIMENSIONS else
                  'INACTIVE_SOURCE' if rule['source'] not in request['active_sources'] else
                  'SCOPE_MISMATCH' if any(nodes[b]['scope'] != head['scope'] for b in rule['body']) else
                  'SENSE_MISMATCH' if any(nodes[b]['sense_id'] != head['sense_id'] for b in rule['body']) else None)
        if reason:
            inactive.append({'rule_id': rule['id'], 'reason': reason})
        else:
            active.append(rule)
    pending = list(active)
    known, trace = set(request['seeds']), []
    while True:
        ready = next((r for r in pending if r['head'] not in known and set(r['body']) <= known), None)
        if ready is None or len(trace) == request['budget']:
            complete = ready is None
            break
        known.add(ready['head'])
        trace.append(ready['id'])
        pending.remove(ready)
    return {'law_id': LAW, 'status': 'CHECKED_CLOSURE' if complete else 'RESOURCE_EXHAUSTED',
            'complete': complete, 'closure_checked': complete,
            'known': [n['id'] for n in request['nodes'] if n['id'] in known], 'trace': trace,
            'seed_assumptions': request['seeds'], 'active_rule_ids': [r['id'] for r in active],
            'inactive': inactive, 'activation_count': len(trace), 'budget': request['budget'],
            'rule_count': len(request['rules']), 'active_rule_count': len(active),
            'world_truth_established': False, 'all_arabic_complete': False}


class GraphEngine:
    """Immutable source snapshot; construct a new engine when sources change."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        try:
            self.completion = CompletionEngine(self.root)
            raw = (self.root / FOLDER / 'graph.json').read_bytes()
            if sha(raw) != GRAPH_SHA:
                raise ValueError('GRAPH_IDENTITY_CHANGED')
            self.graph = _strict_json(raw)
            if canonical(self.graph) != canonical(compile_graph(self.completion)):
                raise ValueError('GRAPH_COMPILATION_DIFFERS')
        except (OSError, ValueError, KeyError) as error:
            raise GraphError('SOURCE_UNAVAILABLE') from error
        try:
            self.license_audit = audit_licenses(self.graph, self.completion)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            raise GraphError('VERIFICATION_UNAVAILABLE') from error
        self.frozen_graph = canonical(self.graph)
        self.exe = ROOT / 'formal/.lake/build/bin/lexicalGraph'
        self.nodes = {n['id']: n for n in self.graph['nodes']}
        self.senses = {s['id'] for s in self.completion.catalogue['senses']}
        self.source_hashes = {work: sha(blob) for work, blob in self.completion.sources.items()}
        node_ids = list(self.nodes)
        pairs = lambda rs: [(b, r['head']) for r in rs for b in r['body']]
        self.topology = {
            'reference_cycles': strong_components(node_ids, pairs(self.graph['references'])),
            'inference_dependency_cycles': strong_components(node_ids, pairs(self.graph['rules'])),
            'authority': 'STRUCTURE_ONLY_NOT_SEMANTIC_ENTAILMENT',
            'and_premises_cannot_be_replaced_by_reachability': True,
        }

    def inventory(self):
        return deepcopy({**self.graph, 'graph_sha256': GRAPH_SHA, 'topology': self.topology,
                         'nodes_count': len(self.nodes), 'rule_count': len(self.graph['rules']),
                         'reference_count': len(self.graph['references']), 'native_license_checks': len(self.license_audit['checked_rules']),
                         'scope': 'INSTALLED_AUTHORED_SENSES_NOT_ALL_ARABIC_ROOTS'})

    def assess(self, request):
        foundation.require_foundation('tools.lexical_graph.graphengine.assess')
        validate(request)
        if canonical(self.graph) != self.frozen_graph:
            raise GraphError('SOURCE_UNAVAILABLE')
        if (any(s not in self.senses for s in request['assumed_senses'])
                or any(t not in self.nodes for t in request['targets'])):
            raise GraphError('INVALID_INPUT')
        if set(request['assumed_senses']) & set(self.graph['unresolved_senses']):
            raise GraphError('UNMEASURED_DEFINITION')
        native_request = {
            'nodes': [{k: n[k] for k in ('id', 'sense_id', 'component', 'scope')} for n in self.graph['nodes']],
            'rules': [{k: r[k] for k in ('id', 'source', 'dimension', 'body', 'head')}
                      for r in self.graph['rules'] + self.graph['references']],
            'seeds': ['sense:' + s for s in request['assumed_senses']],
            'active_sources': sorted(self.graph['sources']), 'budget': request['budget'],
        }
        binary_sha = sha(self.exe.read_bytes())
        native = _native(self.exe, native_request)
        if canonical(native) != canonical(expected_native(native_request)):
            raise GraphError('VERIFICATION_UNAVAILABLE')
        if sha(self.exe.read_bytes()) != binary_sha:
            raise GraphError('VERIFICATION_UNAVAILABLE')
        known = set(native['known'])
        results = [{'node_id': t, 'status': 'DERIVED_UNDER_ASSUMPTIONS' if t in known else
                    'NOT_DERIVED_IN_INSTALLED_GRAPH' if native['complete'] else 'UNKNOWN_RESOURCE_EXHAUSTED'}
                   for t in request['targets']]
        return {'schema': LAW, 'status': native['status'], 'native_checked': True,
                'request_sha256': sha(canonical(request).encode()), 'graph_sha256': GRAPH_SHA,
                'native_sha256': binary_sha, 'lexical_checker_sha256': self.license_audit['native_sha256'],
                'source_sha256': deepcopy(self.source_hashes), 'native_request': deepcopy(native_request), 'native_result': native,
                'assumptions': [{'sense_id': s, 'authority': 'DECLARED_HYPOTHETICAL_INTERPRETATION',
                                 'world_fact': False} for s in request['assumed_senses']],
                'target_results': results, 'topology': deepcopy(self.topology),
                'reverse_dependencies': reverse_dependencies(self.graph, request['targets']),
                'unresolved_senses': list(self.graph['unresolved_senses']),
                'scope': 'SOURCE_RELATIVE_LEAST_CLOSURE_OF_EXPLICIT_HYPOTHESES',
                'all_arabic_complete': False, 'world_truth_established': False,
                'speaker_intent_established': False, 'transmission_type': 'UNASSESSED',
                'python_compiler_refinement_proved': False, 'app_disclaimer': DISCLAIMER}


def failure(status):
    return {'schema': LAW, 'status': status, 'native_checked': False,
            'all_arabic_complete': False, 'world_truth_established': False,
            'app_disclaimer': DISCLAIMER}


def request_json(raw):
    """Validate numeric spellings before Python can normalize -0 to zero."""
    text = raw.decode('utf-8', errors='strict')
    request = _strict_json(text)

    def unsigned_integer(token):
        if token.startswith('-'):
            raise ValueError('NONCANONICAL_INTEGER')
        return int(token)

    def no_decimal(_):
        raise ValueError('NONINTEGER_NUMBER')

    json.loads(text, parse_int=unsigned_integer, parse_float=no_decimal)
    return request


def assess(request, *, engine=None):
    foundation.require_foundation('tools.lexical_graph.assess')
    try:
        validate(request)
        engine = engine or GraphEngine()
        return engine.assess(request)
    except GraphError as error:
        return failure(str(error))
    except subprocess.TimeoutExpired:
        return failure('RESOURCE_EXHAUSTED')
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
        return failure('VERIFICATION_UNAVAILABLE')


def main():
    foundation.require_foundation('tools.lexical_graph.main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--inventory', action='store_true')
    args = parser.parse_args()
    if args.inventory:
        try:
            result = GraphEngine().inventory()
        except GraphError as error:
            result = failure(str(error))
    elif args.request:
        try:
            with args.request.open('rb') as stream:
                raw = stream.read(65537)
            result = assess(request_json(raw)) if len(raw) <= 65536 else failure('RESOURCE_LIMIT')
        except (OSError, ValueError, UnicodeError):
            result = assess(None)
    else:
        parser.error('choose --inventory or --request')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('native_checked') is True or 'nodes' in result else 2


if __name__ == '__main__':
    raise SystemExit(main())

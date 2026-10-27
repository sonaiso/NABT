"""Independent finite-model oracle and hostile graph/provenance controls.

The oracle intersects every closed superset of the explicit assumptions. It
does not reuse the production forward-chaining recurrence or its stopping test.
These synthetic graph controls are not an Arabic population benchmark.
"""
from copy import deepcopy
import itertools
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'formal/.lake/build/bin/lexicalGraph'
SEMANTIC = {'mutabaqa', 'tadammun', 'iltizam'}


def fixture(size, rules=(), seeds=(), budget=512):
    """Synthetic premise labels, deliberately not Arabic lexical evidence."""
    return {
        'nodes': [{'id': f'n{i}', 'sense_id': 'sense:fixture', 'component': f'p{i}',
                   'scope': 'scope:fixture'} for i in range(size)],
        'rules': [{'id': f'r{i}', 'source': 'source:fixture', 'dimension': 'iltizam',
                   'body': [f'n{n}' for n in body], 'head': f'n{head}'}
                  for i, (body, head) in enumerate(rules)],
        'seeds': [f'n{i}' for i in seeds],
        'active_sources': ['source:fixture'], 'budget': budget,
    }


def active_rules(request):
    nodes = {node['id']: node for node in request['nodes']}
    return [rule for rule in request['rules']
            if rule['dimension'] in SEMANTIC and rule['source'] in request['active_sources']
            and all(nodes[p]['scope'] == nodes[rule['head']]['scope']
                    and nodes[p]['sense_id'] == nodes[rule['head']]['sense_id']
                    for p in rule['body'])]


def finite_model_intersection(request):
    """Least Horn model by all-model enumeration, not iteration to a fixed point."""
    universe = {node['id'] for node in request['nodes']}
    ordered = sorted(universe)
    rules = active_rules(request)
    models = []
    for flags in itertools.product((False, True), repeat=len(ordered)):
        model = {name for name, flag in zip(ordered, flags) if flag}
        if not set(request['seeds']) <= model:
            continue
        if all(not set(rule['body']) <= model or rule['head'] in model for rule in rules):
            models.append(model)
    # The finite universe is always a model of well-formed positive Horn rules.
    assert models
    return set.intersection(*models)


def native_batch(requests):
    encoded = b''.join(json.dumps(r, ensure_ascii=False).encode() + b'\n' for r in requests)
    run = subprocess.run([str(EXE)], input=encoded, capture_output=True, check=True, timeout=60)
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    if len(rows) != len(requests):
        raise AssertionError('native JSONL did not return one receipt per request')
    return rows


def exhaustive_native_oracle_report():
    """Reusable evidence generator; the test and report run this same oracle."""
    templates = [([0], 1), ([1], 2), ([2], 0), ([0, 1], 2),
                 ([1, 2], 0), ([0, 2], 1), ([0], 0), ([1], 1), ([2], 2)]
    cases = []
    for enabled in itertools.product((False, True), repeat=len(templates)):
        rules = [rule for rule, flag in zip(templates, enabled) if flag]
        for seed_mask in itertools.product((False, True), repeat=3):
            cases.append(fixture(3, rules, [i for i, flag in enumerate(seed_mask) if flag]))
    failures = []
    for index, (request, receipt) in enumerate(zip(cases, native_batch(cases))):
        expected = finite_model_intersection(request)
        correct = (receipt.get('status') == 'CHECKED_CLOSURE'
                   and receipt.get('complete') is True
                   and set(receipt.get('known', [])) == expected
                   and receipt.get('world_truth_established') is False
                   and receipt.get('all_arabic_complete') is False)
        if not correct:
            failures.append({'case_index': index, 'expected_known': sorted(expected),
                             'receipt': receipt})
    return {
        'schema': 'nabt.lexical-graph-independent-oracle.v1',
        'test': 'tests.test_lexical_graph.NativeGraphOracleTests.test_4096_tiny_graphs_against_closed_subset_intersection',
        'oracle': 'intersection_of_all_closed_seed_supersets',
        'independent_of_production_recurrence': True,
        'node_count': 3, 'rule_template_count': len(templates),
        'graph_count': 2 ** len(templates), 'seed_sets_per_graph': 8,
        'cases_evaluated': len(cases), 'passed': len(cases) - len(failures),
        'failed': len(failures), 'failure_examples': failures[:20],
        'native_processes': 1,
        'scope': 'SYNTHETIC_FINITE_HORN_GRAPHS_NOT_ARABIC_USAGE_BENCHMARK',
        'all_arabic_complete': False, 'world_truth_established': False,
    }


@unittest.skipUnless(EXE.is_file(), 'requires compiled lexicalGraph; mandatory in graph CI')
class NativeGraphOracleTests(unittest.TestCase):
    def check_complete(self, request):
        row = native_batch([request])[0]
        self.assertEqual(row['status'], 'CHECKED_CLOSURE', row)
        self.assertIs(row['complete'], True)
        self.assertEqual(set(row['known']), finite_model_intersection(request))
        self.assertEqual(set(row['active_rule_ids']), {r['id'] for r in active_rules(request)})
        self.assertIs(row['world_truth_established'], False)
        self.assertIs(row['all_arabic_complete'], False)
        return row

    def test_4096_tiny_graphs_against_closed_subset_intersection(self):
        report = exhaustive_native_oracle_report()
        self.assertEqual(report['cases_evaluated'], 4096)
        self.assertEqual(report['passed'], 4096, report)
        self.assertEqual(report['failed'], 0, report)

    def test_cycle_without_assumption_cannot_certify_its_own_start(self):
        row = self.check_complete(fixture(3, [([0], 1), ([1], 2), ([2], 0)]))
        self.assertEqual(row['known'], [])
        self.assertEqual(row['trace'], [])

    def test_seeded_cycle_terminates_without_deriving_disconnected_node(self):
        row = self.check_complete(fixture(4, [([0], 1), ([1], 2), ([2], 0)], [0]))
        self.assertEqual(set(row['known']), {'n0', 'n1', 'n2'})

    def test_shared_component_text_does_not_collapse_node_identity(self):
        request = fixture(2, seeds=[0])
        request['nodes'][1]['component'] = request['nodes'][0]['component']
        row = self.check_complete(request)
        self.assertEqual(row['known'], ['n0'])

    def test_reachable_scc_is_insufficient_for_an_and_premise(self):
        # A topological SCC/reachability algorithm would wrongly add n1/n2.
        row = self.check_complete(fixture(3, [([0, 2], 1), ([1], 2)], [0]))
        self.assertEqual(row['known'], ['n0'])

    def test_side_cycle_does_not_erase_another_branch(self):
        row = self.check_complete(fixture(5, [([0], 1), ([1], 0), ([0], 2), ([2], 3)], [0]))
        self.assertEqual(set(row['known']), {'n0', 'n1', 'n2', 'n3'})

    def test_long_chain_has_no_arbitrary_depth_five_cutoff(self):
        request = fixture(9, [([i], i + 1) for i in range(8)], [0])
        row = self.check_complete(request)
        self.assertEqual(len(row['known']), 9)

    def test_rule_and_node_order_do_not_change_the_closure(self):
        request = fixture(4, [([2], 3), ([1], 2), ([0], 1), ([3], 0)], [0])
        expected = set(self.check_complete(request)['known'])
        for rules in itertools.permutations(request['rules']):
            variant = {**request, 'nodes': list(reversed(request['nodes'])), 'rules': list(rules)}
            self.assertEqual(set(self.check_complete(variant)['known']), expected)

    def test_guard_failures_do_not_turn_into_inference_edges(self):
        base = fixture(2, [([0], 1)], [0])
        changes = []
        missing_source = deepcopy(base)
        missing_source['active_sources'] = []
        changes.append(missing_source)
        for field in ('scope', 'sense_id'):
            mismatch = deepcopy(base)
            mismatch['nodes'][1][field] = 'another:' + field
            changes.append(mismatch)
        for dimension in ('definition_reference', 'opposition_reference'):
            reference = deepcopy(base)
            reference['rules'][0]['dimension'] = dimension
            changes.append(reference)
        for request in changes:
            with self.subTest(request=request):
                self.assertEqual(self.check_complete(request)['known'], ['n0'])

    def test_budget_exhaustion_preserves_prefix_but_does_not_assert_closure(self):
        request = fixture(3, [([0], 1), ([1], 2)], [0], budget=0)
        row = native_batch([request])[0]
        self.assertEqual(row['status'], 'RESOURCE_EXHAUSTED')
        self.assertIs(row['complete'], False)
        self.assertEqual(row['known'], ['n0'])
        self.assertNotIn('REFUTED', json.dumps(row))

    def test_empty_body_cannot_be_smuggled_in_as_an_unannounced_axiom(self):
        row = native_batch([fixture(1, [([], 0)])])[0]
        self.assertEqual(row['status'], 'INVALID_INPUT')

    def test_noncanonical_identity_and_authority_fields_are_invalid(self):
        original = fixture(2, [([0], 1)], [0])
        invalid = []
        for location, field, value in [('request', 'budget', True), ('request', 'budget', 1.0),
                                       ('request', 'verified', True), ('node', 'id', 1),
                                       ('node', 'scope', ''), ('node', 'component', '\ud800'),
                                       ('rule', 'head', 'absent'), ('rule', 'dimension', 'MUTABAQAH')]:
            changed = deepcopy(original)
            obj = changed if location == 'request' else changed[location + 's'][0]
            obj[field] = value
            invalid.append(changed)
        for location in ('nodes', 'rules', 'seeds', 'active_sources'):
            changed = deepcopy(original)
            changed[location].append(deepcopy(changed[location][0]))
            invalid.append(changed)
        changed = deepcopy(original)
        changed['rules'][0]['body'] *= 2
        invalid.append(changed)
        # ensure_ascii=True is necessary to submit the deliberately invalid surrogate.
        wire = b''.join(json.dumps(r, ensure_ascii=True).encode() + b'\n' for r in invalid)
        run = subprocess.run([str(EXE)], input=wire, capture_output=True, check=True, timeout=20)
        self.assertEqual([json.loads(line)['status'] for line in run.stdout.splitlines()],
                         ['INVALID_INPUT'] * len(invalid))

    def test_invalid_jsonl_does_not_corrupt_the_next_valid_request(self):
        request = fixture(2, [([0], 1)], [0])
        valid = json.dumps(request).encode()
        malformed = valid.replace(b'"budget": 512', b'"budget": -0')
        run = subprocess.run([str(EXE)], input=malformed + b'\n\xff\n' + valid + b'\n',
                             capture_output=True, check=True, timeout=20)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([r['status'] for r in rows], ['INVALID_INPUT', 'INVALID_INPUT', 'CHECKED_CLOSURE'])
        self.assertEqual(set(rows[-1]['known']), {'n0', 'n1'})

    def test_duplicate_field_and_scalar_limit_are_not_lossily_normalized(self):
        valid = json.dumps(fixture(2, [([0], 1)], [0])).encode()
        duplicates = b'{"budget":512,' + valid[1:]
        escaped_duplicate = b'{"bu\\u0064get":512,' + valid[1:]
        nested_duplicate = valid.replace(b'"id": "n0"', b'"id": "n0", "id": "n0"', 1)
        oversize = json.dumps(fixture(2, [([0], 1)], [0], budget=513)).encode()
        run = subprocess.run([str(EXE)], input=b'\n'.join([duplicates, escaped_duplicate, nested_duplicate, oversize]) + b'\n',
                             capture_output=True, check=True, timeout=20)
        self.assertEqual([json.loads(line)['status'] for line in run.stdout.splitlines()],
                         ['INVALID_INPUT', 'INVALID_INPUT', 'INVALID_INPUT', 'RESOURCE_LIMIT'])

    def test_duplicate_looking_strings_are_data_not_object_fields(self):
        request = fixture(2, [([0], 1)], [0])
        request['nodes'][0]['component'] = 'text: "id":0,"id":1, {"budget":0}'
        self.assertEqual(set(self.check_complete(request)['known']), {'n0', 'n1'})

    def test_oversize_jsonl_recovers_before_a_valid_request(self):
        valid = json.dumps(fixture(1, seeds=[0])).encode()
        wire = b' ' * (1024 * 1024 + 1) + b'\n' + valid + b'\n'
        run = subprocess.run([str(EXE)], input=wire, capture_output=True, check=True, timeout=20)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([r['status'] for r in rows], ['RESOURCE_LIMIT', 'CHECKED_CLOSURE'])
        self.assertEqual(rows[-1]['known'], ['n0'])


def public_request(assumptions=(), targets=(), budget=512):
    return {'assumed_senses': list(assumptions), 'targets': list(targets), 'budget': budget}


class PublicGraphBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import lexical_graph
        cls.lg = lexical_graph

    def test_caller_cannot_supply_graph_sources_weights_or_verification(self):
        good = public_request()
        values = [None, {}, {'targets': [], 'budget': 512},
                  {**good, 'assumed_senses': True}, {**good, 'targets': 'sense:x'},
                  public_request([True]), public_request(targets=[1]),
                  public_request(['']), public_request(targets=['\ud800']),
                  public_request(budget=True), public_request(budget=1.0), public_request(budget=-1)]
        for name, value in [('graph', {}), ('active_sources', ['forged']), ('verified', True),
                            ('transmission_type', 'متواتر'), ('vector_score', 1.0),
                            ('world_truth_established', True)]:
            values.append({**good, name: value})
        with patch.object(self.lg, 'GraphEngine') as factory:
            for value in values:
                with self.subTest(value=repr(value)):
                    result = self.lg.assess(value)
                    self.assertEqual(result['status'], 'INVALID_INPUT')
                    self.assertIs(result['native_checked'], False)
            factory.assert_not_called()

    def test_raw_json_preserves_integer_spelling_and_utf8_identity(self):
        valid = b'{"assumed_senses":[],"targets":["sense:-0"],"budget":0}'
        invalid = [valid.replace(b'"budget":0', b'"budget":' + spelling)
                   for spelling in (b'-0', b'0.0', b'0e0')]
        invalid += [valid.decode().encode('utf-16'), valid.decode().encode('utf-16-le'),
                    b'{"budget":0,' + valid[1:], b'{"bu\\u0064get":0,' + valid[1:]]
        with patch.object(self.lg, 'GraphEngine') as factory:
            for wire in invalid:
                with self.subTest(wire=wire), self.assertRaises(ValueError):
                    self.lg.request_json(wire)
            parsed = self.lg.request_json(valid)
            self.assertEqual(parsed, public_request(targets=['sense:-0'], budget=0))
            self.assertIs(type(parsed['budget']), int)
            factory.assert_not_called()

    def test_cyclic_components_match_mutual_reachability_for_all_512_graphs(self):
        nodes = ['a', 'b', 'c']
        possible_edges = list(itertools.product(nodes, repeat=2))
        for enabled in itertools.product((False, True), repeat=len(possible_edges)):
            edges = {edge for edge, flag in zip(possible_edges, enabled) if flag}
            # Independent oracle: enumerate every walk up to length three.
            # Three vertices suffice for every simple path or elementary cycle.
            reachable = set()
            for length in range(1, len(nodes) + 1):
                for walk in itertools.product(nodes, repeat=length + 1):
                    if all(edge in edges for edge in zip(walk, walk[1:])):
                        reachable.add((walk[0], walk[-1]))
            expected = {tuple(sorted(other for other in nodes
                                     if (node, other) in reachable and (other, node) in reachable))
                        for node in nodes if (node, node) in reachable}
            actual = self.lg.strong_components(list(reversed(nodes)), sorted(edges, reverse=True))
            self.assertEqual(actual, [list(group) for group in sorted(expected)], edges)

    def test_reverse_dependencies_include_alternatives_and_all_premises_but_not_references(self):
        graph = fixture(6, [([1, 2], 0), ([3], 0), ([0], 1), ([4], 3)])
        graph['references'] = [{'id': 'reference-only', 'body': ['n5'], 'head': 'n0',
                                'dimension': 'definition_reference'}]
        reports = self.lg.reverse_dependencies(graph, ['n0', 'n2'])
        self.assertEqual(reports, [
            {'target': 'n0', 'node_ids': ['n0', 'n1', 'n2', 'n3', 'n4'],
             'rule_ids': ['r0', 'r1', 'r2', 'r3'],
             'authority': 'PREREQUISITE_INSPECTION_NOT_A_PROOF'},
            {'target': 'n2', 'node_ids': ['n2'], 'rule_ids': [],
             'authority': 'PREREQUISITE_INSPECTION_NOT_A_PROOF'},
        ])


PUBLIC_AVAILABLE = EXE.is_file() and (ROOT / 'formal/.lake/build/bin/lexicalCompletion').is_file() and (
    ROOT / 'artifacts/local/lisan.txt').is_file()


@unittest.skipUnless(PUBLIC_AVAILABLE, 'requires installed sources and both graph/lexical native checkers')
class InstalledLexicalGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import lexical_graph
        cls.lg = lexical_graph
        cls.engine = lexical_graph.GraphEngine()

    def execute(self, value):
        row = self.lg.assess(value, engine=self.engine)
        self.assertIs(row['native_checked'], True, row)
        self.assertIs(row['world_truth_established'], False)
        self.assertIs(row['all_arabic_complete'], False)
        return row

    def test_root_index_keeps_all_five_senses_without_collapsing_them(self):
        inventory = self.engine.inventory()
        eye = inventory['entries']['عين']
        expected = ['lisan:v2:eye-' + suffix for suffix in ('vision', 'spy', 'spring', 'cash', 'letter')]
        self.assertCountEqual(eye, expected)
        nodes = {n['id'] for n in inventory['nodes']}
        self.assertTrue({'sense:' + s for s in expected} <= nodes)
        targets = ['sense:' + s for s in expected]
        result = self.execute(public_request(['lisan:v2:eye-cash'], targets))
        observed = {r['node_id']: r['status'] for r in result['target_results']}
        self.assertEqual(observed['sense:lisan:v2:eye-cash'], 'DERIVED_UNDER_ASSUMPTIONS')
        self.assertTrue(all(observed['sense:' + s] == 'NOT_DERIVED_IN_INSTALLED_GRAPH'
                            for s in expected if s != 'lisan:v2:eye-cash'))

    def test_source_reference_cycle_does_not_produce_semantic_implication(self):
        source, other = 'lisan:v2:exit', 'lisan:v2:entry'
        result = self.execute(public_request([source], ['sense:' + other]))
        self.assertEqual(result['target_results'], [
            {'node_id': 'sense:' + other, 'status': 'NOT_DERIVED_IN_INSTALLED_GRAPH'}])
        self.assertTrue(self.engine.inventory()['references'])
        empty = self.execute(public_request([], ['sense:' + source, 'sense:' + other]))
        self.assertEqual(empty['native_result']['known'], [])
        self.assertTrue(all(r['status'] == 'NOT_DERIVED_IN_INSTALLED_GRAPH' for r in empty['target_results']))

    def test_assumed_meaning_is_recorded_but_never_promoted_to_world_truth(self):
        sense = 'lisan:v2:earth'
        result = self.execute(public_request([sense], ['sense:' + sense, 'component:' + sense + ':0']))
        self.assertTrue(result['assumptions'])
        self.assertTrue(all(t['status'] == 'DERIVED_UNDER_ASSUMPTIONS' for t in result['target_results']))
        self.assertIs(result['world_truth_established'], False)
        self.assertIs(result['all_arabic_complete'], False)

    def test_zero_budget_certifies_seed_only_and_keeps_missing_target_unknown(self):
        sense = 'lisan:v2:earth'
        result = self.execute(public_request([sense], ['sense:' + sense, 'component:' + sense + ':0'], budget=0))
        self.assertEqual(result['status'], 'RESOURCE_EXHAUSTED')
        self.assertIs(result['native_result']['complete'], False)
        self.assertEqual(result['target_results'], [
            {'node_id': 'sense:' + sense, 'status': 'DERIVED_UNDER_ASSUMPTIONS'},
            {'node_id': 'component:' + sense + ':0', 'status': 'UNKNOWN_RESOURCE_EXHAUSTED'}])

    def test_unknown_identity_and_unresolved_definition_are_distinct(self):
        for request in (public_request(['not-installed']), public_request(targets=['sense:not-installed'])):
            self.assertEqual(self.lg.assess(request, engine=self.engine)['status'], 'INVALID_INPUT')
        unresolved = self.lg.assess(public_request(['lisan:v2:sun-deictic']), engine=self.engine)
        self.assertEqual(unresolved['status'], 'UNMEASURED_DEFINITION')
        self.assertIs(unresolved['native_checked'], False)
        self.assertIs(unresolved['world_truth_established'], False)

    def test_modified_source_bytes_cannot_be_certified_by_unchanged_catalogue(self):
        original = Path.read_bytes

        def changed(path):
            raw = original(path)
            return raw + b' ' if path == ROOT / 'artifacts/local/lisan.txt' else raw

        with patch.object(Path, 'read_bytes', changed), patch.object(self.lg, '_native') as native:
            result = self.lg.assess(public_request(['lisan:v2:earth']))
        self.assertEqual(result['status'], 'SOURCE_UNAVAILABLE')
        self.assertIs(result['native_checked'], False)
        native.assert_not_called()

    def test_missing_native_and_timeout_never_become_positive_receipts(self):
        for error, status in [(OSError('missing checker'), 'VERIFICATION_UNAVAILABLE'),
                              (subprocess.TimeoutExpired('lexicalGraph', 20), 'RESOURCE_EXHAUSTED')]:
            with self.subTest(status=status), patch.object(self.lg, '_native', side_effect=error):
                result = self.lg.assess(public_request(['lisan:v2:earth']), engine=self.engine)
            self.assertEqual(result['status'], status)
            self.assertIs(result['native_checked'], False)
            self.assertNotIn('native_result', result)

    def test_forged_native_closure_or_boolean_is_rejected(self):
        real = self.lg._native
        for mutation in ('add_unknown_node', 'drop_seed', 'complete_number'):
            def fake(exe, request=None):
                result = real(exe, request)
                if Path(exe).name == 'lexicalGraph' and request is not None:
                    if mutation == 'add_unknown_node':
                        result['known'].append('sense:forged')
                    elif mutation == 'drop_seed':
                        result['known'] = []
                    else:
                        result['complete'] = 1
                return result
            with self.subTest(mutation=mutation), patch.object(self.lg, '_native', side_effect=fake):
                result = self.lg.assess(public_request(['lisan:v2:earth']), engine=self.engine)
            self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
            self.assertIs(result['native_checked'], False)

    def test_editing_a_returned_receipt_does_not_change_later_provenance(self):
        engine = self.lg.GraphEngine()
        request = public_request(['lisan:v2:earth'])
        receipt = self.lg.assess(request, engine=engine)
        self.assertIs(receipt['native_checked'], True, receipt)
        expected_hashes = deepcopy(receipt['source_sha256'])
        expected_unresolved = deepcopy(receipt['unresolved_senses'])
        inventory = engine.inventory()
        inventory['nodes'].clear()
        receipt['source_sha256'].clear()
        receipt['unresolved_senses'].clear()
        receipt['native_request']['rules'][0]['body'].clear()
        repeated = self.lg.assess(request, engine=engine)
        self.assertIs(repeated['native_checked'], True, repeated)
        self.assertEqual(repeated['source_sha256'], expected_hashes)
        self.assertEqual(repeated['unresolved_senses'], expected_unresolved)
        self.assertTrue(engine.inventory()['nodes'])


if __name__ == '__main__':
    unittest.main()

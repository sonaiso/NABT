"""Measure installed graph controls separately from synthetic closure models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from tools.lexical_graph import GraphEngine, assess
from tools.lexical_completion import sha
from tests.test_lexical_graph import exhaustive_native_oracle_report


def run():
    engine = GraphEngine()
    rows = []
    cases = [
        ('no_self_support', [], ['sense:lisan:v2:exit'], 512,
         ['NOT_DERIVED_IN_INSTALLED_GRAPH']),
        ('reference_is_not_implication', ['lisan:v2:exit'],
         ['component:lisan:v2:exit:0', 'sense:lisan:v2:entry'], 512,
         ['DERIVED_UNDER_ASSUMPTIONS', 'NOT_DERIVED_IN_INSTALLED_GRAPH']),
        ('polysemy_not_collapsed', ['lisan:v2:eye-cash'],
         ['sense:lisan:v2:eye-cash', 'sense:lisan:v2:eye-vision', 'sense:lisan:v2:eye-spring'], 512,
         ['DERIVED_UNDER_ASSUMPTIONS', 'NOT_DERIVED_IN_INSTALLED_GRAPH', 'NOT_DERIVED_IN_INSTALLED_GRAPH']),
        ('mental_not_world', ['lisan:ama'], ['necessity:lisan:ama:1'], 512,
         ['DERIVED_UNDER_ASSUMPTIONS']),
        ('budget_does_not_mean_rejection', ['lisan:v2:exit'],
         ['sense:lisan:v2:exit', 'component:lisan:v2:exit:0'], 0,
         ['DERIVED_UNDER_ASSUMPTIONS', 'UNKNOWN_RESOURCE_EXHAUSTED']),
        ('unresolved_not_empty_axiom', ['lisan:v2:sun-deictic'],
         ['sense:lisan:v2:sun-deictic'], 512, 'UNMEASURED_DEFINITION'),
        ('unknown_not_lexically_invalid', ['not:installed'], [], 512, 'INVALID_INPUT'),
        ('empty_assumptions_are_valid', [], [], 0, []),
    ]
    for label, assumptions, targets, budget, expected in cases:
        request = {'assumed_senses': assumptions, 'targets': targets, 'budget': budget}
        receipt = assess(request, engine=engine)
        actual = ([r['status'] for r in receipt['target_results']]
                  if type(expected) is list else receipt['status'])
        correct = (actual == expected and receipt['world_truth_established'] is False
                   and receipt['all_arabic_complete'] is False)
        rows.append({'id': label, 'request': request, 'expected': expected,
                     'actual': actual, 'passed': correct, 'receipt': receipt})
    oracle = exhaustive_native_oracle_report()
    files = ['formal/Nabt/LexicalGraph.lean', 'formal/LexicalGraphMain.lean',
             'tools/lexical_graph.py', 'tools/build_lexical_graph.py',
             'tools/benchmark_lexical_graph.py', 'tests/test_lexical_graph.py',
             'evidence/lexical_graph_v1/graph.json']
    return {'schema': 'nabt.lexical-graph-benchmark.v1',
            'installed_controls': {'total': len(rows), 'passed': sum(r['passed'] for r in rows),
                                   'failed': sum(not r['passed'] for r in rows), 'cases': rows},
            'independent_oracle': oracle,
            'inventory': {k: engine.inventory()[k] for k in
                          ['nodes_count', 'rule_count', 'reference_count', 'native_license_checks', 'graph_sha256']},
            'inputs_sha256': {p: sha((ROOT / p).read_bytes()) for p in files},
            'natural_arabic_usage_measured_here': False,
            'previous_natural_usage_result_changed': False,
            'compiler_refinement_proved': False, 'all_arabic_complete': False,
            'world_truth_established': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'installed_passed': result['installed_controls']['passed'],
                      'installed_total': result['installed_controls']['total'],
                      'synthetic_passed': result['independent_oracle']['passed'],
                      'synthetic_total': result['independent_oracle']['cases_evaluated']}))
    return int(bool(result['installed_controls']['failed'] or result['independent_oracle']['failed']))


if __name__ == '__main__':
    raise SystemExit(main())

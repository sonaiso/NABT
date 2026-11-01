"""Read-only isolated comparison of the installed JSON owner in routing.

This prototype changes module bindings only in this process. It is not a new
runtime entry point or an independent semantic acceptance oracle.
"""
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]

from nabt.corpus_sources import _same_json
from tools.grammar_catalog import routing
from tools.grammar_catalog.retrieval import SearchIndex

OUTPUT = Path(__file__).with_name('state_equality_observation_v1.json')
if OUTPUT.exists():
    raise SystemExit('Refusing to overwrite a performance observation')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')

def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()

def stamp():
    return datetime.now(timezone.utc).isoformat()

def identities():
    paths = ['tools/grammar_catalog/routing.py', 'tools/grammar_catalog/retrieval.py',
             'tools/grammar_catalog/catalog.py', 'src/nabt/corpus_sources.py',
             'src/nabt/classical_laws.py', '.github/workflows/ci.yml', 'Makefile']
    return {p: sha((ROOT / p).read_bytes()) for p in paths}

started = stamp()
start_head = head()
before = identities()
original = routing._fresh_index
original_canonical = routing.catalog_canonical
original_source = inspect.getsource(original)
needle = '            try:\n                same = catalog_canonical(row) == catalog_canonical(expected_row)'
assert original_source.count(needle) == 1
candidate_source = original_source.replace(needle,
    '            if installed_same_json(row, expected_row):\n'
    '                continue\n' + needle)

counts = {'canonical_calls': 0, 'structural_calls': 0}
def counted_canonical(value):
    counts['canonical_calls'] += 1
    return original_canonical(value)

def installed_same_json(actual, expected):
    counts['structural_calls'] += 1
    return _same_json(actual, expected)

namespace = dict(routing.__dict__)
namespace.update(catalog_canonical=counted_canonical,
                 installed_same_json=installed_same_json)
exec(compile(candidate_source, '<isolated-existing-owner-comparison>', 'exec'), namespace)
candidate = namespace['_fresh_index']

query = 'همزة الأمر'
frames = json.loads((ROOT / 'examples/operator_context_frames.json').read_text())
rounds = []
baseline_report = baseline_verification = None

try:
    routing.catalog_canonical = counted_canonical
    for round_number, order in enumerate((('baseline', 'candidate'),
                                           ('candidate', 'baseline'),
                                           ('baseline', 'candidate')), 1):
        row = {'round': round_number, 'order': list(order)}
        for mode in order:
            routing._fresh_index = original if mode == 'baseline' else candidate
            counts.update(canonical_calls=0, structural_calls=0)
            begin = time.perf_counter()
            index = SearchIndex(root=ROOT)
            setup = time.perf_counter()
            report = routing.build_routing_report(index, query, frames)
            built = time.perf_counter()
            verification = routing.verify_routing_report(report, query=query,
                                                         frames_by_rule=frames, root=ROOT)
            finished = time.perf_counter()
            report_bytes = canonical(report)
            verification_bytes = canonical(verification)
            if baseline_report is None:
                assert mode == 'baseline'
                baseline_report, baseline_verification = report_bytes, verification_bytes
            assert report_bytes == baseline_report
            assert verification_bytes == baseline_verification
            row[mode] = {
                'setup_seconds': setup - begin,
                'build_seconds': built - setup,
                'verify_seconds': finished - built,
                'total_seconds': finished - begin,
                'report_sha256': sha(report_bytes),
                'verification_sha256': sha(verification_bytes),
                **counts,
            }
        rounds.append(row)
finally:
    routing._fresh_index = original
    routing.catalog_canonical = original_canonical

after = identities()
assert before == after
assert head() == start_head
summary = {}
for field in ('setup_seconds', 'build_seconds', 'verify_seconds', 'total_seconds'):
    baseline = statistics.median(row['baseline'][field] for row in rounds)
    improved = statistics.median(row['candidate'][field] for row in rounds)
    summary[field] = {'baseline_median': baseline, 'candidate_median': improved,
                      'reduction_fraction': 1 - improved / baseline}

record = {
    'schema': 'nabt.operator-context.existing-comparator-performance.v1',
    'started_utc': started, 'finished_utc': stamp(), 'head': start_head,
    'python': sys.version, 'platform': platform.platform(),
    'inputs_before': before, 'inputs_after': after, 'inputs_unchanged': before == after,
    'script_sha256': sha(Path(__file__).read_bytes()),
    'original_function_source_sha256': sha(original_source.encode('utf-8')),
    'candidate_function_source': candidate_source,
    'existing_comparator': 'nabt.corpus_sources._same_json',
    'query': query, 'frames': frames, 'budget': None,
    'catalog_sha256': json.loads(baseline_report)['catalog_sha256'],
    'rounds': rounds, 'summary': summary,
    'full_report_bytes_equal': True, 'full_verification_bytes_equal': True,
    'production_bindings_restored': routing._fresh_index is original and
                                    routing.catalog_canonical is original_canonical,
    'limits': [
        'One existing owner comparison candidate, observed before production edit.',
        'Three local alternating pairs; source filesystem caches may be warm and other work may contend.',
        'Only positive repeated owner comparisons use the existing structural comparator.',
        'All mismatches retain the original canonical fallback and exception path.',
        'Fresh SearchIndex, source validation, receipt checks and end-of-operation source rechecks remain present.',
        'Differential performance observation; independent semantic acceptance is separately authored.',
        'No CI deadline guarantee or general Arabic interpretation claim.',
    ],
}
with OUTPUT.open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'output': str(OUTPUT.relative_to(ROOT)), 'summary': summary,
                  'source_unchanged': True, 'full_outputs_equal': True}, ensure_ascii=False, indent=2))

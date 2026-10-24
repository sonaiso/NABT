#!/usr/bin/env python3
"""Compare complete strict observations and explicitly separate measured time."""
from hashlib import sha256
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def differences(left, right, path=''):
    if left == right:
        return []
    if type(left) is not type(right):
        return [{'path': path, 'before': left, 'after': right}]
    if isinstance(left, dict):
        require(left.keys() == right.keys(), 'Observation keys changed: ' + path)
        return [d for key in left for d in differences(left[key], right[key], path + '/' + str(key))]
    if isinstance(left, list):
        require(len(left) == len(right), 'Observation list inventory changed: ' + path)
        return [d for i, (a, b) in enumerate(zip(left, right))
                for d in differences(a, b, path + '/' + str(i))]
    return [{'path': path, 'before': left, 'after': right}]


def main():
    report = {'schema': 'nabt.guard-only-runtime.observation-continuation.v1',
        'old_runtime_sha256': 'eeb9864b08e8ae25e841b18b0d25858d95268fce2435d51c340d69a41782f089',
        'new_runtime_sha256': '045d6b3d6d3c2f6744b3157a2bd3cbf025b401e2efd215d8a4200182685978dd',
        'suites': {}, 'all_arabic_completeness': 'NOT_ESTABLISHED'}
    for suite in ('construction', 'discourse'):
        paths = [PHASE / name / (suite + '.raw.jsonl.gz')
                 for name in ('strict_review_v2', 'strict_review_v3')]
        streams = []
        for path in paths:
            with gzip.open(path, 'rt', encoding='utf-8') as handle:
                streams.append([json.loads(line) for line in handle])
        delta = differences(*streams)
        allowed_times = {'/' + str(i) + '/score/seconds' for i, row in enumerate(streams[0])
                         if 'score' in row and 'seconds' in row['score']}
        require(all(suite == 'construction' and item['path'] in allowed_times
                    and type(item['before']) in (int, float) and type(item['after']) in (int, float)
                    and item['before'] >= 0 and item['after'] >= 0 for item in delta),
                'Public payload or a substantive scoring field changed')
        report['suites'][suite] = {
            'entire_raw_json_equal': not delta, 'raw_json_row_count': len(streams[0]),
            'public_payloads_and_substantive_score_fields_exact': True,
            'complete_differences': delta,
            'comparison': 'Every JSON field and list order compared. Only recorded per-case evaluator elapsed seconds may differ, and every such difference is listed; no public report, question, answer or verification field is normalized.',
            'source_receipts': [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                                 'sha256': sha256(path.read_bytes()).hexdigest()} for path in paths],
        }
    output = PHASE / 'strict_review_v3/raw_continuation.json'
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'receipt_sha256': sha256(output.read_bytes()).hexdigest(),
        'differences': {name: len(row['complete_differences']) for name, row in report['suites'].items()},
        'public_payloads_exact': True}))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Independently replay every archived prediction's exact source binding."""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.qatr_training.data import export_teacher, prepare, index_teacher


def check_bindings(examples, records, teacher):
    words=[w for e in examples if e['split']=='test' for w in e['words'] if w['qatr'] is not None]
    if len(records)!=len(words):raise ValueError('source denominator changed')
    lookup=index_teacher(teacher)
    fields={'address','csv_rows','text_sha256','gold_reading','gold_case','reading','case_ranking','authority'}
    for word,record in zip(words,records,strict=True):
        if set(record)!=fields:raise ValueError('prediction schema changed')
        binding=dict(address=word['address'],csv_rows=word['csv_rows'],text_sha256=word['text_sha256'],
                     gold_reading=word['qatr'],gold_case=word['case'],authority='NONE')
        if any(record[k]!=v or type(record[k]) is not type(v) for k,v in binding.items()):
            raise ValueError('source binding changed')
        if any(type(x) is not int for x in record['address']+record['csv_rows']):
            raise ValueError('source identity must use integer fields')
        if record['reading'] not in lookup or not lookup[record['reading']]['rows']:
            raise ValueError('unknown reading set')
        if record['case_ranking'] not in {'raf','nasb','jarr','jazm'}:
            raise ValueError('unknown case ranking')
    return len(words)


# One installed compatibility review; no arbitrary historical hash override.
REVIEW = Path('evidence/qatr_lean_training/replay_compatibility_v1/review.json')
REVIEW_SHA256 = '3721424476a13318c34cc79ed687ccd0a9892a2e4f2497bf3ecf2cc7430bb505'
HISTORICAL_RUN = Path('evidence/qatr_lean_training/run_01')


def _digest(raw):
    return sha256(raw).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate replay manifest key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _current_training_paths(root):
    paths = [*root.glob('tools/qatr_training/*.py'), root/'tools/train_qatr_readings.py',
             root/'tools/arabic_training/data.py', root/'tools/arabic_training/model.py',
             root/'tools/arabic_training/experiment.py', root/'formal/Nabt/QatrReading.lean',
             root/'formal/QatrReadingMain.lean', root/'formal/Nabt/Words.lean',
             root/'formal/Nabt/InflectionEvidence.lean', root/'formal/Nabt/QatrRules.lean',
             root/'formal/ProbeJson.lean', root/'evidence/qatr_lean_training/book_probe.json',
             root/'evidence/qatr_lean_training/source_coverage.json']
    return {str(path.relative_to(root)) for path in paths}


def _verify_implementation(root, model_dir):
    """Validate the implementation only; this does not grant replay success."""
    root, model_dir = Path(root).resolve(), Path(model_dir).resolve()
    raw_manifest = (model_dir/'code_manifest.json').read_bytes()
    manifest = _json(raw_manifest)
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError('empty or invalid experiment implementation manifest')
    changed = {}
    for name, expected in manifest.items():
        path = PurePosixPath(name)
        if (path.is_absolute() or '..' in path.parts or str(path) != name
                or not isinstance(expected, str) or len(expected) != 64
                or any(c not in '0123456789abcdef' for c in expected)):
            raise ValueError('invalid experiment implementation manifest entry')
        if _digest((model_dir/'code_snapshot'/name).read_bytes()) != expected:
            raise ValueError('historical experiment snapshot changed: ' + name)
        actual = _digest((root/name).read_bytes())
        if actual != expected:
            changed[name] = {'before_sha256': expected, 'after_sha256': actual}
    # The installed historical run cannot rebase its manifest and snapshots to
    # current bytes and escape its immutable artifact/review checks. Exact mode
    # is available only to other runs; all historical admission passes below.
    if model_dir != (root/HISTORICAL_RUN).resolve():
        if changed:
            raise ValueError('unreviewed experiment implementation change')
        if set(manifest) != _current_training_paths(root):
            raise ValueError('experiment implementation inventory changed')
        return {'status': 'EXACT_TRAINING_IMPLEMENTATION', 'changed_files': [],
                'model_replay_required': True}
    # A caller's path/manifest cannot select or broaden the one installed review.
    raw_review = (root/REVIEW).read_bytes()
    if _digest(raw_review) != REVIEW_SHA256:
        raise ValueError('Qatr replay compatibility review changed')
    review = _json(raw_review)
    if (_digest(raw_manifest) != review['historical_manifest_sha256']
            or changed != review['changes']):
        raise ValueError('unreviewed experiment implementation change')
    additions = review['existing_nontraining_modules']
    if set(_current_training_paths(root)) != set(manifest) | set(additions):
        raise ValueError('unreviewed experiment implementation inventory change')
    for name, expected in additions.items():
        if _digest((root/name).read_bytes()) != expected:
            raise ValueError('unreviewed nontraining module change: ' + name)
    for name, expected in review['preserved_artifacts'].items():
        if _digest((model_dir/name).read_bytes()) != expected:
            raise ValueError('historical Qatr artifact changed: ' + name)
    patch = root/REVIEW.parent/review['patch_filename']
    if _digest(patch.read_bytes()) != review['patch_sha256']:
        raise ValueError('Qatr replay compatibility patch changed')
    return {'status': 'REVIEWED_IMPLEMENTATION_MIGRATION',
            'review': str(REVIEW), 'review_sha256': REVIEW_SHA256,
            'historical_manifest_sha256': review['historical_manifest_sha256'],
            'changed_files': sorted(changed), 'model_replay_required': True,
            'scope': 'Exact historical run only; unchanged teacher, source intake, vocabulary, predictions, metrics, baselines and native results must be independently replayed.'}



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--lean',type=Path,required=True)
    p.add_argument('--model-dir',type=Path,required=True);a=p.parse_args()
    teacher=export_teacher(a.lean);examples,_=prepare(a.source,teacher)
    records=[json.loads(s) for s in (a.model_dir/'test_predictions.jsonl').read_text().splitlines()]
    print(json.dumps(dict(ok=True,source_bound_predictions=check_bindings(examples,records,teacher))))

if __name__=='__main__':main()

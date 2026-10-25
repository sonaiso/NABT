"""Independent adversarial probes; no benchmark gold or upstream code imported.

Run from any directory. Reports exact checked file hashes and small outcome
summaries; mutates only disposable copies of the installed source review.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.linguistic_truth import runtime
from tools.linguistic_truth import links, pipeline, retrieval
from tools.linguistic_truth.sources import build_inventory, INVENTORY_PATH, SourceInventoryError


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(result):
    return {
        'status': result['status'],
        'native_checked': result['native_checked'],
        'intended_sense_acquired': result['intended_sense_acquired'],
        'world_truth_established': result['world_truth_established'],
        'certified_sense_ids': [o['certified_sense_ids'] for o in result['occurrences']],
        'candidate_counts': [len(o['candidates']) for o in result['occurrences']],
    }


def run(output=None):
    checks = []

    def record(name, actual, passed):
        checks.append({'probe': name, 'passed': bool(passed), 'actual': actual})

    def raw_case(name, text, expected_status, *, acquired=None, supported=None, **kwargs):
        result = runtime.acquire(text, **kwargs)
        okay = result['status'] == expected_status and not result['world_truth_established']
        if acquired is not None:
            okay &= result['intended_sense_acquired'] is acquired
        if supported is not None:
            okay &= any(o['certified_sense_ids'] for o in result['occurrences']) is supported
        record(name, compact(result), okay)
        return result

    inventory = build_inventory()
    for kind in ('deleted_source', 'one_byte_change', 'source_and_manifest_rehash',
                 'designation_identity_rewrite', 'manifest_path_escape', 'source_symlink_escape'):
        with tempfile.TemporaryDirectory(prefix='nabt-independent-review-') as temporary:
            outside = Path(temporary)
            root = outside / 'root'
            metadata = root / INVENTORY_PATH
            metadata.parent.mkdir(parents=True)
            metadata.write_bytes((ROOT / INVENTORY_PATH).read_bytes())
            for source in inventory['sources']:
                target = root / source['local_path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / source['local_path']).read_bytes())
            manifest = json.loads(metadata.read_text())
            source = manifest['sources'][0]
            target = root / source['local_path']
            if kind == 'deleted_source':
                target.unlink()
            elif kind in ('one_byte_change', 'source_and_manifest_rehash'):
                target.write_bytes(target.read_bytes() + b'\n')
                if kind == 'source_and_manifest_rehash':
                    source['sha256'] = sha(target)
                    source['bytes'] += 1
                    metadata.write_text(json.dumps(manifest, ensure_ascii=False))
            elif kind == 'designation_identity_rewrite':
                manifest['designations'][0]['sense_id'] = 'forged'
                metadata.write_text(json.dumps(manifest, ensure_ascii=False))
            elif kind == 'manifest_path_escape':
                source['local_path'] = str(outside / 'outside.txt')
                metadata.write_text(json.dumps(manifest, ensure_ascii=False))
            elif kind == 'source_symlink_escape':
                external = outside / 'outside.txt'
                external.write_bytes(target.read_bytes())
                target.unlink()
                target.symlink_to(external)
            try:
                build_inventory(root)
                record(kind, 'ACCEPTED', False)
            except SourceInventoryError as error:
                record(kind, str(error), True)

    literal = 'أعني بالأسد الحيوان المفترس'
    baseline = raw_case('literal_actual_source_and_native', literal, 'COMPLETE',
                        acquired=True, supported=True, profile_id='linguistic')
    raw_case('figurative_needs_literal_exclusion', 'أعني بالأسد الرجل الشجاع', 'COMPLETE',
             acquired=True, supported=False, profile_id='linguistic')
    raw_case('figurative_with_explicit_exclusion', 'أعني بالأسد الرجل الشجاع لا الحيوان المفترس',
             'COMPLETE', acquired=True, supported=True, profile_id='linguistic')
    raw_case('homonym_joint_selection', 'أعني بالقرء الطهر والحيض', 'COMPLETE',
             acquired=True, supported=True, profile_id='linguistic')
    raw_case('same_occurrence_signed_conflict', literal + ' لا الحيوان المفترس', 'CONFLICT',
             acquired=True, supported=False, profile_id='linguistic')
    raw_case('unknown_suffix_not_erased', literal + ' ربما', 'UNKNOWN',
             acquired=False, supported=False, profile_id='linguistic')
    raw_case('plain_sentence_does_not_assign_intention', 'رأيت الأسد', 'UNKNOWN',
             acquired=False, supported=False, profile_id='linguistic')
    for opening, closing in (('«', '»'), ('"', '"'), ("'", "'"), ('‘', '’'),
                             ('```', '```'), ('`', '`'), ('{', '}'), ('(', ')')):
        raw_case('multiline_quotation_' + repr(opening), opening + '\n' + literal + '\n' + closing,
                 'UNKNOWN', acquired=False, supported=False, profile_id='linguistic')
    raw_case('long_chain_is_exhaustion_not_recursion_crash', literal + ' والحيوان المفترس' * 1200,
             'RESOURCE_EXHAUSTED', acquired=False, supported=False, profile_id='linguistic')
    raw_case('native_transport_limit_is_exhaustion', literal + '.' + 'x' * 18000,
             'RESOURCE_EXHAUSTED', supported=False, profile_id='linguistic')
    raw_case('no_default_convention_promotion', 'أعني بالدابة ذوات الأربع', 'UNKNOWN',
             acquired=True, supported=False)
    raw_case('wrong_convention_does_not_license_selected_sense', 'أعني بالدابة ذوات الأربع',
             'COMPLETE', acquired=True, supported=False, profile_id='linguistic')
    raw_case('explicit_customary_convention_is_conditional', 'أعني بالدابة ذوات الأربع',
             'COMPLETE', acquired=True, supported=True, profile_id='customary')
    result = raw_case('two_occurrence_scopes', literal + '. أعني بالأسد الرجل الشجاع لا الحيوان المفترس',
                     'COMPLETE', acquired=True, supported=True, profile_id='linguistic')
    record('two_occurrence_different_intended_senses',
           [o['certified_sense_ids'] for o in result['occurrences']],
           len(result['occurrences']) == 2 and
           result['occurrences'][0]['certified_sense_ids'] != result['occurrences'][1]['certified_sense_ids'])
    for budget in ({'max_native_scan': 4097}, {'max_readings': True}):
        try:
            runtime.AcquisitionBudget(**budget)
            record('invalid_budget_' + str(budget), 'ACCEPTED', False)
        except ValueError as error:
            record('invalid_budget_' + str(budget), str(error), True)

    genuine = baseline['occurrences'][0]['native_result']
    for kind in ('invalid_status', 'wrong_law', 'wrong_authority', 'changed_second_row',
                 'complete_bool_alias', 'world_truth_claim', 'unknown_verdict', 'integer_float_alias'):
        forged = deepcopy(genuine)
        if kind == 'invalid_status':
            forged = {'status': 'INVALID_INPUT', 'message': 'review probe'}
        elif kind == 'wrong_law':
            forged['law_id'] = 'forged-law'
        elif kind == 'wrong_authority':
            forged['authority'] = 'CALLER_TRUSTED'
        elif kind == 'changed_second_row':
            forged['rows'][1]['candidate']['intended_sense'] = 'forged'
        elif kind == 'complete_bool_alias':
            forged['complete_proposal'] = 1
        elif kind == 'world_truth_claim':
            forged['world_truth_asserted'] = True
        elif kind == 'unknown_verdict':
            forged['rows'][0]['verdict'] = 'TRUE_IN_REALITY'
        elif kind == 'integer_float_alias':
            for row in forged['rows']:
                citation = row['candidate']['designation']['citation']
                citation['start_byte'] = float(citation['start_byte'])
                relation = row['candidate']['relation']
                if relation is not None:
                    citation = relation['designation']['citation']
                    citation['start_byte'] = float(citation['start_byte'])
        with patch('tools.linguistic_truth.runtime._verify_native', return_value=forged):
            raw_case('native_response_' + kind, literal, 'VERIFICATION_UNAVAILABLE',
                     acquired=True, supported=False, profile_id='linguistic')

    for call_to_fail in (2, 3):
        count = 0

        def replay_or_fail(root=ROOT):
            nonlocal count
            count += 1
            if count == call_to_fail:
                raise SourceInventoryError('independent replay-race probe')
            return build_inventory(root)

        with patch('tools.linguistic_truth.inventory.build_inventory', side_effect=replay_or_fail):
            raw_case('source_replay_failure_call_' + str(call_to_fail), literal, 'SOURCE_UNAVAILABLE',
                     supported=False)

    # A valid vocabulary label can still lie about the signed obligations.
    # This mutation used to pass shape-only native validation; the full finite
    # postcondition must reject it without relying on an unknown enum value.
    no_exclusion = runtime.acquire('أعني بالأسد الرجل الشجاع', profile_id='linguistic')
    forged = deepcopy(no_exclusion['occurrences'][0]['native_result'])
    for row in forged['rows']:
        if row['kind'] == 'figurative':
            row['verdict'] = 'SUPPORTED_PREMISES'
    with patch('tools.linguistic_truth.runtime._verify_native', return_value=forged):
        raw_case('native_valid_but_false_support_verdict', 'أعني بالأسد الرجل الشجاع',
                 'VERIFICATION_UNAVAILABLE', acquired=True, supported=False, profile_id='linguistic')

    index = retrieval.LinguisticTruthSearchIndex()
    vector = {'schema': 'nabt.retrieval-vectors.v1', 'catalog_sha256': index.catalog_sha256,
              'model_id': 'independent-adversarial-ranking', 'revision': '1' * 40,
              'dimensions': 3, 'input_recipe': retrieval.INPUT_RECIPE,
              'scores': [{'kind': 'item', 'id': 'relation:asad_animal_to_brave',
                          'cosine_similarity': 1.0}]}
    unranked = pipeline.run('رأيت الأسد', profile_id='linguistic', display_limit=10)
    reranked = pipeline.run('رأيت الأسد', profile_id='linguistic', display_limit=1,
                            reverse_candidates=True, vector_scores=vector)
    record('real_pipeline_rank_display_invariance',
           {'unranked': compact(unranked['acquisition']),
            'reranked': compact(reranked['acquisition']),
            'display_counts': [len(unranked['retrieval']['candidates']),
                               len(reranked['retrieval']['candidates'])]},
           unranked['acquisition'] == reranked['acquisition'] and
           not reranked['acquisition']['intended_sense_acquired'] and
           not reranked['world_truth_established'])
    proposal = {'schema': 'nabt.linguistic-truth-database-proposals.v1',
                'inventory_sha': index.catalog_sha256,
                'candidates': [{'kind': 'item', 'id': 'designation:asad_animal',
                                'gloss': 'forged', 'world_truth_established': True,
                                'native_result': forged}]}
    restored = index.rehydrate_database(proposal)
    restored['candidates'][0]['record']['gloss'] = 'caller-mutation'
    restored['candidates'][0]['record']['evidence'][0]['quote'] = 'caller-mutation'
    again = index.rehydrate_database(proposal)
    actual = again['candidates'][0]['record']
    record('retrieval_returned_record_isolation',
           {'gloss': actual['gloss'], 'authority': again['authority'],
            'world_truth_established': again['world_truth_established']},
           actual['gloss'] == 'الحيوان المفترس' and
           actual['evidence'][0]['quote'] != 'caller-mutation' and
           'native_result' not in actual and not again['world_truth_established'])
    boolean_score = deepcopy(vector)
    boolean_score['scores'][0]['cosine_similarity'] = True
    try:
        index.search('الأسد', vector_scores=boolean_score)
        record('vector_boolean_score_rejected', 'ACCEPTED', False)
    except retrieval.RetrievalError as error:
        record('vector_boolean_score_rejected', str(error), True)

    # compose is a pure link formatter; the public builder obtains compilation
    # itself. These edge probes use the retained compiled catalogue, do not
    # claim to recompile it, and assert rejection of broken local references.
    compiled = json.loads((ROOT / 'evidence/linguistic_truth_v1/proof_catalog.json').read_text())
    for mutation in ('missing_source_edge', 'compiled_source_binding_mismatch'):
        changed_inventory, changed_compiled = deepcopy(inventory), deepcopy(compiled)
        if mutation == 'missing_source_edge':
            absent = links.SOURCE_CONTRACTS['used_sense_required'][0]
            changed_inventory['passages'] = [p for p in changed_inventory['passages']
                                              if p['passage_id'] != absent]
        else:
            declaration = next(r for r in changed_compiled['theorems']
                               if r['name'] == 'Nabt.LinguisticTruth.used_sense_required')
            declaration['source_sha256'] = '0' * 64
        try:
            links.compose(changed_inventory, changed_compiled)
            record('proof_links_' + mutation, 'ACCEPTED', False)
        except ValueError as error:
            record('proof_links_' + mutation, str(error), True)

    inspected = ['tools/linguistic_truth/runtime.py', 'tools/linguistic_truth/sources.py',
                 'tools/linguistic_truth/inventory.py', 'formal/LinguisticTruthMain.lean',
                 'tools/mantuq_sources.py', 'formal/ProbeJson.lean',
                 'tools/linguistic_truth/calculus.py', 'tools/mantuq_inference/evaluator.py',
                 'tools/linguistic_truth/retrieval.py', 'tools/linguistic_truth/pipeline.py',
                 'tools/linguistic_truth/links.py', 'tools/grammar_catalog/retrieval.py',
                 'tools/mantuq_inference/retrieval.py', 'tools/proof_catalog.py',
                 'evidence/linguistic_truth_v1/proof_catalog.json',
                 'formal/Nabt/LinguisticTruth.lean', str(INVENTORY_PATH),
                 str(Path(__file__).relative_to(ROOT)),
                 'formal/.lake/build/bin/linguisticTruth']
    report = {
        'schema': 'nabt.linguistic-truth.independent-security-review.v1',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer_role': 'independent repository-survey agent; did not author production runtime or source inventory',
        'benchmark_gold_read': False,
        'python_version': platform.python_version(),
        'files_sha256': {path: sha(ROOT / path) for path in inspected},
        'source_replay': inventory['replay'],
        'probe_count': len(checks),
        'passed': sum(c['passed'] for c in checks),
        'failed': sum(not c['passed'] for c in checks),
        'probes': checks,
        'scope': 'Adversarial selected input, retained-source and native-response boundary probes; not unrestricted Arabic completeness or original-book authentication.',
    }
    target = Path(output).resolve() if output is not None else Path(__file__).with_name('results.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    try:
        display_path = str(target.relative_to(ROOT))
    except ValueError:
        display_path = str(target)
    print(json.dumps({'report': display_path, 'probes': len(checks),
                      'passed': report['passed'], 'failed': report['failed']}, ensure_ascii=False))
    return 1 if report['failed'] else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        help='Write the receipt here; default is results.json beside this script.')
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output))

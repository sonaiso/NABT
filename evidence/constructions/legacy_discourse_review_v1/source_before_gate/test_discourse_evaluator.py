"""Independent scorer obligations; these do not run the held-out predictions."""
from copy import deepcopy
from hashlib import sha256
import gzip
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'tools/discourse_evaluation.py'
spec = importlib.util.spec_from_file_location('discourse_review_evaluator', PATH)
evaluation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = evaluation
spec.loader.exec_module(evaluation)


def example():
    text = 'حازم حكيم'
    source_id = 'test_source'
    inputs = {'text': text, 'source_id': source_id, 'scope': 'test',
              'context': {'entities': [{'id': 'h', 'name': 'حازم'}], 'closed_reference_scope': True}}
    checksum = sha256(text.encode()).hexdigest()
    def span(a, b):
        return {'source_id': source_id, 'source_sha256': checksum, 'start': a, 'end': b}
    first, gap, second, whole = span(0, 8), span(8, 9), span(9, 17), span(0, 17)
    context = {'entities': [{'id': 'h', 'name': 'حازم', 'gender': 'unknown', 'number': 'unknown', 'kind': 'unknown'}],
               'deixis': [], 'closed_reference_scope': True}
    context_sha = evaluation.digest(context)
    reference = {'origin': 'named', 'surface': 'حازم', 'span': first, 'scope': 'test',
                 'context_sha256': context_sha, 'candidate_entity_ids': ['h'], 'bound_entity_id': 'h'}
    reference['reference_id'] = evaluation.digest(reference)
    rows = []
    for rid, surface, location, pos in [('subject', 'حازم', first, 'PN'), ('predicate', 'حكيم', second, 'N')]:
        rows.append({'reading_id': rid, 'kind': 'noun', 'construction': None, 'class_candidates': [],
                     'stem_span': location, 'stem_surface': surface, 'nun_readings': [],
                     'lexical_features': {'lemma': surface, 'pos': pos},
                     'segmentation': {'parts': [{'span': location, 'surface': surface}]}})
    assignments = []
    for rid, surface, location, role, head in [('subject', 'حازم', first, 'nominal_subject', None),
                                              ('predicate', 'حكيم', second, 'nominal_predicate', first)]:
        assignments.append({'reading_id': rid, 'span': location, 'surface': surface, 'role': role,
            'required_case': 'raf', 'head_span': head, 'activated': True, 'actual_role': role,
            'inflected_case': None, 'local_case': None, 'case_domain': None, 'sign_candidates': []})
    claim = {'predicate': 'حكيم', 'predicate_kind': 'property', 'voice': None, 'args': ['h'],
             'positive': True, 'tense': 'unspecified', 'time': [], 'place': [], 'restriction': []}
    analysis = {'span': whole, 'reading_ids': ['subject', 'predicate'], 'references': [reference],
                'assignments': assignments, 'force': 'ASSERT', 'licensed_syntax': True,
                'references_complete': True, 'rejected_candidate': False, 'assertion_allowed': True,
                'claims': [deepcopy(claim)]}
    analysis['analysis_id'] = evaluation.digest(analysis)
    clause = {'span': whole, 'status': 'LICENSED', 'force': 'ASSERT', 'analyses': [analysis]}
    clause['clause_id'] = evaluation.digest(clause)
    claim['claim_id'] = 'claim'
    claim['proofs'] = [{'analysis_id': analysis['analysis_id'], 'clause_id': clause['clause_id'], 'span': whole}]
    report = {'source_text': text, 'source_id': source_id, 'scope': 'test', 'source_sha256': checksum,
              'world_truth': 'NOT_ESTABLISHED', 'context': {'value': context, 'sha256': context_sha},
              'partition': [{'kind': 'written_run', 'surface': 'حازم', 'span': first},
                            {'kind': 'spacing', 'surface': ' ', 'span': gap},
                            {'kind': 'written_run', 'surface': 'حكيم', 'span': second}],
              'occurrences': [{'surface': row['stem_surface'], 'span': row['stem_span'], 'readings': [row]} for row in rows],
              'derived_readings': [], 'clauses': [clause], 'claims': [claim], 'status': 'LICENSED_DISCOURSE'}
    report['report_id'] = evaluation.digest(report)
    return inputs, report


def rehash(report):
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            analysis['analysis_id'] = evaluation.digest({k: v for k, v in analysis.items() if k != 'analysis_id'})
        clause['clause_id'] = evaluation.digest({k: v for k, v in clause.items() if k != 'clause_id'})
    for claim in report['claims']:
        for proof in claim['proofs']:
            proof['analysis_id'] = report['clauses'][0]['analyses'][0]['analysis_id']
            proof['clause_id'] = report['clauses'][0]['clause_id']
    report['report_id'] = evaluation.digest({k: v for k, v in report.items() if k != 'report_id'})


def update_context(inputs, report):
    value = {'entities': [{'gender': 'unknown', 'number': 'unknown', 'kind': 'unknown', **e}
                          for e in inputs['context']['entities']],
             'deixis': inputs['context'].get('deixis', []),
             'closed_reference_scope': inputs['context'].get('closed_reference_scope', False)}
    for name in ('speaker', 'addressee'):
        if name in inputs['context']:
            value[name] = inputs['context'][name]
    report['context'] = {'value': value, 'sha256': evaluation.digest(value)}
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            for reference in analysis['references']:
                reference['context_sha256'] = report['context']['sha256']
                reference['reference_id'] = evaluation.digest({k: v for k, v in reference.items() if k != 'reference_id'})
    rehash(report)


def answer_example(variable=False):
    inputs, document = example()
    inputs['context']['entities'][0]['kind'] = 'person'
    update_context(inputs, document)
    inquiry = deepcopy(document)
    inquiry['claims'] = []
    analysis = inquiry['clauses'][0]['analyses'][0]
    analysis['force'], analysis['assertion_allowed'] = 'QUESTION', False
    analysis['question_kind'] = 'person' if variable else 'polar'
    inquiry['clauses'][0]['force'] = 'QUESTION'
    if variable:
        analysis['claims'][0]['args'] = ['?person']
    rehash(inquiry)
    bindings = {'?person': 'h'} if variable else {}
    proof = {'claim_id': document['claims'][0]['claim_id'], 'document_report_id': document['report_id'],
             'question_report_id': inquiry['report_id'], 'bindings': bindings,
             'source_proofs': deepcopy(document['claims'][0]['proofs'])}
    answer = {'source_text': inputs['text'], 'question_text': inputs['text'], 'scope': inputs['scope'],
              'source_id': inputs['source_id'], 'source_sha256': document['source_sha256'],
              'question_sha256': inquiry['source_sha256'], 'document_report_id': document['report_id'],
              'question_report_id': inquiry['report_id'], 'context_sha256': document['context']['sha256'],
              'world_truth': 'NOT_ESTABLISHED', 'kind': 'person' if variable else 'polar', 'status': 'SUPPORTED',
              'query': deepcopy(analysis['claims'][0]), 'proofs': [proof], 'counterproofs': [],
              'bindings': [{'values': bindings, 'status': 'SUPPORTED', 'proofs': [deepcopy(proof)],
                            'counterproofs': []}] if variable else []}
    answer['answer_id'] = evaluation.digest(answer)
    return inputs, document, inquiry, answer


def relational_time_example(*, resolved=True):
    """Authored API fixture, not a held-out runtime prediction."""
    inputs, report = example()
    text = inputs['text'] + ' حين الموعد'
    checksum = sha256(text.encode()).hexdigest()
    inputs['text'] = report['source_text'] = text
    report['source_sha256'] = checksum
    def rebind(value):
        if type(value) is dict:
            if 'source_sha256' in value:
                value['source_sha256'] = checksum
            for item in value.values():
                rebind(item)
        elif type(value) is list:
            for item in value:
                rebind(item)
    rebind(report)
    def span(a, b):
        return {'source_id': inputs['source_id'], 'source_sha256': checksum, 'start': a, 'end': b}
    whole, adverb, complement = span(0, len(text.encode())), span(18, 24), span(25, 37)
    report['partition'].extend([
        {'kind': 'spacing', 'surface': ' ', 'span': span(17, 18)},
        {'kind': 'written_run', 'surface': 'حين', 'span': adverb},
        {'kind': 'spacing', 'surface': ' ', 'span': span(24, 25)},
        {'kind': 'written_run', 'surface': 'الموعد', 'span': complement}])
    analysis = report['clauses'][0]['analyses'][0]
    for rid, surface, location, pos in [('time', 'حين', adverb, 'T'), ('date', 'الموعد', complement, 'N')]:
        reading = {'reading_id': rid, 'kind': 'noun', 'construction': None, 'class_candidates': [],
                   'stem_span': location, 'stem_surface': surface, 'nun_readings': [],
                   'lexical_features': {'lemma': surface, 'pos': pos},
                   'segmentation': {'parts': [{'span': location, 'surface': surface}]}}
        report['occurrences'].append({'surface': surface, 'span': location, 'readings': [reading]})
        analysis['reading_ids'].append(rid)
    predicate = analysis['assignments'][1]['span']
    for rid, surface, location, role, case, head in [
        ('time', 'حين', adverb, 'time_adverb', 'nasb', predicate),
        ('date', 'الموعد', complement, 'idafa_complement', 'jarr', adverb)]:
        analysis['assignments'].append({'reading_id': rid, 'span': location, 'surface': surface,
            'role': role, 'required_case': case, 'head_span': head, 'activated': True, 'actual_role': role,
            'inflected_case': None, 'local_case': None, 'case_domain': None, 'sign_candidates': []})
    reference = {'origin': 'named', 'surface': 'الموعد', 'span': complement, 'scope': inputs['scope'],
                 'candidate_entity_ids': ['date'] if resolved else [],
                 'bound_entity_id': 'date' if resolved else None}
    analysis['references'].append(reference)
    if resolved:
        inputs['context']['entities'].append({'id': 'date', 'name': 'الموعد'})
    qualification = {'kind': 'temporal_relation', 'relation': 'حين', 'object': reference['bound_entity_id']}
    analysis['claims'][0]['time'] = [deepcopy(qualification)]
    report['claims'][0]['time'] = [deepcopy(qualification)]
    analysis['relations'] = [
        {'kind': 'time_adverb', 'head_span': predicate, 'dependent_span': adverb,
         'complement_span': complement, 'relation_lemma': 'حين', 'dependent_reading_id': 'time',
         'ownership_asserted': False},
        {'kind': 'idafa', 'head_span': adverb, 'dependent_span': complement,
         'complement_span': complement, 'ownership_asserted': False}]
    analysis['span'] = report['clauses'][0]['span'] = whole
    report['claims'][0]['proofs'][0]['span'] = whole
    if not resolved:
        analysis['references_complete'] = analysis['assertion_allowed'] = False
        report['claims'] = []
        report['status'] = report['clauses'][0]['status'] = 'DEFER'
    update_context(inputs, report)
    return inputs, report


def journal_example():
    score = {'id': 'authored', 'passed': True, 'checks': []}
    values = [{'model_profile': 'authored_source', 'summary': {}},
              {'id': 'authored', 'variant': 'mask', 'report': {}},
              {'id': 'authored', 'report': {}, 'questions': [{}], 'score': score}]
    lines = [evaluation.wire(value) + b'\n' for value in values]
    payload = b''.join(lines)
    captured = {'records': [{'identity': evaluation.raw_record_identity(value),
                            'bytes': len(line), 'sha256': sha256(line).hexdigest()}
                           for value, line in zip(values, lines)],
                'sha256': sha256(payload).hexdigest(), 'bytes': len(payload)}
    inventory = {'case_ids': ['authored'], 'variants': [['authored', 'mask']],
                 'profiles': ['authored_source'], 'question_counts': {'authored': 1}}
    return payload, captured, inventory, [{**score, 'seconds': 0.25}]


class DiscourseReviewTests(unittest.TestCase):
    def test_frozen_material_inventory_and_all_predicates_implemented(self):
        freeze, material, inventory = evaluation.load_material()
        self.assertEqual(len(material['cases']), 86)
        self.assertEqual(len(inventory['profiles']['qac_form_holdout']['excluded_verses']), 83)
        self.assertFalse(freeze['new_runtime_or_formal_files_opened_before_freeze'])

    def test_valid_correlated_report(self):
        inputs, report = example()
        evaluation.validate_report(report, inputs)

    def test_relational_time_preserves_attachment_and_gold_qualification(self):
        inputs, report = relational_time_example()
        evaluation.validate_report(report, inputs)
        claim = report['claims'][0]
        self.assertEqual(evaluation.gold_time_label(claim['time'][0]), claim['time'][0])
        unqualified = {**deepcopy(claim), 'time': []}
        self.assertNotEqual(evaluation.claim_key(claim), evaluation.claim_key(unqualified))
        self.assertNotEqual(evaluation.gold_claim_key(claim), evaluation.gold_claim_key(unqualified))

    def test_unresolved_temporal_object_remains_a_candidate(self):
        inputs, report = relational_time_example(resolved=False)
        evaluation.validate_report(report, inputs)
        analysis = report['clauses'][0]['analyses'][0]
        analysis['references_complete'] = True
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Unresolved temporal object'):
            evaluation.validate_report(report, inputs)

    def test_temporal_relation_cannot_borrow_head_edge_or_entity(self):
        for mutation in ('head', 'edge', 'entity', 'lemma'):
            inputs, report = relational_time_example()
            analysis = report['clauses'][0]['analyses'][0]
            if mutation == 'head':
                analysis['relations'][0]['head_span'] = analysis['assignments'][0]['span']
            elif mutation == 'edge':
                analysis['relations'].pop()
            else:
                field, value = ('object', 'h') if mutation == 'entity' else ('relation', 'آخر')
                for claim in analysis['claims'] + report['claims']:
                    claim['time'][0][field] = value
            rehash(report)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'Temporal qualification'):
                evaluation.validate_report(report, inputs)

    def test_relational_time_has_an_exact_typed_schema(self):
        _, report = relational_time_example()
        for value in ({'kind': 'temporal_relation', 'relation': 'حين', 'object': True},
                      {'kind': 'temporal_relation', 'relation': '', 'object': 'date'},
                      {'kind': 'temporal_relation', 'relation': 'حين', 'object': 'date', 'ignored': 'x'}):
            claim = {**deepcopy(report['claims'][0]), 'time': [value]}
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Invalid relational time'):
                evaluation.claim_view(claim)

    def test_closed_raw_journal_is_verified_against_log_time_capture(self):
        payload, captured, inventory, scores = journal_example()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.gz'
            path.write_bytes(gzip.compress(payload, mtime=0))
            checked = evaluation.verify_raw_journal(path, captured, inventory, scores)
        self.assertTrue(checked['valid'])
        self.assertEqual((checked['record_count'], checked['case_count'], checked['variant_count'],
                          checked['profile_count']), (3, 1, 1, 1))

    def test_a_hashed_truncated_gzip_is_not_a_valid_measurement(self):
        payload, captured, inventory, scores = journal_example()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.gz'
            path.write_bytes(gzip.compress(payload, mtime=0)[:-8])
            self.assertEqual(len(sha256(path.read_bytes()).hexdigest()), 64)
            with self.assertRaisesRegex(ValueError, 'Invalid raw measurement journal'):
                evaluation.verify_raw_journal(path, captured, inventory, scores)

    def test_closed_journal_rejects_lost_changed_or_extra_rows(self):
        payload, captured, inventory, scores = journal_example()
        lines = payload.splitlines(keepends=True)
        variants = [b''.join(lines[:-1]), payload.replace(b'authored_source', b'replaced_source'),
                    payload + lines[-1], b''.join(reversed(lines))]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.gz'
            for variant in variants:
                path.write_bytes(gzip.compress(variant, mtime=0))
                with self.subTest(variant=variant), self.assertRaisesRegex(ValueError, 'Raw journal'):
                    evaluation.verify_raw_journal(path, captured, inventory, scores)

    def test_journal_inventory_questions_and_scores_are_independently_held(self):
        payload, captured, inventory, scores = journal_example()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'raw.gz'
            path.write_bytes(gzip.compress(payload, mtime=0))
            for field, value in [('case_ids', ['other']), ('profiles', ['other']),
                                 ('variants', []), ('question_counts', {'authored': 2})]:
                changed = {**deepcopy(inventory), field: value}
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Raw journal'):
                    evaluation.verify_raw_journal(path, captured, changed, scores)
            with self.assertRaisesRegex(ValueError, 'Raw journal score'):
                evaluation.verify_raw_journal(path, captured, inventory, [{**scores[0], 'passed': False}])

    def test_closed_operator_reading_uses_its_complete_occurrence_partition(self):
        inputs, report = example()
        occurrence = report['occurrences'][0]
        occurrence['readings'].append({'reading_id': 'operator_alternative', 'kind': 'particle',
            'operator_qualified': True, 'construction': 'built', 'lexical_features': {},
            'segmentation': {'parts': [{'span': occurrence['span'], 'surface': occurrence['surface']}]},
            'nun_readings': []})
        rehash(report)
        evaluation.validate_report(report, inputs)
        occurrence['readings'][-1]['kind'] = 'noun'
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'omitted its stem'):
            evaluation.validate_report(report, inputs)

    def test_signed_claim_cannot_borrow_opposite_analysis(self):
        inputs, report = example()
        report['claims'][0]['positive'] = False
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Claim proof'):
            evaluation.validate_report(report, inputs)

    def test_qualification_cannot_be_erased_from_claim_proof(self):
        inputs, report = example()
        report['clauses'][0]['analyses'][0]['claims'][0]['time'] = ['أمس']
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Claim proof'):
            evaluation.validate_report(report, inputs)

    def test_property_event_and_voice_are_not_equal(self):
        _, report = example()
        claim = report['claims'][0]
        for field, value in [('predicate_kind', 'event'), ('voice', 'passive'), ('tense', 'past'),
                             ('place', ['p']), ('restriction', ['only'])]:
            other = {**deepcopy(claim), field: value}
            self.assertNotEqual(evaluation.claim_key(claim), evaluation.claim_key(other))

    def test_integer_is_not_claim_polarity(self):
        _, report = example()
        report['claims'][0]['positive'] = 1
        with self.assertRaises(ValueError):
            evaluation.claim_view(report['claims'][0])

    def test_role_required_case_is_checked_independently(self):
        inputs, report = example()
        report['clauses'][0]['analyses'][0]['assignments'][1]['required_case'] = 'jarr'
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Role/case'):
            evaluation.validate_report(report, inputs)

    def test_predicate_head_cannot_be_reassigned_to_itself(self):
        inputs, report = example()
        a = report['clauses'][0]['analyses'][0]['assignments'][1]
        a['head_span'] = a['span']
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Predicate governor'):
            evaluation.validate_report(report, inputs)

    def test_claim_arguments_cannot_borrow_another_context_entity(self):
        inputs, report = example()
        inputs['context']['entities'].append({'id': 'other', 'name': 'آخر'})
        update_context(inputs, report)
        report['claims'][0]['args'] = ['other']
        report['clauses'][0]['analyses'][0]['claims'][0]['args'] = ['other']
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'Claim argument'):
            evaluation.validate_report(report, inputs)

    def test_named_reference_cannot_substitute_a_different_name(self):
        inputs, report = example()
        inputs['context']['entities'].append({'id': 'other', 'name': 'آخر'})
        reference = report['clauses'][0]['analyses'][0]['references'][0]
        reference['candidate_entity_ids'], reference['bound_entity_id'] = ['other'], 'other'
        report['claims'][0]['args'] = ['other']
        report['clauses'][0]['analyses'][0]['claims'][0]['args'] = ['other']
        update_context(inputs, report)
        with self.assertRaisesRegex(ValueError, 'Reference candidates'):
            evaluation.validate_report(report, inputs)

    def test_predicate_cannot_borrow_subject_lemma(self):
        inputs, report = example()
        report['claims'][0]['predicate'] = 'حازم'
        report['clauses'][0]['analyses'][0]['claims'][0]['predicate'] = 'حازم'
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'predicate-role'):
            evaluation.validate_report(report, inputs)

    def test_participant_and_deictic_origins_require_original_bindings(self):
        for origin in ('speaker', 'addressee', 'deictic'):
            inputs, report = example()
            inputs['context']['entities'].append({'id': 'other', 'name': 'آخر'})
            inputs['context'].update(speaker='other', addressee='other',
                                     deixis=[{'form': 'حازم', 'entity_ids': ['other']}])
            reference = report['clauses'][0]['analyses'][0]['references'][0]
            reference['origin'] = origin
            update_context(inputs, report)
            with self.subTest(origin=origin), self.assertRaisesRegex(ValueError, 'Reference candidates'):
                evaluation.validate_report(report, inputs)

    def test_prior_defer_cannot_be_removed_from_reference_scope_receipt(self):
        context = {'closed_reference_scope': True}
        reference = {'origin': 'antecedent', 'source_prefix_complete': True,
                     'closed_scope': True, 'bound_entity_id': 'h'}
        with self.assertRaisesRegex(ValueError, 'prefix receipt'):
            evaluation.validate_reference_prefix(reference, [{'status': 'DEFER'}], context)
        reference['source_prefix_complete'] = False
        with self.assertRaisesRegex(ValueError, 'closed scope'):
            evaluation.validate_reference_prefix(reference, [{'status': 'DEFER'}], context)
        reference['closed_scope'] = False
        with self.assertRaisesRegex(ValueError, 'resolved across'):
            evaluation.validate_reference_prefix(reference, [{'status': 'DEFER'}], context)
        reference['bound_entity_id'] = None
        evaluation.validate_reference_prefix(reference, [{'status': 'DEFER'}], context)

    def test_prefix_receipt_keeps_mentions_and_explicit_participants_distinct(self):
        context = {'closed_reference_scope': True}
        reference = {'origin': 'antecedent', 'source_prefix_complete': True,
                     'closed_scope': True, 'bound_entity_id': 'h'}
        evaluation.validate_reference_prefix(reference, [{'status': 'MENTION'}, {'status': 'LICENSED'}], context)
        for origin in ('named', 'speaker', 'addressee', 'deictic', 'relative_return'):
            explicit = {**reference, 'origin': origin, 'source_prefix_complete': False}
            evaluation.validate_reference_prefix(explicit, [{'status': 'DEFER'}], context)

    def test_valid_polar_and_variable_answer(self):
        for variable in (False, True):
            inputs, document, inquiry, answer = answer_example(variable)
            evaluation.validate_answer(answer, document, inquiry, inputs, inputs['text'])

    def test_answer_kind_cannot_change_original_question(self):
        inputs, document, inquiry, answer = answer_example()
        answer['kind'] = 'person'
        answer['answer_id'] = evaluation.digest({k: v for k, v in answer.items() if k != 'answer_id'})
        with self.assertRaisesRegex(ValueError, 'Answer kind'):
            evaluation.validate_answer(answer, document, inquiry, inputs, inputs['text'])

    def test_person_binding_requires_explicit_person_domain(self):
        inputs, document, inquiry, answer = answer_example(True)
        inputs['context']['entities'][0]['kind'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'person/place domain'):
            evaluation.validate_answer(answer, document, inquiry, inputs, inputs['text'])

    def test_binding_status_cannot_claim_an_unproved_sign(self):
        inputs, document, inquiry, answer = answer_example(True)
        answer['bindings'][0]['status'] = 'REFUTED'
        answer['answer_id'] = evaluation.digest({k: v for k, v in answer.items() if k != 'answer_id'})
        with self.assertRaisesRegex(ValueError, 'binding status'):
            evaluation.validate_answer(answer, document, inquiry, inputs, inputs['text'])

    def test_proved_variable_binding_cannot_be_silently_omitted(self):
        inputs, document, inquiry, answer = answer_example(True)
        answer['bindings'] = []
        answer['answer_id'] = evaluation.digest({k: v for k, v in answer.items() if k != 'answer_id'})
        with self.assertRaisesRegex(ValueError, 'omitted or duplicated'):
            evaluation.validate_answer(answer, document, inquiry, inputs, inputs['text'])

    def test_unresolved_alternative_blocks_accepted_claim(self):
        inputs, report = example()
        a = deepcopy(report['clauses'][0]['analyses'][0])
        a['references_complete'] = False
        a['assertion_allowed'] = False
        a['claims'][0]['args'] = [None]
        a['references'][0]['bound_entity_id'] = None
        a['references'][0]['reference_id'] = evaluation.digest({k: v for k, v in a['references'][0].items() if k != 'reference_id'})
        report['clauses'][0]['analyses'].append(a)
        rehash(report)
        with self.assertRaisesRegex(ValueError, 'unresolved alternative'):
            evaluation.validate_report(report, inputs)

    def test_complete_nun_cluster_required(self):
        text = 'يَحْزَنُونَ'
        raw = text.encode()
        start = raw.rindex('ن'.encode())
        inputs = {'text': text, 'source_id': 'nun'}
        span = {'source_id': 'nun', 'source_sha256': sha256(raw).hexdigest(), 'start': start, 'end': len(raw)}
        nun = {'span': span, 'surface': 'نَ'}
        self.assertTrue(evaluation.nun_span_valid(nun, inputs))
        nun['span'] = {**span, 'end': start + len('ن'.encode())}
        nun['surface'] = 'ن'
        self.assertFalse(evaluation.nun_span_valid(nun, inputs))

    def test_binding_instantiation_preserves_all_other_fields(self):
        _, report = example()
        pattern = deepcopy(report['claims'][0])
        pattern['args'] = ['?person']
        pattern['time'] = ['?time']
        bound = evaluation.instantiate(pattern, {'?person': 'h', '?time': 'أَمْس'})
        self.assertEqual(bound['time'], ['أَمْس'])
        self.assertEqual(evaluation.gold_time_label(bound['time'][0]), 'أمس')
        self.assertEqual(bound['predicate_kind'], 'property')
        with self.assertRaises(ValueError):
            evaluation.instantiate(pattern, {'?person': 'h'})
        with self.assertRaises(ValueError):
            evaluation.instantiate(pattern, {'?person': 'h', '?time': 'أمس', '?other': 'h'})

    def test_time_article_is_preserved_in_proof_and_gold_comparison(self):
        _, report = example()
        today = {**report['claims'][0], 'time': [{'lemma': 'يَوْم', 'form': 'اليوم', 'source_article': True}]}
        indefinite = {**report['claims'][0], 'time': [{'lemma': 'يَوْم', 'form': 'يوما', 'source_article': False}]}
        gold = {**report['claims'][0], 'time': ['اليوم']}
        self.assertNotEqual(evaluation.claim_key(today), evaluation.claim_key(indefinite))
        self.assertNotEqual(evaluation.claim_key(today), evaluation.claim_key(gold))
        self.assertEqual(evaluation.gold_claim_key(today), evaluation.gold_claim_key(gold))
        self.assertNotEqual(evaluation.gold_claim_key(indefinite), evaluation.gold_claim_key(gold))
        changed_lemma = deepcopy(today)
        changed_lemma['time'][0]['lemma'] = 'أَمْس'
        self.assertNotEqual(evaluation.gold_claim_key(changed_lemma), evaluation.gold_claim_key(gold))

    def test_qualified_time_binding_is_not_replaced_by_its_display_label(self):
        _, report = example()
        pattern = {**report['claims'][0], 'time': ['?time']}
        value = {'lemma': 'يَوْم', 'form': 'اليوم', 'source_article': True}
        bound = evaluation.instantiate(pattern, {'?time': value})
        self.assertEqual(bound['time'], [value])
        self.assertEqual(evaluation.gold_time_label(bound['time'][0]), 'اليوم')
        bad = {**bound, 'time': [{**value, 'source_article': 1}]}
        with self.assertRaisesRegex(ValueError, 'qualified time'):
            evaluation.claim_view(bad)

    def test_documented_boundary_gate_does_not_change_strict_coverage(self):
        cases = [{'id': c['id'], 'passed': True, 'failures': [], 'false_accepts': []}
                 for c in evaluation.load_material()[1]['cases']]
        boundary = next(c for c in cases if c['id'] == 'DSC-P02')
        boundary.update(passed=False, failures=[{'check': 'required_claim:0'}])
        result = {'cases': cases, 'total': 86, 'strict_pass': False, 'false_accept_count': 0,
                  'execution_errors': [], 'question_execution_errors': [],
                  'snapshot': {'runtime_freeze_sha256': 'approved'}}
        with patch.object(evaluation, 'DOCUMENTED_BOUNDARY_RUNTIME', 'approved'):
            self.assertFalse(evaluation.gate_decision(result)['gate_pass'])
            permitted = evaluation.gate_decision(result, True)
            self.assertTrue(permitted['gate_pass'])
            self.assertFalse(permitted['coverage_complete'])
            self.assertFalse(result['strict_pass'])
            boundary['failures'].append({'check': 'report_integrity'})
            self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])
            boundary['failures'].pop()
            result['false_accept_count'] = 1
            self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])
            result['false_accept_count'] = 0
            result['question_execution_errors'] = [{'type': 'ValueError'}]
            self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])
            result['question_execution_errors'] = []
            result['snapshot']['runtime_freeze_sha256'] = 'unapproved'
            self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])

    def test_p09_prefix_coverage_exception_is_check_specific_and_not_safety(self):
        cases = [{'id': c['id'], 'passed': True, 'failures': [], 'false_accepts': []}
                 for c in evaluation.load_material()[1]['cases']]
        boundary = next(c for c in cases if c['id'] == 'DSC-P09')
        boundary.update(passed=False, failures=[{'check': name} for name in
                        ('required_claim:0', 'reading:0', 'question:0')])
        result = {'cases': cases, 'total': 86, 'strict_pass': False, 'false_accept_count': 0,
                  'execution_errors': [], 'question_execution_errors': [],
                  'snapshot': {'runtime_freeze_sha256': evaluation.DOCUMENTED_BOUNDARY_RUNTIME}}
        self.assertFalse(evaluation.gate_decision(result)['gate_pass'])
        permitted = evaluation.gate_decision(result, True)
        self.assertTrue(permitted['gate_pass'])
        self.assertFalse(permitted['coverage_complete'])
        self.assertFalse(result['strict_pass'])
        for additional in ('required_claim:1', 'reading:1', 'forbidden_claim:0', 'report_integrity'):
            boundary['failures'].append({'check': additional})
            self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])
            boundary['failures'].pop()
        boundary['false_accepts'] = ['unsupported pronoun binding']
        result['false_accept_count'] = 1
        self.assertFalse(evaluation.gate_decision(result, True)['gate_pass'])


if __name__ == '__main__':
    unittest.main()

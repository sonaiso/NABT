"""Authored adversarial receipt tests; no parser, gold, or holdout execution.

These are public-contract objects, not claims that the abbreviated synthetic
reports below constitute full Arabic parses. Matching outcomes are supplied
explicitly by each test. No production answer/matching helper constructs them.
"""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_evaluator(name):
    spec = importlib.util.spec_from_file_location('independent_test_' + name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATORS = (load_evaluator('discourse_evaluation'), load_evaluator('construction_evaluation'))
FIELDS = ('predicate', 'predicate_kind', 'voice', 'args', 'positive', 'tense', 'time', 'place', 'restriction')
RULE = 'EXACT_SIGNED_QUALIFIED_CLAIM_WITH_EXPLICIT_VARIABLE_SUBSTITUTION'


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def rehash_answer(answer):
    answer['answer_id'] = digest({key: value for key, value in answer.items() if key != 'answer_id'})


def rehash_report(report):
    old_ids = {}
    for clause in report['clauses']:
        old_clause_id = clause.get('clause_id')
        for analysis in clause['analyses']:
            old_analysis_id = analysis.get('analysis_id')
            analysis['analysis_id'] = digest({key: value for key, value in analysis.items() if key != 'analysis_id'})
            old_ids[old_analysis_id] = analysis['analysis_id']
        clause['clause_id'] = digest({key: value for key, value in clause.items() if key != 'clause_id'})
        old_ids[old_clause_id] = clause['clause_id']
    for claim in report['claims']:
        for proof in claim['proofs']:
            proof['analysis_id'] = old_ids.get(proof['analysis_id'], proof['analysis_id'])
            proof['clause_id'] = old_ids.get(proof['clause_id'], proof['clause_id'])
    report['report_id'] = digest({key: value for key, value in report.items() if key != 'report_id'})


def authored_reports(styles=('plain', 'typed'), *, gender='masculine', signs=(True,), source_predicate='حكيم'):
    text, question = 'زيد حكيم', 'من حكيم'
    inputs = {'text': text, 'source_id': 'authored_source', 'scope': 'receipt_test',
              'context': {'entities': [{'id': 'z', 'name': 'زيد', 'kind': 'person',
                                       'gender': gender, 'number': 'singular'}], 'closed_reference_scope': True}}
    source_sha, question_sha = sha256(text.encode()).hexdigest(), sha256(question.encode()).hexdigest()
    context = {'value': deepcopy(inputs['context']), 'sha256': digest(inputs['context'])}
    def span(start, end):
        return {'source_id': inputs['source_id'], 'source_sha256': source_sha, 'start': start, 'end': end}
    head_span, dependent_span, whole = span(0, 6), span(7, 15), span(0, 15)
    profile = {'gender': gender, 'number': 'singular'}
    rows = [{'reading_id': 'subject', 'kind': 'noun', 'construction': None,
             'stem_span': head_span, 'lexical_features': {'pos': 'PN', 'lemma': 'زيد', **profile}},
            {'reading_id': 'predicate', 'kind': 'noun', 'construction': None,
             'stem_span': dependent_span, 'lexical_features': {'pos': 'ADJ', 'lemma': source_predicate, **profile}}]
    reference = {'reference_id': 'authored_reference', 'status': 'RESOLVED', 'origin': 'named',
                 'span': head_span, 'bound_entity_id': 'z', 'context_sha256': context['sha256']}
    assignments = [{'reading_id': 'subject', 'role': 'nominal_subject', 'span': head_span,
                    'activated': True, 'head_span': None},
                   {'reading_id': 'predicate', 'role': 'nominal_predicate', 'span': dependent_span,
                    'activated': True, 'head_span': head_span}]
    relation = {'kind': 'predicate_agreement', 'status': 'confirmed', 'regime_licensed': True,
                'head_reading_id': 'subject', 'dependent_reading_id': 'predicate',
                'head_span': head_span, 'dependent_span': dependent_span,
                'subject_role': 'nominal_subject', 'predicate_role': 'nominal_predicate',
                'subject_profile': profile, 'predicate_profile': profile,
                'axes': {'gender': 'confirmed', 'number': 'confirmed'}, 'predicate_lemma': source_predicate,
                'subject_reference_ids': [reference['reference_id']]}
    base = {'predicate': source_predicate, 'predicate_kind': 'property', 'voice': None,
            'args': ['z'], 'positive': True, 'tense': 'unspecified', 'time': [], 'place': [], 'restriction': []}
    document = {'source_text': text, 'source_id': inputs['source_id'], 'scope': inputs['scope'],
                'source_sha256': source_sha, 'context': context, 'status': 'LICENSED_DISCOURSE',
                'world_truth': 'NOT_ESTABLISHED', 'clauses': [], 'claims': [],
                'occurrences': [{'span': row['stem_span'], 'readings': [row]} for row in rows], 'derived_readings': []}
    for positive in signs:
        claim = {**deepcopy(base), 'positive': positive}
        analysis = {'reading_ids': ['subject', 'predicate'], 'rejected_candidate': False,
                    'licensed_syntax': True, 'references_complete': True, 'force': 'ASSERT',
                    'assertion_allowed': True, 'claims': [deepcopy(claim)], 'relations': [deepcopy(relation)],
                    'references': [deepcopy(reference)], 'assignments': deepcopy(assignments)}
        analysis['analysis_id'] = digest(analysis)
        clause = {'span': whole, 'status': 'LICENSED', 'force': 'ASSERT', 'analyses': [analysis]}
        clause['clause_id'] = digest(clause)
        claim.update(claim_id=digest(claim), proofs=[{'clause_id': clause['clause_id'],
                     'analysis_id': analysis['analysis_id'], 'span': whole}])
        document['clauses'].append(clause)
        document['claims'].append(claim)
    rehash_report(document)
    query_base = {**deepcopy(base), 'predicate': 'حكيم'}
    analyses = []
    for index, style in enumerate(styles):
        argument = ({'kind': 'question_variable', 'name': '?person', 'gender': 'masculine', 'number': 'singular'}
                    if style == 'typed' else 'z' if style == 'polar' else '?person')
        analysis = {'authored_alternative': index, 'rejected_candidate': False, 'licensed_syntax': True,
                    'references_complete': True, 'force': 'QUESTION', 'assertion_allowed': False,
                    'question_kind': 'polar' if style == 'polar' else 'person',
                    'claims': [{**deepcopy(query_base), 'args': [argument]}]}
        analysis['analysis_id'] = digest(analysis)
        analyses.append(analysis)
    clause = {'status': 'DEFER' if len(set(styles)) > 1 else 'LICENSED',
              'force': 'AMBIGUOUS' if len(set(styles)) > 1 else 'QUESTION', 'analyses': analyses}
    clause['clause_id'] = digest(clause)
    inquiry = {'source_text': question, 'source_id': 'question', 'scope': inputs['scope'],
               'source_sha256': question_sha, 'context': deepcopy(context),
               'status': 'DEFER' if len(set(styles)) > 1 else 'LICENSED_DISCOURSE',
               'clauses': [clause], 'claims': [], 'world_truth': 'NOT_ESTABLISHED'}
    rehash_report(inquiry)
    return inputs, document, inquiry


def authored_answer(inputs, document, inquiry, results, *, top_status='SUPPORTED', common_query=False,
                    missing=(), basis='ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE'):
    """results are explicit (analysis index, status, positive IDs, negative IDs)."""
    interpretations = []
    for index, status, positives, negatives in results:
        clause, analysis = inquiry['clauses'][0], inquiry['clauses'][0]['analyses'][index]
        query = deepcopy(analysis['claims'][0])
        kind = analysis.get('question_kind') or 'polar'
        result = {'clause_id': clause['clause_id'], 'analysis_id': analysis['analysis_id'],
                  'kind': kind, 'query': query, 'status': status, 'proofs': [], 'counterproofs': [], 'bindings': []}
        for sign, indices in [('proofs', positives), ('counterproofs', negatives)]:
            for claim_index in indices:
                claim = document['claims'][claim_index]
                proof = {'claim_id': claim['claim_id'], 'document_report_id': document['report_id'],
                         'question_report_id': inquiry['report_id'], 'question_analysis_id': analysis['analysis_id'],
                         'bindings': {} if kind == 'polar' else {'?person': 'z'},
                         'source_proofs': deepcopy(claim['proofs']), 'rule': RULE}
                if type(query['args'][0]) is dict:
                    source = document['clauses'][claim_index]
                    source_analysis = source['analyses'][0]
                    proof['predicate_agreement_bindings'] = [{'argument_index': 0, 'variable': '?person',
                        'entity_id': 'z', 'required_profile': {'gender': 'masculine', 'number': 'singular'},
                        'context_sha256': document['context']['sha256'], 'source_witnesses': [{
                            'clause_id': source['clause_id'], 'analysis_id': source_analysis['analysis_id'],
                            'head_reading_id': 'subject', 'dependent_reading_id': 'predicate',
                            'reference_id': 'authored_reference'}]}]
                result[sign].append(proof)
        if kind != 'polar' and positives:
            result['bindings'] = [{'values': {'?person': 'z'}, 'status': 'CONFLICT' if negatives else 'SUPPORTED',
                                   'proofs': deepcopy(result['proofs']), 'counterproofs': deepcopy(result['counterproofs'])}]
        interpretations.append(result)
    answer = {'schema': 'nabt.discourse-answer.v2', 'source_text': inputs['text'],
              'question_text': inquiry['source_text'], 'source_id': inputs['source_id'], 'scope': inputs['scope'],
              'source_sha256': document['source_sha256'], 'question_sha256': inquiry['source_sha256'],
              'document_report_id': document['report_id'], 'question_report_id': inquiry['report_id'],
              'context_sha256': document['context']['sha256'], 'world_truth': 'NOT_ESTABLISHED',
              'status': top_status, 'query': deepcopy(interpretations[0]['query']) if common_query and interpretations else None,
              'kind': interpretations[0]['kind'] if interpretations else None, 'proofs': [], 'counterproofs': [], 'bindings': [],
              'question_interpretations': interpretations, 'answer_basis': basis, 'missing_premises': list(missing)}
    if top_status != 'DEFER':
        for sign in ('proofs', 'counterproofs'):
            answer[sign] = [deepcopy(proof) for result in interpretations for proof in result[sign]]
        if interpretations and interpretations[0]['bindings']:
            answer['bindings'] = [{'values': {'?person': 'z'}, 'status': interpretations[0]['bindings'][0]['status'],
                                   'proofs': deepcopy(answer['proofs']), 'counterproofs': deepcopy(answer['counterproofs'])}]
    rehash_answer(answer)
    return answer


class QuestionInterpretationValidationTests(unittest.TestCase):
    def check(self, inputs, document, inquiry, answer):
        for evaluator in EVALUATORS:
            with self.subTest(evaluator=evaluator.__file__):
                evaluator.validate_answer(answer, document, inquiry, inputs, inquiry['source_text'])

    def reject(self, inputs, document, inquiry, answer, pattern=None):
        rehash_answer(answer)
        for evaluator in EVALUATORS:
            with self.subTest(evaluator=evaluator.__file__):
                manager = self.assertRaisesRegex(ValueError, pattern) if pattern else self.assertRaises(ValueError)
                with manager:
                    evaluator.validate_answer(answer, document, inquiry, inputs, inquiry['source_text'])

    def consensus(self, styles=('plain', 'typed')):
        values = authored_reports(styles)
        answer = authored_answer(*values, [(i, 'SUPPORTED', [0], []) for i in range(len(styles))],
                                 common_query=len(set(styles)) == 1)
        return (*values, answer)

    def test_consensus_retains_every_complete_pattern_and_receipt(self):
        for styles in [('plain', 'typed'), ('plain', 'plain'), ('polar',)]:
            self.check(*self.consensus(styles))

    def test_different_outcomes_defer_with_all_subresults_retained(self):
        values = authored_reports(gender='feminine')
        answer = authored_answer(*values, [(0, 'SUPPORTED', [0], []), (1, 'UNKNOWN', [], [])],
                                 top_status='DEFER', basis=None, missing=['QUESTION_INTERPRETATION_OUTCOMES_DISAGREE'])
        self.check(*values, answer)
        answer['status'], answer['answer_basis'] = 'SUPPORTED', 'ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE'
        self.reject(*values, answer)

    def test_equal_unknown_status_with_different_counterproofs_is_not_consensus(self):
        values = authored_reports(gender='feminine', signs=(False,))
        answer = authored_answer(*values, [(0, 'UNKNOWN', [], [0]), (1, 'UNKNOWN', [], [])],
                                 top_status='DEFER', basis=None, missing=['QUESTION_INTERPRETATION_OUTCOMES_DISAGREE'])
        self.check(*values, answer)
        answer['status'], answer['answer_basis'], answer['missing_premises'] = 'UNKNOWN', 'ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE', []
        self.reject(*values, answer)

    def test_unknown_variable_answer_can_retain_only_counterproofs(self):
        values = authored_reports(signs=(False,))
        answer = authored_answer(*values, [(0, 'UNKNOWN', [], [0]), (1, 'UNKNOWN', [], [0])], top_status='UNKNOWN')
        self.check(*values, answer)
        self.assertEqual(answer['bindings'], [])
        self.assertEqual(len(answer['counterproofs']), 2)

    def test_polar_refutation_and_conflict_are_recomputed(self):
        for signs, status, positive, negative in [((False,), 'REFUTED', [], [0]),
                                                  ((True, False), 'CONFLICT', [0], [1])]:
            values = authored_reports(('polar',), signs=signs)
            answer = authored_answer(*values, [(0, status, positive, negative)], top_status=status, common_query=True)
            self.check(*values, answer)
            answer['status'] = 'UNKNOWN'
            self.reject(*values, answer)

    def test_viable_incomplete_alternative_cannot_be_ignored(self):
        for field, value in [('licensed_syntax', False), ('references_complete', False)]:
            inputs, document, inquiry = authored_reports()
            inquiry['clauses'][0]['analyses'][1][field] = value
            rehash_report(inquiry)
            forged = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
            self.reject(inputs, document, inquiry, forged, 'inventory')
            deferred = authored_answer(inputs, document, inquiry, [], top_status='DEFER', basis=None,
                                       missing=['ONE_COMPLETE_QUESTION_READING'])
            self.check(inputs, document, inquiry, deferred)

    def test_rejected_alternative_is_excluded_without_requiring_its_completeness(self):
        inputs, document, inquiry = authored_reports()
        rejected = inquiry['clauses'][0]['analyses'][1]
        rejected.update(rejected_candidate=True, licensed_syntax=False, references_complete=False)
        rehash_report(inquiry)
        answer = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
        self.check(inputs, document, inquiry, answer)
        forged = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], []), (1, 'SUPPORTED', [0], [])])
        self.reject(inputs, document, inquiry, forged, 'inventory')

    def test_nonquestion_or_non_single_claim_alternative_blocks_all_subresults(self):
        for mutation in ['force', 'no_claim', 'two_claims']:
            inputs, document, inquiry = authored_reports()
            analysis = inquiry['clauses'][0]['analyses'][1]
            if mutation == 'force':
                analysis['force'] = 'ASSERT'
            elif mutation == 'no_claim':
                analysis['claims'] = []
            else:
                analysis['claims'].append(deepcopy(analysis['claims'][0]))
            rehash_report(inquiry)
            answer = authored_answer(inputs, document, inquiry, [], top_status='DEFER', basis=None,
                                     missing=['EXPLICIT_SINGLE_QUESTION_FORCE'])
            self.check(inputs, document, inquiry, answer)
            forged = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
            self.reject(inputs, document, inquiry, forged)

    def test_dropping_or_duplicating_an_equal_pattern_is_rejected(self):
        for mutation in ['drop', 'duplicate']:
            inputs, document, inquiry, answer = self.consensus(('plain', 'plain'))
            if mutation == 'drop':
                answer['question_interpretations'].pop()
            else:
                answer['question_interpretations'][1] = deepcopy(answer['question_interpretations'][0])
            self.reject(inputs, document, inquiry, answer, 'inventory|unique viable')

    def test_interpretation_must_be_the_same_inquiry_analysis(self):
        for field, value in [('analysis_id', 'foreign'), ('clause_id', 'foreign'), ('kind', 'polar')]:
            inputs, document, inquiry, answer = self.consensus()
            answer['question_interpretations'][0][field] = value
            self.reject(inputs, document, inquiry, answer)
        inputs, document, inquiry, answer = self.consensus()
        answer['question_interpretations'][0]['query'] = deepcopy(answer['question_interpretations'][1]['query'])
        self.reject(inputs, document, inquiry, answer, 'original inquiry pattern')

    def test_missing_matching_claims_cannot_be_hidden_by_unknown_status(self):
        values = authored_reports(('plain',))
        answer = authored_answer(*values, [(0, 'UNKNOWN', [], [])], top_status='UNKNOWN', common_query=True)
        self.reject(*values, answer, 'all source matches')

    def test_same_status_does_not_allow_omission_of_one_matching_source_claim(self):
        inputs, document, inquiry = authored_reports(('plain',))
        second = deepcopy(document['claims'][0])
        second['claim_id'] = 'separate_accepted_source_claim'
        document['claims'].append(second)
        rehash_report(document)
        answer = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
        self.reject(inputs, document, inquiry, answer, 'complete proofs')

    def test_every_proof_is_bound_to_its_query_analysis_and_full_source_receipt(self):
        for mutation in ['question_analysis_id', 'question_report_id', 'source_proofs', 'rule', 'duplicate']:
            inputs, document, inquiry, answer = self.consensus()
            result = answer['question_interpretations'][0]
            if mutation == 'duplicate':
                result['proofs'].append(deepcopy(result['proofs'][0]))
            else:
                result['proofs'][0][mutation] = [] if mutation == 'source_proofs' else 'foreign'
            self.reject(inputs, document, inquiry, answer, 'complete proofs')

    def test_top_level_must_retain_all_interpretation_receipts(self):
        for field in ['proofs', 'bindings']:
            inputs, document, inquiry, answer = self.consensus()
            if field == 'proofs':
                answer['proofs'].pop()
            else:
                answer['bindings'][0]['proofs'].pop()
            self.reject(inputs, document, inquiry, answer)

    def test_top_query_only_exists_for_exactly_one_common_pattern(self):
        inputs, document, inquiry, answer = self.consensus()
        answer['query'] = deepcopy(answer['question_interpretations'][0]['query'])
        self.reject(inputs, document, inquiry, answer, 'common interpretation pattern')
        inputs, document, inquiry, answer = self.consensus(('plain', 'plain'))
        answer['query'] = None
        self.reject(inputs, document, inquiry, answer, 'common interpretation pattern')

    def test_qualified_patterns_cannot_borrow_an_unqualified_proof(self):
        for field, value in [('time', ['أمس']), ('place', ['p']), ('restriction', ['only']), ('tense', 'past')]:
            inputs, document, inquiry = authored_reports(('plain',))
            inquiry['clauses'][0]['analyses'][0]['claims'][0][field] = value
            rehash_report(inquiry)
            answer = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
            self.reject(inputs, document, inquiry, answer, 'all source matches')

    def test_relative_inner_predicate_cannot_lend_outer_claim_agreement(self):
        inputs, document, inquiry = authored_reports(('typed',))
        analysis = document['clauses'][0]['analyses'][0]
        edge = analysis['relations'][0]
        analysis['relations'].append({'kind': 'relative_clause',
            'inner_predicate_reading_id': edge['dependent_reading_id'], 'inner_predicate_span': deepcopy(edge['dependent_span'])})
        rehash_report(document)
        forged = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
        self.reject(inputs, document, inquiry, forged, 'all source matches')
        safe = authored_answer(inputs, document, inquiry, [(0, 'UNKNOWN', [], [])], top_status='UNKNOWN', common_query=True)
        self.check(inputs, document, inquiry, safe)
        for evaluator in EVALUATORS:
            witnesses = evaluator.question_validation.source_agreement_witnesses(
                document['claims'][0], {'gender': 'masculine', 'number': 'singular'}, 'z', document)
            self.assertEqual(witnesses, [])
        self.assertEqual(EVALUATORS[0].source_agreement_witnesses(
            document['claims'][0], {'gender': 'masculine', 'number': 'singular'}, 'z', document), [])

    def test_typed_receipt_cannot_borrow_a_differently_qualified_claim(self):
        inputs, document, inquiry = authored_reports(('typed',))
        analysis = document['clauses'][0]['analyses'][0]
        analysis['claims'].append({**deepcopy(analysis['claims'][0]), 'time': ['أمس']})
        rehash_report(document)
        answer = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], [])], common_query=True)
        self.reject(inputs, document, inquiry, answer, 'all source matches')

    def test_agreement_receipt_profiles_and_complete_witnesses_are_recomputed(self):
        for mutation in ['profile', 'context', 'reference', 'omitted', 'duplicate', 'extra_field']:
            inputs, document, inquiry, answer = self.consensus()
            proof = answer['question_interpretations'][1]['proofs'][0]
            receipt = proof['predicate_agreement_bindings'][0]
            if mutation == 'profile':
                receipt['required_profile']['gender'] = 'feminine'
            elif mutation == 'context':
                receipt['context_sha256'] = 'foreign'
            elif mutation == 'reference':
                receipt['source_witnesses'][0]['reference_id'] = 'foreign'
            elif mutation == 'omitted':
                receipt['source_witnesses'] = []
            elif mutation == 'duplicate':
                receipt['source_witnesses'].append(deepcopy(receipt['source_witnesses'][0]))
            else:
                receipt['ungranted_authority'] = True
            self.reject(inputs, document, inquiry, answer, 'agreement receipts')

    def test_incomplete_source_keeps_patterns_but_has_no_answer_receipts(self):
        inputs, document, inquiry = authored_reports()
        document['status'] = 'DEFER'
        rehash_report(document)
        answer = authored_answer(inputs, document, inquiry, [(0, 'DEFER', [], []), (1, 'DEFER', [], [])],
                                 top_status='DEFER', basis=None, missing=['COMPLETE_SOURCE_DISCOURSE_READING'])
        self.check(inputs, document, inquiry, answer)
        forged = authored_answer(inputs, document, inquiry, [(0, 'SUPPORTED', [0], []), (1, 'SUPPORTED', [0], [])])
        self.reject(inputs, document, inquiry, forged)

    def test_new_schema_cannot_downgrade_by_omitting_interpretation_inventory(self):
        inputs, document, inquiry, answer = self.consensus(('polar',))
        del answer['question_interpretations']
        self.reject(inputs, document, inquiry, answer, 'inventory must be a list')

    def test_legacy_single_query_receipt_still_validates(self):
        inputs, document, inquiry, answer = self.consensus(('polar',))
        for field in ['question_interpretations', 'answer_basis', 'missing_premises']:
            del answer[field]
        answer['schema'] = 'nabt.discourse-answer.v1'
        for proof in answer['proofs']:
            del proof['question_analysis_id']
        rehash_answer(answer)
        self.check(inputs, document, inquiry, answer)


if __name__ == '__main__':
    unittest.main()

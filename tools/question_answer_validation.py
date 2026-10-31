"""Independent validation of the public multi-interpretation answer contract.

This module has no runtime imports. It reconstructs matches from the supplied,
separately validated source claims and checks every viable question analysis.
It does not establish that the source report is true, or that its parser is
complete. The caller still validates the two reports and their replay receipts.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json


CLAIM_FIELDS = ('predicate', 'predicate_kind', 'voice', 'args', 'positive',
                'tense', 'time', 'place', 'restriction')
PROOF_RULE = 'EXACT_SIGNED_QUALIFIED_CLAIM_WITH_EXPLICIT_VARIABLE_SUBSTITUTION'
CONSENSUS_BASIS = 'ALL_COMPLETE_QUERY_INTERPRETATIONS_AGREE'
VARIABLES = {'polar': set(), 'person': {'?person'}, 'subject': {'?person'},
             'object': {'?object'}, 'place': {'?place'}, 'time': {'?time'}}


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def constrained_person_argument(value):
    return (type(value) is dict and set(value) == {'kind', 'name', 'gender', 'number'}
            and value['kind'] == 'question_variable' and value['name'] == '?person'
            and value['gender'] in ('masculine', 'feminine') and value['number'] == 'singular')


def semantic_key(claim):
    return wire({field: claim[field] for field in CLAIM_FIELDS})


def _feature(row, axis):
    return row.get('profile', {}).get(axis, row.get('lexical_features', {}).get(axis))


def _span(span):
    return span['start'], span['end']


def _reading_rows(document):
    rows, ranges = {}, defaultdict(set)
    for occurrence in document.get('occurrences', []):
        for row in occurrence.get('readings', []):
            rid = row['reading_id']
            require(rid not in rows or rows[rid] == row, 'Reading identity collision in agreement witness')
            rows[rid] = row
            ranges[rid].add(_span(occurrence['span']))
    for row in document.get('derived_readings', []):
        rid = row['reading_id']
        require(rid not in rows or rows[rid] == row, 'Derived reading identity collision in agreement witness')
        rows[rid] = row
        ranges[rid].add(_span(row['stem_span']))
    return rows, ranges


def _subject_profile_supported(row, relation, reference, required, context_sha256):
    if all(_feature(row, axis) == value for axis, value in required.items()):
        return True
    basis, features = relation.get('subject_gender_basis', {}), row.get('lexical_features', {})
    common = (features.get('pos') == 'PRON' and _feature(row, 'gender') in (None, 'unknown')
              and _feature(row, 'number') == required['number']
              and basis.get('kind') == 'resolved_common_gender_pronoun'
              and reference.get('reference_id') in basis.get('reference_ids', [])
              and row.get('segmentation', {}).get('licensed') is True)
    named = (features.get('pos') == 'PN' and row.get('construction') is None
             and row.get('variant') == 'declared_grammatical_paradigm'
             and row.get('segmentation', {}).get('licensed') is True
             and row.get('support_records') == [{'kind': 'explicit_context',
                  'sha256': context_sha256, 'field': 'entities.name'}]
             and reference.get('origin') == 'named'
             and basis.get('kind') == 'explicit_named_person_semantic_profile'
             and basis.get('lexical_profile_acquired') is False
             and basis.get('source_fields') == ['entities.name', 'entities.kind', 'entities.gender', 'entities.number']
             and basis.get('reference_ids') == [reference.get('reference_id')]
             and all(features.get(axis) is None for axis in ('gender', 'number')))
    return ((common or named) and basis.get('entity_id') == reference.get('bound_entity_id')
            and basis.get('context_sha256') == context_sha256)


def _linked_contract(document):
    """Current receipts cannot silently fall back to the historical guard."""
    current = (document.get('schema') == 'nabt.discourse-report.v2' or
               document.get('reader_version') == 'nabt.discourse-reader.v8')
    if current:
        require(document.get('schema') == 'nabt.discourse-report.v2' and
                document.get('reader_version') == 'nabt.discourse-reader.v8' and
                document.get('claim_binding_schema') == 'nabt.claim-predication-binding.v1',
                'Incomplete versioned claim-predication contract')
    return current


def _direct_bindings(proof, analysis, claim, relation, document):
    """Independently check the producer-selected claim/edge association.

    Claim equality alone is deliberately insufficient. The index, direct path,
    occurrence, reading, role and reference all belong to this alternative.
    """
    index = proof.get('claim_index')
    ids = proof.get('predication_binding_ids')
    if (type(index) is not int or not 0 <= index < len(analysis['claims']) or
            semantic_key(analysis['claims'][index]) != semantic_key(claim) or
            type(ids) is not list or any(type(value) is not str for value in ids) or
            len(ids) != len(set(ids))):
        return []
    keys = {'schema', 'claim_index', 'claim_path', 'subject_reading_id', 'subject_span', 'subject_role',
            'predicate_reading_id', 'predicate_span', 'predicate_role', 'subject_reference_ids',
            'source_id', 'source_sha256', 'scope', 'force', 'owner_claim_key', 'claim_key',
            'agreement_relation_id', 'binding_id'}
    expected_key = sha256(wire(analysis['claims'][index])).hexdigest()
    selected = []
    for binding in analysis.get('claim_bindings', []):
        if (type(binding) is not dict or set(binding) != keys or
                binding['schema'] != 'nabt.claim-predication-binding.v1' or
                type(binding['claim_index']) is not int or binding['claim_index'] != index or
                binding['claim_path'] != [] or binding['force'] != analysis['force'] or
                any(binding[field] != document[field] for field in ('source_id', 'source_sha256', 'scope')) or
                binding['claim_key'] != expected_key or binding['owner_claim_key'] != expected_key or
                binding['binding_id'] not in ids or binding['binding_id'] !=
                    sha256(wire({key: value for key, value in binding.items() if key != 'binding_id'})).hexdigest() or
                binding['agreement_relation_id'] != sha256(wire(relation)).hexdigest() or
                type(binding['subject_reference_ids']) is not list or len(binding['subject_reference_ids']) != 1 or
                any(type(value) is not str for value in binding['subject_reference_ids']) or
                any(value not in relation.get('subject_reference_ids', [])
                    for value in binding['subject_reference_ids'])):
            continue
        if all(binding[left] == relation.get(right) for left, right in (
                ('subject_reading_id', 'head_reading_id'), ('predicate_reading_id', 'dependent_reading_id'),
                ('subject_span', 'head_span'), ('predicate_span', 'dependent_span'),
                ('subject_role', 'subject_role'), ('predicate_role', 'predicate_role'))):
            selected.append(binding)
    return selected


def source_agreement_witnesses(claim, required, entity_id, document):
    """Return only the accepted claim's own adjective/subject witnesses.

    A relative clause's inner predicate is not the outer claim's predicate,
    even if the lemma, person, and agreement axes happen to be identical.
    """
    rows, ranges = _reading_rows(document)
    linked = _linked_contract(document)
    analyses = {(clause['clause_id'], analysis['analysis_id']): analysis
                for clause in document['clauses'] if clause['status'] == 'LICENSED'
                for analysis in clause['analyses']}
    pairs = {'nominal_predicate': 'nominal_subject', 'inna_predicate': 'inna_subject',
             'kana_predicate': 'kana_subject'}
    witnesses = []
    for proof in claim['proofs']:
        analysis = analyses.get((proof['clause_id'], proof['analysis_id']))
        if (analysis is None or analysis.get('rejected_candidate') is not False
                or analysis.get('licensed_syntax') is not True or analysis.get('references_complete') is not True
                or analysis.get('assertion_allowed') is not True or analysis.get('force') != 'ASSERT'
                or not any(semantic_key(other) == semantic_key(claim) for other in analysis['claims'])):
            continue
        if not linked and any(semantic_key(other) != semantic_key(claim) for other in analysis['claims']):
            continue
        inner_predicates = {(relation.get('inner_predicate_reading_id'), wire(relation.get('inner_predicate_span')))
                            for relation in analysis.get('relations', [])
                            if relation.get('kind') == 'relative_clause'}
        for relation in analysis.get('relations', []):
            bindings = _direct_bindings(proof, analysis, claim, relation, document) if linked else [None]
            if not bindings:
                continue
            head_id, dependent_id = relation.get('head_reading_id'), relation.get('dependent_reading_id')
            head_span, dependent_span = relation.get('head_span'), relation.get('dependent_span')
            if (relation.get('kind') != 'predicate_agreement' or relation.get('status') != 'confirmed'
                    or relation.get('regime_licensed') is not True
                    or (dependent_id, wire(dependent_span)) in inner_predicates
                    or relation.get('predicate_lemma') != claim['predicate']
                    or any(relation.get('axes', {}).get(axis) != 'confirmed' for axis in required)
                    or any(relation.get(profile, {}).get(axis) != value
                           for profile in ('subject_profile', 'predicate_profile') for axis, value in required.items())
                    or head_id not in analysis['reading_ids'] or dependent_id not in analysis['reading_ids']
                    or head_id not in rows or dependent_id not in rows
                    or type(head_span) is not dict or type(dependent_span) is not dict
                    or _span(head_span) not in ranges[head_id] or _span(dependent_span) not in ranges[dependent_id]):
                continue
            head, dependent = rows[head_id], rows[dependent_id]
            features = dependent.get('lexical_features', {})
            predicate_role, subject_role = relation.get('predicate_role'), relation.get('subject_role')
            if (dependent.get('kind') != 'noun' or features.get('pos') != 'ADJ'
                    or features.get('lemma') != claim['predicate']
                    or any(_feature(dependent, axis) != value for axis, value in required.items())
                    or predicate_role not in pairs or pairs[predicate_role] != subject_role):
                continue
            heads = [assignment for assignment in analysis['assignments']
                     if assignment['reading_id'] == head_id and assignment['role'] == subject_role
                     and assignment['span'] == head_span]
            dependents = [assignment for assignment in analysis['assignments']
                          if assignment['reading_id'] == dependent_id and assignment['role'] == predicate_role
                          and assignment['span'] == dependent_span]
            if not any(head.get('activated') is True and dependent.get('activated') is True
                       and (dependent.get('head_span') == head['span'] if predicate_role == 'nominal_predicate'
                            else dependent.get('head_span') is not None
                            and dependent.get('head_span') == head.get('head_span'))
                       for head in heads for dependent in dependents):
                continue
            for reference in analysis['references']:
                if (reference.get('status') != 'RESOLVED' or reference.get('bound_entity_id') != entity_id
                        or reference.get('span') != head_span
                        or reference.get('reference_id') not in relation.get('subject_reference_ids', [])
                        or reference.get('context_sha256') != document['context']['sha256']
                        or not _subject_profile_supported(head, relation, reference, required,
                                                          document['context']['sha256'])):
                    continue
                for binding in bindings:
                    if binding is not None and reference['reference_id'] not in binding['subject_reference_ids']:
                        continue
                    witness = {'clause_id': proof['clause_id'], 'analysis_id': proof['analysis_id'],
                               'head_reading_id': head_id, 'dependent_reading_id': dependent_id,
                               'reference_id': reference['reference_id']}
                    if binding is not None:
                        witness['predication_binding_id'] = binding['binding_id']
                    if witness not in witnesses:
                        witnesses.append(witness)
    return witnesses


def typed_question_claim_supported(claim, analysis, rows):
    """Bind a typed query slot to its own pending interrogative ADJ edge."""
    if (claim['predicate_kind'] != 'property' or claim['voice'] is not None or len(claim['args']) != 1
            or not constrained_person_argument(claim['args'][0])
            or analysis.get('force') != 'QUESTION' or analysis.get('assertion_allowed') is not False):
        return False
    argument = claim['args'][0]
    required = {axis: argument[axis] for axis in ('gender', 'number')}
    for subject in analysis['assignments']:
        if subject['role'] != 'nominal_subject':
            continue
        head = rows[subject['reading_id']]
        if (head.get('lexical_features', {}).get('pos') != 'INTG'
                or head.get('support_records') != [{'kind': 'grammar', 'rule': 'wh_subject'}]):
            continue
        references = [reference for reference in analysis['references'] if reference['span'] == subject['span']]
        if (len(references) != 1 or references[0].get('origin') != 'question_variable'
                or references[0].get('status') != 'VARIABLE'
                or references[0].get('bound_entity_id') != argument['name']):
            continue
        for predicate in analysis['assignments']:
            if predicate['role'] != 'nominal_predicate' or predicate.get('head_span') != subject['span']:
                continue
            dependent = rows[predicate['reading_id']]
            if (dependent.get('lexical_features', {}).get('pos') != 'ADJ'
                    or dependent.get('lexical_features', {}).get('lemma') != claim['predicate']
                    or any(_feature(dependent, axis) != value for axis, value in required.items())):
                continue
            for relation in analysis.get('relations', []):
                if (relation.get('kind') == 'predicate_agreement'
                        and relation.get('status') == 'pending_substitution'
                        and relation.get('regime_licensed') is False
                        and relation.get('question_variable') == argument['name']
                        and relation.get('predicate_lemma') == claim['predicate']
                        and relation.get('head_reading_id') == subject['reading_id']
                        and relation.get('dependent_reading_id') == predicate['reading_id']
                        and relation.get('head_span') == subject['span']
                        and relation.get('dependent_span') == predicate['span']
                        and relation.get('subject_role') == subject['role']
                        and relation.get('predicate_role') == predicate['role']
                        and relation.get('subject_reference_ids') == [references[0].get('reference_id')]
                        and all(relation.get('predicate_profile', {}).get(axis) == value for axis, value in required.items())
                        and all(relation.get('subject_profile', {}).get(axis) in (None, 'unknown')
                                for axis in ('gender', 'number'))):
                    return True
    return False


def _query_variables(query, kind):
    require(kind in VARIABLES, 'Question interpretation has an unknown kind')
    variables = set()
    for field in ('args', 'time', 'place'):
        for value in query[field]:
            if constrained_person_argument(value):
                require(field == 'args', 'Typed question variable escaped its argument field')
                variables.add(value['name'])
            elif type(value) is str and value.startswith('?'):
                variables.add(value)
    require(variables == VARIABLES[kind], 'Question kind and variable domain disagree')


def _match(query, claim, entities, *, opposite):
    """Unify declared top-level variable slots, preserving all qualifications."""
    bindings = {}
    for field in CLAIM_FIELDS:
        if field == 'positive':
            if claim[field] is not (not query[field] if opposite else query[field]):
                return None
        elif field not in ('args', 'time', 'place'):
            if wire(query[field]) != wire(claim[field]):
                return None
        else:
            if len(query[field]) != len(claim[field]):
                return None
            for pattern, value in zip(query[field], claim[field]):
                typed = constrained_person_argument(pattern)
                variable = pattern['name'] if typed else pattern if type(pattern) is str and pattern.startswith('?') else None
                if variable is None:
                    if wire(pattern) != wire(value):
                        return None
                    continue
                if variable in ('?person', '?place'):
                    entity = entities.get(value, {}) if type(value) is str else {}
                    if entity.get('kind') != variable[1:]:
                        return None
                    if typed and any(entity.get(axis) != pattern[axis] for axis in ('gender', 'number')):
                        return None
                if variable in bindings and wire(bindings[variable]) != wire(value):
                    return None
                bindings[variable] = deepcopy(value)
    return bindings


def _proof(query, bindings, claim, document, inquiry, analysis_id):
    proof = {'claim_id': claim['claim_id'], 'document_report_id': document['report_id'],
             'question_report_id': inquiry['report_id'], 'question_analysis_id': analysis_id,
             'bindings': deepcopy(bindings), 'source_proofs': deepcopy(claim['proofs']), 'rule': PROOF_RULE}
    receipts = []
    for index, argument in enumerate(query['args']):
        if not constrained_person_argument(argument):
            continue
        required = {axis: argument[axis] for axis in ('gender', 'number')}
        entity_id = bindings[argument['name']]
        witnesses = source_agreement_witnesses(claim, required, entity_id, document)
        if not witnesses:
            return None
        receipts.append({'argument_index': index, 'variable': argument['name'], 'entity_id': entity_id,
                         'required_profile': required, 'context_sha256': document['context']['sha256'],
                         'source_witnesses': witnesses})
    if receipts:
        proof['predicate_agreement_bindings'] = receipts
    return proof


def _result(clause, analysis, query, document, inquiry, entities):
    kind = analysis.get('question_kind') or 'polar'
    _query_variables(query, kind)
    result = {'clause_id': clause['clause_id'], 'analysis_id': analysis['analysis_id'],
              'kind': kind, 'query': query, 'status': 'DEFER',
              'bindings': [], 'proofs': [], 'counterproofs': []}
    if _linked_contract(document):
        result['missing_premises'] = []
    if document['status'] != 'LICENSED_DISCOURSE':
        return result
    for claim in document['claims']:
        for sign in ('proofs', 'counterproofs'):
            bindings = _match(query, claim, entities, opposite=sign == 'counterproofs')
            if bindings is not None:
                proof = _proof(query, bindings, claim, document, inquiry, analysis['analysis_id'])
                if proof is not None:
                    result[sign].append(proof)
                elif 'missing_premises' in result:
                    result['missing_premises'] = ['CLAIM_PREDICATION_AGREEMENT_WITNESS_REQUIRED']
    if kind == 'polar':
        positive, negative = bool(result['proofs']), bool(result['counterproofs'])
        result['status'] = ('CONFLICT' if positive and negative else 'SUPPORTED' if positive
                            else 'REFUTED' if negative else 'UNKNOWN')
    else:
        groups = {}
        for proof in result['proofs']:
            key = wire(proof['bindings'])
            groups.setdefault(key, {'values': deepcopy(proof['bindings']),
                                    'proofs': [], 'counterproofs': []})['proofs'].append(proof)
        for proof in result['counterproofs']:
            key = wire(proof['bindings'])
            if key in groups:
                groups[key]['counterproofs'].append(proof)
        for group in groups.values():
            group['status'] = 'CONFLICT' if group['counterproofs'] else 'SUPPORTED'
            result['bindings'].append(group)
        result['status'] = ('CONFLICT' if any(group['status'] == 'CONFLICT' for group in groups.values())
                            else 'SUPPORTED' if groups else 'UNKNOWN')
    return result


def _evidence_equal(actual, expected):
    # Source-witness order is not semantic, but omission or duplication is.
    def normalized(proof):
        result = deepcopy(proof)
        for receipt in result.get('predicate_agreement_bindings', []):
            receipt['source_witnesses'] = sorted(receipt['source_witnesses'], key=wire)
        return wire(result)
    return (type(actual) is list and Counter(map(normalized, actual)) == Counter(map(normalized, expected)))


def _check_payload(actual, expected, label):
    require(actual.get('status') == expected['status'], label + ' status differs from all source matches')
    if 'missing_premises' in expected:
        require(actual.get('missing_premises') == expected['missing_premises'],
                label + ' omitted or changed a missing predication agreement witness')
    for sign in ('proofs', 'counterproofs'):
        require(_evidence_equal(actual.get(sign), expected[sign]),
                label + ' omitted, duplicated, or changed complete ' + sign + '/agreement receipts')
    bindings = actual.get('bindings')
    require(type(bindings) is list and all(type(binding) is dict and set(binding) == {
        'values', 'status', 'proofs', 'counterproofs'} for binding in bindings),
        label + ' has malformed binding groups')
    by_value = {wire(binding['values']): binding for binding in bindings}
    expected_groups = {wire(binding['values']): binding for binding in expected['bindings']}
    require(len(by_value) == len(bindings) and set(by_value) == set(expected_groups),
            label + ' omitted, duplicated, or invented binding groups')
    for value, expected_binding in expected_groups.items():
        actual_binding = by_value[value]
        require(actual_binding['status'] == expected_binding['status'], label + ' changed a binding status')
        for sign in ('proofs', 'counterproofs'):
            require(_evidence_equal(actual_binding[sign], expected_binding[sign]),
                    label + ' changed a complete binding proof group')


def _outcome_key(result):
    # Receipt syntax may depend on the interpretation; the backed claim and
    # substitution must still agree, including counterproofs with no positive
    # binding. Equal top-level statuses alone are not an agreement criterion.
    return wire({'kind': result['kind'], 'status': result['status'],
                 'bindings': sorted(({'values': binding['values'], 'status': binding['status']}
                                     for binding in result['bindings']), key=wire),
                 **{sign: sorted(({'bindings': proof['bindings'], 'claim_id': proof['claim_id']}
                                  for proof in result[sign]), key=wire)
                    for sign in ('proofs', 'counterproofs')}})


def _nominal_targets(document, used_claims):
    """Locate selected nominal occurrences in separately validated reports.

    This checks graph/claim attachment independently of the runtime consumer.
    It does not re-parse the Arabic source or authenticate descriptive premises.
    Source replay remains a prerequisite of the enclosing evaluation.
    """
    rows, ranges = _reading_rows(document)
    analyses = {(clause['clause_id'], analysis['analysis_id']): analysis
                for clause in document['clauses'] if clause['status'] == 'LICENSED'
                for analysis in clause['analyses']}
    pairs = {'nominal_predicate': 'nominal_subject', 'inna_predicate': 'inna_subject',
             'kana_predicate': 'kana_subject', 'zanna_object2': 'zanna_object1'}
    targets = {}
    for claim in document['claims']:
        if claim['claim_id'] not in used_claims:
            continue
        for proof in claim['proofs']:
            analysis = analyses.get((proof['clause_id'], proof['analysis_id']))
            require(analysis is not None and analysis['licensed_syntax'] is True
                    and analysis['references_complete'] is True and analysis['assertion_allowed'] is True
                    and analysis['rejected_candidate'] is False and analysis['force'] == 'ASSERT',
                    'Nominal explanation has no complete asserted owner analysis')
            index, ids = proof.get('claim_index'), proof.get('predication_binding_ids')
            require(type(index) is int and 0 <= index < len(analysis['claims'])
                    and semantic_key(analysis['claims'][index]) == semantic_key(claim)
                    and type(ids) is list and all(type(value) is str for value in ids)
                    and len(ids) == len(set(ids)), 'Nominal explanation owner claim selector changed')
            owner = analysis['claims'][index]
            for binding in analysis.get('claim_bindings', []):
                if binding.get('binding_id') not in ids or binding.get('claim_index') != index:
                    continue
                require(type(binding.get('claim_index')) is int
                        and binding.get('schema') == 'nabt.claim-predication-binding.v1'
                        and binding.get('force') == 'ASSERT'
                        and all(binding.get(field) == document[field]
                                for field in ('source_id', 'source_sha256', 'scope'))
                        and binding.get('owner_claim_key') == sha256(wire(owner)).hexdigest()
                        and binding.get('binding_id') == sha256(wire({key: value for key, value in binding.items()
                                                                    if key != 'binding_id'})).hexdigest(),
                        'Nominal explanation binding changed its source, owner or identity')
                selected, path = owner, binding.get('claim_path')
                require(type(path) is list, 'Nominal explanation claim path is not a list')
                if path:
                    require(owner['predicate_kind'] == 'scoped' and len(path) == 4
                            and path[0] == 'restriction' and path[2] == 'embedded'
                            and type(path[1]) is int and type(path[3]) is int
                            and 0 <= path[1] < len(owner['restriction']),
                            'Nominal explanation escaped its owner operator scope')
                    scope = owner['restriction'][path[1]]
                    require(type(scope) is dict and scope.get('kind') == 'operator_scope'
                            and type(scope.get('embedded')) is list and 0 <= path[3] < len(scope['embedded']),
                            'Nominal explanation has no retained embedded proposition')
                    selected = scope['embedded'][path[3]]
                if selected['predicate_kind'] != 'property':
                    continue
                require(binding.get('claim_key') == sha256(wire(selected)).hexdigest(),
                        'Nominal explanation changed its qualified predicate claim')
                head_id, predicate_id = binding.get('subject_reading_id'), binding.get('predicate_reading_id')
                require(head_id in rows and predicate_id in rows
                        and head_id in analysis['reading_ids'] and predicate_id in analysis['reading_ids']
                        and _span(binding['subject_span']) in ranges[head_id]
                        and _span(binding['predicate_span']) in ranges[predicate_id],
                        'Nominal explanation is detached from its selected source occurrences')
                reading = rows[predicate_id]
                require(reading.get('kind') == 'noun'
                        and reading.get('lexical_features', {}).get('lemma') == selected['predicate'],
                        'Nominal explanation borrowed a different predicate reading')
                subject_role, predicate_role = binding['subject_role'], binding['predicate_role']
                require(predicate_role in pairs and pairs[predicate_role] == subject_role,
                        'Nominal explanation changed its predication roles')
                heads = [a for a in analysis['assignments'] if a['reading_id'] == head_id
                         and a['span'] == binding['subject_span'] and a['role'] == subject_role
                         and a.get('activated') is True and a.get('compatible') is True]
                predicates = [a for a in analysis['assignments'] if a['reading_id'] == predicate_id
                              and a['span'] == binding['predicate_span'] and a['role'] == predicate_role
                              and a.get('activated') is True and a.get('compatible') is True]
                require(any((p.get('head_span') == h['span'] if predicate_role == 'nominal_predicate'
                             else p.get('head_span') is not None and p['head_span'] == h.get('head_span'))
                            for h in heads for p in predicates),
                        'Nominal explanation lost its activated predication edge')
                ref_ids = binding.get('subject_reference_ids')
                require(type(ref_ids) is list and len(ref_ids) == 1 and type(ref_ids[0]) is str
                        and any(r.get('reference_id') == ref_ids[0] and r.get('status') == 'RESOLVED'
                                and r.get('span') == binding['subject_span']
                                and r.get('context_sha256') == document['context']['sha256']
                                and selected['args'] == [r.get('bound_entity_id')]
                                for r in analysis['references']),
                        'Nominal explanation changed its predicate subject reference')
                key = (claim['claim_id'], proof['clause_id'], proof['analysis_id'], binding['binding_id'])
                require(key not in targets, 'Nominal explanation source binding is duplicated')
                targets[key] = (binding, selected, reading)
    return targets


def _validate_nominal_projections(answer, document, expected):
    """Check complete explanation projections, then bind their IDs to proofs.

    Descriptive candidates and corpus features remain separate axes. This is
    preservation of replayed evidence, not acquisition of a corpus sense link.
    """
    require('nominal_morphology' in document and 'nominal_description_source' in answer
            and type(answer.get('predicate_interpretations')) is list,
            'Current answer omitted its nominal interpretation contract')
    morphology = document['nominal_morphology']
    lexical = None if morphology is None else morphology.get('lexical_source')
    require(wire(answer['nominal_description_source']) == wire(lexical),
            'Nominal interpretation changed its descriptive source')
    if morphology is not None:
        require(all(morphology.get(field) == document[field]
                    for field in ('source_id', 'source_sha256', 'scope'))
                and morphology.get('raw_text') == document['source_text']
                and type(lexical) is dict and lexical.get('scope') == document['scope']
                and type(lexical.get('raw_text')) is str
                and lexical.get('sha256') == sha256(lexical['raw_text'].encode()).hexdigest(),
                'Nominal interpretation morphology belongs to another source or scope')
    used = {proof['claim_id'] for result in expected for sign in ('proofs', 'counterproofs')
            for proof in result[sign]}
    targets = _nominal_targets(document, used)
    actual, by_key = answer['predicate_interpretations'], {}
    fields = {'schema', 'clause_id', 'analysis_id', 'predication_binding_id', 'owner_claim_id',
              'claim_path', 'predicate_claim', 'assertion_scope', 'predicate_reading_id',
              'predicate_span', 'predicate', 'source_lexical_id', 'grammatical_kind',
              'grammatical_profile', 'derivation', 'nominal_denotation', 'world_truth', 'interpretation_id'}
    for row in actual:
        require(type(row) is dict and set(row) == fields
                and all(type(row[field]) is str for field in ('clause_id', 'analysis_id',
                    'predication_binding_id', 'owner_claim_id', 'interpretation_id')),
                'Malformed nominal predicate interpretation')
        key = (row['owner_claim_id'], row['clause_id'], row['analysis_id'], row['predication_binding_id'])
        require(key in targets and key not in by_key, 'Nominal interpretation added, duplicated or borrowed a binding')
        binding, selected, reading = targets[key]
        features = reading['lexical_features']
        require(row['schema'] == 'nabt.nominal-predicate-interpretation.v1'
                and row['world_truth'] == 'NOT_ESTABLISHED'
                and row['predicate_reading_id'] == reading['reading_id']
                and wire(row['predicate_span']) == wire(binding['predicate_span'])
                and wire(row['claim_path']) == wire(binding['claim_path'])
                and wire(row['predicate_claim']) == wire(selected)
                and row['predicate'] == selected['predicate']
                and row['assertion_scope'] == ('EMBEDDED_IN_OWNER_CLAIM_NOT_ASSERTED_SEPARATELY'
                                               if binding['claim_path'] else 'ASSERTED_SOURCE_CLAIM')
                and row['grammatical_kind'] == reading['kind']
                and wire(row['grammatical_profile']) == wire({k: features.get(k) for k in ('gender', 'number', 'person')})
                and row['source_lexical_id'] == (reading.get('identity', {}).get('lexical_id') or
                                               reading.get('person_evidence', {}).get('source_lexical_id')),
                'Nominal interpretation changed its selected meaning, source reading or scope')
        tags = features.get('nominal_derivation_features') or []
        require(wire(row['derivation']) == wire({
            'status': 'SOURCE_QUALIFIED' if tags else 'DEFER', 'features': tags,
            'support_records': reading['support_records'],
            'missing': [] if tags else ['NOMINAL_DERIVATION_SOURCE_FEATURES'],
            'authority': 'ANNOTATED_LEXICAL_READING_NOT_WEIGHT_INFERENCE'}),
            'Nominal interpretation changed its source derivation evidence')
        descriptions = [] if morphology is None else [r for occurrence in morphology['occurrences']
            if wire(occurrence['span']) == wire(binding['predicate_span']) for r in occurrence['readings']
            if r['lexical_link'] is not None]
        denotation = row['nominal_denotation']
        require(type(denotation) is dict and set(denotation) == {
            'status', 'alternatives', 'missing', 'sense_equivalence_established', 'authority'}
            and denotation['status'] == ('SOURCE_READING_CANDIDATES' if descriptions else 'DEFER')
            and denotation['sense_equivalence_established'] is False
            and denotation['authority'] == 'EXACT_OCCURRENCE_DESCRIPTIVE_ALTERNATIVES_NOT_CORPUS_SENSE_IDENTITY'
            and denotation['missing'] == (['DESCRIPTIVE_READING_TO_LEXICAL_SENSE_CORRESPONDENCE']
                                         if descriptions else ['LEXICAL_UNIVERSAL_AND_PROPERTY_BEARING_WITNESS'])
            and type(denotation['alternatives']) is list and len(denotation['alternatives']) == len(descriptions),
            'Nominal interpretation collapsed its unresolved descriptive alternatives')
        for candidate, source in zip(denotation['alternatives'], descriptions):
            require(type(candidate) is dict and set(candidate) == {
                'reading_id', 'identity', 'lexical_link', 'kind', 'nominal_semantics', 'premises', 'blockers', 'condition'}
                and all(wire(candidate[k]) == wire(source[k]) for k in ('reading_id', 'identity', 'lexical_link', 'blockers'))
                and all(wire(candidate[k]) == wire(source['axes'][k]) for k in ('kind', 'nominal_semantics'))
                and wire(candidate['premises']) == wire([p for p in source['linked_properties']
                    if p['property'] in ('independent', 'time_in_form', 'universal', 'property_bearing')])
                and candidate['condition'] == 'IF_THIS_DESCRIPTIVE_READING_IS_THE_SELECTED_PREDICATE_SENSE',
                'Nominal interpretation changed a correlated descriptive reading or its premises')
        require(row['interpretation_id'] == sha256(wire({k: v for k, v in row.items()
                                                       if k != 'interpretation_id'})).hexdigest(),
                'Nominal interpretation identity mismatch')
        by_key[key] = row['interpretation_id']
    require(set(by_key) == set(targets) and actual == sorted(actual, key=lambda row: row['interpretation_id']),
            'Nominal interpretation inventory omitted a selected source binding or changed canonical order')
    ids_by_claim = defaultdict(list)
    for key in targets:
        ids_by_claim[key[0]].append(by_key[key])
    for result in expected:
        for sign in ('proofs', 'counterproofs'):
            for proof in result[sign]:
                if ids_by_claim[proof['claim_id']]:
                    proof['predicate_interpretation_ids'] = ids_by_claim[proof['claim_id']]


def validate_interpretations(answer, document, inquiry, inputs, *, claim_view):
    """Validate all subresults and recompute consensus without runtime helpers."""
    supplied = answer.get('question_interpretations')
    linked = _linked_contract(document)
    require((answer.get('schema') == 'nabt.discourse-answer.v3') == linked,
            'Answer and source use different claim-predication contract versions')
    require(type(supplied) is list, 'Question interpretation inventory must be a list')
    claims = document['claims']
    require(len({claim['claim_id'] for claim in claims}) == len(claims), 'Accepted source claim IDs are not unique')
    for claim in claims:
        claim_view(claim)
    entities = {entity['id']: entity for entity in (inputs.get('context') or {}).get('entities', [])}
    source_complete = document['status'] == 'LICENSED_DISCOURSE'
    missing = [] if source_complete else ['COMPLETE_SOURCE_DISCOURSE_READING']
    expected, clauses = [], inquiry['clauses']
    if len(clauses) == 1:
        analyses = clauses[0]['analyses']
        require(all(type(analysis.get('rejected_candidate')) is bool for analysis in analyses),
                'Question rejection markers must be explicit booleans')
        require(len({analysis['analysis_id'] for analysis in analyses}) == len(analyses),
                'Question analysis inventory contains duplicate IDs')
        viable = [analysis for analysis in analyses if analysis['rejected_candidate'] is False]
    else:
        viable = []
    if not viable or any(analysis.get('licensed_syntax') is not True
                         or analysis.get('references_complete') is not True for analysis in viable):
        missing.append('ONE_COMPLETE_QUESTION_READING')
    elif any(analysis.get('force') != 'QUESTION' or type(analysis.get('claims')) is not list
             or len(analysis['claims']) != 1 for analysis in viable):
        missing.append('EXPLICIT_SINGLE_QUESTION_FORCE')
    else:
        for analysis in viable:
            query = claim_view(analysis['claims'][0])
            expected.append(_result(clauses[0], analysis, query, document, inquiry, entities))
    require(len(supplied) == len(expected), 'Question interpretation inventory dropped or added a viable analysis')
    if linked:
        _validate_nominal_projections(answer, document, expected)
    expected_by_id = {(result['clause_id'], result['analysis_id']): result for result in expected}
    actual_ids = []
    for result in supplied:
        require(type(result) is dict and set(result) == {
            'clause_id', 'analysis_id', 'kind', 'query', 'status', 'bindings', 'proofs', 'counterproofs'} |
            ({'missing_premises'} if linked else set()),
            'Malformed question interpretation result')
        key = result['clause_id'], result['analysis_id']
        require(key in expected_by_id and key not in actual_ids,
                'Question interpretation is not a unique viable inquiry analysis')
        actual_ids.append(key)
        original = expected_by_id[key]
        require(result['kind'] == original['kind'] and wire(result['query']) == wire(original['query']),
                'Question interpretation changed its own original inquiry pattern or kind')
        _check_payload(result, original, 'Question interpretation')
    patterns = {wire(result['query']) for result in expected}
    kinds = {result['kind'] for result in expected}
    common_query = expected[0]['query'] if len(patterns) == 1 else None
    common_kind = expected[0]['kind'] if len(kinds) == 1 else None
    require(wire(answer.get('query')) == wire(common_query), 'Top query is not exactly the common interpretation pattern')
    require(answer.get('kind') == common_kind, 'Top kind is not exactly the common interpretation kind')
    top = {'status': 'DEFER', 'proofs': [], 'counterproofs': [], 'bindings': []}
    basis = None
    if expected and source_complete:
        missing.extend(sorted({premise for result in expected for premise in result.get('missing_premises', [])}))
        if len({_outcome_key(result) for result in expected}) != 1:
            missing.append('QUESTION_INTERPRETATION_OUTCOMES_DISAGREE')
        else:
            basis, top['status'] = CONSENSUS_BASIS, expected[0]['status']
            for sign in ('proofs', 'counterproofs'):
                top[sign] = [proof for result in expected for proof in result[sign]]
            for binding in expected[0]['bindings']:
                group = {'values': deepcopy(binding['values']), 'status': binding['status']}
                for sign in ('proofs', 'counterproofs'):
                    group[sign] = [proof for proof in top[sign] if wire(proof['bindings']) == wire(binding['values'])]
                top['bindings'].append(group)
    require(answer.get('answer_basis') == basis, 'Answer basis does not follow complete interpretation consensus')
    actual_missing = answer.get('missing_premises')
    require(type(actual_missing) is list and Counter(actual_missing) == Counter(missing),
            'Answer missing premises do not describe all incomplete/disagreeing interpretations')
    _check_payload(answer, top, 'Top answer')

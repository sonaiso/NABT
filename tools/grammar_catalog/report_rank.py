"""Condition a finite, explicitly hypothetical opening scene on scoped observations."""
from fractions import Fraction
from unicodedata import category, normalize

from . import valency

SCHEMA = 'nabt.report-rank.finite-scene.v1'
ROLES = ('opener', 'opened_entity', 'time', 'place', 'instrument')


def bounded(value, limit=120):
    return type(value) is str and bool(value.strip()) and len(value.encode()) <= limit


def validate(model):
    required = {'event', 'speaker', 'addressee', 'source_id', 'source_sha256', 'worlds', 'witnesses'}
    if type(model) is not dict or set(model) - {'compatibility', 'speaker_history'} != required:
        raise ValueError('Expected an attributed, source-bound finite scene')
    if not all(bounded(model[k]) for k in ('event', 'speaker', 'addressee', 'source_id', 'source_sha256')):
        raise ValueError('Missing scene or source identity')
    for name, fields in [('worlds', {'id', 'text', 'mass'}), ('witnesses', {'id', 'event', 'role', 'value'})]:
        rows = model[name]
        if type(rows) is not list or len(rows) > 32:
            raise ValueError('Expected up to 32 rows per scene table')
        ids = set()
        for row in rows:
            if type(row) is not dict or set(row) != fields or not bounded(row['id']) or row['id'] in ids:
                raise ValueError('Invalid or duplicate scene row')
            ids.add(row['id'])
            if name == 'worlds':
                if not bounded(row['text'], 512) or type(row['mass']) is not int or not 1 <= row['mass'] <= 1000:
                    raise ValueError('Expected an Arabic scene and positive integer prior mass')
            elif not (bounded(row['event']) and bounded(row['role']) and row['role'] in ROLES
                      and bounded(row['value']) and row['value'] == key(row['value'])):
                raise ValueError('Invalid scoped observation')

    if 'speaker_history' in model:
        history = model['speaker_history']
        if type(history) is not dict or set(history) != {'setting', 'audits'} or not bounded(history['setting']):
            raise ValueError('Expected a named reporting setting and past attributed observations')
        rows = history['audits']
        if type(rows) is not list or len(rows) > 128:
            raise ValueError('Invalid number of past observations')
        names = {'event', 'speaker', 'setting', 'masdar', 'source'}
        for row in rows:
            if type(row) is not dict or set(row) != names | {'reported', 'observed'}:
                raise ValueError('Incomplete audit observation')
            if not all(bounded(row[k]) for k in names) or any(type(row[k]) is not bool for k in ('reported', 'observed')):
                raise ValueError('Expected named provenance and two boolean outcomes')

    if 'compatibility' in model:
        contract = model['compatibility']
        if type(contract) is not dict or set(contract) != {'memberships', 'exclusions'}:
            raise ValueError('Expected attributed memberships and exclusions')
        common = {'id', 'source', 'axis', 'type', 'event'}
        ids = {w['id'] for w in model['witnesses']}
        for group, extra in [('memberships', {'entity', 'positive'}), ('exclusions', {'role'})]:
            rows = contract[group]
            if type(rows) is not list or len(rows) > 32:
                raise ValueError('Invalid compatibility table')
            for row in rows:
                if type(row) is not dict or set(row) != common | extra or not all(bounded(row[k]) for k in common):
                    raise ValueError('Incomplete model premise')
                if row['id'] in ids or row['axis'] not in ('genus', 'property', 'attribute', 'disposition'):
                    raise ValueError('Invalid model axis or duplicate premise identity')
                ids.add(row['id'])
                if group == 'memberships':
                    if type(row['positive']) is not bool or not bounded(row['entity']) or row['entity'] != key(row['entity']):
                        raise ValueError('Expected a scoped signed membership')
                elif row['role'] not in ROLES:
                    raise ValueError('Unknown role in exclusion')



def key(surface):
    # Case endings and supplied vocalization are retained in the reading. Only compare
    # these five slots inside the small licensed opening vocabulary after parsing.
    return ''.join(c for c in normalize('NFC', surface) if category(c) != 'Mn')


def bindings(frame):
    if not frame:
        return None
    row = frame['reading']
    if row['force'] != 'REPORTED_MATRIX_EVENT' or row['masdar'] != 'فتح':
        return None
    if any(edge['role'] not in ROLES for edge in row['roles']):
        return None
    return {edge['role']: edge['witness'] for edge in row['roles']}


def compatibility(values, model):
    """A negative role license requires both an applicable exclusion and positive membership."""
    contract = model.get('compatibility', {})
    blocked, conflicts = [], []
    for law in contract.get('exclusions', []):
        if law['event'] != model['event'] or law['role'] not in values:
            continue
        evidence = [row for row in contract['memberships'] if row['entity'] == values[law['role']]
                    and all(row[k] == law[k] for k in ('axis', 'type', 'event'))]
        positive = [row['id'] for row in evidence if row['positive']]
        negative = [row['id'] for row in evidence if not row['positive']]
        if positive:
            trace = {'law': law['id'], 'source': law['source'], 'role': law['role'], 'axis': law['axis'],
                     'type': law['type'], 'supports': positive, 'opposes': negative}
            (conflicts if negative else blocked).append(trace)
    return {'blockers': blocked, 'conflicts': conflicts}


def speaker_likelihood(model, masdar):
    """Estimate P(affirmation | state) from deduplicated past events, within the supplied model."""
    equal = (Fraction(1), Fraction(1))
    history = model.get('speaker_history')
    if history is None:
        return {'status': 'NO_SPEAKER_HISTORY'}, equal
    cases = {}
    for row in history['audits']:
        if ((row['speaker'], row['setting'], row['masdar']) != (model['speaker'], history['setting'], masdar)
                or row['event'] == model['event']):
            continue
        cases.setdefault(row['event'], set()).add((row['reported'], row['observed']))
    conflicts = sorted(event for event, observations in cases.items() if len(observations) > 1)
    audit = {'status': 'SUPPLIED_AUDITS', 'setting': history['setting'], 'events': sorted(cases),
             'conflicting_events': conflicts, 'estimator': 'ADD_ONE_BERNOULLI_PER_TRUE_STATE'}
    if conflicts:
        return {**audit, 'status': 'CONFLICTING_HISTORY_UNUSED'}, equal
    observed = [0, 0]
    affirmed = [0, 0]
    for observations in cases.values():
        reported, truth = next(iter(observations))
        observed[truth] += 1
        affirmed[truth] += int(reported)
    audit.update(observed_false_true=observed, affirmed_false_true=affirmed)
    if 0 in observed:
        return {**audit, 'status': 'INSUFFICIENT_OUTCOME_COVERAGE'}, equal
    yes, no = (Fraction(1 + affirmed[i], 2 + observed[i]) for i in (1, 0))
    return {**audit, 'if_true': [yes.numerator, yes.denominator],
            'if_false': [no.numerator, no.denominator]}, (yes, no)


def assess(frame, model, source_id, source_digest):
    validate(model)
    if (model['source_id'], model['source_sha256']) != (source_id, source_digest):
        raise ValueError('Scene belongs to a different report')
    spans = bindings(frame)
    result = {'schema': SCHEMA, 'source_id': source_id, 'source_sha256': source_digest, 'speaker': model['speaker'],
              'addressee': model['addressee'], 'event': model['event'], 'external_truth': 'UNASSESSED',
              'empirical_cause': 'UNASSESSED', 'empirical_effect': 'UNASSESSED',
              'authority': 'CONDITIONAL_ON_SUPPLIED_FINITE_MODEL'}
    if not spans:
        return {**result, 'status': 'OUTSIDE_OPENING_REPORT_PROFILE'}
    claim = {role: key(span['surface']) for role, span in spans.items()}
    worlds = []
    seen = set()
    columns = None
    for world in model['worlds']:
        parsed = bindings(valency.analyze(world['text'], world['id']))
        if not parsed or not claim.keys() <= parsed.keys() or (columns is not None and columns != parsed.keys()):
            raise ValueError('Scene alternatives must explicitly resolve the same roles and every reported role')
        columns = set(parsed)
        values = {role: key(span['surface']) for role, span in parsed.items()}
        signature = tuple(sorted(values.items()))
        if signature in seen:
            raise ValueError('Repeated alternative: declare its mass once')
        seen.add(signature)
        worlds.append((world['id'], world['mass'], values))
    active = [w for w in model['witnesses'] if w['event'] == model['event']]
    if columns is not None and any(w['role'] not in columns for w in active):
        raise ValueError('An observation references a role missing from the alternative descriptions')
    cuts = {wid: [w['id'] for w in active if values[w['role']] != key(w['value'])]
            for wid, _, values in worlds}
    checks = {wid: compatibility(values, model) for wid, _, values in worlds}
    live = [w for w in worlds if not cuts[w[0]] and not checks[w[0]]['blockers']]
    uncertain = [w[0] for w in live if checks[w[0]]['conflicts']]
    history, (if_true, if_false) = speaker_likelihood(model, frame['reading']['masdar'])
    masses = {wid: weight * (if_true if all(values[r] == val for r, val in claim.items()) else if_false)
              for wid, weight, values in live}

    def grade(target):
        def agrees(world):
            return all(world[2][role] == value for role, value in target.items())
        check = compatibility(target, model)
        if check['blockers']:
            return {'rank': 'IMPOSSIBLE_UNDER_SUPPLIED_RULE', 'fraction': None, **check}
        if check['conflicts'] or uncertain:
            return {'rank': 'CONFLICTING_MEMBERSHIP', 'fraction': None, **check}
        if not worlds or not live:
            return {'rank': 'UNASSESSED', 'fraction': None}
        total = sum(masses.values())
        yes = sum(masses[w[0]] for w in live if agrees(w))
        fraction = Fraction(yes, total)
        if not any(agrees(w) for w in worlds):
            rank = 'ABSENT_FROM_ENUMERATED_MODEL'
        elif yes == 0:
            rank = 'REFUTED_IN_CONDITIONED_SCENE'
        elif yes == total:
            rank = 'CERTAIN_IN_CONDITIONED_SCENE'
        elif 2 * yes == total:
            rank = 'BALANCED'
        else:
            rank = 'PREPONDERANT' if 2 * yes > total else 'DISFAVORED'
        return {'rank': rank, 'fraction': [fraction.numerator, fraction.denominator]}

    status = 'CONTESTED_MODEL' if uncertain else 'ASSESSED' if live else 'NO_COMPATIBLE_ALTERNATIVE' if worlds else 'NO_ALTERNATIVES_SUPPLIED'
    return {**result, 'status': status, 'roles': {r: {'span': spans[r], **grade({r: v})} for r, v in claim.items()},
            'report': grade(claim), 'surviving_worlds': [w[0] for w in live], 'excluded_by': cuts,
            'speaker_calibration': history, 'model_rule_checks': checks, 'worlds_with_contested_membership': uncertain,
            'active_witnesses': [w['id'] for w in active],
            'out_of_scope_witnesses': [w['id'] for w in model['witnesses'] if w['event'] != model['event']]}

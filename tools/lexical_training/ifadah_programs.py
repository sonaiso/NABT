"""Bounded typed utterance programs over existing governor readings.

Exact bindings and authored grammar remain separate from learned operator heads.
No score is a license, no source assertion is a world fact, no A116 claim is made
for an unlicensed Unicode projection. All external calls use cognitive.lesson.
"""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from tools import evidence_lifecycle_v1 as wire
from tools.grammar_catalog import awamil_occurrence as awamil, classical_roles
from tools.grammar_catalog.source_evidence_view import pinned_excerpts
from tools.grammar_catalog.licensed_speech import under_question
from tools.grammar_catalog.operations import exact_terms
from . import shared_encoder as shared

SCHEMA = 'ntl.ifadah-program-lesson.v1'
RESULT = 'ntl.ifadah-program-result.v1'
LAW = 'nabt.authored-ifadah-program.v1'
DIRECTORY = shared.ROOT / 'evidence/ifadah_programs_v1'
MODEL = Path(__file__).with_name('data') / 'ifadah_programs_v1.json'
FORCES = ('assert', 'ask', 'wish', 'hope')
FRAMES = ('plain', 'emphasis', 'past', 'negation')
PROGRAMS = {'plain': ('assert', 'plain'), 'emphasis': ('assert', 'emphasis'),
            'past': ('assert', 'past'), 'negation': ('assert', 'negation'),
            'wish': ('wish', 'plain'), 'hope': ('hope', 'plain'), 'ask': ('ask', 'plain'),
            'ask_past': ('ask', 'past'), 'ask_negation': ('ask', 'negation')}
FACTORS = {18: 'emphasis', 22: 'wish', 23: 'hope', 64: 'past', 76: 'negation', 99: 'plain'}
WIDTH = 16 * shared.HIDDEN + 1  # first two, mean, max of 4H token vectors; bias
OPEN = ('GENERAL_RELATION_ACQUISITION_OPEN', 'GENERAL_CONTEXT_ACQUISITION_OPEN',
        'GENERAL_IFADAH_ACQUISITION_OPEN', 'GENUS_AND_CAPABILITY_BINDING_NOT_TRAINED',
        'INDEPENDENT_LINGUISTIC_REVIEW_OPEN', 'PYTHON_LEAN_REFINEMENT_OPEN')


def identity(path):
    return sha256(path.read_bytes()).hexdigest()


def dataset():
    data = json.loads((DIRECTORY / 'data.json').read_bytes())
    if data['slot_sha256'] != identity(awamil.DATA / 'awamil_occurrence_bank_v1.json'):
        raise ValueError('Unbound lexical slot inventory')
    return data


def validate(request):
    wire._encoded(request, 8192)
    if type(request) is not dict or request.get('schema') != SCHEMA:
        raise ValueError('Unknown ifadah lesson schema')
    mode = request.get('mode')
    required = {'schema', 'mode', 'source_id', 'text'} if mode == 'understand' else {
        'schema', 'mode', 'source_id', 'instruction', 'subject', 'predicate'}
    wire._fields(request, required, 'ifadah lesson')
    if mode not in ('understand', 'produce'):
        raise ValueError('Unknown ifadah mode')
    wire._text(request['source_id'], 'source_id', 128)
    text = request['text'] if mode == 'understand' else request['instruction']
    if type(text) is not str or not text.strip() or len(text.encode()) > 256:
        raise ValueError('Expected nonempty source within 256 UTF-8 bytes')
    if mode == 'produce':
        for field in ('subject', 'predicate'):
            if type(request[field]) is not int or not 0 <= request[field] < 6:
                raise ValueError('Unknown fixed lexical slot identity')
    return deepcopy(request)


def program(name, subject, predicate):
    if name not in PROGRAMS or any(type(v) is not int or not 0 <= v < 6 for v in (subject, predicate)):
        raise ValueError('Program outside typed finite domain')
    force, frame = PROGRAMS[name]
    node = {'op': 'predication', 'subject': subject, 'predicate': predicate}
    if frame != 'plain':
        node = {'op': frame, 'body': node}
    if force != 'assert':
        node = {'op': force, 'body': node}
    return node


def program_name(tree):
    # Equality of complete typed trees; do not erase ordering or arbitrary nodes.
    node, depth = tree, 0
    while type(node) is dict and node.get('op') != 'predication' and depth < 4:
        if set(node) != {'op', 'body'} or type(node['op']) is not str:
            raise ValueError('Invalid operator node')
        node, depth = node['body'], depth + 1
    if (type(node) is not dict or set(node) != {'op', 'subject', 'predicate'}
            or node.get('op') != 'predication'
            or any(type(node[k]) is not int or not 0 <= node[k] < 6 for k in ('subject', 'predicate'))):
        raise ValueError('Invalid predication leaves')
    for name in PROGRAMS:
        for i in range(6):
            for j in range(6):
                if tree == program(name, i, j):
                    return name, i, j
    raise ValueError('Unsupported operator order or fields')


def realize(tree):
    name, subject, predicate = program_name(tree)
    force, frame = PROGRAMS[name]
    bank, _ = awamil.curriculum()
    s = bank['slots']['person_a' if name in ('emphasis', 'wish', 'hope') else 'person_u'][subject]
    p = bank['slots']['adj_a' if frame in ('past', 'negation') else 'adj_u'][predicate]
    cue = {'emphasis': 'إِنَّ', 'wish': 'لَيْتَ', 'hope': 'لَعَلَّ',
           'past': 'كَانَ', 'negation': 'لَيْسَ'}.get(name if force in ('wish', 'hope') else frame)
    text = ' '.join(x for x in (cue, s, p) if x)
    return 'هَلْ ' + text + '؟' if force == 'ask' else text


def understand(text, source_id):
    """All supported readings, each with the original complete owner record."""
    wrapper = under_question(text)
    body, offset = (wrapper[0], wrapper[1]) if wrapper else (text, 0)
    rows, owner_status = awamil.read(body)
    question_source = pinned_excerpts(classical_roles.inventory(), ['question']) if wrapper else {}
    readings = []
    bank, _ = awamil.curriculum()
    for row in rows:
        name = FACTORS.get(row['factor'])
        if name is None or (wrapper and name not in ('plain', 'past', 'negation')):
            continue
        if wrapper:
            name = {'plain': 'ask', 'past': 'ask_past', 'negation': 'ask_negation'}[name]
        # Identity comes from exact owner-attested forms, not a neural gender/kind guess.
        bindings = deepcopy(row['bindings'])
        for token in bindings.values():
            a, b = token['utf8_span']
            token['utf8_span'] = [a + offset, b + offset]
            if text.encode()[a + offset:b + offset].decode() != token['surface']:
                raise ValueError('Detached role witness')
            token['codepoint_span'] = [len(text.encode()[:v].decode()) for v in token['utf8_span']]
            token['source_id'] = source_id
            token['source_sha256'] = sha256(text.encode()).hexdigest()
        subject_form = bindings['subject']['surface']
        predicate_form = bindings['predicate']['surface']
        s = next(i for i in range(6) if subject_form in
                 (bank['slots']['person_u'][i], bank['slots']['person_a'][i]))
        p = next(i for i in range(6) if predicate_form in
                 (bank['slots']['adj_u'][i], bank['slots']['adj_a'][i]))
        force, frame = PROGRAMS[name]
        readings.append({'program': program(name, s, p), 'name': name, 'bindings': bindings,
                         'force': force, 'frame': frame, 'owner': row,
                         'outer_question_cue': {'utf8_span': wrapper[2], 'surface': text.encode()[slice(*wrapper[2])].decode(), 'witnesses': question_source}
                         if wrapper else None,
                         'source_commitment': force == 'assert', 'world_truth_established': False,
                         'obligations': ['SPEAKER_AND_REFERENCE_CONTEXT_NOT_GROUNDED',
                                         'GENUS_PROPERTIES_AND_INDIVIDUAL_CAPABILITY_NOT_ESTABLISHED']})
    return {'status': 'SCOPED_READINGS' if readings else 'OUTSIDE_FRAGMENT',
            'owner_status': owner_status, 'readings': readings,
            'scope': 'AUTHORED_FULL_PATTERN_AND_LEXICAL_FACE', 'native_checked': False}


@lru_cache(maxsize=1024)
def token_vector(encoder_bytes, token):
    encoder = shared.validate_model(json.loads(encoder_bytes))
    ids = [b + 1 for b in token.encode()]
    forward = shared.states_for_ids(encoder, ids)[-1]
    reverse = shared.states_for_ids(encoder, list(reversed(ids)))[-1]
    return [0.] * shared.HIDDEN + forward + reverse + [0.] * shared.HIDDEN


def features(encoder_bytes, text):
    terms = exact_terms(text)
    if not 1 <= len(terms) <= 20 or len(text.encode()) > 256:
        raise ValueError('Feature budget or no written terms')
    vectors = [token_vector(encoder_bytes, t['surface']) for t in terms]
    mean = [sum(col) / len(vectors) for col in zip(*vectors, strict=True)]
    maximum = [max(col) for col in zip(*vectors, strict=True)]
    return vectors[0] + (vectors[1] if len(vectors) > 1 else [0.] * (4 * shared.HIDDEN)) + mean + maximum + [1.]


def load_model():
    if MODEL.stat().st_size > 3_000_000:
        raise ValueError('Model size limit')
    raw = MODEL.read_bytes()
    model = wire.strict_loads(raw, maximum_bytes=3_000_000, report=True)
    if (type(model) is not dict or model.get('schema') != 'ntl.ifadah-heads.v2' or model.get('authority') != 'NONE'
            or model.get('encoder_sha256') != identity(shared.MODEL)
            or model.get('data_sha256') != identity(DIRECTORY / 'data.json')
            or model.get('protocol_sha256') != identity(DIRECTORY / 'protocol.json')
            or model.get('local_protocol_sha256') != identity(DIRECTORY / 'protocol_local.json')):
        raise ValueError('Unbound ifadah model')
    if set(model.get('heads', {})) != {'understand', 'produce'}:
        raise ValueError('Unknown model modes')
    for mode in model['heads'].values():
        if type(mode) is not dict or set(mode) != {'force', 'frame'}:
            raise ValueError('Unknown program heads')
        for key, labels in (('force', FORCES), ('frame', FRAMES)):
            if not shared._shape(mode[key], (len(labels), WIDTH)):
                raise ValueError('Invalid finite readout tensors')
    if set(model.get('local_heads', {})) != {'understand', 'produce'}:
        raise ValueError('Unknown local head modes')
    for heads in model['local_heads'].values():
        if type(heads) is not dict or set(heads) != {'force', 'frame'} or any(
                not shared._shape(heads[key], (4, 4 * shared.HIDDEN + 1)) for key in ('force', 'frame')):
            raise ValueError('Invalid local readout tensors')
    return model, sha256(raw).hexdigest()


def predict(heads, x):
    values = {}
    for key, labels in (('force', FORCES), ('frame', FRAMES)):
        scores = [sum(a * b for a, b in zip(row, x, strict=True)) for row in heads[key]]
        values[key] = labels[max(range(len(labels)), key=lambda i: scores[i])]
    name = next((k for k, v in PROGRAMS.items() if v == (values['force'], values['frame'])), None)
    return {**values, 'name': name}


def local_predict(heads, encoder_bytes, text):
    """Learn cues locally, then compose only the declared typed scope orders.

    No runtime lookup of Arabic operator spellings or test labels. Conflicting
    local labels abstain; absence of a cue is the plain/assert default in this
    deliberately finite law, not a general absence-of-evidence inference.
    """
    terms = exact_terms(text)
    if not 1 <= len(terms) <= 20 or len(text.encode()) > 256:
        raise ValueError('Local feature budget')
    decisions = {}
    cues = []
    for key, labels in (('force', FORCES), ('frame', FRAMES)):
        found = set()
        for term in terms:
            x = token_vector(encoder_bytes, term['surface']) + [1.]
            scores = [sum(a*b for a,b in zip(w,x,strict=True)) for w in heads[key]]
            best = max(range(4), key=lambda i: scores[i])
            if best != 0:
                found.add(labels[best])
                cues.append({'head': key, 'label': labels[best],
                             'surface': term['surface'], 'utf8_span': term['utf8_span']})
        decisions[key] = next(iter(found)) if len(found) == 1 else labels[0] if not found else 'CONFLICT'
    # Emit selected operators in observed order; never commute ask and negation.
    ordered = sorted(cues, key=lambda c: (c['utf8_span'][0], c['head']))
    sequence = [c['label'] for c in ordered]
    def operations(tree):
        return [] if tree['op'] == 'predication' else [tree['op']] + operations(tree['body'])
    name = next((n for n in PROGRAMS if operations(program(n, 0, 0)) == sequence), None)
    if 'CONFLICT' in decisions.values():
        name = None
    return {**decisions, 'name': name, 'operator_sequence': sequence, 'local_cues': ordered}


def propose(mode, text):
    try:
        model, digest = load_model()
        prediction = local_predict(model['local_heads'][mode], shared.MODEL.read_bytes(), text)
        return {'status': 'PROPOSED', 'authority': 'NONE', 'model_sha256': digest,
                'encoder_sha256': model['encoder_sha256'], **prediction}
    except (OSError, ValueError, KeyError) as exc:
        return {'status': 'MODEL_UNAVAILABLE', 'authority': 'NONE', 'reason': type(exc).__name__}


def run(request):
    r = validate(request)
    text = r['text'] if r['mode'] == 'understand' else r['instruction']
    proposal = propose(r['mode'], text)
    result = {'schema': RESULT, 'law': LAW, 'source_id': r['source_id'],
              'source_text': text, 'source_sha256': sha256(text.encode()).hexdigest(),
              'execution_measured': True, 'measured_scope': 'PYTHON_AUTHORED_PROGRAM_AND_READOUT', 'request': r, 'neural_proposal': proposal,
              'world_truth_established': False, 'empirical_causality_established': False,
              'grammar_certified': False, 'native_checked': False, 'open_obligations': list(OPEN),
              'binding_authority': 'EXACT_EXISTING_SLOT_FORMS_NOT_NEURAL',
              'status': 'DEFER', 'accepted_program': None}
    if r['mode'] == 'understand':
        try:
            owner = understand(text, r['source_id'])
        except (OSError, ValueError) as exc:
            result.update(status='EVIDENCE_UNAVAILABLE', execution_measured=False, evidence_failure=type(exc).__name__)
            return result
        result['owner'] = owner  # Keep alternatives even when the proposal fails.
        matching = [a for a in owner['readings'] if a['name'] == proposal.get('name')]
        if matching:
            result.update(status='CHECKED_IN_AUTHORED_FRAGMENT', accepted_program=matching[0]['program'])
        result['proposal_agrees_with_owner'] = bool(matching)
    elif proposal.get('name') is not None:
        tree = program(proposal['name'], r['subject'], r['predicate'])
        generated = realize(tree)
        try:
            owner = understand(generated, r['source_id'] + ':realization')
        except (OSError, ValueError) as exc:
            result.update(status='EVIDENCE_UNAVAILABLE', execution_measured=False, evidence_failure=type(exc).__name__)
            return result
        checks = [a for a in owner['readings'] if a['program'] == tree]
        result.update(generated_text=generated, intended_program=tree, realization_owner=owner,
                      roundtrip_matches=bool(checks), intent_grounding='LEARNED_PROPOSAL_NOT_PROVEN_SPEAKER_INTENT')
        # A roundtrip checks realization, not correctness of the learned intent interpretation.
        result['status'] = 'REALIZATION_CHECKED_INTENT_PROPOSED' if checks else 'DEFER'
        result['realized_program'] = tree if checks else None
        result['accepted_program'] = None
        result['open_obligations'].append('INSTRUCTION_TO_INTENT_ALIGNMENT_UNVERIFIED')
    return result

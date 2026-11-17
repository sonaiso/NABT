"""Ordered A116 recursive proposals. Exact identities/law remain owned by NABT."""
from hashlib import sha256
import json
import math
import re
from pathlib import Path

from nabt.alphabet import ALPHABET_ID, validate_cells, parse_word, render_word
from nabt.codec import encode_cells, decode_number, pack_cells, unpack_cells
from nabt.errors import resource_limit
from nabt.machine import Machine, compose_effects

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'evidence/ntp_recursive_v1/model.json'
MODEL_SHA256 = 'd5284a47e83ade9a018ec092d88b0738fe6b58a03138bdc5e79513953ebf81f7'
DIM = 16
MAX_CELLS = 64
MAX_TEXT_BYTES = 4 * MAX_CELLS
LABELS = {
    'reading': ['faala_marks', 'fuila_marks', 'suffix_ta', 'suffix_ti', 'suffix_tu'],
    'morphology': ['active_past', 'addressee_female', 'addressee_male', 'passive_past', 'speaker'],
    'attachment': ['addressee_suffix', 'agent', 'patient_subject', 'speaker_suffix'],
}


def bits(cell):
    return [(cell >> i) & 1 for i in range(7)]


def shared_shapes():
    return {'bits': (DIM, 7), 'carrier': (29, DIM), 'mark': (4, DIM),
            'compose': (DIM, 2 * DIM), 'bias': (DIM,)}


def shapes():
    return {**shared_shapes(),
            **{'head_' + h: (len(v), DIM) for h, v in LABELS.items()}}


def validate_model(model):
    def shape(x, dims):
        if not dims:
            return type(x) in (int, float) and abs(x) <= 1000 and math.isfinite(x)
        return type(x) is list and len(x) == dims[0] and all(shape(v, dims[1:]) for v in x)
    if (type(model) is not dict or set(model) != {'schema', 'alphabet_id', 'labels', 'parameters',
            'protocol_sha256', 'source_sha256', 'authority', 'release_policy'}
            or model['schema'] != 'nabt.ntp-recursive-model.v1' or model['alphabet_id'] != ALPHABET_ID
            or model['labels'] != LABELS or model['authority'] != 'NONE'
            or model['release_policy'] != 'REVIEW_ONLY'
            or any(type(model[field]) is not str or re.fullmatch('[0-9a-f]{64}', model[field]) is None
                   for field in ('protocol_sha256', 'source_sha256'))
            or type(model['parameters']) is not dict or set(model['parameters']) != set(shapes())
            or any(not shape(model['parameters'][k], dims) for k, dims in shapes().items())):
        raise ValueError('Invalid recursive model')
    return model


def load():
    raw = MODEL.read_bytes()
    if len(raw) > 1048576 or sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError('Recursive model identity changed')
    model = validate_model(json.loads(raw))
    for path, field in ((ROOT / 'evidence/ntp_recursive_v1/protocol.json', 'protocol_sha256'),
                        (ROOT / 'evidence/shared_cell_reading_v1/train.json', 'source_sha256')):
        if sha256(path.read_bytes()).hexdigest() != model[field]:
            raise ValueError('Recursive model provenance changed')
    return model


def _linear(matrix, vector):
    return [sum(a * b for a, b in zip(row, vector, strict=True)) for row in matrix]


def join_states(parameters, left, right):
    """Shared neural composition; this is not a license for a source join."""
    if len(left) != DIM or len(right) != DIM:
        raise ValueError('Recursive state dimension changed')
    return [math.tanh(v + parameters['bias'][i]) for i, v in enumerate(
        _linear(parameters['compose'], list(left) + list(right)))]


def encode_state(parameters, cells):
    """Ordered A116 word representation reused by every learned objective."""
    values = validate_cells(cells)
    if len(values) > MAX_CELLS:
        raise resource_limit('Recursive cell budget exceeded', maximum=MAX_CELLS)
    if not values:
        raise ValueError('Expected 1..64 A116 cells')
    hidden = None
    for c in values:
        projection = _linear(parameters['bits'], bits(c))
        atom = [math.tanh(v + parameters['carrier'][c // 4][i] + parameters['mark'][c % 4][i])
                for i, v in enumerate(projection)]
        hidden = atom if hidden is None else join_states(parameters, hidden, atom)
    return hidden


def scores(model, cells):
    """The training graph: ordered left fold; every original cell is retained."""
    p = validate_model(model)['parameters']
    hidden = encode_state(p, cells)
    result = {}
    for head, labels in LABELS.items():
        logits = _linear(p['head_' + head], hidden)
        z = max(logits)
        weights = [math.exp(v - z) for v in logits]
        result[head] = [{'label': label, 'score': v / sum(weights)} for label, v in zip(labels, weights)]
    return result


def source(request):
    if type(request) is not dict or set(request) not in ({'text'}, {'packed_hex'}):
        raise ValueError('Forward accepts marked text or the installed A116 bit frame')
    if 'text' in request:
        text = request['text']
        if type(text) is not str:
            raise ValueError('Expected bounded exact marked text')
        if len(text) > MAX_TEXT_BYTES:
            raise resource_limit('Recursive source byte budget exceeded', maximum_bytes=MAX_TEXT_BYTES)
        try:
            byte_count = len(text.encode('utf-8', errors='strict'))
        except UnicodeError as error:
            raise ValueError('Invalid source UTF-8') from error
        if byte_count > MAX_TEXT_BYTES:
            raise resource_limit('Recursive source byte budget exceeded', maximum_bytes=MAX_TEXT_BYTES)
        cells = parse_word(text)
        kind = 'EXACT_MARKED_TEXT'
    else:
        raw = request['packed_hex']
        if type(raw) is not str:
            raise ValueError('Expected canonical bounded A116 frame hex')
        if len(raw) > 130:
            raise resource_limit('Recursive bit frame budget exceeded', maximum_hex_characters=130)
        if re.fullmatch(r'(?:[0-9a-f]{2})+', raw) is None:
            raise ValueError('Expected canonical bounded A116 frame hex')
        cells = unpack_cells(bytes.fromhex(raw))
        text, kind = render_word(cells), 'A116_BIT_FRAME'
    if len(cells) > MAX_CELLS:
        raise resource_limit('Recursive cell budget exceeded', maximum=MAX_CELLS)
    if not cells:
        raise ValueError('Recursive source is empty')
    return text, cells, kind


def forward(request):
    text, cells, kind = source(request)
    number = encode_cells(cells)
    machine = Machine('wasl')
    exact = machine.analyse(cells).as_dict()
    # Reuse the exact input-dependent algebra, not independent state-zero
    # acceptance of each child. Neural tanh never supplies these certificates.
    effect = machine.effect(cells[:1])
    joins = []
    for i in range(1, len(cells)):
        right_entry = effect.destinations[0]
        effect = compose_effects(effect, machine.effect(cells[i:i + 1]))
        joins.append({'op': 'join', 'left_span': [0, i], 'right_span': [i, i + 1],
                      'right_entry_state': right_entry, 'output_state': effect.destinations[0],
                      'weight': effect.weights[0], 'scope': 'EXACT_STATE_RELATIVE_EFFECT',
                      'linguistic_interpretation_established': False})
    result = {'schema': 'nabt.ntp-recursive-forward.v1', 'text': text,
              'input_kind': kind, 'packed_hex': pack_cells(cells).hex(),
              'alphabet_id': ALPHABET_ID, 'cells': list(cells), 'number_hex': hex(number),
              'number_encoding': 'BIJECTIVE_BASE116',
              'restored': list(decode_number(number)), 'law': exact,
              'law_table_sha256': machine.table_sha256, 'authority': 'NONE',
              'algebra': {'joins': joins, 'effect': effect.as_dict(),
                          'source_restored': effect.cells == cells},
              'release_policy': 'REVIEW_ONLY', 'grammar_certified': False,
              'world_truth_established': False, 'proposals': None,
              'general_ifadah_established': False}
    try:
        result.update(status='PROPOSED', proposals=scores(load(), cells), model_sha256=MODEL_SHA256)
    except (OSError, ValueError, KeyError) as error:
        result.update(status='MODEL_UNAVAILABLE', reason=str(error))
    return result

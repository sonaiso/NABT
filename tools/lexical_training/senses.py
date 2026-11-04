"""Text-to-sense proposals over the installed catalogue, without acceptance authority.

The small NumPy MLP is optional. The existing lexical testimony owner alone
replays conditional indications. Scores never enter its request or prune rows.
"""
from pathlib import Path
import json
import re
import numpy as np
from tools import lexical_testimony as testimony
from .data import normalize, digest
from .features import features

SCHEMA = 'nabt.neural-sense-model.v1'
BUCKETS, HIDDEN = 512, 32


def catalogue():
    raw = (testimony.ROOT / testimony.CATALOG).read_bytes()
    if digest(raw) != testimony.CATALOG_SHA:
        raise ValueError('CATALOGUE_IDENTITY_CHANGED')
    return json.loads(raw)


def encode(texts):
    x = np.zeros((len(texts), BUCKETS), dtype=np.float64)
    for i, text in enumerate(texts):
        if type(text) is not str or not text.strip() or len(text.encode('utf-8')) > 8192:
            raise ValueError('nonempty UTF-8 text of at most 8192 bytes required')
        view = ' '.join(re.findall('[ء-غف-ي]+', normalize(text)))
        if not view:
            raise ValueError('no Arabic retrieval features')
        for k, v in features(view, BUCKETS).items():
            x[i, k] = 1 + np.log(v)
        x[i] /= max(np.linalg.norm(x[i]), 1e-12)
    return x


def forward(weights, x):
    hidden = np.tanh(x @ weights['w1'] + weights['b1'])
    logits = hidden @ weights['w2'] + weights['b2']
    ex = np.exp(logits - logits.max(axis=1, keepdims=True))
    return ex / ex.sum(axis=1, keepdims=True)


def training_rows(cat):
    # Multiple identities may share one gloss: do not invent a unique gold sense.
    rows = {}
    ids = [s['id'] for s in cat['senses']]
    for s in cat['senses']:
        for text in [s['citation']['quotation'], ' '.join(s['components'])]:
            rows.setdefault(text, set()).add(ids.index(s['id']))
    texts = list(rows)
    y = np.zeros((len(texts), len(ids)))
    for i, text in enumerate(texts):
        for index in rows[text]:
            y[i, index] = 1 / len(rows[text])
    return texts, y


def train(x, y, protocol):
    if (protocol['buckets'], protocol['hidden']) != (BUCKETS, HIDDEN):
        raise ValueError('unsupported architecture')
    rng = np.random.default_rng(protocol['seed'])
    weights = {'w1': rng.normal(0, .1, (BUCKETS, HIDDEN)), 'b1': np.zeros(HIDDEN),
               'w2': rng.normal(0, .1, (HIDDEN, y.shape[1])), 'b2': np.zeros(y.shape[1])}
    m = {k: np.zeros_like(v) for k, v in weights.items()}
    v = {k: np.zeros_like(a) for k, a in weights.items()}
    history = []
    for step in range(1, protocol['epochs'] + 1):
        h = np.tanh(x @ weights['w1'] + weights['b1'])
        p = forward(weights, x)
        error = (p-y)/len(x)
        dh = (error @ weights['w2'].T) * (1-h*h)
        grads = {'w1': x.T@dh, 'b1': dh.sum(0), 'w2': h.T@error, 'b2': error.sum(0)}
        for k, g in grads.items():
            m[k] = .9*m[k]+.1*g
            v[k] = .999*v[k]+.001*g*g
            weights[k] -= protocol['learning_rate']*(m[k]/(1-.9**step))/(np.sqrt(v[k]/(1-.999**step))+1e-8)
        if step == 1 or step % 100 == 0:
            history.append({'step': step, 'loss': float(-(y*np.log(np.maximum(p, 1e-15))).sum()/len(x))})
    return weights, history


def load_model(directory):
    directory = Path(directory)
    if (directory/'model.json').stat().st_size > 65536 or (directory/'weights.npz').stat().st_size > 2_000_000:
        raise ValueError('model size limit')
    meta = testimony._strict_json((directory/'model.json').read_bytes())
    cat = catalogue()
    ids = [s['id'] for s in cat['senses']]
    if (meta['schema'] != SCHEMA or meta['catalogue_sha256'] != testimony.CATALOG_SHA
            or meta['sense_ids'] != ids or meta['features'] != 'lexical-crc32-word-char34-v1'
            or meta['weights_sha256'] != digest((directory/'weights.npz').read_bytes())):
        raise ValueError('model identity mismatch')
    shapes = {'w1': (BUCKETS, HIDDEN), 'b1': (HIDDEN,), 'w2': (HIDDEN, len(ids)), 'b2': (len(ids),)}
    # npz is data only; reject object arrays and compressed bombs before loading.
    import zipfile
    with zipfile.ZipFile(directory/'weights.npz') as archive:
        if sum(i.file_size for i in archive.infolist()) > 2_000_000:
            raise ValueError('expanded weights limit')
    with np.load(directory/'weights.npz', allow_pickle=False) as archive:
        if set(archive.files) != set(shapes):
            raise ValueError('unexpected model tensors')
        weights = {k: archive[k] for k in shapes}
    for k, a in weights.items():
        if a.shape != shapes[k] or a.dtype.kind != 'f' or not np.isfinite(a).all() or np.max(np.abs(a)) > 100:
            raise ValueError('invalid tensor shape or values')
    return weights, meta, cat


def propose(text, entry, directory, target=None):
    if type(entry) is not str or not entry.strip() or len(entry.encode()) > 128:
        raise ValueError('explicit bounded root index required')
    target = [] if target is None else target
    if type(target) is not list or len(target) > 64 or any(type(t) is not str or not t.strip() or len(t.encode()) > 4096 for t in target):
        raise ValueError('invalid target components')
    x = encode([text])
    weights, meta, cat = load_model(directory)
    scores = forward(weights, x)[0]
    rows = [{'sense_id': s['id'], 'score': float(scores[i]), 'sense': s}
            for i, s in enumerate(cat['senses']) if s['root'] == entry]
    rows.sort(key=lambda r: (-r['score'], r['sense_id']))
    # Do not pass argmax, score, order, or only the top sense into the owner.
    checked = testimony.assess(entry, target)
    return {'schema': 'nabt.neural-sense-proposal.v1', 'text': text,
            'text_sha256': digest(text.encode()), 'entry': entry, 'target': target,
            'model_sha256': meta['weights_sha256'], 'catalogue_sha256': testimony.CATALOG_SHA,
            'status': 'UNVERIFIED_SENSE_PROPOSAL' if rows else 'UNMEASURED_ROOT',
            'authority': 'NONE', 'intended_sense_established': False,
            'calibrated_probabilities': False, 'all_arabic_senses_enumerated': False,
            'ranking': rows, 'conditional_testimony': checked,
            'limits': ['Root is supplied, not acquired.', 'Scores rank all installed senses; none is selected as intended.',
                       'The native result checks supplied target components, not neural interpretation fidelity.',
                       'Training interpretations are authored, not independently adjudicated.']}

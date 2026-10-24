"""Extract immutable source windows for review; does not import NABT or change gold."""
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from pathlib import Path
import gzip
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(raw):
    return sha256(raw).hexdigest()


def window(path, first, last, record_id, authority):
    p = ROOT / path
    raw = p.read_bytes()
    lines = raw.splitlines(keepends=True)
    start, end = sum(map(len, lines[:first - 1])), sum(map(len, lines[:last]))
    excerpt = raw[start:end]
    return {'record_id': record_id, 'authority': authority, 'path': path,
            'source_sha256': digest(raw), 'source_bytes': len(raw),
            'line_start': first, 'line_end': last, 'start': start, 'end': end,
            'span_sha256': digest(excerpt), 'raw_text': excerpt.decode('utf-8')}


def html_section(path, title, record_id):
    raw = (ROOT / path).read_bytes()
    headings = list(re.finditer(rb'<h4\b[^>]*>(.*?)</h4>', raw, re.S | re.I))
    index = next(i for i, heading in enumerate(headings)
                 if unescape(re.sub('<[^>]+>', '', heading.group(1).decode())).strip() == title)
    start = headings[index].start()
    end = headings[index + 1].start() if index + 1 < len(headings) else raw.find(b'<h3', start)
    if end < 0:
        end = len(raw)
    excerpt = raw[start:end]
    text = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', excerpt.decode()))).strip()
    return {'record_id': record_id, 'authority': 'QAC_PUBLISHER_ENCODING_DOCUMENTATION',
            'path': path, 'source_url': 'https://corpus.quran.com/documentation/morphologicalfeatures.jsp',
            'source_sha256': digest(raw), 'source_bytes': len(raw), 'title': title,
            'line_start': raw[:start].count(b'\n') + 1,
            'line_end': raw[:end].count(b'\n') + 1,
            'start': start, 'end': end, 'span_sha256': digest(excerpt),
            'raw_html': excerpt.decode(), 'visible_text': text}


head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT).decode().strip()
base = 'src/nabt/data/source_evidence/'
sources = [
    window(base + 'sibawayhi.txt', 110, 148, 'sibawayhi_mutamakkin_case_endings',
           'CLASSICAL_GRAMMATICAL_RULE_WITH_EXAMPLES'),
    window(base + 'sibawayhi.txt', 216, 229, 'sibawayhi_tanwin_tamkin',
           'CLASSICAL_GRAMMATICAL_RULE_WITH_EXCEPTIONS'),
    window(base + 'qatr.txt', 41, 52, 'qatr_nominal_diagnostics_and_declension',
           'CLASSICAL_GRAMMATICAL_RULE_WITH_EXCEPTIONS'),
    window(base + 'qatr.txt', 75, 95, 'qatr_case_signs_and_nonregular_paradigms',
           'CLASSICAL_GRAMMATICAL_RULE_WITH_EXCEPTIONS'),
    window(base + 'sibawayhi.txt', 10510, 10538, 'sibawayhi_adjectivity_diptote_caution',
           'CLASSICAL_COUNTEREVIDENCE_TO_UNRESTRICTED_POS_COLLAPSE'),
    html_section('evidence/arabic_completion_v3/source_review/qac_morphologicalfeatures.html',
                 'Roots and Lemmas', 'qac_lemma_identity_contract'),
    html_section('evidence/arabic_completion_v3/source_review/qac_morphologicalfeatures.html',
                 'Derived Nouns', 'qac_noun_adjective_derived_nominal_encoding'),
    html_section('evidence/arabic_completion_v3/source_review/qac_morphologicalfeatures.html',
                 'Nominal Features', 'qac_shared_nominal_case_encoding'),
    html_section('evidence/arabic_completion_v3/source_review/qac_morphologicalfeatures.html',
                 'Person, Gender and Number', 'qac_explicit_number_encoding_no_documented_default'),
]
qac_path = ROOT / 'artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz'
compressed = qac_path.read_bytes()
qac = gzip.decompress(compressed)
assert digest(qac) == 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46'
qac_lines = qac.splitlines(keepends=True)
qac_rows = []
cursor = 0
for number, line in enumerate(qac_lines, 1):
    text = line.decode('utf-8')
    selected = any(tag in text for tag in ('LEM:kariym|', 'LEM:baSiyr|', 'LEM:raADiyap|', 'LEM:bayot|'))
    selected = selected or text.startswith(('(89:15:7:', '(89:15:11:'))
    if selected:
        qac_rows.append({'line': number, 'start': cursor, 'end': cursor + len(line),
                         'sha256': digest(line), 'raw_text': text})
    cursor += len(line)
qac_identity = {'path': str(qac_path.relative_to(ROOT)), 'format': 'QAC_MORPHOLOGY_0.4',
                'compressed_sha256': digest(compressed), 'decoded_sha256': digest(qac),
                'decoded_bytes': len(qac), 'records': qac_rows,
                'scope': 'Full-source research inventory only. Runtime donors must separately survive the original exclusion/holdout policy; this file does not license training on excluded rows.'}
with (HERE / 'selected_qac_source_rows_v1.json').open('x', encoding='utf-8') as handle:
    json.dump(qac_identity, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write('\n')

review = {
    'schema': 'nabt.arabic-completion.nominal-pos-bridge-source-review.v1',
    'created_utc': datetime.now(timezone.utc).isoformat(), 'head': head, 'tree': tree,
    'status': 'SOURCE_SUPPORTED_BOUNDED_DESIGN_INFERENCE',
    'source_selection_was_after_residual_case_exposure': True,
    'independence': 'Primary source texts and QAC publication predate the benchmark; source selection and this review are by the same collaborating development team, not a blind or externally independent evaluation.',
    'proposed_rule_id': 'same_lexeme_class0_nominal_inflection_v1',
    'conditions': [
        'Both origins are actually source-backed N or ADJ, not PN or context-only declarations.',
        'Their complete lemma/root/vocalized template/gender/number and derivational features agree exactly; lexical shadda is retained.',
        'Number is independently known to be singular in both origins; unknown is not a match that supplies singular.',
        'Each origin independently has exactly class_candidates=[0] from its own current evidence; each has a raw tanwin witness and the target class is not borrowed from the donor.',
        'The donor has inflected construction established by a valid pair of distinct observed case endings for that same lexical identity.',
        'All donor and origin records are reacquired from current raw source after the declared exclusions; cached class or lexical_id labels alone are insufficient.',
        'Raw source IDs, record locations and pair provenance remain bound to the promoted construction.',
    ],
    'permitted_effect': 'Only construction=inflected and the retained pair witness IDs. No transfer of sense, reference, grammatical gender/number, POS, lemma, or class restriction.',
    'interpretation': 'The classical sources establish declension of independently established mutamakkin nominals and distinguish exceptional patterns. QAC documents shared nominal case features and lemma/derived-nominal grouping across N and ADJ. Treating the specified equal source identities as one class-0 inflectional paradigm is an explicit bounded implementation inference from these premises; no source literally specifies a Python dictionary key or proves general parser refinement.',
    'candidate_scope': {'strong_candidates': ['kariym N/ADJ', 'baSiyr N/ADJ'],
                        'excluded_by_present_premises': ['raADiyap: distinct r/rr source templates and unknown number',
                                                       'context proper names', 'diptotes and non-class-0 paradigms']},
    'counterexample_requirements': ['Withdraw either origin raw witness', 'Withdraw or exclude either pair member',
        'Change one lexical shadda or derivation feature', 'Unknown or different number/gender',
        'Change origin to PN or context-only source', 'Introduce a conflicting class candidate',
        'Keep original N/ADJ semantic alternatives even after completing their morphology'],
    'source_windows': sources,
    'qac_source_rows': {'path': 'evidence/arabic_completion_v3/source_review/selected_qac_source_rows_v1.json',
                        'sha256': digest((HERE / 'selected_qac_source_rows_v1.json').read_bytes())},
    'not_claimed': ['All adjectives and nouns share one declension paradigm', 'Missing QAC number means singular',
                    'Shadda may be discarded', 'A lexical paradigm fixes contextual meaning or external reference',
                    'Original heldout cases have become a new blind test'],
}
with (HERE / 'nominal_pos_bridge_source_review_v1.json').open('x', encoding='utf-8') as handle:
    json.dump(review, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write('\n')

dictionary_path = HERE / 'mukhtar_sihah_part1.html'
dictionary = dictionary_path.read_bytes()
start = dictionary.index('[ حسب ]'.encode())
end = dictionary.index('[ حسد ]'.encode(), start)
excerpt = dictionary[start:end]
visible = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', excerpt.decode()))).strip()
hasiba = {
    'schema': 'nabt.arabic-completion.hasiba-source-review.v1',
    'created_utc': datetime.now(timezone.utc).isoformat(), 'head': head,
    'status': 'POSITIVE_VOCALIZED_SENSE_DISCRIMINATOR_FOUND',
    'source_author': 'محمد بن أبي بكر بن عبد القادر الرازي', 'work': 'مختار الصحاح',
    'entry': 'حسب', 'source_url': 'https://www.islamicbook.ws/adab/la/mkhtar-alshah-001.html',
    'edition_scope': 'Named primary dictionary in an online transcription; exact downloaded bytes are preserved. This is not diplomatic authentication of a printed edition.',
    'path': str(dictionary_path.relative_to(ROOT)), 'source_sha256': digest(dictionary),
    'source_bytes': len(dictionary), 'start': start, 'end': end,
    'line_start': dictionary[:start].count(b'\n') + 1,
    'line_end': dictionary[:end].count(b'\n') + 1,
    'span_sha256': digest(excerpt), 'raw_html': excerpt.decode(), 'visible_text': visible,
    'corroborating_pinned_sources': [
        window(base + 'sabban.txt', 16313, 16335, 'sabban_counting_hasaba_open_sin',
               'LATER_COMMENTATOR_EXPLICIT_VOWEL_GLOSS'),
        window(base + 'sibawayhi.txt', 398, 418, 'sibawayhi_cognitive_hasiba_and_ambiguous_alima',
               'CLASSICAL_GRAMMATICAL_RULE_WITH_SENSE_DISTINCTIONS'),
    ],
    'finding': 'The dictionary explicitly distinguishes hasaba=count, in the nasara/kataba pattern, from hasibtuhu salihan with kasra=thought him righteous. This supplies a positive phonological/sense discriminator for a fully vocalized hasiba occurrence; the bare consonantal string does not.',
    'proposed_scope': 'Source-qualified perfect form-I حَسِبَ with the explicit medial kasra and the independently licensed cognitive two-complement construction. Keep the embedded proposition inside cognitive scope; do not assert its truth.',
    'negative_controls': ['حَسَبَ with fatha must not receive the same cognitive license',
                          'Unvocalized حسب must retain unresolved senses unless another independent witness supplies the missing distinction',
                          'حَسُبَ / حَسْب / حَسَّب / حاسَب and incompatible morphological analyses must not match',
                          'عَلِمَ is not licensed by this distinction; the pinned Sibawayhi passage explicitly retains عرف usage'],
    'source_selection_was_after_residual_case_exposure': True,
    'not_claimed': 'No general sense disambiguation from word order alone, no arbitrary lemma/root equivalence, no world truth, and no newly blind test.',
}
with (HERE / 'hasiba_source_review_v1.json').open('x', encoding='utf-8') as handle:
    json.dump(hasiba, handle, ensure_ascii=False, indent=2, sort_keys=True)
    handle.write('\n')
for name in ['nominal_pos_bridge_source_review_v1.json', 'hasiba_source_review_v1.json', 'selected_qac_source_rows_v1.json']:
    raw = (HERE / name).read_bytes()
    print(json.dumps({'path': str((HERE / name).relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}, ensure_ascii=False))

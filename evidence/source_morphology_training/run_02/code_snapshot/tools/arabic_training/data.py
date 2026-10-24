"""Exact MASAQ intake and book-grounded annotation conflict audit.

Quranic morphology only. No syntactic-role or semantic labels enter the learner.
The original source remains unchanged; gold segmentation is never model input.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
DATA_SHA256 = 'd43d2a813afbe0490254bb26623d6041ed352a273d333e731ddbcda3bd0b6f3a'
DATA_BYTES = 20302008
FIELDS = ['ID', 'Sura_No', 'Verse_No', 'Column5', 'Word_No', 'Word', 'Without_Diacritics',
          'Segmented_Word', 'Morph_tag', 'Morph_type', 'Punctuation_Mark', 'Invariable_Declinable',
          'Syntactic_Role', 'Possessive_Construct', 'Case_Mood', 'Case_Mood_Marker', 'Phrase', 'Phrasal_Function', 'Notes']
TASKS = ('tag', 'declension', 'case_mood')
VERBS = {'PV', 'PV_PASS', 'IV', 'IV_PASS', 'CV', 'UNINFLECTED_VERB'}
BUILT_VERBS = {'PV', 'PV_PASS', 'CV'}
MISSING = {'', 'None'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_constraints(tag, declension, case_mood):
    """Flag incompatible annotations under these explicitly scoped readings.

    These are audit obligations, not automatic corrections or corpus verdicts.
    In particular, built forms can occupy a syntactic case position; that pair
    is NOT rejected. Only the independently stated narrow constraints apply.
    """
    result = []
    if tag in VERBS and case_mood == 'مجرور':
        result.append('VERB_HAS_NO_GENITIVE')
    if tag.startswith(('NOUN', 'GERUND', 'ADJ')) and case_mood == 'مجزوم':
        result.append('NOUN_HAS_NO_JUSSIVE')
    if tag in BUILT_VERBS and declension == 'معرب':
        result.append('PAST_AND_IMPERATIVE_ARE_BUILT')
    return result


def book_evidence():
    registry = json.loads((ROOT / 'src/nabt/data/source_evidence/source_manifest.json').read_text())
    pins = {r['source_id']: r for r in registry['documents']}
    specs = [
        ('sibawayhi', 102, 110, 'WORD_CATEGORIES'),
        ('sibawayhi', 111, 126, 'NOUN_HAS_NO_JUSSIVE'),
        ('qatr', 54, 71, 'PAST_AND_IMPERATIVE_ARE_BUILT'),
        ('qatr', 77, 82, 'VERB_HAS_NO_GENITIVE'),
        ('qatr', 84, 95, 'NUMBER_AND_AFFIX_SIGN_SCOPE'),
        ('qatr', 219, 239, 'PARTICIPANT_AND_AGREEMENT_BACKLOG'),
        ('qatr', 313, 320, 'TAMYIZ_FRAME_AND_OWNER_BACKLOG'),
    ]
    records = []
    for book, first, last, rule in specs:
        path = ROOT / 'src/nabt/data/source_evidence' / (book + '.txt')
        raw = path.read_bytes()
        if sha(raw) != pins[book]['sha256'] or len(raw) != pins[book]['bytes']:
            raise ValueError('book source identity mismatch')
        lines = raw.splitlines(keepends=True)
        start = sum(map(len, lines[:first-1]))
        end = sum(map(len, lines[:last]))
        records.append(dict(rule=rule, source_path=str(path.relative_to(ROOT)),
                            source_sha256=sha(raw), start_byte=start, end_byte=end,
                            first_line=first, last_line=last, quote_sha256=sha(raw[start:end]),
                            quote=raw[start:end].decode('utf-8'),
                            scope='authored interpretation of pinned source; not a model-derived law'))
    return records


def split_for_sura(sura):
    if type(sura) is not int or not 1 <= sura <= 114:
        raise ValueError('invalid sura identity')
    bucket = int(sha(('nabt-morph-v1:' + str(sura)).encode())[:8], 16) % 10
    return 'test' if bucket == 0 else 'dev' if bucket == 1 else 'train'


def duplicate_key(words):
    # Audit key only; original training/evaluation bytes are NEVER normalized.
    return tuple(''.join(c for c in word if not unicodedata.combining(c)) for word in words)


def read_source(path, *, verify=True):
    raw = Path(path).read_bytes()
    if verify and (len(raw) != DATA_BYTES or sha(raw) != DATA_SHA256):
        raise ValueError('MASAQ byte identity mismatch')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    if reader.fieldnames != FIELDS:
        raise ValueError('unexpected MASAQ schema')
    groups = defaultdict(list)
    for row_number, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError('malformed CSV row')
        key = tuple(int(row[k]) for k in ('Sura_No', 'Verse_No', 'Column5'))
        if not 1 <= key[0] <= 114 or min(key[1:]) < 1:
            raise ValueError('invalid source address')
        groups[key].append((row_number, row))
    verses = defaultdict(list)
    reasons, conflicts = Counter(), []
    for key, group in sorted(groups.items()):
        if len({r['Word'] for _, r in group}) != 1:
            raise ValueError('one address has competing word bytes')
        text = group[0][1]['Word']
        stems = [(n, r) for n, r in group if r['Morph_type'] == 'Stem']
        labels = dict.fromkeys(TASKS)
        why = []
        if len({r['ID'] for _, r in group}) != 1:
            why.append('MULTIPLE_ANNOTATION_IDS')
        if len(stems) != 1:
            why.append('MULTIPLE_OR_MISSING_STEMS')
        if not re.search('[\u064b-\u0652]', text):
            why.append('NO_VOWEL_MARK_OBSERVED')
        if len(text) > 32:
            why.append('CHARACTER_BUDGET')
        original_labels = None
        if len(stems) == 1:
            row = stems[0][1]
            original_labels = dict(tag=row['Morph_tag'], declension=row['Invariable_Declinable'], case_mood=row['Case_Mood'])
            violations = source_constraints(row['Morph_tag'], row['Invariable_Declinable'], row['Case_Mood'])
            why.extend(violations)
            if violations:
                conflicts.append(dict(address=list(key), csv_rows=[n for n, _ in group],
                                      word=text, raw_labels=original_labels, obligations=violations))
            if not why:
                labels = dict(tag=row['Morph_tag'] if row['Morph_tag'] not in MISSING else None,
                              declension=row['Invariable_Declinable'] if row['Invariable_Declinable'] in {'معرب', 'مبني'} else None,
                              case_mood=row['Case_Mood'] if row['Case_Mood'] not in MISSING else None)
        reasons.update(why)
        # Affix labels come only from explicit prefix/suffix rows. OTHER_I3RAB
        # is neither an alternative reading nor a new textual observation.
        affixes = sorted({r['Morph_tag'] for _, r in group if r['Morph_type'] in {'Prefix', 'Suffix'} and r['Morph_tag'] not in MISSING})
        word = dict(address=list(key), csv_rows=[n for n, _ in group], text=text,
                    text_sha256=sha(text.encode()), labels=labels, raw_labels=original_labels,
                    affixes=affixes if not why else None, excluded_reasons=why)
        verses[key[:2]].append(word)
    # Quarantine every duplicate verse across different suras before assigning
    # folds; no test labels/predictions are inspected to decide the quarantine.
    identities = defaultdict(set)
    for key, words in verses.items():
        identities[duplicate_key([w['text'] for w in words])].add(key[0])
    examples, duplicate_verses = [], []
    for (sura, verse), words in sorted(verses.items()):
        if len(identities[duplicate_key([w['text'] for w in words])]) > 1:
            duplicate_verses.append([sura, verse])
            continue
        examples.append(dict(id=f'{sura}:{verse}', sura=sura, verse=verse,
                             split=split_for_sura(sura), words=words))
    split_counts = {}
    for split in ('train', 'dev', 'test'):
        part = [e for e in examples if e['split'] == split]
        split_counts[split] = dict(verses=len(part), suras=sorted({e['sura'] for e in part}),
                                  words=sum(len(e['words']) for e in part),
                                  targets={task: sum(w['labels'][task] is not None for e in part for w in e['words']) for task in TASKS},
                                  affix_targets=sum(w['affixes'] is not None for e in part for w in e['words']))
    manifest = dict(schema='nabt.masaq-morphology-intake.v1', source_sha256=sha(raw), source_bytes=len(raw),
                    csv_rows=sum(map(len, groups.values())), word_occurrences=len(groups), verse_count=len(verses),
                    supervision_exclusion_reasons=dict(reasons),
                    duplicate_verses_quarantined=duplicate_verses, splits=split_counts,
                    scope='Quranic morphology from pinned repository copy; not independent general Arabic or semantic truth',
                    input_columns=['Word', 'same-verse Word context'],
                    forbidden_input_columns=[c for c in FIELDS if c != 'Word'],
                    root_ood_measured=False, template_ood_measured=False,
                    all_arabic_complete=False, world_truth_established=False)
    return examples, manifest, conflicts

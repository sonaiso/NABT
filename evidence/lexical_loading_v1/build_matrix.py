#!/usr/bin/env python3
"""Replay a source-only diagnostic matrix; never read benchmark cases or labels.

The frozen catalogue defines the complete selection. A consonantal headword
candidate is not a licensed cross-source sense identification. The original
external QAC source remains unmodified and is not redistributed here.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from nabt.corpus_evidence import buckwalter_to_arabic, _root
from nabt.corpus_sources import read_corpus
from nabt.errors import NabtError

HERE = Path(__file__).parent
QAC_PATH = ROOT / 'artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz'
QAC_SHA = 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46'
QAC_BYTES = 6309503
CATALOGUE = ROOT / 'evidence/lexical_completion_v1/catalog.json'
# All explicitly lexical headwords in the unchanged pre-existing catalogue.
# Root-origin passages are deliberately not relabelled as lemma definitions.
BASE_HEADWORDS = {
    'lisan:fahm-knowledge': 'الفهم', 'lisan:fahm-tribe': 'فهم',
    'lisan:qalam-writing': 'القلم', 'lisan:qalam-lot': 'القلم',
    'lisan:qalam-gambling': 'القلم', 'lisan:sama-hearing': 'السمع',
    'lisan:sama-ear': 'السمع', 'lisan:basar': 'البصر',
    'lisan:faras': 'الفرس', 'lisan:saqf': 'السقف',
    'lisan:asad-animal': 'الأسد', 'lisan:ama': 'العمى',
    'shakhsiyya3:insan-definition': 'الإنسان',
}
NOMINAL_TAGS = {'N', 'PN', 'ADJ', 'T', 'LOC'}
# Shadda and dagger alif remain significant; madda is retained in the original
# source and only ignored in this candidate-search projection. No hamza fold.
SEARCH_MARKS = re.compile('[\u064b-\u0650\u0652\u0653]')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def wire(obj): return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
def key(value):
    return unicodedata.normalize('NFC', SEARCH_MARKS.sub('', unicodedata.normalize('NFD', value)))
def base_headword(value): return value[2:] if value.startswith('ال') else value

def build(source_path=QAC_PATH):
    freeze = json.loads((HERE / 'selection.json').read_text())
    catalogue_raw = CATALOGUE.read_bytes()
    if sha(catalogue_raw) != freeze['catalogue_sha256']:
        raise ValueError('Frozen catalogue identity mismatch')
    catalog = json.loads(catalogue_raw)
    if [s['id'] for s in catalog['senses']] != freeze['sense_ids']:
        raise ValueError('Frozen all-sense selection mismatch')
    raw = gzip.decompress(source_path.read_bytes())
    if len(raw) != QAC_BYTES or sha(raw) != QAC_SHA:
        raise ValueError('Pinned external QAC identity mismatch')
    corpus = read_corpus(raw, format='qac', source_id='qac_external_v04')
    by_key = defaultdict(lambda: defaultdict(list))
    tag_counts = Counter(); omitted = Counter(); unique_lemmas = set()
    # No source case/mood labels license a new occurrence. They are retained as
    # exact annotation provenance here, and masked by the production learner.
    for row in corpus['records']:
        fields = row.get('fields')
        if not fields: continue
        features = fields['FEATURES'].split('|')
        if 'STEM' not in features: continue
        pos = fields['TAG']; tag_counts[pos] += 1
        if pos not in NOMINAL_TAGS: continue
        lbw = next((f[4:] for f in features if f.startswith('LEM:')), None)
        rbw = next((f[5:] for f in features if f.startswith('ROOT:')), None)
        if not lbw: omitted['lemma_missing'] += 1; continue
        try:
            lemma = buckwalter_to_arabic(lbw)
            surface = buckwalter_to_arabic(fields['FORM'])
        except NabtError:
            omitted['outside_declared_buckwalter_projection'] += 1; continue
        root = _root(rbw)
        unique_lemmas.add((lemma, pos))
        loc = fields['LOCATION']
        coords = [int(x) for x in loc.strip('()').split(':')]
        record_raw = raw[row['byte_start']:row['byte_end']]
        witness = {'locator': loc, 'word_locator': coords[:3],
            'surface': surface, 'form_bw': fields['FORM'],
            'features': fields['FEATURES'],
            'source_record': {'byte_start': row['byte_start'],
                'byte_end': row['byte_end'], 'sha256': sha(record_raw)}}
        by_key[key(lemma)][(lemma, lbw, root, rbw, pos)].append(witness)
    entries = []
    for sense in catalog['senses']:
        head = sense.get('lemma') or BASE_HEADWORDS.get(sense['id'])
        lemma = base_headword(head) if head else None
        candidates = []
        for i, ((ql, qlbw, qr, qrbw, pos), witnesses) in enumerate(sorted(
                by_key.get(key(lemma), {}).items(), key=lambda x: str(x[0])) if lemma else []):
            candidates.append({'id': f"{sense['id']}:morphology:{i}",
                'lemma': ql, 'lemma_bw': qlbw, 'root': qr, 'root_bw': qrbw,
                'pos': pos, 'occurrence_count': len(witnesses), 'witnesses': witnesses,
                'alignment_authority': 'CONSONANTAL_HEADWORD_CANDIDATE_ONLY',
                'contextual_sense_identified': False,
                'root_agreement': 'EXACT_RECORDED_LABEL' if qr == sense['root'] else 'DIFFERENT_OR_UNRESOLVED_LABEL'})
        residuals = list(sense.get('residuals', []))
        if not head: residuals.append('ROOT_PASSAGE_IS_NOT_A_LEMMA')
        elif not candidates: residuals.append('NO_PROJECTED_NOMINAL_LEMMA_IN_QAC')
        else: residuals.append('CROSS_SOURCE_SENSE_ALIGNMENT_UNADJUDICATED')
        if sense['id'] == 'lisan:v2:child':
            residuals.append('DICTIONARY_EXPLICIT_DAMMA_NOT_IDENTIFIED_WITH_QAC_FATHA')
        if sense['id'] == 'shakhsiyya3:insan-definition':
            residuals.append('LOGICAL_EXAMPLE_NOT_DICTIONARY_ATTESTATION')
        entries.append({'id': sense['id'], 'lemma': lemma, 'source_headword': head,
            'root': sense['root'], 'dictionary_citation': sense['citation'],
            'interpretation_status': sense['interpretation_status'],
            'components': sense['components'],
            'alignment_status': 'CANDIDATES_ONLY' if candidates else 'UNRESOLVED',
            'morphology_candidates': candidates, 'residuals': residuals,
            'sense_licensed_for_new_occurrence': False,
            'world_truth_asserted': False})
    counts = {'catalogue_senses': len(entries),
        'entries_with_morphological_candidates': sum(bool(e['morphology_candidates']) for e in entries),
        'entries_without_morphological_candidates': sum(not e['morphology_candidates'] for e in entries),
        'candidate_groups': sum(len(e['morphology_candidates']) for e in entries),
        'unique_candidate_lemmas': len({(c['lemma'],c['pos']) for e in entries for c in e['morphology_candidates']}),
        'unique_candidate_source_records': len({w['locator'] for e in entries for c in e['morphology_candidates'] for w in c['witnesses']}),
        'source_nominal_lemma_pos_pairs_projectable': len(unique_lemmas),
        'source_nominal_projection_omissions': dict(sorted(omitted.items())),
        'cross_source_senses_licensed': 0,
        'unresolved_deictic_senses': sum(e['interpretation_status']=='UNRESOLVED_DEICTIC_GLOSS' for e in entries)}
    return {'schema': 'nabt.lexical-loading-matrix.v1',
        'authority': 'EXACT_SOURCE_REPLAY_AND_CANDIDATE_ALIGNMENT_ONLY',
        'selection_sha256': sha((HERE/'selection.json').read_bytes()),
        'sources': {'qac': {'sha256': QAC_SHA, 'bytes': QAC_BYTES,
            'path': str(source_path.relative_to(ROOT)),
            'source_id': 'qac_external_v04',
            'url': 'https://raw.githubusercontent.com/Saleh1967/Alghanem/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/corpora/qac/quranic-corpus-morphology-0.4.txt.gz',
            'attribution': 'Quranic Arabic Corpus v0.4, Kais Dukes, 2011; http://corpus.quran.com; Tanzil text notice retained in the unmodified external file'},
            'catalogue': {'path': str(CATALOGUE.relative_to(ROOT)), 'sha256': sha(catalogue_raw)}},
        'projection': {'id': 'nabt.lexical-headword-candidate-projection.v1',
            'source_unchanged': True, 'strip_initial_al_from_declared_headword': True,
            'ignored_candidate_marks': ['U+064B..U+0650','U+0652','U+0653'],
            'shadda_preserved': True, 'dagger_alif_preserved': True,
            'hamza_carriers_preserved': True,
            'notes': 'Projection proposes candidates only; short-vowel contrasts remain in every lemma and original witness. It does not certify vocalization or sense identity.'},
        'counts': counts, 'source_stem_tag_counts': dict(sorted(tag_counts.items())),
        'entries': entries, 'all_arabic_complete': False,
        'independent_human_adjudication': False,
        'denotation_loaded_from_lemma_match': False,
        'runtime_source_selection': 'Entire original QAC source; this diagnostic matrix does not filter the runtime reader.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    result=build(); target=HERE/'matrix.json'; content=wire(result)
    if a.check:
        if target.read_text()!=content: raise ValueError('Source matrix replay mismatch')
    else: target.write_text(content)
    print(json.dumps(result['counts'],ensure_ascii=False))
if __name__=='__main__': main()

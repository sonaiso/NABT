"""Pinned corpus premises -> native Lean reading sets. Never infer hidden classes.

Case_Mood is an independent annotated evaluation/training task. It does NOT
select the Lean reading set, and incompatible annotations remain in the audit.
The case names in estimated-marker annotations are erased before querying Lean.
"""
import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

from tools.arabic_training.data import ROOT, DATA_SHA256, read_source, sha

QATR_SHA256 = '2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d'
MARKS = {'الضمة':'damma', 'الفتحة':'fatha', 'الكسرة':'kasra', 'السكون':'sukun',
         'الواو':'waw', 'الألف':'alif', 'الياء':'ya', 'ثبوت النون':'nun_retained',
         'حذف النون':'nun_deleted', 'حذف حرف العلة':'weak_deleted',
         'ضمة مقدرة':'hidden', 'فتحة مقدرة':'hidden', 'الكسرة المقدرة':'hidden',
         'الفتحة (ممنوع من الصرف)':'fatha'}
CASES = {'مرفوع':'raf', 'منصوب':'nasb', 'مجرور':'jarr', 'مجزوم':'jazm'}


def premises(row):
    """No Case_Mood, syntactic role, surface suffix or inferred class enters here."""
    if row['Invariable_Declinable'] != 'معرب':
        return None, 'DECLINABILITY_NOT_ESTABLISHED'
    tag = row['Morph_tag']
    if tag in {'IV', 'IV_PASS'}:
        kind = 'verb'
    elif tag.startswith(('NOUN', 'ADJ', 'GERUND')):
        kind = 'noun'
    else:
        return None, 'KIND_OUTSIDE_SCOPED_MAPPING'
    mark = MARKS.get(row['Case_Mood_Marker'])
    if mark is None:
        return None, 'SIGN_UNRESOLVED'
    return dict(kind=kind, mark=mark, classes=None, proposed=None), None


def export_teacher(executable):
    raw = subprocess.run([str(Path(executable).resolve()), '--export'],
                         capture_output=True, check=True, timeout=120).stdout
    table = json.loads(raw)
    source = (ROOT/'src/nabt/data/source_evidence/qatr.txt').read_bytes()
    if sha(source) != QATR_SHA256 or table['source_sha256'] != QATR_SHA256:
        raise ValueError('Qatr source identity mismatch')
    if table['law_id'] != 'nabt.qatr-reading.v1' or len(table['rows']) != 45:
        raise ValueError('unexpected Lean teacher domain')
    return table


def index_teacher(table):
    return {q['kind']+':'+q['mark']:q for q in table['queries']}


def prepare(path, teacher):
    examples, intake, old_conflicts = read_source(path)
    # Preserve the existing source-disjoint development split. Its test fold
    # was already observed in PR25, so this is a regression evaluation, not blind.
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        rows = {n:r for n,r in enumerate(csv.DictReader(stream), 2)}
    lookup = index_teacher(teacher)
    exclusions, conflicts = Counter(), []
    for example in examples:
        for word in example['words']:
            word['qatr'] = None
            word['case'] = None
            stems = [rows[n] for n in word['csv_rows'] if rows[n]['Morph_type']=='Stem']
            # Structural/source intake exclusions only; do not use Case_Mood to
            # exclude a contradiction from the new Qatr evaluation denominator.
            structural = set(word['excluded_reasons']) - {
                'VERB_HAS_NO_GENITIVE', 'NOUN_HAS_NO_JUSSIVE', 'PAST_AND_IMPERATIVE_ARE_BUILT'}
            if structural or len(stems)!=1:
                exclusions['SOURCE_STRUCTURE_OR_TEXT'] += 1
                continue
            row = stems[0]
            query, reason = premises(row)
            if reason:
                exclusions[reason] += 1
                continue
            label = query['kind']+':'+query['mark']
            if not lookup[label]['rows']:
                exclusions['NO_SUPPORTED_READING'] += 1
                conflicts.append(dict(address=word['address'], csv_rows=word['csv_rows'],
                                      query=query, reason='NO_SUPPORTED_READING'))
                continue
            word['qatr'] = label
            word['case'] = CASES.get(row['Case_Mood'])
            if word['case'] is not None and word['case'] not in lookup[label]['cases']:
                conflicts.append(dict(address=word['address'], csv_rows=word['csv_rows'],
                                      query=query, annotated_case=word['case'],
                                      reason='ANNOTATED_CASE_OUTSIDE_CONDITIONAL_READINGS'))
    counts={s:dict(verses=sum(e['split']==s for e in examples),
                   words=sum(len(e['words']) for e in examples if e['split']==s),
                   supervised=sum(w['qatr'] is not None for e in examples if e['split']==s for w in e['words']),
                   labels=dict(Counter(w['qatr'] for e in examples if e['split']==s for w in e['words'] if w['qatr'])))
            for s in ('train','dev','test')}
    return examples, dict(source_sha256=DATA_SHA256, qatr_sha256=QATR_SHA256,
                          existing_split=intake, splits=counts, exclusions=dict(exclusions),
                          conflicts=conflicts, test_status='OBSERVED_REGRESSION_NOT_BLIND',
                          input_columns=['Word','same-verse Word context'],
                          teacher_premises=['Morph_tag','Invariable_Declinable','Case_Mood_Marker'],
                          teacher_never_reads=['Case_Mood','Syntactic_Role','Possessive_Construct'],
                          hidden_classes=None, authority='NONE', world_truth_established=False)


def native_checks(executable, requests):
    payload=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests)
    run=subprocess.run([str(Path(executable).resolve())], input=payload, text=True,
                       capture_output=True, check=True, timeout=120)
    replies=[json.loads(line) for line in run.stdout.splitlines()]
    if len(replies)!=len(requests):
        raise ValueError('native reply denominator mismatch')
    return replies

#!/usr/bin/env python3
"""Review saved measurements only. Never execute a NABT prediction or rescore gold."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CURRENT = ROOT / 'evidence/arabic_completion_v3/strict_review_v2'
FIRST = ROOT / 'evidence/arabic_completion_v3/strict_attempt_v1'
OLD_POLICY = ROOT / 'evidence/arabic_coverage/regression_policy_v1.json'


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def load(path):
    def unique(items):
        result = {}
        for key, value in items:
            assert key not in result, ('duplicate JSON key', key)
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def receipt(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha256(data).hexdigest()}


def identity(row, suite):
    if suite == 'construction' and 'model_summary' in row:
        return {'kind': 'model', 'id': None}
    if 'model_profile' in row:
        return {'kind': 'profile', 'profile': row['model_profile']}
    if 'variant' in row:
        return {'kind': 'variant', 'id': row['id'], 'variant': row['variant']}
    return {'kind': 'case', 'id': row['id']}


def claim_view(value):
    return {key: value[key] for key in ('predicate', 'predicate_kind', 'args', 'positive',
            'tense', 'time', 'place', 'restriction', 'voice') if key in value}


def observations(report, questions):
    if not report or 'clauses' not in report:
        return {'report_status': (report or {}).get('status'), 'non_discourse_result': report}
    clauses = []
    for clause in report['clauses']:
        viable = [a for a in clause['analyses'] if not a.get('rejected_candidate')]
        refs = [{key: ref.get(key) for key in ('surface', 'origin', 'candidate_entity_ids',
                'bound_entity_id', 'source_prefix_complete', 'profile')}
                for analysis in viable for ref in analysis['references']]
        refs = [json.loads(x) for x in sorted({wire(ref) for ref in refs})]
        clauses.append({'status': clause['status'], 'obligations': clause['obligations'],
            'analysis_count': len(clause['analyses']), 'viable_analysis_count': len(viable),
            'viable_obligations': sorted({o for a in viable for o in a.get('obligations', [])}),
            'references': refs})
    occurrences = []
    for occurrence in report['occurrences']:
        reading_summaries = []
        for row in occurrence['readings']:
            features = {key: row.get('lexical_features', {}).get(key) for key in
                        ('pos', 'lemma', 'root', 'person', 'gender', 'number', 'aspect', 'voice')}
            item = {key: row.get(key) for key in ('kind', 'variant', 'stem_surface',
                    'construction', 'construction_basis', 'class_candidates', 'obligations')}
            item['lexical_features'] = features
            if 'person_evidence' in row:
                person = row['person_evidence']
                item['person_evidence'] = {key: person.get(key) for key in ('form_kind',
                    'host_form', 'host_variant', 'segmentation_licensed', 'obligations')}
                item['person_evidence']['valency_witness_count'] = len(person.get('valency_witnesses', []))
            reading_summaries.append(item)
        occurrences.append({'surface': occurrence['surface'], 'reading_count': len(occurrence['readings']),
            'reading_summaries': [json.loads(x) for x in sorted({wire(x) for x in reading_summaries})]})
    answers = []
    for index, question in enumerate(questions):
        answer, inquiry = question.get('answer') or {}, question.get('inquiry') or {}
        answers.append({'index': index, 'question_text': answer.get('question_text'),
            'status': answer.get('status'), 'bindings': answer.get('bindings'),
            'proof_count': len(answer.get('proofs', [])),
            'counterproof_count': len(answer.get('counterproofs', [])),
            'verification_valid': question.get('verification', {}).get('valid'),
            'missing_premises': answer.get('missing_premises'),
            'inquiry_status': inquiry.get('status'),
            'inquiry_obligations': sorted({o for c in inquiry.get('clauses', [])
                for o in c.get('obligations', [])})})
    return {'report_status': report['status'], 'world_truth': report.get('world_truth'),
            'claim_count': len(report['claims']), 'claims': [claim_view(c) for c in report['claims']],
            'clauses': clauses, 'occurrences': occurrences, 'questions': answers}


def journal(path, report, policy, suite, inspect_ids=()):
    compressed = path.read_bytes()
    assert sha256(compressed).hexdigest() == report['raw_log']['sha256']
    decoded = gzip.decompress(compressed)  # Forces trailer/EOF/CRC verification.
    assert decoded.endswith(b'\n')
    lines = decoded.splitlines(keepends=True)
    scores = {c['id']: c for c in report['cases']}
    ids, records, reports, answers, selected = [], [], {}, {}, {}
    for index, line in enumerate(lines):
        row = json.loads(line)
        assert line == wire(row) + b'\n', ('noncanonical raw record', path, index)
        rid = identity(row, suite)
        ids.append(rid)
        rec = {'bytes': len(line), 'sha256': sha256(line).hexdigest()}
        if suite == 'construction':
            rec.update(index=index, kind=rid['kind'], id=rid.get('id'))
        else:
            rec['identity'] = rid
        records.append(rec)
        if rid['kind'] != 'case':
            continue
        case_id = row['id']
        assert case_id not in reports
        score = scores[case_id]
        # The discourse writer appends elapsed seconds to the final score
        # after journaling. Every substantive field remains exactly bound.
        if suite == 'discourse':
            assert 'seconds' in score and 'seconds' not in row['score']
            score = {key: value for key, value in score.items() if key != 'seconds'}
        assert wire(row['score']) == wire(score), ('raw score mismatch', case_id)
        reports[case_id] = sha256(wire(row.get('report'))).hexdigest()
        answers[case_id] = [sha256(wire(q.get('answer'))).hexdigest() for q in row.get('questions', [])]
        if case_id in inspect_ids:
            selected[case_id] = {'raw_record_index': index, 'raw_record_sha256': rec['sha256'],
                'observations': observations(row.get('report'), row.get('questions', []))}
    assert ids == policy['raw_record_identities'], ('raw identity inventory', suite)
    assert list(reports) == [c['id'] for c in report['cases']]
    assert sum(map(len, answers.values())) == policy['question_total']
    saved = report['raw_log'].get('record_inventory', report['raw_log'].get('records'))
    assert wire(saved) == wire(records), ('raw receipt ledger', suite)
    assert report['raw_log']['record_count'] == len(records)
    size_key, hash_key = ('decoded_bytes', 'decoded_sha256') if suite == 'construction' else ('uncompressed_bytes', 'uncompressed_sha256')
    assert report['raw_log'][size_key] == len(decoded)
    assert report['raw_log'][hash_key] == sha256(decoded).hexdigest()
    return {'file': receipt(path), 'decoded_bytes': len(decoded),
        'decoded_sha256': sha256(decoded).hexdigest(), 'record_count': len(records),
        'case_count': len(reports), 'question_count': sum(map(len, answers.values())),
        'ordered_raw_identities_equal_to_pr17_policy': True,
        'all_raw_substantive_scores_equal_to_saved_report': True,
        'excluded_score_timing_metadata': ['seconds'] if suite == 'discourse' else [],
        'complete_gzip_crc_eof_verified': True,
        'all_canonical_jsonl_record_receipts_verified': True}, selected, reports, answers


GAPS = {
 'CON-Z07': ('مقدمة دلالية غير محسومة', 'يحفظ علم معنى المعرفة ومعنى الإسناد القلبي؛ لا يوجد في المدخل شاهد مستقل يختار الإطار ذا المفعولين. لا يصلح الشكل المتعدي المتوقع في gold شاهدًا على المعنى.'),
 'CON-Z10': ('حد ترخيص السؤال، لا إخفاق الخبر', 'الخبر المنفي مرخص ويحفظ نفي الاعتقاد دون نفي الصفة المضمنة. البقية في سؤال هل ما ظن فقط: NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE. يلزم ترخيص مستقل لهذه الصيغة ضمن الملف اللغوي أو إعادة تقييم مستقلة لصيغة السؤال؛ لم يتغير gold.'),
 'CON-M01': ('إطار نسبة غير منقول إلى القارئ', 'الفعل والأسماء لها قراءات صرفية في الخام، لكن ازداد ليس ضمن nisba_frames المنفذة؛ لا توجد قراءة جملة مكتملة. الشاهد النصي ازداد نشاطا محفوظ في بحث المصادر، ولم يتحول بعد إلى جسر موثق يختار دور التمييز ومالكه لكل هدف.'),
 'CON-M03': ('شاهد وحدة/إطار تمييز ناقص', 'امتلأ داخل إطار عام مشهود، لكن لبنا غير موجودة في أزواج verb/unit المنفذة؛ يبقى TAMYIZ_VERSUS_OTHER_NOMINAL_USE_REQUIRES_SOURCE_FRAME. وجود شواهد استعمال امتلأ ضرعها لبنا في البحث لا يكفي وحده لإثبات تطبيق الدور على الكأس في الهدف.'),
 'DSC-P03': ('عدد/تصريف راضية', 'العدد في القراءة المصدرية لراضية غير معلوم، وبناء N غير مكتمل؛ قالب ADJ ذي شدة الإدغام لا يطابق قالب N مباشرة. لا يجوز ملء العدد أو حذف الشدة كي يعمل الجسر الجديد.'),
 'DSC-P08': ('عدد/تصريف راضية ثم إحالة', 'عدم اكتمال راضية يمنع اكتمال السابقة التي يطلبها ربط هي؛ المطلوب شاهد العدد/التصريف أولًا ثم إحالة من سابقة مكتملة، لا اختيار المرجع المتوقع مباشرة.'),
 'DSC-P09': ('مقدمة سابقة غير مكتملة', 'قراءة نوف راضية غير مكتملة بمشكلتي العدد/التصريف؛ لذلك لا يجعل القارئ السابقة مغلقة لربط هو بحازم. ليست المسألة مجرد وجود اسم مذكر سابق.'),
 'DSC-P12': ('عدد/تصريف راضية', 'الإشارة مؤطرة، لكن راضية تفتقد شاهد اتفاق العدد والبناء في البديل الاسمي؛ لا يحل جسر N/ADJ هذه الفروق غير المتطابقة.'),
 'DSC-P13': ('صيغة اسم السياق المنصوبة', 'حازما بلا قراءة مؤهلة في occurrences؛ معرفة الاسم في السياق ليست شاهدًا مستقلًا لصيغته المنصوبة أو ألفها، فلا تكتمل جملة إن.'),
 'DSC-P14': ('تصريف اسم السياق في إطار الناسخ', 'حازم قراءة سياقية PN ذات construction=null وclasses=[]؛ الخبر حكيمًا مؤهل. يلزم شاهد مستقل للتصريف الذي يتطلبه إطار كان.'),
 'DSC-P15': ('تصريف اسم السياق في إطار الناسخ', 'حازم قراءة سياقية بلا شاهد البناء/الإعراب اللازم لإطار ليس؛ لا يجوز إسقاط CONSTRUCTION_EVIDENCE_REQUIRED أو ترقية عدم اكتمال القراءة إلى نفي قطعي.'),
 'DSC-P17': ('تصريف اسم السياق في نصف التعارض', 'الشق الموجب مرخص، والشق المنفي بليس يفتقد تصريف اسم السياق. لا يتولد CONFLICT قبل ترخيص الإسنادين بالفعل.'),
 'DSC-P26': ('عدد بيت وتصريف مضاف إليه سياقي', 'بيت معرب بشواهد حركة، لكن number=null؛ وحازمٍ السياقي construction=null. يلزم شاهد العدد لاتفاق الخبر وشاهد تصريف المضاف إليه، ولا يمثل غياب S في QAC افتراض المفرد.'),
 'DSC-P27': ('مضيف فعلي وصيغة مفعول سياقي', 'يوجد STEM للفعل أكرم، لكن لا قراءة person_evidence مؤهلة من مضيف كامل مستقل، وسهيلا بلا قراءة صرفية. يلزم جسر مصدر للمضيف ودليل صيغة المفعول؛ وجود الجذر أو توقع اسم المفعول لا يكفي.'),
 'DSC-P28': ('جسر المضيف واللاحقة', 'أكرمه لا ينتج قراءة مؤهلة رغم وجود شاهد QAC متصل؛ عقد الفصل الحالي يطلب مضيفًا كاملًا مستقلًا لربط اللاحقة. المطلوب جسر موثق لهذا الفصل ثم ربط الضمير، لا اختراع هوية ه من gold.'),
 'DSC-T04': ('استبعاد شاهد الصرف داخل القالب المباشر', 'بعد حجب83آية تبقى N ببصيرُ/بصيرِ وADJ ببصيرُ؛ القراءة المستهدفة في المجموعتين classes=[0,5]. لا تنوين طرفي مشهود داخل هذا القالب المباشر، فيمتنع جسر class0. توجد صيغ بصيرًا في الخام المتبقي، لكنها قالب ألف مستقل؛ يلزم جسر إضافي مبرر لنقل شاهدها، ولا يجوز تسريب الصيغة المحجوبة.'),
 'DSC-B05': ('اتفاق مجهول ثم سابقة غير مكتملة', 'كريم أصبح معربًا في كل القراءات المعنية، لكن جنس سهيل وعدده في السياق unknown؛ يبقى اتفاق خبره غير مؤهل ثم source_prefix_complete=false. هو يحتفظ بالمرشح h بلا ربط، بينما gold يطلب h,s. هذا ليس إثبات عدم توافق سهيل ولا إذنًا لملء صفاته.'),
 'DSC-B14': ('مراسلة صيغة الأمر في الوصل والابتداء/الوقف', 'اُدْخُلْ بلا قراءة في التقرير. الشاهد الخام من36:26:2:1 هو {doxuli، أي صورة وصل ذات كسرة نهائية؛ لا يوجد في هذا الملف جسر مؤهل إلى صيغة الهدف الساكنة. وجود باب الأمر والجذر لا يثبت هذا التحويل الكتابي/الصوتي تلقائيًا.'),
 'DSC-B15': ('صيغة اسم السياق المنصوبة', 'حازما بلا قراءة مؤهلة فلا تتكون قراءة كاملة تحفظ WISH في إطار ليت. البقية ليست تقريرًا بأن ليت لا تدل على التمني.'),
 'DSC-B16': ('صيغة اسم السياق المنصوبة', 'حازما بلا قراءة مؤهلة فلا تتكون قراءة كاملة تحفظ HOPE في إطار لعل. لا يعوض اسم السياق عن شاهد التصريف.'),
 'DSC-B19': ('تركيب النفي والعطف مع أسماء سياق', 'لا توجد قراءة جملة مكتملة؛ وَسُهَيْلٌ بلا قراءة مؤهلة وحازم السياقي بلا construction. تحسن كريم لا يكفي لتجاوز ربط الاسم المعطوف وإطار ليس ونطاقه.'),
 'DSC-B24': ('تصريف اسم السياق في إطار الناسخ', 'البقية في الحكم الماضي بكان بسبب شاهد تصريف حازم السياقي؛ تبقى القراءة DEFER ولا تصير حقيقة ماضية بمجرد وسم الزمن.'),
}

IMPROVEMENTS = {
 'CON-Z02': ('POSITIVE_COMPREHENSION', 'تعيين حسِب القلبية من حَسِبَ كاملة الحركات وشاهد مختار الصحاح والقراءة الخام؛ نجاح الإطار والسؤال مع منع إثبات الصفة المضمنة.'),
 'CON-N01': ('POSITIVE_COMPREHENSION', 'ربط الاسم المشدد بالاسم السياقي غير المشكول عبر قراءة مصدرية محددة، مع بقاء الهوية مشروطة بمقدمة التسمية ومعالجة النعت والسؤال.'),
 'DSC-P02': ('POSITIVE_COMPREHENSION', 'اكتمال قراءة كريم بعد جسر البناء الصرفي بين N/ADJ دون دمج الوسمين أو نقل ميزات مجهولة.'),
 'DSC-P18': ('POSITIVE_COMPREHENSION', 'اكتمال الإسنادين المنسقين الحكمة والكرم والسؤالين بعد تأهيل قراءة كريم المنافسة.'),
 'DSC-P25': ('POSITIVE_COMPREHENSION', 'اكتمال إسناد الكرم في السياق المؤلف مع حفظ قيود القراءة والشاهد.'),
 'DSC-T02': ('POSITIVE_COMPREHENSION', 'نجاح نقل نهاية محجوبة للفظ معلوم المصدر؛ بقي شاهد التنوين المستقل داخل مجموعتي كريم، وأصلح المدقق شرط العضوية الزائد. هذا ليس اختبار جذور جديدة أو corpus طبيعي جديدًا.'),
 'DSC-B04': ('AMBIGUITY_AND_ABSTENTION_PRESERVED', 'ترخيص المقدمتين الأوليين مع إبقاء هو بين h,s ومنع الاختيار بحسب القرب. الوثيقة والجواب النهائيان DEFER، ولا تسند الحكمة لأي منهما. نجاح هذه الحالة يتضمن فهم المقدمتين وحفظ الغموض، ولا يعني حسم الضمير.'),
}


def main():
    for name in ('review.json', 'review.md', 'strict1_erratum.json'):
        assert not (OUT / name).exists(), 'Refusing to overwrite ' + name
    policy = load(OLD_POLICY)
    inputs = [OLD_POLICY, Path(__file__).resolve(), ROOT / 'evidence/arabic_completion_v3/code_freeze_v1.json',
              ROOT / 'evidence/discourse/independent_source_inventory_v1.json']
    suites = {}
    for suite in ('construction', 'discourse'):
        prior = ROOT / policy['suites'][suite]['strict_measurement']
        current, first = CURRENT / (suite + '.json'), FIRST / (suite + '.json')
        material = ROOT / ('evidence/constructions' if suite == 'construction' else 'evidence/discourse') / 'independent_cases_v1.json'
        inputs += [prior, prior.with_suffix('.raw.jsonl.gz'), material, first, first.with_suffix('.raw.jsonl.gz')]
        inputs += [CURRENT / (suite + suffix) for suffix in ('.json', '.raw.jsonl.gz', '.code.tar.gz')]
        suites[suite] = (prior, current, first, material)
    inputs += [FIRST / 'attempt.json', ROOT / 'artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz']
    before = [receipt(p) for p in sorted(set(inputs))]
    result = {'schema': 'nabt.arabic-completion.independent-residual-review.v1',
        'reviewer': '/root/empirical_audit', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Comparison of existing complete strict measurements only; no new prediction execution or rescoring.',
        'base_commit': 'd791fd7730cde2256dfac8a27687010b392876b3', 'baseline_policy': receipt(OLD_POLICY),
        'runtime_freeze': receipt(ROOT / 'evidence/arabic_completion_v3/code_freeze_v1.json'),
        'suites': {}, 'remaining_cases': [], 'improved_cases': [], 'inputs_before': before}
    errata = {'schema': 'nabt.arabic-completion.strict1-checker-erratum.review.v1',
        'preserved_attempt': receipt(FIRST / 'attempt.json'), 'runtime_changed_between_attempts': False,
        'classification': 'CHECKER_FALSE_REJECTION_NOT_A_NEW_RUNTIME_UNSAFE_ACCEPTANCE',
        'explanation_ar': 'اشترط المدقق خطأً أن يكون شاهد التنوين ضمن أول شاهدَي عائلة حركة. أثر ذلك في DSC-T02 في التقرير والسؤال؛ لم تعدل درجات المحاولة الأولى. إصلاح التناقض في raw3MS تقوية إضافية للمدقق، لا تعديل runtime أو gold.',
        'before_review': 'evidence/arabic_completion_v3/source_review/independent_validator_review_v1/review.json',
        'after_review': 'evidence/arabic_completion_v3/source_review/independent_validator_review_v1/postreview.json',
        'suites': {}}
    for item in load(FIRST / 'attempt.json')['files']:
        assert receipt(ROOT / item['path']) == item
    for suite, (prior_path, current_path, first_path, material_path) in suites.items():
        old, new, first = load(prior_path), load(current_path), load(first_path)
        ref = policy['suites'][suite]
        assert receipt(prior_path)['sha256'] == ref['strict_measurement_sha256']
        assert old['passed'] == ref['observed_passed'] and old['total'] == ref['total']
        assert new['completed_at_utc'] and new['measurement_valid'] is True
        assert new['false_accept_count'] == new['false_accept_case_count'] == 0
        assert new['execution_errors'] == new['question_execution_errors'] == []
        if suite == 'construction': assert new['finalization_errors'] == []
        for key in ('runtime_freeze_sha256', 'runtime_snapshot_sha256', 'runtime_file_count'):
            assert new['snapshot'][key] == first['snapshot'][key]
        runtime_files = load(ROOT / 'evidence/arabic_completion_v3/code_freeze_v1.json')['files']
        first_files = {row['path']: row for row in first['snapshot']['files']}
        new_files = {row['path']: row for row in new['snapshot']['files']}
        assert all(first_files.get(row['path']) == new_files.get(row['path']) == row for row in runtime_files)
        changed_measured_files = [path for path in sorted(first_files.keys() | new_files.keys())
                                  if first_files.get(path) != new_files.get(path)]
        assert new['snapshot']['runtime_freeze_sha256'] == result['runtime_freeze']['sha256']
        assert all(new[k] == old[k] == ref[k] for k in ('gold_freeze_sha256', 'source_sha256'))
        assert [c['id'] for c in old['cases']] == [c['id'] for c in new['cases']] == [c['id'] for c in ref['cases']]
        gold = {c['id']: c for c in load(material_path)['cases']}
        ledger, failures, regressions, changed_signatures, improved = [], [], [], [], []
        for a, b, p in zip(old['cases'], new['cases'], ref['cases']):
            assert len({c['check'] for c in b['checks']}) == len(b['checks'])
            assert [c['check'] for c in a['checks']] == [c['check'] for c in b['checks']] == p['checks']
            assert wire(a['failures']) == wire(p['allowed_failures'])
            assert all(type(c['passed']) is bool for c in b['checks'])
            assert b['passed'] is (not b['failures']) and b['false_accepts'] == []
            assert [c['check'] for c in b['checks'] if not c['passed']] == [f['check'] for f in b['failures']]
            fixed = [y['check'] for x, y in zip(a['checks'], b['checks']) if not x['passed'] and y['passed']]
            reg = [y['check'] for x, y in zip(a['checks'], b['checks']) if x['passed'] and not y['passed']]
            fresh = [f for f in b['failures'] if wire(f) not in {wire(f) for f in a['failures']}]
            regressions += [{'id': b['id'], 'check': check} for check in reg]
            changed_signatures += [{'id': b['id'], 'failure': f} for f in fresh]
            ledger.append({'id': b['id'], 'previous_passed': a['passed'], 'current_passed': b['passed'],
                'ordered_checks': p['checks'], 'improved_checks': fixed, 'regressed_checks': reg,
                'remaining_failure_payloads': b['failures'], 'all_failure_payloads_equal_to_pr17_debt': not fresh})
            if not b['passed']: failures.append(b['id'])
            if b['passed'] and not a['passed']: improved.append(b['id'])
        assert not regressions and not changed_signatures
        assert sum(c['passed'] for c in new['cases']) == new['passed']
        assert new['strict_pass'] is False and new['passed'] < new['total']
        assert set(failures) <= set(GAPS) and set(improved) <= set(IMPROVEMENTS)
        raw, inspected, current_hashes, current_answers = journal(current_path.with_suffix('.raw.jsonl.gz'), new, ref, suite, failures + improved)
        old_raw, _, _, _ = journal(prior_path.with_suffix('.raw.jsonl.gz'), old, ref, suite)
        # First-attempt question inventory is complete even though one stored
        # answer is an exception; keep the recorded error, never rewrite it.
        first_raw, _, first_hashes, first_answers = journal(first_path.with_suffix('.raw.jsonl.gz'), first, ref, suite)
        assert current_hashes == first_hashes, 'Runtime document reports changed between checker attempts'
        answer_changes = [case for case in current_answers if current_answers[case] != first_answers[case]]
        if suite == 'construction': assert not answer_changes
        else: assert answer_changes == ['DSC-T02']
        summary = {'baseline': receipt(prior_path), 'current': receipt(current_path),
            'baseline_passed_cases': old['passed'], 'passed_cases': new['passed'], 'case_total': new['total'],
            'baseline_failed_case_count': old['total'] - old['passed'], 'remaining_failed_case_count': len(failures),
            'check_total': sum(len(c['checks']) for c in new['cases']),
            'baseline_failed_check_count': sum(len(c['failures']) for c in old['cases']),
            'remaining_failed_check_count': sum(len(c['failures']) for c in new['cases']),
            'improved_check_count': sum(len(c['improved_checks']) for c in ledger),
            'question_total': ref['question_total'], 'false_accept_count': 0,
            'measurement_valid': True, 'strict_pass': False, 'case_improvements': improved,
            'remaining_case_ids': failures, 'case_regressions': [], 'check_regressions': regressions,
            'new_failure_signatures': changed_signatures, 'complete_ordered_case_check_inventory_equal': True,
            'gold_and_raw_lexical_source_hashes_equal_to_pr17': True,
            'raw': raw, 'baseline_raw': old_raw, 'complete_case_check_ledger': ledger}
        result['suites'][suite] = summary
        for cid in failures:
            label, missing = GAPS[cid]
            result['remaining_cases'].append({'suite': suite, 'id': cid, 'text': gold[cid]['input']['text'],
                'failure_category_ar': label, 'missing_witness_or_bridge_ar': missing,
                'failed_checks': next(c['remaining_failure_payloads'] for c in ledger if c['id'] == cid),
                **inspected[cid]})
        for cid in improved:
            category, explanation = IMPROVEMENTS[cid]
            result['improved_cases'].append({'suite': suite, 'id': cid, 'text': gold[cid]['input']['text'],
                'classification': category, 'explanation_ar': explanation, **inspected[cid]})
        errata['suites'][suite] = {'first_report': receipt(first_path), 'first_passed': first['passed'],
            'first_false_accept_count_as_recorded': first['false_accept_count'],
            'first_question_execution_errors': first['question_execution_errors'],
            'current_report': receipt(current_path), 'current_passed': new['passed'],
            'runtime_snapshot_identical': True, 'all_document_report_payloads_identical': True,
            'changed_nonruntime_measured_files': changed_measured_files,
            'changed_stored_answer_cases': answer_changes, 'first_raw_integrity': first_raw}
        assert receipt(CURRENT / new['code_archive']['filename'])['sha256'] == new['code_archive']['sha256']
    # Independently inspect the surviving raw source, without compiling it.
    qac_path = ROOT / 'artifacts/local/external/quranic-corpus-morphology-0.4.txt.gz'
    qac = gzip.decompress(qac_path.read_bytes())
    assert sha256(qac).hexdigest() == 'a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46'
    source_inventory = load(ROOT / 'evidence/discourse/independent_source_inventory_v1.json')
    excluded = {tuple(x) for x in source_inventory['profiles']['qac_form_holdout']['excluded_verses']}
    source_audit, imperative = {}, []
    for line in qac.decode().splitlines():
        if not line.startswith('('): continue
        loc, form, tag, feature_string = line.split('\t')
        tokens = feature_string.split('|'); address = tuple(map(int, loc.strip('()').split(':')))
        if 'LEM:baSiyr' in tokens and tag in ('N', 'ADJ'):
            bucket = source_audit.setdefault(tag, {'retained_forms': Counter(), 'excluded_forms': Counter(),
                'retained_bare_terminal_tanwin_rows': [], 'excluded_bare_terminal_tanwin_rows': []})
            retained = address[:2] not in excluded
            bucket['retained_forms' if retained else 'excluded_forms'][form] += 1
            if re.sub(r'[\[\]]+$', '', form).endswith(('F', 'N', 'K')):
                bucket['retained_bare_terminal_tanwin_rows' if retained else 'excluded_bare_terminal_tanwin_rows'].append({'locator': loc, 'form': form})
        if 'ROOT:dxl' in tokens and 'IMPV' in tokens and '2MS' in tokens and 'LEM:daxala' in tokens:
            imperative.append({'locator': loc, 'form': form, 'tokens': tokens})
    result['raw_source_boundary_checks'] = {'decoded_qac_sha256': sha256(qac).hexdigest(),
        'excluded_verse_count': len(excluded), 'basir_by_pos': source_audit,
        'basir_scope_note_ar': 'فارغ هنا يعني غياب التنوين الطرفي في القالب بلا ألف، لا غياب بصيرًا ذات ألف النصب؛ صيغها الباقية مذكورة صراحة في retained_forms.',
        'retained_form_I_imperative_2MS_dakhala': imperative}
    result['interpretation_limits_ar'] = [
        'نجاح الحالة يعني اجتياز جميع فحوصها المحددة؛ بعض الحالات تتوقع امتناعًا أو حفظ الغموض، وليس كل نجاح حكمًا موجبًا.',
        'المادة الأصلية لم تتغير؛ التركيبات تستخدم مقدمات معجمية مؤلفة، والخطاب حلقات مؤلفة بمفردات QAC الموسومة وسياق مصرح به.',
        'التحسينات طورت بعد الاطلاع على إخفاقات PR17. ليست هذه إعادة القياس اختبارًا أعمى جديدًا، ولا تخص نتائج المصفوفة الجديدة ذات24حالة.',
        'التغطية الصارمة ما زالت غير مكتملة في المجموعتين. جواز بوابة انحدار ببقية موثقة لا يجعل الفشل نجاحًا.',
        'الشواهد المقترحة لازداد نشاطا وامتلأ لبنا بقيت بحثًا مصدريًا؛ لم تدخل runtime ولم تملأ توقعات gold.',
        'لا تثبت هذه المقارنة صواب جميع العربية أو اكتساب المعجم الكامل أو صدق الوقائع الخارجية أو تنقيح Python إلى Lean.']
    result['strict1_erratum'] = 'strict1_erratum.json'
    after = [receipt(ROOT / item['path']) for item in before]
    assert after == before
    result['inputs_after'] = after
    result['reviewed_input_bytes_unchanged'] = True
    result['review_status'] = 'COMPLETE_NO_REGRESSION_NO_NEW_FAILURE_SIGNATURE'
    for name, value in (('strict1_erratum.json', errata), ('review.json', result)):
        with (OUT / name).open('x', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2); f.write('\n')
    paragraphs = ['# مراجعة البقية والتغطية بعد PR17\n',
        'اكتملت مراجعة التقريرين الصارمين في الإعادة الثانية. **لا تراجع لأي حالة أو فحص كان ناجحًا في PR17، ولا بصمة إخفاق جديدة خارج البقية السابقة.** بقيت التغطية غير مكتملة، مع عدم تسجيل قبول غير آمن في هذه المصفوفتين.\n',
        '## الأرقام ومعنى المقام\n',
        '| المجال | الحالات سابقًا | الحالات الآن | الفحوص سابقًا | الفحوص الآن | الأسئلة المنفذة | القبول غير الآمن الآن |\n|---|---:|---:|---:|---:|---:|---:|']
    for suite, label in (('construction', 'التركيبات'), ('discourse', 'الخطاب')):
        s = result['suites'][suite]
        paragraphs.append(f"| {label} | {s['baseline_passed_cases']}/{s['case_total']} | {s['passed_cases']}/{s['case_total']} | {s['check_total']-s['baseline_failed_check_count']}/{s['check_total']} | {s['check_total']-s['remaining_failed_check_count']}/{s['check_total']} | {s['question_total']} | 0 |")
    paragraphs += ['\nالحالة ناجحة فقط إذا نجحت جميع فحوصها. بقي **4 حالات/30 فحصًا** في التركيبات و**18 حالة/38 فحصًا** في الخطاب. تحسن16فحصًا و12فحصًا على الترتيب. جرد كل الحالات والفحوص وترتيبها مطابق للمحفوظ، وجميع حمولة الإخفاقات الباقية مساوية حرفيًا لدين PR17؛ لم تستبدل حمولة قديمة بأخرى أخف.\n',
        'تحققت المراجعة كذلك من اكتمال gzip وCRC وEOF، ومن كل سطر JSONL القانوني وبصمته، ومساواة درجات الخام مع التقرير:87سجلًا للتركيبات و90للخطاب. اكتمل تنفيذ106سؤالًا و74سؤالًا؛ لا أخطاء تنفيذ أو أسئلة في الإعادة الثانية. التفاصيل المربوطة ببصمات الملفات في [review.json](review.json).\n',
        '## ما تحسن، وما نوع النجاح؟\n',
        '| الحالة | النوع | الدلالة المحدودة |\n|---|---|---|']
    for c in result['improved_cases']:
        kind = 'فهم موجب ضمن الملف' if c['classification'] == 'POSITIVE_COMPREHENSION' else 'حفظ الغموض والامتناع'
        paragraphs.append(f"| {c['id']} | {kind} | {c['explanation_ar']} |")
    paragraphs += ['\nإذن التحسن في التركيبات حالتان موجبتان، وفي الخطاب أربع حالات موجبة وحالة حدودية واحدة. في **DSC-B04** أصبح الإسنادان الأولان مرخصين، وبقي ضمير «هو» بين حازم وسهيل دون ربط؛ الوثيقة والسؤال النهائيان `DEFER`، مع منع نسبة الحكمة إلى أي منهما. لا يصح عرض هذا النجاح على أنه حسم للضمير.\n',
        '## البقية: المخرجات الخام والمقدمة الناقصة\n',
        'الرموز التالية من التقرير الخام نفسه. إذا لم ينتج تحليلًا، فـ`COMPLETE_SUPPORTED_CLAUSE_READING` يسجل هذا الحد؛ لا نخترع له تعليقًا أدق لم يصدر. تفسير الشاهد الناقص في العمود الأخير استنتاج مراجعة من القراءات والمصادر المثبتة.\n',
        '| الحالة | التعليقات الفعلية على مستوى الجمل/البدائل | الشاهد أو الجسر الناقص |\n|---|---|---|']
    for c in result['remaining_cases']:
        obs = c['observations']
        obligations = sorted({o for clause in obs.get('clauses', []) for o in clause['obligations']} |
                             {o for q in obs.get('questions', []) for o in q['inquiry_obligations']})
        codes = '، '.join('`'+o+'`' for o in obligations) or 'لا تحليل مكتمل'
        paragraphs.append(f"| {c['id']} | {codes} | {c['missing_witness_or_bridge_ar']} |")
    paragraphs += ['\n### T04: غياب محدد داخل القالب، لا نفي وجود التنوين في المصدر كله\n',
        'في الملف المحجوب استبعدت83آية. بقي لبصير تحت N أربع مشاهدات `baSiyru` وواحدة `baSiyri`، وتحت ADJ أربع مشاهدات `baSiyru`. حُجبت جميع صيغ `baSiyrN` ذات الصلة، فظلت قراءات القالب المباشر `[0,5]`، وامتنع الجسر الذي يشترط `[0]` مستقلة في الطرفين. في المقابل بقيت7صيغ `baSiyrFA` تحت N و7تحت ADJ، وصيغة `baSiyrF[A` إضافية تحت ADJ: هذه تنوينات نصب مع ألف، وقالبها مختلف في النظام الحالي. الانتقال منها إلى حكم الصرف للقالب بلا ألف يحتاج جسرًا مستقلاً؛ لا نعالج الفشل بإعادة الشاهد المحجوب إلى التدريب.\n',
        '### B05: جهل الاتفاق يمنع اكتمال السابقة\n',
        'مصدر كريم الصرفي مؤهل الآن. لكن سياق سهيل يصرح بأن الجنس والعدد مجهولان؛ فتظل جملته غير مكتملة بالرمز `PREDICATE_AGREEMENT_EVIDENCE_REQUIRED`. لذلك يسجل الضمير `source_prefix_complete=false` ومرشحًا سابقًا واحدًا `h` دون ربط، بينما gold يطلب `[h,s]`. البقية ما زالت فشلًا في شرط حفظ مجموعة المرشحين المطلوبة، وليست دليلاً أن سهيل غير متوافق ولا مبررًا لملء صفاته من الجواب.\n',
        '## تصويب المدقق في المحاولة الأولى\n',
        'حُفظت المحاولة الأولى دون تعديل: التركيبات82/86، والخطاب67/86 مع إنذار قبول غير آمن واحد وخطأ سؤال واحد مسجلين. كان السبب شرطًا زائدًا في المدقق: إلزام شاهد التنوين بعضوية أول شاهدَي عائلة حركة. تأثرت DSC-T02 في التقرير والسؤال. عالج التصحيح المدقق وحده؛ لم يغير runtime أو gold. بعده أصبحت68/86 بلا الإنذار أو خطأ السؤال.\n',
        'تحققت هذه المراجعة من تطابق runtime snapshot ومن **تطابق حمولة تقارير الوثائق الـ86 كاملة** بين المحاولتين في كل مجال. تغير سجل الجواب المحفوظ في DSC-T02 فقط من استثناء مدقق إلى الجواب المكتمل. لم تُعد كتابة الدرجة الأولى، ولم يُحذف الإنذار من تاريخها. يوجد السجل المنفصل في [strict1_erratum.json](strict1_erratum.json)، والمادة الأصلية في [strict_attempt_v1](../strict_attempt_v1/attempt.json). تقوية رفض ملفات الشخص المتناقضة في حَسِبَ إصلاح آخر للمدقق، ولا تمثل تحسينًا إضافيًا في عدد حالات runtime.\n',
        '## حدود الاستنتاج\n']
    paragraphs += ['- '+item for item in result['interpretation_limits_ar']]
    paragraphs += ['\n## المراجع القابلة لإعادة الفحص\n',
        '- [التركيبات الحالية](../strict_review_v2/construction.json) و[خامها](../strict_review_v2/construction.raw.jsonl.gz).',
        '- [الخطاب الحالي](../strict_review_v2/discourse.json) و[خامه](../strict_review_v2/discourse.raw.jsonl.gz).',
        '- [سياسة PR17](../../arabic_coverage/regression_policy_v1.json)، وتتضمن مسارات التقريرين السابقين وبصماتهما والجرد الكامل للدين.',
        '- [بحث أطر التمييز المقترحة](../source_review/tamyiz_frame_source_review_v1.json)؛ بقي خارج runtime في هذا الإصدار.',
        '- [مراجعة حدود الجسر الاسمي وحَسِبَ](../source_review/nominal_bridge_and_hasiba_language_review_v1.json).',
        '\nهذه مراجعة لقياسات محفوظة. لم تشغّل تنبؤًا جديدًا أو wheel أو الحالات الأصلية مرة أخرى. جميع مدخلات المراجعة بقيت مطابقة في البداية والنهاية، والبصمات الكاملة محفوظة في JSON.']
    with (OUT / 'review.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(paragraphs) + '\n')
    print(json.dumps({'status': result['review_status'], 'files': [receipt(OUT / name) for name in
          ('review.json', 'review.md', 'strict1_erratum.json')]}, ensure_ascii=False))


if __name__ == '__main__':
    main()

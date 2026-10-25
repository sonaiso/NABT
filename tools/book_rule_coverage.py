#!/usr/bin/env python3
"""Replay complete *available byte streams*, without claiming whole-book rules.

The installed policy fixes the six source identities independently of a proposed
index. Headers/page markers are retrieval aids, never a rule inventory. Every
body segment remains unadjudicated even when a selected law overlaps it. This
tool is audit metadata and grants no runtime language or source authority.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = ROOT / "src/nabt/data/source_evidence"
INVENTORY_SHA256 = "6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d"
BASELINE_CROSSWALK_SHA256 = "f7e560c4ecb446d01980282ffc41dcdfa2a2f2383cd4e777b63f72e800c7c19e"
DEFAULT_OUTPUT = ROOT / "evidence/arabic_completion_v6/books/book_source_index_v1.json"
POLICY = "nabt.book-rule-coverage.v1"
AUTHORITY = "AUDIT_METADATA_NOT_RUNTIME_LICENSING_AUTHORITY"
GATE_OBLIGATIONS = (
    "physical_edition_extent_and_transcription_collation",
    "independent_semantic_rule_inventory_for_every_body_segment",
    "explicit_disputes_exceptions_dialects_and_attribution",
    "source_to_Lean_translation_fidelity_adjudication",
    "kernel_checked_soundness_and_completeness_for_each_rule_domain",
    "runtime_refinement_and_premise_acquisition",
    "independently_adjudicated_external_benchmark",
    "separate_argument_that_book_scope_exhausts_claimed_Arabic_domain",
)
# No complete-book closure evidence has been independently reviewed/installed.
# A future version must pin reviewed receipt identities here; input receipt IDs
# or success flags are never self-authenticating. Selected-rule proofs remain in
# their own crosswalk and cannot satisfy a whole-book receipt requirement.
INSTALLED_CLOSURE_RECEIPTS: dict[str, tuple[str, ...]] = {key: () for key in GATE_OBLIGATIONS}

SOURCES = {
    "qatr": "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d",
    "alfiyya": "13b351a0a02d9060fdedbb5db568544718eb4e89bef323f5572b8a26c0921ca0",
    "sibawayhi": "a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625",
    "sabban": "8b9e86da786cf65e7b32498b2524ee48a8dcf9f61b59e1bbc32b99ce7db5b396",
    "ibn_aqil": "661e43ea265eca8c72b9e4ab7a46cd9182b34e834105b595241bc7787b471f09",
    "mughni": "f37ac2bb4b273f59169053dd0ac2abf50a52846a7e87ddf689ee5c0b87f77e7d",
}
PAGE = re.compile(rb"PageV\d+P\d+")
MARKUP_HEADING = re.compile(r"^#+\s+\|+")
PROSE_HEADING = re.compile(r"^#\s+(?:(?:هذا\s+)?باب(?:\s|:)|الباب\s|فصل(?:\s|:))")

EXTENT_NOTES = {
    "qatr": ["Qatr matn, not its separate sharh; available ending contains hamzat al-wasl. Physical-edition collation is not certified."],
    "alfiyya": ["Concluding verses are present. A known ba/ya transcription discrepancy remains in the preserved bytes; conclusion presence is not text-integrity adjudication."],
    "sibawayhi": ["Available page markers reach V04P485. Header reports five volumes; this may include indices. Full edition collation is not established by metadata."],
    "sabban": ["Available text ends at V03P462 in the subjunctive-verb discussion. Later Alfiyya chapters are absent from this available text. A different four-volume edition must not be spliced silently into this one."],
    "ibn_aqil": ["The supplement beginning at line 9658 is explicitly by Muhammad Muhyi al-Din Abd al-Hamid, not Ibn Aqil. Earlier editorial material also requires passage-level attribution review."],
    "mughni": ["A concluding passage is present; repeated V00P000 markers are not distinct printed pages. Full edition collation remains unverified."],
}

# Authored after reading the entire 453-line Qatr matn. These are a work docket,
# not a claim to have atomized every semantic rule or exception. Consecutive
# spans include every byte after metadata, including page markers/preamble.
# (first line, last line, title, extraction obligations, existing narrow bridge)
QATR_DOCKET = [
    (38, 40, "التصدير والعلامات", ["تمييز التصدير من القواعد وعدم إسقاط بايتاته"], None),
    (41, 52, "الكلمة والاسم والمعرب والمبني", ["تعريف القول المفرد وحدود الكلمة", "علامات الاسم ومجال كفايتها", "المعرب والمبني والأمثلة ولهجات حذام وأمس", "حذف المضاف إليه ونية معناه"], ("Morphology", "singleton_observation_does_not_prove_built")),
    (53, 57, "الماضي", ["علامة تاء التأنيث الساكنة", "حركات البناء بحسب ضمير الفاعل", "نعم وبئس وعسى وليس والخلاف"], ("QatrRules", "past_attachment_matters")),
    (58, 63, "الأمر", ["الطلب وقبول ياء المخاطبة", "الصحيح والمعتل وحذف النون", "هلم التميمية وهات وتعال"], ("QatrReading", "imperative_exceptions")),
    (64, 69, "المضارع", ["اختبار لم وحروف نأيت", "حركة أوله بحسب عدد أصول الماضي وزوائده", "نون النسوة ونون التوكيد المباشرة وغير المباشرة"], ("Morphology", "verb_inflected_iff")),
    (70, 74, "الحرف والكلام", ["علامة الحرف السلبية وشروط استنفاد الاختبار", "الخلاف في مهما وإذما وما ولما", "الإفادة وحد الكلام وأقل ائتلافه"], None),
    (75, 91, "أنواع الإعراب وعلاماته", ["مجال الرفع والنصب والجر والجزم", "شروط الأسماء الستة والمثنى والجمع وملحقاتها", "ألف وتاء الجمع والممنوع من الصرف مع أل والإضافة", "الأمثلة الخمسة والمضارع المعتل"], ("QatrReading", "read_exact")),
    (92, 95, "الإعراب المقدر", ["المضاف لياء المتكلم والمقصور والمنقوص", "حركات المعتل الظاهرة والمقدرة", "منع استعمال الحركة المقدرة كأنها ملاحظة صوتية"], ("QatrReading", "estimated_erases_case")),
    (96, 99, "رفع المضارع ولن وكي وإذن", ["عدم الناصب والجازم مقدمة تحتاج إثباتا", "كي المصدرية", "صدرية إذن والاستقبال والاتصال واستثناء القسم"], ("Governors", "completeAlternatives_exact")),
    (100, 107, "أن الظاهرة والمضمرة", ["العلم والظن والخفيفة والمصدرية", "الإضمار الجائز والواجب وموانع الإضمار", "حتى المستقبلية وأو بمعنى إلى أو إلا"], ("Governors", "ambiguous_labels_retained")),
    (108, 114, "السببية والمعية وجواب الطلب والجوازم", ["النفي المحض والطلب الحقيقي", "فاء السببية وواو المعية وشروط أن", "جواب الطلب ومعيار إن لا في النهي", "لم ولما ولام الأمر ولا الطلبية"], ("Governors", "completeAlternatives_exact")),
    (115, 121, "الشرط والجواب", ["استنفاد أدوات الجزم المصرح بها", "تعيين فعل الشرط والجواب", "صلاحية الجواب وموجبات الفاء وإذا الفجائية"], None),
    (122, 128, "النكرة والمعرفة والضمير", ["الشيوع في الجنس الموجود والمقدر", "الشخص والحضور والاستتار الوجوبي والجوازي", "المتصل والمنفصل واستثناءات سلنيه وظننتكه وكنته"], ("PersonEvidence", "plain_ta_ambiguous")),
    (129, 131, "العلم", ["الشخصي والجنسي والاسم واللقب والكنية", "ترتيب اللقب وحكم الإفراد والإضافة"], None),
    (132, 136, "الإشارة", ["جميع صيغ الجنس والعدد وحالات المثنى", "الكاف واللام والبعد ولهجة المد", "ها التنبيه وموانع اللام"], None),
    (137, 143, "الموصول والصلة", ["الموصول الخاص والمشترك ولهجة طي", "صلة أل والصفة الصريحة غير التفضيل", "الجملة الخبرية والعائد وحذفه", "شبه الجملة والتعلق المحذوف"], ("DiscourseEvidence", "relative_requires_return")),
    (144, 151, "أل والإضافة والتعريف", ["خلاف أل واللام وإبدال الميم", "العهد والجنس والاستغراق للأفراد والصفات", "رتبة المضاف إلى المعارف والضمير"], None),
    (152, 168, "المبتدأ والخبر", ["الرفع ومسوغات الابتداء بالنكرة", "رابط الخبر الجملة واستثناء ضمير الشأن", "الظرف والتعلق والزمان والذات", "الوصف الساد مسد الخبر", "التعدد والتقديم والحذف ومواضع الوجوب"], ("ClassicalReferenceReadings", "dual_description_excludes_subject")),
    (169, 180, "كان وأخواتها", ["قائمة الأفعال والعمل والتوسط والتقدم", "التمام ومعنى صار واستثناءاتها", "زيادة كان وحذفها وحذف اسمها", "حذف نون يكن في الوصل وموانعه"], ("Governors", "distinct_nasikh_equations")),
    (181, 186, "ما ولا ولات", ["شروط إعمال ما الحجازية والموانع", "لا العاملة في الشعر والتنكير", "لات والحين وحذف أحد الجزأين"], ("Governors", "completeAlternatives_exact")),
    (187, 200, "إن وأخواتها", ["المعاني والعمل وما الكافة واستثناء ليت", "التخفيف والإهمال والإعمال وضمير الشأن", "فواصل أن وكأن", "توسط الخبر وكسر إن", "لام الابتداء والفارقة ومواضعها"], ("Governors", "inna_requires_both_slots")),
    (201, 207, "لا النافية للجنس", ["التنكير والاتصال والمضاف وشبهه", "بناء المفرد بحسب النوع والعدد", "استنفاد وجوه تكرار لا والنعت", "موانع الفتح عند الفصل وعدم الإفراد"], ("Governors", "alternatives_not_collapsed")),
    (208, 218, "ظن وأخواتها", ["تعيين المعنى القلبي والتعدية لمفعولين", "الإلغاء بعد المعمولين وبينهما", "التعليق بالنفي واللام والاستفهام"], ("Governors", "distinct_nasikh_equations")),
    (219, 239, "الفاعل", ["الرفع والترتيب وإفراد الفعل", "تأنيث الفعل الوجوبي والجوازي والشاذ", "مواضع حذف الفاعل وموانعه", "تقديم المفعول وتأخيره والإضمار واللبس", "فاعل نعم وبئس والمخصوص"], ("InflectionEvidence", "same_case_does_not_identify_relation")),
    (240, 245, "النائب عن الفاعل", ["حذف الفاعل وترتيب النيابة وشروط الظرف والمصدر", "صوغ الماضي والمضارع المبنيين للمجهول", "بدائل الأجوف والإشمام"], None),
    (246, 257, "الاشتغال", ["عامل النصب المحذوف وموقع الجملة", "مواضع ترجيح النصب ووجوبه ووجوب الرفع", "التكافؤ والاستثناءات الدلالية"], ("ClassicalReferenceReadings", "enumeration_exact")),
    (258, 266, "التنازع", ["عاملان ومعمول واحد بشروط المعنى", "بديل الكوفيين وبديل البصريين", "الإضمار الواجب واستثناء فساد المعنى"], None),
    (267, 273, "المفعول به والمنادى", ["العلاقة بالفعل ودور المفعول", "المنادى المضاف وشبهه والنكرة غير المقصودة", "بناء المفرد المعرفة والنكرة المقصودة"], ("ConstructionEvidence", "built_assignment_local")),
    (274, 276, "نداء المضاف لياء المتكلم", ["بدائل يا غلام وحركات الياء والألف", "يا أبت وأمت وابن أم وعم", "فصل الجائز والقبيح والضعيف"], None),
    (277, 280, "توابع المنادى", ["الإتباع على اللفظ أو المحل بحسب الإضافة وأل", "نعت أي والبدل والنسق المجرد", "بدائل يا زيد زيد اليعملات"], None),
    (281, 284, "الترخيم", ["حذف الآخر وشروط التعريف والعلمية والبناء والطول", "ذو التاء وغير ذي التاء", "حذف حرفين أو الجزء الثاني وبدائل الحركة"], None),
    (285, 288, "الاستغاثة والندبة", ["لام المستغاث به والمستغاث له والاستثناء", "ألف الندبة وشروط الإلحاق", "هاء الوقف وعدم تعميمها على الوصل"], None),
    (289, 292, "المفعول المطلق", ["المصدر الفضلة وعلاقة اللفظ أو المعنى", "نواب المصدر وأعداد الضرب", "التمييز عن الحال والمفعولات الأخرى"], None),
    (293, 296, "المفعول له", ["المصدر والتعليل واتحاد الوقت والفاعل", "الجر عند فقد الشرط", "اقتناء علاقة التعليل من المقام"], None),
    (297, 300, "المفعول فيه", ["الزمان والمكان المبهم وحدود معنى في", "الجهات والمقادير", "المكان المصوغ من مصدر العامل"], None),
    (301, 306, "المفعول معه", ["واو المعية والعامل الفعلي", "فصل العطف عن المعية", "الوجوب والترجيح والضعف بحسب السياق"], None),
    (307, 312, "الحال", ["الوصف والفضلة والتنكير", "مسوغات صاحب الحال", "العلاقة بالمقام وفصلها عن النعت والتمييز"], ("ConstructionEvidence", "same_case_does_not_choose_hal_tamyiz")),
    (313, 325, "التمييز", ["الذات والنسبة والتحويل", "المقادير والأعداد وكم الاستفهامية والخبرية", "بدائل الجر والنصب", "التمييز المؤكد والخلاف مع سيبويه"], ("ConstructionEvidence", "same_case_does_not_choose_hal_tamyiz")),
    (326, 336, "الاستثناء", ["تمام الكلام وإيجابه والاتصال والانقطاع", "التقديم ولهجتا الحجاز وتميم", "المفرغ بحسب العامل", "غير وسوى وخلا وعدا وحاشا وليس وما المصدرية"], ("Governors", "alternatives_not_collapsed")),
    (337, 346, "الجر والإضافة", ["الحروف المشتركة والمختصة بالظاهر", "الإضافة المعنوية واللفظية", "حذف التنوين ونون الإعراب", "مواضع جواز أل والاستثناءات"], ("ConstructionEvidence", "idafa_confirmation_needs_absences")),
    (347, 350, "اسم الفعل", ["معناه وبناؤه وعدم الحذف والتأخر", "إضمار فاعله", "جزم جواب الطلب واستثناء النصب"], None),
    (351, 357, "عمل المصدر", ["إحلال أن أو ما والفعل", "موانع التصغير والإضمار والنعت والحذف والفصل والتأخير", "مراتب المضاف والمنون والمقرون بأل"], None),
    (358, 364, "اسم الفاعل والمبالغة", ["أل والعمل المطلق", "الزمان والاعتماد عند التجرد", "حكاية الحال والخلاف", "أوزان المبالغة ودرجات الكثرة"], None),
    (365, 369, "اسم المفعول والصفة المشبهة", ["عمل اسم المفعول وشروط مشابهته لاسم الفاعل", "الثبوت والتعدية لواحد", "ترتيب المعمول والسببية", "بدائل الفاعلية والبدل والتمييز والتشبيه بالمفعول والإضافة"], None),
    (370, 373, "اسم التفضيل", ["المشاركة والزيادة", "مطابقة المجرد والمضاف وأل", "منع نصب المفعول", "رفع الظاهر ومسألة الكحل"], None),
    (374, 383, "النعت", ["المشتق والمؤول والوظائف المقامية", "الموافقة الإعرابية والتعريفية", "النعت الحقيقي والسببي واختلاف المطابقة", "قطع النعت ومقدرات المدح والذم والترحم"], ("ConstructionEvidence", "agreement_confirmed_exact")),
    (384, 395, "التوكيد", ["اللفظي وتكرار الأصناف واستثناء دكا وصفا", "النفس والعين والترتيب والجمع", "كل وكلا وكلتا وأجمع وشروطها", "الضمير ومنع التعاطف وتوكيد النكرة والندور"], None),
    (396, 402, "عطف البيان", ["الجامد غير المؤول والتوضيح والتخصيص", "الموافقة", "التداخل مع بدل الكل وموانع الإحلال"], None),
    (403, 408, "عطف النسق", ["الجمع والترتيب والتعقيب والتراخي والغاية", "التخيير والإباحة والشك والتشكيك", "التعيين وأم المتصلة", "لا ولكن وبل وتغير الحكم مع النفي والإيجاب"], ("Governors", "conjunction_propagates")),
    (409, 413, "البدل", ["المقصود بالحكم بلا واسطة", "الكل والبعض والاشتمال", "الإضراب والغلط والنسيان وقصد المتكلم"], None),
    (414, 418, "العدد", ["المخالفة من ثلاثة إلى تسعة والعشرة غير المركبة", "ما دون الثلاثة والتركيب", "فاعل العدد والإضافة والعمل"], ("NominalEvidence", "Cardinal.rule_exact")),
    (419, 431, "موانع الصرف", ["العلل التسع واستقلال القوي منها", "العلمية والوصفية وشروط العجمة والصفة", "هند وزينب وسقر وبلخ", "حذام وأمس وسحر ولهجاتها"], ("Morphology", "cause_prediction_exact")),
    (432, 439, "التعجب", ["تحليل ما أفعل وأفعل به", "الباء الزائدة والموقع الإعرابي", "شروط الفعل السبعة للتعجب والتفضيل"], None),
    (440, 448, "الوقف والرسم", ["تاء التأنيث والهاء وجمع المؤنث", "المنقوص وأل والتنوين", "إذن ونون التوكيد الخفيفة وألف النصب", "ألف واو الجماعة وموانعها", "رسم الألف بحسب الزيادة والأصل وشهادة التصريف"], ("PhonologicalModes", "feminine_pause_is_h")),
    (449, 453, "همزة الوصل", ["حصر الأسماء المثبتة وتثنياتها واختلاف الحركات", "الابتداء والإسقاط في الوصل", "الماضي فوق الرباعي وأمره ومصدره", "حركة أمر الثلاثي والأمثلة المعتلة والجموع"], ("PhonologicalModes", "wasl_onset_empty")),
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _load_pinned(path: Path, expected: str) -> dict:
    raw = path.read_bytes()
    require(digest(raw) == expected, f"installed evidence identity changed: {path.name}")
    return json.loads(raw)


def _inputs(directory: Path) -> tuple[dict, dict, dict[str, bytes]]:
    inventory = _load_pinned(directory / "classical_rule_inventory_v1.json", INVENTORY_SHA256)
    baseline = _load_pinned(
        ROOT / "evidence/arabic_completion_v5/rule_implementation_crosswalk.json",
        BASELINE_CROSSWALK_SHA256,
    )
    require({s["source_id"] for s in inventory["sources"]} == set(SOURCES), "source set changed")
    raws = {}
    for source_id, expected in SOURCES.items():
        raw = (directory / (source_id + ".txt")).read_bytes()
        require(digest(raw) == expected, f"source identity changed: {source_id}")
        raw.decode("utf-8")
        raws[source_id] = raw
    return inventory, baseline, raws


def _book(source_id: str, raw: bytes, inventory: dict) -> dict:
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    metadata_end = next(i + 1 for i, line in enumerate(lines) if b"#META#Header#End#" in line)
    # The fixed source-bound supplement cut prevents attribution to Ibn Aqil.
    supplement_start = 9657 if source_id == "ibn_aqil" else len(lines)
    if source_id == "ibn_aqil":
        require("تكملة: في تصريف الأفعال" in lines[supplement_start].decode(), "supplement boundary changed")
        require("محمد محيي الدين عبد الحميد" in lines[supplement_start + 1].decode(), "supplement author changed")
    boundaries = {0, metadata_end, supplement_start, len(lines)}
    headings = []
    for index, line in enumerate(lines):
        text = line.decode().rstrip("\r\n")
        if MARKUP_HEADING.match(text) or PROSE_HEADING.match(text):
            boundaries.add(index)
            headings.append({
                "line": index + 1, "start": offsets[index], "end": offsets[index + 1],
                "sha256": digest(line), "text": text,
                "kind": "markup_candidate" if MARKUP_HEADING.match(text) else "prose_candidate",
                "rule_adjudication": "not_established_by_heading_detection",
            })
        if PAGE.search(line):
            boundaries.add(index + 1)
    pages = [{"marker": match[0].decode(), "start": match.start(), "end": match.end(),
              "line": bisect_right(offsets, match.start())}
             for match in PAGE.finditer(raw)]
    source_spans = [(rule["rule_id"], span)
                    for rule in inventory["rules"] for span in rule["source_spans"]
                    if span["source_id"] == source_id]
    segments = []
    cuts = sorted(boundaries)
    for first, last in zip(cuts, cuts[1:]):
        start, end = offsets[first], offsets[last]
        if first < metadata_end:
            layer = "source_metadata"
        elif first >= supplement_start:
            layer = "named_editor_supplement"
        else:
            layer = "main_text_attribution_unadjudicated"
        segments.append({
            "segment_id": f"{source_id}:{SOURCES[source_id][:16]}:{start}:{end}",
            "start": start, "end": end, "line_start": first + 1, "line_end": last,
            "sha256": digest(raw[start:end]), "layer": layer,
            "adjudication": "not_applicable_metadata" if layer == "source_metadata" else "unreviewed_rule_inventory",
            "selected_law_ids": sorted({rule_id for rule_id, span in source_spans
                                         if span["start"] < end and span["end"] > start}),
        })
    cited = set(rule_id for rule_id, _ in source_spans)
    return {
        "source_id": source_id, "file": source_id + ".txt", "sha256": SOURCES[source_id],
        "size_bytes": len(raw), "line_count": len(lines), "metadata_end": offsets[metadata_end],
        "extent_status": "available_bytes_only_physical_edition_unverified",
        "extent_notes": EXTENT_NOTES[source_id],
        "selected_law_count": len(cited), "selected_law_ids": sorted(cited),
        "total_rule_count": None, "semantic_rule_inventory_complete": False,
        "page_marker_occurrence_count": len(pages),
        "distinct_page_marker_count": len({p["marker"] for p in pages}),
        "heading_candidate_count": len(headings), "segment_count": len(segments),
        "page_markers": pages, "heading_candidates": headings, "segments": segments,
    }


def qatr_docket(raw: bytes) -> dict:
    """A complete line partition with manually authored extraction obligations.

    Existing theorem references are checked for declaration identity, not
    promoted to proof of this section or a fresh kernel replay. The docket's
    semantic exhaustiveness and every source/formal translation remain open.
    """
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    sections = []
    cursor = 38
    for index, (first, last, title, obligations, bridge) in enumerate(QATR_DOCKET):
        require(first == cursor and first <= last, "Qatr docket has a gap or overlap")
        cursor = last + 1
        start, end = offsets[first - 1], offsets[last]
        references = []
        if bridge:
            module, theorem = bridge
            path = f"formal/Nabt/{module}.lean"
            code = (ROOT / path).read_bytes()
            name = theorem.split(".")[-1]
            match = re.search(r"^theorem " + re.escape(name) + r"(?:\s|\[|\()", code.decode(), re.M)
            require(match is not None, f"missing linked declaration: {module}.{theorem}")
            references.append({
                "path": path, "source_sha256": digest(code),
                "declaration": f"Nabt.{module}.{theorem}",
                "line": code.decode()[:match.start()].count("\n") + 1,
                "status": "existing_narrow_bridge_not_complete_section_implementation",
                "source_translation_fidelity_proved": False,
            })
        section_id = f"QATR-SECTION-{index:02d}"
        sections.append({
            "section_id": section_id, "title": title, "line_start": first, "line_end": last,
            "start": start, "end": end, "sha256": digest(raw[start:end]),
            "extraction_status": "authored_first_pass_needs_independent_clause_adjudication",
            "semantic_rule_denominator": None,
            "extraction_obligations": [{"obligation_id": f"{section_id}-O{number:02d}",
                                         "statement": obligation,
                                         "status": "open_complete_source_to_Lean_contract"}
                                        for number, obligation in enumerate(obligations, 1)],
            "existing_formal_references": references,
            "section_complete": False,
        })
    require(cursor == len(lines) + 1, "Qatr docket omits its end")
    return {
        "source_id": "qatr", "source_sha256": SOURCES["qatr"],
        "scope": "Entire available matn after metadata, lines 38-453; not the separate sharh",
        "section_count": len(sections),
        "extraction_obligation_count": sum(len(s["extraction_obligations"]) for s in sections),
        "sections_with_existing_narrow_bridge": sum(bool(s["existing_formal_references"]) for s in sections),
        "complete_section_count": 0, "semantic_rule_denominator": None,
        "independent_extraction_exhaustiveness_established": False,
        "sections": sections,
    }


def closure_status(document: dict) -> dict:
    """Evaluate reviewed evidence obligations, rather than count present files.

    Only exact, independently installed receipt identities can discharge a
    whole-book obligation. The caller may propose receipts but cannot install
    authority. ``validate_index`` additionally requires the complete policy
    replay, so modified adjudication labels cannot affect a public result.
    """
    receipts = document.get("closure_receipts", {})
    gates = {key: any(receipt in INSTALLED_CLOSURE_RECEIPTS[key]
                      for receipt in receipts.get(key, []))
             for key in GATE_OBLIGATIONS}
    books = document.get("books", [])
    gates[GATE_OBLIGATIONS[0]] = gates[GATE_OBLIGATIONS[0]] and bool(books) and all(
        book["extent_status"] == "independently_collated_complete_edition" for book in books)
    gates[GATE_OBLIGATIONS[1]] = gates[GATE_OBLIGATIONS[1]] and bool(books) and all(
        book["semantic_rule_inventory_complete"] is True and
        type(book["total_rule_count"]) is int and
        all(segment["adjudication"] == "independently_adjudicated_complete"
            for segment in book["segments"] if segment["layer"] != "source_metadata")
        for book in books)
    whole_book = all(gates[key] for key in GATE_OBLIGATIONS[:-1])
    return {
        "obligation_results": gates,
        "unresolved_gate_obligations": [key for key, passed in gates.items() if not passed],
        "whole_book_strict_pass": whole_book,
        "whole_arabic_strict_pass": whole_book and gates[GATE_OBLIGATIONS[-1]],
    }


def beyond_selected_inventory(raw: bytes, inventory: dict) -> list[dict]:
    """Concrete following passages missed by the selected 38-law denominator."""
    lines = raw.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    rows = []
    entries = [
        (9236, 9249, "WEAK-FINAL-PLURAL-CASCADE",
         "تسلسل جمع المعتل اللام بعد إبدال الهمزة: قضايا وزوايا وهراوى مع فرق الواو السالمة في المفرد"),
        (9250, 9254, "INITIAL-TWO-WAWS",
         "إبدال أول الواوين المصدرتين همزة واستثناء كون الثانية بدلا من ألف فاعل"),
        (9261, 9288, "TWO-HAMZAS-CONDITIONAL-REPLACEMENT",
         "تفريع تخفيف الهمزتين بحسب حركتيهما والموقع والاستثناء وبدائل أئمة؛ يحتاج مقابلة مواضع التفريغ المشتبهة"),
    ]
    for first, last, key, title in entries:
        start, end = offsets[first - 1], offsets[last]
        overlaps = [rule["rule_id"] for rule in inventory["rules"] for span in rule["source_spans"]
                    if span["source_id"] == "ibn_aqil" and span["start"] < end and span["end"] > start]
        require(not overlaps, "a beyond-selected passage now overlaps the fixed selected inventory")
        rows.append({
            "obligation_id": key, "source_id": "ibn_aqil", "title": title,
            "source_sha256": SOURCES["ibn_aqil"], "line_start": first, "line_end": last,
            "start": start, "end": end, "sha256": digest(raw[start:end]),
            "text": raw[start:end].decode(), "selected_38_span_overlap": [],
            "status": "open_independent_rule_extraction_and_composed_derivation",
            "atomic_rule_count": None,
        })
    return rows


def build_index(directory: Path = SOURCE_DIRECTORY) -> dict:
    inventory, baseline, raws = _inputs(directory)
    baseline_rows = {r["rule_id"]: r for r in baseline["rows"]}
    links = []
    for rule in inventory["rules"]:
        row = baseline_rows[rule["rule_id"]]
        links.append({
            "rule_id": rule["rule_id"], "selected_inventory_status": rule["status"],
            "source_spans": [{k: span[k] for k in ("source_id", "start", "end", "sha256")}
                             for span in rule["source_spans"]],
            "v5_baseline_status": row["status"],
            "v5_baseline_formal_namespace": row["formal_namespace"],
            "v5_baseline_implementation_path": row["implementation_path"],
            "mapping_is_whole_book_adjudication": False,
            "v6_rule_scope_and_proof_receipts": "See the separate v6 implementation crosswalk; this immutable baseline is not a v6 score.",
        })
    document = {
        "schema": POLICY, "authority": AUTHORITY,
        "source_inventory_sha256": INVENTORY_SHA256,
        "baseline_crosswalk_sha256": BASELINE_CROSSWALK_SHA256,
        "segmentation": "UTF-8 original line boundaries; metadata end, heading candidates and lines ending page-marker occurrences; no normalized text",
        "denominator": "all bytes of the six pinned available files, not all rules or all Arabic",
        "books": [_book(sid, raw, inventory) for sid, raw in raws.items()],
        "selected_rule_links": links,
        "qatr_semantic_docket": qatr_docket(raws["qatr"]),
        "beyond_selected_inventory_obligations": beyond_selected_inventory(raws["ibn_aqil"], inventory),
        "closure_receipts": {key: [] for key in GATE_OBLIGATIONS},
        "whole_book_rule_denominator": None, "whole_arabic_coverage": None,
    }
    gate = closure_status(document)
    document.update({
        "unresolved_gate_obligations": gate["unresolved_gate_obligations"],
        "whole_book_complete": gate["whole_book_strict_pass"],
        "whole_arabic_complete": gate["whole_arabic_strict_pass"],
    })
    return document


def validate_index(document: dict, directory: Path = SOURCE_DIRECTORY) -> dict:
    """Replay exact installed identity, partitions, mappings and non-authority.

    A caller cannot mark segments reviewed, replace source hashes, remove a
    difficult section, change attribution, or relabel a strict gate as passing.
    New adjudications require a separately versioned reviewed policy, not input
    booleans. This checker does not establish correctness of linguistic content.
    """
    require(type(document) is dict, "index must be an object")
    require(document.get("schema") == POLICY, "unsupported schema")
    require(document.get("authority") == AUTHORITY, "index cannot grant runtime authority")
    for book in document.get("books", []):
        for name in ("size_bytes", "line_count", "metadata_end", "selected_law_count",
                     "page_marker_occurrence_count", "distinct_page_marker_count",
                     "heading_candidate_count", "segment_count"):
            require(type(book.get(name)) is int, f"{name} must be an integer")
        for segment in book.get("segments", []):
            require(all(type(segment.get(k)) is int for k in ("start", "end", "line_start", "line_end")),
                    "segment coordinates must be integers, not booleans")
    expected = build_index(directory)
    # JSON equality also distinguishes 1/1.0/true at every nested coordinate.
    require(json.dumps(document, sort_keys=True, ensure_ascii=False) ==
            json.dumps(expected, sort_keys=True, ensure_ascii=False),
            "index differs from replayed fixed source/partition/obligation policy")
    books = document["books"]
    body_segments = [s for b in books for s in b["segments"] if s["layer"] != "source_metadata"]
    gate = closure_status(document)
    return {
        "schema": "nabt.book-rule-coverage-result.v1", "valid": True,
        "source_count": len(books), "source_bytes": sum(b["size_bytes"] for b in books),
        "source_lines": sum(b["line_count"] for b in books),
        "partition_segment_count": sum(b["segment_count"] for b in books),
        "body_segment_obligations": len(body_segments),
        "body_segments_with_selected_law_overlap": sum(bool(s["selected_law_ids"]) for s in body_segments),
        "fully_adjudicated_body_segments": sum(s["adjudication"] == "independently_adjudicated_complete"
                                                for s in body_segments),
        "heading_candidate_count": sum(b["heading_candidate_count"] for b in books),
        "page_marker_occurrences": sum(b["page_marker_occurrence_count"] for b in books),
        "selected_rule_count": len(document["selected_rule_links"]),
        "qatr_docket": {k: document["qatr_semantic_docket"][k] for k in (
            "section_count", "extraction_obligation_count", "sections_with_existing_narrow_bridge",
            "complete_section_count", "semantic_rule_denominator",
            "independent_extraction_exhaustiveness_established")},
        "exact_available_byte_partition": True,
        "whole_book_strict_pass": gate["whole_book_strict_pass"],
        "whole_arabic_strict_pass": gate["whole_arabic_strict_pass"],
        "obligation_results": gate["obligation_results"],
        "whole_book_rule_denominator": None, "whole_arabic_coverage": None,
        "unresolved_gate_obligations": document["unresolved_gate_obligations"],
        "books": [{k: b[k] for k in ("source_id", "size_bytes", "line_count", "segment_count",
                   "heading_candidate_count", "page_marker_occurrence_count", "selected_law_count",
                   "extent_status", "extent_notes")} for b in books],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-directory", type=Path, default=SOURCE_DIRECTORY)
    parser.add_argument("--write", type=Path, help="write a replayable index")
    parser.add_argument("--check", type=Path, help="validate an existing index")
    parser.add_argument("--summary", type=Path, help="write result JSON")
    parser.add_argument("--qatr-docket", type=Path, help="write the full Qatr semantic extraction work docket")
    parser.add_argument("--require-whole-book", action="store_true",
                        help="return 1 until the strict whole-book obligations are established")
    args = parser.parse_args()
    try:
        require(not (args.write and args.check), "choose --write or --check")
        document = json.loads(args.check.read_text()) if args.check else build_index(args.source_directory)
        result = validate_index(document, args.source_directory)
        if args.write:
            args.write.parent.mkdir(parents=True, exist_ok=True)
            args.write.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        if args.qatr_docket:
            args.qatr_docket.parent.mkdir(parents=True, exist_ok=True)
            args.qatr_docket.write_text(json.dumps(document["qatr_semantic_docket"], ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.require_whole_book and not result["whole_book_strict_pass"] else 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        print(json.dumps({"valid": False, "error": str(exc), "whole_book_strict_pass": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

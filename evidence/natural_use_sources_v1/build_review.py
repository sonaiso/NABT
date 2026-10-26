"""Rebuild the bounded source supplement from already pinned repository bytes.

No runtime gold, generated meaning, or retrieval score enters this review.
Editorial mappings are explicit premises; byte replay does not prove them.
"""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).with_name("source_inventory.json")


def digest(data):
    return sha256(data).hexdigest()


def build():
    original = json.loads((ROOT / "evidence/linguistic_truth_v1/source_inventory.json").read_bytes())
    source = next(s for s in original["sources"] if s["source_id"] == "shakhsiyya3_linguistic_truth_selected")
    rows = [dict(source)]
    extra = [
        ("natural_mukhtar", "mukhtar_sihah", "مختار الصحاح، مادة عين وقصد وحنن", "evidence/arabic_completion_v3/source_review/mukhtar_sihah_openiti_jk000107.txt"),
        ("natural_qatr", "qatr", "قطر الندى: المضارع والإعراب والمفعول", "src/nabt/data/source_evidence/qatr.txt"),
        ("natural_aqil", "ibn_aqil", "شرح ابن عقيل: الاسم المنون والوقف", "src/nabt/data/source_evidence/ibn_aqil.txt"),
        ("natural_ana", "lisan", "لسان العرب: عنا، مقتطف الضبط المودع", "evidence/attested_mark_recovery_v1/sources/lisan_ana.txt"),
    ]
    for sid, work, title, path in extra:
        data = (ROOT / path).read_bytes()
        rows.append(dict(source_id=sid, work=work, title=title, local_path=path,
                         bytes=len(data), sha256=digest(data)))
    passages = []
    data_by_id = {s["source_id"]: (ROOT / s["local_path"]).read_bytes() for s in rows}

    def passage(pid, sid, quote):
        raw = data_by_id[sid]
        selected = quote.encode()
        assert raw.count(selected) == 1, pid
        start = raw.index(selected)
        row = dict(passage_id=pid, source_id=sid, start=start, end=start+len(selected),
                   original_start=start, original_end=start+len(selected),
                   sha256=digest(selected), raw_text=quote,
                   coordinate_domain="retained_source_UTF8_bytes")
        if sid == source["source_id"]:
            parent = next(p for p in original["passages"] if p["start"] <= start < p["end"])
            row["original_start"] = parent["original_start"] + start - parent["start"]
            row["original_end"] = row["original_start"] + len(selected)
            row["coordinate_domain"] = "retained_excerpt_and_original_canonical_extraction"
        passages.append(row)
        return row

    shared = passage("natural::shared_ayn", source["source_id"],
        "المشترك هو اللفظ الموضوع لكل واحد من معنيين فاكثر، مثل لفظ العين للباصرة، والجارية، والذهب")
    mk = data_by_id["natural_mukhtar"].decode()
    ayn = mk[mk.index("# ع ي ن "):mk.index("# ع ي ي ")]
    passage("natural::mukhtar_ayn_full", "natural_mukhtar", ayn)
    passage("natural::qasd_verb", "natural_mukhtar", "القصد إتيان الشيء وبابه ضرب تقول قصده وقصد له وقصد اليه كله\n~~بمعنى واحد")
    passage("natural::qasd_word_use", "natural_mukhtar", "قصدت به البلد والموضع ذكرته وصرفته")
    passage("natural::ani_qasd", "natural_ana", "وَمَنْ تَعْنِي بِقَوْلِكَ أَيْ : مَنْ تَقْصِدُ")
    passage("natural::present_prefix", "natural_qatr", "ومضارع: ويعرف بلم. وافتتاحه بحرف من نأيت، نحو نقوم وأقوم ويقوم وتقوم.\n~~ويضم أوله إن كان ماضيه رباعيا ك\"يدحرج ويكرم\"، ويفتح في غيره ك\"يضرب\n~~ويستخرج\".")
    passage("natural::object_case", "natural_qatr", "باب المفعول منصوب وهو خمسة:\n# المفعول به، وهو ما وقع عليه فعل الفاعل ك \"ضربت زيدا\"")
    passage("natural::case_signs", "natural_qatr", "فيرفع بضمة، وينصب بفتحة،\n~~ويجر بكسرة، ويجزم بحذف حركة")
    passage("natural::tanwin_pause", "natural_aqil", "أي إذا وقف على الاسم المنون فإن كان التنوين واقعا بعد فتحه أبدل ألفا\n~~ويشمل ذلك ما فتحته للإعراب نحو رأيت زيدا")
    evidence = dict(passage_id=shared["passage_id"], quote=shared["raw_text"],
                    start=shared["start"], end=shared["end"], sha256=shared["sha256"],
                    original_start=shared["original_start"], original_end=shared["original_end"])
    meanings = [("ayn_eye", "العين الباصرة", ["العين الباصرة", "الباصرة", "حاسة الرؤية"]),
                ("ayn_spring", "عين الماء", ["عين الماء", "الجارية", "العين الجارية"]),
                ("ayn_gold", "الذهب", ["الذهب"])]
    designations = [dict(designation_id=sid, expression="العين", forms=["العين", "عين"],
                         sense_id=sid, gloss=gloss, sense_forms=forms, convention="linguistic",
                         origin="original", passage_ids=[shared["passage_id"]],
                         evidence=[dict(evidence)], evidence_kind="author_explicit_designation_report")
                    for sid, gloss, forms in meanings]
    retrieval = []
    for expression, stem in [("الأسد", "أسد"), ("العين", "عين")]:
        for form in [stem+"ا", stem+"اً"]:
            retrieval.append(dict(expression=expression, form=form, normal=stem+"ا",
                passage_ids=["natural::object_case", "natural::case_signs", "natural::tanwin_pause"],
                authority="LEXICAL_RETRIEVAL_PROPOSAL", selected_sense=None,
                caveat="Bounded orthographic retrieval proposal, not a licensed case assignment or a source-to-A116 bridge. The pause rule is not promoted into a universal spelling theorem."))
    review = dict(schema="nabt.linguistic-source-supplement.v1",
        law_id="nabt.contextual-lexical-supplement.v1",
        base_review_sha256=digest((ROOT/"evidence/linguistic_truth_v1/source_inventory.json").read_bytes()),
        authority="SOURCE_BACKED_EDITORIAL_PREMISES_NOT_A_NATIVE_ACQUISITION_PROOF",
        sources=rows, passages=passages, designations=designations, relations=[],
        acquisition_extension=dict(cue_verbs=[dict(normal="أقصد", forms=["أَقْصِدُ"],
            passage_ids=["natural::ani_qasd", "natural::qasd_verb", "natural::qasd_word_use", "natural::present_prefix"],
            evidence_kind="editorial_first_person_present_derivation",
            caveat="The exact first-person form is a reviewed derivation, not a verbatim dictionary quotation; semantics applies only to the already bounded explicit metalinguistic construction.")],
            initial_conjunction=None, retrieval_forms=retrieval),
        scope=dict(new_designations=3, native_acquisition_proof=False, tawatur_assessed=False,
            all_arabic_complete=False, external_truth_established=False,
            all_ayn_senses_exhausted=False,
            omitted_ayn_uses=["عين الركبة", "عين الشمس", "الدينار", "المال الناض", "الديدبان والجاسوس", "خيار الشيء", "نفس الشيء", "رأس عين", "عين البقر", "أعيان القوم", "أعيان الإخوة", "عين الميزان", "أنت على عيني"],
            lexical_scope="Three original-designation reports explicitly attributed by the selected Shakhsiyya passage. The complete retained Mukhtar entry is review context and exposes additional unmapped senses, not an assertion that the three are exhaustive.",
            unsupported_aliases=["الحيوان المعروف"],
            unsupported_alias_reason="A known animal need not denote the lion; 'من السباع معروف' does not justify this reverse implication.",
            retrieval_is_not_case_or_sense_acceptance=True),
        source_origin=dict(mukhtar="Pinned OpenITI bytes already recorded in evidence/arabic_completion_v3/source_review/mukhtar_openiti_retrieval_v1.json; no fresh remote or print collation performed.",
            vocalization="Existing short Lisan excerpt retained in attested_mark_recovery_v1; no new quotation or whole-book claim.",
            books="Current pinned Qatr/Ibn Aqil bytes replayed locally. Imported edition readings and editorial interpretation remain explicit premises."))
    return review


if __name__ == "__main__":
    DEST.write_text(json.dumps(build(), ensure_ascii=False, indent=2)+"\n")
    print(digest(DEST.read_bytes()))

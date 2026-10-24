"""Make source-relative frame recommendations; this does not run NABT."""
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def source_window(local_file, first, last, record_id, evidence_kind):
    path = HERE / local_file if not local_file.startswith("src/") else ROOT / local_file
    stored = path.read_bytes()
    raw = gzip.decompress(stored) if path.suffix == ".gz" else stored
    lines = raw.splitlines(keepends=True)
    start = sum(map(len, lines[:first - 1]))
    end = sum(map(len, lines[:last]))
    return {"record_id": record_id, "evidence_kind": evidence_kind,
            "path": str(path.relative_to(ROOT)), "source_sha256": sha256(raw).hexdigest(),
            "source_bytes": len(raw), "physical_lines": len(lines),
            "line_start": first, "line_end": last, "start": start, "end": end,
            "span_sha256": sha256(raw[start:end]).hexdigest(),
            "text": raw[start:end].decode("utf-8")}


windows = [
    source_window("samani_tafsir_openiti_v1.txt.gz", 664, 673,
                  "samani_izdada_nashatan_context", "AUTHOR_EXPLANATORY_PROSE_USAGE"),
    source_window("samani_tafsir_openiti_v1.txt.gz", 671, 673,
                  "samani_izdada_nashatan", "AUTHOR_EXPLANATORY_PROSE_USAGE"),
    source_window("firuzabadi_basair_openiti_v1.txt.gz", 17654, 17665,
                  "firuzabadi_increase_entry_context", "LEXICAL_EXPLANATION_WITH_TRANSFORMED_EXAMPLE"),
    source_window("firuzabadi_basair_openiti_v1.txt.gz", 17654, 17657,
                  "firuzabadi_izdadtu_fadlan", "LEXICAL_EXPLANATION_WITH_TRANSFORMED_EXAMPLE"),
    source_window("ibnathir_nihaya_openiti_v1.txt.gz", 16007, 16015,
                  "ibnathir_imtila_laban_drr", "LEXICOGRAPHER_EXPLANATION_OF_REPORTED_WORDING"),
    source_window("ibnathir_nihaya_openiti_v1.txt.gz", 26190, 26192,
                  "ibnathir_imtalaa_laban", "LEXICOGRAPHER_EXPLANATION_WITH_PERFECT_FRAME"),
    source_window("mukhtar_sihah_openiti_jk000107.txt", 12377, 12380,
                  "razi_nashat_as_verbal_noun", "LEXICAL_VOWEL_AND_MASDAR_ENTRY"),
    source_window("mukhtar_sihah_openiti_jk000107.txt", 11112, 11117,
                  "razi_laban_as_generic_noun", "LEXICAL_GENERIC_NOUN_ENTRY_NOT_NUMBER_INFERENCE"),
    source_window("src/nabt/data/source_evidence/qatr.txt", 313, 319,
                  "qatr_tamyiz_jamid_nisba", "EXPLICIT_GRAMMAR_RULE_AND_EXAMPLES"),
    source_window("src/nabt/data/source_evidence/sibawayhi.txt", 2048, 2056,
                  "sibawayhi_imtalaa_nontransitive_boundary", "EXPLICIT_GRAMMAR_BOUNDARY"),
    source_window("src/nabt/data/source_evidence/sabban.txt", 25543, 25563,
                  "sabban_ashmuni_nisba_transform_and_nontransform", "QUOTED_ASHMUNI_EXPOSITION_AND_SABBAN_COMMENTARY"),
]

sources = []
for filename in ["tamyiz_openiti_retrieval_v1.json", "nihaya_openiti_retrieval_v1.json"]:
    sources.extend(json.loads((HERE / filename).read_text())["files"])
report = {
    "schema": "nabt.arabic-completion.tamyiz-frame-source-review.v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_SUPPORTED_BOUNDED_FRAME_PROPOSALS_REQUIRING_IMPLEMENTATION_REVIEW",
    "selection_phase": "POST_BASELINE_PRIMARY_SOURCE_REVIEW_NOT_BLIND_EVALUATION",
    "source_and_benchmark_relation": "Residual cases guided this research. The source passages pre-exist NABT, but their selection is exposed and cannot be counted as a new blind holdout.",
    "sources": sources,
    "byte_span_convention": "Zero-based UTF-8 decoded source byte offsets [start,end); one-based inclusive physical lines. Gzip is storage only, not source normalization.",
    "passages": windows,
    "proposals": [
        {"candidate_rule": "attested_izdada_nashat_frame", "verb_lemma": "ازداد", "unit_form": "نشاطا",
         "case_motivating_search": "CON-M01", "status": "INDEPENDENT_PAIR_USAGE_FOUND",
         "primary_pair": "samani_izdada_nashatan", "supporting_scope": ["firuzabadi_izdadtu_fadlan", "razi_nashat_as_verbal_noun", "qatr_tamyiz_jamid_nisba"],
         "linguistic_claim": "The exact verb-plus-specification pair is attested in explanatory prose about a reader. The lexical explanation of increase supplies an independently stated transformed nisba example; the existing grammar source gives the grammatical category.",
         "inference_not_literal_quote": "Treating the attested pair as a parameterized frame with a new independently analyzed subject is a declared grammatical generalization, not an exact replay of Samani's sentence.",
         "unsettled": "The prose witness does not itself label nashatan as tamyiz or prove uniqueness against every possible contextual reading. Retain any independently supplied rival reading and all current morphological/reference/case obligations."},
        {"candidate_rule": "attested_imtalaa_laban_frame", "verb_lemma": "امتلأ", "unit_form": "لبنا",
         "case_motivating_search": "CON-M03", "status": "INDEPENDENT_PAIR_USAGE_AND_EXISTING_GRAMMAR_FRAME_FOUND",
         "primary_pair": "ibnathir_imtalaa_laban", "supporting_scope": ["ibnathir_imtila_laban_drr", "qatr_tamyiz_jamid_nisba", "sibawayhi_imtalaa_nontransitive_boundary", "razi_laban_as_generic_noun"],
         "linguistic_claim": "Ibn al-Athir's own lexical explanation uses imtalaa with laban; Qatr separately treats imtalaa al-ina ma as non-transformed nisba, while Sibawayhi explicitly distinguishes this pattern from ordinary direct-object transitivity.",
         "inference_not_literal_quote": "Changing the source subject (udder) to another independently analyzed subject and marking subject agreement is a bounded frame generalization. The source does not state the benchmark sentence or establish an actual filled cup.",
         "unsettled": "The word milk is a generic noun in the dictionary, not a source of unlimited units or a license to supply unknown QAC number/gender. The existing reading still has to satisfy its own acquired nominal and inflection premises."}
    ],
    "required_executable_conditions": [
        "Register exact source version, full-byte hash, record kind, line/byte span and allowed rule; replay the pair from actual preserved source bytes.",
        "Use only the explicitly acquired verb-unit pairs, not all nouns following these verbs and not the benchmark's expected relation.",
        "Require separately acquired verb/nominal readings and existing subject agreement, reference, case, indefiniteness and nominal-use constraints; do not fill missing features from the witness label.",
        "Keep the utterance event qualified by the specification. A source pattern must not create physical-world truth or erase competing analyses.",
        "No automatic direct-object valency transfer: Sibawayhi explicitly rejects imtala'tuhu for this filling pattern.",
        "Publish any subsequent improvement as post-baseline development on unchanged historical cases, alongside fresh adversarial cases; do not call it blind validation."
    ],
    "adversarial_controls": [
        {"text": "ازداد سامر باسما", "expected_boundary": "No nashat-frame witness for an arbitrary substituted noun."},
        {"text": "امتلأ الكأس نشاطا", "expected_boundary": "A unit attested with another verb cannot cross-license this pair."},
        {"text": "ازداد سامر النشاط", "expected_boundary": "Definite specification must not silently inherit the current indefinite tamyiz frame."},
        {"text": "امتلأ الكأس لبنٌ", "expected_boundary": "An incompatible explicit case ending cannot be changed to accusative by frame selection."},
        {"text": "امتلأته", "expected_boundary": "Do not derive ordinary transitive object-clitic behavior from the specification frame."},
        {"text": "حدث خارجي", "expected_boundary": "Source usage and grammatical conditional acceptance never establish that the event occurred."},
        {"text": "مصدر معدّل أو معطل", "expected_boundary": "Any source-byte/edition/span mismatch or revoked supporting record must prevent source activation."}
    ],
    "rejected_or_limited_search_leads": [
        "Forum replies about imtalaa al-kas labanan were not used as grammar authority.",
        "The modern al-Rajihi textbook's izdad zayd ilman example is a primary authored grammar exposition, but was not installed or used to pretend a classical quotation.",
        "Asas al-Balagha was acquired and searched; its found drr passage attests blood, not the milk pair. It is not the positive milk witness.",
        "Reported hadith truth is not inferred; the relevant authority is the lexicographer's wording and grammatical explanation."
    ],
    "runtime_changed_by_this_review": False,
    "historical_gold_changed": False,
}
output = HERE / "tamyiz_frame_source_review_v1.json"
with output.open("x", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"path": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
                  "passages": [{k: p[k] for k in ["record_id", "line_start", "line_end", "start", "end", "span_sha256"]} for p in windows]}, ensure_ascii=False, indent=2))

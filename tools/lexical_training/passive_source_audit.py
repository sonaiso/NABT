"""Replay a purposive reading of deposited Arabic sources for the passive-transfer study.

This is development evidence for the construction and its limits. Its quotations
are neither neural examples nor runtime certificates for an input occurrence.
"""
import argparse
from bisect import bisect_right
import json

from nabt.learning.source_evidence import SourceStore
from tools.grammar_catalog.catalog import ROOT, SOURCE_DIR, _line_offsets, build_catalog

OUTPUT = ROOT / "evidence/passive_relation_transfer_v1/source_audit.json"

# Source, physical starting line, exact deposited bytes as text, research question,
# shared textual lineage. The two books quoting the same verse are one lineage.
ANCHORS = (
    ("qatr", 241, "يحذف الفاعل فينوب عنه في أحكامه كلها مفعول به", "syntactic_deputy", "qatr_deputy"),
    ("qatr", 243, "ويفتح ما قبل الآخر في المضارع، ويكسر في الماضي", "passive_voice_shape", "qatr_deputy"),
    ("alfiyya", 331, "كنيل خير نائل", "illustrated_affirmative_passive", "alfiyya_nayl"),
    ("ibn_aqil", 3324, "فخير نائل مفعول قائم مقام الفاعل", "gloss_of_same_example", "alfiyya_nayl"),
    ("ibn_aqil", 3390, "سير يوم الجمعة", "temporal_deputy_not_an_affected_object", "ibn_aqil_nonobject"),
    ("qatr", 112, "لم يلد ولم\n~~يولد", "negated_active_and_passive", "quran_112_3"),
    ("mughni", 6404, "لم يلد ولم يولد", "same_quotation_in_lam_discussion", "quran_112_3"),
    ("mughni", 6407, "يوم الصليفاء لم يوفون بالجار", "attested_exception_discussed_after_lam", "poetic_lam_499"),
    ("ibn_aqil", 4644, "جئت كي أكرم زيدا", "purpose_complement_outside_the_frame", "ibn_aqil_kay"),
    ("mukhtar_sihah", 9272, "فتح الباب فانفتح", "attested_opening_frame", "mukhtar_open"),
    ("mukhtar_sihah", 9075, "أغلق الباب فهو مغلق", "attested_closing_frame", "mukhtar_close"),
    ("mukhtar_sihah", 10752, "كسره من باب ضرب فانكسر", "attested_breaking_frame", "mukhtar_break"),
)


def report():
    catalog = build_catalog()
    selected = {row[0] for row in ANCHORS}
    docs = {s["source_id"]: s for s in catalog["sources"] if s["source_id"] in selected}
    store = SourceStore.from_directory(ROOT / SOURCE_DIR, {k: d["sha256"] for k, d in docs.items()})
    lines = {name: _line_offsets(source.raw_bytes) for name, source in store.sources.items()}
    rows = []
    for name, line, excerpt, question, lineage in ANCHORS:
        raw = store.sources[name].raw_bytes
        # Physical lines retain OpenITI markers and their exact line delimiters.
        starts = lines[name]
        text = excerpt.encode("utf-8")
        start = raw.index(text, starts[line - 1])
        if bisect_right(starts, start) != line:
            raise ValueError(f"Selected anchor is missing on {name}:{line}")
        end = start + len(text)
        span = store.span(name, start, end)
        passages = sorted(p["passage_id"] for p in catalog["passages"]
                          if p["source_id"] == name and p["start"] <= start and end <= p["end"])
        rows.append({"observation": question, "lineage": lineage, "source": name,
                     "line_start": line, "line_end": bisect_right(starts, end - 1),
                     "start_byte": start, "end_byte": end, "span_sha256": span.span_sha256,
                     "raw_text": store.text(span), "containing_catalog_passages": passages})
    return {"schema": "nabt.passive-transfer.source-audit.v1",
            "selection": "PURPOSIVE_CONSTRUCTION_EXAMPLES_AND_COUNTEREXAMPLES",
            "scope": "Authored reading of cited grammar examples and lexicographic frames. "
                     "The original writing may lack marks; the classification uses the cited context. "
                     "Books, repeated quotations and commentaries are not independent event witnesses. "
                     "No frequency, corpus exhaustiveness or universal semantic role is inferred.",
            "neural_training_input": False, "blind_transfer_evaluation": False,
            "sources": {k: {f: d[f] for f in ("local_path", "sha256", "original_url")}
                        for k, d in docs.items()}, "observations": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the tracked audit; default checks it")
    args = parser.parse_args()
    result = report()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif json.loads(OUTPUT.read_text(encoding="utf-8")) != result:
        parser.exit(1, "Passive-transfer source audit differs from the pinned record.\n")
    print(f"Verified {len(result['observations'])} selected spans in {len(result['sources'])} sources.")


if __name__ == "__main__":
    main()

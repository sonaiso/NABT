"""Record source windows without importing or evaluating NABT."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
source = HERE / "mukhtar_sihah_openiti_jk000107.txt"
raw = source.read_bytes()
lines = raw.splitlines(keepends=True)
retrieval = json.loads((HERE / "mukhtar_openiti_retrieval_v1.json").read_text())
identity = retrieval["files"][0]


def window(name, first, last):
    start = sum(map(len, lines[:first - 1]))
    end = sum(map(len, lines[:last]))
    payload = raw[start:end]
    return {"record_id": name, "line_start": first, "line_end": last,
            "start": start, "end": end, "sha256": sha256(payload).hexdigest(),
            "text": payload.decode("utf-8")}


record = {
    "schema": "nabt.arabic-completion.hasiba-openiti-source-review.v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "source_selection_phase": "POST_BASELINE_PRIMARY_SOURCE_REVIEW_NOT_BLIND_VALIDATION",
    "status": "PINNED_WHOLE_LINE_LEXICAL_DISCRIMINATOR_FOUND",
    "authority": "EXACT_DIGITAL_TRANSCRIPTION_AND_SOURCE_RELATIVE_LEXICAL_RULE",
    "source": {**identity, "local_path": str(source.relative_to(ROOT)),
               "physical_lines": len(lines), "modified_locally": False,
               "pinned_url": "https://github.com/OpenITI/0675AH/blob/" + identity["commit"] + "/" + identity["path"]},
    "attribution": {
        "work": "مختار الصحاح", "author_as_recorded": "محمد بن أبي بكر بن عبدالقادر الرازي",
        "version_uri": "0666IbnAbiBakrZaynDinRazi.MukhtarSihah.JK000107-ara1",
        "edition_record_in_header": "محمود خاطر؛ مكتبة لبنان ناشرون؛ بيروت؛ طبعة جديدة؛ 1415 - 1995",
        "provider_identifier": "JK000107",
        "transmission": "Upstream version YAML marks PRIMARY_VERSION and CLEANED_VERSION; paratext removed by HRH and MGR, OpenITI Clean 2023.",
        "metadata_conflict_retained": "Repository author URI begins 0666, but inherited text header has AuthorDIED 721 and older BookURI #0721. This review does not resolve or rely on the death date.",
        "authentication": "PINNED_CLEANED_DIGITAL_VERSION_NOT_DIPLOMATIC_PRINT_COLLATION",
    },
    "license_review": {
        "repository_specific_license": "No LICENSE or COPYING file was present in the complete non-truncated pinned repository tree; root README only identifies 0675AH.",
        "official_corpus_declaration_url": "https://openiti.org/documentation/#how-can-i-use-openiti-what-license-is-used",
        "declared_license": "CC-BY-NC-SA-4.0",
        "scope": "Upstream corpus-level declaration, checked 2026-10-24; no independent printed-edition rights audit inferred.",
        "installation_note": "Preserve upstream version URI and attribution and add the corpus license notice if these bytes are installed in runtime data.",
    },
    "byte_span_convention": "UTF-8 bytes, zero-based inclusive start/exclusive end; physical lines one-based inclusive.",
    "passages": [window("mukhtar_hasaba_vs_hasiba_entry", 2723, 2730),
                 window("mukhtar_hasaba_counting_pattern", 2723, 2724),
                 window("mukhtar_hasiba_explicit_kasra_thought", 2729, 2730)],
    "finding": "The same entry gives counting in the nasara/kataba pattern and explicitly labels hasibtuhu salihan as kasra and glosses it as zanantuhu. This is a lexical-sense discriminator independent of benchmark answers.",
    "proposed_rule_scope": "Only a source-qualified form-I perfect verb occurrence with explicit medial kasra and the already licensed cognitive two-complement construction. Do not infer the sense from bare root or object count alone.",
    "scope_of_result": "A source-relative cognitive matrix; no promotion of its embedded proposition to an asserted fact or external truth.",
    "negative_controls": [
        "Fatha hasaba (counting) does not inherit this cognitive license.",
        "Unvocalized hasaba retains missing sense unless another independent witness settles it.",
        "Damma, sukūn, form-II shadda, form-III alif, or incompatible morphological readings cannot match this rule.",
        "Alima remains separately ambiguous: the pinned Sibawayhi source explicitly permits the one-object arafa meaning.",
        "A changed source byte, wrong source edition, altered span, or missing runtime registration must invalidate source replay.",
    ],
    "relationship_to_prior_html_review": "hasiba_source_review_v1.json remains unchanged. HTML and OpenITI are two transmissions of the same authored entry, not two independent speakers or statistically independent observations.",
    "not_claimed": ["A blind held-out evaluation", "Independent printed-edition or manuscript authentication", "An exhaustive inventory of Arabic senses", "Resolution of alima by this rule"],
}
assert "حسبته صالحا بالكسر" in record["passages"][0]["text"]
assert "ظننته" in record["passages"][0]["text"]
assert "حسبه عده وبابه نصر وكتب" in record["passages"][0]["text"]
out = HERE / "hasiba_openiti_source_review_v1.json"
with out.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"path": str(out), "sha256": sha256(out.read_bytes()).hexdigest(),
                  "source_sha256": sha256(raw).hexdigest(), "physical_lines": len(lines),
                  "passages": [{k: v for k, v in p.items() if k != "text"} for p in record["passages"]]}, ensure_ascii=False, indent=2))

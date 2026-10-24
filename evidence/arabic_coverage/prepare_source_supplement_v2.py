"""Install two bounded passages from the already acquired, pinned source.

This is post-baseline development acquisition, not blind validation. The
original three-source manifest and earlier supplementation receipt are left
unchanged. Re-execution checks immutable files instead of overwriting them.
"""

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/nabt/data/source_evidence"
EVIDENCE = ROOT / "evidence/arabic_coverage"
SOURCE_SHA = "8b9e86da786cf65e7b32498b2524ee48a8dcf9f61b59e1bbc32b99ce7db5b396"
BEFORE_SHA = "a70ffd541c444f86cf76ec6e6d8af692989d88b35129e277da1addf33a5a310a"
COMMIT = "4ec30fc763750fc1233d3774c4416b28c5c8b886"
UPSTREAM_PATH = ("data/1206IbnCaliSabbanShafici/1206IbnCaliSabbanShafici.HashiyaCalaSharhAshmuni/"
                 "1206IbnCaliSabbanShafici.HashiyaCalaSharhAshmuni.Shamela0011539-ara1")
REGISTRY = "construction_supplementary_sources_v1.json"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def immutable(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Immutable evidence differs: " + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def main():
    source = ROOT / "artifacts/local/arabic-coverage-source/sabban.txt"
    raw = source.read_bytes() if source.exists() else (DATA / "sabban.txt").read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("Pinned full source differs")
    lines = raw.splitlines(keepends=True)
    attribution = {
        "title": "حاشية الصبان على شرح الأشموني لألفية ابن مالك",
        "author": "أبو العرفان محمد بن علي الصبان الشافعي",
        "author_death_ah_as_recorded_in_header": 1206,
        "provider_identifier": "Shamela0011539",
        "version_uri": UPSTREAM_PATH.rsplit("/", 1)[-1],
        "quoted_text_layers": "Ashmuni exposition and Sabban commentary are distinguished per passage.",
        "edition_record_in_header": "دار الكتب العلمية بيروت-لبنان، الأولى 1417 هـ -1997م",
        "edition_authentication": "PINNED_CLEANED_DIGITAL_VERSION_NOT_DIPLOMATIC_PRINT_COLLATION",
        "transmission": "OpenITI metadata: PRIMARY_VERSION, CLEANED_VERSION; paratextual removal by HRH and MGR, 2023.",
    }
    registry = {
        "schema": "nabt.construction-supplementary-sources.v1",
        "selection_phase": "POST_BASELINE_PRIMARY_SOURCE_REVIEW_NOT_BLIND_VALIDATION",
        "authority": "PINNED_DIGITAL_SOURCE_IDENTITY_NOT_EXTERNAL_TRUTH",
        "byte_span_convention": "UTF-8 bytes, zero-based start inclusive/end exclusive; physical lines are 1-based inclusive.",
        "sources": [{
            "source_id": "sabban", "local_file": "sabban.txt", "repository": "OpenITI/1225AH",
            "commit": COMMIT, "path": UPSTREAM_PATH,
            "pinned_url": "https://github.com/OpenITI/1225AH/blob/" + COMMIT + "/" + UPSTREAM_PATH,
            "git_blob_sha1": "0627e5e730863f4886b9be6e771edea0cd41fcf0",
            "source_sha256": SOURCE_SHA, "bytes": len(raw), "physical_lines": len(lines),
            "allowed_rules": ["inception_sharaa", "tamyiz_taba_nafs"],
            "source_bytes_modified_locally": False, "attribution": attribution,
            "declared_corpus_license": "CC-BY-NC-SA-4.0",
            "license_notice": "LICENSE-DATA.md",
            "license_authority": "OpenITI corpus-level declaration; no repository-specific or printed-edition rights audit inferred.",
            "review_record": "evidence/arabic_coverage/source_audit_v1/license_attribution_review.json",
            "review_record_sha256": sha256((EVIDENCE / "source_audit_v1/license_attribution_review.json").read_bytes()).hexdigest(),
        }],
    }
    registry_raw = encoded(registry)
    registry_sha = sha256(registry_raw).hexdigest()
    passages = []
    specifications = [
        ("inception_sharaa", 13764, 13771, "SABBAN_COMMENTARY_EXPLICIT_PROPOSED_ADDITION",
         "Al-Sabban explicitly proposes adding sharaa in sharaa Zayd yakulu. This is a later commentator's constructed grammatical example, not Ibn Aqil, early observed usage, or consensus. The bounded complete onset auxiliary + subject + imperfect frame still requires independent lexical forms, reference, agreement and mood. The onset scope survives; an/no-an policy comes from the independently replayed inception-family rule. Other senses and incomplete frames remain unlicensed."),
        ("tamyiz_taba_nafs", 25543, 25550, "ASHMUNI_EXPOSITION_QUOTED_WITHIN_SABBAN_DIGITAL_SOURCE",
         "The quoted grammatical exposition explicitly gives taba Zayd nafsan and the transformed tabat nafs Zayd, distinguishing a nisba specification transformed from a subject. The reader acquires only this verb/unit frame, with independent target lexical form, reference, case and event attachment. It does not classify every N after taba, generalize to azdada/nashatan or milk after imtalaa, assert a timeless property, or authenticate a new event in the world."),
    ]
    for rule, lo, hi, layer, scope in specifications:
        start, end = sum(map(len, lines[:lo - 1])), sum(map(len, lines[:hi]))
        excerpt = raw[start:end]
        passages.append({
            "rule": rule, "source_id": "sabban", "source_commit": COMMIT,
            "source_path": UPSTREAM_PATH, "source_sha256": SOURCE_SHA,
            "start": start, "end": end, "line_start": lo, "line_end": hi,
            "span_sha256": sha256(excerpt).hexdigest(), "raw_text": excerpt.decode(),
            "source_layer": layer, "premise_scope": scope,
            "supplementary_registry_sha256": registry_sha,
            "selection_phase": "POST_BASELINE_NOT_BLIND",
        })
    path = DATA / "construction_policy.json"
    current_raw = path.read_bytes()
    policy = json.loads(current_raw)
    before_path = EVIDENCE / "source_policy_before_v2/construction_policy.json"
    if sha256(current_raw).hexdigest() == BEFORE_SHA:
        immutable(before_path, current_raw)
    elif not before_path.exists() or sha256(before_path.read_bytes()).hexdigest() != BEFORE_SHA:
        raise ValueError("Expected prior construction policy is unavailable")
    policy["passages"] = [p for p in policy["passages"] if p["rule"] not in {s[0] for s in specifications}] + passages
    policy["supplementary_source_registry"] = {"file": REGISTRY, "sha256": registry_sha}
    policy["supplementary_source_scope"] = "Separately attributed, post-baseline acquired cleaned OpenITI source; identity and passage applicability do not establish world truth or universal Arabic coverage."
    final_raw = encoded(policy)
    immutable(DATA / "sabban.txt", raw)
    immutable(DATA / REGISTRY, registry_raw)
    path.write_bytes(final_raw)
    receipt = {
        "schema": "nabt.arabic-coverage-source-supplement.v2",
        "base_commit": "f0064f0a4baab3cc816087a322aabc0c8fbb2d19",
        "selection_phase": "POST_BASELINE_PRIMARY_SOURCE_ACQUISITION_NOT_BLIND_VALIDATION",
        "previous_receipt": "evidence/arabic_coverage/source_supplement_v1.json",
        "previous_receipt_sha256": sha256((EVIDENCE / "source_supplement_v1.json").read_bytes()).hexdigest(),
        "original_source_manifest_changed": False, "original_three_source_bytes_changed": False,
        "new_source_bytes_changed": False,
        "construction_policy": {"policy_id": policy["policy_id"], "path": str(path.relative_to(ROOT)),
            "sha256": sha256(final_raw).hexdigest(), "previous_path": str(before_path.relative_to(ROOT)),
            "previous_sha256": BEFORE_SHA, "rule_count": len(policy["passages"])},
        "supplementary_registry": {"path": "src/nabt/data/source_evidence/" + REGISTRY,
            "sha256": registry_sha, "source_ids": ["sabban"]},
        "rules_added": passages,
        "source": registry["sources"][0],
    }
    immutable(EVIDENCE / "source_supplement_v2.json", encoded(receipt))
    print(json.dumps({"policy_sha256": sha256(final_raw).hexdigest(),
                      "registry_sha256": registry_sha, "rules": len(policy["passages"])}))


if __name__ == "__main__":
    main()

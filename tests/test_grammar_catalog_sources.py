"""Counterexamples for source identity, denominator and explicit proof edges."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from tools.grammar_catalog.catalog import (
    AUTHORITY, CatalogError, INPUT_SHA256, ROOT, build_catalog,
    catalog_sha256, validate_catalog,
)


class GrammarCatalogSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog()
        cls.passages = {p["passage_id"]: p for p in cls.catalog["passages"]}
        cls.rules = {r["rule_key"]: r for r in cls.catalog["rules"]}
        cls.sources = {s["source_id"]: s for s in cls.catalog["sources"]}

    def test_denominators_do_not_count_book_segments_as_rules(self):
        coverage = self.catalog["coverage"]
        self.assertEqual(coverage["book_partition_segments"], 9157)
        self.assertEqual(coverage["book_partition_bytes"], 10595657)
        self.assertEqual(coverage["namespaced_policy_entries"], 125)
        self.assertEqual(coverage["installed_conditional_operators"], 24)
        self.assertIsNone(coverage["whole_book_rule_denominator"])
        self.assertIsNone(coverage["whole_arabic_coverage"])
        self.assertFalse(coverage["whole_arabic_complete"])
        self.assertEqual(self.catalog["authority"], AUTHORITY)

    def test_all_raw_spans_replay_and_book_partition_reconstructs_bytes(self):
        book_parts = {}
        source_bytes = {sid: (ROOT / s["local_path"]).read_bytes()
                        for sid, s in self.sources.items() if s["content_available"]}
        for p in self.catalog["passages"]:
            s = self.sources[p["source_id"]]
            raw = source_bytes[p["source_id"]][p["start"]:p["end"]]
            self.assertEqual(raw, p["raw_text"].encode("utf-8"))
            self.assertEqual(sha256(raw).hexdigest(), p["sha256"])
            if "book_segment" in p["kinds"]:
                book_parts.setdefault(p["source_id"], []).append(p)
        for source_id, parts in book_parts.items():
            reconstructed = b"".join(p["raw_text"].encode("utf-8")
                                     for p in sorted(parts, key=lambda p: p["start"]))
            self.assertEqual(reconstructed, (ROOT / self.sources[source_id]["local_path"]).read_bytes())

    def test_shared_witness_preserves_three_distinct_imperative_rule_ids(self):
        prefix = "nabt.classical-rule-inventory.v1::"
        records = [self.rules[prefix + rid] for rid in
                   ("CMD-SOUND-2MS", "CMD-WEAK-DELETE", "CMD-NUN-DELETE")]
        shared = set.intersection(*(set(r["source_passage_ids"]) for r in records))
        self.assertTrue(shared)
        self.assertEqual(len({r["rule_key"] for r in records}), 3)
        self.assertTrue(any(self.passages[p]["source_id"] == "qatr" for p in shared))

    def test_span_identity_deduplicates_origins_not_rules(self):
        identities = [(p["source_key"], p["start"], p["end"], p["sha256"])
                      for p in self.catalog["passages"]]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertTrue(any(len(p["origins"]) >= 3 for p in self.catalog["passages"]))
        self.assertEqual(len(self.rules), 125)

    def test_external_dictionaries_are_not_claimed_installed(self):
        for sid in ("maqayis", "lisan"):
            self.assertFalse(self.sources[sid]["content_available"])
            self.assertIsNone(self.sources[sid]["local_path"])
            self.assertFalse(any(p["source_id"] == sid for p in self.catalog["passages"]))

    def test_excerpt_source_has_distinct_local_offset_space(self):
        source = self.sources["shakhsiyya_j3"]
        self.assertTrue(source["local_path"].endswith("morphology_j3.txt"))
        self.assertEqual(source["content_scope"], "selected_excerpt_deposit")
        spans = [p for p in self.catalog["passages"] if p["source_id"] == "shakhsiyya_j3"]
        self.assertEqual(len(spans), 5)
        self.assertTrue(all(p["original_offsets"]["start"] > 300000 for p in spans))
        self.assertTrue(all(p["end"] <= source["bytes"] for p in spans))

    def test_discrepant_text_is_not_silently_repaired_by_active_operator(self):
        r = self.rules["nabt.classical-rule-inventory.v1::ASSIM-NUN-B-BLOCKED-TEXT"]
        self.assertEqual(r["source_status"], "textual_discrepancy")
        self.assertEqual(r["runtime_rule_id"], r["local_id"])
        self.assertEqual(r["implementation_status"], "new_scoped_conditional_operator")
        self.assertFalse(r["full_source_rule_complete"])
        self.assertEqual({self.passages[p]["source_id"] for p in r["source_passage_ids"]},
                         {"alfiyya", "ibn_aqil"})

    def test_theorem_edges_resolve_but_namespaces_are_not_promoted(self):
        names = set(json.loads((ROOT / "formal/theorems.json").read_text())["theorems"])
        for row in self.catalog["rules"] + self.catalog["items"]:
            self.assertTrue(set(row["theorem_names"]) <= names)
        self.assertEqual(sum(bool(r["theorem_names"]) for r in self.catalog["rules"]), 24)
        self.assertEqual({n for r in self.catalog["rules"] for n in r["theorem_names"]},
                         {"Nabt.ClassicalHamza.enumeration_exact",
                          "Nabt.ClassicalWeak.enumeration_exact",
                          "Nabt.ClassicalGemination.enumeration_exact",
                          "Nabt.ClassicalGemination.nun_exact",
                          "Nabt.ClassicalBoundaryAffixes.weak_exact",
                          "Nabt.ClassicalBoundaryAffixes.light_exact",
                          "Nabt.ClassicalBoundaryAffixes.ana_exact"})
        self.assertEqual(self.rules["nabt.classical-rule-inventory.v1::CMD-SOUND-2MS"]["theorem_names"], [])

    def test_docket_obligations_are_open_and_separate(self):
        sections = [i for i in self.catalog["items"] if i["kind"] == "semantic_docket_section"]
        obligations = [i for i in self.catalog["items"] if i["kind"] == "open_obligation"]
        self.assertEqual(len(sections), 55)
        self.assertEqual(len(obligations), 187)
        self.assertTrue(all(not s["section_complete"] for s in sections))
        self.assertTrue(all(not o["theorem_names"] for o in obligations))

    def test_no_unestablished_alfiyya_verse_number(self):
        matches = [p for p in self.catalog["passages"] if p["source_id"] == "alfiyya"
                   and "مبتدأ زيد وعاذر خبر" in p["raw_text"]]
        self.assertTrue(matches)
        self.assertTrue(all("verse_number" not in p for p in matches))

    def test_unchanged_catalog_validates_to_fresh_object(self):
        verified = validate_catalog(self.catalog)
        self.assertIsNot(verified, self.catalog)
        self.assertEqual(catalog_sha256(verified), catalog_sha256(self.catalog))

    def test_forged_quote_even_with_rehashed_span_and_catalog_is_rejected(self):
        forged = copy.deepcopy(self.catalog)
        p = forged["passages"][0]
        p["raw_text"] += " مختلق"
        p["sha256"] = sha256(p["raw_text"].encode()).hexdigest()
        self.assertNotEqual(catalog_sha256(forged), catalog_sha256(self.catalog))
        with self.assertRaises(CatalogError):
            validate_catalog(forged)

    def test_forged_existing_theorem_link_is_rejected(self):
        forged = copy.deepcopy(self.catalog)
        forged["rules"][0]["theorem_names"] = ["Nabt.ClassicalHamza.enumeration_exact"]
        with self.assertRaises(CatalogError):
            validate_catalog(forged)

    def test_bool_cannot_impersonate_zero_offset(self):
        forged = copy.deepcopy(self.catalog)
        p = next(p for p in forged["passages"] if p["start"] == 0)
        p["start"] = False
        # Plain Python equality would incorrectly accept this substitution.
        self.assertEqual(forged, self.catalog)
        with self.assertRaises(CatalogError):
            validate_catalog(forged)

    def test_noncanonical_json_values_are_rejected(self):
        for value in (float("nan"), 0.0, (), Path("source")):
            with self.subTest(value=repr(value)), self.assertRaises(CatalogError):
                catalog_sha256({"value": value})

    def test_mutated_installed_registry_cannot_supply_its_own_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            relative = sorted(INPUT_SHA256)[0]
            target = root / relative
            target.parent.mkdir(parents=True)
            # The proposed file's internal hash/status does not override code pins.
            target.write_text('{"authority":"TRUST_ME","sha256":"rehashed"}')
            with self.assertRaisesRegex(CatalogError, "installed input hash mismatch"):
                build_catalog(root)


if __name__ == "__main__":
    unittest.main()

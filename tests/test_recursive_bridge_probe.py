"""Authored development regressions for the recursive Lean source bridge.

These use explicit Unicode scalar carrier values. They are separate from the
frozen external fixtures with opaque carrier IDs and from Arabic acquisition
measurements. Build ``recursiveBridgeProbe`` before running this module.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(text, source_id=1):
    return {"source_id": source_id, "revision": 1, "scope_id": 7,
            "atomization_id": 1, "atoms": list(text)}


def span(origin, start=0, stop=None):
    result = {name: origin[name] for name in
              ("source_id", "revision", "scope_id", "atomization_id")}
    result.update(start=start, stop=len(origin["atoms"]) if stop is None else stop)
    return result


def tag(class_id=10):
    return {"rule_id": 3, "reading_id": 4, "class_id": class_id, "requirements": []}


def atomic(origin, index):
    return {"op": "atom", "source": deepcopy(origin),
            "before": origin["atoms"][:index], "value": origin["atoms"][index],
            "after": origin["atoms"][index + 1:]}


def complete_host(origin, start=0, stop=None):
    stop = len(origin["atoms"]) if stop is None else stop
    if stop - start == 1:
        return atomic(origin, start)
    middle = (start + stop) // 2
    return {"op": "join", "tag": tag(),
            "left": complete_host(origin, start, middle),
            "right": complete_host(origin, middle, stop)}


def metadata(origin, *, start=0, stop=None, native=True):
    return {"registry_id": "development.rules.v1", "reading_id": "development.reading.1",
            "source": deepcopy(origin), "host": span(origin, start, stop),
            "host_tree": complete_host(origin, start, stop), "morphology": None,
            "section": None, "roles": [], "evidence_ids": [], "required": [],
            "provenance": "native_tree" if native else "source_reconstruction",
            "unresolved": [] if native else ["original_child_tree_unavailable"]}


def root_node(root="كتب", pattern=None, *, native=True):
    pattern = pattern or [{"literal": "م"}, {"literal": "َ"}, {"slot": 0},
                          {"literal": "ْ"}, {"slot": 1}, {"literal": "ُ"},
                          {"literal": "و"}, {"slot": 2}]
    rendered = "".join(root[token["slot"]] if "slot" in token else token["literal"]
                       for token in pattern)
    origin = source(rendered)
    details = metadata(origin, native=native)
    details["morphology"] = {
        "catalog_id": "development.mafool", "registry_id": "development.patterns.v1",
        "reading_id": "development.root.1",
        "reading": {"arity": len(root), "root": list(root), "pattern": deepcopy(pattern)},
        "alignment": [
            {"pattern_position": index, "source_position": index,
             "origin": {"kind": "radical", "index": token["slot"]} if "slot" in token
             else {"kind": "literal", "value": token["literal"]}}
            for index, token in enumerate(pattern)]}
    node = {"op": "leaf", "seed": {"kind": f"root{len(root)}", "radicals": list(map(ord, root))},
            "metadata": details}
    return origin, node


WITNESS = source("ش", source_id=90)


def receipt(node, *, positive=True, witness_id=100, requirement=0):
    return {"target": deepcopy(node), "requirement": requirement, "positive": positive,
            "witness_id": witness_id,
            "supports": [{"source": deepcopy(WITNESS), "span": span(WITNESS)}]}


def request(origin, node, interpreted=(), *, offered=None):
    return {"op": "bridge_assess", "node": deepcopy(node),
            "inventory": [deepcopy(origin), deepcopy(WITNESS)],
            "interpreted": deepcopy(list(interpreted)),
            "offered": deepcopy(list(interpreted if offered is None else offered))}


def structural_number(tree):
    def pair(a, b):
        return (a + b) * (a + b + 1) // 2 + b

    def seed_number(seed):
        if seed["kind"] == "lexical":
            return 3 * seed["entry"] + 2
        a, b, c, *tail = seed["radicals"]
        if tail:
            return 3 * pair(a, pair(b, pair(c, tail[0]))) + 1
        return 3 * pair(a, pair(b, c))

    if tree["op"] == "leaf":
        return 3 * seed_number(tree["seed"])
    if tree["op"] == "unary":
        return 3 * pair(tree["rule"], structural_number(tree["child"])) + 1
    return 3 * pair(tree["rule"], pair(structural_number(tree["left"]),
                                      structural_number(tree["right"]))) + 2


class RecursiveBridgeProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared = os.environ.get("NABT_RECURSIVE_BRIDGE_PROBE")
        cls.probe = Path(declared) if declared else ROOT / "formal/.lake/build/bin/recursiveBridgeProbe"
        if not cls.probe.is_file():
            if declared:
                raise RuntimeError("Declared recursive Lean executable is missing: " + str(cls.probe))
            raise unittest.SkipTest("Build recursiveBridgeProbe before Lean integration tests")

    def raw_queries(self, payload):
        run = subprocess.run([str(self.probe)], input=payload, capture_output=True,
                             check=True, timeout=30)
        self.assertEqual(run.stderr, b"")
        results = [json.loads(line) for line in run.stdout.splitlines()]
        for result in results:
            self.assertEqual(result["law_id"], "nabt.recursive-source-bridge.v1")
            self.assertIs(result["conditional"], True)
            self.assertIs(result["acquisition_measured"], False)
            self.assertIs(result["grammar_certified"], False)
        return results

    def queries(self, *values):
        results = self.raw_queries("".join(json.dumps(value, ensure_ascii=False) + "\n"
                                          for value in values).encode())
        self.assertEqual(len(results), len(values))
        return results

    def query(self, value):
        result, = self.queries(value)
        return result

    def test_discontinuous_unicode_radicals_bind_a_complete_contiguous_host(self):
        origin, node = root_node(native=False)
        result = self.query(request(origin, node))
        self.assertEqual(result["verdict"], "SOURCE_ONLY")
        self.assertIs(result["source_bound"], True)
        self.assertIs(result["conditional_licensed"], False)
        self.assertEqual(result["node"], node)
        alignment = result["node"]["metadata"]["morphology"]["alignment"]
        self.assertEqual([point["source_position"] for point in alignment
                          if point["origin"]["kind"] == "radical"], [2, 4, 7])
        self.assertEqual(len(alignment), len(origin["atoms"]))
        self.assertIs(result["steps"][0]["reconstruction_matches"], True)

    def test_radical_only_host_cannot_bypass_original_join_adjacency(self):
        origin, node = root_node()
        node["metadata"]["host_tree"] = {
            "op": "join", "tag": tag(), "left": atomic(origin, 2),
            "right": {"op": "join", "tag": tag(),
                      "left": atomic(origin, 4), "right": atomic(origin, 7)}}
        result = self.query(request(origin, node, [receipt(node)]))
        self.assertEqual(result["verdict"], "INVALID_SOURCE_BINDING")
        self.assertIs(result["source_bound"], False)

    def test_repeated_and_reordered_radical_positions_are_preserved(self):
        repeated = [{"slot": 0}, {"slot": 1}, {"slot": 2}, {"slot": 2}]
        interleaved = [{"slot": 0}, {"literal": "َ"}, {"slot": 2}, {"slot": 1}, {"slot": 3}]
        fixtures = [root_node(pattern=repeated), root_node("دحرج", interleaved)]
        for result, (_, node) in zip(self.queries(*(request(*fixture) for fixture in fixtures)), fixtures):
            self.assertIs(result["source_bound"], True)
            self.assertEqual(result["node"], node)
        self.assertEqual([point["origin"].get("index") for point in
                          fixtures[0][1]["metadata"]["morphology"]["alignment"]], [0, 1, 2, 2])

    def test_complete_interpreted_full_target_receipt_is_conditional(self):
        origin, node = root_node()
        result = self.query(request(origin, node, [receipt(node)]))
        self.assertEqual(result["verdict"], "CONDITIONALLY_LICENSED")
        self.assertIs(result["all_premises"], True)
        self.assertIn("PR14_host_Licensed", result["semantic_obligation"])
        self.assertEqual(result["steps"][0]["admitted_positive_witness_ids"], [100])

    def test_unresolved_or_reconstructed_nodes_do_not_gain_a_linguistic_license(self):
        origin, node = root_node()
        unresolved = deepcopy(node)
        unresolved["metadata"]["unresolved"] = ["lexical_attestation_missing"]
        reconstructed = deepcopy(node)
        reconstructed["metadata"]["provenance"] = "source_reconstruction"
        for result in self.queries(*(request(origin, target, [receipt(target)])
                                     for target in (unresolved, reconstructed))):
            self.assertIs(result["source_bound"], True)
            self.assertIs(result["all_premises"], True)
            self.assertIs(result["linguistic_ready"], False)
            self.assertEqual(result["verdict"], "SOURCE_ONLY")

    def test_known_negative_cannot_be_hidden_or_downgraded_to_source_only(self):
        origin, node = root_node(native=False)
        yes, no = receipt(node), receipt(node, positive=False, witness_id=101)
        present, withdrawn = self.queries(request(origin, node, [yes, no]),
                                          request(origin, node, [yes, no], offered=[yes]))
        for result in (present, withdrawn):
            self.assertEqual(result["verdict"], "REJECTED")
            self.assertIs(result["negative"], True)
            self.assertIs(result["linguistic_ready"], False)
            self.assertEqual(result["steps"][0]["known_negative_witness_ids"], [101])

    def test_source_identity_requires_complete_atoms_and_scope_revision(self):
        origin, node = root_node()
        valid = request(origin, node)
        variants = []
        missing = deepcopy(valid)
        missing["inventory"] = [deepcopy(WITNESS)]
        variants.append(missing)
        forged = deepcopy(valid)
        forged["inventory"][0]["atoms"][0] = "ن"
        variants.append(forged)
        for field in ("revision", "scope_id", "source_id"):
            changed = deepcopy(valid)
            changed["node"]["metadata"]["host"][field] += 1
            variants.append(changed)
        for result in self.queries(*variants):
            self.assertEqual(result["verdict"], "INVALID_SOURCE_BINDING")

    def test_missing_or_changed_alignment_fails_even_when_root_surface_matches(self):
        origin, node = root_node()
        variants = []
        missing = deepcopy(node)
        missing["metadata"]["morphology"]["alignment"].pop(0)
        variants.append(missing)
        shifted = deepcopy(node)
        shifted["metadata"]["morphology"]["alignment"][2]["source_position"] = 3
        variants.append(shifted)
        reassigned = deepcopy(node)
        reassigned["metadata"]["morphology"]["alignment"][2]["origin"]["index"] = 1
        variants.append(reassigned)
        for result in self.queries(*(request(origin, target) for target in variants)):
            self.assertEqual(result["verdict"], "INVALID_SOURCE_BINDING")

    def test_root_seed_must_match_typed_reading_in_the_declared_carrier_domain(self):
        origin, node = root_node()
        node["seed"]["radicals"] = [0, 1, 2]
        result = self.query(request(origin, node))
        self.assertEqual(result["verdict"], "INVALID_SOURCE_BINDING")
        self.assertIs(result["source_bound"], False)

    def test_metadata_cannot_be_swapped_behind_an_unchanged_receipt_target(self):
        origin, node = root_node()
        variants = []
        for field in ("registry_id", "reading_id"):
            changed = deepcopy(node)
            changed["metadata"][field] += ".different"
            variants.append(changed)
        for field in ("catalog_id", "registry_id", "reading_id"):
            changed = deepcopy(node)
            changed["metadata"]["morphology"][field] += ".different"
            variants.append(changed)
        for field, value in (("section", "noun"), ("evidence_ids", [99]),
                             ("required", [9]), ("provenance", "source_reconstruction"),
                             ("unresolved", ["missing"])):
            changed = deepcopy(node)
            changed["metadata"][field] = value
            variants.append(changed)
        changed = deepcopy(node)
        changed["metadata"]["roles"] = [{"role": "nominal_subject", "reading_id": "role.1",
                                          "target": span(origin), "head": None,
                                          "case": "raf", "case_domain": "inflected_case"}]
        variants.append(changed)
        for result in self.queries(*(request(origin, node, [receipt(value)]) for value in variants)):
            self.assertEqual(result["verdict"], "UNKNOWN")
            self.assertEqual(result["steps"][0]["admitted_positive_witness_ids"], [])

    def test_offered_receipts_and_unregistered_support_do_not_self_authorize(self):
        origin, node = root_node()
        yes = receipt(node)
        variants = [request(origin, node, [], offered=[yes])]
        for mutation in ("empty", "outside", "forged_atoms", "wrong_scope"):
            changed = deepcopy(yes)
            if mutation == "empty":
                changed["supports"] = []
            elif mutation == "outside":
                changed["supports"][0]["span"]["stop"] += 1
            elif mutation == "forged_atoms":
                changed["supports"][0]["source"]["atoms"] = ["ز"]
            else:
                changed["supports"][0]["span"]["scope_id"] += 1
            variants.append(request(origin, node, [changed]))
        for result in self.queries(*variants):
            self.assertEqual(result["verdict"], "UNKNOWN")

    def test_parent_receipt_never_bypasses_child_premises(self):
        origin, child = root_node()
        parent = {"op": "unary", "rule": 7, "metadata": deepcopy(child["metadata"]),
                  "child": child}
        parent["metadata"]["reading_id"] = "parent.1"
        only_parent = request(origin, parent, [receipt(parent)])
        complete = request(origin, parent, [receipt(parent), receipt(child, witness_id=102)])
        absent, accepted = self.queries(only_parent, complete)
        self.assertEqual(absent["verdict"], "UNKNOWN")
        self.assertEqual(absent["steps"][1]["missing_requirements"], [0])
        self.assertEqual(accepted["verdict"], "CONDITIONALLY_LICENSED")

    def test_full_substitution_is_retained_while_original_source_is_recovered(self):
        origin, node = root_node(native=False)
        original = deepcopy(node["metadata"]["host_tree"])
        node["metadata"]["host_tree"] = {"op": "substitute", "tag": tag(20),
                                            "replacement": ["ش"], "child": original}
        result = self.query(request(origin, node, [receipt(node)]))
        self.assertEqual(result["verdict"], "SOURCE_ONLY")
        self.assertIs(result["source_bound"], True)
        self.assertEqual(result["node"], node)
        self.assertEqual(result["node"]["metadata"]["host_tree"]["replacement"], ["ش"])
        self.assertIs(result["steps"][0]["reconstruction_matches"], True)

    def test_noop_substitution_and_same_class_lift_fail_existing_host_entry_gates(self):
        origin, node = root_node()
        original = deepcopy(node["metadata"]["host_tree"])
        variants = []
        noop = deepcopy(node)
        noop["metadata"]["host_tree"] = {"op": "substitute", "tag": tag(20),
                                            "replacement": origin["atoms"], "child": original}
        variants.append(noop)
        same_class = deepcopy(node)
        same_class["metadata"]["host_tree"] = {"op": "lift", "tag": tag(), "child": original}
        variants.append(same_class)
        for result in self.queries(*(request(origin, target, [receipt(target)]) for target in variants)):
            self.assertEqual(result["verdict"], "INVALID_SOURCE_BINDING")

    def test_zero_structural_number_is_valid_and_registry_scoped(self):
        tree = {"op": "leaf", "seed": {"kind": "root3", "radicals": [0, 0, 0]}}
        requests = [{"op": "core_number", "registry_id": registry, "tree": tree}
                    for registry in ("r1", "r2")]
        left, right = self.queries(*requests)
        self.assertEqual(left["number"], "0")
        self.assertEqual(left["number"], right["number"])
        self.assertNotEqual(left["registry_id"], right["registry_id"])
        self.assertIs(left["structural_only"], True)
        self.assertIs(left["linguistically_licensed"], False)

    def test_fast_numbering_matches_independent_closed_arithmetic_with_bit_preflight(self):
        left = {"op": "leaf", "seed": {"kind": "root3", "radicals": list(map(ord, "كتب"))}}
        right = {"op": "leaf", "seed": {"kind": "lexical", "entry": 29}}
        tree = {"op": "binary", "rule": 7, "left": left, "right": right}
        valid = {"op": "core_number", "registry_id": "r", "tree": tree}
        limited = dict(valid, max_number_bits=1)
        result, exhausted = self.queries(valid, limited)
        value = int(result["number"])
        self.assertEqual(value, structural_number(tree))
        self.assertLess(value, 2 ** result["estimated_max_number_bits"])
        self.assertEqual(exhausted["error"], "RESOURCE_LIMIT")
        self.assertIs(exhausted["linguistic_rejection"], False)

    def test_enumeration_deduplicates_inventory_and_reports_structural_completeness(self):
        seeds = [{"kind": "root3", "radicals": [1, 2, 3]},
                 {"kind": "root4", "radicals": [1, 2, 3, 4]},
                 {"kind": "lexical", "entry": 0}]
        inventory = {"seeds": seeds + [seeds[0]], "unary_rules": [0, 1, 0],
                     "binary_rules": [0, 1, 1]}
        results = self.queries(*({"op": "core_enumerate", "registry_id": "r",
                                  "inventory": inventory, "height": height} for height in (0, 1, 2)))
        for result, count in zip(results, (3, 27, 1515)):
            self.assertEqual(result["enumeration"], "COMPLETE")
            self.assertIs(result["search_complete"], True)
            self.assertEqual(result["candidate_count"], count)
            self.assertEqual(len(result["candidates"]), count)
            self.assertEqual(len({row["number"] for row in result["candidates"]}), count)
            self.assertEqual(result["removed_duplicate_seeds"], 1)
            self.assertEqual(result["removed_duplicate_unary_rules"], 1)
            self.assertEqual(result["removed_duplicate_binary_rules"], 1)

    def test_candidate_and_number_budget_exhaustion_do_not_claim_rejection(self):
        inventory = {"seeds": [{"kind": "lexical", "entry": 0}],
                     "unary_rules": [0], "binary_rules": [0]}
        base = {"op": "core_enumerate", "registry_id": "r", "inventory": inventory, "height": 2}
        for result in self.queries(dict(base, max_candidates=1), dict(base, max_number_bits=1)):
            self.assertEqual(result["enumeration"], "EXHAUSTED")
            self.assertIs(result["search_complete"], False)
            self.assertIs(result["linguistic_rejection"], False)
            self.assertEqual(result["candidates"], [])

    def test_unknown_metadata_or_claim_flags_and_non_scalar_atoms_are_rejected(self):
        origin, node = root_node()
        values = []
        extra = request(origin, node)
        extra["node"]["metadata"]["caller_licensed"] = True
        values.append(extra)
        flag = request(origin, node)
        flag["grammar_certified"] = True
        values.append(flag)
        multi_scalar = request(origin, node)
        multi_scalar["node"]["metadata"]["source"]["atoms"][0] = "مَ"
        values.append(multi_scalar)
        for result in self.queries(*values):
            self.assertEqual(result["error"], "INVALID_INPUT")

    def test_jsonl_recovers_after_invalid_or_oversized_requests(self):
        good = {"op": "core_number", "registry_id": "r",
                "tree": {"op": "leaf", "seed": {"kind": "lexical", "entry": 0}}}
        payload = b'{"op":"core_number","registry_id":"\\ud800"}\n'
        payload += b" " * (1048576 + 1) + b"\n"
        payload += json.dumps(good).encode() + b"\n"
        invalid, exhausted, recovered = self.raw_queries(payload)
        self.assertEqual(invalid["error"], "INVALID_INPUT")
        self.assertEqual(exhausted["error"], "RESOURCE_LIMIT")
        self.assertEqual(recovered["number"], "6")

    def test_duplicate_object_keys_are_rejected_before_lossy_typed_projection(self):
        origin, node = root_node()
        raw = json.dumps(request(origin, node), ensure_ascii=False, separators=(",", ":"))
        variants = [
            raw.replace('"op":"bridge_assess"', '"op":"foreign","op":"bridge_assess"', 1),
            raw.replace('"source_id":', '"source_id":999999,"source_id":', 1),
            raw.replace('"evidence_ids":', '"evidence_ids":[999999],"evidence_ids":', 1),
            raw.replace('"op":"bridge_assess"', '"op":"bridge_assess","op":"bridge_assess"', 1),
        ]
        results = self.raw_queries(("\n".join(variants) + "\n").encode())
        self.assertEqual(len(results), len(variants))
        for result in results:
            self.assertEqual(result["error"], "INVALID_INPUT")
            self.assertEqual(result["message"], "duplicate JSON object key")

    def test_duplicate_key_detection_decodes_escaped_keys_and_nested_receipts(self):
        origin, node = root_node()
        raw = json.dumps(request(origin, node, [receipt(node)]), ensure_ascii=False,
                         separators=(",", ":"))
        variants = [
            raw.replace('"op":"bridge_assess"',
                        '"\\u006fp":"foreign","op":"bridge_assess"', 1),
            raw.replace('"evidence_ids":', '"\\u0065vidence_ids":[999999],"evidence_ids":', 1),
            raw.replace('"positive":true', '"positive":false,"positive":true', 1),
        ]
        results = self.raw_queries(("\n".join(variants) + "\n").encode())
        self.assertEqual(len(results), len(variants))
        for result in results:
            self.assertEqual(result["error"], "INVALID_INPUT")
            self.assertEqual(result["message"], "duplicate JSON object key")

    def test_key_guard_respects_independent_objects_strings_and_following_lines(self):
        registry = r'{"op":"a","op":"b"} \\u006fp ["key","key"]'
        leaf = {"op": "leaf", "seed": {"kind": "lexical", "entry": 0}}
        valid = {"op": "core_number", "registry_id": registry,
                 "tree": {"op": "binary", "rule": 0, "left": leaf, "right": deepcopy(leaf)}}
        payload = '{"op":"bad","op":"bad"}\n' + json.dumps(valid) + "\n"
        rejected, accepted = self.raw_queries(payload.encode())
        self.assertEqual(rejected["error"], "INVALID_INPUT")
        self.assertEqual(accepted["status"], "OK")
        self.assertEqual(accepted["registry_id"], registry)
        self.assertEqual(accepted["tree"], valid["tree"])


if __name__ == "__main__":
    unittest.main()

"""Independent replay boundaries for the newly registered digital source.

The outer pins are bypassed only in explicitly named inner-contract tests,
so source identity, allowlists and byte/line validation execute independently.
No installed source file is mutated by these regressions.
"""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from nabt import construction_sources as sources
from nabt.errors import NabtError
from nabt.word_reader import replay_policy


PACKAGE = Path(__file__).resolve().parents[1] / "src/nabt"
DATA = PACKAGE / "data/source_evidence"


class Overlay:
    def __init__(self, replacements, parts=()):
        self.replacements, self.parts = replacements, parts

    def joinpath(self, *parts):
        return Overlay(self.replacements, self.parts + tuple(parts))

    def read_bytes(self):
        path = Path(*self.parts)
        return self.replacements.get(path.as_posix(), (PACKAGE / path).read_bytes())


def wire(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


class ConstructionSupplementarySourcesTests(unittest.TestCase):
    def check_rejected(self, replacements, *, policy_pin=None, registry_pin=None):
        with patch.object(sources, "files", return_value=Overlay(replacements)), \
                patch.object(sources, "EXPECTED_POLICY_SHA256", policy_pin or sources.EXPECTED_POLICY_SHA256), \
                patch.object(sources, "EXPECTED_SUPPLEMENTARY_SHA256", registry_pin or sources.EXPECTED_SUPPLEMENTARY_SHA256):
            with self.assertRaises(NabtError) as caught:
                sources.replay_construction_policy()
            self.assertEqual(caught.exception.code, "INSTALLED_CONTRACT_FAILED")
            self.assertEqual(caught.exception.status, "DEFER")

    def test_separate_registry_does_not_change_original_word_sources(self):
        base = replay_policy()
        self.assertEqual(set(base["sources"]), {"qatr", "alfiyya", "sibawayhi"})
        replay = sources.replay_construction_policy()
        self.assertEqual(set(replay["supplementary_source_ids"]), {"sabban", "mukhtar_sihah"})
        self.assertEqual(replay["supplementary_registry_sha256"], sources.EXPECTED_SUPPLEMENTARY_SHA256)
        for rule in ("inception_sharaa", "tamyiz_taba_nafs"):
            self.assertEqual(replay["rules"][rule]["source_id"], "sabban")
            self.assertEqual(replay["rules"][rule]["selection_phase"], "POST_BASELINE_NOT_BLIND")
        self.assertNotEqual(replay["rules"]["inception_sharaa"]["source_layer"],
                            replay["rules"]["tamyiz_taba_nafs"]["source_layer"])
        self.assertEqual(replay["rules"]["vocalized_hasiba_sense"]["source_id"], "mukhtar_sihah")

    def test_registry_and_full_source_bytes_are_rechecked(self):
        for filename in (sources.SUPPLEMENTARY_REGISTRY, "sabban.txt", "mukhtar_sihah.txt"):
            with self.subTest(filename=filename):
                original = (DATA / filename).read_bytes()
                # The final byte is outside both selected source passages.
                self.check_rejected({"data/source_evidence/" + filename: original + b"\n"})

    def test_inner_contract_binds_supplementary_commit_path_and_registry(self):
        original = json.loads((DATA / "construction_policy.json").read_bytes())
        for field, value in (("source_commit", "0" * 40), ("source_path", "unregistered/path"),
                             ("source_id", "unregistered_source"), ("supplementary_registry_sha256", "0" * 64)):
            with self.subTest(field=field):
                policy = deepcopy(original)
                next(p for p in policy["passages"] if p["rule"] == "inception_sharaa")[field] = value
                raw = wire(policy)
                self.check_rejected({"data/source_evidence/construction_policy.json": raw},
                                    policy_pin=sha256(raw).hexdigest())

    def test_inner_contract_replays_source_lines_bytes_and_raw_text(self):
        original = json.loads((DATA / "construction_policy.json").read_bytes())
        for field, value in (("line_start", True), ("line_end", 13770), ("start", 0),
                             ("span_sha256", "0" * 64), ("raw_text", "unwitnessed quotation")):
            with self.subTest(field=field):
                policy = deepcopy(original)
                next(p for p in policy["passages"] if p["rule"] == "inception_sharaa")[field] = value
                raw = wire(policy)
                self.check_rejected({"data/source_evidence/construction_policy.json": raw},
                                    policy_pin=sha256(raw).hexdigest())

    def test_inner_registry_rejects_renamed_or_unregistered_source(self):
        registry = json.loads((DATA / sources.SUPPLEMENTARY_REGISTRY).read_bytes())
        registry["sources"][0]["source_id"] = "unregistered_source"
        raw = wire(registry)
        digest = sha256(raw).hexdigest()
        policy = json.loads((DATA / "construction_policy.json").read_bytes())
        policy["supplementary_source_registry"]["sha256"] = digest
        policy_raw = wire(policy)
        self.check_rejected({"data/source_evidence/" + sources.SUPPLEMENTARY_REGISTRY: raw,
                             "data/source_evidence/construction_policy.json": policy_raw},
                            policy_pin=sha256(policy_raw).hexdigest(), registry_pin=digest)

    def test_replayed_nisba_models_are_exact_bounded_pairs(self):
        models = sources.replay_construction_policy()["examples"]["nisba_frames"]
        self.assertEqual({(m["verb"], m["unit_form"]) for m in models},
                         {("اشتعل", "شيبا"), ("امتلأ", "ماء"), ("طاب", "نفسا")})
        taba = next(m for m in models if m["verb"] == "طاب")
        self.assertEqual(taba["source_rule"], "tamyiz_taba_nafs")
        self.assertEqual(taba["transformation"], "from_subject")


if __name__ == "__main__":
    unittest.main()

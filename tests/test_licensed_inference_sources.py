"""Independent source-byte boundary checks for the finite reading law."""

import contextlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.licensed_inference import sources


def document_copy():
    return json.loads((sources.ROOT / sources.REVIEW_PATH).read_text())


@contextlib.contextmanager
def installed_copy():
    document = document_copy()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        paths = [sources.REVIEW_PATH]
        paths += [row["path"] for row in document["source_registries"]]
        paths += [row["local_path"] for row in document["sources"]]
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sources.ROOT / relative, target)
        yield root, document


class LicensedInferenceSourceTests(unittest.TestCase):
    def test_installed_sources_replay_with_limited_authority(self):
        review = sources.build_inventory()
        self.assertEqual(review["law_id"], "nabt.licensed-inference.v1")
        self.assertEqual((review["source_count"], review["passage_count"]), (8, 16))
        self.assertEqual(review["review_sha256"], sources.SOURCE_LINKS_SHA256)
        receipt = review["source_replay"]
        self.assertEqual(receipt["mode"], "retained_bytes_only")
        self.assertIs(receipt["originals_rechecked"], False)
        self.assertEqual(receipt["original_recheck"]["scope"], [])
        self.assertIs(receipt["world_truth_established"], False)
        self.assertIs(receipt["source_interpretation_proved"], False)
        self.assertIn("inverse_profile_disabled", review["relation_ids"])
        self.assertIn("unresolved_reference", review["relation_ids"])

    def test_caller_edited_review_cannot_grant_authority(self):
        with installed_copy() as (root, document):
            document["world_truth"] = True
            (root / sources.REVIEW_PATH).write_text(json.dumps(document))
            with self.assertRaisesRegex(sources.SourceValidationError, "review hash"):
                sources.build_inventory(root)

    def test_mutated_source_or_registry_fails_closed(self):
        for kind in ("source", "registry"):
            with self.subTest(kind=kind), installed_copy() as (root, document):
                relative = (document["sources"][0]["local_path"] if kind == "source"
                            else document["source_registries"][0]["path"])
                path = root / relative
                raw = bytearray(path.read_bytes())
                raw[0] ^= 1
                path.write_bytes(raw)
                with self.assertRaisesRegex(sources.SourceValidationError, "hash mismatch"):
                    sources.build_inventory(root)

    def test_missing_source_is_not_linguistic_rejection(self):
        with installed_copy() as (root, document):
            (root / document["sources"][0]["local_path"]).unlink()
            with self.assertRaisesRegex(sources.SourceValidationError, "unavailable"):
                sources.build_inventory(root)

    def test_boolean_offsets_are_not_integers(self):
        for field in ("start", "end", "line_start", "line_end"):
            with self.subTest(field=field):
                document = document_copy()
                document["passages"][0][field] = True
                # Direct validation tests defenses below the public pin; it
                # cannot authorize an edited review through build_inventory.
                with self.assertRaisesRegex(sources.SourceValidationError, "invalid"):
                    sources._validate_document(sources.ROOT, document)

    def test_duplicate_ids_are_rejected(self):
        for collection, key in (("sources", "source_id"), ("passages", "passage_id"),
                                ("relations", "relation_id")):
            with self.subTest(collection=collection):
                document = document_copy()
                document[collection][1][key] = document[collection][0][key]
                with self.assertRaisesRegex(sources.SourceValidationError, "duplicate"):
                    sources._validate_document(sources.ROOT, document)

    def test_exact_raw_text_is_required(self):
        document = document_copy()
        document["passages"][0]["raw_text"] += " invented attribution"
        with self.assertRaisesRegex(sources.SourceValidationError, "raw text"):
            sources._validate_document(sources.ROOT, document)

    def test_unpaired_surrogate_is_a_source_error(self):
        document = document_copy()
        document["passages"][0]["raw_text"] = chr(0xD800)
        with self.assertRaisesRegex(sources.SourceValidationError, "valid Unicode"):
            sources._validate_document(sources.ROOT, document)

    def test_correct_hash_does_not_authorize_shifted_line_range(self):
        document = document_copy()
        document["passages"][0]["line_start"] += 1
        with self.assertRaisesRegex(sources.SourceValidationError, "line/span"):
            sources._validate_document(sources.ROOT, document)

    def test_utf8_mid_codepoint_cannot_be_a_span_start(self):
        document = document_copy()
        passage = next(row for row in document["passages"]
                       if row["source_id"] == "nabhani_condition_profile")
        passage["start"] = 1  # Inside the first two-byte Arabic letter.
        with self.assertRaisesRegex(sources.SourceValidationError, "UTF-8 boundary"):
            sources._validate_document(sources.ROOT, document)

    def test_unknown_relation_passage_cannot_be_linked(self):
        document = document_copy()
        document["relations"][0]["passage_ids"] = ["not-a-source-passage"]
        with self.assertRaisesRegex(sources.SourceValidationError, "relation passage"):
            sources._validate_document(sources.ROOT, document)

    def test_retained_excerpt_must_cover_the_original_span_manifest(self):
        document = document_copy()
        source = next(row for row in document["sources"] if "retained_original_spans" in row)
        source["retained_original_spans"].pop()
        with self.assertRaisesRegex(sources.SourceValidationError, "incomplete retained"):
            sources._validate_document(sources.ROOT, document)

    def test_source_paths_stay_within_root(self):
        for path in ("../outside.txt", "/etc/passwd", "src/../outside.txt"):
            with self.subTest(path=path):
                document = document_copy()
                document["sources"][0]["local_path"] = path
                with self.assertRaisesRegex(sources.SourceValidationError, "canonical and relative"):
                    sources._validate_document(sources.ROOT, document)

    def test_symlink_cannot_escape_root(self):
        with installed_copy() as (root, document):
            relative = document["sources"][0]["local_path"]
            target = root / relative
            target.unlink()
            target.symlink_to(sources.ROOT / relative)
            with self.assertRaisesRegex(sources.SourceValidationError, "escapes root"):
                sources.build_inventory(root)

    def test_original_recheck_requires_exact_uploaded_docx(self):
        with tempfile.TemporaryDirectory() as directory:
            bogus = Path(directory) / "wrong.docx"
            bogus.write_bytes(b"a caller flag is not an original")
            with self.assertRaisesRegex(sources.SourceValidationError, "original DOCX"):
                sources.build_inventory(original_part3=bogus)

    def test_source_reader_has_a_resource_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.txt").write_bytes(b"12345")
            with self.assertRaisesRegex(sources.SourceValidationError, "resource bound"):
                sources._read(root, "large.txt", 4)


if __name__ == "__main__":
    unittest.main()

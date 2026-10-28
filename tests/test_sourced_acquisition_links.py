"""Source replay and synthetic-index boundaries, independent of runtime/gold.

Synthetic rows exercise checking logic only; they are never kernel evidence.
The actual fresh compiled catalogue is supplied separately by integration.
"""

from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_sourced_acquisition_links as links
from tools import proof_catalog


def explicit_names():
    return sorted({module + "." + name for _, module, names, _, _ in links.OBLIGATIONS for name in names})


def synthetic_catalog(root):
    """Make a toy source tree/index, not a Lean build or a substitute for one."""
    names = explicit_names()
    rows, texts = [], {}
    for name in names:
        module, short = name.rsplit(".", 1)
        path = f"formal/{module.replace('.', '/')}.lean"
        text = texts.setdefault(path, "-- Synthetic fixture only; no kernel evidence.\n")
        line = text.count("\n") + 1
        texts[path] += f"theorem {short} : True := by trivial\n"
        rows.append({"name": name, "module": module, "source_path": path,
                     "canonical_name": name, "statement_sha256": sha256(name.encode()).hexdigest(),
                     "universe_parameters": 0, "proof_dependencies": [], "type_dependencies": [], "axioms": [],
                     "range": {"line": line, "end_line": line, "column": 0, "end_column": 20}})
    texts.update({"formal/theorems.json": json.dumps({"theorems": names}),
                  "formal/lean-toolchain": "synthetic-test-toolchain\n",
                  "formal/ExportProofCatalog.lean": "-- Synthetic exporter\n",
                  "tools/proof_catalog.py": "# Synthetic index producer\n"})
    for path, text in texts.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    inputs = {p: sha256(t.encode()).hexdigest() for p, t in texts.items()}
    for row in rows:
        row["source_sha256"] = inputs[row["source_path"]]
    return {"schema": proof_catalog.SCHEMA, "authority": "COMPILED_DECLARATION_INDEX_ONLY",
            "inputs": inputs, "lean_toolchain": "synthetic-test-toolchain", "theorems": rows}


class SourcedPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = {kind: json.loads((links.ROOT / path).read_bytes()) for kind, (path, _) in links.PACKETS.items()}

    def test_frozen_sources_spans_and_authored_denominators_replay(self):
        indexes = links._read_sources(links.ROOT)
        self.assertEqual({k: len(v["sources"]) for k, v in indexes.items()}, {"shared": 7, "natural": 4})
        self.assertEqual({k: len(v["passages"]) for k, v in indexes.items()}, {"shared": 30, "natural": 8})
        self.assertEqual(len(indexes["shared"]["readings"]), 34)
        self.assertEqual(set(indexes["natural"]["senses"]), {"ayn_eye", "ayn_spring", "ayn_gold"})
        negative = indexes["natural"]["passages"]["negative_lam"]
        self.assertEqual((negative["line_start_1based"], negative["line_end_1based_inclusive"]), (15517, 15517))
        for kind, (path, digest) in links.PACKETS.items():
            self.assertEqual(sha256((links.ROOT / path).read_bytes()).hexdigest(), digest)

    def test_exact_raw_quote_hashes_and_offsets_are_independently_checked(self):
        for kind, fields in (("shared", ("raw_text", "span_sha256", "byte_start_0based", "byte_end_0based_exclusive")),
                             ("natural", ("quote", "sha256", "start_byte", "end_byte"))):
            for field, value in zip(fields, ("invented quote", "0" * 64, True, 10**30)):
                with self.subTest(kind=kind, field=field):
                    data = deepcopy(self.packets[kind]); data["passages"][0][field] = value
                    with self.assertRaises(links.LinkError):
                        links._validate_packet(links.ROOT, kind, data)

    def test_offset_empty_negative_and_utf8_midpoint_are_rejected(self):
        for start, end in ((-1, 5), (4, 4), (23852, 23924)):
            data = deepcopy(self.packets["natural"])
            data["passages"][0].update(start_byte=start, end_byte=end)
            with self.subTest(start=start), self.assertRaises((links.LinkError, UnicodeError)):
                links._validate_packet(links.ROOT, "natural", data)

    def test_full_line_metadata_cannot_describe_only_a_substring(self):
        for field, value in (("line_start_1based", True), ("line_end_1based_inclusive", 10**9)):
            data = deepcopy(self.packets["shared"]); data["passages"][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(links.LinkError, "line offsets"):
                links._validate_packet(links.ROOT, "shared", data)
        data = deepcopy(self.packets["shared"])
        row = data["passages"][0]; row["byte_start_0based"] += 1
        row["raw_text"] = row["raw_text"][1:]; row["span_sha256"] = sha256(row["raw_text"].encode()).hexdigest()
        with self.assertRaisesRegex(links.LinkError, "byte/line offsets disagree"):
            links._validate_packet(links.ROOT, "shared", data)

    def test_retained_source_hash_length_and_passage_source_hash(self):
        for kind in self.packets:
            for mutation in ("hash", "length", "source"):
                data = deepcopy(self.packets[kind])
                if mutation == "hash":
                    data["sources"][0]["source_sha256" if kind == "shared" else "sha256"] = "0" * 64
                elif mutation == "length":
                    data["sources"][0]["bytes"] = True
                else:
                    data["passages"][0]["source_id"] = "missing_source"
                with self.subTest(kind=kind, mutation=mutation), self.assertRaises(links.LinkError):
                    links._validate_packet(links.ROOT, kind, data)
        data = deepcopy(self.packets["shared"]); data["passages"][0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(links.LinkError, "passage source hash"):
            links._validate_packet(links.ROOT, "shared", data)

    def test_source_and_passage_inventories_must_be_complete_and_unique(self):
        for kind in self.packets:
            for key in ("sources", "passages"):
                for operation in ("duplicate", "missing"):
                    data = deepcopy(self.packets[kind])
                    if operation == "duplicate": data[key].append(deepcopy(data[key][0]))
                    else: data[key].pop()
                    with self.subTest(kind=kind, key=key, operation=operation), self.assertRaises(links.LinkError):
                        links._validate_packet(links.ROOT, kind, data)

    def test_upstream_pin_and_inventory_are_exact(self):
        for mutation in ("hash", "missing", "extra", "wrong_bytes"):
            data = deepcopy(self.packets["shared"])
            if mutation == "hash": data["upstream_dependencies"][0]["sha256"] = "0" * 64
            elif mutation == "missing": data["upstream_dependencies"].pop()
            elif mutation == "extra": data["upstream_dependencies"].append({"path": "invented", "sha256": "0" * 64})
            else:
                data["upstream_dependencies"][0]["sha256"] = "0" * 64
            with self.subTest(mutation=mutation), self.assertRaises(links.LinkError):
                if mutation == "wrong_bytes":
                    altered = dict(links.DEPENDENCIES); altered[data["upstream_dependencies"][0]["path"]] = "0" * 64
                    with patch.object(links, "DEPENDENCIES", altered):
                        links._validate_packet(links.ROOT, "shared", data)
                else: links._validate_packet(links.ROOT, "shared", data)

    def test_finite_reading_uniqueness_and_references_are_checked(self):
        for mutation in ("duplicate_raw", "cross_reading_alias", "canonical", "missing", "reference", "count_boolean", "authority"):
            data = deepcopy(self.packets["shared"]); r = data["finite_registry"]; a, b = r["readings"][:2]
            if mutation == "duplicate_raw": a["input_surfaces"].append(a["input_surfaces"][0])
            elif mutation == "cross_reading_alias": b["input_surfaces"].append(a["input_surfaces"][0])
            elif mutation == "canonical": a["canonical"] = "not an admitted raw surface"
            elif mutation == "missing": r["readings"].pop()
            elif mutation == "reference": a["source_passages"] = ["unknown"]
            elif mutation == "count_boolean": r["reading_count"] = True
            else: a["authority"] = "FULL_ARABIC"
            with self.subTest(mutation=mutation), self.assertRaises(links.LinkError):
                links._validate_packet(links.ROOT, "shared", data)

    def test_natural_candidates_and_claims_cannot_be_silently_narrowed(self):
        for mutation in ("missing_sense", "invented_sense", "reference", "intent", "all_senses", "alias", "alias_authority"):
            data = deepcopy(self.packets["natural"])
            if mutation == "missing_sense": data["added_senses"].pop()
            elif mutation == "invented_sense": data["added_senses"][0]["sense_id"] = "invented"
            elif mutation == "reference": data["added_senses"][0]["passage_ids"] = ["eye_definition"]
            elif mutation == "intent": data["reading_policy"]["author_intention_established"] = True
            elif mutation == "all_senses": data["reading_policy"]["all_arabic_senses_complete"] = True
            elif mutation == "alias": data["lexical_form_aliases"]["العين"].append("عين")
            else: data["lexical_form_alias_evidence_kind"] = "EXACT_SOURCE_QUOTATION"
            with self.subTest(mutation=mutation), self.assertRaises(links.LinkError):
                links._validate_packet(links.ROOT, "natural", data)

    def test_changed_packet_rejected_before_its_sources_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root / links.PACKETS["shared"][0]
            path.parent.mkdir(parents=True); path.write_text(json.dumps(self.packets["shared"]))
            with self.assertRaisesRegex(links.LinkError, "packet pin differs"):
                links._read_sources(root)

    def test_noncanonical_paths_and_symlink_escape_rejected(self):
        for path in ("/tmp/source", "../source", "a/../b", "a//b", "./source", "a\\b", True):
            with self.subTest(path=path), self.assertRaises(links.LinkError): links._file(links.ROOT, path)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "outside").symlink_to(root.parent, target_is_directory=True)
            with self.assertRaisesRegex(links.LinkError, "escapes root"): links._file(root, "outside/source")

    def test_strict_json_rejects_duplicates_nonfinite_and_invalid_unicode(self):
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'"\xff"', b'"\\ud800"'):
            with self.subTest(data=data), self.assertRaises((ValueError, UnicodeError)): links._strict_json(data)


class SourcedCompiledLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indexes = links._read_sources(links.ROOT)

    def test_explicit_links_have_actual_header_identity_and_bounded_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); compiled = synthetic_catalog(root)
            report = links._compose(root, self.indexes, compiled, links._validate_compiled(root, compiled))
        self.assertEqual(report["referenced_declaration_names"], explicit_names())
        self.assertEqual(report["counts"]["validated_passage_records"], 38)
        self.assertEqual(report["counts"]["distinct_source_byte_spans"], 35)
        self.assertEqual(report["counts"]["distinct_retained_source_files"], 8)
        self.assertEqual(report["counts"]["source_entries"], 11)
        self.assertEqual(report["counts"]["unresolved_supplied_references"], 0)
        self.assertIn("natural::negative_lam", report["passages_without_explicit_theorem_links"])
        self.assertIn("shared::mukhtar_labis_counterexample", report["passages_without_explicit_theorem_links"])
        self.assertTrue(all(edge["declaration_header"].startswith("theorem ") for edge in report["edges"]))
        for key in ("fresh_kernel_check_performed_by_this_command", "linguistic_interpretation_proved",
                    "source_books_fully_formalized", "all_passages_have_matching_theorems", "natural_parser_proved",
                    "python_lean_refinement_proved", "author_intention_established", "world_truth_established",
                    "arabic_completeness_established"):
            self.assertIs(report["claims"][key], False)

    def test_explicit_reference_is_not_namespace_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); compiled = synthetic_catalog(root)
            declarations = links._validate_compiled(root, compiled)
            for name in explicit_names():
                reduced = dict(declarations); del reduced[name]
                with self.subTest(name=name), self.assertRaisesRegex(links.LinkError, "explicit theorem missing"):
                    links._compose(root, self.indexes, compiled, reduced)

    def test_stale_or_added_formal_inputs_and_toolchain_rejected(self):
        for mutation in ("changed", "added", "removed", "producer", "toolchain"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); compiled = synthetic_catalog(root)
                if mutation == "changed": (root / "formal/Nabt/AcquiredSyntaxV3.lean").write_text("changed")
                elif mutation == "added": (root / "formal/New.lean").write_text("new")
                elif mutation == "removed": del compiled["inputs"]["formal/ExportProofCatalog.lean"]
                elif mutation == "producer": (root / "tools/proof_catalog.py").write_text("changed producer")
                else: compiled["lean_toolchain"] = "wrong toolchain"
                with self.assertRaises(links.LinkError): links._validate_compiled(root, compiled)

    def test_cache_is_not_counted_as_project_formal_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); compiled = synthetic_catalog(root)
            cached = root / "formal/.lake/packages/cache.lean"; cached.parent.mkdir(parents=True); cached.write_text("cached")
            links._validate_compiled(root, compiled)

    def test_compiled_exact_manifest_sequence_and_source_binding(self):
        for mutation in ("reorder", "duplicate", "missing", "module", "path", "hash"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); compiled = synthetic_catalog(root); row = compiled["theorems"][0]
                if mutation == "reorder": compiled["theorems"].reverse()
                elif mutation == "duplicate": compiled["theorems"].append(deepcopy(row))
                elif mutation == "missing": compiled["theorems"].pop()
                elif mutation == "module": row["module"] = "Nabt...Bad"
                elif mutation == "path": row["source_path"] = "formal/Nabt/Invented.lean"
                else: row["source_sha256"] = "0" * 64
                with self.assertRaises(links.LinkError): links._validate_compiled(root, compiled)

    def test_canonical_statement_identity_must_resolve(self):
        for mutation in ("missing", "other_statement", "not_self_canonical", "invalid_fingerprint"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); compiled = synthetic_catalog(root); a, b = compiled["theorems"][:2]
                if mutation == "missing": a["canonical_name"] = "Nabt.Invented"
                elif mutation == "other_statement": a["canonical_name"] = b["name"]
                elif mutation == "not_self_canonical": a["canonical_name"] = b["name"]; b["canonical_name"] = a["name"]
                else: a["statement_sha256"] = "not-a-sha"
                with self.assertRaises(links.LinkError): links._validate_compiled(root, compiled)

    def test_universe_and_axiom_boundaries_are_strict(self):
        for key, value in (("universe_parameters", True), ("universe_parameters", -1),
                           ("axioms", ["Custom.extra"]), ("axioms", ["propext", "propext"]),
                           ("proof_dependencies", [False]), ("type_dependencies", ["z", "a"])):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); compiled = synthetic_catalog(root); compiled["theorems"][0][key] = value
                with self.assertRaises(links.LinkError): links._validate_compiled(root, compiled)

    def test_header_range_must_refer_to_named_declaration(self):
        for mutation in ("missing", "boolean", "out_of_bounds", "wrong_theorem"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); compiled = synthetic_catalog(root); row = compiled["theorems"][0]
                if mutation == "missing": del row["range"]
                elif mutation == "boolean": row["range"]["line"] = True
                elif mutation == "out_of_bounds": row["range"]["end_line"] = 10**9
                else: row["range"]["line"] = row["range"]["end_line"] = 1
                with self.assertRaises(links.LinkError): links._statement_header(root, row)

    def test_header_preserves_nested_structure_assignments_in_actual_type(self):
        header = ('theorem projection (x : T) :\n'
                  '  result = {x with decision := licensed "ARTICLE_INITIAL" [⟨112, by decide⟩]}')
        self.assertEqual(links._header_text(header + " := by rfl\n"), header)
        header = 'theorem quoted (x : String := ":=\\\"") /- outer /- := -/ comment -/ : x = x'
        self.assertEqual(links._header_text(header + " := rfl"), header)
        header = 'theorem comment : True -- := not the proof\n'
        self.assertEqual(links._header_text(header + " := by trivial"), header.rstrip())
        for text in ('theorem x : True', 'theorem x (a : T] : True := by trivial', 'theorem x : "bad'):
            with self.subTest(text=text), self.assertRaises(links.LinkError): links._header_text(text)

    def test_actual_compiled_doc_comment_ranges_extract_complete_named_headers(self):
        reference = links.ROOT / "evidence/sourced_acquisition_v3/integration/proof_catalog.json"
        compiled = links._strict_json(reference.read_bytes())
        rows = {row["name"]: row for row in compiled["theorems"]}
        for name in ("Nabt.LinguisticTruth.supported_exact", "Nabt.LinguisticTruth.literal_support_with_false_world"):
            with self.subTest(name=name):
                row = rows[name]
                data = (links.ROOT / row["source_path"]).read_bytes()
                self.assertEqual(sha256(data).hexdigest(), row["source_sha256"])
                line = row["range"]["line"]
                self.assertTrue(data.decode().splitlines()[line - 1].startswith("/--"))
                result = links._statement_header(links.ROOT, row)
                self.assertEqual(result["source_line_1based"], line + 1)
                self.assertTrue(result["declaration_header"].startswith("theorem " + name.rsplit(".", 1)[1]))
                if name.endswith("supported_exact"):
                    self.assertTrue(result["declaration_header"].endswith("∀ r ∈ requirements f c, r.atom.opposite ∉ known"))
                else:
                    self.assertTrue(result["declaration_header"].endswith("¬ (LexicalDenotation.componentFormula context concept).meaning model env"))

    def test_leading_comments_do_not_authorize_search_past_another_declaration(self):
        text = " /-- outer /- nested -/ comment -/\n-- line comment\n theorem selected : True := by trivial"
        self.assertEqual(text[links._declaration_start(text):], "theorem selected : True := by trivial")
        self.assertEqual(links._declaration_start("def other := 1\ntheorem selected : True := by trivial"), 0)
        with self.assertRaisesRegex(links.LinkError, "unterminated leading"):
            links._declaration_start("/-- comment without end\ntheorem selected : True := by trivial")

    def test_build_rechecks_sources_and_formal_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); compiled = synthetic_catalog(root); reference = root / "index.json"
            reference.write_text(json.dumps(compiled))
            with patch.object(links, "_read_sources", return_value=self.indexes) as replay:
                report = links.build_report(root=root, proof_reference=reference)
            self.assertEqual(replay.call_count, 2)
            self.assertEqual(report["compiled_proof_catalog_sha256"], proof_catalog.digest(compiled))
            changed = deepcopy(self.indexes); changed["natural"]["senses"].pop("ayn_gold")
            with patch.object(links, "_read_sources", side_effect=[self.indexes, changed]):
                with self.assertRaisesRegex(links.LinkError, "source replay after"):
                    links.build_report(root=root, proof_reference=reference)
            actual_inputs = links._formal_inputs(root)
            with patch.object(links, "_read_sources", return_value=self.indexes), patch.object(
                    links, "_formal_inputs", side_effect=[actual_inputs, {}]):
                with self.assertRaisesRegex(links.LinkError, "formal inputs after"):
                    links.build_report(root=root, proof_reference=reference)

    def test_cli_explicit_reference_output_and_full_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); compiled = synthetic_catalog(root)
            report = links._compose(root, self.indexes, compiled, links._validate_compiled(root, compiled))
            output = root / "links.json"
            with redirect_stdout(io.StringIO()), patch.object(links, "build_report", return_value=report) as build:
                self.assertEqual(links.main(["--proof-reference", "explicit.json", "--output", str(output)]), 0)
                build.assert_called_with(proof_reference=Path("explicit.json"))
                self.assertEqual(links.main(["--proof-reference", "explicit.json", "--check", str(output)]), 0)
                self.assertEqual(links.main(["--proof-reference", "explicit.json", "--output", str(output)]), 1)
                altered = deepcopy(report); altered["claims"]["world_truth_established"] = True
                output.write_text(json.dumps(altered))
                self.assertEqual(links.main(["--proof-reference", "explicit.json", "--check", str(output)]), 1)
            self.assertEqual(json.loads(output.read_text()), altered)


if __name__ == "__main__":
    unittest.main()

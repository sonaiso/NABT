"""Check pinned article sources and explicit links to a current compiled index.

Run after the native/formal build and proof-catalog gate. This command does not
compile Lean, and a stored catalogue is not itself proof authority. The links
record authored representation obligations; they do not prove faithful Arabic
interpretation or a Python/Lean refinement theorem.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from tools import proof_catalog

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "nabt.article-acquisition-proof-links.v2"
SOURCE_PATH = "evidence/article_acquisition_v2/source_evidence.json"
SOURCE_SHA256 = "d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c"
PROOF_REFERENCE = "evidence/sourced_acquisition_v3/integration/proof_catalog.json"
LAW_ID = "nabt.aligned-acquisition.v2"
SOURCE_HASHES = {
    "qatr": "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d",
    "sibawayhi": "a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625",
    "mukhtar_sihah": "e93f4054f3cddb826a7b3fafd01eac8c4b39b25ed2d92ece7ea093b755776691",
}
PASSAGE_IDS = frozenset({
    "qatr_wasl_fatha", "qatr_case_marks", "qatr_weak_imperative",
    "sibawayhi_article_initial_fatha", "sibawayhi_connected_restart",
    "sibawayhi_sukun_contact", "sibawayhi_long_vowel_contact",
    "sibawayhi_article_sun", "sibawayhi_article_lam_shown",
    "sibawayhi_haqq_article", "mukhtar_haqq", "mukhtar_qawm",
    "mukhtar_ghulam", "mukhtar_labis_counterexample",
    "mukhtar_laib_counterexample", "mukhtar_laqiya",
})
ENTRY_PATTERNS = {
    "ARTICLE_HAQQ": [
        {"head": "ح", "allowed_marks": ["َ"]},
        {"head": "ق", "allowed_marks": ["َّ", "ُّ", "ِّ", "َّ", "ُّ", "ِّ"]},
    ],
    "ARTICLE_QAWM": [
        {"head": "ق", "allowed_marks": ["َ"]},
        {"head": "و", "allowed_marks": ["ْ"]},
        {"head": "م", "allowed_marks": ["َ", "ُ", "ِ"]},
    ],
    "ARTICLE_GHULAM": [
        {"head": "غ", "allowed_marks": ["ُ"]},
        {"head": "ل", "allowed_marks": ["َ"]},
        {"head": "ا", "allowed_marks": [""]},
        {"head": "م", "allowed_marks": ["َ", "ُ", "ِ"]},
    ],
}
ENTRY_PASSAGES = {
    "ARTICLE_HAQQ": ["sibawayhi_haqq_article", "mukhtar_haqq",
                     "sibawayhi_article_initial_fatha", "qatr_case_marks"],
    "ARTICLE_QAWM": ["sibawayhi_article_initial_fatha", "mukhtar_qawm", "qatr_case_marks"],
    "ARTICLE_GHULAM": ["qatr_wasl_fatha", "mukhtar_ghulam", "qatr_case_marks"],
}
CONVENTIONS = frozenset({
    "ARTICLE_CITATION_ONSET", "FINITE_ARTICLE_READING", "EXPLICIT_STEM_VOCALIZATION",
    "TERMINAL_CASE_VARIANTS", "INITIAL_UNICODE_SPELLINGS", "RAW_SOURCE_AND_A116",
    "LOCAL_ENDING_SEPARATE_FROM_ONSET", "SUN_LAM_EXCLUSION",
})
NAMESPACE = "Nabt.AlignedAcquisitionV2."
# These are explicit reviewed obligations, not inferred namespace matches.
OBLIGATIONS = (
    ("partition", ("acquire_spans", "acquire_restores_source", "acquire_offsets_contiguous"), (),
     "Exact original-source partition and offset restoration; an interface property."),
    ("complete_binding", ("acquired_no_pending", "verified_binding"), (),
     "Completion and request/onset binding relative to the installed definitions."),
    ("connected_boundary", ("connected_no_handoff",),
     ("sibawayhi_connected_restart", "sibawayhi_sukun_contact", "sibawayhi_long_vowel_contact"),
     "The implementation refuses connected-mode handoff; it does not prove connected phonology."),
    ("shape_handoff", ("checkedHandoff_sound", "silent_initial_rejected"),
     ("qatr_wasl_fatha",),
     "Existing shape-law handoff and silent-onset rejection, not an acoustic or lexical proof."),
)
ARTICLE_THEOREMS = ("licensed_override_has_finite_witness", "article_onset_cells")


class LinkError(ValueError):
    """Pinned source, field scope or compiled-reference validation failed."""


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise LinkError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json(data: bytes) -> object:
    def reject_constant(value: str) -> None:
        raise LinkError(f"non-finite JSON constant: {value}")

    result = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=_pairs,
                        parse_constant=reject_constant)
    # Reject escaped lone surrogates as well as malformed literal UTF-8.
    proof_catalog.canonical_json(result).encode("utf-8", errors="strict")
    return result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LinkError(message)


def _index(rows: object, key: str) -> dict[str, dict]:
    _require(type(rows) is list, f"{key} collection must be a list")
    result = {}
    for row in rows:
        _require(type(row) is dict, f"malformed {key} row")
        identity = row.get(key)
        _require(type(identity) is str and bool(identity) and identity not in result,
                 f"invalid or repeated {key}")
        result[identity] = row
    return result


def _same(candidate: object, expected: object, label: str) -> None:
    _require(proof_catalog.catalog_matches(candidate, expected), f"invalid {label}")


def _hash(value: object, label: str) -> str:
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"invalid SHA-256: {label}")
    return value


def _references(row: dict, available: dict[str, dict], key: str = "passage_ids") -> list[str]:
    values = row.get(key)
    _require(type(values) is list and all(type(v) is str for v in values)
             and len(values) == len(set(values)) and all(v in available for v in values),
             f"invalid source passage references: {row.get('id')}")
    return values


def _validate_source_payload(root: Path, source: dict) -> dict:
    """Independently check source structure; the public reader also pins all bytes.

    This helper accepts synthetic data for counterexample tests. Passing it does
    not grant a new source packet authority; only _read_source enforces the pin.
    """
    _same(source.get("schema"), "nabt.article-acquisition-source-evidence.v2", "source schema")
    _same(source.get("law_id"), LAW_ID, "source law")
    _same(source.get("alphabet_id"), "nabt.a116.v1", "source alphabet")
    _same(source.get("authority"),
          "SOURCE_IDENTITY_AND_BOUNDED_AUTHORED_INTERPRETATION_NOT_RUNTIME_AUTHORITY", "source authority")
    sources = _index(source.get("sources"), "source_id")
    _require(set(sources) == set(SOURCE_HASHES), "retained source inventory differs")
    source_bytes = {}
    for sid, row in sources.items():
        relative = f"src/nabt/data/source_evidence/{sid}.txt"
        _same(row.get("repository_path"), relative, f"retained source path: {sid}")
        _same(row.get("source_sha256"), SOURCE_HASHES[sid], f"retained source pin: {sid}")
        data = (root / relative).read_bytes()
        _require(sha256(data).hexdigest() == SOURCE_HASHES[sid], f"retained source hash differs: {sid}")
        _require(type(row.get("bytes")) is int and row["bytes"] == len(data), f"retained source length: {sid}")
        _require(row.get("runtime_required") is False, f"retained source runtime scope: {sid}")
        _same(row.get("U+0671_count"), data.decode("utf-8").count("ٱ"), f"retained Unicode count: {sid}")
        source_bytes[sid] = data
    passages = _index(source.get("passages"), "id")
    _require(set(passages) == PASSAGE_IDS, "source passage inventory differs")
    for pid, row in passages.items():
        sid = row.get("source_id")
        _require(sid in source_bytes, f"unknown passage source: {pid}")
        _same(row.get("source_sha256"), SOURCE_HASHES[sid], f"passage source hash: {pid}")
        start, end = row.get("byte_start_0based"), row.get("byte_end_0based_exclusive")
        first, last = row.get("line_start_1based"), row.get("line_end_1based_inclusive")
        data = source_bytes[sid]
        lines = data.splitlines(keepends=True)
        _require(all(type(v) is int for v in (start, end, first, last))
                 and 0 <= start < end <= len(data) and 1 <= first <= last <= len(lines),
                 f"invalid passage offsets: {pid}")
        _require(sum(map(len, lines[:first - 1])) == start and sum(map(len, lines[:last])) == end,
                 f"passage byte/line offsets disagree: {pid}")
        raw = data[start:end]
        _same(row.get("raw_text"), raw.decode("utf-8"), f"passage raw text: {pid}")
        _same(row.get("span_sha256"), sha256(raw).hexdigest(), f"passage span hash: {pid}")
        _same(row.get("evidence_kind"), "NARRATED_LINGUISTIC_EVIDENCE", f"passage evidence kind: {pid}")
    registry = source["finite_registry"]
    _same(registry.get("evidence_kind"), "AUTHOR_CONVENTION", "finite reading evidence kind")
    _same(registry.get("authority"),
          "INSTALLED_FINITE_READING_SPECIFICATION_TO_BE_CHECKED_BY_SEPARATE_VERSIONED_RUNTIME_LAW",
          "finite reading authority")
    _same(registry.get("onset_interpretation"), "word_initial", "finite reading onset")
    _same(registry.get("unsupported_onset"), "connected", "unsupported onset scope")
    _same(registry.get("prefix_pieces"),
          [{"allowed_heads": ["ا", "ٱ"], "allowed_marks": ["", "َ"]},
           {"head": "ل", "allowed_marks": ["ْ"]}], "finite prefix")
    _same(registry.get("terminal_ordinary_marks"), ["َ", "ُ", "ِ"], "terminal explicit vowels")
    entries = _index(registry.get("entries"), "id")
    _require(set(entries) == set(ENTRY_PATTERNS), "finite reading inventory differs")
    for identity, entry in entries.items():
        _same(entry.get("stem_pieces"), ENTRY_PATTERNS[identity], f"finite reading signature: {identity}")
        _same(entry.get("passage_ids"), ENTRY_PASSAGES[identity], f"finite reading source links: {identity}")
        _references(entry, passages)
    conventions = _index(source.get("conventions"), "id")
    _require(set(conventions) == CONVENTIONS, "authored convention inventory differs")
    for row in conventions.values():
        _same(row.get("evidence_kind"), "AUTHOR_CONVENTION", "authored convention kind")
        _references(row, passages)
    for row in source["counterexample_obligations"]:
        if "passage_ids" in row:
            _references(row, passages)
    return {"sources": sources, "passages": passages, "entries": entries}


def _read_source(root: Path) -> tuple[dict, dict]:
    data = (root / SOURCE_PATH).read_bytes()
    _require(sha256(data).hexdigest() == SOURCE_SHA256, "installed source packet pin differs")
    source = _strict_json(data)
    _require(type(source) is dict, "source packet must be an object")
    return source, _validate_source_payload(root, source)


def _formal_inputs(root: Path) -> dict[str, str]:
    formal = root / "formal"
    paths = set(formal.rglob("*.lean")) - set((formal / ".lake").rglob("*.lean"))
    paths.update({formal / "theorems.json", formal / "lean-toolchain", root / "tools/proof_catalog.py"})
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def _validate_compiled(root: Path, compiled: dict) -> dict[str, dict]:
    _same(compiled.get("schema"), proof_catalog.SCHEMA, "compiled catalogue schema")
    _same(compiled.get("authority"), "COMPILED_DECLARATION_INDEX_ONLY", "compiled catalogue authority")
    inputs = _formal_inputs(root)
    _same(compiled.get("inputs"), inputs, "current compiled input inventory/hashes")
    _same(compiled.get("lean_toolchain"), (root / "formal/lean-toolchain").read_text().strip(), "Lean toolchain")
    manifest = _strict_json((root / "formal/theorems.json").read_bytes())["theorems"]
    _require(type(manifest) is list and bool(manifest) and all(type(n) is str for n in manifest)
             and len(manifest) == len(set(manifest)), "invalid current theorem manifest")
    declarations = _index(compiled.get("theorems"), "name")
    _same(list(declarations), manifest, "exact compiled manifest name sequence")
    for name, row in declarations.items():
        module = row.get("module")
        _require(type(module) is str and module.startswith("Nabt.")
                 and all(part.isidentifier() for part in module.split(".")), f"invalid compiled module: {name}")
        path = f"formal/{module.replace('.', '/')}.lean"
        _same(row.get("source_path"), path, f"compiled declaration source path: {name}")
        _require(path in inputs and row.get("source_sha256") == inputs[path], f"unbound compiled source: {name}")
        _hash(row.get("statement_sha256"), f"compiled statement: {name}")
        target = declarations.get(row.get("canonical_name"))
        _require(target is not None and target.get("canonical_name") == target["name"]
                 and target.get("statement_sha256") == row["statement_sha256"], f"invalid canonical identity: {name}")
        _require(type(row.get("universe_parameters")) is int and row["universe_parameters"] >= 0,
                 f"invalid universe parameter count: {name}")
        for key in ("proof_dependencies", "type_dependencies", "axioms"):
            values = row.get(key)
            _require(type(values) is list and all(type(v) is str for v in values)
                     and values == sorted(set(values)), f"invalid {key}: {name}")
        _require(set(row["axioms"]) <= proof_catalog.ALLOWED_AXIOMS, f"unapproved compiled axiom: {name}")
    return declarations


def _compose(source_index: dict, compiled: dict, declarations: dict[str, dict]) -> dict:
    """Pure link construction; callers cannot obtain authority from this helper."""
    nodes = []
    for identity in sorted(source_index["entries"]):
        nodes.append({"id": identity, "kind": "finite_reading",
                      "passage_ids": ENTRY_PASSAGES[identity], "theorems": ARTICLE_THEOREMS,
                      "scope": "Only the frozen finite witness can license this article citation onset; emitted onset is hamza+fatḥa."})
    for identity, names, passages, scope in OBLIGATIONS:
        nodes.append({"id": identity, "kind": "representation_obligation",
                      "passage_ids": list(passages), "theorems": names, "scope": scope})
    edges = []
    for node in nodes:
        for pid in node["passage_ids"]:
            _require(pid in source_index["passages"], f"unresolved link passage: {pid}")
        for short_name in node.pop("theorems"):
            name = NAMESPACE + short_name
            _require(name in declarations, f"explicit theorem missing from compiled catalogue: {name}")
            row = declarations[name]
            target = declarations[row["canonical_name"]]
            edges.append({
                "node_id": node["id"], "source_passage_ids": node["passage_ids"],
                "referenced_declaration": name, "canonical_name": row["canonical_name"],
                "statement_sha256": row["statement_sha256"], "source_path": row["source_path"],
                "source_sha256": row["source_sha256"],
                "canonical_source_path": target["source_path"],
                "canonical_source_sha256": target["source_sha256"],
                "relation": "authored_reference_to_compiled_representation_declaration",
            })
    passage_fields = ("id", "source_id", "source_sha256", "line_start_1based", "line_end_1based_inclusive",
                      "byte_start_0based", "byte_end_0based_exclusive", "span_sha256")
    names = sorted({edge["referenced_declaration"] for edge in edges})
    return {
        "schema": SCHEMA, "law_id": LAW_ID, "alphabet_id": "nabt.a116.v1",
        "authority": "PINNED_SOURCE_AND_COMPILED_REFERENCE_LINK_INDEX_ONLY",
        "source_packet": {"path": SOURCE_PATH, "sha256": SOURCE_SHA256},
        "compiled_proof_catalog_sha256": proof_catalog.digest(compiled),
        "theorem_manifest_sha256": compiled["inputs"]["formal/theorems.json"],
        "lean_toolchain": compiled["lean_toolchain"],
        "counts": {"retained_sources": len(source_index["sources"]), "validated_passages": len(source_index["passages"]),
                   "finite_readings": len(source_index["entries"]), "explicit_reference_edges": len(edges),
                   "referenced_declaration_names": len(names), "unresolved_references": 0},
        "sources": [{key: row[key] for key in ("source_id", "repository_path", "source_sha256", "bytes", "pinned_url")}
                    for _, row in sorted(source_index["sources"].items())],
        "passages": [{key: row[key] for key in passage_fields} for _, row in sorted(source_index["passages"].items())],
        "nodes": nodes, "edges": edges, "referenced_declaration_names": names,
        "claims": {
            "retained_source_bytes_and_spans_match": True,
            "authored_finite_signatures_checked": True,
            "compiled_reference_inputs_match_current_files": True,
            "exact_manifest_names_match_reference": True,
            "fresh_kernel_check_performed_by_this_command": False,
            "linguistic_interpretation_proved": False,
            "python_lean_refinement_proved": False,
            "connected_pronunciation_implemented": False,
            "arabic_completeness_established": False,
        },
    }


def build_report(*, root: Path = ROOT, proof_reference: Path | None = None) -> dict:
    """Validate installed evidence and an already built current proof reference."""
    root = Path(root).resolve()
    _, source_index = _read_source(root)
    reference = Path(proof_reference) if proof_reference is not None else root / PROOF_REFERENCE
    compiled = _strict_json(reference.read_bytes())
    _require(type(compiled) is dict, "compiled reference must be an object")
    declarations = _validate_compiled(root, compiled)
    report = _compose(source_index, compiled, declarations)
    # Detect sampled changes during reading; this is not atomic execution isolation.
    _read_source(root)
    _same(_formal_inputs(root), compiled["inputs"], "formal inputs after crosslink validation")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-reference", type=Path, default=ROOT / PROOF_REFERENCE)
    parser.add_argument("--output", type=Path, help="write a new report; existing paths are never overwritten")
    parser.add_argument("--check", type=Path, help="compare a previous report with the complete current replay")
    args = parser.parse_args(argv)
    try:
        report = build_report(proof_reference=args.proof_reference)
        if args.check:
            _same(_strict_json(args.check.read_bytes()), report, "stored article source links")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"ok": True, **report["counts"], "link_catalog_sha256": proof_catalog.digest(report)}))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

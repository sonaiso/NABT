"""Replay frozen v3 sources and explicitly link bounded obligations to Lean.

This independent checker reads no acquisition gold or runtime proposer. Supply
an already built current compiled catalogue with --proof-reference. This tool
does not compile Lean or prove a source interpretation/Python refinement.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from tools import proof_catalog

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "nabt.sourced-acquisition-proof-links.v3"
PACKETS = {
    "shared": ("evidence/sourced_acquisition_v3/source_evidence.json",
               "64d6d40943ed59a34d16a58de92e11f8672cbdc7ed47ec15f4e341d07594e423"),
    "natural": ("evidence/sourced_acquisition_v3/natural_sources.json",
                "f96689c943b06155f8e91a10fabf7b94ac9ae34200a8682ffa086aad604db7f6"),
}
SOURCE_IDS = {
    "shared": {"sibawayhi", "qatr", "mukhtar_sihah", "sabban", "ibn_aqil",
               "linguistic_inventory", "maqayis"},
    "natural": {"linguistic_inventory", "maqayis", "qatr", "mughni"},
}
PASSAGE_IDS = {
    "shared": set("""qatr_wasl_fatha sibawayhi_article_initial_fatha
        sibawayhi_connected_restart sibawayhi_sukun_contact sibawayhi_long_vowel_contact
        sibawayhi_article_sun sibawayhi_article_lam_shown sibawayhi_haqq_article
        mukhtar_labis_counterexample mukhtar_laib_counterexample qatr_case_marks
        qatr_weak_imperative mukhtar_haqq mukhtar_ghulam mukhtar_qawm mukhtar_laqiya
        mukhtar_walad_and_awlad sibawayhi_awlad_occurrence qatr_dual_plural_endings
        qatr_qumt_pronoun sabban_ta_person ibn_aqil_dhahib natural_eye_senses
        natural_eye_definition natural_spring_definition qatr_nominal_frame
        ibn_aqil_fronting ibn_aqil_fronting_restrictions ibn_aqil_descriptor_dispute
        ibn_aqil_predicate_agreement""".split()),
    "natural": set("""eye_senses cue_required eye_definition spring_definition
        restrictive_adjective adjective_agreement jussive_weak negative_lam""".split()),
}
READING_IDS = {
    f"ARTICLE_{stem}_{case}" for stem in
    ("HAQQ", "QAWM", "GHULAM", "RAJUL", "WALAD", "AWLAD", "AYN", "JARIYA", "BASIRA")
    for case in ("U", "A", "I")
} | {"ARTICLE_WALAD_DUAL", "QUMT_SPEAKER", "QUMT_ADDRESSEE_M", "QUMT_ADDRESSEE_F",
     "DHAHIB_SINGULAR", "DHAHIB_DUAL", "DHAHIB_PLURAL"}
DEPENDENCIES = {
    "evidence/aligned_acquisition_v1/source_evidence.json":
        "269f1aa66756aefc6277e5ff0ef4922dc9ad13fdd2a7bab5e9347649c1fa3cc5",
    "evidence/article_acquisition_v2/source_evidence.json":
        "d5d348e17fd3f34eaa69e5a031956972860dd8dbf3eee25674a265ee4578543c",
    PACKETS["natural"][0]: PACKETS["natural"][1],
}


class LinkError(ValueError):
    """Frozen evidence or an explicit compiled reference failed validation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LinkError(message)


def _same(candidate: object, expected: object, label: str) -> None:
    _require(proof_catalog.catalog_matches(candidate, expected), f"invalid {label}")


def _strict_json(data: bytes) -> object:
    def pairs(rows):
        result = {}
        for key, value in rows:
            _require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise LinkError(f"non-finite JSON constant: {value}")

    result = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                        parse_constant=constant)
    proof_catalog.canonical_json(result).encode("utf-8", errors="strict")
    return result


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


def _hash(value: object, label: str) -> str:
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"invalid SHA-256: {label}")
    return value


def _file(root: Path, relative: object) -> Path:
    _require(type(relative) is str and bool(relative), "invalid repository path")
    parsed = PurePosixPath(relative)
    _require(not parsed.is_absolute() and str(parsed) == relative
             and all(part not in {".", ".."} for part in parsed.parts)
             and "\\" not in relative, f"noncanonical repository path: {relative}")
    path = root / relative
    _require(path.resolve().is_relative_to(root.resolve()), f"repository path escapes root: {relative}")
    return path


def _references(row: dict, key: str, available: dict) -> list[str]:
    values = row.get(key)
    _require(type(values) is list and bool(values) and all(type(v) is str for v in values)
             and len(set(values)) == len(values) and all(v in available for v in values),
             f"invalid {key}: {row.get('id', row.get('designation_id'))}")
    return values


def _validate_packet(root: Path, kind: str, packet: dict) -> dict:
    """Structural replay for tests; only _read_sources grants installed identity."""
    _same(packet.get("schema"), "nabt.sourced-acquisition-source.v3" if kind == "shared"
          else "nabt.natural-acquisition-source.v3", "source schema")
    _same(packet.get("law_id"), "nabt.sourced-acquisition.v3" if kind == "shared"
          else "nabt.natural-acquisition.v3", "source law")
    sources = _index(packet.get("sources"), "source_id")
    _require(set(sources) == SOURCE_IDS[kind], f"{kind} source inventory differs")
    source_bytes, normalized_sources = {}, {}
    for sid, row in sources.items():
        relative = row.get("repository_path" if kind == "shared" else "path")
        digest = _hash(row.get("source_sha256" if kind == "shared" else "sha256"), sid)
        data = _file(root, relative).read_bytes()
        _require(sha256(data).hexdigest() == digest, f"retained source hash differs: {sid}")
        _require(type(row.get("bytes")) is int and row["bytes"] == len(data), f"source byte count: {sid}")
        data.decode("utf-8", errors="strict")
        source_bytes[sid] = data
        normalized_sources[sid] = {"source_id": sid, "path": relative, "sha256": digest, "bytes": len(data)}
    passages = _index(packet.get("passages"), "id" if kind == "shared" else "passage_id")
    _require(set(passages) == PASSAGE_IDS[kind], f"{kind} passage inventory differs")
    normalized_passages = {}
    for pid, row in passages.items():
        sid = row.get("source_id")
        _require(type(sid) is str and sid in source_bytes, f"unknown passage source: {pid}")
        if kind == "shared":
            _same(row.get("source_sha256"), normalized_sources[sid]["sha256"], f"passage source hash: {pid}")
        start = row.get("byte_start_0based" if kind == "shared" else "start_byte")
        end = row.get("byte_end_0based_exclusive" if kind == "shared" else "end_byte")
        data = source_bytes[sid]
        _require(type(start) is int and type(end) is int and 0 <= start < end <= len(data),
                 f"invalid passage offsets: {pid}")
        raw = data[start:end]
        # Decoding the three pieces separately also checks UTF-8 boundaries.
        data[:start].decode("utf-8", errors="strict")
        data[end:].decode("utf-8", errors="strict")
        _same(row.get("raw_text" if kind == "shared" else "quote"), raw.decode("utf-8"), f"passage raw text: {pid}")
        _same(row.get("span_sha256" if kind == "shared" else "sha256"), sha256(raw).hexdigest(), f"passage span hash: {pid}")
        first, last = data[:start].count(b"\n") + 1, data[:end - 1].count(b"\n") + 1
        if "line_start_1based" in row or "line_end_1based_inclusive" in row:
            a, b = row.get("line_start_1based"), row.get("line_end_1based_inclusive")
            _require(type(a) is int and type(b) is int and (a, b) == (first, last), f"invalid passage line offsets: {pid}")
            lines = data.splitlines(keepends=True)
            _require(sum(map(len, lines[:a - 1])) == start and sum(map(len, lines[:b])) == end,
                     f"passage byte/line offsets disagree: {pid}")
        normalized_passages[pid] = {
            "id": f"{kind}::{pid}", "packet": kind, "source_id": sid,
            "source_path": normalized_sources[sid]["path"], "source_sha256": normalized_sources[sid]["sha256"],
            "byte_start_0based": start, "byte_end_0based_exclusive": end,
            "line_start_1based": first, "line_end_1based_inclusive": last,
            "span_sha256": sha256(raw).hexdigest(),
        }
    result = {"sources": normalized_sources, "passages": normalized_passages}
    if kind == "shared":
        _same(packet.get("alphabet_id"), "nabt.a116.v1", "source alphabet")
        _same(packet.get("authority"), "SOURCE_IDENTITY_AND_BOUNDED_AUTHORED_INTERPRETATION_NOT_RUNTIME_AUTHORITY", "source authority")
        deps = _index(packet.get("upstream_dependencies"), "path")
        _same({path: row.get("sha256") for path, row in deps.items()}, DEPENDENCIES, "upstream dependency inventory")
        for path, digest in DEPENDENCIES.items():
            _same(sha256(_file(root, path).read_bytes()).hexdigest(), digest, f"upstream dependency bytes: {path}")
        registry = packet.get("finite_registry")
        _require(type(registry) is dict, "missing finite registry")
        readings = _index(registry.get("readings"), "id")
        _require(set(readings) == READING_IDS, "finite reading inventory differs")
        _same(registry.get("reading_count"), 34, "finite reading count")
        _same(registry.get("surface_count"), 151, "finite surface count")
        _same(registry.get("matching"), "EXACT_RAW_SURFACE_ONLY; no normalization, partial-mark subset rule or generic article prefix rule", "finite matching scope")
        surfaces = set()
        for rid, row in readings.items():
            _same(row.get("authority"), "FINITE_AUTHORED_REPRESENTATION_READING_NOT_EXHAUSTIVE_LEXICAL_ANALYSIS", "finite reading authority")
            _require(row.get("article_kind") in ("moon", "sun", "none"), f"invalid article kind: {rid}")
            _references(row, "source_passages", passages)
            aliases = row.get("input_surfaces")
            _require(type(aliases) is list and bool(aliases) and all(type(s) is str and s for s in aliases)
                     and len(aliases) == len(set(aliases)) and not surfaces.intersection(aliases), f"nonunique finite surfaces: {rid}")
            _require(type(row.get("canonical")) is str and row["canonical"] in aliases, f"canonical reading absent: {rid}")
            surfaces.update(aliases)
        _same(len(surfaces), 151, "actual finite surface count")
        result["readings"] = readings
    else:
        senses = _index(packet.get("added_senses"), "designation_id")
        _require(set(senses) == {"ayn_eye", "ayn_spring", "ayn_gold"}, "natural sense inventory differs")
        for sid, row in senses.items():
            _same(row.get("sense_id"), sid, "sense identity")
            _same(row.get("expression"), "العين", "sense expression")
            _same(row.get("convention"), "linguistic", "sense convention")
            _same(row.get("origin"), "original", "reported sense origin")
            _same(_references(row, "passage_ids", passages), ["eye_senses"], "sense passage")
        _same(packet.get("reading_policy"), {
            "authority": "BOUNDED_LITERAL_READING_UNDER_EXPLICIT_LINGUISTIC_PROFILE",
            "all_installed_alternatives_retained": True, "all_arabic_senses_complete": False,
            "author_intention_established": False, "world_truth_established": False,
            "grammar_certified": False, "general_python_lean_refinement_proved": False,
        }, "natural reading scope")
        _same(packet.get("lexical_form_alias_evidence_kind"), "AUTHORED_FINITE_ORTHOGRAPHIC_AND_INFLECTIONAL_ALIASES_NOT_EXACT_SOURCE_QUOTATIONS", "natural alias authority")
        aliases = packet.get("lexical_form_aliases")
        _require(type(aliases) is dict and set(aliases) == {"العين", "الأسد"}, "natural alias inventory differs")
        seen = set()
        for forms in aliases.values():
            _require(type(forms) is list and bool(forms) and all(type(s) is str and s for s in forms)
                     and len(forms) == len(set(forms)) and not seen.intersection(forms), "nonunique natural aliases")
            seen.update(forms)
        _same(len(seen), 15, "natural alias count")
        result["senses"] = senses
    return result


def _read_sources(root: Path) -> dict:
    indexes = {}
    for kind, (path, digest) in PACKETS.items():
        data = _file(root, path).read_bytes()
        _require(sha256(data).hexdigest() == digest, f"{kind} installed source packet pin differs")
        packet = _strict_json(data)
        _require(type(packet) is dict, "source packet must be an object")
        indexes[kind] = _validate_packet(root, kind, packet)
    # Shared sources must have one identity even though packets use different keys.
    for sid in SOURCE_IDS["shared"] & SOURCE_IDS["natural"]:
        _same(indexes["shared"]["sources"][sid], indexes["natural"]["sources"][sid], f"cross-packet source identity: {sid}")
    for shared, natural in (("natural_eye_senses", "eye_senses"),
                            ("natural_eye_definition", "eye_definition"),
                            ("natural_spring_definition", "spring_definition")):
        a = {k: v for k, v in indexes["shared"]["passages"][shared].items() if k not in {"id", "packet"}}
        b = {k: v for k, v in indexes["natural"]["passages"][natural].items() if k not in {"id", "packet"}}
        _same(a, b, f"copied natural span: {shared}")
    return indexes


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
        _require(type(module) is str and module.startswith("Nabt.") and all(p.isidentifier() for p in module.split(".")), f"invalid compiled module: {name}")
        path = f"formal/{module.replace('.', '/')}.lean"
        _same(row.get("source_path"), path, f"compiled declaration source path: {name}")
        _require(path in inputs and row.get("source_sha256") == inputs[path], f"unbound compiled source: {name}")
        _hash(row.get("statement_sha256"), f"compiled statement: {name}")
        canonical = row.get("canonical_name")
        _require(type(canonical) is str and canonical in declarations, f"missing canonical declaration: {name}")
        target = declarations[canonical]
        _require(target.get("canonical_name") == canonical and target.get("statement_sha256") == row["statement_sha256"], f"invalid canonical identity: {name}")
        _require(type(row.get("universe_parameters")) is int and row["universe_parameters"] >= 0, f"invalid universe parameter count: {name}")
        for key in ("proof_dependencies", "type_dependencies", "axioms"):
            values = row.get(key)
            _require(type(values) is list and all(type(v) is str for v in values) and values == sorted(set(values)), f"invalid {key}: {name}")
        _require(set(row["axioms"]) <= proof_catalog.ALLOWED_AXIOMS, f"unapproved compiled axiom: {name}")
    return declarations


def _header_text(text: str) -> str:
    """Find the proof assignment outside binders, structure updates and strings.

    A plain split at ':=' truncates the types of canonical projection theorems,
    whose conclusions contain structure updates. This is a bounded source
    extractor for the curated declarations, not a Lean parser or type checker.
    """
    stack, i, block = [], 0, 0
    pairs = {"(": ")", "[": "]", "{": "}", "⟨": "⟩"}
    while i < len(text):
        if text.startswith("/-", i):
            block += 1; i += 2
        elif block:
            if text.startswith("-/", i): block -= 1; i += 2
            else: i += 1
        elif text.startswith("--", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
        elif text[i] == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            _require(i < len(text), "unterminated string in curated declaration")
            i += 1
        elif not stack and text.startswith(":=", i):
            return text[:i].rstrip()
        elif text[i] in pairs:
            stack.append(pairs[text[i]]); i += 1
        elif text[i] in pairs.values():
            _require(bool(stack) and stack.pop() == text[i], "unbalanced curated declaration header")
            i += 1
        else:
            i += 1
    raise LinkError("curated declaration proof delimiter missing")


def _declaration_start(text: str) -> int:
    """Skip only leading whitespace/comments in Lean's declaration range.

    Compiled DeclarationRanges include an attached doc comment. Do not search
    indiscriminately for a later theorem: an unrelated declaration or attribute
    prefix is outside this extractor's reviewed syntax and must fail closed.
    """
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("--", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
        elif text.startswith("/-", i):
            depth = 1
            i += 2
            while i < len(text) and depth:
                if text.startswith("/-", i): depth += 1; i += 2
                elif text.startswith("-/", i): depth -= 1; i += 2
                else: i += 1
            _require(depth == 0, "unterminated leading declaration comment")
        else:
            break
    return i


def _statement_header(root: Path, row: dict) -> dict:
    """Expose actual current declaration text as well as its compiled fingerprint."""
    where = row.get("range")
    _require(type(where) is dict, f"missing compiled source range: {row['name']}")
    first, last = where.get("line"), where.get("end_line")
    lines = _file(root, row["source_path"]).read_text(encoding="utf-8").splitlines(keepends=True)
    _require(type(first) is int and type(last) is int and 1 <= first <= last <= len(lines), f"invalid compiled source range: {row['name']}")
    text = "".join(lines[first - 1:last])
    start = _declaration_start(text)
    source_line = first + text[:start].count("\n")
    text = text[start:]
    short = row["name"].rsplit(".", 1)[1]
    _require(re.match(rf"theorem {re.escape(short)}(?:\s|\()", text) is not None and ":=" in text,
             f"unexpected curated declaration header: {row['name']}")
    header = _header_text(text)
    return {"declaration_header": header, "declaration_header_sha256": sha256(header.encode()).hexdigest(),
            "source_line_1based": source_line}


# Each edge is deliberately reviewed, including declarations reused by the
# natural adapter. A source motivates an authored interpretation; the Lean
# theorem establishes only the stated formal relation, not that interpretation.
OBLIGATIONS = (
    ("connected_source_partition", "Nabt.ConnectedAcquisitionV3",
     ("acquire_spans", "acquire_restores_source", "acquire_offsets_contiguous"), (),
     "Acquired realization preserves the original source partition, exact text and contiguous offsets for every Request; no pronunciation or lexical adequacy follows."),
    ("finite_representation_selection", "Nabt.ConnectedAcquisitionV3",
     ("select_has_finite_witness",),
     ("shared::qatr_wasl_fatha", "shared::sibawayhi_article_initial_fatha", "shared::qatr_case_marks"),
     "Conditional selection implies membership in the installed Lean registry and membership of the exact raw surface in that entry. This does not prove that the frozen JSON and Lean tables agree or that an authored marked form occurs in the source."),
    ("canonical_moon_article_projection", "Nabt.ConnectedAcquisitionV3", ("canonical_moon_projection",),
     ("shared::qatr_wasl_fatha", "shared::sibawayhi_article_initial_fatha", "shared::sibawayhi_article_lam_shown"),
     "Given article=moon and a specified nonempty canonical classifyWord result, canonicalEntries replaces only the initial decision with A116 [112], retaining its span and the remaining entries. The theorem does not establish that the canonical word is attested or that a particular raw spelling selects it."),
    ("canonical_sun_article_projection", "Nabt.ConnectedAcquisitionV3", ("canonical_sun_projection",),
     ("shared::sibawayhi_article_sun", "shared::sibawayhi_article_initial_fatha"),
     "Given article=sun and a canonical classifyWord result with initial and lam entries, canonicalEntries sets the initial decision to A116 [112], retains the lam span with empty emission, and retains the tail. It does not separately prove the tail's ra-shadda cells, registry restriction to RAJUL, source attestation or acoustic assimilation."),
    ("connected_article_elision", "Nabt.ConnectedAcquisitionV3",
     ("finite_article_connected_elision", "elision_preserves_spans", "elision_deletes_only_first_cells", "elision_keeps_original_head"),
     ("shared::sibawayhi_connected_restart", "shared::qatr_wasl_fatha"),
     "Given a true shortFinal guard, a selected finite article and connected/joined arguments, realizeWord equals elide. Elide removes only first-piece emitted cells, preserving its original span and all later emissions. No productive sandhi or acoustic theorem is asserted."),
    ("connected_initial_word", "Nabt.ConnectedAcquisitionV3", ("initial_word_retained",),
     ("shared::sibawayhi_connected_restart",),
     "The connected word function with no predecessor retains its supplied entries; citation onset correctness is a separate obligation."),
    ("unsupported_contact", "Nabt.ConnectedAcquisitionV3", ("unguarded_contact_deferred",),
     ("shared::sibawayhi_sukun_contact", "shared::sibawayhi_long_vowel_contact"),
     "A false shortFinal guard yields CONTACT_REPAIR_NOT_IMPLEMENTED deferral. The cited contact repairs are retained scope boundaries, not implemented transformations proved here."),
    ("connected_request_binding", "Nabt.ConnectedAcquisitionV3", ("verified_binding",), (),
     "True Lean verify entails claimed equals acquire of the independently supplied expected Request and binds the complete request. This is not a proof of Python serialization or transport refinement."),
    ("connected_shape_handoff", "Nabt.ConnectedAcquisitionV3", ("checked_phrase_sound", "verified_phrase_sourceful"), (),
     "True checkedPhrase entails connected mode, ACQUIRED status and Law.machine Licensed from state zero for phraseCells. Together with true verify, the claim binds the exact expected Request, restores its source and has whole-phrase licensing under its ending. It proves no source-word, acoustic or lexical adequacy."),
    ("syntax_finite_lexical_relation", "Nabt.AcquiredSyntaxV3", ("lexical_read_exact", "words_read_exact"),
     ("shared::qatr_qumt_pronoun", "shared::sabban_ta_person", "shared::ibn_aqil_dhahib", "shared::mukhtar_walad_and_awlad", "shared::sibawayhi_awlad_occurrence", "shared::qatr_dual_plural_endings"),
     "Exact lexical lookup and word-list lookup agree with the authored full-or-short Lexical relation. Canonical vowels, finite compositions and aliases are not asserted to be verbatim source quotations; WALAD cardinality remains outside this relation."),
    ("syntax_finite_parser", "Nabt.AcquiredSyntaxV3", ("frame_read_exact", "parser_exact", "parser_sound"),
     ("shared::qatr_nominal_frame", "shared::ibn_aqil_fronting", "shared::ibn_aqil_fronting_restrictions", "shared::ibn_aqil_descriptor_dispute"),
     "Frame lookup agrees with its task/lexeme relation. Original-source parse succeeds exactly for SourceGrammar: declared boundary validity, task, and LexicalWords of an installed Frame. This excludes other school, descriptor, dialect and discourse analyses from its domain; it does not refute them."),
    ("syntax_person", "Nabt.AcquiredSyntaxV3", ("person_mapping", "person_surface_roundtrip", "unmarked_no_person"),
     ("shared::qatr_qumt_pronoun", "shared::sabban_ta_person"),
     "The three finite PersonForm mappings preserve first-person unspecified gender and second-person masculine/feminine distinctions; each explicit full/short spelling parses. Three specified unmarked/sukun spellings parse to none. No speaker/addressee identity or complete homograph inventory follows."),
    ("syntax_nominal_agreement_and_order", "Nabt.AcquiredSyntaxV3",
     ("nominal_number_mismatch", "nominal_both_orders", "nominal_source_roundtrip", "nominal_mismatch_rejected"),
     ("shared::qatr_nominal_frame", "shared::qatr_dual_plural_endings", "shared::ibn_aqil_fronting", "shared::ibn_aqil_predicate_agreement"),
     "The authored OrdinaryPredication relation forces equal Number tags; installed frames admit both orders, and short source forms joined by one space parse in both orders. Unequal subject/predicate Number tags are rejected by subject-first readFrame. This is not universal Arabic agreement, full surface mismatch rejection, or world cardinality."),
    ("syntax_source_and_request_binding", "Nabt.AcquiredSyntaxV3",
     ("source_restoration", "source_offsets_contiguous", "verified_binding"), (),
     "Original sourcePieces restore the text with contiguous offsets. True verify binds the claimed result and request to evaluate of the expected Request; no Python or acquisition-chain refinement theorem is asserted."),
    ("natural_candidate_inventory", "Nabt.LinguisticTruth", ("enumeration_exact", "omitted_candidate_rejected"),
     ("natural::eye_senses", "natural::eye_definition", "natural::spring_definition"),
     "Enumeration is exact for Compatible candidates of supplied designation/relation ledgers; omission of a compatible candidate fails completeProposal. The retained source inventory motivates three installed eye senses but these theorems do not establish the ledger's truth, exhaustiveness or Python parser fidelity."),
    ("natural_usage_premises", "Nabt.LinguisticTruth",
     ("used_sense_required", "supported_exact", "changed_frame_cannot_borrow_usage", "literal_supported_by_explicit_evidence"),
     ("natural::cue_required",),
     "Supported assessment requires the fully bound used-sense premise and all signed obligations without opposites. A distinct Frame cannot borrow the literal usage premises. The canonical explicit premise list supports a matched literal designation. These are conditional formal premises, not a proof that an adjective cue establishes actual author intention."),
    ("natural_reported_origin", "Nabt.LinguisticTruth", ("literal_keeps_origin",),
     ("natural::eye_senses",),
     "For a matching designation, literal shape preserves the supplied origin tag. The original tag records the selected source's account and does not decide competing historical accounts of transfer."),
    ("natural_world_separation", "Nabt.LinguisticTruth", ("literal_support_with_false_world",), (),
     "A matched literal designation with explicit premises has a false-world countermodel. Supported lexical classification alone does not establish external existence, referents or utterance truth."),
)


def _compose(root: Path, indexes: dict, compiled: dict, declarations: dict[str, dict]) -> dict:
    nodes, edges = [], []
    all_passages = {row["id"]: row for index in indexes.values() for row in index["passages"].values()}
    for identity, module, names, passage_ids, scope in OBLIGATIONS:
        _require(all(p in all_passages for p in passage_ids), f"unresolved source link: {identity}")
        nodes.append({"id": identity, "source_passage_ids": list(passage_ids), "theorem_scope": scope})
        for short in names:
            name = module + "." + short
            _require(name in declarations, f"explicit theorem missing from compiled catalogue: {name}")
            row = declarations[name]
            _same(row["module"], module, f"explicit declaration module: {name}")
            canonical = declarations[row["canonical_name"]]
            edges.append({"node_id": identity, "source_passage_ids": list(passage_ids),
                          "referenced_declaration": name, "canonical_name": row["canonical_name"],
                          "statement_sha256": row["statement_sha256"],
                          "source_path": row["source_path"], "source_sha256": row["source_sha256"],
                          "canonical_source_path": canonical["source_path"],
                          "canonical_source_sha256": canonical["source_sha256"],
                          "relation": "authored_reference_to_compiled_bounded_declaration",
                          **_statement_header(root, row)})
    names = sorted({edge["referenced_declaration"] for edge in edges})
    linked = {pid for node in nodes for pid in node["source_passage_ids"]}
    sources = {row["path"]: row for index in indexes.values() for row in index["sources"].values()}
    unique_spans = {(p["source_path"], p["byte_start_0based"], p["byte_end_0based_exclusive"]) for p in all_passages.values()}
    return {
        "schema": SCHEMA, "law_ids": ["nabt.sourced-acquisition.v3", "nabt.acquired-syntax.v3", "nabt.natural-acquisition.v3"],
        "alphabet_id": "nabt.a116.v1", "authority": "PINNED_SOURCE_AND_COMPILED_REFERENCE_LINK_INDEX_ONLY",
        "source_packets": [{"id": k, "path": v[0], "sha256": v[1]} for k, v in PACKETS.items()],
        "upstream_dependencies": [{"path": p, "sha256": h} for p, h in sorted(DEPENDENCIES.items())],
        "compiled_proof_catalog_sha256": proof_catalog.digest(compiled),
        "theorem_manifest_sha256": compiled["inputs"]["formal/theorems.json"], "lean_toolchain": compiled["lean_toolchain"],
        "counts": {"source_packets": 2, "source_entries": 11, "distinct_retained_source_files": len(sources),
                   "validated_passage_records": len(all_passages), "distinct_source_byte_spans": len(unique_spans),
                   "shared_finite_readings": len(indexes["shared"]["readings"]), "shared_exact_raw_surfaces": 151,
                   "natural_added_senses": len(indexes["natural"]["senses"]),
                   "curated_obligations": len(nodes), "explicit_reference_edges": len(edges),
                   "referenced_declaration_names": len(names), "passage_records_with_explicit_links": len(linked),
                   "unresolved_supplied_references": 0},
        "sources": [sources[p] for p in sorted(sources)],
        "passages": [all_passages[p] for p in sorted(all_passages)],
        "nodes": nodes, "edges": edges, "referenced_declaration_names": names,
        "passages_without_explicit_theorem_links": sorted(set(all_passages) - linked),
        "scope": "Links are reviewed obligations, not a completeness denominator for Arabic, source books, or the natural parser. Unlinked retained passages include lexical motivations and counterexamples without a claimed matching theorem.",
        "claims": {
            "frozen_packets_sources_spans_and_dependencies_match": True,
            "compiled_reference_inputs_match_current_files": True, "exact_manifest_names_match_reference": True,
            "fresh_kernel_check_performed_by_this_command": False, "linguistic_interpretation_proved": False,
            "source_books_fully_formalized": False, "all_passages_have_matching_theorems": False,
            "natural_parser_proved": False, "python_lean_refinement_proved": False,
            "author_intention_established": False, "world_truth_established": False,
            "arabic_completeness_established": False,
        },
    }


def build_report(*, proof_reference: Path, root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    indexes = _read_sources(root)
    compiled = _strict_json(Path(proof_reference).read_bytes())
    _require(type(compiled) is dict, "compiled reference must be an object")
    declarations = _validate_compiled(root, compiled)
    report = _compose(root, indexes, compiled, declarations)
    # Detect sampled changes during replay; not atomic filesystem isolation.
    _same(_read_sources(root), indexes, "source replay after link composition")
    _same(_formal_inputs(root), compiled["inputs"], "formal inputs after link composition")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-reference", type=Path, required=True, help="current already compiled catalogue")
    parser.add_argument("--output", type=Path, help="write a new report; never overwrite existing files")
    parser.add_argument("--check", type=Path, help="compare the full report with current replay")
    args = parser.parse_args(argv)
    try:
        report = build_report(proof_reference=args.proof_reference)
        if args.check:
            _same(_strict_json(args.check.read_bytes()), report, "stored sourced acquisition links")
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

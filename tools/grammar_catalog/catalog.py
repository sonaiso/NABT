"""Rebuild a retrieval-only catalogue from pinned source bytes and explicit links.

An entry is a namespaced policy record, not a distinct theorem or a count of all
Arabic rules. Raw UTF-8 spans, editions, source limitations and open obligations
remain separate. Nothing in this module licenses a sentence or establishes that
a formal declaration faithfully translates a passage.
"""
from __future__ import annotations

from bisect import bisect_right
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = "src/nabt/data/source_evidence"
SCHEMA = "nabt.grammar-retrieval-catalog.v1"
AUTHORITY = "RETRIEVAL_ONLY"

# Code-owned installed input identities. A submitted hash/manifest cannot change
# these. A new edition/selection requires a reviewed version change here.
INPUT_SHA256 = {
    'evidence/arabic_completion_v6/books/book_source_index_v1.json': 'e7a12c55f5ebaa38297ec63f2236d32e0b20b480c982e23eb59b783e01456054',
    'evidence/arabic_completion_v6/books/qatr_semantic_docket_v1.json': '7ed896f324824271ee67d15676831fb1dc34e252b2f6925b75ef6fc8527ff68a',
    'evidence/arabic_completion_v6/rule_implementation_crosswalk.json': '52f27b7e00e730525c4278d7600f3668495ef75cf327f19a6fe7a81759b4c8a6',
    'src/nabt/data/source_evidence/classical_rule_inventory_v1.json': '6de39f04e6981ec646a9af98ed3ebb600d1c60bcd498ddfc925d6ba44664061d',
    'src/nabt/data/source_evidence/construction_policy.json': '2faa90be033475c458eeabe61cda472c7856a0342803325bef6474c6c88b13f5',
    'src/nabt/data/source_evidence/construction_supplementary_sources_v1.json': '816e3a89aa80138b31f88b8dd33752160468c17b84927623b43fa41def39fdf0',
    'src/nabt/data/source_evidence/construction_supplementary_sources_v2.json': '96f505a0e34964e6b7fc65ed7dfaa6c0f5430c75a51766760495c25295ab1fe7',
    'src/nabt/data/source_evidence/discourse_policy.json': '584dce90517121ba5e1fad8015f50e14b1adad437c6af879753038703222b3b7',
    'src/nabt/data/source_evidence/governor_policy.json': '26fdd34913ccca180bb1bf19bd58d725881117c0d01027f51374fd29d578dfa6',
    'src/nabt/data/source_evidence/imperative_paradigm_v1.json': '1f0a8baec82a0a7cd37217278e3258d12cec4e18b1408b332d32b7eecb95310d',
    'src/nabt/data/source_evidence/inflection_policy.json': '87d28b0d9a23ea3300f033aeef38884132d4863f4906e57dda1ee490c1365f09',
    'src/nabt/data/source_evidence/license_evidence.json': '4a1cfef0eb7ce0647a3da85db59783d59a03502bc175d50a49a5faa392e9e60b',
    'src/nabt/data/source_evidence/morphology_policy.json': '14463f75b6cfa54ed2a9a5ad56b2a595ac87ee0ad97dab43ef6a376079cb3f1a',
    'src/nabt/data/source_evidence/phonological_modes_v1.json': '3cc6781732cdfff3bca8b396c5bea78a72e87c5d89c31ad3bf70b9876578f387',
    'src/nabt/data/source_evidence/pilot_conditions.json': '3ffd79d951a5ce21647441f9b325fd26129dec4d48b3b28d9b39ac0db66a3dd1',
    'src/nabt/data/source_evidence/pilot_examples.json': 'b3e000e455e2551962c332ec16b8814a2dfdc07d90a0f457c0cb6829650ad0ac',
    'src/nabt/data/source_evidence/productive_forms_v1.json': 'faf134dabd4ce9d3718274c04660c1c7a9532d6c6f6a1072f2c1af67978e2003',
    'src/nabt/data/source_evidence/source_lexicon_contexts_v1.json': '3a41aa6df562e1b617eb54207098058bd1150c33bd97b6e4e3ed2503de6edfd6',
    'src/nabt/data/source_evidence/source_lexicon_v1.json': 'd2e3b32712248a3d614ec7831ad2b81fe7c3d8dd0b1ca436782bd8a7e3c67b5f',
    'src/nabt/data/source_evidence/source_manifest.json': '4eb5f589f8a016adcf070cf1995905c78b65c18c1963c0d158f04a5beb349998',
    'src/nabt/data/source_evidence/word_policy.json': 'c03134674fb8702af2d0ff4ce91c06d6b6b2f1422373da52e6449f24d1efd5f1',
}

LOCAL_SOURCE_FILES = {
    "qatr": "qatr.txt", "alfiyya": "alfiyya.txt",
    "sibawayhi": "sibawayhi.txt", "sabban": "sabban.txt",
    "ibn_aqil": "ibn_aqil.txt", "mughni": "mughni.txt",
    "mukhtar_sihah": "mukhtar_sihah.txt",
    # This is an excerpt deposit, not the full original book/offset space.
    "shakhsiyya_j3": "morphology_j3.txt",
}
BOOK_INDEX = "evidence/arabic_completion_v6/books/book_source_index_v1.json"
QATR_DOCKET = "evidence/arabic_completion_v6/books/qatr_semantic_docket_v1.json"
CROSSWALK = "evidence/arabic_completion_v6/rule_implementation_crosswalk.json"


class CatalogError(ValueError):
    """A source, link or proposed catalogue does not match installed inputs."""


def _canonical(value: Any) -> bytes:
    """Only ordinary JSON containers/scalars; no custom equality or NaN."""
    def check(x: Any) -> None:
        if type(x) is dict:
            if any(type(k) is not str for k in x):
                raise CatalogError("JSON object keys must be strings")
            for v in x.values():
                check(v)
        elif type(x) is list:
            for v in x:
                check(v)
        elif x is not None and type(x) not in (str, int, bool):
            raise CatalogError("catalogue permits only JSON strings, integers, booleans and null")
    try:
        check(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise CatalogError("noncanonical catalogue value") from exc


def catalog_sha256(catalog: dict) -> str:
    """Identity only; never an authority claim or substitute for validation."""
    return sha256(_canonical(catalog)).hexdigest()


def _read(root: Path, relative: str) -> bytes:
    path = root / relative
    # No source is permitted to escape a checkout via symlink substitution.
    if path.resolve() != root.resolve() / relative:
        raise CatalogError(f"nonlocal or symlinked input: {relative}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CatalogError(f"missing installed input: {relative}") from exc


def _first(record: dict, *keys: str, default: Any = None) -> Any:
    return next((record[k] for k in keys if k in record), default)


def build_catalog(root: Path = ROOT) -> dict:
    """Replay installed bytes and explicit many-to-many links from scratch.

    The dynamic Lean manifest is recorded only to resolve advertised declaration
    names. Kernel checking and source-to-formal fidelity are separate evidence.
    """
    root = Path(root)
    documents: dict[str, dict] = {}
    inputs = []
    for path, expected in sorted(INPUT_SHA256.items()):
        data = _read(root, path)
        if sha256(data).hexdigest() != expected:
            raise CatalogError(f"installed input hash mismatch: {path}")
        documents[path] = json.loads(data)
        inputs.append({"path": path, "sha256": expected, "bytes": len(data),
                       "identity_policy": "code_pinned"})

    def doc(name: str) -> dict:
        return documents[f"{SOURCE_DIR}/{name}"]

    theorem_path = "formal/theorems.json"
    theorem_bytes = _read(root, theorem_path)
    theorem_manifest = json.loads(theorem_bytes)
    theorem_names = theorem_manifest["theorems"]
    if (type(theorem_names) is not list or
            any(type(n) is not str for n in theorem_names) or
            len(theorem_names) != len(set(theorem_names))):
        raise CatalogError("invalid theorem name manifest")
    known_theorems = set(theorem_names)
    inputs.append({"path": theorem_path, "sha256": sha256(theorem_bytes).hexdigest(),
                   "bytes": len(theorem_bytes),
                   "identity_policy": "observed_name_resolution_only_not_kernel_evidence"})

    sources: dict[str, dict] = {}
    raw_sources: dict[str, bytes] = {}
    line_starts: dict[str, list[int]] = {}

    def add_source(source_id: str, meta: dict, expected: str) -> None:
        filename = LOCAL_SOURCE_FILES[source_id]
        path = f"{SOURCE_DIR}/{filename}"
        raw = _read(root, path)
        if sha256(raw).hexdigest() != expected:
            raise CatalogError(f"source bytes changed: {source_id}")
        try:
            raw.decode("utf-8")
        except UnicodeError as exc:
            raise CatalogError(f"source is not UTF-8: {source_id}") from exc
        attribution = meta.get("attribution", {})
        sources[source_id] = {
            "source_key": f"{source_id}:{expected}", "source_id": source_id,
            "sha256": expected, "local_path": path,
            "title": meta.get("title", attribution.get("title", source_id)),
            "bytes": len(raw), "content_available": True,
            "original_url": _first(meta, "original_url", "pinned_url", default=None),
            "vocalization": "original_bytes_no_invented_diacritics",
            "content_scope": "selected_excerpt_deposit" if source_id == "shakhsiyya_j3" else "available_digital_file",
            "physical_edition_verified": False,
            "whole_book_rules_formalized": False,
        }
        raw_sources[source_id] = raw
        line_starts[source_id] = [0] + [i + 1 for i, b in enumerate(raw) if b == 10]
        inputs.append({"path": path, "sha256": expected, "bytes": len(raw),
                       "identity_policy": "from_code_pinned_source_registry"})

    inventory = doc("classical_rule_inventory_v1.json")
    for s in inventory["sources"]:
        add_source(s["source_id"], s, s["raw_sha256"])
    supplementary = doc("construction_supplementary_sources_v2.json")
    for s in supplementary["sources"]:
        if s["source_id"] not in sources:
            add_source(s["source_id"], s, s["source_sha256"])
    morphology = doc("morphology_policy.json")
    for s in morphology["sources"]:
        if s["id"] not in sources:
            add_source(s["id"], s, s["sha256"])
    if set(sources) != set(LOCAL_SOURCE_FILES):
        raise CatalogError("local source inventory differs from installed schema")

    # Full dictionary files are not installed by this tool. Existing selected
    # lexical evidence elsewhere must not be promoted to full-text availability.
    for sid, s in doc("source_lexicon_v1.json")["sources"].items():
        sources[sid] = {
            "source_key": f"{sid}:{s['sha256']}", "source_id": sid,
            "sha256": s["sha256"], "local_path": None,
            "title": s["title"], "bytes": s["bytes"], "content_available": False,
            "original_url": s["pinned_url"], "content_scope": "external_full_text_not_installed",
            "physical_edition_verified": False, "whole_book_rules_formalized": False,
        }

    passages: dict[str, dict] = {}
    items: list[dict] = []
    rules: list[dict] = []

    def add_passage(record: dict, origin: str, kind: str,
                    sid: str | None = None) -> str:
        sid = sid or record["source_id"]
        if sid not in raw_sources:
            raise CatalogError(f"span references unavailable source: {sid}")
        start = _first(record, "start", "start_byte", "byte_start_0based")
        end = _first(record, "end", "end_byte", "byte_end_0based_exclusive")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw_sources[sid]):
            raise CatalogError(f"invalid span offsets: {origin}")
        raw = raw_sources[sid][start:end]
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise CatalogError(f"span splits UTF-8 code point: {origin}") from exc
        digest = sha256(raw).hexdigest()
        claimed_hash = _first(record, "span_sha256", "sha256")
        if claimed_hash is not None and claimed_hash != digest:
            raise CatalogError(f"span hash mismatch: {origin}")
        claimed_text = _first(record, "raw_text", "text")
        if claimed_text is not None and claimed_text != text:
            raise CatalogError(f"span quotation mismatch: {origin}")
        if "source_sha256" in record and record["source_sha256"] != sources[sid]["sha256"]:
            raise CatalogError(f"span edition mismatch: {origin}")
        identity = [sources[sid]["source_key"], start, end, digest]
        pid = "passage:" + sha256(_canonical(identity)).hexdigest()
        line_start = bisect_right(line_starts[sid], start)
        line_end = bisect_right(line_starts[sid], end - 1)
        claimed_start = _first(record, "line_start", "line_start_1based")
        claimed_end = _first(record, "line_end", "line_end_1based_inclusive")
        if claimed_start is not None and (type(claimed_start) is not int or claimed_start != line_start):
            raise CatalogError(f"span line start mismatch: {origin}")
        if claimed_end is not None and (type(claimed_end) is not int or claimed_end != line_end):
            raise CatalogError(f"span line end mismatch: {origin}")
        if pid not in passages:
            passages[pid] = {
                "passage_id": pid, "source_key": sources[sid]["source_key"],
                "source_id": sid, "start": start, "end": end, "sha256": digest,
                "raw_text": text, "kind": kind, "kinds": [], "origins": [],
                "line_start": line_start, "line_end": line_end,
                "attribution": record.get("layer", "passage_attribution_not_independently_adjudicated"),
            }
        p = passages[pid]
        if "original_start" in record:
            p["original_offsets"] = {"start": record["original_start"],
                                     "end": record["original_end"],
                                     "replay_status": "original_full_text_not_installed"}
        if kind not in p["kinds"]:
            p["kinds"].append(kind)
        if origin not in p["origins"]:
            p["origins"].append(origin)
        return pid

    def checked_names(names: list[str]) -> list[str]:
        if any(type(n) is not str or n not in known_theorems for n in names):
            raise CatalogError("explicit formal reference absent from installed name manifest")
        return sorted(set(names))

    crosswalk = documents[CROSSWALK]
    crosswalk_by_id = {r["rule_id"]: r for r in crosswalk["rows"]}
    runtime_ids = {r["rule_id"] for r in crosswalk["rows"]
                   if r["status"] == "new_scoped_conditional_operator"}
    if len(runtime_ids) != 24:
        raise CatalogError("installed conditional operator crosswalk changed")

    def add_rule(registry: str, local_id: str, record: dict, pids: list[str],
                 scope: str, *, theorem_refs: list[str] | None = None,
                 runtime_id: str | None = None) -> None:
        rules.append({
            "rule_key": f"{registry}::{local_id}", "registry_id": registry,
            "local_id": local_id,
            "title": record.get("title", local_id.replace("_", " ")),
            "description": _first(record, "premise_scope", "interpretation", "interpretation_note", "scope", default=scope),
            "keywords": sorted(set([local_id, record.get("category", "")] + record.get("keywords", [])) - {""}),
            "source_passage_ids": sorted(set(pids)),
            "theorem_names": checked_names(theorem_refs or []),
            "theorem_link_status": "explicit_reference_only_not_source_fidelity_proof",
            "runtime_rule_id": runtime_id,
            "source_status": record.get("status", "authored_selected_policy"),
            "scope": record.get("scope", scope),
            "full_source_rule_complete": False,
        })

    # Complete available-byte partition is a retrieval collection, not a rule
    # denominator. Recheck adjacency independently of the manifest's counts.
    index = documents[BOOK_INDEX]
    book_segment_count = 0
    book_partition_bytes = 0
    for b in index["books"]:
        sid = b["source_id"]
        if b["sha256"] != sources[sid]["sha256"]:
            raise CatalogError(f"book index edition mismatch: {sid}")
        position = 0
        for segment in b["segments"]:
            if type(segment["start"]) is not int or segment["start"] != position:
                raise CatalogError(f"book partition gap or overlap: {sid}")
            add_passage(segment, f"book_segment:{segment['segment_id']}", "book_segment", sid)
            position = segment["end"]
            book_segment_count += 1
        if position != len(raw_sources[sid]) or position != b["size_bytes"]:
            raise CatalogError(f"book partition does not cover available bytes: {sid}")
        book_partition_bytes += position
        sources[sid]["extent_status"] = b["extent_status"]
        sources[sid]["extent_notes"] = b["extent_notes"]

    for r in inventory["rules"]:
        rid = r["rule_id"]
        pids = [add_passage(s, f"{inventory['schema']}::{rid}", "selected_rule_witness") for s in r["source_spans"]]
        linked = crosswalk_by_id[rid]
        names = [linked["formal_exactness_theorem"]] if "formal_exactness_theorem" in linked else []
        add_rule(inventory["schema"], rid, r, pids, inventory["scope"],
                 theorem_refs=names, runtime_id=rid if rid in runtime_ids else None)
        rules[-1]["implementation_status"] = linked["status"]
        rules[-1]["implemented_scope"] = linked["implemented_scope"]

    for name in ("construction_policy.json", "discourse_policy.json", "governor_policy.json", "inflection_policy.json"):
        policy = doc(name)
        for r in policy["passages"]:
            rid = r["rule"]
            pid = add_passage(r, f"{policy['policy_id']}::{rid}", "selected_rule_witness")
            add_rule(policy["policy_id"], rid, r, [pid], policy["scope"])

    word = doc("word_policy.json")
    for r in word["rules"]:
        pid = add_passage(r, f"{word['policy_id']}::{r['id']}", "selected_rule_witness")
        add_rule(word["policy_id"], r["id"], r, [pid], "Selected word classification policy; not a complete parser")

    morphology_passages = {}
    for s in morphology["sources"]:
        for p in s["passages"]:
            pid = add_passage(p, f"{morphology['schema']}:{p['id']}", "selected_rule_witness", s["id"])
            morphology_passages[p["id"]] = pid
    for r in morphology["rules"]:
        add_rule(morphology["schema"], r["id"], r,
                 [morphology_passages[x] for x in r["passage_ids"]], morphology["scope"])

    # Other schemas are explicit evidence items, never additional "rules".
    for r in inventory["reference_constructions"]:
        pids = [add_passage(s, f"reference:{r['case_id']}", "reference_construction") for s in r["source_spans"]]
        items.append({"item_id": f"reference:{r['case_id']}", "kind": "reference_construction",
                      "title": r["case_id"], "description": r["input"],
                      "source_passage_ids": pids, "theorem_names": [],
                      "record": r})
    for name, key in (("imperative_paradigm_v1.json", "passages"),
                      ("phonological_modes_v1.json", "passages"),
                      ("productive_forms_v1.json", "passages"),
                      ("source_lexicon_contexts_v1.json", "contexts"),
                      ("source_manifest.json", "selected_spans")):
        policy = doc(name)
        for i, r in enumerate(policy[key]):
            rid = str(_first(r, "passage_id", "id", "span_id", default=i))
            item_id = f"{name}:{rid}"
            pid = add_passage(r, item_id, "selected_evidence")
            items.append({"item_id": item_id, "kind": "selected_evidence",
                          "title": rid, "description": _first(r, "interpretation", "selection_note", default=""),
                          "source_passage_ids": [pid], "theorem_names": []})

    # Pilot prescription/cue spans are kept apart from rule and attestation
    # counts. Only explicitly described span fields are traversed.
    for name, idkey in (("pilot_examples.json", "record_id"), ("pilot_conditions.json", "condition_id")):
        for r in doc(name)["records"]:
            iid = f"{name}:{r[idkey]}"
            parts = list(r.get("evidence_parts", [])) + list(r.get("cue_parts", []))
            parts += [r[k] for k in ("cue", "target", "marker") if k in r]
            pids = [add_passage(p, iid, "pilot_evidence_part", r["source_id"]) for p in parts]
            items.append({"item_id": iid, "kind": "pilot_" + r["kind"],
                          "title": r[idkey], "description": r.get("interpretation_note", ""),
                          "source_passage_ids": sorted(set(pids)), "theorem_names": [],
                          "context_span_id": r["context_span_id"]})

    docket = documents[QATR_DOCKET]
    if docket["source_sha256"] != sources["qatr"]["sha256"]:
        raise CatalogError("Qatr docket edition mismatch")
    for s in docket["sections"]:
        sid = s["section_id"]
        pid = add_passage(s, f"qatr_docket:{sid}", "semantic_docket_section", "qatr")
        names = checked_names([ref["declaration"] for ref in s["existing_formal_references"]])
        items.append({"item_id": sid, "kind": "semantic_docket_section",
                      "title": s["title"], "description": s["extraction_status"],
                      "source_passage_ids": [pid], "theorem_names": names,
                      "section_complete": False})
        for obligation in s["extraction_obligations"]:
            items.append({"item_id": obligation["obligation_id"], "kind": "open_obligation",
                          "title": obligation["statement"], "description": obligation["status"],
                          "source_passage_ids": [pid], "theorem_names": [],
                          "section_id": sid})

    if len(rules) != 125 or len({r["rule_key"] for r in rules}) != len(rules):
        raise CatalogError("namespaced policy denominator differs from installed selection")
    if len({i["item_id"] for i in items}) != len(items):
        raise CatalogError("duplicate evidence item identity")
    for p in passages.values():
        p["origins"].sort()
        p["kinds"].sort()
    return {
        "schema": SCHEMA, "authority": AUTHORITY,
        "sources": sorted(sources.values(), key=lambda r: r["source_key"]),
        "passages": sorted(passages.values(), key=lambda r: r["passage_id"]),
        "rules": sorted(rules, key=lambda r: r["rule_key"]),
        "items": sorted(items, key=lambda r: r["item_id"]),
        "coverage": {
            "available_source_files": len(raw_sources),
            "unavailable_external_full_texts": sum(not s["content_available"] for s in sources.values()),
            "partitioned_grammar_books": len(index["books"]),
            "book_partition_segments": book_segment_count,
            "book_partition_bytes": book_partition_bytes,
            "unique_passages": len(passages), "namespaced_policy_entries": len(rules),
            "installed_conditional_operators": len(runtime_ids),
            "evidence_items": len(items),
            "rule_denominator_scope": "125 installed namespaced entries, not distinct semantic rules or all Arabic",
            "theorem_manifest_scope": "advertised name resolution only; compile audit is separate",
            "whole_book_rule_denominator": None,
            "whole_arabic_coverage": None,
            "whole_book_complete": False, "whole_arabic_complete": False,
        },
        "inputs": sorted(inputs, key=lambda r: r["path"]),
    }


def validate_catalog(candidate: dict, root: Path = ROOT) -> dict:
    """Reject any change, even with a recomputed caller-provided digest.

    Return the freshly rebuilt catalogue so downstream tools need not trust or
    retain a mutable caller object after validation. JSON-byte comparison keeps
    booleans distinct from integers (Python equality alone would not).
    """
    if type(candidate) is not dict:
        raise CatalogError("catalogue must be a JSON object")
    submitted = _canonical(candidate)
    installed = build_catalog(root)
    if submitted != _canonical(installed):
        raise CatalogError("proposed catalogue differs from installed source/link replay")
    return installed

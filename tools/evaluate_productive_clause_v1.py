#!/usr/bin/env python3
"""Replay the preimplementation, authored productive-clause matrix.

The oracle is independent of the producer but exposed, not a blind test.
The unchanged v1 bootstrap owns fresh source-only imports. A source/native
freeze binds this execution; neither hashes nor this finite result establish
unrestricted grammar, actual reference, intention, or external truth.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = "tools/evaluate_aligned_acquisition.py"
BOOTSTRAP_SHA256 = "50b8e45b821818180854f6990324ea255206913ade849ee97c4fd5b5a0d056cb"
SOURCE_COMMIT = "34acd468c2568b3236818d1f72b92b9651a6f070"
MATRIX_COMMIT = "7ca87dcda09427641ad346fa1108eb2c87382f22"
GOLD_PATH = "evidence/productive_clause_v1/cases.json"
GOLD_SHA256 = "5a6de98a71551c3a1dc0870c15de52b10f50e5233c145c033664c7c500b008f1"
SOURCE_PATH = "evidence/productive_clause_v1/source_scope.json"
SOURCE_PINS = {
    "docs/PRODUCTIVE_CLAUSE_V1_SPEC.md": "ff0d244a5fdd102b34855a18e426475091f240183c43383d7fbd6ce5992493bb",
    SOURCE_PATH: "eb3a1d93730c4a402bce2561afb8934d1f76853ca31fe8ad1167c33ed08d4f17",
    "evidence/productive_clause_v1/acceptance_protocol.json": "8adfb5b35af609e152c1c19879fa328ae97e365838e72994ee22500e7db27c25",
}
MATRIX_PINS = {
    GOLD_PATH: GOLD_SHA256,
    "evidence/productive_clause_v1/GOLD_METHOD.md": "e67aa0570e65138e5c2bfbed366f1bbe41519141f87086c1c56ba9a33bfd3748",
}
PINS = {**SOURCE_PINS, **MATRIX_PINS}
EVALUATOR_ID = "nabt.productive-clause-evaluator.v1.review1"
EVALUATOR_REVIEW = {
    "original_commit": "3d42187e7491e6e74ce89d8f2792efe40ce7d5f8",
    "original_evaluator_sha256": "3fb9e43ec2ffa1f8e9992bfc5fac291b69db8b7f118d998a9a1edb07635c394d",
    "change": "Order projected roles by source word_index; preserve gold and producer outputs.",
    "validation_phase": "exposed_only",
}
SCHEMA = "nabt.productive-clause-code-freeze.v1.review1"
RESULT_SCHEMA = "nabt.productive-clause-evaluation.v1.review1"
LAW_ID = "nabt.productive-clause.v1"
COMPOSITE_LAW_ID = "nabt.acquired-productive-clause.v1"
SLICE_COUNTS = {"positive_in_scope": 100, "negative_in_scope": 50, "outside_scope": 50}
INPUT_FIELDS = ("text", "source_id", "revision", "scope", "ending", "onset")
COORDS = ("raw", "start", "end", "byte_start", "byte_end")
SEPARATORS = frozenset(' \t\r\n.،؛,:!?؟()[]{}«»"“”')
JOIN_GATE_ORDER = ("source_evidence_checked", "source_acquired", "acquisition_native_checked",
    "source_shapes", "syntax_native_checked", "finite_grammar_reading", "same_source_binding",
    "source_alignment", "scope_modes")
JOIN_GATES = frozenset(JOIN_GATE_ORDER)
NATIVE_PATHS = frozenset("formal/.lake/build/bin/" + name for name in
    ("alignedAcquisition", "licensedInference", "connectedAcquisitionV3", "productiveClauseV1"))
REFERENCES = frozenset("evidence/productive_clause_v1/integration/" + name + ".json" for name in
    ("proof_catalog", "grammar_link_summary", "mantuq_proof_links", "linguistic_proof_links",
     "licensed_proof_links", "article_proof_links", "sourced_proof_links"))
V3_SOURCE_PATH = "evidence/sourced_acquisition_v3/source_evidence.json"
EXTRA_PATHS = frozenset(PINS) | REFERENCES | frozenset({
    "evidence/aligned_acquisition_v1/gold.json", V3_SOURCE_PATH,
    "evidence/operator_traceability_v1/registry.json", "formal/theorems.json", "Makefile",
    "tools/aligned_acquisition.mk", "tools/article_acquisition.mk", "tools/sourced_acquisition_v3.mk",
    "tools/productive_clause_v1.mk", "integrations/current_proof_references.mk",
    "tools/evaluate_productive_clause_v1.py", "tools/freeze_productive_clause_v1.py",
    "tools/productive_clause_v1.py", "tools/productive_clause_cli.py",
    "tests/test_productive_clause_v1.py", "tests/test_productive_clause_evaluator.py",
    "formal/Nabt/ProductiveClauseV1.lean", "formal/ProductiveClauseV1Main.lean",
    "integrations/grammar_catalog.mk", "integrations/mantuq_inference.mk",
    "integrations/linguistic_truth.mk", "integrations/licensed_inference.mk",
    ".github/workflows/aligned-acquisition.yml"})


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def same(left, right):
    """JSON comparison retains bool/int and integer/float distinctions."""
    try:
        return wire(left) == wire(right)
    except (TypeError, ValueError, RecursionError):
        return False


def digest(raw):
    return sha256(raw).hexdigest()


def load_bootstrap():
    path = ROOT / BOOTSTRAP_PATH
    raw = path.read_bytes()
    if path.resolve() != path or digest(raw) != BOOTSTRAP_SHA256:
        raise ValueError("trusted source-only bootstrap differs")
    module = ModuleType("_nabt_productive_clause_bootstrap")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def packets_at(guard, commit):
    return [guard.parse_json(guard.git("show", commit + ":" + name, binary=True))
            for name in (SOURCE_PATH, V3_SOURCE_PATH)]


def required_paths(guard, inventory, inference_sources, packets):
    result = guard.required_freeze_paths(inventory, inference_sources) | set(EXTRA_PATHS)
    for packet in packets:
        entries = ([(row, "local_path") for row in packet.get("passages", []) if "local_path" in row]
                   + [(row, "repository_path" if "repository_path" in row else "path")
                      for row in packet.get("sources", [])]
                   + [(row, "path") for row in packet.get("upstream_dependencies", [])])
        for row, field in entries:
            name = row[field]
            guard.local_path(name)
            result.add(name)
    return result


def verify_freeze(path, phase):
    if phase != "exposed":
        raise ValueError("evaluator review1 accepts exposed reruns only; preserve original first attempts")
    guard = load_bootstrap()
    envelope, fingerprint = guard.load_json(path)
    if (envelope.get("schema") != SCHEMA or envelope.get("evaluator_id") != EVALUATOR_ID or
            envelope.get("evaluator_review") != EVALUATOR_REVIEW or envelope.get("content_pins") != PINS or
            envelope.get("source_commit") != SOURCE_COMMIT or envelope.get("matrix_commit") != MATRIX_COMMIT or
            envelope.get("bootstrap") != {"path": BOOTSTRAP_PATH, "sha256": BOOTSTRAP_SHA256}):
        raise ValueError("freeze schema, chronology or code-owned pins differ")
    inner = envelope.get("baseline")
    if type(inner) is not dict or type(inner.get("native")) is not dict or set(inner["native"]) != NATIVE_PATHS:
        raise ValueError("freeze requires exactly the four declared executables")
    # Reuse the old source/stdlib/import boundary. Its original v1 first-run
    # chronology is not ours, so validate its contents in exposed mode.
    with tempfile.TemporaryDirectory(prefix="nabt-clause-freeze-") as directory:
        baseline = Path(directory) / "baseline.json"
        baseline.write_text(wire(inner), encoding="utf-8")
        _, evidence = guard.verify_freeze(baseline, "exposed", guard.GOLD_PATH)
    commit = inner["commit"]
    inventory = set(guard.git("ls-files", "-z").split("\0")) | set(
        guard.git("ls-tree", "-r", "--name-only", "-z", commit).split("\0"))
    inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
    required = required_paths(guard, inventory, inference, packets_at(guard, commit))
    if not required <= set(inner["files"]):
        raise ValueError("missing required frozen inputs: " + ", ".join(sorted(required - set(inner["files"]))))
    for name, expected in {**PINS, BOOTSTRAP_PATH: BOOTSTRAP_SHA256}.items():
        if inner["files"].get(name) != expected:
            raise ValueError("frozen content pin differs: " + name)
    for name, expected in inner["native"].items():
        native = guard.local_path(name)
        if not native.is_file() or not os.access(native, os.X_OK) or digest(native.read_bytes()) != expected:
            raise ValueError("required native executable unavailable or changed: " + name)
    if phase == "first":
        if guard.git("rev-parse", "HEAD") != commit or commit in {SOURCE_COMMIT, MATRIX_COMMIT}:
            raise ValueError("first execution requires a later committed implementation HEAD")
        guard.git("merge-base", "--is-ancestor", SOURCE_COMMIT, MATRIX_COMMIT)
        guard.git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
        for name, expected in SOURCE_PINS.items():
            if digest(guard.git("show", SOURCE_COMMIT + ":" + name, binary=True)) != expected:
                raise ValueError("source-phase content differs: " + name)
        for name, expected in PINS.items():
            if digest(guard.git("show", MATRIX_COMMIT + ":" + name, binary=True)) != expected:
                raise ValueError("matrix-phase content differs: " + name)
    return envelope, {"manifest_sha256": fingerprint, "commit": commit,
        "evaluator_id": EVALUATOR_ID, "evaluator_review": EVALUATOR_REVIEW,
        "evaluator_sha256": inner["files"]["tools/evaluate_productive_clause_v1.py"],
        "source_commit": SOURCE_COMMIT, "matrix_commit": MATRIX_COMMIT,
        "local_source_matrix_implementation_chronology_verified": phase == "first",
        "requested_first_execution": phase == "first", "blind": False, "held_out_lexemes": False,
        "chronology_scope": "Local preimplementation source and authored matrix commits; exposed to implementers. Not a blind validation.",
        "baseline": evidence}


def initial_snapshot(guard, inner, phase):
    before = guard.snapshot(inner, ROOT / GOLD_PATH)
    bad = [name for hashes in (inner["files"], inner["native"]) for name, expected in hashes.items()
           if before["files"].get(name) != expected]
    if before["gold_sha256"] != GOLD_SHA256:
        bad.append("independent matrix")
    if phase == "first" and before["head"] != inner["commit"]:
        bad.append("first execution HEAD")
    if bad:
        raise ValueError("initial snapshot differs from validated freeze: " + ", ".join(sorted(bad)))
    return before


def load_gold(guard):
    gold, actual = guard.load_json(ROOT / GOLD_PATH)
    if actual != GOLD_SHA256 or gold.get("schema") != "nabt.productive-clause.cases.v1":
        raise ValueError("independent matrix content pin or schema differs")
    cases = gold.get("cases")
    if type(cases) is not list or len(cases) != 200:
        raise ValueError("independent matrix denominator differs")
    ids, slices, frames = set(), Counter(), defaultdict(list)
    for case in cases:
        if type(case) is not dict or any(type(case.get(key)) is not str for key in ("id", "slice", "family", "surface_variant")):
            raise ValueError("malformed case identity")
        if not case["id"] or case["id"] in ids or case["slice"] not in SLICE_COUNTS:
            raise ValueError("duplicate, empty or unknown case identity")
        ids.add(case["id"]); slices[case["slice"]] += 1
        request, expected = case.get("input"), case.get("expected")
        if type(request) is not dict or set(request) != set(INPUT_FIELDS) or any(type(request[k]) is not str for k in INPUT_FIELDS):
            raise ValueError("malformed input binding")
        request["text"].encode("utf-8", "strict")
        if type(expected) is not dict or expected.get("syntax_status") not in {"LICENSED_CLAUSE", "REJECTED_IN_SCOPE", "DEFER"}:
            raise ValueError("malformed expected syntax status")
        if expected.get("establishes_world_truth") is not False or expected.get("entails_exclusivity") is not False:
            raise ValueError("oracle must not establish world truth or exclusivity")
        if case["slice"] == "positive_in_scope":
            if (type(case.get("frame_id")) is not str or not case["frame_id"] or
                    expected["syntax_status"] != "LICENSED_CLAUSE" or type(expected.get("reading")) is not dict or
                    type(expected.get("roles")) is not list or len(expected["roles"]) != 3 or
                    type(expected.get("word_cells")) is not list or type(expected.get("word_spans")) is not list):
                raise ValueError("positive case requires complete independent projections")
            frames[case["frame_id"]].append(case["surface_variant"])
        elif expected.get("roles") != [] or expected.get("reading") is not None:
            raise ValueError("nonpositive case must contain no reading or roles")
    if dict(slices) != SLICE_COUNTS or len(frames) != 50 or any(
            sorted(variants) != ["full_stop", "no_full_stop"] for variants in frames.values()):
        raise ValueError("matrix slice or paired-frame populations differ")
    return gold


def fields(value, wanted):
    return type(value) is dict and all(key in value and same(value[key], target) for key, target in wanted.items())


def source_summary():
    """Expected certificate links come from the pinned source packet, not runtime."""
    packet, fingerprint = load_bootstrap().load_json(ROOT / SOURCE_PATH)
    if fingerprint != PINS[SOURCE_PATH]:
        raise ValueError("source packet differs from the independent pin")
    return {"schema": packet["schema"], "sha256": fingerprint,
        "sources": len(packet["sources"]), "passages": len(packet["passages"]),
        "passage_ids": sorted(row["id"] for row in packet["passages"]),
        "lexical_sources": [{"surface": row["surface"], "lexeme_id": row["lexeme_id"],
                             "source_refs": row["source_refs"]} for row in packet["lexical_readings"]],
        "authority": "SOURCE_IDENTITY_AND_AUTHORED_SCOPE"}


def span(text, start, end):
    return dict(raw=text[start:end], start=start, end=end,
                byte_start=len(text[:start].encode("utf-8")), byte_end=len(text[:end].encode("utf-8")))


def word_spans(text):
    result, cursor = [], 0
    while cursor < len(text):
        if text[cursor] in SEPARATORS:
            cursor += 1
            continue
        start = cursor
        while cursor < len(text) and text[cursor] not in SEPARATORS:
            cursor += 1
        result.append(span(text, start, cursor))
    return result


def partition(pieces, text):
    if type(pieces) is not list:
        return False
    cursor = 0
    for piece in pieces:
        if type(piece) is not dict:
            return False
        start, end = piece.get("start"), piece.get("end")
        if type(start) is not int or type(end) is not int or start != cursor or not start < end <= len(text):
            return False
        if not fields(piece, span(text, start, end)):
            return False
        cursor = end
    return cursor == len(text)


def reading_projection(native):
    """Project native fields to the independently frozen oracle vocabulary."""
    reading = native.get("reading")
    if reading is None:
        return {"reading": None, "roles": [], "role_spans_valid": True}
    tokens = native.get("tokens")
    if type(reading) is not dict or type(tokens) is not list:
        return {"reading": None, "roles": None, "role_spans_valid": False}
    indices = [reading.get(key) for key in ("verb_index", "subject_index", "object_index")]
    if any(type(i) is not int or not 0 <= i < len(tokens) for i in indices) or len(set(indices)) != 3:
        return {"reading": None, "roles": None, "role_spans_valid": False}
    roles, aligned = [], same(reading.get("source_words"), tokens)
    for role, label, index in zip(("verb", "agent", "patient"), ("verb", "subject", "object"), indices):
        token = tokens[index]
        if type(token) is not dict or not set((*COORDS, "lexeme", "category", "nominal_case")) <= set(token):
            return {"reading": None, "roles": None, "role_spans_valid": False}
        roles.append({"role": role, "word_index": index, "lexeme_id": token.get("lexeme"),
                      "nominal_case": token.get("nominal_case")})
        aligned = aligned and same(reading.get(label + "_source"), token)
        aligned = aligned and same(reading.get(label + "_lexeme"), token.get("lexeme"))
    aligned = (aligned and indices[0] == 0 and tokens[indices[0]].get("category") == "verb" and
        all(tokens[i].get("category") == "proper_name" for i in indices[1:]) and
        reading.get("subject_case") == tokens[indices[1]].get("nominal_case") == "nom" and
        reading.get("object_case") == tokens[indices[2]].get("nominal_case") == "acc" and
        reading.get("referents") is None and reading.get("world_truth") is None)
    return {"reading": {"verb_id": reading.get("verb_lexeme"), "tense": reading.get("tense"),
        "voice": reading.get("voice"), "order": reading.get("order"),
        "agent_word_index": indices[1], "patient_word_index": indices[2]},
        # The frozen oracle lists role assignments in source-occurrence order.
        "roles": sorted(roles, key=lambda row: row["word_index"]), "role_spans_valid": bool(aligned)}


def expected_reading_id(expected):
    if expected["reading"] is None:
        return None
    roles = {row["role"]: row["lexeme_id"] for row in expected["roles"]}
    return "_".join((expected["reading"]["verb_id"], roles["agent"], roles["patient"],
                     expected["reading"]["order"]))


def candidate_consistent(report, native, syntax_checked, reading_id):
    """Check the finite diagnostic relation without calling producer helpers."""
    status = native.get("status")
    exact = syntax_checked and status in {"LICENSED_CLAUSE", "REJECTED_IN_SCOPE"}
    licensed = syntax_checked and status == "LICENSED_CLAUSE" and native.get("reading") is not None
    complete = report.get("chain_complete") is True
    gates = report.get("gates")
    if type(gates) is not dict or set(gates) != JOIN_GATES or any(type(v) is not bool for v in gates.values()):
        return False
    blocked = [key for key in JOIN_GATE_ORDER if not gates[key]]
    if not same(report.get("blocked_by"), blocked):
        return False
    expected = {"domain_id": LAW_ID, "unit": "scoped_syntactic_reading",
        "completeness_scope": "installed_finite_grammar", "count_mode": "EXACT" if exact else "UNMEASURED",
        "count": (1 if licensed else 0) if exact else None,
        "hartley_bits": 0.0 if licensed and exact else None,
        "unknown_reason": None if exact else "NATIVE_READING_NOT_WITHIN_VERIFIED_SCOPE",
        "candidates": [{"id": reading_id, "state": "LICENSED" if complete else "PENDING",
                        "obligations": [] if complete else blocked}] if licensed else [],
        "world_truth_established": False}
    return same(report.get("candidate_space"), expected)


def audit_clause(case, report, checks, expected_source=None):
    request, expected = case["input"], case["expected"]
    text = request["text"]; binding = {key: request[key] for key in INPUT_FIELDS if key != "text"}
    if type(report) is not dict:
        raise ValueError("producer report must be an object")
    acquired = report.get("acquisition")
    acquisition_audit = checks.audit_report("connected", acquired, **request)
    syntax = report.get("syntax")
    syntax = syntax if type(syntax) is dict else {}
    native = syntax.get("native_result")
    native = native if type(native) is dict else {}
    projection = reading_projection(native)
    tokens = native.get("tokens")
    native_spans = ([{key: token.get(key) for key in COORDS} for token in tokens]
                    if type(tokens) is list and all(type(token) is dict for token in tokens) else None)
    source_checks = {
        "outer_binding": fields(report, {"schema": "nabt.acquired-productive-clause-result.v1",
            "law_id": COMPOSITE_LAW_ID, "binding": binding,
            "source_sha256": digest(text.encode("utf-8"))}),
        "native_binding": fields(native, {**request, "law_id": LAW_ID}),
        "native_source_restoration": partition(native.get("source_pieces"), text),
        "native_token_spans": same(native_spans, word_spans(text)),
        "native_status_binding": same(syntax.get("status"), native.get("status")),
        "role_source_binding": projection["role_spans_valid"],
    }
    spans_match = None if expected["word_spans"] is None else same(native_spans, expected["word_spans"])
    inner_acquisition = acquired.get("acquisition") if type(acquired) is dict else None
    words = inner_acquisition.get("words") if type(inner_acquisition) is dict else None
    actual_cells = [word.get("cells") for word in words] if type(words) is list and all(type(w) is dict for w in words) else None
    cells_match = None if expected["word_cells"] is None else same(actual_cells, expected["word_cells"])
    denials = all(report.get(name) is False for name in
        ("world_truth_established", "referents_established", "entails_exclusivity", "all_arabic_complete"))
    typed = all(type(report.get(name)) is bool for name in ("verified", "chain_complete"))
    syntax_checked = syntax.get("verified") is True and all(source_checks.values())
    reading_id = expected_reading_id(expected)
    syntax_match = (syntax_checked and same(native.get("status"), expected["syntax_status"]) and
        same(projection["reading"], expected["reading"]) and same(projection["roles"], expected["roles"]) and
        fields(native, {"reading_id": reading_id}) and spans_match is not False and denials)
    syntax_grant = syntax.get("verified") is True and (
        native.get("status") == "LICENSED_CLAUSE" or native.get("reading") is not None)
    joined_grant = (report.get("chain_complete") is True or report.get("verified") is True or
        report.get("reading") is not None or report.get("status") == "LICENSED_CLAUSE")
    gates = report.get("gates")
    all_gates = type(gates) is dict and set(gates) == JOIN_GATES and all(value is True for value in gates.values())
    acq_safe = all(acquisition_audit[key] is True for key in ("source_safe", "chain_safe", "claim_safe"))
    acq_claimed = type(acquired) is dict and (acquired.get("status") == "ACQUIRED" or
        acquired.get("verified") is True or acquired.get("shape_verified") is True)
    acq_complete = (type(acquired) is dict and acquired.get("status") == "ACQUIRED" and
        acquired.get("verified") is True and acquired.get("shape_verified") is True and
        acq_safe)
    source_evidence = report.get("source_evidence")
    source_evidence_valid = same(source_evidence, source_summary() if expected_source is None else expected_source)
    candidate_valid = candidate_consistent(report, native, syntax_checked, reading_id)
    candidate = report.get("candidate_space")
    candidate_rows = candidate.get("candidates") if type(candidate) is dict else None
    candidate_grant = type(candidate_rows) is list and any(
        type(row) is dict and row.get("state") == "LICENSED" for row in candidate_rows)
    positive = case["slice"] == "positive_in_scope"
    joined_valid = (positive and syntax_match and cells_match is True and spans_match is True and
        acq_complete and all_gates and report.get("blocked_by") == [] and source_evidence_valid and typed and denials and
        candidate_valid and
        report.get("chain_complete") is True and report.get("verified") is True and
        report.get("status") == native.get("status") == "LICENSED_CLAUSE" and
        same(report.get("reading"), native.get("reading")))
    rejection_valid = (not positive and expected["syntax_status"] == "REJECTED_IN_SCOPE" and
        syntax_match and acq_complete and cells_match is True and spans_match is True and
        source_evidence_valid and candidate_valid and typed and denials and
        type(gates) is dict and set(gates) == JOIN_GATES and
        all(value is (key != "finite_grammar_reading") for key, value in gates.items()) and
        report.get("verified") is False and report.get("chain_complete") is False and report.get("reading") is None)
    false_authorization = ((syntax_grant and not syntax_match) or (joined_grant and not joined_valid) or
                           (acq_claimed and not acq_safe) or (candidate_grant and not joined_valid)
                           or (report.get("status") == "REJECTED_IN_SCOPE" and not rejection_valid)
                           or not denials or not typed)
    control = (not positive and syntax_match and not joined_grant and
               report.get("status") == expected["syntax_status"] and report.get("reading") is None and
               candidate_valid and (expected["syntax_status"] != "REJECTED_IN_SCOPE" or rejection_valid))
    return {"source_checks": source_checks, "acquisition_audit": acquisition_audit,
        "source_evidence_valid": source_evidence_valid,
        "candidate_space_consistent": candidate_valid,
        "syntax_contract_match": bool(syntax_match and not false_authorization),
        "acquisition_complete": bool(acq_complete and cells_match is True and not false_authorization),
        "word_spans_match": spans_match, "word_cells_match": cells_match,
        "roles_match": same(projection["roles"], expected["roles"]),
        "reading_match": same(projection["reading"], expected["reading"]),
        "syntax_claimed": syntax_grant, "chain_claimed": joined_grant,
        "complete_chain": bool(joined_valid and not false_authorization),
        "control_match": bool(control and not false_authorization),
        "false_authorization": bool(false_authorization),
        "authority_denials_valid": denials, "typed_flags": typed}


def evaluate_case(case, modules):
    report = modules["reader"].evaluate(**case["input"])
    audit = audit_clause(case, report, modules["checks"], modules["source_summary"])
    return {"id": case["id"], "slice": case["slice"], "family": case["family"],
        "frame_id": case["frame_id"], "surface_variant": case["surface_variant"],
        **audit, "raw_result": report}


def counts(rows):
    positives = [r for r in rows if r["slice"] == "positive_in_scope"]
    negative = [r for r in rows if r["slice"] == "negative_in_scope"]
    outside = [r for r in rows if r["slice"] == "outside_scope"]
    frames = defaultdict(list)
    for row in positives:
        frames[row["frame_id"]].append(row)
    frame_results = {key: len(group) == 2 and
        {r["surface_variant"] for r in group} == {"no_full_stop", "full_stop"} and
        all(r["complete_chain"] for r in group) for key, group in sorted(frames.items())}
    axes = {}
    for key in ("word_cells_match", "word_spans_match", "roles_match", "reading_match"):
        measured = [r for r in rows if r[key] is not None]
        axes[key] = {"measured": len(measured), "correct": sum(r[key] is True for r in measured),
                     "unmeasured": len(rows) - len(measured)}
    return {"cases": len(rows), "syntax_contracts": sum(r["syntax_contract_match"] for r in rows),
        "candidate_space_consistent": sum(r["candidate_space_consistent"] for r in rows),
        "positive_surfaces": {"required": len(positives), "complete": sum(r["complete_chain"] for r in positives),
            "misses": [r["id"] for r in positives if not r["complete_chain"]]},
        "positive_frames": {"required": len(frames), "complete": sum(frame_results.values()),
                            "outcomes": frame_results},
        "positive_acquisition": {"required": len(positives),
            "complete": sum(r["acquisition_complete"] for r in positives),
            "misses": [r["id"] for r in positives if not r["acquisition_complete"]]},
        "negative_in_scope": {"required": len(negative), "correct": sum(r["control_match"] for r in negative),
                              "false_authorizations": sum(r["false_authorization"] for r in negative)},
        "outside_scope": {"required": len(outside), "correct": sum(r["control_match"] for r in outside),
                          "false_authorizations": sum(r["false_authorization"] for r in outside)},
        "false_authorizations": sum(r["false_authorization"] for r in rows), "projection_axes": axes,
        "statuses": dict(Counter(r["raw_result"].get("status", "MISSING") for r in rows))}


def acceptance(summary, integrity):
    checks = {"execution_integrity": integrity,
        "matrix_population": summary["cases"] == 200,
        "positive_surfaces": summary["positive_surfaces"]["required"] == 100 and summary["positive_surfaces"]["complete"] >= 95,
        "positive_frames": summary["positive_frames"]["required"] == 50 and summary["positive_frames"]["complete"] >= 48,
        "syntax_contracts": summary["syntax_contracts"] >= 195,
        "candidate_diagnostic_consistency": summary["candidate_space_consistent"] == 200,
        "negative_controls": summary["negative_in_scope"]["required"] == summary["negative_in_scope"]["correct"] == 50,
        "outside_controls": summary["outside_scope"]["required"] == summary["outside_scope"]["correct"] == 50,
        "no_observed_false_authorizations": summary["false_authorizations"] == 0}
    return {"passed": all(checks.values()), "checks": checks}


def run(envelope, evidence, phase):
    guard = load_bootstrap(); inner = envelope["baseline"]
    before = initial_snapshot(guard, inner, phase)
    gold = load_gold(guard)
    expected_source = source_summary()
    with guard.frozen_runtime(inner) as imports:
        modules = {"reader": importlib.import_module("tools.productive_clause_v1"),
                   "checks": importlib.import_module("tools.sourced_acquisition_v3_checks"),
                   "source_summary": expected_source}
        rows = [evaluate_case(case, modules) for case in gold["cases"]]
        after = guard.snapshot(inner, ROOT / GOLD_PATH)
        imports.audit_origins()
        wrong = sorted(name for name, actual in imports.executed.items() if inner["files"].get(name) != actual)
        loaded = {}
        for module in tuple(sys.modules.values()):
            filename = getattr(module, "__file__", None)
            if filename:
                path = Path(filename).resolve()
                if path.suffix == ".py" and path.is_relative_to(ROOT):
                    loaded[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    uncovered = sorted(set(loaded) - set(inner["files"]))
    loaded_wrong = sorted(name for name, actual in loaded.items() if inner["files"].get(name) != actual)
    integrity = before == after and not wrong and not uncovered and not loaded_wrong
    summary = counts(rows)
    return {"schema": RESULT_SCHEMA, "evaluator_id": EVALUATOR_ID,
        "evaluator_review": EVALUATOR_REVIEW, "phase": phase,
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Authored exposed finite grammar: 200 cases, 100 positive surfaces over 50 frames; no held-out lexeme or all-Arabic completeness claim.",
        "summary": summary, "acceptance_gate": acceptance(summary, bool(integrity)),
        "execution_evidence": {**evidence, "before": before, "after": after,
            "initial_snapshot_matches_freeze": True, "integrity_valid": bool(integrity),
            "runtime_import_policy": "fresh-frozen-source-only.v1", "executed_repository_python": imports.executed,
            "executed_hash_mismatches": wrong, "loaded_repository_python": loaded,
            "uncovered_modules": uncovered, "loaded_hash_mismatches": loaded_wrong,
            "python": sys.version, "platform": platform.platform(),
            "command": list(sys.argv),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()},
        "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        report = {"schema": RESULT_SCHEMA, "evaluator_id": EVALUATOR_ID,
                  "evaluator_review": EVALUATOR_REVIEW, "phase": args.phase, "status": "ATTEMPT_STARTED",
                  "started_at_utc": datetime.now(timezone.utc).isoformat(), "gold_sha256": GOLD_SHA256}
        stream.write(wire(report) + "\n"); stream.flush(); os.fsync(stream.fileno())
        stage = "preflight"
        try:
            freeze, evidence = verify_freeze(args.code_freeze, args.phase)
            stage = "execution"; report = run(freeze, evidence, args.phase)
        except Exception as exc:
            report = {**report, "status": "EVALUATOR_FAILURE", "failure_stage": stage,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}
        stream.seek(0); json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
    print(wire({key: value for key, value in report.items() if key in
                {"summary", "acceptance_gate", "status", "failure_stage", "error"}}))
    return 0 if report.get("acceptance_gate", {}).get("passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())

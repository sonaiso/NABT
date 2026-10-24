#!/usr/bin/env python3
"""Replay independently authored recursive-algebra contracts without gold-fed plans.

Requests are built only from the operation, input and frozen fixtures. Gold is
consulted after every request is fixed. An absent carrier map, gate interpreter,
inverse evaluator or source-bound role premise is UNMEASURED, never a pass.
The CLI's zero exit status means the *measured* contract gate passed; it is not
a claim of complete coverage or acquisition of Arabic grammar.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "evidence/recursive_algebra/independent_v1/material_v2.json"
MATERIAL_SHA = "2d030838c7fa4ccf5a8f0d45ed554000a197e23a94449648d8011be4bf77a048"
SCHEMA = "nabt.recursive-bridge.independent-measurement.v1"
LAW = "nabt.recursive-source-bridge.v1"
SCOPE = "structural_source_binding_and_conditional_interpretations"
NUMBER_DOMAIN = "nabt.recursive-structural-cantor.v1"
SOURCE_FIELDS = ("source_id", "revision", "scope_id", "atomization_id")
ENVELOPE = {"law_id", "scope", "conditional", "acquisition_measured", "grammar_certified", "status", "op"}
TAG = {"rule_id": 0, "reading_id": 0, "class_id": 0, "requirements": []}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def equal(left, right):
    """Wire equality deliberately separates Boolean, integer and float values."""
    return canonical(left) == canonical(right)


def nat(value):
    require(type(value) is int and value >= 0, "Expected a natural number, not Boolean/float")
    return value


def fields(value, allowed, required=None):
    require(type(value) is dict, "Expected a JSON object")
    require(set(value) <= set(allowed), "Undeclared output fields: " + repr(set(value) - set(allowed)))
    require(set(allowed if required is None else required) <= set(value), "Missing required output fields")


def exact(value, wanted, message):
    require(equal(value, wanted), message)


def file_ref(path):
    path = Path(path).resolve()
    digest, size = sha256(), 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
            size += len(block)
    result = {"path": str(path), "bytes": size, "sha256": digest.hexdigest()}
    if path.is_relative_to(ROOT):
        result["repository_path"] = path.relative_to(ROOT).as_posix()
    return result


def resolve_ref(reference):
    """Repository evidence remains replayable after cloning into a new path."""
    if "repository_path" in reference:
        relative = Path(reference["repository_path"])
        require(not relative.is_absolute() and ".." not in relative.parts,
                "Repository artifact path may not escape the checkout")
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT.resolve()), "Repository artifact symlink escapes the checkout")
    else:
        path = Path(reference["path"]).resolve()
    actual = file_ref(path)
    exact(actual["sha256"], reference["sha256"], "Artifact digest differs: " + str(path))
    exact(actual["bytes"], reference["bytes"], "Artifact size differs: " + str(path))
    return path


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def load_material():
    raw = MATERIAL.read_bytes()
    exact(sha256(raw).hexdigest(), MATERIAL_SHA, "Frozen material changed")
    material = parse(raw)
    exact(material["schema"], "nabt.recursive-algebra.independent-material.v2", "Material schema")
    exact(material["case_count"], 40, "Material count")
    require(len(material["cases"]) == 40 and len({c["case_id"] for c in material["cases"]}) == 40,
            "Missing or duplicate material cases")
    return material


def mutate(value, changes):
    value = deepcopy(value)
    for change in changes:
        target = value
        for key in change["path"][:-1]:
            target = target[key]
        last = change["path"][-1]
        if "remove_index" in change:
            del target[last][change["remove_index"]]
        else:
            target[last] = deepcopy(change["value"])
    return value


def boundaries(text):
    result = [0]
    for character in text:
        result.append(result[-1] + len(character.encode("utf-8")))
    return result


def source(spec):
    require(spec["atomization_id"] == "unicode_scalars_with_exact_utf8.v1", "Unmapped atomization")
    return {"source_id": nat(spec["source_id"]), "revision": nat(spec["revision"]),
            "scope_id": nat(spec["scope_id"]), "atomization_id": 1, "atoms": list(spec["text"])}


def scalar_span(spec, interval):
    require(type(interval) is list and len(interval) == 2, "Expected byte interval")
    start, stop = map(nat, interval)
    cuts = boundaries(spec["text"])
    require(start < stop and start in cuts and stop in cuts, "Unrepresentable UTF-8 byte interval")
    return {**{key: source(spec)[key] for key in SOURCE_FIELDS},
            "start": cuts.index(start), "stop": cuts.index(stop)}


def atom_at(src, position):
    atoms = src["atoms"]
    require(0 <= position < len(atoms), "Atom outside source")
    return {"op": "atom", "source": deepcopy(src), "before": atoms[:position],
            "value": atoms[position], "after": atoms[position + 1:]}


def join_trees(trees):
    require(bool(trees), "No empty source occurrence may be manufactured")
    if len(trees) == 1:
        return deepcopy(trees[0])
    middle = len(trees) // 2
    return {"op": "join", "tag": deepcopy(TAG),
            "left": join_trees(trees[:middle]), "right": join_trees(trees[middle:])}


def host_tree(src, host):
    return join_trees([atom_at(src, position) for position in range(host["start"], host["stop"])])


def string_number(text):
    """Declared injective UTF-8 string label encoding, not a radical alphabet map."""
    return int.from_bytes(b"\x01" + text.encode("utf-8"), "big")


def core_seed(spec):
    if spec["kind"] == "lexical":
        return {"kind": "lexical", "entry": nat(spec["entry"])}
    values = spec.get("values", spec.get("radicals"))
    require(spec["kind"] in ("root3", "root4"), "Unknown seed kind")
    require(len(values) == int(spec["kind"][-1]), "Root arity")
    return {"kind": spec["kind"], "radicals": [nat(n) for n in values]}


def core_tree(spec):
    op = spec.get("kind", spec.get("op"))
    if op == "leaf":
        return {"op": op, "seed": core_seed(spec["seed"])}
    rule = nat(spec.get("rule_id", spec.get("rule")))
    if op == "unary":
        return {"op": op, "rule": rule, "child": core_tree(spec["child"])}
    require(op == "binary", "Unknown tree constructor")
    return {"op": op, "rule": rule, "left": core_tree(spec["left"]), "right": core_tree(spec["right"])}


def metadata(spec, host, reading_id, registry="independent.source-bridge.v1"):
    src = source(spec)
    return {"registry_id": registry, "reading_id": reading_id, "source": src,
            "host": host, "host_tree": host_tree(src, host), "morphology": None,
            "section": None, "roles": [], "evidence_ids": [], "required": [],
            "provenance": "source_reconstruction", "unresolved": ["UNINTERPRETED_AUTHORED_SOURCE_PROPOSAL"]}


def annotated(tree, meta):
    if tree["op"] == "leaf":
        return {**deepcopy(tree), "metadata": deepcopy(meta)}
    if tree["op"] == "unary":
        return {"op": "unary", "rule": tree["rule"], "metadata": deepcopy(meta),
                "child": annotated(tree["child"], meta)}
    return {"op": "binary", "rule": tree["rule"], "metadata": deepcopy(meta),
            "left": annotated(tree["left"], meta), "right": annotated(tree["right"], meta)}


def reading_node(original, current=None, supplied_tree=None):
    """Freeze the template before input mutations; bad alignment is not repaired."""
    current = original if current is None else current
    spec = current["source"]
    host = scalar_span(spec, current["host_byte_span"])
    meta = metadata(spec, host, current["reading_id"], current["catalog_id"])
    meta["section"] = current.get("category_claim")
    meta["roles"] = deepcopy(current.get("role_claims", []))
    if current["seed_kind"] == "lexical":
        seed = {"kind": "lexical", "entry": string_number(current["lexical_entry_id"])}
    else:
        root = current["root"]
        seed = {"kind": current["seed_kind"], "radicals": [ord(c) for c in root]}
        pattern = []
        for row in original["alignment"]:
            if row["origin"] != "boundary":
                pattern.append({"slot": row["root_index"]} if row["origin"] == "radical"
                               else {"literal": row["text"]})
        aligned = []
        for row in current["alignment"]:
            if row["origin"] == "boundary":
                continue
            loc = scalar_span(spec, row["byte_span"])
            require(loc["stop"] == loc["start"] + 1, "Alignment span is not one scalar")
            origin = ({"kind": "radical", "index": row["root_index"]} if row["origin"] == "radical"
                      else {"kind": "literal", "value": row["text"]})
            aligned.append({"pattern_position": row["position"], "source_position": loc["start"], "origin": origin})
        meta["morphology"] = {"catalog_id": current["template_id"], "registry_id": current["catalog_id"],
                              "reading_id": current["reading_id"],
                              "reading": {"arity": len(root), "root": root, "pattern": pattern},
                              "alignment": aligned}
    return annotated(supplied_tree or {"op": "leaf", "seed": seed}, meta)


def assess_request(node, inventory):
    return {"op": "bridge_assess", "node": node, "inventory": inventory,
            "interpreted": [], "offered": []}


def native_read(spec):
    return {"op": "transport_read", "text": spec["text"],
            # The unchanged source reader accepts [a-z][a-z0-9_]*. Decimal
            # natural components with named separators retain both IDs.
            "source_id": "authored_s" + str(nat(spec["source_id"])) + "_r" + str(nat(spec["revision"])),
            "scope": canonical([spec["scope_id"], spec["atomization_id"]])}


def build_case_plan(operation, inp, fixtures):
    """Input-only planning boundary. This function never receives a gold object."""
    inp, fixtures = deepcopy(inp), deepcopy(fixtures)
    plan = {"operation": operation, "requests": [], "notes": []}

    def add(backend, label, request):
        plan["requests"].append({"backend": backend, "label": label, "request": request})

    if operation == "align_reading":
        original = fixtures[inp["fixture"]]
        current = mutate(original, inp.get("mutations", []))
        plan["reading"] = current
        bad_spans = []
        for row in current.get("alignment", []):
            try:
                scalar_span(current["source"], row["byte_span"])
            except ValueError:
                bad_spans.append(row["byte_span"])
        if bad_spans:
            for index, interval in enumerate(bad_spans):
                add("native", "span_" + str(index), {**native_read(current["source"]), "op": "check_span", "byte_span": interval})
            plan["notes"].append("Partial UTF-8 intervals use the actual Python byte-to-scalar boundary; no scalar is invented.")
        else:
            node = reading_node(original, current)
            registered = inp.get("registered_source", current["source"])
            add("lean", "binding", assess_request(node, [source(registered)]))
            if "mutations" not in inp:
                add("native", "transport", native_read(current["source"]))
    elif operation == "join_source_spans":
        src = source(inp["source"])
        spans = [scalar_span(inp["source"], interval) for interval in inp["spans"]]
        host = {**spans[0], "stop": spans[-1]["stop"]}
        meta = metadata(inp["source"], host, "authored.original-adjacency")
        meta["host_tree"] = join_trees([host_tree(src, span) for span in spans])
        add("lean", "binding", assess_request({"op": "leaf", "seed": {"kind": "lexical", "entry": 0},
                                                "metadata": meta}, [src]))
    elif operation == "compare_readings":
        for side in ("left", "right"):
            original = fixtures[inp[side + "_fixture"]]
            current = mutate(original, inp.get(side + "_mutations", []))
            plan[side + "_reading"] = current
            add("lean", side, assess_request(reading_node(original, current), [source(current["source"])]))
        if equal(plan["left_reading"]["source"], plan["right_reading"]["source"]):
            add("native", "transport", native_read(plan["left_reading"]["source"]))
    elif operation == "compare_sources":
        for side in ("left", "right"):
            add("native", side, {**native_read(inp[side]), "op": "source_view"})
    elif operation in ("assess_recursive", "withdraw_and_reassess"):
        plan["notes"].append("UNMEASURED: opaque radicals [0,1,2] have no declared mapping to the Arabic reading; repairing the fixture would change its input. Gate, face and residual interpretation are also not supplied by this protocol.")
        # Preserve the simplest unchanged target as a diagnostic only. No ledger
        # assertion is scored from this source-invalid baseline.
        if set(inp) == {"fixture"}:
            target = fixtures[inp["fixture"]]["target"]
            tree = core_tree(target["tree"])
            node = reading_node(target["reading"], supplied_tree=tree)
            add("lean", "opaque_seed_diagnostic", assess_request(node, [source(target["reading"]["source"])]))
    elif operation == "compare_tree_identity":
        for side in ("left", "right"):
            add("lean", side, {"op": "core_number", "registry_id": canonical(inp["registry_" + side]),
                               "tree": core_tree(inp[side])})
        if "rule_realization" in inp:
            plan["notes"].append("UNMEASURED: the probe does not evaluate an arbitrary Grammar.realize contract.")
    elif operation == "compare_occurrence_identity":
        tree = core_tree(inp["tree"])
        for side in ("left", "right"):
            add("lean", side + "_number", {"op": "core_number", "registry_id": "independent.occurrence.v1", "tree": tree})
            spec = inp[side + "_source"]
            meta = metadata(spec, scalar_span(spec, inp[side + "_byte_span"]), "authored.occurrence")
            add("lean", side, assess_request(annotated(tree, meta), [source(spec)]))
    elif operation == "compare_certificates":
        target = fixtures[inp["fixture"]]["target"]
        request = {"op": "core_number", "registry_id": canonical([target["registry_id"], target["registry_version"]]),
                   "tree": core_tree(target["tree"])}
        add("lean", "left", request)
        add("lean", "right", deepcopy(request))
        plan["notes"].append("UNMEASURED: certificate-record comparison requires the absent carrier and interpretation mapping.")
    elif operation == "enumerate_trees":
        add("lean", "enumeration", {"op": "core_enumerate", "registry_id": "independent.enumeration.v1",
                                      "inventory": {"seeds": [core_seed(s) for s in inp["seeds"]],
                                                    "unary_rules": inp["unary_rules"], "binary_rules": inp["binary_rules"]},
                                      "height": inp["height"], "max_candidates": inp["max_candidates"]})
        plan["notes"].append("Only deduplicated structural enumeration is exposed. Raw duplicate-list length and a certified-filter decision procedure are not measured.")
    elif operation == "rewrite_audit":
        plan["notes"].append("UNMEASURED: this input supplies removed bytes/current output but the new bridge has no inverse/current-output assessment operation. Existing PR14 restoration proofs are not a measurement of this assertion.")
    elif operation in ("lift_role_scope", "assess_role_binding"):
        plan["notes"].append("UNMEASURED: the abstract role premise lacks exact source endpoints, typed nodes and interpreted relation receipts; no such premises are fabricated.")
    else:
        raise ValueError("Unknown authored operation: " + operation)
    return plan


def build_plans(material):
    return [{"case_id": case["case_id"], **build_case_plan(case["operation"], case["input"], material["fixtures"])}
            for case in material["cases"]]


def pair(a, b):
    # Independent closed mathematical specification, not the executable's
    # recursive triangle implementation or an imported runtime function.
    return (a + b) * (a + b + 1) // 2 + b


def seed_number(seed):
    if seed["kind"] == "lexical":
        return 3 * nat(seed["entry"]) + 2
    values = list(map(nat, seed["radicals"]))
    if seed["kind"] == "root3":
        a, b, c = values
        return 3 * pair(a, pair(b, c))
    a, b, c, d = values
    return 3 * pair(a, pair(b, pair(c, d))) + 1


def structural_number(tree):
    if tree["op"] == "leaf":
        return 3 * seed_number(tree["seed"])
    if tree["op"] == "unary":
        return 3 * pair(nat(tree["rule"]), structural_number(tree["child"])) + 1
    return 3 * pair(nat(tree["rule"]), pair(structural_number(tree["left"]), structural_number(tree["right"]))) + 2


def children(node):
    return [] if node["op"] == "leaf" else ([node["child"]] if node["op"] == "unary" else [node["left"], node["right"]])


def preorder(tree):
    return [tree] + [descendant for child in children(tree) for descendant in preorder(child)]


def tree_height(tree):
    return 0 if not children(tree) else 1 + max(map(tree_height, children(tree)))


def erase(node):
    if node["op"] == "leaf":
        return {"op": "leaf", "seed": deepcopy(node["seed"])}
    if node["op"] == "unary":
        return {"op": "unary", "rule": node["rule"], "child": erase(node["child"])}
    return {"op": "binary", "rule": node["rule"], "left": erase(node["left"]), "right": erase(node["right"])}


def decimal(value):
    require(type(value) is str and re.fullmatch(r"0|[1-9][0-9]*", value) is not None,
            "A structural number must be a canonical decimal string")
    return int(value)


def dedup(values):
    seen, result = set(), []
    for value in values:
        key = canonical(value)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def enumeration_universe(inventory, height, limit=4096):
    """An independent finite set of constructor terms, or None beyond the cap.

    The authored E02 oracle separately specifies the thirteen expected terms
    by their one-leaf/three-unary/nine-binary decomposition. This set closure
    prevents a forged COMPLETE flag from passing assertions that do not ask
    for a candidate count. It does not filter by any grammatical predicate.
    """
    seeds = dedup(inventory["seeds"])
    unary, binary = dedup(inventory["unary_rules"]), dedup(inventory["binary_rules"])
    terms = {canonical({"op": "leaf", "seed": seed}): {"op": "leaf", "seed": seed} for seed in seeds}
    if len(terms) > limit:
        return None
    for _ in range(height):
        previous = list(terms.values())
        terms = {canonical({"op": "leaf", "seed": seed}): {"op": "leaf", "seed": seed} for seed in seeds}
        for rule in unary:
            for child in previous:
                tree = {"op": "unary", "rule": rule, "child": child}
                terms[canonical(tree)] = tree
                if len(terms) > limit:
                    return None
        for rule in binary:
            for left in previous:
                for right in previous:
                    tree = {"op": "binary", "rule": rule, "left": left, "right": right}
                    terms[canonical(tree)] = tree
                    if len(terms) > limit:
                        return None
    return terms


def valid_span(src, span):
    return (all(equal(src[key], span[key]) for key in SOURCE_FIELDS)
            and type(span["start"]) is int and type(span["stop"]) is int
            and 0 <= span["start"] < span["stop"] <= len(src["atoms"]))


def host_value(tree, inventory):
    """Reconstruct source contexts; adjacency is checked in original coordinates."""
    op = tree["op"]
    if op == "atom":
        src = tree["source"]
        raw = [tree["value"]]
        valid = any(equal(src, item) for item in inventory) and equal(src["atoms"], tree["before"] + raw + tree["after"])
        return {"source": src, "before": tree["before"], "raw": raw, "after": tree["after"],
                "output": raw, "valid": valid, "class_id": None}
    if op == "join":
        left, right = host_value(tree["left"], inventory), host_value(tree["right"], inventory)
        valid = (left["valid"] and right["valid"] and equal(left["source"], right["source"])
                 and equal(left["before"] + left["raw"], right["before"])
                 and equal(left["after"], right["raw"] + right["after"]))
        return {"source": left["source"], "before": left["before"], "raw": left["raw"] + right["raw"],
                "after": right["after"], "output": left["output"] + right["output"], "valid": valid,
                "class_id": tree["tag"]["class_id"]}
    child = host_value(tree["child"], inventory)
    if op == "substitute":
        child = {**child, "output": tree["replacement"],
                 "valid": child["valid"] and not equal(tree["replacement"], child["output"])}
    elif op == "lift":
        child = {**child, "valid": child["valid"] and not equal(tree["tag"]["class_id"], child["class_id"])}
    else:
        require(op == "wrap", "Unknown host constructor")
    return {**child, "class_id": tree["tag"]["class_id"]}


def morphology_valid(meta):
    morph = meta["morphology"]
    if morph is None:
        return True
    reading, host, src = morph["reading"], meta["host"], meta["source"]
    root, pattern = reading["root"], reading["pattern"]
    if reading["arity"] != len(root) or len(root) not in (3, 4):
        return False
    slots = [token["slot"] for token in pattern if "slot" in token]
    if set(slots) != set(range(len(root))):
        return False
    rendered = [root[token["slot"]] if "slot" in token else token["literal"] for token in pattern]
    expected = [{"pattern_position": index, "source_position": host["start"] + index,
                 "origin": ({"kind": "radical", "index": token["slot"]} if "slot" in token
                            else {"kind": "literal", "value": token["literal"]})}
                for index, token in enumerate(pattern)]
    return (all(type(morph[key]) is str and bool(morph[key]) for key in ("catalog_id", "registry_id", "reading_id"))
            and valid_span(src, host) and equal(rendered, src["atoms"][host["start"]:host["stop"]])
            and equal(expected, morph["alignment"]))


def local_source_valid(node, inventory):
    meta = node["metadata"]
    src, host = meta["source"], meta["host"]
    value = host_value(meta["host_tree"], inventory)
    roles_valid = all(bool(role["role"]) and bool(role["reading_id"]) and valid_span(src, role["target"])
                      and (role["head"] is None or valid_span(src, role["head"]))
                      and ((role["case"] is None) == (role["case_domain"] is None)) for role in meta["roles"])
    valid = (bool(meta["registry_id"]) and bool(meta["reading_id"])
             and any(equal(src, item) for item in inventory) and valid_span(src, host)
             and value["valid"] and equal(value["source"], src)
             and len(value["before"]) == host["start"] and len(value["before"]) + len(value["raw"]) == host["stop"]
             and equal(value["raw"], src["atoms"][host["start"]:host["stop"]]) and roles_valid and morphology_valid(meta))
    if meta["morphology"] is not None:
        root = meta["morphology"]["reading"]["root"]
        roots = [leaf["seed"] for leaf in preorder(erase(node)) if leaf["op"] == "leaf"]
        valid = valid and equal(roots, [{"kind": "root" + str(len(root)), "radicals": list(map(ord, root))}])
    for child in children(node):
        other = child["metadata"]
        valid = valid and equal(meta["registry_id"], other["registry_id"]) and equal(src, other["source"])
        valid = valid and host["start"] <= other["host"]["start"] and other["host"]["stop"] <= host["stop"]
    return bool(valid)


def bridge_oracle(request):
    """Check full identity, source and ledger closure independently of output flags."""
    inventory, interpreted, offered = request["inventory"], request["interpreted"], request["offered"]
    steps = []
    for index, node in enumerate(preorder(request["node"])):
        meta = node["metadata"]
        requirements = [0] + meta["required"]

        def accepted(receipt):
            return (equal(receipt["target"], node) and any(equal(receipt, known) for known in interpreted)
                    and bool(receipt["supports"]) and all(any(equal(support["source"], src) for src in inventory)
                    and valid_span(support["source"], support["span"]) for support in receipt["supports"]))

        positive = [r for r in offered if r["positive"] is True and accepted(r)]
        negative = [r for r in interpreted if r["positive"] is False and accepted(r)]
        missing = [r for r in requirements if not any(equal(p["requirement"], r) for p in positive)]
        value = host_value(meta["host_tree"], inventory)
        steps.append({"preorder_index": index, "registry_id": meta["registry_id"], "reading_id": meta["reading_id"],
                      "host": meta["host"], "source_bound": local_source_valid(node, inventory),
                      "requirements": requirements, "missing_requirements": missing, "positive_complete": not missing,
                      "negative": any(any(equal(n["requirement"], r) for n in negative) for r in requirements),
                      "admitted_positive_witness_ids": [p["witness_id"] for p in positive],
                      "known_negative_witness_ids": [n["witness_id"] for n in negative],
                      "provenance": meta["provenance"], "unresolved": meta["unresolved"],
                      "reconstruction_matches": equal(value["before"] + value["raw"] + value["after"], meta["source"]["atoms"])})
    bound = all(step["source_bound"] for step in steps)
    positive = all(step["positive_complete"] for step in steps)
    negative = any(step["negative"] for step in steps)
    ready = all(step["provenance"] == "native_tree" and not step["unresolved"] for step in steps)
    verdict = ("INVALID_SOURCE_BINDING" if not bound else "REJECTED" if negative else "SOURCE_ONLY" if not ready
               else "CONDITIONALLY_LICENSED" if positive else "UNKNOWN")
    return {"source_bound": bound, "all_premises": positive, "negative": negative, "linguistic_ready": ready,
            "conditional_licensed": verdict == "CONDITIONALLY_LICENSED", "verdict": verdict, "steps": steps}


def validate_lean(request, output):
    require(type(output) is dict, "Probe output is not an object")
    for key, wanted in (("law_id", LAW), ("scope", SCOPE), ("conditional", True),
                        ("acquisition_measured", False), ("grammar_certified", False), ("status", "OK"),
                        ("op", request["op"])):
        exact(output.get(key), wanted, "Incorrect probe envelope: " + key)
    op = request["op"]
    if op == "core_number":
        fields(output, ENVELOPE | {"number_domain", "registry_id", "number", "tree", "estimated_max_number_bits",
                                   "number_bit_budget", "structural_only", "linguistically_licensed", "height", "nodes"})
        for key, wanted in (("number_domain", NUMBER_DOMAIN), ("registry_id", request["registry_id"]),
                            ("tree", request["tree"]), ("structural_only", True), ("linguistically_licensed", False),
                            ("height", tree_height(request["tree"])), ("nodes", len(preorder(request["tree"])))):
            exact(output[key], wanted, "Core field: " + key)
        number = decimal(output["number"])
        exact(number, structural_number(request["tree"]), "Incorrect structural number")
        budget, estimate = nat(output["number_bit_budget"]), nat(output["estimated_max_number_bits"])
        exact(budget, request.get("max_number_bits", 4096), "Number budget echo")
        require(max(1, number.bit_length()) <= estimate <= budget <= 4096, "Invalid number bound")
    elif op == "core_enumerate":
        common = {"enumeration", "search_complete", "linguistic_rejection", "registry_id", "height", "candidates"}
        exact(output["registry_id"], request["registry_id"], "Enumeration registry")
        exact(output["height"], request["height"], "Enumeration height")
        exact(output["linguistic_rejection"], False, "Exhaustion cannot reject a linguistic reading")
        if output["enumeration"] == "EXHAUSTED":
            more = ({"reason", "estimated_max_number_bits", "number_bit_budget"} if "reason" in output
                    else {"candidate_budget", "required_candidates_at_least"})
            fields(output, ENVELOPE | common | more)
            exact(output["search_complete"], False, "Exhausted search marked complete")
            exact(output["candidates"], [], "Exhausted enumeration fabricated candidate results")
            if "reason" in output:
                exact(output["reason"], "number_bit_budget", "Unknown exhaustion reason")
                exact(output["number_bit_budget"], request.get("max_number_bits", 4096), "Number budget echo")
                require(nat(output["estimated_max_number_bits"]) > nat(output["number_bit_budget"]), "False number exhaustion")
            else:
                exact(output["candidate_budget"], request.get("max_candidates", 4096), "Candidate budget echo")
                require(nat(output["required_candidates_at_least"]) > nat(output["candidate_budget"]), "False candidate exhaustion")
                require(enumeration_universe(request["inventory"], request["height"], output["candidate_budget"]) is None,
                        "Claimed candidate exhaustion although the declared finite universe fits")
            return
        exact(output["enumeration"], "COMPLETE", "Unknown enumeration result")
        more = {"structural_only", "number_domain", "candidate_count", "inventory", "removed_duplicate_seeds",
                "removed_duplicate_unary_rules", "removed_duplicate_binary_rules", "estimated_max_number_bits", "number_bit_budget"}
        fields(output, ENVELOPE | common | more)
        exact(output["search_complete"], True, "Complete enumeration flag")
        exact(output["structural_only"], True, "Enumeration scope")
        exact(output["number_domain"], NUMBER_DOMAIN, "Enumeration number domain")
        original = request["inventory"]
        normalized = {key: dedup(value) for key, value in original.items()}
        fields(output["inventory"], {"seeds", "unary_rules", "binary_rules"})
        # Normalization order is not a public grammatical identity; require the
        # same unique members, while candidate tree order remains explicit.
        for key in normalized:
            require(type(output["inventory"][key]) is list, "Inventory list type")
            exact(sorted(map(canonical, output["inventory"][key])), sorted(map(canonical, normalized[key])), "Normalized inventory")
            exact(output["removed_duplicate_" + key], len(original[key]) - len(normalized[key]), "Duplicate count")
        entries = output["candidates"]
        require(type(entries) is list, "Candidates list type")
        exact(output["candidate_count"], len(entries), "Candidate count")
        require(len(entries) <= request.get("max_candidates", 4096), "Candidate budget exceeded")
        seen_trees, seen_numbers = set(), set()
        for entry in entries:
            fields(entry, {"tree", "number"})
            tree, number = entry["tree"], decimal(entry["number"])
            exact(number, structural_number(tree), "Candidate number")
            require(tree_height(tree) <= request["height"], "Candidate height")
            for sub in preorder(tree):
                if sub["op"] == "leaf":
                    require(any(equal(sub["seed"], seed) for seed in normalized["seeds"]), "Foreign candidate seed")
                else:
                    require(sub["op"] in ("unary", "binary"), "Candidate constructor")
                    require(type(sub["rule"]) is int and sub["rule"] in normalized[sub["op"] + "_rules"], "Foreign candidate rule")
            key = canonical(tree)
            require(key not in seen_trees and number not in seen_numbers, "Duplicate structural candidate")
            seen_trees.add(key)
            seen_numbers.add(number)
        universe = enumeration_universe(request["inventory"], request["height"])
        require(universe is not None and seen_trees == set(universe), "Incomplete structural set labeled COMPLETE")
        budget, estimate = nat(output["number_bit_budget"]), nat(output["estimated_max_number_bits"])
        exact(budget, request.get("max_number_bits", 4096), "Enumeration bit budget")
        require(all(max(1, n.bit_length()) <= estimate for n in seen_numbers) and estimate <= budget <= 4096, "Candidate bit bound")
    else:
        require(op == "bridge_assess", "Unknown planned probe operation")
        fields(output, ENVELOPE | {"verdict", "source_bound", "conditional_licensed", "all_premises", "negative", "linguistic_ready",
                                   "atomization_domain", "node", "erased_tree", "nodes", "steps", "semantic_obligation"})
        exact(output["node"], request["node"], "Annotated node was not exactly preserved")
        exact(output["erased_tree"], erase(request["node"]), "Erased ordered tree changed")
        exact(output["nodes"], len(preorder(request["node"])), "Preorder node count")
        exact(output["atomization_domain"], "unicode-scalar-exact.v1", "Atomization domain")
        exact(output["semantic_obligation"], "explicit_PR14_host_Licensed_and_Grammar_Certified_and_RealizationAligned_contracts_required",
              "Semantic obligation disappeared")
        for key, wanted in bridge_oracle(request).items():
            exact(output[key], wanted, "Bridge independently replayed field: " + key)


def validate_source_view(request, view):
    fields(view, {"source_id", "source_sha256", "scope", "raw_text", "byte_length", "atoms", "byte_boundaries",
                  "atomization", "normalization", "lean_source"})
    text = request["text"]
    digest = sha256(text.encode()).hexdigest()
    for key, wanted in (("source_id", request["source_id"]), ("scope", request["scope"]), ("raw_text", text),
                        ("source_sha256", digest), ("byte_length", len(text.encode())), ("atoms", list(text)),
                        ("byte_boundaries", boundaries(text)), ("atomization", "nabt.unicode-scalars.utf8-boundaries.v1"),
                        ("normalization", "NONE")):
        exact(view[key], wanted, "Actual transport source field: " + key)
    exact(view["lean_source"], {"source_id": string_number(request["source_id"]), "revision": int(digest, 16),
                                 "scope_id": string_number(request["scope"]), "atomization_id": 1, "atoms": list(text)},
          "Exact source projection")


def validate_native(request, output):
    if request["op"] == "source_view":
        validate_source_view(request, output)
        return
    if request["op"] == "check_span":
        fields(output, {"status", "span_valid", "span", "error"})
        start, stop = request["byte_span"]
        cuts = boundaries(request["text"])
        valid = type(start) is int and type(stop) is int and start < stop and start in cuts and stop in cuts
        exact(output["span_valid"], valid, "Byte span validity differs from exact scalar boundaries")
        if valid:
            exact(output["status"], "VALID", "Successful span status")
            exact(output["error"], None, "Unexpected valid-span error")
            require(output["span"]["start"] == cuts.index(start) and output["span"]["stop"] == cuts.index(stop), "Span projection")
        else:
            exact(output["status"], "INVALID", "Invalid span status")
            exact(output["span"], None, "Invalid span invented coordinates")
            exact(output["error"], "INVALID_RECURSIVE_SPAN", "An unrelated exception is not evidence of UTF-8 rejection")
        return
    require(request["op"] == "transport_read", "Unknown native request")
    fields(output, {"schema", "scope", "source", "profile", "with_discourse", "upstream_morphology", "morphology_nodes",
                    "upstream_discourse", "syntax_frames", "evidence_records", "evidence_number_domain", "status",
                    "grammar_certified", "acquisition_measured", "lexical_root_from_shape", "world_truth", "identity_authority", "report_id"})
    for key, wanted in (("schema", "nabt.recursive-source-transport.v1"),
                        ("scope", "EXACT_SOURCE_TRANSPORT_WITH_EXPLICIT_GRAMMAR_OBLIGATIONS"), ("profile", "surface_v1"),
                        ("with_discourse", False), ("status", "SOURCE_TRANSPORT_COMPLETE"), ("grammar_certified", False),
                        ("acquisition_measured", False), ("lexical_root_from_shape", False), ("world_truth", "NOT_ESTABLISHED"),
                        ("identity_authority", "FULL_REPLAY_NOT_DIGEST_ALONE"), ("syntax_frames", []),
                        ("upstream_discourse", None), ("evidence_records", []),
                        ("evidence_number_domain", "report_local_upstream_supports.v1")):
        exact(output[key], wanted, "Actual transport envelope: " + key)
    validate_source_view(request, output["source"])
    exact(output["report_id"], sha256(canonical({k: v for k, v in output.items() if k != "report_id"}).encode()).hexdigest(),
          "Transport report hash")
    src = output["source"]["lean_source"]
    upstream = [candidate for occurrence in output["upstream_morphology"]["occurrences"] for candidate in occurrence["candidates"]]
    exact(len(output["morphology_nodes"]), len(upstream), "A reading was lost during transport")
    for node, candidate in zip(output["morphology_nodes"], upstream, strict=True):
        fields(node, {"reading_id", "catalog_id", "registry_id", "root_alphabet", "root", "arity", "template",
                      "alignment", "radical_fibers", "host", "boundary", "source_before", "source_after", "host_tree",
                      "upstream_candidate", "section", "roles", "evidence_ids", "provenance", "child_tree_authority",
                      "source_binding", "linguistic_license", "attested_root", "unresolved", "node_id"})
        exact(node["upstream_candidate"], candidate, "Full upstream candidate not retained")
        for key, wanted in (("section", None), ("roles", []), ("linguistic_license", False), ("attested_root", False),
                            ("provenance", "source_reconstruction"), ("evidence_ids", []),
                            ("child_tree_authority", "NEW_ORDERED_SOURCE_TREE_NOT_RECOVERED_SYNTAX"),
                            ("source_binding", "EXACT_ALL_POSITION_TEMPLATE_REPLAY"),
                            ("unresolved", ["INDEPENDENT_LEXICAL_ROOT_WITNESS", "GRAMMAR_REALIZATION_CONTRACTS"])):
            exact(node[key], wanted, "Unwitnessed transport inference: " + key)
        exact(node["catalog_id"], node["template"]["id"], "Catalog entry identity")
        exact(node["reading_id"], candidate["candidate_id"], "Reading identity")
        require(type(candidate["root"]) is str, "Upstream root must retain its string representation")
        exact(node["root"], list(candidate["root"]), "Root transport")
        exact(node["node_id"], sha256(canonical({k: v for k, v in node.items() if k != "node_id"}).encode()).hexdigest(), "Node hash")
        root, tokens, host = node["root"], node["template"]["tokens"], node["host"]
        exact(node["arity"], len(root), "Transport root arity")
        require(valid_span(src, host), "Transport host is not source bound")
        value = host_value(node["host_tree"], [src])
        require(value["valid"] and equal(value["raw"], src["atoms"][host["start"]:host["stop"]]), "Transport original host adjacency")
        exact(node["source_before"] + value["raw"] + node["source_after"], src["atoms"], "Transport source restoration")
        fibers = [[] for _ in root]
        exact(len(node["alignment"]), len(tokens), "Complete positional alignment")
        for index, (row, token) in enumerate(zip(node["alignment"], tokens, strict=True)):
            fields(row, {"pattern_position", "source_position", "origin", "byte_span", "atom_span"})
            position = host["start"] + index
            expected = root[token] if type(token) is int else token
            exact(src["atoms"][position], expected, "Template refill differs from source")
            exact(row["pattern_position"], index, "Pattern position")
            exact(row["source_position"], position, "Source position")
            origin = {"kind": "radical", "index": token} if type(token) is int else {"kind": "literal", "value": token}
            exact(row["origin"], origin, "Origin position")
            exact(row["byte_span"], candidate["alignment"][index]["span"], "Original byte span changed")
            cuts = boundaries(request["text"])
            raw = request["text"].encode()
            exact(row["byte_span"], {"source_id": request["source_id"], "source_sha256": sha256(raw).hexdigest(),
                                      "start": cuts[position], "end": cuts[position + 1],
                                      "span_sha256": sha256(raw[cuts[position]:cuts[position + 1]]).hexdigest()},
                  "Byte-scalar correspondence and exact original source identity")
            exact(row["atom_span"], {**{k: src[k] for k in SOURCE_FIELDS}, "start": position, "stop": position + 1}, "Scalar span")
            if type(token) is int:
                fibers[token].append(position)
        exact(node["radical_fibers"], fibers, "Repeated/discontinuous radical fibers")


def observations(plan, responses):
    """Read only validated returned evidence; unsupported claims stay absent."""
    results = {item["label"]: result for item, result in zip(plan["requests"], responses, strict=True)}
    op, observed = plan["operation"], {}
    if op == "align_reading":
        if "binding" not in results:
            observed["alignment_valid"] = all(result["span_valid"] for result in results.values())
            # The byte-to-scalar adapter rejects these inputs before any typed
            # assessment exists; it does not itself return a grammar license.
            return observed
        out = results["binding"]
        meta, morph = out["node"]["metadata"], out["node"]["metadata"]["morphology"]
        observed.update(alignment_valid=out["source_bound"], source_binding_valid=out["source_bound"],
                        licensed=out["conditional_licensed"],
                        source_reconstructed_exactly=all(s["reconstruction_matches"] for s in out["steps"]))
        if morph is not None:
            rows = [row for row in morph["alignment"] if row["origin"]["kind"] == "radical"]
            cuts = boundaries("".join(meta["source"]["atoms"]))
            spans = [[cuts[row["source_position"]], cuts[row["source_position"] + 1]] for row in rows]
            observed.update(root_arity=morph["reading"]["arity"], root_byte_spans=spans,
                            root_is_contiguous=all(a[1] == b[0] for a, b in zip(spans, spans[1:])),
                            radical_occurrence_count=len(rows),
                            root_index_1_byte_spans=[span for row, span in zip(rows, spans) if row["origin"]["index"] == 1],
                            root_arity_inflated=morph["reading"]["arity"] != len(plan["reading"]["root"]))
            # The probe diagnoses whole invalid bindings, not a specific
            # omission/overlap error code. Those diagnostic assertions remain
            # UNMEASURED even when the invalid-binding assertion is measured.
        else:
            observed.update(seed_kind=out["erased_tree"]["seed"]["kind"],
                            root_invented=any(leaf["seed"]["kind"] != "lexical" for leaf in preorder(out["erased_tree"])
                                              if leaf["op"] == "leaf"))
        if "transport" in results:
            wanted = plan["reading"].get("template_id")
            nodes = [n for n in results["transport"]["morphology_nodes"] if n["catalog_id"] == wanted
                     and equal(n["root"], plan["reading"]["root"])]
            if nodes:
                observed.update(root_lexically_attested=any(n["attested_root"] for n in nodes),
                                syntactic_role_assigned=any(bool(n["roles"]) for n in nodes),
                                case_assigned=any(r["case"] is not None for n in nodes for r in n["roles"]),
                                noun_category_inferred_from_shape_alone=any(n["section"] == "noun" for n in nodes))
    elif op == "join_source_spans":
        out = results["binding"]
        value = host_value(out["node"]["metadata"]["host_tree"], [out["node"]["metadata"]["source"]])
        observed.update(original_adjacency=value["valid"], join_licensed=out["conditional_licensed"])
    elif op == "compare_readings":
        left, right = results["left"]["node"]["metadata"], results["right"]["node"]["metadata"]
        observed.update(same_surface=equal(left["source"]["atoms"], right["source"]["atoms"]),
                        same_root=equal(left["morphology"]["reading"]["root"], right["morphology"]["reading"]["root"]),
                        same_alignment=equal(left["morphology"]["alignment"], right["morphology"]["alignment"]),
                        same_reading_identity=equal(left, right))
        if "transport" in results:
            wanted = {plan[side + "_reading"]["template_id"] for side in ("left", "right")}
            nodes = [n for n in results["transport"]["morphology_nodes"] if n["catalog_id"] in wanted
                     and equal(n["root"], plan["left_reading"]["root"])]
            observed["retained_alternatives"] = len(nodes)
            observed["unique_analysis"] = len(results["transport"]["morphology_nodes"]) == 1
    elif op == "compare_sources":
        left, right = results["left"], results["right"]
        same = equal(left["lean_source"], right["lean_source"])
        observed.update(same_original_bytes=left["raw_text"].encode() == right["raw_text"].encode(),
                        source_identity_equal=same, normalization_grants_identity=same)
    elif op in ("compare_tree_identity", "compare_certificates"):
        left, right = results["left"], results["right"]
        observed.update(same_structural_tree=equal(left["tree"], right["tree"]),
                        same_structural_number=equal(left["number"], right["number"]),
                        same_qualified_unit_identity=equal([left["number_domain"], left["registry_id"], left["number"]],
                                                          [right["number_domain"], right["registry_id"], right["number"]]),
                        ordered_children_preserved=True)
        if right["tree"]["op"] == "unary":
            observed["child_retained"] = equal(right["tree"]["child"], left["tree"])
    elif op == "compare_occurrence_identity":
        left, right = results["left"]["node"]["metadata"], results["right"]["node"]["metadata"]
        observed.update(same_structural_number=equal(results["left_number"]["number"], results["right_number"]["number"]),
                        same_occurrence=equal([left["source"], left["host"]], [right["source"], right["host"]]))
    elif op == "enumerate_trees":
        out = results["enumeration"]
        observed.update(structural_search_complete=out["search_complete"], search_complete=out["search_complete"],
                        resource_exhausted=out["enumeration"] == "EXHAUSTED", linguistic_rejection=out["linguistic_rejection"])
        if out["enumeration"] == "COMPLETE":
            observed.update(structural_count=out["candidate_count"], distinct_count=len({canonical(e["tree"]) for e in out["candidates"]}),
                            linguistic_license_inferred=out["grammar_certified"],
                            two_distinct_analyses_inferred=out["candidate_count"] >= 2)
    return observed


def score_assertions(expected, observed):
    return [{"assertion": name, "expected": wanted,
             "status": "UNMEASURED" if name not in observed else "PASS" if equal(observed[name], wanted) else "FAIL",
             **({"actual": observed[name]} if name in observed else
                {"reason": "No representable assertion with the exact frozen input and declared runtime operation; see plan notes."})}
            for name, wanted in expected.items()]


def score_measurement(material, plans, response_groups):
    exact(len(plans), len(material["cases"]), "Plan count")
    exact(len(response_groups), len(plans), "Response group count")
    cases = []
    for case, plan, responses in zip(material["cases"], plans, response_groups, strict=True):
        exact(plan["case_id"], case["case_id"], "Plan case ID")
        integrity = []
        exact(len(responses), len(plan["requests"]), "Responses per case")
        for item, output in zip(plan["requests"], responses, strict=True):
            try:
                (validate_lean if item["backend"] == "lean" else validate_native)(item["request"], output)
            except (KeyError, IndexError, TypeError, ValueError, OverflowError) as error:
                integrity.append({"request": item["label"], "error": type(error).__name__ + ": " + str(error)})
        observed = {} if integrity else observations(plan, responses)
        assertions = score_assertions(case["expected"], observed)
        if integrity:
            status = "FAIL"
        elif any(a["status"] == "FAIL" for a in assertions):
            status = "FAIL"
        elif all(a["status"] == "UNMEASURED" for a in assertions):
            status = "UNMEASURED"
        elif any(a["status"] == "UNMEASURED" for a in assertions):
            status = "PARTIALLY_MEASURED"
        else:
            status = "PASS"
        cases.append({"case_id": case["case_id"], "group": case["group"], "status": status,
                      "assertions": assertions, "response_integrity_errors": integrity,
                      "request_count": len(plan["requests"]), "notes": plan["notes"]})
    counts = {status: sum(a["status"] == status for c in cases for a in c["assertions"])
              for status in ("PASS", "FAIL", "UNMEASURED")}
    integrity_errors = sum(len(c["response_integrity_errors"]) for c in cases)
    gate = counts["PASS"] > 0 and counts["FAIL"] == 0 and integrity_errors == 0
    return {"cases": cases, "summary": {"case_count": len(cases), "assertions": counts,
            "cases_by_status": {s: sum(c["status"] == s for c in cases) for s in ("PASS", "PARTIALLY_MEASURED", "UNMEASURED", "FAIL")},
            "response_integrity_errors": integrity_errors, "measured_contract_gate": gate,
            "strict_complete_pass": gate and counts["UNMEASURED"] == 0,
            "acquisition_measured": False, "held_out_arabic_discovery_measured": False}}


def worker(request):
    # Production imports are deliberately isolated from the planner/scorer.
    # Keep this new adapter outside the exact historical src/nabt inventory.
    # Loading its explicit path also works under Python's isolated (-I) mode.
    spec = importlib.util.spec_from_file_location("nabt_recursive_source_transport", ROOT / "tools/recursive_bridge.py")
    require(spec is not None and spec.loader is not None, "Standalone recursive source adapter is unavailable")
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    from nabt.errors import NabtError
    options = {key: request[key] for key in ("source_id", "scope")}
    if request["op"] == "transport_read":
        return bridge.read_recursive_source(request["text"], **options)
    view = bridge.source_view(request["text"], **options)
    if request["op"] == "source_view":
        return view
    require(request["op"] == "check_span", "Unknown native worker operation")
    start, stop = request["byte_span"]
    raw = request["text"].encode()
    byte_span = {"source_id": view["source_id"], "source_sha256": view["source_sha256"],
                 "start": start, "end": stop, "span_sha256": sha256(raw[start:stop]).hexdigest()}
    try:
        span = bridge._atom_span(view, byte_span)
        return {"status": "VALID", "span_valid": True, "span": span, "error": None}
    except NabtError as error:
        return {"status": "INVALID", "span_valid": False, "span": None, "error": error.code}


def source_paths():
    paths = [Path(__file__), ROOT / "tools/recursive_bridge.py", ROOT / "tests/test_recursive_bridge_checker.py", ROOT / "formal/RecursiveBridgeProbe.lean",
             ROOT / "formal/ProbeJson.lean", ROOT / "formal/lakefile.lean", ROOT / "formal/lean-toolchain",
             ROOT / "evidence/recursive_algebra/independent_v1/IMPLEMENTER_EXPOSURE.json"]
    paths += sorted((ROOT / "formal/Nabt").glob("*.lean"))
    paths += sorted((ROOT / "formal").glob("*.lean"))
    paths += sorted((ROOT / "src/nabt").rglob("*.py"))
    paths += sorted((ROOT / "src/nabt/data").rglob("*.json"))
    paths += sorted((ROOT / "evidence/recursive_algebra/independent_v1").glob("*"))
    return sorted(set(path for path in paths if path.is_file()))


def save_sources(path, paths):
    with tarfile.open(path, "x:gz") as archive:
        for file in paths:
            archive.add(file, arcname=file.relative_to(ROOT).as_posix(), recursive=False)


def run_backend(command, requests, prefix):
    raw_in = "".join(canonical(request) + "\n" for request in requests).encode()
    input_path, output_path, error_path = (Path(str(prefix) + suffix) for suffix in (".stdin.jsonl", ".stdout.jsonl", ".stderr.log"))
    with input_path.open("xb") as stream:
        stream.write(raw_in)
    result = subprocess.run(command, input=raw_in, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=ROOT, timeout=60, check=False)
    with output_path.open("xb") as stream:
        stream.write(result.stdout)
    with error_path.open("xb") as stream:
        stream.write(result.stderr)
    require(result.returncode == 0, "Backend failed; exact stdout/stderr preserved: " + str(prefix))
    lines = result.stdout.splitlines()
    exact(len(lines), len(requests), "Backend JSONL line count")
    outputs = [parse(line) for line in lines]
    return outputs, {"command": command, "exit_code": result.returncode,
                     "stdin": file_ref(input_path), "stdout": file_ref(output_path), "stderr": file_ref(error_path)}


def execute(plans, probe, output):
    flat = [(case_index, request_index, item) for case_index, plan in enumerate(plans)
            for request_index, item in enumerate(plan["requests"])]
    groups = [[None for _ in plan["requests"]] for plan in plans]
    backends = {}
    for backend, command in (("lean", [str(probe)]), ("native", [sys.executable, str(Path(__file__).resolve()), "--worker"])):
        chosen = [entry for entry in flat if entry[2]["backend"] == backend]
        if not chosen:
            continue
        results, record = run_backend(command, [entry[2]["request"] for entry in chosen], str(output) + "." + backend)
        for (case_index, request_index, _), result in zip(chosen, results, strict=True):
            groups[case_index][request_index] = result
        record["positions"] = [[i, j] for i, j, _ in chosen]
        backends[backend] = record
    return groups, backends


def replay(saved, output):
    material = load_material()
    record = parse(Path(saved).read_bytes())
    exact(record["schema"], SCHEMA, "Saved schema")
    exact(record["material"]["sha256"], MATERIAL_SHA, "Saved material hash")
    archive_path = resolve_ref(record["source_archive"])
    with tarfile.open(archive_path, "r:gz") as code:
        for reference in record["source_files_before"]:
            relative = Path(reference["repository_path"])
            require(not relative.is_absolute() and ".." not in relative.parts, "Unsafe archived source path")
            member = code.extractfile(reference["repository_path"])
            require(member is not None, "Archived source file missing")
            raw = member.read()
            exact(sha256(raw).hexdigest(), reference["sha256"], "Archived source digest")
            exact(len(raw), reference["bytes"], "Archived source size")
    exact(record["source_files_before"], record["source_files_after"], "Sources changed during saved run")
    exact(record["probe_before"], record["probe_after"], "Probe changed during saved run")
    exact(record["sources_stable_during_run"], True, "Unstable run cannot be replayed as a stable result")
    plans = build_plans(material)
    exact(record["plans"], plans, "Saved requests differ from input-only planning")
    groups = [[None for _ in plan["requests"]] for plan in plans]
    for backend, run in record["backends"].items():
        expected_positions = [[i, j] for i, plan in enumerate(plans) for j, item in enumerate(plan["requests"])
                              if item["backend"] == backend]
        exact(run["positions"], expected_positions, "Replay backend position mapping")
        resolved = {key: resolve_ref(run[key]) for key in ("stdin", "stdout", "stderr")}
        request_lines = resolved["stdin"].read_bytes().splitlines()
        response_lines = resolved["stdout"].read_bytes().splitlines()
        exact(len(request_lines), len(expected_positions), "Replay request count")
        exact(len(response_lines), len(expected_positions), "Replay response count")
        for position, raw_request, raw_response in zip(expected_positions, request_lines, response_lines, strict=True):
            i, j = position
            exact(parse(raw_request), plans[i]["requests"][j]["request"], "Replay request differs from plan")
            groups[i][j] = parse(raw_response)
    require(all(all(value is not None for value in group) for group in groups), "Replay missing backend output")
    measurement = score_measurement(material, plans, groups)
    exact(measurement, record["measurement"], "Saved scores differ from independent raw-output replay")
    result = {"schema": SCHEMA + ".replay", "source": file_ref(saved), "material_sha256": MATERIAL_SHA,
              "probe_executed": False, "raw_artifacts_verified": True, "scores_reproduced": True,
              "summary": measurement["summary"]}
    write_json(output, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--probe", type=Path, default=ROOT / "formal/.lake/build/bin/recursiveBridgeProbe")
    parser.add_argument("--no-build", action="store_true", help="Use an already-built, hash-recorded probe without invoking Lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        for line in sys.stdin:
            print(canonical(worker(parse(line))), flush=True)
        return 0
    require(args.output is not None, "--output is required")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), "Measurement output already exists; preserve previous runs")
    if args.replay:
        result = replay(args.replay, output)
        print(canonical(result["summary"]))
        return 0 if result["summary"]["measured_contract_gate"] else 1
    material = load_material()
    # Never invoke the full project build from this checker. --no-build is for
    # an explicitly coordinated, already-built binary; its hash is recorded.
    if not args.no_build:
        subprocess.run([args.lake, "build", "recursiveBridgeProbe"], cwd=ROOT / "formal", check=True, timeout=60)
    require(args.probe.is_file(), "Requested probe binary is unavailable")
    paths = source_paths()
    before = [file_ref(path) for path in paths]
    binary_before = file_ref(args.probe)
    plans = build_plans(material)
    archive = Path(str(output) + ".code.tar.gz")
    save_sources(archive, paths)
    # Preserve the fixed requests even when execution fails before scoring.
    write_json(str(output) + ".plan.json", {"material_sha256": MATERIAL_SHA, "plans": plans})
    groups, backends = execute(plans, args.probe.resolve(), output)
    measurement = score_measurement(material, plans, groups)
    after = [file_ref(path) for path in paths]
    binary_after = file_ref(args.probe)
    stable = equal(before, after) and equal(binary_before, binary_after)
    if not stable:
        measurement["summary"]["measured_contract_gate"] = False
        measurement["summary"]["strict_complete_pass"] = False
    result = {"schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
              "material": file_ref(MATERIAL), "source_files_before": before, "source_files_after": after,
              "probe_before": binary_before, "probe_after": binary_after, "sources_stable_during_run": stable,
              "source_archive": file_ref(archive), "plans": plans, "backends": backends, "measurement": measurement,
              "disclosure": "Independent authorship; implementer saw the first 100 material lines (one alignment fixture), not gold assertions. This is authored contract coverage, not blind Arabic discovery. Frozen opaque-seed and unavailable grammar assertions remain UNMEASURED."}
    write_json(output, result)
    print(canonical(measurement["summary"]))
    return 0 if measurement["summary"]["measured_contract_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

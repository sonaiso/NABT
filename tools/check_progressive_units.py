#!/usr/bin/env python3
"""Measure frozen authored contracts through the progressive Lean JSONL probe.

The planner accepts only (operation, input). Expected answers are consulted
only after the request bytes are fixed. Explicit synthetic positive fixtures
remain conditional premises. Unrepresented rank and necessity contracts are
UNMEASURED; an echoed caller status or completeness flag grants no authority.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "evidence/progressive_units/independent_cases_v1.json"
MATERIAL_SHA = "246a6abb17ea439bf896e1409f97cb2519b7f3762b0e9aac77fb3efbb31896ee"
SOUND_TABLE = ROOT / "src/nabt/data/law.json"
SOUND_TABLE_SHA = "14e32ae208ac5ed2f754e83506e72133d0962756ef0c944d12370746febddcdd"
LAW = "nabt.licensed-derivation.v1"
SCOPE = "conditional_on_supplied_interpretations"
SCHEMA = "nabt.progressive-units.measurement.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def equal(left, right):
    """JSON numbers and booleans are different values, including nested ones."""
    return canonical(left) == canonical(right)


def nat(value):
    require(type(value) is int and value >= 0, "Expected a natural number, not a Boolean")
    return value


def text_atoms(value):
    require(type(value) is list and all(type(a) is str and a for a in value),
            "Expected declared nonempty string atoms")
    return value


def file_ref(path):
    digest = sha256()
    size = 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    result = {"path": str(path.resolve()), "bytes": size, "sha256": digest.hexdigest()}
    if path.resolve().is_relative_to(ROOT):
        result["repository_path"] = path.resolve().relative_to(ROOT).as_posix()
    return result


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def load_material():
    require(sha256(MATERIAL.read_bytes()).hexdigest() == MATERIAL_SHA, "Frozen independent material changed")
    data = parse(MATERIAL.read_bytes())
    require(data["schema"] == "nabt.progressive-units.independent-cases.v1", "Material schema")
    require(data["case_count"] == 34 and len(data["cases"]) == 34, "Material count")
    require(len({case["id"] for case in data["cases"]}) == 34, "Duplicate case IDs")
    return data


@lru_cache(maxsize=1)
def load_sound_table():
    """The unchanged pre-existing Lean-exported law is a separate oracle."""
    raw = SOUND_TABLE.read_bytes()
    require(sha256(raw).hexdigest() == SOUND_TABLE_SHA, "Pinned sound-law table changed")
    table = parse(raw)
    require(table["alphabet_id"] == "nabt.a116.v1" and table["law_id"] == "nabt-sound-shape-v1",
            "Sound-table identities")
    require(equal(table["alphabet_size"], 116) and equal(table["state_count"], 97) and
            equal(table["dead_state"], 96), "Sound-table domains")
    return table


def expected_cell_effect(request):
    """Replay every entry through the pinned table, including path cost."""
    table = load_sound_table()
    require(request["mode"] in ("waqf", "wasl"), "Sound-law mode")
    entry = nat(request["entry"])
    require(entry < 97, "Sound-law entry domain")
    cells = request["cells"]
    require(type(cells) is list and cells and all(type(a) is int and 0 <= a < 116 for a in cells),
            "Atomic-cell input domain")
    effect = []
    for initial in range(97):
        state, weight = initial, 0
        for atom in cells:
            state, delta = table["transitions"][state][atom]
            weight += delta
        effect.append({"entry": initial, "exit": state, "weight": weight})
    number = 0
    for atom in cells:
        number = 116 * number + atom + 1
    selected = effect[entry]
    return {"unit_n": number, "effect": effect, "exit": selected["exit"],
            "weight": selected["weight"],
            "sound_shape_accepted": table["final_" + request["mode"]][selected["exit"]]}


def metadata(inp, class_id=None):
    return {"rule_id": nat(inp["rule"]), "reading_id": nat(inp["reading"]),
            "class_id": nat(inp["class"] if class_id is None else class_id), "requirements": []}


def atom_at(source, position, value=None):
    """Preserve a supplied atom even when it contradicts the source location."""
    position = nat(position)
    atoms = text_atoms(source["atoms"])
    if value is None:
        require(position < len(atoms), "A source span must name an existing atom")
        value = atoms[position]
    text_atoms([value])
    return {"op": "atom", "source": deepcopy(source), "before": atoms[:position],
            "value": value, "after": atoms[position + 1:]}


def join_trees(trees, tag):
    """Balanced input-only representation; no expected rank is consumed."""
    require(bool(trees), "No empty source occurrence is manufactured")
    if len(trees) == 1:
        return deepcopy(trees[0])
    midpoint = len(trees) // 2
    return {"op": "join", "tag": deepcopy(tag),
            "left": join_trees(trees[:midpoint], tag),
            "right": join_trees(trees[midpoint:], tag)}


def span_tree(source, interval, tag, supplied=None):
    require(type(interval) is list and len(interval) == 2, "A span has two endpoints")
    start, stop = map(nat, interval)
    require(start < stop, "No empty source occurrence is manufactured")
    if supplied is None:
        trees = [atom_at(source, index) for index in range(start, stop)]
    else:
        require(len(supplied) == stop - start, "Removed-material length disagrees with span")
        trees = [atom_at(source, start + index, value) for index, value in enumerate(supplied)]
    return join_trees(trees, tag)


def specification_tree(spec, source, tag):
    if type(spec) is list and len(spec) == 2 and all(type(x) is int for x in spec):
        return span_tree(source, spec, tag)
    require(type(spec) is list and bool(spec), "Tree specification")
    if spec[0] == "join" and len(spec) == 3:
        return {"op": "join", "tag": deepcopy(tag),
                "left": specification_tree(spec[1], source, tag),
                "right": specification_tree(spec[2], source, tag)}
    if spec[0] == "lift" and len(spec) == 2:
        # A fresh opaque intermediate tag implements the supplied lift. It
        # carries no discovered linguistic class semantics or expected answer.
        child_tag = {**tag, "class_id": tag["class_id"] + 1}
        return {"op": "lift", "tag": deepcopy(tag),
                "child": specification_tree(spec[1], source, child_tag)}
    raise ValueError("Unsupported tree specification")


def nodes(tree):
    if tree["op"] == "atom":
        return []
    if tree["op"] == "join":
        return [tree] + nodes(tree["left"]) + nodes(tree["right"])
    return [tree] + nodes(tree["child"])


def sources(tree):
    if tree["op"] == "atom":
        return [tree["source"]]
    if tree["op"] == "join":
        values = sources(tree["left"]) + sources(tree["right"])
    else:
        values = sources(tree["child"])
    result = []
    for value in values:
        if not any(equal(value, previous) for previous in result):
            result.append(deepcopy(value))
    return result


def make_receipt(tree, witness_id, source, *, positive=True):
    extent = {key: source[key] for key in ("source_id", "revision", "scope_id", "atomization_id")}
    extent.update(start=0, stop=len(source["atoms"]))
    return {"target": deepcopy(tree), "requirement": 0, "positive": positive,
            "witness_id": witness_id,
            "supports": [{"source": deepcopy(source), "span": extent}]}


def derive_request(tree, source, evidence):
    inventory = sources(tree)
    if not any(equal(source, value) for value in inventory):
        inventory.append(deepcopy(source))
    receipts = []
    if evidence in ("exact_positive", "all_exact_positive", "exact_positive_and_exact_negative"):
        receipts = [make_receipt(node, index + 1, source) for index, node in enumerate(nodes(tree))]
    if evidence == "positive_for_wrap_only":
        foreign = {"op": "wrap", "tag": deepcopy(tree["tag"]), "child": deepcopy(tree)}
        receipts = [make_receipt(foreign, 1, source)]
    if evidence == "exact_positive_and_exact_negative":
        receipts.append(make_receipt(tree, len(receipts) + 1, source, positive=False))
    require(evidence in ("none", "exact_positive", "all_exact_positive",
                         "positive_for_wrap_only", "exact_positive_and_exact_negative"),
            "Evidence fixture is not a recognized explicit input")
    return {"op": "derive", "tree": deepcopy(tree), "inventory": inventory,
            "interpreted": deepcopy(receipts), "offered": deepcopy(receipts)}


def build_requests(operation, inp):
    """Input-only planner. In particular this function never sees `expected`."""
    plan = {"requests": [], "notes": [], "unmeasured_reason": None}

    def add(label, request):
        plan["requests"].append({"label": label, "request": request})

    if operation == "alphabet":
        require(inp["alphabet"] == "nabt.a116.v1" and nat(inp["carriers"]) == 29 and
                inp["states"] == ["fatha", "damma", "kasra", "sukun"], "Unsupported alphabet input")
        add("alphabet", {"op": "alphabet"})
    elif operation == "ordered_quota":
        require(inp["onset_filter"] is False, "No undeclared onset policy")
        add("quota", {"op": "quota", "consonants": nat(inp["c"]),
                      "vowels": nat(inp["v"]), "max_atoms": nat(inp["max_atoms"])})
    elif operation == "concatenate":
        add("composition", {"op": "compose_shapes", "parts": [inp["left"], inp["right"]]})
        add("comparison", {"op": "shape", "shape": inp["comparison"]})
    elif operation == "sound_law":
        require(inp["alphabet"] == "nabt.a116.v1" and inp["law"] == "nabt-sound-shape-v1",
                "Unsupported sound-law identity")
        for mode in ("waqf", "wasl"):
            add(mode, {"op": "cell_effect", "cells": deepcopy(inp["atoms"]),
                       "entry": nat(inp["start_state"]), "mode": mode})
    elif operation == "lift":
        plan["unmeasured_reason"] = (
            "The case supplies child_rank/output_rank as asserted layer numbers. The probe computes "
            "derivation height and does not validate these declarations; ignoring them would change the case.")
    elif operation == "necessity":
        plan["unmeasured_reason"] = (
            "Supplied admitted/refuted strings and search_complete are not interpreted witnesses or a "
            "CompleteWithin proof. The binary-join forest domain does not cover this join/wrap domain.")
    elif operation == "occurrence_identity":
        trees = [span_tree(inp[key]["source"], inp[key]["extent"], metadata(inp[key]))
                 for key in ("left", "right")]
        add("comparison", {"op": "compare", "left": trees[0], "right": trees[1]})
        plan["notes"].append("Compare measures proposal identity only; it grants no occurrence license.")
    else:
        source = deepcopy(inp["source"])
        tag = metadata(inp)
        plan["notes"].append("Exact-positive fixtures are declared conditional interpretations of their input trees, not acquired evidence.")
        if operation == "atom":
            tree = atom_at(source, inp["position"], inp["atom"])
        elif operation == "join":
            require(len(inp["children"]) == 2, "Binary join input")
            right_source = deepcopy(source)
            if "right_revision" in inp:
                right_source["revision"] = nat(inp["right_revision"])
            tree = {"op": "join", "tag": tag,
                    "left": span_tree(source, inp["children"][0], tag),
                    "right": span_tree(right_source, inp["children"][1], tag)}
        elif operation == "wrap":
            pieces = [span_tree(source, inp[key], tag) for key in ("left", "middle", "right")]
            tree = {"op": "wrap", "tag": tag, "child": join_trees(pieces, tag)}
            plan["notes"].append("Enclosure translates the three supplied ordered spans into joins plus an output-preserving wrapper.")
        elif operation == "substitute":
            extent_start, extent_stop = map(nat, inp["extent"])
            start = nat(inp["start"])
            removed, inserted = text_atoms(inp["removed"]), text_atoms(inp["inserted"])
            require(bool(removed), "An empty removed span is not represented by this adapter")
            stop = start + len(removed)
            require(extent_start <= start < stop <= extent_stop, "Local edit coordinates")
            child = span_tree(source, [start, stop], tag, supplied=removed)
            local = {"op": "substitute", "tag": tag, "replacement": deepcopy(inserted), "child": child}
            pieces = []
            if extent_start < start:
                pieces.append(span_tree(source, [extent_start, start], tag))
            pieces.append(local)
            if stop < extent_stop:
                pieces.append(span_tree(source, [stop, extent_stop], tag))
            tree = join_trees(pieces, tag)
            plan["notes"].append("Local edit preserves the supplied removed atoms, even when false, and joins original prefix/suffix occurrences.")
        elif operation == "alternative_trees":
            trees = [specification_tree(spec, source, tag) for spec in inp["trees"]]
            require(len(trees) == 2, "Pair of alternatives")
            for index, tree in enumerate(trees):
                add("alternative_" + str(index), derive_request(tree, source, inp["evidence"]))
            add("comparison", {"op": "compare", "left": trees[0], "right": trees[1]})
            return plan
        elif operation == "withdraw_premise":
            tree = specification_tree(inp["tree"], source, tag)
            before = derive_request(tree, source, "all_exact_positive")
            after = deepcopy(before)
            extent = inp["remove_support_for"]
            def remains(receipt):
                view = tree_view(receipt["target"], before["inventory"])
                return [len(view["before"]), len(view["before"]) + len(view["raw"])] != extent
            after["offered"] = [r for r in after["offered"] if remains(r)]
            after["interpreted"] = [r for r in after["interpreted"] if remains(r)]
            require(len(after["offered"]) < len(before["offered"]), "No premise matched withdrawal")
            add("before", before)
            add("after", after)
            plan["notes"].append("Lift's immediate child receives opaque class input.class+1; outer class stays input.class. These are fixture identifiers, not learned linguistic classes.")
            plan["notes"].append("Withdrawal removes only exact receipts targeting the supplied child extent; the entire parent tree and parent receipts remain unchanged.")
            return plan
        else:
            plan["unmeasured_reason"] = "Unsupported operation: " + operation
            return plan
        add("derivation", derive_request(tree, source, inp["evidence"]))
    return plan


def build_plan(material):
    """Gold/rationales are deliberately not passed to the request planner."""
    result = {"cases": [], "requests": []}
    for case in material["cases"]:
        plan = build_requests(case["operation"], deepcopy(case["input"]))
        entry = {"case_id": case["id"], "operation": case["operation"],
                 "notes": plan["notes"], "unmeasured_reason": plan["unmeasured_reason"], "requests": []}
        for item in plan["requests"]:
            request_id = case["id"] + ":" + item["label"]
            row = {"request_id": request_id, "case_id": case["id"], **item,
                   "sha256": sha256((canonical(item["request"]) + "\n").encode()).hexdigest()}
            result["requests"].append(row)
            entry["requests"].append(request_id)
        result["cases"].append(entry)
    return result


def tree_view(tree, inventory):
    """Independent mechanical consistency oracle; never uses expected answers."""
    op = tree["op"]
    if op == "atom":
        raw = [tree["value"]]
        before, after, source = tree["before"], tree["after"], tree["source"]
        entry = any(equal(source, s) for s in inventory) and equal(source["atoms"], before + raw + after)
        return {"source": source, "before": before, "raw": raw, "after": after,
                "output": raw, "rank": 0, "class_id": None, "entry": entry,
                "structural": entry, "nodes": 1, "steps": []}
    if op == "join":
        left, right = tree_view(tree["left"], inventory), tree_view(tree["right"], inventory)
        entry = (equal(left["source"], right["source"]) and
                 equal(right["before"], left["before"] + left["raw"]) and
                 equal(left["after"], right["raw"] + right["after"]))
        result = {"source": left["source"], "before": left["before"],
                  "raw": left["raw"] + right["raw"], "after": right["after"],
                  "output": left["output"] + right["output"],
                  "rank": max(left["rank"], right["rank"]) + 1,
                  "class_id": tree["tag"]["class_id"], "entry": entry,
                  "structural": entry and left["structural"] and right["structural"],
                  "nodes": 1 + left["nodes"] + right["nodes"]}
        result["steps"] = [tree] + left["steps"] + right["steps"]
        return result
    child = tree_view(tree["child"], inventory)
    entry = (op == "wrap" or
             (op == "substitute" and not equal(tree["replacement"], child["output"])) or
             (op == "lift" and not equal(tree["tag"]["class_id"], child["class_id"])))
    return {**child, "output": tree["replacement"] if op == "substitute" else child["output"],
            "rank": child["rank"] + 1, "class_id": tree["tag"]["class_id"],
            "entry": entry, "structural": entry and child["structural"],
            "nodes": child["nodes"] + 1, "steps": [tree] + child["steps"]}


def valid_receipt(request, target, receipt):
    if not equal(receipt["target"], target) or not any(equal(receipt, r) for r in request["interpreted"]):
        return False
    if not receipt["supports"]:
        return False
    for support in receipt["supports"]:
        source, span = support["source"], support["span"]
        if not any(equal(source, known) for known in request["inventory"]):
            return False
        if any(not equal(source[k], span[k]) for k in ("source_id", "revision", "scope_id", "atomization_id")):
            return False
        if not (type(span["start"]) is int and type(span["stop"]) is int and
                0 <= span["start"] < span["stop"] <= len(source["atoms"])):
            return False
    return True


def step_view(request, target):
    admitted = [r for r in request["offered"] if valid_receipt(request, target, r)]
    required = [0] + target["tag"]["requirements"]
    negatives = [r for r in request["interpreted"] if r["positive"] is False and
                 r["requirement"] in required and valid_receipt(request, target, r)]
    positive_requirements = {r["requirement"] for r in admitted if r["positive"] is True}
    negative_requirements = {r["requirement"] for r in negatives}
    base = tree_view(target, request["inventory"])
    return {"target": target, "rank": base["rank"], "raw": base["raw"], "output": base["output"],
            "displaced_output": (tree_view(target["child"], request["inventory"])["output"]
                                 if target["op"] == "substitute" else None),
            "extent": [len(base["before"]), len(base["before"]) + len(base["raw"])],
            "requirements": required, "entry_valid": base["entry"],
            "positive_complete": all(r in positive_requirements for r in required),
            "negative": bool(negative_requirements),
            "conflict": any(r in positive_requirements and r in negative_requirements for r in required),
            "offered_admitted_ids": [r["witness_id"] for r in admitted],
            "known_negative_ids": [r["witness_id"] for r in negatives]}


def check_present(response, expected, context):
    for field, value in expected.items():
        if field in response:
            require(equal(response[field], value), context + ": inconsistent field " + field)


def validate_response(request, response):
    require(type(response) is dict, "Probe response must be an object")
    for key, expected in (("law_id", LAW), ("scope", SCOPE), ("conditional", True),
                          ("acquisition_measured", False)):
        require(key in response and equal(response[key], expected), "Probe scope field: " + key)
    require(response.get("status") in ("OK", "ERROR"), "Probe envelope status")
    if response["status"] == "ERROR":
        require(response.get("error") in ("INVALID_INPUT", "RESOURCE_LIMIT"), "Probe error status")
        return
    require(response.get("op") == request["op"], "Response operation binding")
    op = request["op"]
    if op == "derive":
        view = tree_view(request["tree"], request["inventory"])
        steps = [step_view(request, step) for step in view["steps"]]
        conflict = any(step["conflict"] for step in steps) if view["structural"] else False
        verdict = ("INVALID_DERIVATION" if not view["structural"] else
                   "REJECTED" if any(step["negative"] for step in steps) else
                   "LICENSED" if all(step["positive_complete"] for step in steps) else "UNKNOWN")
        reconstructed = view["before"] + view["raw"] + view["after"]
        seen = request.get("seen", view["output"])
        undo = view["raw"] if equal(seen, view["output"]) else None
        check_present(response, {"verdict": verdict, "licensed": verdict == "LICENSED", "conflict": conflict,
                      "structural": view["structural"], "source": view["source"],
                      "rank": view["rank"], "rank_domain": "derivation_height", "tree_nodes": view["nodes"],
                      "extent": [len(view["before"]), len(view["before"]) + len(view["raw"])],
                      "raw": view["raw"], "output": view["output"], "before": view["before"],
                      "after": view["after"], "reconstruction": reconstructed,
                      "reconstruction_matches": equal(reconstructed, view["source"]["atoms"]),
                      "seen": seen, "undo_raw": undo,
                      "undo_source": None if undo is None else view["before"] + undo + view["after"],
                      "class_id": view["class_id"],
                      "necessity": "NOT_ESTABLISHED_BY_A_SINGLE_DERIVATION"}, "Derivation")
        if "premise_steps" in response:
            require(type(response["premise_steps"]) is list and len(response["premise_steps"]) == len(steps),
                    "Premise trace length")
            for actual, expected in zip(response["premise_steps"], steps):
                require(type(actual) is dict, "Premise trace item")
                check_present(actual, expected, "Premise trace")
    elif op == "quota":
        if response.get("enumeration") == "COMPLETE":
            shapes = response.get("shapes")
            if shapes is not None:
                require(type(shapes) is list and all(type(s) is str and set(s) <= {"C", "V"} for s in shapes),
                        "Invalid quota shapes")
                check_present(response, {"count": len(shapes), "search_complete": True,
                              "consonants": request["consonants"], "vowels": request["vowels"],
                              "linguistic_license_inferred": False}, "Quota")
                if "shape_numbers" in response:
                    numbers = response["shape_numbers"]
                    require(type(numbers) is list and len(numbers) == len(shapes) and
                            all(type(n) is int and n >= 0 for n in numbers), "Typed shape number list")
                    require(len(set(numbers)) == len(set(shapes)), "Shape number collision or inconsistent equality")
        elif response.get("enumeration") == "EXHAUSTED":
            check_present(response, {"search_complete": False, "linguistic_rejection": False,
                          "required_atoms": request["consonants"] + request["vowels"]}, "Quota exhaustion")
        else:
            require("enumeration" not in response, "Unknown quota enumeration status")
    elif op in ("shape", "compose_shapes"):
        shape = request["shape"] if op == "shape" else "".join(request["parts"])
        check_present(response, {"shape": shape, "consonants": shape.count("C"),
                      "vowels": shape.count("V"), "linguistic_license_inferred": False}, "Shape")
        if "shape_n" in response:
            nat(response["shape_n"])
        if "partitions" in response:
            parts = response["partitions"]
            require(type(parts) is list, "Partitions must be a list")
            for row in parts:
                require(type(row) is list and all(type(p) is str and p for p in row) and "".join(row) == shape,
                        "Partition does not restore supplied shape")
            check_present(response, {"partition_count": len(parts)}, "Partitions")
    elif op == "compare":
        left, right = (tree_view(request[k], sources(request[k])) for k in ("left", "right"))
        same_occurrence = equal(left["source"], right["source"]) and len(left["before"]) == len(right["before"]) and equal(left["raw"], right["raw"])
        same_output = equal(left["output"], right["output"])
        check_present(response, {"comparison_scope": "proposal_identity_only", "licensed_comparison": False,
                      "same_derivation": equal(request["left"], request["right"]),
                      "same_output": same_output, "same_occurrence": same_occurrence,
                      "same_unit_key": same_occurrence and same_output and equal(left["class_id"], right["class_id"]),
                      "left_rank": left["rank"], "right_rank": right["rank"]}, "Comparison")
    elif op == "cell_effect":
        check_present(response, {"cells": request["cells"], "entry": request["entry"], "mode": request["mode"],
                      "alphabet_id": "nabt.a116-sequence.v1", "sub_law_id": "nabt.unit-carrier.v1",
                      "sound_law_id": "nabt-sound-shape-v1",
                      "lexical_attestation_inferred": False}, "Cell effect")
        check_present(response, expected_cell_effect(request), "Pinned sound-law replay")
        for key in ("unit_n", "entry", "exit", "weight"):
            if key in response:
                nat(response[key])
        if "sound_shape_accepted" in response:
            require(type(response["sound_shape_accepted"]) is bool, "Typed acceptance")
        if "effect" in response:
            require(type(response["effect"]) is list and len(response["effect"]) == 97, "Effect domain")
            for index, row in enumerate(response["effect"]):
                require(type(row) is dict and equal(row.get("entry"), index), "Effect entry identity")
                nat(row["exit"])
                nat(row["weight"])
            row = response["effect"][request["entry"]]
            check_present(response, {"exit": row["exit"], "weight": row["weight"]}, "Selected effect")
    elif op == "alphabet":
        for key in ("carriers", "cells", "non_sukun_cells", "sukun_cells"):
            if key in response:
                nat(response[key])
        for key in ("all_cells_are_phonetic_cv", "articulation_classes_acquired"):
            if key in response:
                require(type(response[key]) is bool, "Typed alphabet claim")


def observation(operation, inp, replies):
    """Project available measured fields only; no expected data is accepted."""
    result = {}

    def copy_fields(reply, mapping):
        for observed, actual in mapping.items():
            if actual in reply:
                result[observed] = deepcopy(reply[actual])

    if not replies:
        return result
    if operation == "alphabet":
        copy_fields(replies["alphabet"], {k: k for k in
                    ("cells", "non_sukun_cells", "sukun_cells", "all_cells_are_phonetic_cv")})
    elif operation == "ordered_quota":
        reply = replies["quota"]
        if reply.get("enumeration") in ("COMPLETE", "EXHAUSTED"):
            result["status"] = reply["enumeration"].lower()
        copy_fields(reply, {"count": "count", "complete": "search_complete",
                    "linguistically_rejected": "linguistic_rejection",
                    "linguistic_license_inferred": "linguistic_license_inferred"})
        if "shapes" in reply:
            shapes = reply["shapes"]
            result["shapes_set"] = sorted(set(shapes))
            result["contains"] = sorted(set(shapes))
            result["duplicates"] = len(shapes) != len(set(shapes))
            quotas = sorted({(s.count("C"), s.count("V")) for s in shapes})
            result["all_have_quota"] = list(quotas[0]) if len(quotas) == 1 else {"mixed_quotas": quotas}
    elif operation == "concatenate":
        actual, comparison = replies["composition"], replies["comparison"]
        copy_fields(actual, {"shape": "shape"})
        if all(k in r for r in (actual, comparison) for k in ("consonants", "vowels")):
            result["same_counts"] = equal([actual["consonants"], actual["vowels"]],
                                          [comparison["consonants"], comparison["vowels"]])
        if "shape" in actual and "shape" in comparison:
            result["same_order"] = actual["shape"] == comparison["shape"]
        if all(k in r for r in (actual, comparison) for k in ("shape_n", "alphabet_id")):
            require(actual["alphabet_id"] == comparison["alphabet_id"], "Shape number domains")
            result["same_content_key"] = equal(actual["shape_n"], comparison["shape_n"])
    elif operation == "sound_law":
        for mode in ("waqf", "wasl"):
            copy_fields(replies[mode], {mode + "_licensed": "sound_shape_accepted"})
        if all("lexical_attestation_inferred" in replies[mode] for mode in ("waqf", "wasl")):
            result["lexical_attestation_inferred"] = any(replies[m]["lexical_attestation_inferred"] for m in ("waqf", "wasl"))
    elif operation == "alternative_trees":
        left, right, comparison = replies["alternative_0"], replies["alternative_1"], replies["comparison"]
        if "same_derivation" in comparison:
            result["different_derivation"] = not comparison["same_derivation"]
        if "same_output" in comparison:
            result["same_yield"] = comparison["same_output"]
        if all(k in r for r in (left, right) for k in ("source", "extent")):
            result["same_source_extent"] = equal(left["source"], right["source"]) and equal(left["extent"], right["extent"])
        if all("licensed" in r for r in (left, right)) and "same_derivation" in comparison:
            count = int(left["licensed"]) + int(right["licensed"])
            if comparison["same_derivation"] and count == 2:
                count = 1
            result["retained_alternatives"] = count
            result["unique_derivation"] = count == 1
    elif operation == "withdraw_premise":
        before, after = replies["before"], replies["after"]
        if "licensed" in before and "licensed" in after and "verdict" in after:
            require(before["licensed"] is True, "Withdrawal control did not begin licensed")
            require(after["verdict"] == "UNKNOWN", "Withdrawal must cause missing support, not a different rejection")
            result["descendant_licensed"] = after["licensed"]
            result["stale_license_reused"] = after["licensed"]
    elif operation == "occurrence_identity":
        reply = replies["comparison"]
        if reply.get("comparison_scope") == "proposal_identity_only":
            copy_fields(reply, {"same_occurrence": "same_occurrence", "same_shape": "same_output"})
    elif "derivation" in replies:
        reply = replies["derivation"]
        copy_fields(reply, {"admitted": "licensed", "licensed": "licensed", "extent": "extent",
                    "reconstruction": "reconstruction", "rank": "rank", "conflict": "conflict",
                    "surface": "output", "source_preserved": "reconstruction_matches",
                    "reconstruction_valid": "reconstruction_matches"})
        if "output" in reply:
            result["shape"] = "".join(reply["output"])
        if "verdict" in reply:
            result["invalid_input"] = reply["verdict"] == "INVALID_DERIVATION"
            result["linguistically_rejected"] = reply["verdict"] == "REJECTED"
            result["status"] = {"LICENSED": "licensed", "UNKNOWN": "unknown", "REJECTED": "rejected",
                                "INVALID_DERIVATION": "invalid_input"}[reply["verdict"]]
            if "structural" in reply:
                invalid = reply["verdict"] == "INVALID_DERIVATION" and reply["structural"] is False
                if operation == "join" and "children" in inp:
                    if inp["children"][0][1] != inp["children"][1][0]:
                        result["gap_must_not_be_erased"] = invalid
                    if "right_revision" in inp:
                        result["foreign_source_binding"] = invalid
        if "premise_steps" in reply:
            steps = reply["premise_steps"]
            if steps and "offered_admitted_ids" in steps[0]:
                result["operation_evidence_reused"] = bool(steps[0]["offered_admitted_ids"])
            edits = [s for s in steps if s.get("target", {}).get("op") == "substitute"]
            if len(edits) == 1 and "displaced_output" in edits[0]:
                result["residual_removed"] = deepcopy(edits[0]["displaced_output"])
    return result


def field_agrees(field, actual, expected):
    if field in ("contains", "shapes_set"):
        if type(actual) is not list or type(expected) is not list or not all(type(x) is str for x in actual + expected):
            return False
        return set(expected) <= set(actual) if field == "contains" else set(actual) == set(expected)
    return equal(actual, expected)


def score(material, plan, responses):
    requests = {r["request_id"]: r for r in plan["requests"]}
    plans = {c["case_id"]: c for c in plan["cases"]}
    cases = []
    for case in material["cases"]:
        entry = plans[case["id"]]
        errors = []
        replies = {}
        for request_id in entry["requests"]:
            if request_id not in responses:
                errors.append("Missing probe response: " + request_id)
                continue
            row = requests[request_id]
            response = responses[request_id]
            try:
                validate_response(row["request"], response)
                if response.get("status") == "ERROR":
                    errors.append(request_id + ": " + response["error"])
                replies[row["label"]] = response
            except (ValueError, KeyError, TypeError) as error:
                errors.append(request_id + ": " + str(error))
        observed = {}
        if not errors:
            try:
                observed = observation(case["operation"], case["input"], replies)
            except (ValueError, KeyError, TypeError) as error:
                errors.append("Observation: " + str(error))
        assertions = []
        for field, expected in case["expected"].items():
            if errors:
                assertions.append({"field": field, "status": "FAIL", "expected": expected,
                                   "reason": "Probe execution/consistency failure prevents a valid measurement"})
            elif field not in observed:
                assertions.append({"field": field, "status": "UNMEASURED", "expected": expected,
                                   "reason": entry["unmeasured_reason"] or
                                   "This assertion has no explicit measured field in the supported operation."})
            else:
                actual = observed[field]
                assertions.append({"field": field, "status": "PASS" if field_agrees(field, actual, expected) else "FAIL",
                                   "expected": expected, "actual": actual})
        passed = sum(a["status"] == "PASS" for a in assertions)
        failed = sum(a["status"] == "FAIL" for a in assertions)
        unmeasured = sum(a["status"] == "UNMEASURED" for a in assertions)
        status = ("FAIL" if failed or errors else "UNMEASURED" if not passed else
                  "PARTIALLY_MEASURED" if unmeasured else "FULLY_MEASURED_PASS")
        cases.append({"case_id": case["id"], "group": case["group"], "status": status,
                      "assertions": assertions, "errors": errors, "notes": entry["notes"]})
    all_assertions = [a for c in cases for a in c["assertions"]]
    summary = {"cases": len(cases), "requests": len(plan["requests"]),
               "assertions": len(all_assertions),
               "measured_pass": sum(a["status"] == "PASS" for a in all_assertions),
               "fail": sum(a["status"] == "FAIL" for a in all_assertions),
               "unmeasured": sum(a["status"] == "UNMEASURED" for a in all_assertions),
               "execution_or_consistency_errors": sum(len(c["errors"]) for c in cases),
               "fully_measured_cases": sum(c["status"] == "FULLY_MEASURED_PASS" for c in cases),
               "partially_measured_cases": sum(c["status"] == "PARTIALLY_MEASURED" for c in cases),
               "unmeasured_cases": sum(c["status"] == "UNMEASURED" for c in cases)}
    summary["measured_contract_gate"] = summary["measured_pass"] > 0 and not summary["fail"] and not summary["execution_or_consistency_errors"]
    summary["coverage_complete"] = summary["unmeasured"] == 0
    summary["strict_pass"] = summary["measured_contract_gate"] and summary["coverage_complete"]
    summary["acquisition_measured"] = False
    return {"summary": summary, "cases": cases}


def stdin_bytes(plan):
    return "".join(canonical(row["request"]) + "\n" for row in plan["requests"]).encode("utf-8")


def response_rows(plan, stdout):
    lines = stdout.splitlines()
    require(len(lines) == len(plan["requests"]), "Response line count differs from closed request count")
    return {row["request_id"]: parse(line) for row, line in zip(plan["requests"], lines)}


def archive_sources(path):
    files = sorted((ROOT / "formal").glob("*.lean")) + sorted((ROOT / "formal/Nabt").glob("*.lean"))
    files += [ROOT / "formal/lean-toolchain", ROOT / "formal/lakefile.lean", MATERIAL,
              SOUND_TABLE, Path(__file__).resolve(), ROOT / "tests/test_progressive_unit_checker.py",
              ROOT / "tests/test_progressive_unit_probe.py"]
    files = sorted(set(files))
    members = {}
    with tarfile.open(path, "x:gz") as archive:
        for file in files:
            data = file.read_bytes()
            name = file.relative_to(ROOT).as_posix()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
            members[name] = {"bytes": len(data), "sha256": sha256(data).hexdigest()}
    with tarfile.open(path, "r:gz") as archive:
        actual = {m.name: {"bytes": m.size, "sha256": sha256(archive.extractfile(m).read()).hexdigest()}
                  for m in archive.getmembers()}
    require(actual == members, "Source archive verification failed")
    return members


def resolve_reference(reference, result_path):
    path = Path(reference["path"])
    candidates = [path, result_path.parent / path.name]
    if "repository_path" in reference:
        candidates.append(ROOT / reference["repository_path"])
    for candidate in candidates:
        if candidate.is_file() and file_ref(candidate)["sha256"] == reference["sha256"]:
            return candidate
    raise ValueError("Recorded artifact missing or changed: " + path.name)


def replay(saved_path, output):
    saved = parse(saved_path.read_bytes())
    require(saved["schema"] == SCHEMA, "Saved result schema")
    refs = saved["artifacts"]
    paths = {key: resolve_reference(value, saved_path) for key, value in refs.items()}
    with tarfile.open(paths["source_archive"], "r:gz") as archive:
        members = {m.name: {"bytes": m.size, "sha256": sha256(archive.extractfile(m).read()).hexdigest()}
                   for m in archive.getmembers()}
        require(members == saved["source_files"], "Closed source archive changed")
        material_bytes = archive.extractfile("evidence/progressive_units/independent_cases_v1.json").read()
    require(sha256(material_bytes).hexdigest() == MATERIAL_SHA, "Archived frozen cases differ")
    material = parse(material_bytes)
    plan = parse(paths["plan"].read_bytes())
    require(equal(plan, build_plan(material)), "Current input-only planner differs from saved plan")
    require(paths["stdin"].read_bytes() == stdin_bytes(plan), "Saved requests differ from closed plan")
    rescored = score(material, plan, response_rows(plan, paths["stdout"].read_bytes()))
    result = {"schema": "nabt.progressive-units.replay.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "saved_result": file_ref(saved_path), "replay_checker": file_ref(Path(__file__).resolve()),
              "source_archive_verified": True, "request_bytes_verified": True,
              "same_score": equal(rescored, saved["measurement"]), "measurement": rescored,
              "probe_calls": 0}
    write_json(output, result)
    return rescored["summary"]


def run_measurement(probe, output, lake=None):
    material = load_material()
    plan = build_plan(material)
    output.parent.mkdir(parents=True, exist_ok=True)
    stem = output.with_suffix("")
    paths = {"plan": Path(str(stem) + ".plan.json"), "stdin": Path(str(stem) + ".stdin.jsonl"),
             "stdout": Path(str(stem) + ".stdout.jsonl"), "stderr": Path(str(stem) + ".stderr.txt"),
             "source_archive": Path(str(stem) + ".sources.tar.gz")}
    require(not any(p.exists() for p in [output, *paths.values()]), "Exclusive evidence path already exists")
    write_json(paths["plan"], plan)
    with paths["stdin"].open("xb") as stream:
        stream.write(stdin_bytes(plan))
    source_files = archive_sources(paths["source_archive"])
    build = None
    if lake:
        built = subprocess.run([str(lake), "build", "progressiveUnitProbe"], cwd=ROOT / "formal",
                               capture_output=True, timeout=300)
        build = {"command": [str(lake), "build", "progressiveUnitProbe"], "returncode": built.returncode,
                 "stdout": built.stdout.decode("utf-8", errors="replace"),
                 "stderr": built.stderr.decode("utf-8", errors="replace")}
    execution_error = None
    stdout = stderr = b""
    returncode = None
    binary = file_ref(probe) if probe.is_file() else None
    try:
        require(build is None or build["returncode"] == 0, "Lean build failed")
        require(binary is not None, "Probe executable missing")
        run = subprocess.run([str(probe)], input=paths["stdin"].read_bytes(), capture_output=True, timeout=60)
        stdout, stderr, returncode = run.stdout, run.stderr, run.returncode
        require(returncode == 0, "Probe process failed")
        require(not stderr, "Unexpected probe stderr")
        responses = response_rows(plan, stdout)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        if isinstance(error, subprocess.TimeoutExpired):
            stdout, stderr = error.stdout or b"", error.stderr or b""
        execution_error = str(error)
        responses = {}
    for name, data in (("stdout", stdout), ("stderr", stderr)):
        with paths[name].open("xb") as stream:
            stream.write(data)
    measurement = score(material, plan, responses)
    result = {"schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "frozen independently authored contracts; not natural-language acquisition",
              "material_sha256": MATERIAL_SHA, "binary": binary, "binary_archived": False,
              "source_files": source_files, "artifacts": {key: file_ref(path) for key, path in paths.items()},
              "command": [str(probe)], "build": build, "returncode": returncode,
              "execution_error": execution_error, "measurement": measurement}
    write_json(output, result)
    return measurement["summary"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--lake", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    try:
        if args.replay:
            summary = replay(args.replay.resolve(), args.output.resolve())
        else:
            probe = (args.probe or ROOT / "formal/.lake/build/bin/progressiveUnitProbe").resolve()
            summary = run_measurement(probe, args.output.resolve(), args.lake)
        print(canonical(summary))
        return 0 if summary["measured_contract_gate"] and (not args.require_complete or summary["coverage_complete"]) else 1
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print("progressive-unit checker: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent checks of a supplied-atom, conditional-evidence Lean contract.

The request planner consumes inputs only. It never turns an expected Arabic
answer into a probe request or credits an absent API field as a successful
linguistic judgment. Unrepresented judgments remain UNMEASURED.
"""

from __future__ import annotations

import argparse
import base64
import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import tarfile
import sys

ROOT = Path(__file__).resolve().parents[1]
MATERIAL_DIR = ROOT / "evidence/unit_discovery"
PINS = {
    "material_v2.json": "5ee2c4ec6f47334f8b27f48b995e147611ffd79ef3327ded147069fea2767e26",
    "protocol_v2.md": "55dedbab1efdfe0439f21d94439e3e228f464c194e0c56fbd565110b5c70ba0a",
    "material_freeze_v2.json": "f0db40442ea8a510064e16714d69e5b8bfccdd83816e3a11722f6e4e24464dbc",
}
LAW_ID = "nabt.unit-discovery.v1"
SCOPE = "conditional_on_supplied_interpretations"
REQUIREMENTS = {"surface_covered": 0, "unit_class": 1,
                "host_compatible": 2, "attachment_licensed": 3}
STAGES = [[], [1], [1, 2], [1, 2, 3]]
CORE_REQUIRED_FIELDS = {
    "UD-M01": {"counts", "empty_input_partitions", "three_atom_cut_sets", "three_atom_partitions"},
    "UD-M02": {"counts_by_segment_count", "two_segment_cut_sets"},
    "UD-M03": {"mechanical_status"}, "UD-M04": {"mechanical_status"},
    "UD-M05": {"partition_count", "three_atom_cut_sets", "merge_equal_position_identities"},
    "UD-M06": {"mechanical_status"}, "UD-M07": {"proposal_statuses", "source_must_be_covered_once"},
    "UD-M08": {"partition_count", "allowed_internal_byte_cuts", "cut_at_byte_2_status", "normalization_performed"},
    "UD-E01": {"surface_status", "classification_status", "attachment_status", "rename_changes_mechanical_partitions"},
    "UD-E02": {"surface_status", "classification_status", "host_status", "attachment_status", "required_witness_ids"},
    "UD-E03": {"classification_status", "host_status", "attachment_status", "duplicate_evidence_advances_stage"},
    "UD-E04": {"attachment_status"},
    "UD-E05": {"certificate_valid", "fresh_attachment_status", "wrong_occurrence_witness_usable"},
    "UD-E06": {"certificate_valid", "fresh_attachment_status", "cross_reading_feature_merge"},
    "UD-E07": {"certificate_valid", "fresh_classification_status", "fresh_attachment_status", "rule_identity_substitution_accepted"},
    "UD-E08": {"initial_attachment_status", "old_certificate_valid_after_each_operation", "fresh_surface_status", "fresh_attachment_status"},
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def equal(left, right):
    # JSON's booleans and integers must remain different values.
    return canonical(left) == canonical(right)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_ref(path):
    digest, size = sha256(), 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block); size += len(block)
    return {"path": str(path), "bytes": size, "sha256": digest.hexdigest()}


def verified_archive(path, inputs):
    members = {}
    with tarfile.open(path, "x:gz") as archive:
        for p in inputs:
            relative = p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else "external/" + p.name
            require(relative not in members, "Duplicate snapshot member")
            data = p.read_bytes(); members[relative] = sha256(data).hexdigest()
            info = tarfile.TarInfo(relative); info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    with tarfile.open(path, "r:gz") as archive:
        observed = {m.name: sha256(archive.extractfile(m).read()).hexdigest() for m in archive.getmembers()}
    require(observed == members, "Closed archive verification failed")
    return members


def load_material():
    for name, pin in PINS.items():
        require(sha256((MATERIAL_DIR / name).read_bytes()).hexdigest() == pin,
                "Frozen material differs: " + name)
    data = parse((MATERIAL_DIR / "material_v2.json").read_bytes())
    require(data["schema"] == "nabt.unit-discovery.independent-material.v2", "Material schema")
    cases = data["cases"]
    require(len(cases) == 40 and len({c["id"] for c in cases}) == 40, "Case inventory")
    require({group: sum(c["group"] == group for c in cases)
             for group in data["group_counts"]} == data["group_counts"], "Group inventory")
    return data


@dataclass
class Ids:
    """An explicit finite bijection, constructed before any probe output exists."""

    rows: list = field(default_factory=list)
    forward: dict = field(default_factory=dict)

    def get(self, namespace, value):
        key = (namespace, canonical(value))
        if key not in self.forward:
            index = len(self.rows) + 1
            self.forward[key] = index
            self.rows.append({"id": index, "namespace": namespace, "value": value})
        return self.forward[key]

    def value(self, namespace, index):
        for row in self.rows:
            if row["namespace"] == namespace and row["id"] == index:
                return row["value"]
        raise ValueError("Unregistered returned ID")


@dataclass
class Plan:
    ids: Ids = field(default_factory=Ids)
    requests: list = field(default_factory=list)
    cases: dict = field(default_factory=dict)

    def add(self, case_id, label, request):
        key = case_id + ":" + label
        require(key not in {r["request_id"] for r in self.requests}, "Duplicate request ID")
        self.requests.append({"request_id": key, "case_id": case_id,
                              "label": label, "request": request})
        self.cases.setdefault(case_id, {})[label] = key


def atom_texts(inp):
    return [a["text"] if isinstance(a, dict) else a for a in inp["atoms"]]


def span(source, interval):
    return {**{k: source[k] for k in ("source_id", "revision", "scope_id", "atomization_id")},
            "start": interval[0], "stop": interval[1]}


def source_for(plan, case_id, atoms, binding=None):
    b = binding or {}
    return {"source_id": plan.ids.get("source", b.get("source_id", case_id)),
            "revision": plan.ids.get("revision", b.get("source_revision", "initial")),
            "scope_id": plan.ids.get("scope", b.get("scope", "review")),
            "atomization_id": plan.ids.get("atomization", "declared_units_v1"),
            "atoms": list(atoms)}


def parts_from_intervals(atoms, unit, host):
    cuts = sorted({0, len(atoms), *unit, *host})
    require(all(type(x) is int and 0 <= x <= len(atoms) for x in cuts), "Proposal intervals")
    parts = [atoms[a:b] for a, b in zip(cuts, cuts[1:]) if a < b]
    require(unit[0] < unit[1], "Empty proposed unit")
    # Unit intervals in this material are single parts; do not silently merge a split unit.
    part_index = next((i for i, (a, b) in enumerate(zip(cuts, cuts[1:]))
                       if [a, b] == list(unit)), None)
    require(part_index is not None, "Unit must be a declared whole part")
    return parts, part_index


def target_for(plan, case_id, atoms, binding, class_label="opaque_kappa", claim="attachment"):
    source = source_for(plan, case_id, atoms, binding)
    unit = binding.get("unit_interval", [0, 1])
    host = binding.get("host_interval", [1, len(atoms)])
    parts, index = parts_from_intervals(atoms, unit, host)
    return {"source": source, "parts": parts, "part_index": index,
            "host": span(source, host), "unit_class": plan.ids.get("class", class_label),
            "claim": claim, "rule_id": plan.ids.get("rule", binding.get("rule_id", "declared_rule")),
            "reading_id": plan.ids.get("reading", binding.get("reading_id", "r0")),
            "occurrence_id": plan.ids.get("occurrence", binding.get("occurrence_id", "o0")),
            "requirements": [1, 2, 3]}


def ledger_request(plan, case_id, atoms, binding, witnesses, class_label="opaque_kappa"):
    target = target_for(plan, case_id, atoms, binding, class_label)
    inventory = [target["source"]]
    receipts = []
    for w in witnesses:
        wb = w.get("binding", binding)
        # A class-valued observation witnesses THAT class. It must not be
        # coerced into a generic positive answer about the caller's class.
        witnessed_class = w["value"] if w["predicate"] == "unit_class" and type(w["value"]) is not bool else class_label
        require(w["predicate"] == "unit_class" or type(w["value"]) is bool,
                "Non-class evidence must have an explicit Boolean polarity")
        wt = target_for(plan, case_id, atoms, wb, witnessed_class)
        ws = wt["source"]
        if ws not in inventory:
            inventory.append(ws)
        positive = w["value"] if type(w["value"]) is bool else True
        receipts.append({"target": wt, "requirement": REQUIREMENTS[w["predicate"]],
                         "positive": positive,
                         "witness_id": plan.ids.get("witness", w["witness_id"]),
                         "supports": [{"source": ws, "span": span(ws, [0, len(atoms)])}]})
    return {"op": "ledger", "target": target, "inventory": inventory,
            "interpreted": receipts, "offered": copy.deepcopy(receipts),
            "stage_requirements": STAGES}


def plan_evidence(plan, case_id, inp):
    atoms = atom_texts(inp)
    witnesses = inp.get("witnesses", inp.get("initial_witnesses", []))
    binding = inp.get("proposal_binding", inp.get("initial_binding"))
    if binding is None:
        binding = witnesses[0]["binding"]
    class_label = inp.get("supplied_class_name", "opaque_kappa")
    req = ledger_request(plan, case_id, atoms, binding, witnesses, class_label)
    plan.add(case_id, "ledger", req)
    plan.add(case_id, "surface", {"op": "inspect_partition", "atoms": atoms,
                                  "position_groups": [list(range(len(atoms)))]})
    if "renamed_class_name" in inp:
        renamed = ledger_request(plan, case_id, atoms, binding, witnesses, inp["renamed_class_name"])
        plan.add(case_id, "renamed_ledger", renamed)
        plan.add(case_id, "partitions", {"op": "partitions", "atoms": atoms})
        # Category names are intentionally absent from the mechanical API.
        plan.add(case_id, "renamed_partitions", {"op": "partitions", "atoms": atoms})
    if "duplicate_witness_id" in inp:
        duplicate = copy.deepcopy(req)
        wid = plan.ids.get("witness", inp["duplicate_witness_id"])
        row = next(r for r in req["offered"] if r["witness_id"] == wid)
        duplicate["offered"] += [copy.deepcopy(row)] * inp["duplicate_repetitions"]
        plan.add(case_id, "duplicated_ledger", duplicate)
    if "second_rule_attempt" in inp:
        changed = copy.deepcopy(req)
        changed["target"]["rule_id"] = plan.ids.get("rule", inp["second_rule_attempt"]["rule_id"])
        plan.add(case_id, "other_rule", changed)
    if "operations" in inp:
        withdrawn = copy.deepcopy(req)
        withdrawn["interpreted"] = [r for r in req["interpreted"] if r["requirement"] == 0]
        plan.add(case_id, "withdrawn", withdrawn)
        revised = copy.deepcopy(req)
        new_source = copy.deepcopy(req["target"]["source"])
        new_source["revision"] = plan.ids.get("revision", "rev_b")
        revised["target"]["source"] = new_source
        revised["target"]["host"]["revision"] = new_source["revision"]
        revised["inventory"] = [new_source]
        plan.add(case_id, "revised", revised)


def template_pattern(inp):
    premises = inp.get("premises", [])
    roots = [p["value"] for p in premises if p["kind"] == "declared_root"]
    if not roots:
        return None
    root = roots[0]
    template = next((p["value"] for p in premises if p["kind"] == "declared_template"), None)
    positions = next((p["value"] for p in premises if p["kind"] == "declared_root_slot_map"), None)
    pattern = []
    if template is not None:
        marks = {"a": "َ", "i": "ِ", "u": "ُ", "sukun": "ْ"}
        for cell in template.split(","):
            if cell == "alif":
                pattern.append({"literal": "ا"})
                continue
            slot, mark = cell.split("+", 1)
            require(slot.startswith("R") and slot[1:].isdigit(), "Declared template slot")
            pattern.append({"slot": int(slot[1:]) - 1})
            if mark == "terminal_tanwin":
                terminal = inp["raw_text"][-1]
                require(terminal in "ًٌٍ", "Declared terminal tanwin missing")
                pattern.append({"literal": terminal})
            else:
                require(mark in marks, "Undeclared template syntax")
                pattern.append({"literal": marks[mark]})
    elif positions is not None:
        for index, atom in enumerate(atom_texts(inp)):
            if index in positions:
                pattern.append({"slot": positions.index(index)})
                pattern.extend({"literal": char} for char in atom[1:])
            else:
                pattern.extend({"literal": char} for char in atom)
    else:
        return None
    return {"op": "root_replay", "arity": len(root), "root": root,
            "pattern": pattern, "surface": inp["raw_text"]}


def annotated_ledger(plan, case_id, inp):
    """Compile explicit annotations into an opaque conditional claim, not Arabic truth."""
    premises = inp.get("premises", [])
    atoms = atom_texts(inp)
    host_p = next((p for p in premises if p["kind"] == "annotated_host"), None)
    unit_p = next((p for p in premises if p["kind"] in
                   {"annotated_unit", "annotated_unit_reading", "annotated_suffix"}), None)
    link_p = next((p for p in premises if p["kind"] in
                   {"declared_attachment_rule_instance", "declared_connection_witness",
                    "declared_affix_map", "declared_form_correspondence"}), None)
    whole = next((p for p in premises if p["kind"] == "annotated_full_word"), None)
    if unit_p is None and whole is not None and whole["value"] == "relative_pronoun":
        unit_p = {**whole, "atom_interval": [0, len(atoms)]}
    if unit_p is None and link_p is None and host_p is None:
        return
    link_value = link_p.get("value", {}) if link_p else {}
    if not isinstance(link_value, dict):
        link_value = {}
    unit = (unit_p or {}).get("atom_interval", (link_p or {}).get("unit_interval"))
    if unit is None:
        unit = link_value.get("protection_nun_interval", link_value.get("raising_nun_interval",
                link_value.get("nominal_nun_interval", [0, len(atoms)])))
    host = (host_p or {}).get("atom_interval", (link_p or {}).get("host_interval",
            link_value.get("host_interval", [0, len(atoms)])))
    # The interval is a supplied proposal. If it overlaps a boundary of the
    # declared host, keep this adapter operation unavailable rather than edit it.
    binding = {"source_id": case_id, "source_revision": "frozen_input", "scope": "review",
               "occurrence_id": case_id, "reading_id": "annotated_reading",
               "unit_interval": unit, "host_interval": host,
               "rule_id": (link_p or {}).get("rule", link_value.get("rule", "declared_link"))}
    facts = [{"witness_id": case_id + ":raw", "predicate": "surface_covered", "value": True}]
    if unit_p is not None:
        facts.append({"witness_id": case_id + ":" + unit_p["id"],
                      "predicate": "unit_class", "value": unit_p.get("value", "annotated_unit")})
    family = next((p for p in premises if p["kind"] == "annotated_paradigm"), None)
    if host_p is not None or (family and family.get("value", {}).get("aspect")):
        facts.append({"witness_id": case_id + ":host", "predicate": "host_compatible", "value": True})
    if link_p is not None:
        facts.append({"witness_id": case_id + ":link", "predicate": "attachment_licensed", "value": True})
    label = (unit_p or {}).get("value", "declared_relation")
    try:
        req = ledger_request(plan, case_id, atoms, binding, facts, label)
    except ValueError:
        return
    plan.add(case_id, "annotation_ledger", req)
    if unit_p is not None and whole is not None and whole.get("value") == "relative_pronoun":
        proposed = next((p for p in premises if p["kind"] == "proposal"), None)
        if proposed:
            alt_binding = {**binding, "unit_interval": proposed["unit_interval"],
                           "host_interval": proposed["host_interval"], "rule_id": "unproved_article"}
            alt = ledger_request(plan, case_id, atoms, alt_binding, facts[:1], proposed["value"])
            # Offer the original whole-word class certificate to the changed target.
            alt["interpreted"] += req["interpreted"][1:]
            alt["offered"] += req["offered"][1:]
            plan.add(case_id, "unproved_article", alt)


def plan_arabic(plan, case_id, inp):
    atoms = atom_texts(inp)
    plan.add(case_id, "partitions", {"op": "partitions", "atoms": atoms})
    replay = template_pattern(inp)
    if replay:
        plan.add(case_id, "root", replay)
    premises = inp.get("premises", [])
    constraints = []
    for p in premises:
        if p["kind"] == "annotated_gender":
            constraints.append(p["value"])
        if p["kind"] == "annotated_paradigm" and isinstance(p["value"], dict):
            for key in ("gender", "number"):
                if p["value"].get(key) in {"masculine", "feminine", "singular", "dual", "plural"}:
                    constraints.append(p["value"][key])
    if constraints or any(p["kind"] == "annotated_full_word" and p["value"] == "proper_name" for p in premises):
        plan.add(case_id, "nominal", {"op": "nominal_profiles", "constraints": constraints})
    profiles = [p["value"] for p in premises if p["kind"] in
                {"annotated_paradigm", "alternative_annotated_reading"}
                and isinstance(p.get("value"), dict) and p["value"].get("aspect") == "imperfect"]
    if profiles:
        profile = profiles[0]
        family = "plain"
        if profile.get("number") == "dual": family = "dual"
        elif profile.get("number") == "plural" and profile.get("gender") == "feminine": family = "feminine_plural"
        elif profile.get("number") == "plural" and profile.get("gender") == "masculine": family = "masculine_plural"
        plan.add(case_id, "person", {"op": "person_profiles", "family": family,
                                     "pre": atoms[0][0], "qualified": True})
        plan.add(case_id, "person_unqualified", {"op": "person_profiles", "family": family,
                                                 "pre": atoms[0][0], "qualified": False})
    annotated_ledger(plan, case_id, inp)


def make_plan(material):
    plan = Plan()
    # Deliberately restrict the planner's view to id/group/input.
    for original in material["cases"]:
        case_id, group, inp = original["id"], original["group"], copy.deepcopy(original["input"])
        plan.cases.setdefault(case_id, {})
        if group == "evidence_binding":
            plan_evidence(plan, case_id, inp)
        elif group == "annotated_arabic":
            plan_arabic(plan, case_id, inp)
        elif "examples" in inp:
            for index, example in enumerate(inp["examples"]):
                plan.add(case_id, "example_" + str(index), {"op": "partitions", "atoms": example["atoms"]})
        elif "proposed_position_groups" in inp:
            plan.add(case_id, "inspect", {"op": "inspect_partition", "atoms": inp["atoms"],
                                          "position_groups": inp["proposed_position_groups"]})
        elif "proposals" in inp:
            for proposal in inp["proposals"]:
                plan.add(case_id, proposal["id"], {"op": "inspect_partition", "atoms": inp["atoms"],
                                                  "position_groups": proposal["position_groups"]})
        else:
            request = {"op": "partitions", "atoms": atom_texts(inp)}
            if "proposed_internal_byte_cut" in inp:
                request["byte_offsets"] = [inp["proposed_internal_byte_cut"]]
            plan.add(case_id, "partitions", request)
    return plan


def is_nat(value, maximum=None):
    return type(value) is int and value >= 0 and (maximum is None or value <= maximum)


def scalar(value):
    return isinstance(value, str) and len(value) == 1 and not 0xD800 <= ord(value) <= 0xDFFF


def logical_assessment(requirements, accepted, well_formed=True):
    """Independent set-of-polarities oracle for consistency of one returned ledger."""
    if not well_formed:
        return "INVALID_HYPOTHESIS", False
    needed = {0, *requirements}
    positive = {r["requirement"] for r in accepted if r["positive"] is True}
    negative = {r["requirement"] for r in accepted if r["positive"] is False}
    conflict = bool(needed & positive & negative)
    verdict = "REJECTED" if needed & negative else "LICENSED" if needed <= positive else "UNKNOWN"
    return verdict, conflict


def validate_ledger(request, result):
    require(result.get("verdict") in {"UNKNOWN", "LICENSED", "REJECTED", "INVALID_HYPOTHESIS"}, "Ledger verdict")
    require(type(result.get("well_formed")) is bool and type(result.get("conflict")) is bool, "Ledger Boolean type")
    require(all(is_nat(x) for x in result["admitted_ids"]), "Admitted ID type")
    require(len(result["receipt_checks"]) == len(request["offered"]), "Receipt check inventory")
    accepted = []
    for given, row in zip(request["offered"], result["receipt_checks"]):
        require(is_nat(row["witness_id"]) and row["witness_id"] == given["witness_id"]
                and type(row["accepted"]) is bool, "Receipt correlation")
        require(row["accepted"] is (row["reason"] == "ACCEPTED"), "Receipt reason contradicts acceptance")
        if row["accepted"]:
            require(result["well_formed"], "Malformed target admitted a receipt")
            accepted.append(given)
    require(equal(result["admitted_ids"], [r["witness_id"] for r in accepted]),
            "Admitted IDs contradict accepted receipt rows")
    atoms = {(r["requirement"], r["positive"]) for r in accepted}
    got = []
    for row in result["supported_atoms"]:
        require(is_nat(row["requirement"]) and type(row["positive"]) is bool, "Logical atom type")
        got.append((row["requirement"], row["positive"]))
    require(len(got) == len(set(got)) and set(got) == atoms, "Supported atoms contradict accepted receipts")
    required = [0, *request["target"]["requirements"]]
    require(all(is_nat(x) for x in result["requirements"]) and equal(result["requirements"], required),
            "Mandatory/source requirement inventory")
    reported = {}
    for row in result["per_requirement"]:
        r = row["requirement"]
        require(is_nat(r) and r not in reported, "Per-requirement identity/type")
        require(type(row["positive"]) is bool and type(row["negative"]) is bool, "Requirement polarity type")
        positive, negative = (r, True) in atoms, (r, False) in atoms
        state = "CONFLICT" if positive and negative else "POSITIVE" if positive else "NEGATIVE" if negative else "UNKNOWN"
        require(row["positive"] is positive and row["negative"] is negative and row["state"] == state,
                "Per-requirement evidence contradicts accepted receipts")
        reported[r] = row
    require(set(reported) == set(required), "Per-requirement inventory")
    verdict, conflict = logical_assessment(request["target"]["requirements"], accepted, result["well_formed"])
    require(result["verdict"] == verdict and result["conflict"] is conflict, "Ledger verdict contradicts requirement evidence")
    require(len(result["stages"]) == len(request.get("stage_requirements", [])), "Stage inventory")
    for stage, requirements in zip(result["stages"], request.get("stage_requirements", [])):
        require(all(is_nat(x) for x in stage["requirements"]) and equal(stage["requirements"], [0, *requirements]),
                "Stage requirement correlation")
        verdict, conflict = logical_assessment(requirements, accepted, result["well_formed"])
        require(stage["verdict"] == verdict and type(stage["conflict"]) is bool and stage["conflict"] is conflict,
                "Stage assessment contradicts its requirement evidence")


def validate_root(request, result):
    arity = request["arity"]
    require(type(arity) is int and arity in {3, 4}, "Requested root arity type/domain")
    require(type(result.get("arity")) is int and result["arity"] == arity, "Returned root arity")
    require(isinstance(request["root"], list) and len(request["root"]) == arity
            and all(scalar(x) for x in request["root"]), "Requested root scalar inventory")
    slots = set()
    def render(radicals):
        chars = []
        for token in request["pattern"]:
            require(isinstance(token, dict) and len(token) == 1, "Root pattern token")
            if "literal" in token:
                require(scalar(token["literal"]), "Pattern literal is not one Unicode scalar")
                chars.append(token["literal"])
            else:
                require(set(token) == {"slot"} and is_nat(token["slot"], arity - 1), "Pattern slot type/domain")
                slots.add(token["slot"])
                chars.append(radicals[token["slot"]])
        return "".join(chars)
    generated = render(request["root"])
    complete = slots == set(range(arity))
    require(type(result.get("complete")) is bool and type(result.get("shape_matches")) is bool, "Root response Boolean type")
    require(result["complete"] is complete, "Root completeness disagrees with declared slot inventory")
    require(isinstance(result.get("generated_surface"), str) and result["generated_surface"] == generated,
            "Generated surface disagrees with supplied root/pattern")
    matches = complete and generated == request["surface"]
    require(result["shape_matches"] is matches, "Shape match contradicts completeness or source rendering")
    recovered = result["recovered_root"]
    if recovered is not None:
        require(isinstance(recovered, list) and len(recovered) == arity and all(scalar(x) for x in recovered),
                "Recovered root arity/scalar domain")
        require(complete and render(recovered) == request["surface"], "Recovered root does not replay the source surface")
    if matches:
        require(equal(recovered, request["root"]), "A complete matching root was not recovered intact")


def validate_profiles(request, result):
    profiles = result.get("profiles")
    require(isinstance(profiles, list), "Profile inventory type")
    require(len({canonical(p) for p in profiles}) == len(profiles), "Duplicate profiles")
    if request["op"] == "nominal_profiles":
        require(result.get("sub_law_id") == "nabt.nominal-evidence.v1", "Nominal sub-law")
        for p in profiles:
            require(all(is_nat(p.get(k), maximum) for k, maximum in
                        (("gender", 1), ("form", 5), ("definiteness", 1), ("number", 2), ("code", 23))),
                    "Nominal profile integer domain (Bool is not Nat)")
            require(p["code"] == 12 * p["gender"] + 2 * p["form"] + p["definiteness"], "Nominal profile code correlation")
            require(p["number"] == (0 if p["form"] == 0 else 1 if p["form"] == 1 else 2), "Nominal profile number/form correlation")
    else:
        require(result.get("sub_law_id") == "nabt.person-evidence.v1", "Person sub-law")
        for p in profiles:
            require(type(p.get("person")) is int and 1 <= p["person"] <= 3
                    and is_nat(p.get("gender"), 2) and is_nat(p.get("number"), 2),
                    "Person profile integer domain (Bool is not Nat)")
            if p["person"] == 1:
                require(p["gender"] == 2 and p["number"] in {0, 2}, "First person profile domain")
                code = "1" + {0: "S", 2: "P"}[p["number"]]
            else:
                require(p["gender"] in {0, 1}, "Second/third person gender domain")
                code = str(p["person"]) + {0: "M", 1: "F"}[p["gender"]] + {0: "S", 1: "D", 2: "P"}[p["number"]]
            require(isinstance(p.get("qac"), str) and p["qac"] == code, "Person QAC code/profile correlation")


def validate_response(request, result):
    require(isinstance(result, dict), "Probe response is not an object")
    require(result.get("law_id") == LAW_ID and result.get("conditional") is True,
            "Probe law identity or conditional scope")
    require(result.get("scope") == SCOPE, "Probe scope identity")
    require("error" not in result, "Probe execution/input error: " + str(result.get("error")))
    require(result.get("status") == "OK" and result.get("op") == request["op"], "Probe response operation/status")
    op = request["op"]
    if op == "partitions":
        groups, parts, cuts = result["position_groups"], result["parts"], result["cut_sets"]
        require(type(result["count"]) is int and result["count"] == len(groups) == len(parts) == len(cuts), "Partition inventory")
        atoms = request["atoms"]
        for positions, chunks, cut in zip(groups, parts, cuts):
            require(all(isinstance(p, list) and p for p in positions), "Empty position part")
            flattened = [x for p in positions for x in p]
            require(all(type(x) is int for x in flattened) and flattened == list(range(len(atoms))), "Partition does not preserve positions")
            require(chunks == [[atoms[i] for i in p] for p in positions], "Atom bytes/order changed")
            require(cut == [p[-1] + 1 for p in positions[:-1]], "Cut/group mismatch")
        require(len({canonical(p) for p in groups}) == len(groups), "Duplicate partitions")
    elif op == "inspect_partition":
        require(type(result.get("valid")) is bool, "Inspect verdict type")
    elif op == "ledger":
        validate_ledger(request, result)
    elif op == "root_replay":
        validate_root(request, result)
    elif op in {"person_profiles", "nominal_profiles"}:
        validate_profiles(request, result)


def assessment_vector(response):
    return {k: response[k] for k in ("verdict", "conflict", "per_requirement", "stages")}


def observations(case, plan, responses):
    """Project genuine probe observations; unknown keys stay unmeasured."""
    cid, inp = case["id"], case["input"]
    rows = {label: responses[key] for label, key in plan.cases[cid].items()}
    obs = {}
    def put(key, value, labels, kind="DIRECT_PROBE_JUDGMENT"):
        obs[key] = {"value": value, "request_ids": [plan.cases[cid][x] for x in labels], "evidence_kind": kind}
    if "examples" in inp:
        names = ["example_" + str(i) for i in range(len(inp["examples"]))]
        put("counts", [rows[k]["count"] for k in names], names)
        put("empty_input_partitions", rows[names[0]]["parts"], [names[0]])
        k = next(names[i] for i, x in enumerate(inp["examples"]) if len(x["atoms"]) == 3)
        put("three_atom_cut_sets", sorted(rows[k]["cut_sets"]), [k])
        put("three_atom_partitions", rows[k]["parts"], [k])
        put("category_annotations_required", False, names, "CATEGORY_FREE_OPERATION_SUCCEEDED")
    if "inspect" in rows:
        put("mechanical_status", "LICENSED" if rows["inspect"]["valid"] else "REJECTED", ["inspect"])
    if "proposals" in inp:
        names = [p["id"] for p in inp["proposals"]]
        put("proposal_statuses", {k: "LICENSED" if rows[k]["valid"] else "REJECTED" for k in names}, names)
        put("source_must_be_covered_once", all(not rows[k]["valid"] for k in names), names, "DECLARED_COUNTEREXAMPLES")
    if "partitions" in rows:
        p = rows["partitions"]
        put("partition_count", p["count"], ["partitions"])
        put("three_atom_cut_sets", sorted(p["cut_sets"]), ["partitions"])
        put("normalization_performed", False, ["partitions"], "EXACT_RETURNED_ATOM_BYTES")
        put("merge_equal_position_identities", False, ["partitions"], "VALIDATED_POSITION_INVENTORY")
        put("source_recomposition_exact", True, ["partitions"], "VALIDATED_ALL_RETURNED_PARTITIONS")
        if "segment_counts" in inp:
            put("counts_by_segment_count", [sum(len(g) == k for g in p["position_groups"]) for k in inp["segment_counts"]], ["partitions"])
            put("two_segment_cut_sets", [cut for cut, g in zip(p["cut_sets"], p["position_groups"]) if len(g) == 2], ["partitions"])
        if "proposed_internal_byte_cut" in inp:
            put("allowed_internal_byte_cuts", p["atom_byte_boundaries"][1:-1], ["partitions"])
            check = next(x for x in p["byte_cut_checks"] if x["offset"] == inp["proposed_internal_byte_cut"])
            put("cut_at_byte_2_status", "LICENSED" if check["allowed"] else "REJECTED", ["partitions"])
        if "raw_text" in inp:
            # Use returned atom bytes after their exact validation, not an expected answer.
            returned = [x for part in p["parts"][0] for x in part]
            put("written_nun_clusters", sum("ن" in a for a in returned), ["partitions"])
            put("tanwin_observed", bool(returned and returned[-1][-1:] in "ًٌٍ"), ["partitions"])
            put("hamza_seat_folded", "".join(returned) != inp["raw_text"], ["partitions"])
            supplied_parts = next((x["value"] for x in inp.get("premises", []) if x["kind"] == "annotated_surface_parts"), None)
            if supplied_parts:
                groups = [list(range(a, b)) for a, b in supplied_parts]
                index = p["position_groups"].index(groups)
                put("surface_parts_text", ["".join(chunk) for chunk in p["parts"][index]], ["partitions"])
    if "ledger" in rows:
        r = rows["ledger"]
        for key, stage in (("classification_status", 1), ("fresh_classification_status", 1), ("host_status", 2)):
            put(key, r["stages"][stage]["verdict"], ["ledger"])
        for key in ("attachment_status", "fresh_attachment_status", "initial_attachment_status"):
            put(key, r["verdict"], ["ledger"])
        put("required_witness_ids", [plan.ids.value("witness", i) for i in dict.fromkeys(r["admitted_ids"])], ["ledger"])
        put("certificate_valid", r["verdict"] == "LICENSED" and all(x["accepted"] for x in r["receipt_checks"]), ["ledger"])
        for key in ("wrong_occurrence_witness_usable", "cross_reading_feature_merge"):
            request = next(x["request"] for x in plan.requests if x["request_id"] == plan.cases[cid]["ledger"])
            bad_ids = {w["witness_id"] for w in request["offered"] if w["target"] != request["target"]}
            put(key, any(x["accepted"] for x in r["receipt_checks"] if x["witness_id"] in bad_ids), ["ledger"])
        if "surface" in rows:
            for key in ("surface_status", "fresh_surface_status"):
                put(key, "LICENSED" if rows["surface"]["valid"] else "REJECTED", ["surface"])
        if "renamed_partitions" in rows:
            put("rename_changes_mechanical_partitions", rows["partitions"]["parts"] != rows["renamed_partitions"]["parts"], ["partitions", "renamed_partitions"])
        if "duplicated_ledger" in rows:
            put("duplicate_evidence_advances_stage", not equal(assessment_vector(r), assessment_vector(rows["duplicated_ledger"])), ["ledger", "duplicated_ledger"])
        if "other_rule" in rows:
            put("rule_identity_substitution_accepted", any(x["accepted"] for x in rows["other_rule"]["receipt_checks"]), ["other_rule"])
        if "withdrawn" in rows:
            put("old_certificate_valid_after_each_operation", any(rows[x]["verdict"] == "LICENSED" for x in ("withdrawn", "revised")), ["withdrawn", "revised"])
            put("fresh_attachment_status", rows["withdrawn"]["verdict"], ["withdrawn"])
    if "annotation_ledger" in rows:
        r = rows["annotation_ledger"]
        # These are explicitly the status of a supplied annotation, not an acquired class.
        for key in ("annotated_article_attachment_status", "annotated_relative_al_status", "annotated_suffix_attachment_status"):
            put(key, r["verdict"], ["annotation_ledger"], "SUPPLIED_ANNOTATION_CONDITIONAL_LEDGER")
        put("whole_relative_reading_status", r["stages"][1]["verdict"], ["annotation_ledger"], "SUPPLIED_ANNOTATION_CONDITIONAL_LEDGER")
    if "unproved_article" in rows:
        r = rows["unproved_article"]
        put("article_attachment_status", r["verdict"], ["unproved_article"])
        request = next(x["request"] for x in plan.requests if x["request_id"] == plan.cases[cid]["unproved_article"])
        bad = {x["witness_id"] for x in request["offered"] if x["target"] != request["target"]}
        put("relative_witness_reused_as_article_witness", any(x["accepted"] for x in r["receipt_checks"] if x["witness_id"] in bad), ["unproved_article"])
    if "root" in rows:
        r = rows["root"]
        put("template_status", "LICENSED" if r["shape_matches"] else "REJECTED", ["root"])
        if r["recovered_root"] is not None:
            put("root_arity", len(r["recovered_root"]), ["root"])
        put("skip_mismatched_mark", r["shape_matches"] and r["generated_surface"] != inp["raw_text"], ["root"])
    if "nominal" in rows:
        profiles = rows["nominal"]["profiles"]
        genders = {p["gender"] for p in profiles}
        if len(genders) == 1:
            put("declared_gender", {0: "masculine", 1: "feminine"}[next(iter(genders))], ["nominal"], "SUPPLIED_GENDER_CONSTRAINT")
        # No proper_name -> definite inference is implemented by this operation.
    if "person" in rows:
        profiles = rows["person"]["profiles"]
        put("unique_person", len({p["person"] for p in profiles}) == 1, ["person"])
        put("unique_gender", len({p["gender"] for p in profiles}) == 1, ["person"])
        ids = []
        for premise in inp.get("premises", []):
            value = premise.get("value")
            if premise["kind"] != "alternative_annotated_reading" or not isinstance(value, dict): continue
            gender = {"masculine": 0, "feminine": 1}.get(value.get("gender"))
            number = {"singular": 0, "dual": 1, "plural": 2}.get(value.get("number"))
            if any((p["person"], p["gender"], p["number"]) == (value.get("person"), gender, number) for p in profiles):
                ids.append(premise["reading_id"])
        if ids: put("retained_reading_ids", ids, ["person"], "MATCHED_SUPPLIED_ALTERNATIVES_TO_CONDITIONAL_PERSON_LAW")
    return obs


UNMEASURED_REASON = (
    "No independent matching judgment is exposed by these probe operations. "
    "A supplied annotation, a missing output field, or an interface scope note "
    "is not credited as an acquired Arabic interpretation."
)


def score_case(case, obs):
    checks = []
    set_fields = {"three_atom_cut_sets", "two_segment_cut_sets", "required_witness_ids", "retained_reading_ids", "three_atom_partitions"}
    for key, expected in case["expected"].items():
        if key not in obs:
            checks.append({"field": key, "status": "UNMEASURED", "expected": expected, "reason": UNMEASURED_REASON})
            continue
        actual = obs[key]["value"]
        left, right = actual, expected
        if key in set_fields and isinstance(left, list) and isinstance(right, list):
            left, right = sorted(left, key=canonical), sorted(right, key=canonical)
        passed = equal(left, right)
        false_accept = not passed and ((expected in ("UNKNOWN", "REJECTED") and actual == "LICENSED")
                                       or (expected is False and actual is True)
                                       or (expected is None and actual is not None))
        checks.append({"field": key, "status": "PASS" if passed else "FAIL", "expected": expected,
                       "actual": actual, "false_accept": false_accept,
                       "request_ids": obs[key]["request_ids"], "evidence_kind": obs[key]["evidence_kind"]})
    measured = [x for x in checks if x["status"] != "UNMEASURED"]
    failed = [x for x in measured if x["status"] == "FAIL"]
    status = "UNMEASURED" if not measured else "MEASURED" if len(measured) == len(checks) else "PARTIALLY_MEASURED"
    return {"case_id": case["id"], "group": case["group"], "case_status": status,
            "fully_passed": status == "MEASURED" and not failed,
            "measured_checks_pass": bool(measured) and not failed,
            "measured_check_count": len(measured), "failed_check_count": len(failed),
            "false_accept_count": sum(bool(c.get("false_accept")) for c in checks),
            "unmeasured_check_count": len(checks) - len(measured), "checks": checks}


def summarize(cases, errors, require_complete=False):
    measured = sum(x["measured_check_count"] for x in cases)
    failed = sum(x["failed_check_count"] for x in cases)
    missing = sum(x["unmeasured_check_count"] for x in cases)
    fully = sum(x["fully_passed"] for x in cases)
    complete = len(cases) == 40 and missing == 0
    # All 16 core cases must measure their declared indispensable judgments.
    # One easy check per group cannot make the gate pass.
    by_id = {c["case_id"]: c for c in cases}
    core_missing = {cid: sorted(fields - {x["field"] for x in by_id.get(cid, {}).get("checks", [])
                                         if x["status"] != "UNMEASURED"})
                    for cid, fields in CORE_REQUIRED_FIELDS.items()}
    core_missing = {cid: fields for cid, fields in core_missing.items() if fields}
    core_measured = not core_missing
    measured_ok = bool(measured) and core_measured and failed == 0 and not errors and len(cases) == 40
    return {"total_cases": 40, "fully_passed_cases": fully,
            "case_statuses": {s: sum(c["case_status"] == s for c in cases)
                              for s in ("MEASURED", "PARTIALLY_MEASURED", "UNMEASURED")},
            "measured_checks": measured, "failed_checks": failed, "unmeasured_checks": missing,
            "false_accept_count": sum(c["false_accept_count"] for c in cases),
            "required_core_judgments_missing": core_missing,
            "coverage_complete": complete, "strict_pass": measured_ok and complete,
            "measured_contract_gate_pass": measured_ok,
            "gate_pass": measured_ok and (complete or not require_complete),
            "gate_scope": "conditional_contract_checks_only",
            "acquisition_measured": False,
            "by_group": {g: {"cases": sum(c["group"] == g for c in cases),
                              "fully_passed": sum(c["group"] == g and c["fully_passed"] for c in cases),
                              "measured_checks": sum(c["measured_check_count"] for c in cases if c["group"] == g),
                              "failed_checks": sum(c["failed_check_count"] for c in cases if c["group"] == g),
                              "unmeasured_checks": sum(c["unmeasured_check_count"] for c in cases if c["group"] == g)}
                         for g in ("mechanical", "evidence_binding", "annotated_arabic")}}


def resolve_artifact(ref, result_path):
    require(type(ref.get("bytes")) is int and ref["bytes"] >= 0, "Artifact byte count type")
    require(isinstance(ref.get("sha256"), str) and len(ref["sha256"]) == 64, "Artifact hash type")
    path = Path(ref["path"])
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        # Historical reports preserve the original absolute checkout path.
        # A relocated repository can resolve only this fixed evidence subtree.
        marker = "evidence/unit_discovery/"
        original = ref["path"]
        require(marker in original, "Missing recorded artifact")
        path = ROOT / original[original.index(marker):]
    path = path.resolve()
    require(path.is_relative_to(ROOT) or path.is_relative_to(result_path.parent), "Artifact outside the review scope")
    observed = file_ref(path)
    require(observed["bytes"] == ref["bytes"] and observed["sha256"] == ref["sha256"], "Recorded artifact bytes differ: " + str(path))
    return path


def audit_saved_run(result_path, require_complete=False):
    """Revalidate and rescore immutable observed responses; never rerun the probe."""
    result_path = result_path.resolve()
    saved = parse(result_path.read_bytes())
    require(saved.get("schema") == "nabt.unit-discovery.independent-check.v1", "Saved result schema")
    require(saved.get("law_id") == LAW_ID and saved.get("scope") == SCOPE, "Saved law/scope")
    paths = {key: resolve_artifact(saved[key], result_path)
             for key in ("requests", "raw", "stdio", "pre_measurement_input_manifest",
                         "source_snapshot_before_execution", "snapshot")}
    for key, inventory_key in (("source_snapshot_before_execution", "source_snapshot_members"),
                               ("snapshot", "snapshot_members")):
        with tarfile.open(paths[key], "r:gz") as archive:
            members = archive.getmembers()
            require(all(m.isfile() for m in members) and len({m.name for m in members}) == len(members), "Archive member type/identity")
            observed = {m.name: sha256(archive.extractfile(m).read()).hexdigest() for m in members}
        require(observed == saved[inventory_key], "Closed archive inventory mismatch")
    input_manifest = parse(paths["pre_measurement_input_manifest"].read_bytes())
    require(input_manifest.get("execution_not_started") is True,
            "Original source snapshot was not declared before execution")
    require(equal(input_manifest["files"], saved["source_inputs"]) and
            equal(input_manifest["requests"], saved["requests"]) and
            equal(input_manifest["probe_build_identity"], saved["probe"]),
            "Pre-execution input manifest correlation")
    def inventory_refs(refs, members):
        expected = {}
        for ref in refs:
            matches = [name for name in members if ref["path"].endswith("/" + name)
                       or (name.startswith("external/") and Path(ref["path"]).name == name[9:])]
            require(len(matches) == 1 and matches[0] not in expected, "Archive/reference identity correlation")
            expected[matches[0]] = ref["sha256"]
        require(expected == members, "Archive inventory differs from retained file references")
    inventory_refs([*saved["source_inputs"], saved["requests"], saved["pre_measurement_input_manifest"]],
                   saved["source_snapshot_members"])
    inventory_refs([saved[k] for k in ("requests", "raw", "stdio", "pre_measurement_input_manifest")],
                   saved["snapshot_members"])
    material = load_material()
    require(saved["material"]["sha256"] == PINS["material_v2.json"] and
            saved["freeze"]["sha256"] == PINS["material_freeze_v2.json"], "Saved material identity")
    plan = make_plan(material)
    requests = parse(paths["requests"].read_bytes())
    require(equal(requests["requests"], plan.requests) and equal(requests["id_bijection"], plan.ids.rows)
            and equal(requests["requirement_ids"], REQUIREMENTS), "Input-only requests changed")
    raw = gzip.decompress(paths["raw"].read_bytes())
    require(sha256(raw).hexdigest() == saved["raw_verification"]["decoded_sha256"] and
            len(raw) == saved["raw_verification"]["decoded_bytes"], "Decoded raw digest/size")
    lines = raw.splitlines()
    rows = [parse(line) for line in lines]
    require(len(rows) == len(plan.requests) == saved["raw_verification"]["records"], "Raw request inventory count")
    require(all((canonical(row)).encode() == line for row, line in zip(rows, lines)), "Noncanonical saved raw record")
    stdio = parse(paths["stdio"].read_bytes())
    require(stdio["returncode"] == 0, "Saved probe process did not complete")
    stdin = "".join(canonical(row["request"]) + "\n" for row in plan.requests).encode()
    require(sha256(stdin).hexdigest() == stdio["stdin_sha256"], "Saved stdin/request correlation")
    stdout = base64.b64decode(stdio["stdout_base64"], validate=True).splitlines()
    require(len(stdout) == len(rows), "Saved stdout inventory")
    responses = {}
    for index, (row, request) in enumerate(zip(rows, plan.requests)):
        require(row["request_id"] == request["request_id"] and equal(row["request"], request["request"]), "Raw request identity")
        wire = base64.b64decode(row["response_raw_base64"], validate=True)
        require(wire == stdout[index] and equal(parse(wire), row["response"]), "Saved raw/stdio response mismatch")
        validate_response(request["request"], row["response"])
        responses[request["request_id"]] = row["response"]
    scored = [score_case(c, observations(c, plan, responses)) for c in material["cases"]]
    summary = summarize(scored, [], require_complete)
    return {"schema": "nabt.unit-discovery.saved-run-audit.v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "original_result": file_ref(result_path), "original_tool": saved["tool"],
            "validator_tool": file_ref(Path(__file__).resolve()),
            "probe_calls": 0, "material_unchanged": True, "requests_unchanged": True,
            "raw_records_verified": len(rows), "closed_archives_verified": 2,
            "source_snapshot_precedes_execution_in_original_record": True,
            "original_case_scores_unchanged": equal(scored, saved["cases"]),
            "original_summary_unchanged": equal(summary, saved["summary"]),
            "scope": "artifact_consistency_and_stronger_response_validation_not_external_source_authentication",
            "summary": summary, "cases": scored}


def replay_saved_run(result_path, output, require_complete=False):
    require(not output.exists(), "Output already exists: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = output.with_suffix(".checker.tar.gz")
    require(not snapshot.exists(), "Checker snapshot already exists")
    members = verified_archive(snapshot, [Path(__file__).resolve(), ROOT / "tests/test_unit_discovery_checker.py"])
    audited = audit_saved_run(result_path, require_complete)
    audited["checker_snapshot"] = file_ref(snapshot)
    audited["checker_snapshot_members"] = members
    with output.open("x", encoding="utf-8") as f:
        json.dump(audited, f, ensure_ascii=False, indent=2, sort_keys=True); f.write("\n")
    print(canonical({"output": str(output), "probe_calls": 0, "case_scores_unchanged": audited["original_case_scores_unchanged"], **audited["summary"]}))
    return 0 if audited["summary"]["gate_pass"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--probe", type=Path, help="Use this explicit executable without building")
    parser.add_argument("--replay", type=Path, help="Audit and rescore one saved result without invoking Lean")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    require(not (args.replay and args.probe), "--replay and --probe are separate modes")
    if args.replay:
        return replay_saved_run(args.replay, output, args.require_complete)
    raw_path = output.with_suffix(".raw.jsonl.gz")
    request_path = output.with_suffix(".requests.json")
    archive_path = output.with_suffix(".snapshot.tar.gz")
    source_archive_path = output.with_suffix(".sources.tar.gz")
    input_manifest_path = output.with_suffix(".inputs.json")
    stdio_path = output.with_suffix(".stdio.json")
    for p in (output, raw_path, request_path, archive_path, stdio_path, source_archive_path, input_manifest_path):
        require(not p.exists(), "Output already exists: " + str(p))
    output.parent.mkdir(parents=True, exist_ok=True)
    material = load_material()
    plan = make_plan(material)
    inputs = [Path(__file__).resolve(), ROOT / "tests/test_unit_discovery_checker.py",
              *[MATERIAL_DIR / name for name in PINS],
              *[MATERIAL_DIR / name for name in ("material_v1.json", "protocol_v1.md", "material_freeze_v1.json",
                                                "material_erratum_v1.json", "material_erratum_v1.md")],
              *[MATERIAL_DIR / "checker_review_v1" / name for name in ("mutations_before.json", "profile_mutations_before.json")],
              *sorted((ROOT / "formal").glob("*.lean")),
              *sorted((ROOT / "formal/Nabt").glob("*.lean")),
              ROOT / "formal/lean-toolchain"]
    inputs = [p for p in dict.fromkeys(inputs) if p.is_file()]
    before = [file_ref(p) for p in inputs]
    build = None
    if args.probe is None:
        command = [args.lake, "build", "unitDiscoveryProbe"]
        built = subprocess.run(command, cwd=ROOT / "formal", capture_output=True, timeout=300)
        build = {"command": command, "returncode": built.returncode,
                 "stdout": built.stdout.decode("utf-8", "strict"), "stderr": built.stderr.decode("utf-8", "strict")}
        require(built.returncode == 0, "Lean probe build failed: " + build["stderr"])
        probe = ROOT / "formal/.lake/build/bin/unitDiscoveryProbe"
    else:
        probe = args.probe.resolve()
    probe_ref = file_ref(probe)
    request_bytes = (canonical({"schema": "nabt.unit-discovery.requests.v1", "id_bijection": plan.ids.rows,
                                "requirement_ids": REQUIREMENTS, "requests": plan.requests}) + "\n").encode()
    with request_path.open("xb") as f: f.write(request_bytes)
    input_manifest = {"schema": "nabt.unit-discovery.pre-measurement-inputs.v1",
                      "created_at_utc": datetime.now(timezone.utc).isoformat(),
                      "files": before, "requests": file_ref(request_path), "probe_build_identity": probe_ref,
                      "probe_binary_archived": False,
                      "rebuild": [args.lake, "build", "unitDiscoveryProbe"],
                      "execution_not_started": True}
    with input_manifest_path.open("x", encoding="utf-8") as f:
        f.write(canonical(input_manifest) + "\n")
    # The replayable source/toolchain and input snapshot is physically closed
    # and verified BEFORE launching the executable. The large binary is pinned
    # by hash/size, not copied into versioned evidence or required by CI.
    source_members = verified_archive(source_archive_path, [*inputs, request_path, input_manifest_path])
    require(before == [file_ref(p) for p in inputs], "Source changed before probe launch")
    stdin = "".join(canonical(row["request"]) + "\n" for row in plan.requests).encode()
    run = subprocess.run([str(probe)], input=stdin, capture_output=True, timeout=180)
    stdio = {"returncode": run.returncode,
             "stdin_sha256": sha256(stdin).hexdigest(),
             "stdout_base64": base64.b64encode(run.stdout).decode("ascii"),
             "stderr_base64": base64.b64encode(run.stderr).decode("ascii")}
    with stdio_path.open("x", encoding="utf-8") as f: f.write(canonical(stdio) + "\n")
    lines = run.stdout.splitlines()
    responses, errors, raw_rows = {}, [], []
    if run.returncode != 0: errors.append({"kind": "PROBE_PROCESS", "returncode": run.returncode})
    if len(lines) != len(plan.requests): errors.append({"kind": "RESPONSE_INVENTORY", "expected": len(plan.requests), "actual": len(lines)})
    for index, request in enumerate(plan.requests):
        line = lines[index] if index < len(lines) else b""
        entry = {**request, "response_raw_base64": base64.b64encode(line).decode("ascii")}
        try:
            result = parse(line)
            validate_response(request["request"], result)
            responses[request["request_id"]] = result
            entry["response"] = result
        except Exception as exc:
            item = {"kind": "PROBE_RESPONSE", "request_id": request["request_id"], "error": str(exc)}
            errors.append(item); entry["error"] = item
        raw_rows.append(entry)
    raw = ("".join(canonical(row) + "\n" for row in raw_rows)).encode()
    with raw_path.open("xb") as target:
        with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as zipped: zipped.write(raw)
    reread = gzip.decompress(raw_path.read_bytes())
    require(reread == raw, "Raw journal byte mismatch after close")
    decoded = [parse(line) for line in reread.splitlines()]
    require([r["request_id"] for r in decoded] == [r["request_id"] for r in plan.requests], "Raw journal inventory")
    scored = []
    for case in material["cases"]:
        if not all(k in responses for k in plan.cases[case["id"]].values()):
            scored.append(score_case(case, {})); continue
        try:
            scored.append(score_case(case, observations(case, plan, responses)))
        except Exception as exc:
            errors.append({"kind": "ADAPTER", "case_id": case["id"], "error": str(exc)})
            scored.append(score_case(case, {}))
    after = [file_ref(p) for p in inputs]
    require(before == after and probe_ref == file_ref(probe), "Probe/source inputs changed during measurement")
    snapshot_members = verified_archive(archive_path, [request_path, raw_path, stdio_path, input_manifest_path])
    result = {"schema": "nabt.unit-discovery.independent-check.v1",
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "law_id": LAW_ID, "scope": SCOPE,
              "classification": "CONDITIONAL_CONTRACT_REVIEW_NOT_LANGUAGE_ACQUISITION",
              "material": file_ref(MATERIAL_DIR / "material_v2.json"),
              "freeze": file_ref(MATERIAL_DIR / "material_freeze_v2.json"),
              "tool": file_ref(Path(__file__).resolve()), "probe": probe_ref,
              "build": build, "source_inputs": before, "source_inputs_unchanged": True,
              "pre_measurement_input_manifest": file_ref(input_manifest_path),
              "source_snapshot_before_execution": file_ref(source_archive_path),
              "source_snapshot_members": source_members, "probe_binary_archived": False,
              "requests": file_ref(request_path), "raw": file_ref(raw_path),
              "stdio": file_ref(stdio_path),
              "raw_verification": {"complete_gzip_verified": True, "records": len(decoded),
                                   "decoded_bytes": len(raw), "decoded_sha256": sha256(raw).hexdigest(),
                                   "request_inventory_matched": True},
              "snapshot": file_ref(archive_path), "snapshot_members": snapshot_members,
              "probe_process": {"returncode": run.returncode, "stderr": run.stderr.decode("utf-8", "replace")},
              "errors": errors, "summary": summarize(scored, errors, args.require_complete), "cases": scored}
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True); f.write("\n")
    print(canonical({"output": str(output), **result["summary"], "errors": len(errors)}))
    return 0 if result["summary"]["gate_pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(canonical({"status": "INVALID_MEASUREMENT", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)

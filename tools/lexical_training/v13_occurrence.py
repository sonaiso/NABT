"""Read the original V13 modular weights as a bounded NTL observation."""
from hashlib import sha256
import json
import math
from pathlib import Path

from nabt.alphabet import ALPHABET_ID, cell_id, cell_parts

SCHEMA = "nabt.ntl.v13-occurrence.v1"
RESULT = "nabt.ntl.v13-occurrence-result.v1"
DIRECTORY = Path(__file__).resolve().parents[2] / "evidence/v13_occurrence_transfer_v1"
PARENT_SHA = "b26f9c8361c6da0c6ab9806777eddac52f0d0fa16fc38bbe77a31ef513ce2c43"
PROTOCOL_SHA = "38f3800a0130c362ea905a7339d2d4f8a054dda2fc91f29f0a5db8f71e5d3c5a"
MODEL_SHA = "d61de814c8b9f90c4ac4b62052d99aa066a28239bf5d615b118bf173f8309805"
BOUNDS = ("WASL", "WAQF", "FASL")
STATES = ("a", "u", "i", "S", "aa")
INPUTS = {"source116_id", "shadda", "tanwin", "boundary"}


def checked_json(name, expected):
    raw = (DIRECTORY / name).read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f"Changed V13 artifact: {name}")
    return json.loads(raw)


def _validate(item):
    if type(item) is not dict or set(item) != INPUTS:
        raise ValueError("Expected a source116_id, shadda, tanwin and boundary")
    if type(item["source116_id"]) is not int or not 0 <= item["source116_id"] < 116:
        raise ValueError("Expected a NABT A116 cell number")
    if type(item["shadda"]) is not bool or type(item["tanwin"]) is not bool or item["boundary"] not in BOUNDS:
        raise ValueError("Expected boolean flags and a known boundary")
    return cell_parts(item["source116_id"])


def _affine(net, layer, vector):
    return [b + sum(x*w for x, w in zip(vector, column, strict=True))
            for b, column in zip(net["b"+layer], zip(*net["W"+layer], strict=True), strict=True)]


def _onehot(i, size):
    return [float(j == i) for j in range(size)]


def observe(nets, item):
    carrier, vowel = cell_parts(item["source116_id"])
    inputs = [_onehot(item["shadda"], 2), _onehot(vowel, 3) + _onehot(item["tanwin"], 2)
              + _onehot(BOUNDS.index(item["boundary"]), 3)]
    hidden = [[math.tanh(v) for v in _affine(net, "1", x)] for net, x in zip(nets, inputs, strict=True)]
    onset, ending = [_affine(net, "2", h) for net, h in zip(nets, hidden, strict=True)]
    state = STATES[max(range(5), key=ending.__getitem__)]
    double, nun = onset[1] > onset[0], ending[6] > ending[5]
    specs = ([(carrier, "S")] if double else []) + [(carrier, state)] + ([("ن", "S")] if nun else [])
    units = []
    for letter, mark in specs:
        parents = ([cell_id(letter, 0), cell_id("ا", 3)] if mark == "aa"
                   else [cell_id(letter, STATES.index(mark))])
        units.append({"carrier": letter, "state": mark, "source116_parent_ids": parents})
    return {"double": double, "final_state": state, "inserted_nun": nun, "units": units}, hidden[0] + hidden[1]


def difference(left, right):
    return [abs(a-b) for a, b in zip(left, right, strict=True)]


def changed(checkpoint, features):
    return checkpoint["bias"] + sum(w*x for w, x in zip(checkpoint["weights"], features, strict=True)) >= 0


def run(lesson):
    if type(lesson) is not dict or set(lesson) not in ({"schema", "before"}, {"schema", "before", "after"}) or lesson["schema"] != SCHEMA:
        raise ValueError("Expected one V13 occurrence and an optional single-field contrast")
    items = [lesson["before"]] + ([lesson["after"]] if "after" in lesson else [])
    cells = [_validate(item) for item in items]
    result = {"schema": RESULT, "alphabet_id": ALPHABET_ID, "authority": "NONE",
              "scope": "SYNTHETIC_V13_OCCURRENCE", "execution_measured": False}
    if any(carrier == "ا" or vowel == 3 for carrier, vowel in cells):
        return dict(result, status="DEFER_OUTSIDE_PROBE")
    if len(items) == 2:
        changes = [k for k in INPUTS if items[0][k] != items[1][k]]
        if cells[0][0] != cells[1][0] or len(changes) != 1:
            raise ValueError("Expected one changed field on the same carrier")
        result["changed_field"] = "vowel" if changes[0] == "source116_id" else changes[0]
    try:
        parent = checked_json("parent.json", PARENT_SHA)
    except (OSError, ValueError) as exc:
        return dict(result, status="MODEL_UNAVAILABLE", reason=type(exc).__name__)
    before, left = observe(parent["nets"], items[0])
    result.update(status="PROPOSED", before=before, execution_measured=True,
                  parent_sha256=PARENT_SHA, original_npz_sha256=parent["parent_npz_sha256"])
    if len(items) == 2:
        after, right = observe(parent["nets"], items[1])
        result["after"] = after
        try:
            checked_json("protocol.json", PROTOCOL_SHA)
            head = checked_json("checkpoint.json", MODEL_SHA)
        except (OSError, ValueError) as exc:
            return dict(result, status="READOUT_UNAVAILABLE", reason=type(exc).__name__)
        result.update(predicted_units_changed=changed(head, difference(left, right)),
                      checkpoint_sha256=MODEL_SHA, protocol_sha256=PROTOCOL_SHA)
    return result

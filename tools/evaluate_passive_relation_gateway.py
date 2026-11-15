"""Evaluate the checked text.read route on the reserved passive-relation corpus.

From the repository root, build the native text.read owners and then run:
PYTHONPATH=src:. python -m tools.evaluate_passive_relation_gateway --output report.json
"""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "evidence/passive_relation_transfer_v1/holdout.json"
FIELDS = ("relation", "verb_span", "patient_span", "cue_span")
CARD_FIELDS = (*FIELDS, "event_family", "event_sense_id", "patient_key", "operator_reading_conditional")
# Crosswalk from the authored reference meanings to the versioned identifiers.
REFERENCE_SENSE = {
    "فتح": "nabt.written-passive-frames.v1:open",
    "غلق": "nabt.written-passive-frames.v1:close",
    "كسر": "nabt.written-passive-frames.v1:break",
}
REFERENCE_PATIENT = {
    "open_door": "باب", "h_pair1": "باب", "h_pair2": "قفل", "h_pair3": "زجاج", "h_pair4": "قلم",
}


def projection(record, fields):
    return {key: record[key] for key in fields}


def evaluate_case(case):
    # Preserve the request independently of the worker and its complete receipt.
    request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": case["text"]}}
    receipt = gateway.run(request)
    replay = gateway.accept_output(receipt, expected_request=request)
    result = {"id": case["id"], "group": case["group"], "reference_relation": case["relation"],
              "execution_status": receipt["status"], "verification": replay["status"],
              "neural_exact": None, "gateway_exact": None}
    if receipt["status"] != "EXECUTED" or not replay["valid"]:
        return result
    view = receipt["execution"]["owner_result"]
    source_hash = sha256(case["text"].encode()).hexdigest()
    transfer = view["passive_relation_transfer"]
    if view["source"]["sha256"] != source_hash or transfer["source_sha256"] != source_hash:
        raise ValueError("Evaluation result refers to a different source")
    proposal = transfer["proposal"]
    result.update(comparison=transfer["comparison"], proposal_status=proposal["status"],
                  model_sha256=proposal["model_sha256"])
    if proposal["status"] in {"PROPOSED", "OUTSIDE"}:
        result["proposal"] = projection(proposal, FIELDS)
        result["neural_exact"] = result["proposal"] == projection(case, FIELDS)
    cards = [c["evidence"] for c in view["cards"] if c["scope"] == "source_event_relation"]
    for card in cards:
        if card["source_sha256"] != source_hash:
            raise ValueError("Event evidence refers to a different source")
    result["readings"] = [projection(c, CARD_FIELDS) for c in cards]
    result["world_open"] = (view["world_truth_established"] is False and
                            all(c["world_truth_established"] is False for c in cards))
    if transfer["comparison"] == "SOURCE_CHECK_UNAVAILABLE":
        return result
    if case["relation"] == "OUTSIDE":
        result["gateway_exact"] = not cards and result["world_open"]
    else:
        # Multiple lexical readings may license the same source-relative proposition.
        cue = case["cue_span"]
        conditional = cue is not None and case["text"].encode()[cue[0]:cue[1]].decode() == "لم"
        result["gateway_exact"] = bool(cards) and result["world_open"] and all(
            projection(c, FIELDS) == projection(case, FIELDS) and c["event_family"] == case["root"]
            and c["event_sense_id"] == REFERENCE_SENSE[case["root"]]
            and c["patient_key"] == REFERENCE_PATIENT[case["pair_id"]]
            and c["operator_reading_conditional"] == conditional for c in cards)
    return result


def counts(rows, key):
    return {"correct": sum(row[key] is True for row in rows),
            "assessed": sum(row[key] is not None for row in rows), "total": len(rows)}


def pair_results(cases, observations):
    cases_by_id = {c["id"]: c for c in cases}
    pairs = defaultdict(dict)
    for row in observations:
        case = cases_by_id[row["id"]]
        if "pair_id" in case:
            pairs[case["pair_id"]][case["relation"]] = row
    results = []
    for pair, readings in pairs.items():
        left, right = readings["ASSERT_PASSIVE"], readings["DENY_PASSIVE"]
        # Exact UTF-8 ranges are evaluated against each original source first.
        # Offsets need not match when adding lam changes the source length.
        stable = None
        if left["gateway_exact"] is not None and right["gateway_exact"] is not None:
            left_keys = {(c["event_sense_id"], c["patient_key"]) for c in left["readings"]}
            right_keys = {(c["event_sense_id"], c["patient_key"]) for c in right["readings"]}
            stable = left["gateway_exact"] and right["gateway_exact"] and left_keys == right_keys
        neural = None
        if left["neural_exact"] is not None and right["neural_exact"] is not None:
            neural = left["neural_exact"] and right["neural_exact"]
        results.append({"pair_id": pair, "group": left["group"], "neural_exact": neural,
                        "gateway_exact_with_same_sense_and_patient": stable})
    return results


def evaluate(workers):
    raw = GOLD.read_bytes()
    reference = json.loads(raw)
    cases = reference["cases"]
    if workers == 1:
        observations = [evaluate_case(case) for case in cases]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            observations = list(executor.map(evaluate_case, cases))
    pairs = pair_results(cases, observations)
    groups = {}
    for group in ("heldout", "control", "anchor"):
        rows = [row for row in observations if row["group"] == group]
        pairs_in_group = [pair for pair in pairs if pair["group"] == group]
        groups[group] = {
            "verified_receipts": sum(row["verification"] == "VERIFIED_IO_REPLAY" for row in rows),
            "neural_relation_and_spans": counts(rows, "neural_exact"),
            "checked_reader_relation_sense_patient_and_spans": counts(rows, "gateway_exact"),
            "conditional_operator_cases": sum(any(c["operator_reading_conditional"] for c in row.get("readings", []))
                                              for row in rows),
            "checked_pairs": counts(pairs_in_group, "gateway_exact_with_same_sense_and_patient")}
    return {"schema": "nabt.passive-relation-public-evaluation.v1", "route": "text.read",
            "holdout_sha256": sha256(raw).hexdigest(), "reserved_roots": reference["held_out_roots"],
            "scope": "Source-relative authored reading and byte spans within the narrow contract. "
                     "A conditioned reading counts only in its declared sense; no uniqueness or external fact follows. "
                     "For controls, gateway_exact means no passive-event card was emitted.",
            "groups": groups, "pairs": pairs, "observations": observations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.workers)
    # Save only after the last independent replay: local snapshots can include evidence.
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["groups"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Replay the fixed transfer challenge. Report rule, neural, ablated and public outputs separately."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import classical_roles, gateway
from tools.lexical_training import classical_attention as net

CHALLENGE = net.ROOT / "evidence/grounded_attention_v1/challenge.json"
CHALLENGE_SHA = "60f79c6333cda62b361b56e02eaeff98210bd0e7e8e2762d7e9ec30723fe5886"


def expected(row):
    terms, _, _ = net.encode(row["text"])
    if row["subject"] is None:
        return None
    spans = {t["surface"]: t["utf8_span"] for t in terms}
    return [spans[row["subject"]], spans[row["object"]], row["force"],
            terms[0]["utf8_span"] if row["force"] == "ask" else None]


def neural_result(observation):
    if observation["status"] != "PROPOSED":
        return None
    h = observation["heads"]
    return [h["subject"]["span"], h["object"]["span"], observation["force_proposal"], h["question_cue"]["span"]]


def checked_result(graph):
    if graph is None:
        return None
    r = graph["reading"]
    return [r["subject"]["term"]["utf8_span"], r["object"]["term"]["utf8_span"], r["force"],
            r["cue"]["utf8_span"] if r["cue"] else None]


def positional(text):
    frame = classical_roles.source_frame(text)
    if frame is None:
        return None
    ts, ask = frame
    return [ts[-2]["utf8_span"], ts[-1]["utf8_span"], "ask" if ask else "assert", ts[0]["utf8_span"] if ask else None]


def public_case(case):
    request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": case["text"]}}
    receipt = gateway.run(request)
    replay = gateway.accept_output(receipt, expected_request=request)
    row = {"id": case["id"], "execution": receipt["status"], "verified": replay["valid"],
           "match": None, "model_match": None}
    if not replay["valid"] or receipt["status"] != "EXECUTED":
        return row
    view = receipt["execution"]["owner_result"]
    bridge = view["classical_role_attention"]
    gold = expected(case)
    cards = [c for c in view["cards"] if c["scope"] == "classical_role_binding"]
    row.update(status=bridge["status"], match=(bridge["status"] in {"SOURCE_BOUND_READING", "NO_SCOPED_BINDING"}
               and len(cards) == int(gold is not None) and checked_result(bridge["graph"]) == gold),
               model_match=(neural_result(bridge["proposal"]) == gold
                            if bridge["proposal"]["status"] in {"PROPOSED", "DEFER"} else None),
               customary_use_established=bridge["customary_use_established"],
               world_truth_established=view["world_truth_established"])
    if bridge["graph"] is not None:
        # These two annotated event frames are independent of the scored pointers.
        r = bridge["graph"]["reading"]
        expected_sense = {"help":"help", "thank":"thank"}.get(case["id"].rstrip("1234"))
        row.update(reading=checked_result(bridge["graph"]), sense=r["sense"],
                   semantic_roles=[e["value"] for e in bridge["graph"]["edges"] if e["type"] == "semantic_role"],
                   usage_handoff=bridge["usage_handoff"]["status"])
        row["match"] = row["match"] and expected_sense == r["sense"]
    return row


def coverage():
    from tools.grammar_catalog.awamil import build_awamil_catalog
    from tools.grammar_catalog.catalog import build_catalog

    catalog = build_catalog()
    factors = [c for c in build_awamil_catalog()["cards"] if c["collection"] == "jurjani"]
    witnesses = classical_roles.inventory()["witnesses"]
    books = {}
    for name in ("sibawayhi", "qatr"):
        passages = {p["passage_id"] for p in catalog["passages"] if p["source_id"] == name}
        rules = [r["rule_key"] for r in catalog["rules"] if passages.intersection(r["source_passage_ids"])]
        books[name] = {"retrieval_passages": len(passages), "catalog_rules_linked": len(rules),
                       "witnesses_used_in_this_bridge": [k for k,v in witnesses.items()
                                                         if v["path"].endswith("/" + name + ".txt")]}
    return {"basis": "Existing catalogue entries; counts of passages are not counts of laws or mastered skills.",
            "books": books, "factors_in_this_bridge": [c["id"] for c in factors if c["id"] in witnesses],
            "other_factors_in_existing_catalog": [c["id"] for c in factors if c["id"] not in witnesses],
            "full_book_coverage_established": False}


def evaluate(public=False, workers=1):
    raw = CHALLENGE.read_bytes()
    if sha256(raw).hexdigest() != CHALLENGE_SHA:
        raise ValueError("Frozen challenge has changed")
    cases = json.loads(raw)["cases"]
    weights = (net.ROOT / net.MODEL_PATH).read_bytes()
    if sha256(weights).hexdigest() != net.MODEL_SHA256:
        raise ValueError("Unverified checkpoint")
    model = json.loads(weights)
    rows = []
    for c in cases:
        text = c["text"]
        gold = expected(c)
        predictions = {"position": positional(text), "law": checked_result(classical_roles.analyze(text)),
                       "attention": neural_result(net.attend(text, model))}
        predictions["without_nominal_marks"] = neural_result(net.attend(text, model, hide_nominal_marks=True))
        for h in net.HEADS:
            predictions["mask_" + h] = neural_result(net.attend(text, model, masked_heads=(h,)))
        rows.append({"id": c["id"], "group": "controls" if gold is None else "heldout",
                     "gold": gold, "predictions": predictions})
    groups = {}
    for group in ("heldout","controls"):
        selected = [r for r in rows if r["group"] == group]
        groups[group] = {"n":len(selected), "correct":{k:sum(r["predictions"][k] == r["gold"] for r in selected)
                          for k in selected[0]["predictions"]}}
    report = {"schema":"nabt.classical-attention.evaluation.v1.1",
              "first_test_ref":"evidence/grounded_attention_v1/FIRST_TEST.json", "holdout_sha256":CHALLENGE_SHA,
              "model_sha256":net.MODEL_SHA256, "groups":groups, "cases":rows, "coverage":coverage(),
              "scope":"Authored held-out stems/senses for neural fit. Rule lexicon includes the tested forms. "
                      "A masked head is a uniform pointer with no unique winner; comparisons are exact joint "
                      "role spans, force and cue or abstention. No independent field sample or usage proof."}
    if public:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            measurements = list(executor.map(public_case,cases))
        return {"schema":"nabt.classical-attention.gateway-evaluation.v1", "route":"text.read",
                "first_test_ref":"evidence/grounded_attention_v1/FIRST_TEST.json",
                "holdout_sha256":CHALLENGE_SHA, "model_sha256":net.MODEL_SHA256, "gateway":measurements}
    return report


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gateway",action="store_true")
    p.add_argument("--workers",type=int,choices=range(1,5),default=1)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=evaluate(args.gateway,args.workers)
    with args.output.open("x",encoding="utf-8") as target:
        json.dump(result,target,ensure_ascii=False,indent=2); target.write("\n")
    print(json.dumps(result.get("groups", result.get("gateway")),ensure_ascii=False))

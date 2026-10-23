"""Read-only, local reproductions of the five reported NABT review defects."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nabt.arabic_reader import LANGUAGE_ID
from nabt.semantics import SemanticKernel
from arabic_syntax_evaluation import FIRST_SNAPSHOT, regression_gate
from arabic_syntax_evaluation_helpers.oracle_helpers import independent_certificate
from arabic_syntax_evaluation_helpers.runner import run

DATA = Path.cwd() / "evidence/arabic_syntax/independent"
REFERENCE = json.loads((DATA / "first_results.json").read_text())
MANUAL = {r["source_text_sha256"]: r["expected"] for r in
          json.loads((DATA / "manual_oracle.json").read_text())["records"]}
SOURCES = {r["id"]: {e["source_id"]: e["text"] for e in r["events"] if e["op"] == "add"}
           for r in json.loads((DATA / "scope_episodes.json").read_text())["cases"]}
CASE = next(r for r in REFERENCE["episodes"] if r["id"] == "s07")
ANSWER = next(e["result"] for e in CASE["events"] if e["op"] == "query")
CERT = ANSWER["proofs"]["query"]


def replay(cert, active=None):
    try:
        return {"accepted": independent_certificate(cert, active or SOURCES["s07"], "eval_s07", MANUAL)}
    except Exception as e:
        return {"accepted": False, "error_type": type(e).__name__, "message": str(e)}


def review_runner(transform, scope):
    original = SemanticKernel.query
    def wrapped(self, *args, **kwargs):
        out = original(self, *args, **kwargs).as_dict()
        if kwargs.get("scope") == scope:
            transform(out)
        return SimpleNamespace(as_dict=lambda: out)
    with patch.object(SemanticKernel, "query", wrapped):
        result = run(DATA, "arabic")
    case = next(r for r in result["episodes"] if "eval_" + r["id"] == scope)
    gate = regression_gate(result, snapshot=FIRST_SNAPSHOT, reference=REFERENCE)
    return {"independent_certificates_pass": case["independent_certificates_pass"],
            "admitted_claims_licensed": case["admitted_claims_licensed"],
            "complete_episode": case["complete_episode"],
            "errors": [e.get("error_type") for e in case["events"] if "error_type" in e],
            "old_gate_passed": gate["passed"],
            "same_summary_as_published": result["summary"] == REFERENCE["summary"]}


observed = {"baseline_commit": "b6ba0c6d960a3627d2841955fa8aeb369d54794c",
            "valid_frozen_certificate": replay(deepcopy(CERT))}
k = SemanticKernel(language_id=LANGUAGE_ID)
observed["relation_source_accepted"] = k.add_source("علاقة يراجع. سالم يراجع تقرير.", source_id="relation").accepted
try:
    observed["relation_query"] = k.query("هل سالم يراجع تقرير؟").as_dict()["status"]
except Exception as e:
    observed["relation_query"] = {"error_type": type(e).__name__, "code": getattr(e, "code", None)}

bad = deepcopy(CERT)
span = bad["steps"][-1]["clause"]["span"]
raw = SOURCES["s07"]["r"].encode()
span.update(start=0, end=2, span_sha256=sha256(raw[:2]).hexdigest())
bad["steps"][-1]["clause"]["component_spans"] = []
observed["rule_reduced_to_one_character"] = replay(bad)
for name, change in [("reversed", lambda x: list(reversed(x))),
                     ("missing", lambda x: x[1:]),
                     ("duplicated", lambda x: [x[0], *x])]:
    bad = deepcopy(CERT)
    bad["steps"][-1]["clause"]["component_spans"] = change(bad["steps"][-1]["clause"]["component_spans"])
    observed["rule_components_" + name] = replay(bad)
bad = deepcopy(CERT)
bad["steps"][-1]["binding"] = {"ريان": "ريان"}
observed["constant_binding_extra_key"] = replay(bad)
bad = deepcopy(CERT)
bad["steps"][-1]["premises"] = [False]
observed["bool_premise_index"] = replay(bad)

# Production verification uses live admitted program identities, so a rejected
# snapshot is not confused with the clause/binding boundary under investigation.
k = SemanticKernel(language_id=LANGUAGE_ID)
active = dict(SOURCES["s07"], b=SOURCES["s02"]["a"])
for sid, raw in active.items():
    assert k.add_source(raw, source_id=sid, scope="eval_s07").accepted
live = k.query("هل ريان هو شاهد؟", scope="eval_s07").as_dict()["proofs"]["query"]
assert k.verify_certificate(live)["accepted"]
fact = k.query("هل أثير هو حاضر؟", scope="eval_s07").as_dict()["proofs"]["query"]
retargeted = deepcopy(live)
retargeted["steps"][0] = deepcopy(fact["steps"][0])
retargeted["steps"][-1]["binding"] = {"ريان": "أثير"}
retargeted["steps"][-1]["atom"]["args"] = ["أثير"]
retargeted["query"]["args"] = ["أثير"]
observed["retargeted_constant_independent"] = replay(retargeted, active)
observed["retargeted_constant_production"] = k.verify_certificate(retargeted)
bad = deepcopy(live)
span = bad["steps"][-1]["clause"]["span"]
span.update(start=0, end=2, span_sha256=sha256(active["r"].encode()[:2]).hexdigest())
bad["steps"][-1]["clause"]["component_spans"] = []
observed["rule_one_character_production"] = k.verify_certificate(bad)
premise = deepcopy(live)
premise["steps"] = premise["steps"][:1]
premise["conclusion"] = 0
premise["query"] = deepcopy(premise["steps"][0]["atom"])
observed["premise_certificate_production"] = k.verify_certificate(premise)

observed["answer_without_proofs"] = review_runner(lambda out: out.update(proofs={}), "eval_s07")
observed["answer_null_proof"] = review_runner(lambda out: out.update(proofs={"query": None}), "eval_s07")
def premise_in_answer(out):
    cert = out["proofs"]["query"]
    cert["steps"] = cert["steps"][:1]
    cert["conclusion"] = 0
    cert["query"] = deepcopy(cert["steps"][0]["atom"])
observed["answer_contains_other_valid_query"] = review_runner(premise_in_answer, "eval_s07")
def signed_in_supported(out):
    out["proofs"]["query"]["proof_kind"] = "signed"
observed["supported_answer_with_signed_proof"] = review_runner(signed_in_supported, "eval_s07")
def malformed_out_of_scope(out):
    out["proofs"] = {"query": {"scope": "eval_s03", "world_truth": "NOT_ESTABLISHED"}}
observed["malformed_certificate_in_already_uncovered_case"] = review_runner(malformed_out_of_scope, "eval_s03")

print(json.dumps(observed, ensure_ascii=False, indent=2))

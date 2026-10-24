"""Versioned rational inquiry over explicit, bounded source snapshots.

This layer executes detectors; it never accepts caller-supplied verdicts.
Snapshot correspondence, conditional entailment, and world correspondence
have different authorities. Provenance is a checked *declared* graph, not an
authentication service. Procedural review is not a claim of human cognition.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from .errors import NabtError, natural, resource_limit

VERSION = "nabt.rational-inquiry.v1"
MAX_DOCUMENT_BYTES = 1048576
MAX_REPORT_BYTES = 2097152
MAX_ITEMS = 64
MAX_CHECKS = 4096
GATE_FLAGS = ("formed", "reviewed", "provenance", "scopeCovered", "supported",
              "counterevidence", "requiresWorldBridge", "worldBridge", "exhausted")
_SCOPE = {"domain", "referent", "time", "unit"}


def _fail(message: str, code: str = "INVALID_INQUIRY") -> None:
    raise NabtError(code, message)


def _object(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        _fail(f"{where} requires exactly: {', '.join(sorted(fields))}")
    return value


def _text(value, where, maximum=4096):
    if type(value) is not str or not value.strip():
        _fail(f"{where} requires nonempty text")
    if len(value) > maximum:
        raise resource_limit("Inquiry text exceeds its budget", field=where)
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise NabtError("INVALID_UNICODE", f"Invalid Unicode in {where}") from exc
    if size > maximum:
        raise resource_limit("Inquiry text exceeds its byte budget", field=where)
    return value


def _items(value, where):
    if type(value) is not list:
        _fail(f"{where} requires an array")
    if len(value) > MAX_ITEMS:
        raise resource_limit("Inquiry collection exceeds its budget", field=where)
    return value


def _scope(value):
    _object(value, _SCOPE, "scope")
    for field in _SCOPE:
        _text(value[field], f"scope.{field}", 256)


def _ref(value, where):
    _object(value, {"source_id", "revision"}, where)
    _text(value["source_id"], where + ".source_id", 128)
    natural(value["revision"], where + ".revision", maximum=1000000000)
    return value["source_id"], value["revision"]


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value):
    return sha256(_bytes(value)).hexdigest()


def _bounded(value, maximum=MAX_DOCUMENT_BYTES):
    """Bound inert input before copying, hashing, parsing, or graph traversal."""
    stack, nodes, size = [(value, 0)], 0, 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if depth > 16 or nodes > 20000:
            raise resource_limit("Inquiry nesting or node budget exhausted")
        if type(item) is dict:
            if len(item) > 128:
                raise resource_limit("Inquiry object is too wide")
            for key, child in item.items():
                if type(key) is not str:
                    _fail("JSON object keys must be strings")
                stack.extend(((key, depth + 1), (child, depth + 1)))
        elif type(item) is list:
            if len(item) > 20000:
                raise resource_limit("Inquiry array is too large")
            stack.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            if len(item) > maximum:
                raise resource_limit("Inquiry text exceeds document budget")
            try:
                size += len(item.encode("utf-8", errors="strict"))
            except UnicodeError as exc:
                raise NabtError("INVALID_UNICODE", "Invalid inquiry Unicode") from exc
        elif type(item) is int:
            if item.bit_length() > 64:
                _fail("Inquiry integers are bounded")
            size += 24
        elif type(item) is bool or item is None:
            size += 5
        else:
            _fail("Inquiry data must be inert JSON; floating point is not installed")
        if size > maximum:
            raise resource_limit("Inquiry document exceeds byte budget")
    if len(_bytes(value)) > maximum:
        raise resource_limit("Inquiry encoded document exceeds byte budget")


def decide_gate(checks: dict) -> dict:
    """Conditional authorization law; flags are not evidence by themselves.

    Mirrored by Nabt.RationalInquiry.assess. The public inquiry API derives
    these flags by executing its installed protocols, never from a report.
    """
    _object(checks, {*GATE_FLAGS, "requestedRank", "evidenceRank"}, "gate")
    for name in GATE_FLAGS:
        if type(checks[name]) is not bool:
            _fail("Gate flags require actual booleans")
    requested = natural(checks["requestedRank"], "requestedRank", maximum=3)
    evidence = natural(checks["evidenceRank"], "evidenceRank", maximum=3)
    if checks["exhausted"]:
        verdict = "RESOURCE_LIMIT"
    elif not checks["formed"]:
        verdict = "UNFORMED"
    elif checks["requiresWorldBridge"] and not checks["worldBridge"]:
        verdict = "DEFER"
    elif not checks["provenance"] or not checks["scopeCovered"]:
        verdict = "DEFER"
    elif checks["counterevidence"]:
        verdict = "CONFLICT" if checks["supported"] else "REFUTED"
    elif not checks["reviewed"]:
        verdict = "UNREVIEWED"
    elif (checks["provenance"] and checks["scopeCovered"] and checks["supported"]
          and (not checks["requiresWorldBridge"] or checks["worldBridge"])
          and requested <= evidence):
        verdict = "LICENSED"
    else:
        verdict = "DEFER"
    return {"verdict": verdict, "authorized_rank": requested if verdict == "LICENSED" else 0}


def _validate(plan, sources):
    _bounded(plan)
    _bounded(sources)
    _object(plan, {"version", "claim", "formation", "review", "requested_rank"}, "plan")
    if plan["version"] != VERSION:
        _fail("Uninstalled inquiry version")
    natural(plan["requested_rank"], "requested_rank", maximum=3)
    if plan["requested_rank"] == 0:
        _fail("An inquiry requests rank 1, 2, or 3")
    claim = _object(plan["claim"], {"claim_id", "kind", "candidate", "scope", "origin_sources"}, "claim")
    _text(claim["claim_id"], "claim_id", 128)
    _text(claim["candidate"], "candidate", 16384)
    if claim["kind"] not in ("TEXT_CORRESPONDENCE", "SOURCE_ENTAILMENT", "WORLD_CORRESPONDENCE"):
        _fail("Uninstalled claim kind")
    _scope(claim["scope"])
    for ref in _items(claim["origin_sources"], "origin_sources"):
        _ref(ref, "origin")
    formation = _object(plan["formation"], {"purpose", "interpretation", "inference", "prior"}, "formation")
    for name in ("purpose", "interpretation", "inference"):
        _text(formation[name], "formation." + name)
    for prior in _items(formation["prior"], "prior"):
        _object(prior, {"source_id", "revision", "role", "relevance"}, "prior")
        _ref({k: prior[k] for k in ("source_id", "revision")}, "prior")
        if prior["role"] not in ("DEFINITION", "KNOWLEDGE", "HYPOTHESIS"):
            _fail("Uninstalled prior-information role")
        _text(prior["relevance"], "prior relevance")
    review = _object(plan["review"], {"depth", "context", "alternatives", "conditions", "limitations", "unresolved"}, "review")
    if review["depth"] not in ("SURFACE", "DEEP", "ENLIGHTENED"):
        _fail("Uninstalled review profile")
    for name in ("context", "conditions"):
        for item in _items(review[name], name):
            _object(item, {"source_id", "revision", "expected"}, name)
            _ref({k: item[k] for k in ("source_id", "revision")}, name)
            _text(item["expected"], name + ".expected", 16384)
    alternatives = set()
    for item in _items(review["alternatives"], "alternatives"):
        _object(item, {"alternative_id", "candidate"}, "alternative")
        _text(item["alternative_id"], "alternative_id", 128)
        _text(item["candidate"], "alternative candidate", 16384)
        if item["alternative_id"] in alternatives or item["candidate"] == claim["candidate"]:
            _fail("Alternatives require unique identities and a distinct candidate")
        alternatives.add(item["alternative_id"])
    for name in ("limitations", "unresolved"):
        for item in _items(review[name], name):
            _text(item, name)
    index = {}
    for source in _items(sources, "sources"):
        _object(source, {"source_id", "revision", "scope", "content", "origin", "parents", "role", "active"}, "source")
        key = _ref({k: source[k] for k in ("source_id", "revision")}, "source")
        _scope(source["scope"])
        _text(source["content"], "source content", 65536)
        _text(source["origin"], "source origin", 256)
        if source["role"] not in ("MATERIAL", "REFERENCE", "CONTEXT") or type(source["active"]) is not bool:
            _fail("Source role/active is invalid")
        parents = [_ref(ref, "parent") for ref in _items(source["parents"], "parents")]
        if len(set(parents)) != len(parents):
            _fail("Duplicate provenance parent")
        if source["source_id"] in index:
            _fail("Source identifiers are unique in the live inventory")
        index[key[0]] = source
    return index


def audit_inquiry(plan: dict, sources: list[dict], *, max_checks: int = 128) -> dict:
    """Execute all relevant live checks within a declared finite inventory.

    No lookup, network access, code evaluation, or world observer is installed.
    Origin/parent declarations are compared and replayed, not authenticated.
    Missing or revoked premises remain distinct from negative evidence.
    """
    natural(max_checks, "max_checks", maximum=MAX_CHECKS)
    _validate(plan, sources)
    plan, sources = deepcopy(plan), deepcopy(sources)
    index = {source["source_id"]: source for source in sources}
    claim, formation, review = plan["claim"], plan["formation"], plan["review"]
    residuals, checks, used = [], [], {}
    cache, visiting = {}, set()

    def residual(code, detail):
        entry = {"code": code, "detail": detail}
        if entry not in residuals:
            residuals.append(entry)

    def resolve(ref):
        source = index.get(ref["source_id"])
        return source if source and source["revision"] == ref["revision"] and source["active"] else None

    def lineage(source):
        sid = source["source_id"]
        if sid in visiting:
            _fail("Cyclic declared provenance", "CYCLIC_PROVENANCE")
        if sid in cache:
            return cache[sid]
        visiting.add(sid)
        roots, valid = {source["origin"]}, source["active"]
        for ref in source["parents"]:
            parent = index.get(ref["source_id"])
            if parent is None or parent["revision"] != ref["revision"]:
                valid = False
                continue
            parent_roots, parent_valid = lineage(parent)
            roots.update(parent_roots)
            valid = valid and parent_valid
        visiting.remove(sid)
        cache[sid] = (roots, valid)
        return roots, valid

    # Validate the whole declared graph, including unoffered and inactive rows.
    for source in sources:
        lineage(source)

    def use(source):
        used[source["source_id"]] = {
            "source_id": source["source_id"], "revision": source["revision"],
            "content_sha256": sha256(source["content"].encode("utf-8")).hexdigest(),
            "record_digest": _digest(source), "scope": source["scope"],
            "declared_origins": sorted(lineage(source)[0]),
        }

    formed = bool(claim["origin_sources"])
    candidate_roots = set()
    for ref in claim["origin_sources"]:
        source = resolve(ref)
        if source is None or not lineage(source)[1]:
            formed = False
            residual("FORMATION_SOURCE_UNAVAILABLE", ref)
        else:
            use(source)
            candidate_roots.update(lineage(source)[0])
    for prior in formation["prior"]:
        source = resolve(prior)
        if source is None or not lineage(source)[1]:
            formed = False
            residual("PRIOR_SOURCE_UNAVAILABLE", {"source_id": prior["source_id"], "revision": prior["revision"]})
        else:
            use(source)
            candidate_roots.update(lineage(source)[0])

    references = sorted((s for s in sources if s["role"] == "REFERENCE" and s["active"]
                         and s["scope"] == claim["scope"]), key=lambda s: s["source_id"])
    usable = []
    for source in references:
        if lineage(source)[1]:
            usable.append(source)
        else:
            residual("REFERENCE_DEPENDENCY_UNAVAILABLE", source["source_id"])
    exhausted, review_ok = False, True

    def room():
        nonlocal exhausted
        if len(checks) >= max_checks:
            exhausted = True
            return False
        return True

    def exact(source, expected, purpose, target):
        if not room():
            return None
        use(source)
        passed = source["content"] == expected
        checks.append({"protocol": "exact-text-v1", "purpose": purpose, "target": target,
                       "source_id": source["source_id"], "revision": source["revision"],
                       "passed": passed, "expected_sha256": sha256(expected.encode("utf-8")).hexdigest(),
                       "actual_sha256": sha256(source["content"].encode("utf-8")).hexdigest(),
                       "detector": "Unequal exact UTF-8 text in the bound snapshot"})
        return passed

    supported, counterevidence, evidence_rank = False, False, 0
    alternative_supported = False
    semantic_incomplete = False
    if claim["kind"] == "SOURCE_ENTAILMENT":
        from .semantics import SemanticBudget, SemanticKernel
        kernel = SemanticKernel(budget=SemanticBudget(max_sources=64, max_total_source_bytes=524288,
                                max_facts=512, max_rules=256, max_atoms=1024, max_groundings=8000))
        # Bind the entire scope, not just its user-facing domain label.
        semantic_scope = "inquiry_" + _digest(claim["scope"])
        for ordinal, source in enumerate(usable):
            use(source)
            try:
                admission = kernel.add_source(source["content"], source_id=f"reference_{ordinal}", scope=semantic_scope)
            except NabtError as exc:
                semantic_incomplete = True
                exhausted = exhausted or exc.code == "RESOURCE_LIMIT"
                residual("SEMANTIC_SOURCE_NOT_ADMITTED", {"source_id": source["source_id"], "error": exc.as_dict()})
                continue
            if not admission.accepted:
                semantic_incomplete = True
                exhausted = exhausted or any(r.get("code") == "RESOURCE_LIMIT" for r in admission.residuals)
                residual("SEMANTIC_SOURCE_NOT_ADMITTED", {"source_id": source["source_id"], "report": admission.as_dict()})
        queries = [("claim", claim["claim_id"], claim["candidate"])] + [
            ("alternative", a["alternative_id"], a["candidate"]) for a in review["alternatives"]]
        for purpose, target, query in queries:
            if not room():
                break
            try:
                result = kernel.query(query, scope=semantic_scope)
                status = result.status
                reason = result.reason
                positive, negative = result.positive_support, result.negative_support
                exhausted = exhausted or (status == "DEFER" and result.reason == "RESOURCE_LIMIT")
            except NabtError as exc:
                status, positive, negative = exc.status, False, False
                reason = exc.code
                exhausted = exhausted or exc.code == "RESOURCE_LIMIT"
                residual("QUERY_NOT_EVALUATED", {"target": target, "error": exc.as_dict()})
            checks.append({"protocol": "source-entailment-v1", "purpose": purpose, "target": target,
                           "source_ids": [s["source_id"] for s in usable], "status": status, "reason": reason,
                           "positive": positive, "negative": negative,
                           "detector": "Re-extraction and signed Horn query against all live scoped references"})
            if status in {"DEFER", "REJECT", "UNKNOWN", "OUT_OF_SCOPE"}:
                semantic_incomplete = True
                residual("SEMANTIC_RESULT_UNRESOLVED", {"target": target, "status": status})
            if purpose == "claim":
                # A signed derivation through contested premises is not a clean
                # endorsement of either polarity. Keep it in diagnostics only.
                qualified = status in {"SUPPORTED", "REFUTED", "CONFLICT"}
                supported, counterevidence = positive and qualified, negative and qualified
                if supported:
                    evidence_rank = 1
            elif positive or status not in {"REFUTED"}:
                alternative_supported = True
    else:
        for source in usable:
            result = exact(source, claim["candidate"], "claim", claim["claim_id"])
            if result is None:
                break
            if result:
                supported = True
                independent = not (candidate_roots & lineage(source)[0])
                evidence_rank = max(evidence_rank, 2 if independent else 1)
                if not independent:
                    residual("SHARED_DECLARED_ORIGIN", source["source_id"])
            else:
                counterevidence = True
            for alternative in review["alternatives"]:
                alt = exact(source, alternative["candidate"], "alternative", alternative["alternative_id"])
                if alt is None:
                    break
                alternative_supported = alternative_supported or alt
            if exhausted:
                break

    for name in ("context", "conditions"):
        for item in review[name]:
            source = resolve(item)
            if source is None or not lineage(source)[1] or source["scope"] != claim["scope"]:
                review_ok = False
                residual("REVIEW_SOURCE_UNAVAILABLE", {"purpose": name, "source_id": item["source_id"]})
                continue
            result = exact(source, item["expected"], name, claim["claim_id"])
            if result is not True:
                review_ok = False
                residual("REVIEW_CHECK_INCOMPLETE" if result is None else "REVIEW_CHECK_FAILED", name)
    if review["unresolved"]:
        review_ok = False
        residual("DECLARED_UNRESOLVED", review["unresolved"])
    if alternative_supported:
        review_ok = False
        residual("ALTERNATIVE_UNRESOLVED", "A declared alternative is supported or not refuted")
    if review["depth"] in {"DEEP", "ENLIGHTENED"} and not review["alternatives"]:
        review_ok = False
        residual("ALTERNATIVE_REVIEW_MISSING", "The selected profile requires a discriminated alternative")
    if review["depth"] == "ENLIGHTENED":
        for name in ("context", "conditions", "limitations"):
            if not review[name]:
                review_ok = False
                residual("ENLIGHTENED_OBLIGATION_MISSING", name)
    if not usable:
        review_ok = False
        residual("NO_SCOPED_REFERENCE", "No usable live reference covers the exact claim scope")
    if semantic_incomplete:
        review_ok = False
    world = claim["kind"] == "WORLD_CORRESPONDENCE"
    if world:
        residual("WORLD_BRIDGE_UNAVAILABLE", "No external observation authority is installed in v1")
    if exhausted:
        residual("CHECK_BUDGET_EXHAUSTED", {"max_checks": max_checks})
    if supported and plan["requested_rank"] > evidence_rank:
        residual("INSUFFICIENT_AUTHORITY_RANK", {"requested": plan["requested_rank"], "available": evidence_rank})
    gates = {"formed": formed, "reviewed": review_ok, "provenance": bool(usable),
             "scopeCovered": bool(usable) and len(usable) == len(references) and not semantic_incomplete,
             "supported": supported, "counterevidence": counterevidence,
             "requiresWorldBridge": world, "worldBridge": False, "exhausted": exhausted,
             "requestedRank": plan["requested_rank"], "evidenceRank": evidence_rank}
    verdict = decide_gate(gates)
    expected_checks = ((1 + len(review["alternatives"])) *
                       (1 if claim["kind"] == "SOURCE_ENTAILMENT" else len(references))
                       + len(review["context"]) + len(review["conditions"]))
    claim_checked = bool(usable) and any(
        check["purpose"] == "claim" and check.get("status") not in {"DEFER", "REJECT", "OUT_OF_SCOPE"}
        for check in checks)
    report = {
        "version": VERSION, "status": verdict["verdict"], "authorized_rank": verdict["authorized_rank"],
        "authority": {"TEXT_CORRESPONDENCE": "SNAPSHOT_COMPARISON", "SOURCE_ENTAILMENT": "SOURCE_RELATIVE_INFERENCE",
                      "WORLD_CORRESPONDENCE": "WORLD_BRIDGE_REQUIRED"}[claim["kind"]],
        "world_truth": "NOT_ESTABLISHED", "external_truth_certified": False,
        "box_opened": claim_checked and not world,
        "checks_performed": len(checks), "checks_expected": expected_checks,
        "review_complete": review_ok and not exhausted,
        "coverage_complete": (not exhausted and not semantic_incomplete and len(usable) == len(references)
                              and bool(usable) and len(checks) == expected_checks),
        "coverage_scope": "Only the declared live reference inventory at the exact domain/referent/time/unit",
        "plan_digest": _digest(plan), "input_digest": _digest([VERSION, plan, sorted(sources, key=lambda s: s["source_id"]), max_checks]),
        "claim": claim, "formation": formation, "review": review, "gates": gates,
        "checks": checks, "sources_used": [used[sid] for sid in sorted(used)], "residuals": residuals,
        "provenance": {"authority": "DECLARED_GRAPH_ONLY_NOT_AUTHENTICATED_ACQUISITION",
                       "candidate_origins": sorted(candidate_roots),
                       "reference_origins": {s["source_id"]: sorted(lineage(s)[0]) for s in usable}},
        "review_authority": "FINITE_PROCEDURAL_PROFILE_NOT_HUMAN_THOUGHT_OR_CERTAINTY",
        "formation_authority": "DECLARED_SOURCE_LINKS_NOT_PROOF_OF_HOW_THE_CANDIDATE_WAS_PRODUCED",
        "temporal_authority": "REPLAY_BINDING_NOT_PROOF_OF_PRE_REGISTERED_OR_UNSEEN_VALIDATION",
    }
    # The CLI emits this compact JSON plus one newline; its own verifier must
    # be able to read every successful report within the same wire budget.
    _bounded(report, MAX_REPORT_BYTES - 1)
    return report


def verify_inquiry(report: object, plan: dict, sources: list[dict], *, max_checks: int = 128) -> dict:
    """Replay against independently supplied expected inputs, never report inputs."""
    try:
        _bounded(report, MAX_REPORT_BYTES)
        expected = audit_inquiry(plan, sources, max_checks=max_checks)
        if type(report) is not dict or _bytes(report) != _bytes(expected):
            return {"valid": False, "status": "REJECT", "reason": "STALE_OR_FORGED_INQUIRY",
                    "world_truth": "NOT_ESTABLISHED"}
        # A faithful DEFER/REFUTED report can be verified without endorsing its claim.
        return {"valid": True, "status": "VERIFIED", "claim_status": expected["status"],
                "authority": "EXACT_INQUIRY_REPLAY", "world_truth": "NOT_ESTABLISHED"}
    except NabtError as exc:
        return {"valid": False, "status": exc.status, "reason": exc.code, "world_truth": "NOT_ESTABLISHED"}

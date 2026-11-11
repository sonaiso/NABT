"""Join occurrence-bound form readings to the installed native indication law."""
from hashlib import sha256
import subprocess

from nabt.derivation import _recover
from tools import explainable_pilot as pilot, lexical_testimony, verified_reading
from tools.arabic_training.source_reading import compatible
from tools.mantuq_inference.source_bound import _witnesses
from .operations import ROOT, digest, exact_terms
from .retrieval import _text

SCHEMA = "nabt.relational-root-sense.v1"
INDICATIONS = ("mutabaqa", "tadammun", "iltizam")
PROFILE = ROOT / "formal/.lake/build/bin/lexicalDenotation"


def validate(query):
    if type(query) is not dict or "target" not in query or query.keys() - {"span", "target", "case"}:
        raise ValueError("Expected original UTF-8 span, target components and optional case")
    span, target = query.get("span"), query["target"]
    if "span" in query and (type(span) is not list or len(span) != 2 or any(type(n) is not int for n in span)
            or not 0 <= span[0] < span[1] <= 8192):
        raise ValueError("Expected a nonempty original UTF-8 interval")
    if type(target) is not list or len(target) > 64:
        raise ValueError("Expected at most 64 target components")
    for term in target:
        if not _text(term, "target component", maximum=4096).strip():
            raise ValueError("Empty target component")
    if "case" in query:
        if "span" not in query:
            raise ValueError("A case ledger requires an exact occurrence span")
        case = query["case"]
        if type(case) is not dict or set(case) != {"source", "source_id", "revision", "scope", "entity", "counterpart"}:
            raise ValueError("Expected a separately bound ground case ledger")
        for field, maximum in (("source", 65536), ("source_id", 128), ("revision", 128), ("scope", 128)):
            if not _text(case[field], field, maximum=maximum).strip():
                raise ValueError("Empty case field: " + field)
        for field in ("entity", "counterpart"):
            name = _text(case[field], field, maximum=128)
            if not verified_reading.valid_name(name):
                raise ValueError("Invalid ground participant name")


def _compatible_form(surface, record):
    canonical = record["surface"]
    if compatible(surface, canonical):
        return True
    # Only these reviewed productive nominal forms have this boundary profile.
    return record["category"] in {"اسم فاعل", "اسم مفعول", "اسم آلة"} and any(
        compatible(surface, canonical + mark) for mark in "ٌٍَُِ")


def _profile_shapes(surface, rows):
    # Delegate exact slot recovery and whole-template refill to the derivation owner.
    proposals = []
    for template in sorted({r["template"] for r in rows if "1" in r["template"]}):
        tokens = [int(c) - 1 if c in "1234" else c for c in template]
        arity = 1 + max(c for c in tokens if type(c) is int)
        pattern = {"tokens": tokens, "arity": arity, "root_domain": "radicals28_shape_only"}
        root = _recover(pattern, surface)
        if root is not None:
            proposals.append({"template": template, "root": root, "arity": arity,
                              "status": "FORMAL_CANDIDATE_NOT_ATTESTED"})
    return proposals


def _gloss(text, clause):
    """A candidate from one local dictionary construction, never a class-wide rule."""
    if len(clause) != 5:
        return None
    for left, right in zip(clause, clause[1:]):
        gap = text[left["codepoint_span"][1]:right["codepoint_span"][0]]
        if not gap or any(ch not in " \t" for ch in gap):
            return None
    token, actor, verb, event, manner = clause
    if not (compatible(verb["surface"], "عَدَا") and
            any(compatible(event["surface"], x) for x in ("عَدْوًا", "عَدْواً")) and
            any(compatible(manner["surface"], x) for x in ("ثَقِيلًا", "ثَقِيلاً", "سَرِيعًا", "سَرِيعاً"))):
        return None
    if len(actor["surface"]) < 3 or not actor["surface"].startswith("ال") or not all("ء" <= ch <= "ي" or "ً" <= ch <= "ْ" for ch in actor["surface"]):
        return None
    return {"status": "LOCAL_GLOSS_CANDIDATE", "head": token, "participant": actor,
            "event": event, "event_verb": verb, "manner": manner, "property_bearer_span": event["utf8_span"],
            "span": [token["utf8_span"][0], manner["utf8_span"][1]], "universal_property": False}


def _case(row, occurrence, case, source_id, source_hash):
    """Reuse the checked full/clean ground ledger. The caller cannot choose obligations."""
    profile = row["capability"]
    anchor = "r_" + digest([source_id, source_hash, occurrence["span"]["start"], occurrence["span"]["end"],
                            row["sense"]["id"]])
    result = {"anchor": anchor, "status": "DEFER", "world_occurrence": False}
    if not profile or occurrence["reading_context"] != "UNQUOTED":
        return result
    x, y = case["entity"], case["counterpart"]
    needs = [("referent", anchor, "مرجع", x, True), ("counterpart", anchor, "طرف", y, True)]
    if profile == "key_lock":
        needs += [("type", x, "عضوية", "أداة", True), ("other_type", y, "عضوية", "قفل", True),
                  ("fit", x, "يوافق", y, True), ("state", y, "حالة", "سليم", True)]
    elif profile == "roll_patient":
        needs += [("type", x, "عضوية", "جسم", True), ("trial", x, "يقبل_التدحرج_على", y, True)]
    else:
        raise ValueError("Unknown installed capability profile")
    needs.append(("blocker_absence", x, "مانع", y, False))
    requirements = [{"slot": slot, "atom": {"predicate": pred, "arguments": [left, right], "positive": sign}}
                    for slot, left, pred, right, sign in needs]
    question = ("هل " + verified_reading.render_atom(requirements[0]["atom"]) + "؟\n").encode()
    try:
        answer = pilot.answer(case["source"].encode(), question, identity=case["source_id"],
                              revision=case["revision"], scope=case["scope"], answer_version="v1")
    except pilot.PilotError as err:
        return {**result, "status": err.code, "reason": str(err)}
    evidence = _witnesses(answer, requirements)
    status = "DEFER"
    if any(w["opposite_full_witness"] and w["full_witness"] for w in evidence):
        status = "CONFLICT"
    elif any(w["opposite_full_witness"] for w in evidence):
        status = "REFUTED"
    elif all(w["clean_witness"] for w in evidence):
        status = "SCOPED_CAPABILITY"
    return {**result, "status": status, "requirements": evidence, "owner_answer": answer}


_UNAVAILABLE = (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError, pilot.PilotError)


def _occurrence(text, query, occurrence, tokens, index, base, native, fingerprint, owner_by_root):
    token = tokens[index]
    out = {**base, "requested_span": token["utf8_span"], "occurrence_id": occurrence["occurrence_id"],
           "occurrence": token, "reading_context": occurrence["reading_context"],
           "formal_roots": occurrence["axes"]["formal_root"], "gloss_candidate": None,
           "checker_sha256": fingerprint, "readings": []}
    try:
        matched = [r for r in native["rows"] if _compatible_form(token["surface"], r)]
        out["proposed_sense_ids"] = [r["sense"]["id"] for r in matched]
        shapes = _profile_shapes(token["surface"], native["rows"])
        out["profile_shape_candidates"] = shapes
        verb_templates = {r["template"] for r in native["rows"] if r["category"] == "فعل"}
        if (any(r["category"] == "فعل" for r in matched)
                or any(c["template"] in verb_templates for c in shapes)
                or any(c["pattern_id"].startswith("past.") for c in occurrence["candidates"])):
            gloss = _gloss(text, tokens[index:index + 5])
            if gloss:
                a, b = gloss["span"]
                appraisal = lexical_testimony._native(PROFILE, {"op": "root_gloss", "value": {
                    "text": text, "start": a, "end": b, "target": query["target"]}})
                if pilot.file_sha(PROFILE) != fingerprint:
                    raise ValueError("Gloss checker changed")
                if appraisal["status"] == "CONDITIONAL_GLOSS" and (
                        appraisal["quotation"].encode() != text.encode()[a:b] or appraisal["head"] != token["surface"]
                        or appraisal["target"] != query["target"] or appraisal["participant"] != gloss["participant"]["surface"]):
                    raise ValueError("Native gloss binding differs")
                out["gloss_candidate"] = {**gloss, "conditional_denotation": appraisal}
        for row in matched:
            sense = row["sense"]
            testimony = lexical_testimony._citation(sense["citation"], ROOT)
            reading = {**row, "testimony": testimony, "root_arity": len(sense["root"]),
                       "same_root_shape_candidate_ids": [c["candidate_id"] for c in occurrence["candidates"]
                                               if c["root"] == sense["root"]],
                       "authority": "CONDITIONAL_LEXICAL_PROFILE"}
            if sense["citation"]["work"] != "root_profile":
                root = sense["root"]
                if root not in owner_by_root:
                    owner = lexical_testimony.assess(root, query["target"])
                    if not owner["native_checked"] or owner["native_sha256"] != fingerprint:
                        raise ValueError("Lexical testimony unavailable: " + owner["status"])
                    owner_by_root[root] = owner
                checked = next(r for r in owner_by_root[root]["rows"] if r["sense_id"] == sense["id"])
                if row["indications"] != [k for k in INDICATIONS if checked["indications"][k]]:
                    raise ValueError("Indication owners disagree")
                reading["commitment_conditions"] = checked["commitment_conditions"]
            if "case" in query:
                reading["case"] = _case(row, occurrence, query["case"], out["source_id"], out["source_sha256"])
            out["readings"].append(reading)
        if not matched:
            out["reason"] = "NO_INSTALLED_LEXICAL_ALIGNMENT"
        else:
            out.update(status="CONDITIONAL_READINGS", common_installed_indications=[
                k for k in INDICATIONS if all(k in r["indications"] for r in matched)])
    except _UNAVAILABLE as err:
        out.update(status="VERIFICATION_UNAVAILABLE", reason=str(err), readings=[], common_installed_indications=[])
    return out

def analyze(text, source_id, query, derivation):
    validate(query)
    span = query.get("span")
    base = {"schema": SCHEMA, "status": "DEFER", "source_id": source_id,
            "source_sha256": sha256(text.encode()).hexdigest(), "target": query["target"],
            "readings": [], "common_installed_indications": [], "world_truth_established": False,
            "all_arabic_senses_enumerated": False, "intended_sense_established": False}
    tokens = exact_terms(text)
    indices = {tuple(t["utf8_span"]): i for i, t in enumerate(tokens)}
    occurrences = derivation.get("occurrences", [])
    selected = []
    for item in occurrences:
        interval = [item["span"]["start"], item["span"]["end"]]
        if span is None or span == interval:
            selected.append((item, interval, indices.get(tuple(interval))))
    if span is not None and not selected:
        return {**base, "requested_span": span, "reason": "NO_COMPLETE_DERIVATION_OCCURRENCE"}

    try:
        fingerprint = pilot.file_sha(PROFILE)
        native = lexical_testimony._native(PROFILE, {"op": "root_sense_profile", "value": query["target"]})
        if native.get("schema") != "nabt.root-sense.profile.v1" or native.get("target") != query["target"]:
            raise ValueError("Native profile protocol mismatch")
        owner_by_root = {}
        rows = []
        for occurrence, interval, index in selected:
            if index is None:
                rows.append({**base, "requested_span": interval, "reason": "SPAN_NOT_A_COMPLETE_TOKEN"})
            else:
                rows.append(_occurrence(text, query, occurrence, tokens, index, base, native, fingerprint, owner_by_root))
        if pilot.file_sha(PROFILE) != fingerprint:
            raise ValueError("Native profile changed during analysis")
        if span is not None:
            result = rows[0]
        else:
            result = {**base, "occurrences": rows, "checker_sha256": fingerprint,
                      "status": "OCCURRENCES_ANALYZED" if rows else "DEFER"}
            if not rows:
                result["reason"] = "NO_DERIVATION_OCCURRENCES"
            elif any(r["status"] == "VERIFICATION_UNAVAILABLE" for r in rows):
                result["status"] = "PARTIAL_VERIFICATION"
        if owner_by_root:
            result["lexical_owner_reports"] = owner_by_root
        return result
    except _UNAVAILABLE as err:
        return {**base, "requested_span": span, "status": "VERIFICATION_UNAVAILABLE", "reason": str(err)}

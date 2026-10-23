"""Explicit discourse premises and conservative, source-bound reference.

An entity declaration is a premise supplied by a user of the reader. It is
not learned gender, a lexical dictionary, a dependency label or world truth.
The complete canonical context is replayed together with the original text.
"""

from copy import deepcopy
from hashlib import sha256
import json
import re
import unicodedata

from .corpus_evidence import lookup_key, template_matches
from .discourse_laws import (combine_compatibility, feature_compatibility,
                             reference_allowed, selection_status)
from .errors import NabtError, resource_limit

MAX_CONTEXT_BYTES = 65536
MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_ENTITIES = 64
GENDERS = ("masculine", "feminine", "unknown")
NUMBERS = ("singular", "dual", "plural", "unknown")
KINDS = ("person", "place", "thing", "unknown")


def wire(value, maximum=MAX_REPORT_BYTES):
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise NabtError("INVALID_DISCOURSE_JSON", "Use bounded strict JSON") from error
    if len(raw) > maximum:
        raise resource_limit("Discourse JSON exceeds its byte budget", maximum_bytes=maximum)
    return raw


def identity(value):
    return sha256(wire(value)).hexdigest()


def _label(value, choices, name):
    if type(value) is not str or value not in choices:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Invalid context " + name)
    return value


def _entity_id(value):
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value) is None:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Entity IDs use bounded lowercase ASCII names")
    return value


def _form(value):
    if (type(value) is not str or not value or len(value.encode("utf-8")) > 256 or
            any(unicodedata.category(c)[0] in ("C", "Z") for c in value) or lookup_key(value) is None):
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "A context form is one bounded Arabic written run")
    return value


def read_context(value=None):
    if value is None:
        value = {}
    if type(value) is not dict or set(value) - {
            "entities", "speaker", "addressee", "deixis", "closed_reference_scope"}:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Use only the declared context premise fields")
    wire(value, MAX_CONTEXT_BYTES)
    entities = value.get("entities", [])
    if type(entities) is not list:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Context entities must be an array")
    if len(entities) > MAX_ENTITIES:
        raise resource_limit("Discourse entity budget exceeded", maximum=MAX_ENTITIES)
    result, ids = [], set()
    for entity in entities:
        if (type(entity) is not dict or not {"id", "name"} <= set(entity) or
                set(entity) - {"id", "name", "gender", "number", "kind"}):
            raise NabtError("INVALID_DISCOURSE_CONTEXT", "Entity declarations need id and name, with optional traits")
        eid = _entity_id(entity["id"])
        if eid in ids:
            raise NabtError("INVALID_DISCOURSE_CONTEXT", "Entity IDs must be unique; names may be ambiguous")
        ids.add(eid)
        result.append({"id": eid, "name": _form(entity["name"]),
                       "gender": _label(entity.get("gender", "unknown"), GENDERS, "gender"),
                       "number": _label(entity.get("number", "unknown"), NUMBERS, "number"),
                       "kind": _label(entity.get("kind", "unknown"), KINDS, "kind")})
    canonical = {"entities": result, "deixis": [],
                 "closed_reference_scope": value.get("closed_reference_scope", False)}
    if type(canonical["closed_reference_scope"]) is not bool:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Reference scope closure is a Boolean premise")
    for key in ("speaker", "addressee"):
        if key in value:
            eid = _entity_id(value[key])
            if eid not in ids:
                raise NabtError("INVALID_DISCOURSE_CONTEXT", "Participant must name a declared entity")
            canonical[key] = eid
    deixis = value.get("deixis", [])
    if type(deixis) is not list:
        raise NabtError("INVALID_DISCOURSE_CONTEXT", "Deixis must be an array of explicit bindings")
    if len(deixis) > MAX_ENTITIES:
        raise resource_limit("Discourse deixis budget exceeded", maximum=MAX_ENTITIES)
    for item in deixis:
        if type(item) is not dict or set(item) != {"form", "entity_ids"}:
            raise NabtError("INVALID_DISCOURSE_CONTEXT", "Deixis requires form and entity_ids")
        targets = item["entity_ids"]
        if type(targets) is not list or not targets or len(targets) > MAX_ENTITIES:
            raise NabtError("INVALID_DISCOURSE_CONTEXT", "Use a nonempty bounded set of deictic alternatives")
        if any(_entity_id(eid) not in ids for eid in targets) or len(set(targets)) != len(targets):
            raise NabtError("INVALID_DISCOURSE_CONTEXT", "Deictic alternatives must be distinct declared entities")
        canonical["deixis"].append({"form": _form(item["form"]), "entity_ids": list(targets)})
    raw = wire(canonical, MAX_CONTEXT_BYTES)
    return {"schema": "nabt.discourse-context.v1", "value": canonical,
            "sha256": sha256(raw).hexdigest(), "canonical_utf8": raw.decode("utf-8"),
            "authority": "EXPLICIT_SOURCE_PREMISES_NOT_ACQUIRED_WORLD_FACTS"}


def form_matches(observed, declared):
    return (lookup_key(observed) == lookup_key(declared) and
            template_matches(observed, declared, mutable_last=True))


def profile_compatibility(profile, entity):
    """Only specified pronoun dimensions constrain an otherwise possible entity."""
    states = []
    for field, labels in (("gender", GENDERS[:2]), ("number", NUMBERS[:3])):
        desired = profile.get(field)
        if desired in labels:
            actual = entity.get(field, "unknown")
            states.append(feature_compatibility(labels.index(desired),
                                                labels.index(actual) if actual in labels else None))
    return combine_compatibility(states)


def resolve_reference(surface, *, origin, profile, context, mentions, span,
                      scope, return_entity=None, source_prefix_complete=True):
    """Enumerate candidates, retain unknown competitors, then apply Lean gates.

    Antecedents here are earlier mentions in this one unquoted text scope.
    This is an explicitly bounded acquisition rule, not a universal theorem
    that every Arabic antecedent must precede its pronoun on the page.
    """
    if type(source_prefix_complete) is not bool:
        raise NabtError("INVALID_REFERENCE_SCOPE", "Source-prefix completeness must be an actual Boolean")
    value = context["value"]
    entities = {entity["id"]: entity for entity in value["entities"]}
    selected, bases = set(), {}
    if origin == "named":
        selected.update(e["id"] for e in entities.values() if form_matches(surface, e["name"]))
    elif origin in ("speaker", "addressee"):
        if origin in value:
            selected.add(value[origin])
    elif origin == "deictic":
        for item in value["deixis"]:
            if form_matches(surface, item["form"]):
                selected.update(item["entity_ids"])
    elif origin == "relative_return":
        if return_entity is not None and return_entity in entities:
            selected.add(return_entity)
    elif origin == "antecedent":
        for mention in mentions:
            if (mention["scope"] == scope and not mention["quoted"] and
                    mention["span"]["source_id"] == span["source_id"] and
                    mention["span"]["source_sha256"] == span["source_sha256"] and
                    mention["span"]["end"] <= span["start"]):
                selected.add(mention["entity_id"])
                bases.setdefault(mention["entity_id"], []).append(mention)
    else:
        raise NabtError("INVALID_REFERENCE_ORIGIN", "Use a declared reference origin")
    candidates = []
    for eid in sorted(selected):
        entity = deepcopy(entities[eid])
        observations = bases.get(eid, [])
        # A prior mention may independently supply a missing lexical trait.
        # Conflicting/ambiguous observations never produce a fabricated value.
        for feature in ("gender", "number"):
            observed = {m.get(feature) for m in observations if m.get(feature) not in (None, "unknown")}
            if entity[feature] == "unknown" and len(observed) == 1:
                entity[feature] = next(iter(observed))
        compatibility = profile_compatibility(profile, entity)
        allowed = reference_allowed(origin, compatibility, origin_licensed=True,
                                    identity_bound=True, source_supported=True,
                                    scope_allowed=True, quote_allowed=True,
                                    order_licensed=origin != "antecedent" or bool(observations),
                                    return_licensed=origin != "relative_return" or return_entity == eid)
        candidates.append({"entity_id": eid, "compatibility": compatibility,
                           "allowed": allowed, "entity_traits": {f: entity[f] for f in ("gender", "number", "kind")},
                           "context_sha256": context["sha256"],
                           "antecedent_witnesses": deepcopy(observations)})
    surviving = [c for c in candidates if c["allowed"]]
    # A declared closed context does not repair an incomplete search through
    # the source. A deferred earlier clause may contain an unacquired rival;
    # do not discard that possibility and turn the surviving list into proof.
    closed = (value["closed_reference_scope"] and source_prefix_complete) if origin == "antecedent" else True
    # Explicit identity bindings do not require invention of unknown traits.
    confirmed = all(c["compatibility"] == "confirmed" for c in surviving) if origin == "antecedent" else True
    status = selection_status(len(surviving), closed_scope=closed, all_confirmed=confirmed)
    bound = surviving[0]["entity_id"] if status == "RESOLVED" else None
    record = {"origin": origin, "surface": surface, "span": deepcopy(span), "scope": scope,
              "profile": deepcopy(profile), "context_sha256": context["sha256"],
              "candidates": candidates, "candidate_entity_ids": [c["entity_id"] for c in surviving],
              "bound_entity_id": bound, "closed_scope": closed, "status": status,
              "source_prefix_complete": source_prefix_complete,
              "authority": "CONDITIONAL_REFERENCE_WITHIN_DECLARED_SOURCE_SCOPE"}
    record["reference_id"] = identity(record)
    return record

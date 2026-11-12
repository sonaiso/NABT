"""Compile a finite, source-relative genus/property slice for the signed reading owner."""
from collections import defaultdict
from hashlib import sha256

from nabt.text_reader import parse_document
from tools import explainable_pilot as pilot
from tools import verified_reading as ground
from tools.licensed_inference.runtime import aggregate_evidence
from .operations import ROOT, exact_terms

LAW = "nabt.genus-property-opening.v1"
STRUCTURE = {"نوع", "أخص", "لازم", "يباين", "يتطلب"}
OBSERVATIONS = {"عضوية", "خاصية", "شرط", "مانع"}
EVENT = "فتح"


def validate(request):
    if type(request) is not dict or set(request) != {"ledger", "root", "parent", "entity"}:
        raise ValueError("Expected genus ledger, root, partition parent and target entity")
    for field in ("root", "parent", "entity"):
        name = request[field]
        if type(name) is not str or not ground.valid_name(name) or len(name) > 40:
            raise ValueError("Invalid genus slice identifier: " + field)
    if type(request["ledger"]) is not str or len(request["ledger"].encode()) > 8192:
        raise ValueError("Expected a bounded original genus ledger")


def atom(predicate, left, right, positive=True):
    return {"predicate": predicate, "arguments": [left, right], "positive": positive}


def read_facts(text):
    if not text.strip():
        return [], []
    doc = parse_document(text, source_id="genus_ledger")
    if not doc.accepted or doc.rules or doc.queries or doc.declarations or doc.definitions:
        raise ValueError("Genus ledger accepts only signed ground facts")
    facts, witnesses = [], []
    raw = text.encode()
    for fact in doc.facts:
        a = ground.literal(fact.atom)
        pred = a["predicate"]
        if (len(a["arguments"]) != 2 or pred not in STRUCTURE | OBSERVATIONS
                or (pred in STRUCTURE and not a["positive"])
                or not all(ground.valid_name(name) and len(name) <= 40 for name in a["arguments"])):
            raise ValueError("Outside the signed genus fact vocabulary")
        facts.append(a)
        start, end = fact.span.start, fact.span.end
        witnesses.append({"byte_span": [start, end], "surface": raw[start:end].decode(), "atom": a})
    return facts, witnesses


def ancestors(edges, nodes):
    parents = defaultdict(set)
    for child, parent in edges:
        parents[child].add(parent)
    cache = {}

    def visit(node, active):
        if node in active:
            raise ValueError("Cycle in genus or property chain")
        if node not in cache:
            result = {node}
            for parent in parents[node]:
                result.update(visit(parent, active | {node}))
            cache[node] = result
        return cache[node]

    return {node: visit(node, set()) for node in sorted(nodes)}


def opening(text, entity):
    """Match one entire pedagogical clause; punctuation, case and voice matter."""
    surface = text.strip().removesuffix(".").strip()
    words = surface.split()
    rows = [
        ("DISPOSITION", ("قابل للفتح", "قابلٌ للفتح", "قَابِلٌ لِلْفَتْحِ"), True),
        ("STATE", ("مفتوح", "مفتوحٌ", "مَفْتُوحٌ"), True),
        ("ASSERTED_PASSIVE", ("فُتح", "فُتِح", "فُتِحَ"), False),
        ("NEGATED_EVENT", ("لم يُفتح", "لم يُفتَح", "لم يُفْتَحْ", "لَمْ يُفْتَحْ"), False),
        ("PURPOSE", ("لكي يُفتح", "لكي يُفتَح", "لكي يُفْتَحَ", "لِكَيْ يُفْتَحَ"), False),
    ]
    for kind, forms, nominal in rows:
        for form in forms:
            parts = form.split()
            for bearer in (entity, entity + "ُ"):
                bound = [bearer, *parts] if nominal else [*parts, bearer]
                if words == bound or words == parts:
                    # Bare يُفتح can also represent active يُفْتِح; keep voice conditional.
                    voice = ("UNRESOLVED" if "يُفتح" in parts else
                             "PASSIVE" if not nominal else None)
                    return {"kind": kind, "bearer": entity if words == bound else None,
                            "voice": voice, "scope": "CONTROLLED_CLAUSE", "tokens": exact_terms(text)}
    return {"kind": "DEFER", "bearer": None, "voice": None, "scope": None, "tokens": exact_terms(text)}


def ground_rules(facts, pairs, individuals, required):
    rules = []

    def add(head, *body):
        if len(rules) + len(facts) >= 250 or len(body) > 16:
            raise OverflowError("Genus projection exceeds the signed owner's finite budget")
        rules.append({"kind": "rule", "body": list(body), "head": head})

    for x in individuals:
        for g, h in sorted(pairs["نوع"]):
            add(atom("عضوية", x, h), atom("عضوية", x, g), atom("نوع", g, h))
        for g, p in sorted(pairs["لازم"]):
            add(atom("خاصية", x, p), atom("عضوية", x, g), atom("لازم", g, p))
        for p, q in sorted(pairs["أخص"]):
            add(atom("خاصية", x, q), atom("خاصية", x, p), atom("أخص", p, q))
            add(atom("خاصية", x, p, False), atom("خاصية", x, q, False), atom("أخص", p, q))
        for g, h in sorted(pairs["يباين"]):
            for left, right in ((g, h), (h, g)):
                add(atom("عضوية", x, right, False), atom("عضوية", x, left), atom("يباين", g, h))
        if required:
            body = [atom("شرط", x, EVENT), atom("مانع", x, EVENT, False)]
            for prop in required:
                body.extend([atom("يتطلب", EVENT, prop), atom("خاصية", x, prop)])
            add(atom("قابلية", x, EVENT), *body)
        add(atom("قابلية", x, EVENT, False), atom("مانع", x, EVENT))
    return rules


def analyze(text, source_id, request):
    validate(request)
    entity, root, parent = (request[k] for k in ("entity", "root", "parent"))
    facts, witnesses = read_facts(request["ledger"])
    pairs = defaultdict(set)
    for fact in facts:
        if fact["positive"]:
            pairs[fact["predicate"]].add(tuple(fact["arguments"]))
    kinds = {root} | {n for edge in pairs["نوع"] | pairs["يباين"] for n in edge}
    kinds.update(g for g, _ in pairs["لازم"])
    kinds.update(a["arguments"][1] for a in facts if a["predicate"] == "عضوية")
    lineage = ancestors(pairs["نوع"], kinds)
    if any(root not in path for path in lineage.values()):
        raise ValueError("Every non-root genus needs a path to the declared root")
    if any(a == b for a, b in pairs["يباين"]):
        raise ValueError("A genus cannot be declared disjoint from itself")
    traits = {n for edge in pairs["أخص"] for n in edge}
    traits.update(prop for _, prop in pairs["لازم"] | pairs["يتطلب"])
    traits.update(a["arguments"][1] for a in facts if a["predicate"] == "خاصية")
    property_lineage = ancestors(pairs["أخص"], traits)
    children = sorted(g for g, p in pairs["نوع"] if p == parent)
    individuals = sorted({entity} | {a["arguments"][0] for a in facts if a["predicate"] in OBSERVATIONS})
    raw_ledger = request["ledger"].encode()
    result = {"schema": LAW, "source_id": source_id, "target_sha256": sha256(text.encode()).hexdigest(),
              "ledger_sha256": sha256(raw_ledger).hexdigest(), "witnesses": witnesses,
              "reading": opening(text, entity), "world_truth_established": False,
              "scope": "DECLARED_GENERA_AND_CONTROLLED_TEXT", "new_lean_theorem": False}
    required = sorted(p for m, p in pairs["يتطلب"] if m == EVENT)
    try:
        rules = ground_rules(facts, pairs, individuals, required)
        clauses = [{"kind": "fact", "atom": a} for a in facts] + rules
        program = "".join(ground.render_clause(c) for c in clauses).encode()
        goal = atom("قابلية", entity, EVENT)
        query = ("هل " + ground.render_atom(goal) + "؟\n").encode()
        cert = pilot.propose_certificate(program, query, "genus_projection", "1", "genus")
    except (OverflowError, pilot.PilotError) as error:
        return {**result, "status": getattr(error, "code", "RESOURCE_LIMIT"), "reason": str(error)}

    try:
        receipt, fingerprint = pilot.native(program, query, cert, "genus_projection", "1", "genus",
                                           ROOT / "formal/.lake/build/bin/verifiedReading", 20)
        check = {"status": "VERIFIED_GROUND_PROJECTION", "receipt": receipt, "checker_sha256": fingerprint}
    except pilot.PilotError as error:
        check = {"status": error.code}
        if error.code != "CHECKER_UNAVAILABLE":
            return {**result, "status": error.code, "checker": check}

    known = {ground.key(a) for a in cert["known"]}
    clean = {ground.key(a) for a in cert["clean_known"]}

    def status(pred, left, right):
        key = (pred, (left, right), True)
        opp = ground.opposite(key)
        evidence = {"positive": key in known, "negative": opp in known,
                    "clean_positive": key in clean, "clean_negative": opp in clean}
        return aggregate_evidence([evidence])["status"]

    candidates = []
    for child in children:
        needed = sorted({p for genus, p in pairs["لازم"] if genus in lineage[child]})
        properties = {p: status("خاصية", entity, p) for p in needed}
        membership = status("عضوية", entity, child)
        states = set(properties.values())
        if "CONFLICT" in states or membership == "CONFLICT" or (membership == "SUPPORTED" and "REFUTED" in states):
            verdict = "CONFLICT"
        elif "REFUTED" in states or membership == "REFUTED":
            verdict = "EXCLUDED"
        elif membership == "SUPPORTED" or (needed and states == {"SUPPORTED"}):
            verdict = "MATCH"
        else:
            verdict = "UNRESOLVED"
        candidates.append({"genus": child, "membership": membership, "properties": properties, "status": verdict})

    matches = [r["genus"] for r in candidates if r["status"] == "MATCH"]
    statuses = {r["status"] for r in candidates}
    parent_status = status("عضوية", entity, parent)
    decision = "DEFER"
    if "CONFLICT" in statuses or parent_status == "CONFLICT":
        decision = "CONFLICT"
    elif parent_status == "SUPPORTED" and len(matches) == 1 and "UNRESOLVED" not in statuses:
        decision = "UNIQUE_IN_LIST"
    # Map the owner's full proof steps back to the original ledger fact spans.
    supports = {}
    for a, step in zip(cert["known"], cert["steps"], strict=True):
        i = step["index"]
        if step["kind"] == "fact":
            indices = {i}
        else:
            indices = set().union(*(supports[ground.key(b)] for b in rules[i]["body"]))
        supports[ground.key(a)] = indices

    collisions = []
    for g, h in sorted(pairs["يباين"]):
        for x in individuals:
            if all(("عضوية", (x, kind), True) in known for kind in (g, h)):
                causes = set().union(supports[("عضوية", (x, g), True)], supports[("عضوية", (x, h), True)],
                                     supports[("يباين", (g, h), True)])
                collisions.append({"genera": [g, h], "common_individual": x, "status": "CONFLICT",
                                   "witness_indices": sorted(causes)})
                if parent in lineage[g] and parent in lineage[h]:
                    decision = "CONFLICT"
    partitions = {"parent": parent, "parent_membership": parent_status, "candidates": candidates,
                  "decision": decision, "selected": matches[0] if decision == "UNIQUE_IN_LIST" else None}
    ability = status("قابلية", entity, EVENT)
    reading = result["reading"]
    checked = check["status"] == "VERIFIED_GROUND_PROJECTION"
    event_scope = {"DISPOSITION": "NOT_ASSERTED", "STATE": "NOT_ASSERTED", "PURPOSE": "INTENDED",
                   "ASSERTED_PASSIVE": "ASSERTED", "NEGATED_EVENT": "DENIED", "DEFER": "UNRESOLVED"}
    return {**result, "status": "EVALUATED" if checked else "PROPOSAL_ONLY", "checker": check, "projection": cert,
            "authority": "CHECKED_GROUND_PROJECTION" if checked else "FINITE_DIAGNOSTIC",
            "hierarchies": {"genus_ancestors": {g: sorted(path - {g}) for g, path in lineage.items()},
                            "property_ancestors": {p: sorted(path - {p}) for p, path in property_lineage.items()}},
            "entity_properties": {p: {"status": status("خاصية", entity, p),
                                      "positive_witness_indices": sorted(supports.get(("خاصية", (entity, p), True), ())),
                                      "negative_witness_indices": sorted(supports.get(("خاصية", (entity, p), False), ()))}
                                  for p in sorted(traits)},
            "partition": partitions, "disjoint_conflicts": collisions,
            "capability": {"entity": entity, "masdar": EVENT, "requirements": required, "status": ability},
            "attribute_bridge": {"masdar": EVENT if reading["kind"] != "DEFER" else None,
                                 "text_relation": reading["kind"], "bearer": reading["bearer"],
                                 "event_in_text": event_scope[reading["kind"]],
                                 "independent_capability": ability if reading["bearer"] == entity else "UNBOUND",
                                 "external_occurrence": "UNKNOWN"}}

"""Source-bound Q/A and selective evidence revision through the installed NTL lesson gateway."""
from hashlib import sha256
from unicodedata import category
import re

from nabt.semantics import atom_number
from nabt.text_ir import Atom, content_id
from tools.grammar_catalog.licensed_speech import SpeechGraph, surviving_nodes
from . import graph_interventions, ntl_core, witness_origins as ranker

SCHEMA = "ntl.witness-families.v1"
RESULT = "ntl.witness-families-result.v1"
QUESTIONS = {
    "capacity": "ما القابلية المنسوبة إلى {0}، وبأي قيد؟", "state": "ما الحالة المنسوبة إلى {0}؟",
    "event": "ما الحدث الذي تخبر العبارة عنه في شأن {0}؟", "negative": "ما الذي نُفي عن {0} وفي أي نطاق؟",
    "purpose": "ما الغاية المذكورة بخصوص {0}؟", "request": "ما المطلوب في شأن {0}؟",
    "even": "ما الوصف العددي المسند إلى {0}؟", "odd": "ما الوصف العددي المسند إلى {0}؟"
}
ANSWERS = {
    "capacity": "ينسب النص إلى «{carrier}» قابلية «{value}»",
    "state": "يصف النص حالة «{carrier}» بـ«{value}»",
    "event": "يُخبر النص عن «{value}» في شأن «{carrier}»",
    "negative": "ينفي النص «{value}» في شأن «{carrier}» في النطاق المذكور",
    "purpose": "يذكر النص «{value}» غايةً تتعلق بـ«{carrier}»",
    "request": "يطلب المتكلم «{value}» في شأن «{carrier}»",
    "even": "الوصف المسند إلى العدد {carrier} في النص هو «{value}»",
    "odd": "الوصف المسند إلى العدد {carrier} في النص هو «{value}»",
}

# An independently inspectable finite grammar for new inputs. An outer quote, condition,
# modifier or unknown noun blocks this binding until there is a contract for its scope.
RULES = (
    ("door", r"(لم يُفتح) (باب (?:المختبر|المتحف|البيت))", "negative", "الفتح"),
    ("seed", r"(لم تنبت) (بذرة (?:الخيار|الجزر|اللفت))", "negative", "الإنبات"),
    ("doc", r"(سَجِّلْ) (وثيقة (?:الإعارة|الزيارة|المعاينة))", "request", "التسجيل"),
)
PROOF = re.compile(r"([0-9]{1,5}) = 2 × ([0-9]{1,5})( \+ 1)?")


def recognize(text):
    for row in ranker.origins():
        if text == row["text"]:
            return row, "RETAINED_INSTRUCTOR_BINDING"
    parts = [p.strip() for p in text.removesuffix(".").split("؛")]
    if not 1 <= len(parts) <= 3 or not all(parts):
        return None, None
    clause = parts[0]
    tail = parts[1:]
    context = ""
    if tail and re.fullmatch(r"مكان الرصد في (المختبر|المشتل|الأرشيف|الفصل)", tail[0]):
        context = tail.pop(0)
    proof = tail[0] if len(tail) == 1 and PROOF.fullmatch(tail[0]) else ""
    if tail and not proof:
        return None, None
    number = re.fullmatch(r"العدد ([0-9]{1,5}) (زوجي|فردي)", clause)
    if number:
        carrier, cue = number.groups()
        family, relation, value = "num", ("even" if cue == "زوجي" else "odd"), cue
    else:
        for family, pattern, relation, value in RULES:
            match = re.fullmatch(pattern, clause)
            if match and not proof:
                cue, carrier = match.groups()
                break
        else:
            return None, None
    return dict(id=family, clause=clause, cue=cue, carrier=carrier, value=value, relation=relation,
                proof=proof, context=context, text=text), "FINITE_COMPOSITION_RULE"


def span(text, literal, base=0):
    if text.count(literal) != 1:
        raise ValueError("Occurrence is missing or ambiguous")
    lo = base + len(text[:text.index(literal)].encode())
    return {"surface": literal, "utf8_span": [lo, lo + len(literal.encode())]}


def number(predicate, first, second, scope):
    return atom_number(Atom(predicate, (first, second)), scope)


def run(lesson):
    if set(lesson) - {"schema", "text", "source_id", "withdraw"} or lesson.get("schema") != SCHEMA:
        raise ValueError("Unexpected witness lesson fields")
    text, source = lesson.get("text"), lesson.get("source_id")
    if not isinstance(text, str) or not 1 <= len(text.encode()) <= 720 or not text.strip():
        raise ValueError("Expected bounded original text")
    if not isinstance(source, str) or not source.strip() or len(source.encode()) > 128:
        raise ValueError("Expected a bounded source identity")
    if len(text) > 512 or any(category(c).startswith("C") for c in text + source):
        raise ValueError("Expected bounded single-line source and identity")
    cuts = lesson.get("withdraw", [])
    if type(cuts) is not list or len(cuts) > 12 or any(type(k) is not str for k in cuts) or len(set(cuts)) != len(cuts):
        raise ValueError("Expected unique witness identifiers")
    record, contract = recognize(text)
    result = {"schema": RESULT, "source_id": source, "source_sha256": sha256(text.encode()).hexdigest(),
              "text": text, "source_number": number("original", source, text, SCHEMA), "neural": ranker.propose(text), "binding": contract,
              "world_occurrence_established": False, "empirical_causality_established": False}
    if record is None:
        if cuts:
            raise ValueError("No licensed witnesses in this profile")
        return {**result, "status": "UNBOUND_READING", "questions": [], "residuals": ["SCOPED_BINDING_REQUIRED"]}
    graph = SpeechGraph(text, source)
    evidence = graph.owners["evidence"] = {}
    def witness(name, view, value):
        evidence[name] = {"view": view, **value}
        position = value.get("utf8_span")
        parents = graph.terms_at(position) if position else []
        space = {"D": "sign", "M": "concept", "W": "joint"}[view]
        graph.node(name, {"D": "sign", "M": "sense", "W": "indication"}[view], value,
                   ["evidence", name], parents, space, position, scope=contract)
    relation = record["relation"]
    carrier = record["carrier"]
    scope = SCHEMA + "/" + result["source_sha256"]
    whole_span = span(text, record["clause"])
    cue = span(record["clause"], record["cue"], whole_span["utf8_span"][0])
    witness("surface", "D", whole_span)
    witness("cue", "D", cue)
    witness("concept", "M", {"relation": relation, "carrier": carrier, "value": record["value"]})
    witness("binding", "W", {"contract": contract, "id": record["id"], "clause": whole_span, "cue": cue})
    specs = []
    def question(key, q, answer, predicate, args, parents, trace_span):
        graph.owners[key] = {"question": q, "answer": answer}
        graph.node(key, "content", answer, [key], parents, "joint", trace_span["utf8_span"], scope=contract)
        structure = number(predicate, *args, SCHEMA)
        where = number("occurrence", source, str(trace_span["utf8_span"]), scope)
        specs.append((key, q, answer, parents, structure, where))
    answer = ANSWERS[relation].format(carrier=carrier, value=record["value"]) + f'، ولفظه «{record["clause"]}».'
    question("reading", QUESTIONS[relation].format(carrier), answer, relation, (carrier, record["value"]),
             ["surface", "cue", "concept", "binding"], whole_span)
    if record["context"]:
        context = span(text, record["context"])
        witness("context.surface", "D", context)
        witness("context.binding", "W", {"contract": contract, "scope": "INDEPENDENT_CLAUSE", "clause": context})
        question("context", "ما البيان المصاحب المستقل في النص؟", record["context"], "stated_context",
                 ("التقرير", record["context"]), ["context.surface", "context.binding"], context)
    formal = None
    if relation in ("even", "odd") and record["proof"]:
        eq = record["proof"]
        match = PROOF.fullmatch(eq)
        bound = bool(match and match[1] == carrier and bool(match[3]) == (relation == "odd"))
        proof_span = span(text, eq)
        witness("proof.surface", "D", proof_span)
        # Equality, its subject, and its parity form must all agree. A false candidate
        # equality removes this proof; it does not prove the opposite parity.
        formal = ntl_core.arithmetic({"text": eq}) if bound else {"answer": None}
        verdict = (formal.get("answer") or {}).get("decision")
        if verdict == "TRUE":
            witness("proof.check", "M", {"checker": "ntl_core.arithmetic", "expression": eq, "decision": verdict})
            question("demonstrated", f"ما الشاهد الحسابي على وصف {carrier}؟", eq, "demonstrated_" + relation,
                     (carrier, record["value"]), ["reading", "proof.surface", "proof.check"], proof_span)
    if any(k not in evidence for k in cuts):
        raise ValueError("Withdrawal must name evidence present in the original reading")
    nodes = graph.report["nodes"]
    prediction = graph_interventions.propose(nodes, cuts)
    before = surviving_nodes(nodes, set())
    after = surviving_nodes(nodes, set(cuts))
    def snapshot(key, live, parents, answer, identity):
        missing = [p for p in parents if p not in live]
        state = "SUPPORTED_IN_SCOPE" if key in live else "WITHDRAWN"
        assessment = number("assessment", identity, content_id([contract, state, missing]), SCHEMA)
        return {"state": state, "answer": answer if key in live else None, "missing": missing, "number": assessment}
    questions = []
    supports = {}
    for key, q, answer, parents, structure, where in specs:
        supports[key] = list(dict.fromkeys(leaf for p in parents for leaf in supports.get(p, [p])))
        identity = content_id([structure, where])
        questions.append({"id": key, "question": q, "sufficient_support": supports[key], "direct_dependencies": parents,
                          "structure_number": structure,
                          "occurrence_number": where, "before": snapshot(key, before, parents, answer, identity),
                          "after": snapshot(key, after, parents, answer, identity)})
    residuals = ["EXTERNAL_OCCURRENCE_UNVERIFIED"]
    if relation in ("even", "odd") and "demonstrated" not in after:
        residuals.append("NO_SURVIVING_VALID_PROOF")
    return {**result, "status": "SOURCE_BOUND", "questions": questions, "evidence": evidence,
            "intervention_proposal": {k: v for k, v in prediction.items() if k != "rows"},
            "predicted_lost": ([r["id"] for r in prediction["rows"] if r["proposed_lost"] and r["id"] in graph.owners
                                 and r["id"] not in evidence] if "rows" in prediction else None),
            "withdrawn": sorted(cuts), "surviving_evidence": sorted(after & evidence.keys()),
            "lost": sorted((before-after) - evidence.keys()),
            "kept": [q["id"] for q in questions if q["id"] in after], "proof_owner": formal, "residuals": residuals}

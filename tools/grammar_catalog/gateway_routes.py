"""Fixed I/O adapters over existing owners. No new linguistic inference law."""
from copy import deepcopy

from .relational import FAMILIES as RELATIONAL_FAMILIES


# These are references into the existing reuse registry, not theorem lists.
# Per-owner validation still runs; these fields only close the outer boundary.
ROUTES = {
    "cognitive.orchestrate": (("rule-routing", "aligned-acquisition", "lexical-denotation", "linguistic-truth", "inflection", "discourse"), ("text",), ("source_id", "lexical_text", "context", "mode", "usage_context")),
    "cognitive.lesson": (("lexical-denotation", "identity", "transition-law", "morphology") + RELATIONAL_FAMILIES, ("lesson",), ()),
    "concept.matrix": (("lexical-denotation", "rule-learning"), ("version",), ()),
    "concept.view": (("lexical-denotation", "mantuq-mafhum"), ("kind", "value", "view", "domain"), ()),
    "neural.propose": (("lexical-denotation", "identity", "morphology"), ("text",), ()),
    "neural.align": (("lexical-denotation", "identity", "morphology"), ("text",), ("source_id",)),
    "neural.graph": (("lexical-denotation", "linguistic-truth", "identity", "transition-law", "morphology") + RELATIONAL_FAMILIES, ("text",), ("source_id", "lexical_text", "context", "usage_context")),
    "lexical.assess": (("lexical-denotation",), ("entry", "target"), ()),
    "lexical.ontolex": (("lexical-denotation",), ("entry", "target"), ()),
    "relations.search": (RELATIONAL_FAMILIES, ("query",), ("limit",)),
    "relations.analyze": (RELATIONAL_FAMILIES, ("text",), ("source_id", "query", "limit", "lexical_text", "context", "temporal", "inference", "bridge", "neural_continuity")),
    "operation": (("identity", "transition-law", "derivation-patterns", "person-reference", "numeric-program", "rule-learning"), (), ()),
    "grammar.search": (("rule-routing", "classical-source-rules"), ("query",), ("kind", "limit")),
    "grammar.route": (("rule-routing", "classical-transforms"), ("query", "frames"), ("budget",)),
    "awamil.search": (("arabic-governors", "classical-source-rules"), ("query",), ("limit", "collection")),
    "awamil.analyze": (("arabic-governors", "discourse", "construction"), ("text",), ("lexical_text", "context")),
    "awamil.check": (("arabic-governors",), ("factor_id", "assignments"), ()),
    "agents.search": (("rule-learning",), ("query",), ("limit",)),
    "agents.transport": (("identity",), ("source_id", "encoding", "hex"), ()),
    "agents.gate": (("arabic-governors", "aligned-acquisition"), (), ()),
    "units.search": (("progressive-units", "unit-discovery"), ("query",), ("limit",)),
    "units.run": (("progressive-units", "identity", "classical-transforms", "morphology"), (), ()),
    "irab.search": (("inflection", "construction", "discourse"), ("query",), ("domain", "limit")),
    "irab.analyze": (("inflection", "construction", "discourse"), (), ()),
    "application.analyze": (("identity", "transition-law", "inflection", "construction", "discourse", "recursive-source"), (), ()),
    "application.temporal": (("discourse",), (), ()),
    "mantuq.search": (("mantuq-mafhum", "classical-source-rules"), ("query",), ("limit",)),
    "mantuq.source": (("mantuq-mafhum", "signed-inference", "classical-source-rules"),
                      ("source", "query", "plan"), ("source_id", "revision", "scope", "context", "time")),
}
SHARED_FAMILIES = ("rule-routing",)


def validate(route, payload):
    if type(route) is not str or route not in ROUTES:
        raise ValueError("Unknown installed gateway route")
    if type(payload) is not dict:
        raise ValueError("Gateway payload must be an object")
    _, required, optional = ROUTES[route]
    if required and (not set(required) <= payload.keys() or set(payload) - set(required + optional)):
        raise ValueError("Unexpected gateway route fields")
    if "query" in required and (type(payload["query"]) is not str or not payload["query"].strip()
                               or len(payload["query"].encode()) > 16384):
        raise ValueError("Expected a bounded nonempty query")
    if "limit" in payload and (type(payload["limit"]) is not int or not 1 <= payload["limit"] <= 100):
        raise ValueError("Expected a positive bounded integer limit")
    if route == "grammar.search" and payload.get("kind") not in (None, "rule", "passage", "item"):
        raise ValueError("Unknown catalogue kind")
    if route == "grammar.route":
        if type(payload["frames"]) is not dict:
            raise ValueError("Expected explicit frames keyed by installed rule")
        if "budget" in payload and (type(payload["budget"]) is not int or payload["budget"] < 0):
            raise ValueError("Expected a nonnegative routing budget")
    if route == "operation":
        from .operation_rag import validate_request
        validate_request(payload)
    if route == "concept.view":
        from tools.lexical_training.concepts import validate as validate_concept
        validate_concept(payload)
    if route == "concept.matrix" and (type(payload["version"]) is not int or payload["version"] != 1):
        raise ValueError("Unknown RAG view version")
    if route == "neural.propose":
        from tools.lexical_training.shared_encoder import validate_request
        validate_request(payload)
    if route == "neural.align":
        from tools.lexical_training.contextual_alignment import validate_request
        validate_request(payload)
    if route == "neural.graph":
        from tools.lexical_training.cognitive_graph import validate_request
        validate_request(payload)
    if route == "cognitive.orchestrate":
        from .orchestration import validate as validate_orchestration
        validate_orchestration(payload)
    if route in ("lexical.assess", "lexical.ontolex"):
        from .lexical_ontolex import validate as validate_lexical
        validate_lexical(payload)
    if route == "relations.analyze":
        from .relational import validate as validate_relations
        validate_relations(payload)
    if route == "mantuq.source":
        if type(payload["source"]) is not str or not payload["source"] or len(payload["source"].encode()) > 65536:
            raise ValueError("Expected bounded original source text")
        if type(payload["plan"]) is not dict:
            raise ValueError("Expected the existing source role plan")
        for name in optional:
            if name in payload and (type(payload[name]) is not str or not payload[name] or len(payload[name].encode()) > 4096):
                raise ValueError("Invalid source context identity")
    return deepcopy(payload)


def execute(route, payload, *, inside_worker=False):
    p = validate(route, payload)
    if route == "cognitive.orchestrate":
        from .orchestration import run
        return run(p)
    if route == "cognitive.lesson":
        from tools.lexical_training.teaching import run_lesson
        return run_lesson(p["lesson"])
    if route == "concept.matrix":
        from tools.lexical_training.rag_views import inventory
        return inventory()
    if route == "concept.view":
        from tools.lexical_training.concepts import evaluate
        return evaluate(p)
    if route == "neural.propose":
        from tools.lexical_training.shared_encoder import propose
        return propose(p)
    if route == "neural.align":
        from tools.lexical_training.contextual_alignment import align
        return align(p)
    if route == "neural.graph":
        from tools.lexical_training.cognitive_graph import analyze
        return analyze(p)
    if route in ("lexical.assess", "lexical.ontolex"):
        from .lexical_ontolex import assess, export
        return (export if route.endswith("ontolex") else assess)(p)
    if route in ("relations.search", "relations.analyze"):
        from .relational import search, analyze
        return search(p["query"], p.get("limit", 5)) if route.endswith("search") else analyze(p)
    if route == "operation":
        from .operation_rag import run, run_inside_worker
        return (run_inside_worker if inside_worker else run)(p)
    if route in ("grammar.search", "grammar.route"):
        from .retrieval import SearchIndex
        index = SearchIndex()
        if route == "grammar.search":
            return index.search(p["query"], kind=p.get("kind"), limit=p.get("limit", 10))
        from .routing import evaluate_candidates
        found = index.search(p["query"], kind="rule", limit=10)
        result = evaluate_candidates(index, [r["id"] for r in found["candidates"]], p["frames"], budget=p.get("budget"))
        return {**result, "retrieval": found}
    if route == "awamil.search":
        from .awamil import AwamilIndex
        return AwamilIndex().search(p["query"], limit=p.get("limit", 5), collection=p.get("collection"))
    if route in ("awamil.analyze", "awamil.check"):
        from .awamil_cli import analyze, check
        return (analyze if route.endswith("analyze") else check)(p)
    if route == "agents.search":
        from tools.lexical_training.agent_plan import search
        return search(p["query"], limit=p.get("limit", 10))
    if route == "agents.transport":
        from .unicode_transport import transcode
        return transcode(p)
    if route == "agents.gate":
        from tools.lexical_training.agent_plan import factor_gate
        return factor_gate(p)
    if route == "units.search":
        from .unit_catalog import search
        return search(p["query"], p.get("limit", 10))
    if route == "units.run":
        from tools.arabic_training.unit_composition import execute as run
        return run(p)
    if route == "irab.search":
        from .irab import IrabIndex
        return IrabIndex(p.get("domain")).search(p["query"], p.get("limit", 5))
    if route == "irab.analyze":
        from .irab import analyze
        return analyze(p)
    if route == "application.analyze":
        from .application import analyze
        return analyze(p)
    if route == "application.temporal":
        from .temporal import evaluate
        return evaluate(p)
    if route == "mantuq.search":
        from tools.mantuq_inference.retrieval import search
        return search(p["query"], limit=p.get("limit", 10))
    from tools.mantuq_inference.source_bound import evaluate_source
    # Native executables are the installed defaults. No request-supplied paths.
    return evaluate_source(p["source"].encode(), p["query"].encode(), p["plan"],
                           **{k: p[k] for k in ROUTES[route][2] if k in p})

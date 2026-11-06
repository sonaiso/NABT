"""RAG views of installed cells, patterns and source-bound lexical declarations."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from tools.evidence_lifecycle_v1 import wire

ROOT = Path(__file__).resolve().parents[2]


def catalog():
    from nabt.derivation import pattern_catalog
    from nabt.word_reader import replay_policy
    from nabt.phonological_modes import replay_policy as sound_policy
    from tools.arabic_training.sign_curriculum import matrix, declared_roles
    from tools.arabic_training.unit_composition import PAIR_BASIS
    from tools.lexical_training.agent_plan import build_report

    plan = build_report()
    patterns, lexical, sounds = pattern_catalog(), replay_policy(), sound_policy()
    signs, roles = matrix(), declared_roles()
    cards = []
    def add(identifier, title, kind, record, owner, source):
        cards.append({"id":identifier,"title":title,"kind":kind,"record":deepcopy(record),
            "owner":owner,"source":source,"record_sha256":sha256(wire(record).encode()).hexdigest(),
            "authority":"SOURCE_NAVIGATION_NOT_APPLICATION_LICENSE"})
    for s in PAIR_BASIS:
        add("shape:"+s,s,"ordered_shape",{"shape":s,"vowel_quantity_not_determined_by_shape":True},
            "progressiveUnitProbe",{"path":"formal/Nabt/ProsodicUnits.lean"})
    for row in signs["cells"]:
        add("cell:"+str(row["cell"]),row["cell_name"],"a116",row,
            "nabt.alphabet",{"path":"tools/arabic_training/sign_curriculum.py"})
    for row in patterns["patterns"]:
        add("pattern:"+row["id"],row["label"],"pattern",row,"nabt.derivation.generate_derivation",
            {"path":"src/nabt/data/derivation_patterns.json","sha256":patterns["table_sha256"]})
    for row in roles["declarations"]:
        add("role:"+row["key"],row["label"],"declared_function",row,"Nabt.AffixFunctions",
            {"path":roles["source_path"],"sha256":roles["source_sha256"]})
    rules = {r["id"]:r for r in lexical["rules"]}
    for row in lexical["entries"]:
        add("lexeme:"+row["id"]," / ".join(f["text"] for f in row["forms"]),"lexeme",row,
            "nabt.word_reader.read_words",{"passages":[rules[k] for k in row["rule_ids"]]})
    passages = {p["passage_id"]:p for p in sounds["passages"]}
    for row in sounds["examples"]:
        add("phonology:"+row["example_id"],row["written_form"],"phonological_example",row,
            "nabt.phonological_modes.realize",{"passages":[passages[k] for k in row["passage_ids"]]})
    consumers = {"units.compose","roles.stem","roles.grammar","root.triliteral","root.quadriliteral",
        "pronouns","built.names","genera","masdar","noun.pre","verb.pre","connector.pre","verb.post","weak.laws"}
    for profile in plan["profiles"]:
        if profile["id"] not in consumers: continue
        for row in profile["topics"]:
            add("topic:"+row["id"],row["label_ar"],"curriculum_topic",row,profile["id"],
                {"framework_sha256":plan["framework_sha256"],"sources":profile["curriculum_sources"]})
    inputs = {p:sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        "tools/grammar_catalog/unit_catalog.py","tools/arabic_training/unit_composition.py",
        "evidence/cognitive_curriculum_v1/learning_framework.json","formal/ProgressiveUnitProbe.lean",
        "formal/Nabt/ProsodicUnits.lean","tools/aligned_acquisition.py",
        "src/nabt/data/derivation_patterns.json","src/nabt/data/source_evidence/word_policy.json",
        "src/nabt/data/source_evidence/phonological_modes_v1.json")}
    return {"schema":"nabt.unit-composition-rag.v1","authority":"RETRIEVAL_ONLY", "cards":cards,
        "counts":dict(Counter(c["kind"] for c in cards)),"inputs":inputs,
        "proof_catalog":plan["proof_catalog"],"agent_profile":"units.compose",
        "proof_navigation":[{k:p[k] for k in ("id","owner_modules","declaration_ids","runtime_paths","open_obligations")}
                            for p in plan["profiles"] if p["id"] in consumers],
        "proof_mapping_scope":"RELATED_OWNER_MODULE_NOT_TOPIC_COMPLETENESS_OR_ADAPTER_REFINEMENT",
        "next_consumers":sorted(consumers-{"units.compose"}),
        "installed_pattern_count":len(patterns["patterns"]),"future_pattern":patterns["future_pattern"],
        "lexical_or_grammatical_completeness_claimed":False}


def search(query,limit=10):
    from .retrieval import SearchIndex, tokens
    data = catalog()
    class UnitIndex(SearchIndex):
        def __init__(self):
            self._catalog = data
            self.catalog_sha256 = sha256(wire(data).encode()).hexdigest()
            self._docs = {}
            for card in data["cards"]:
                self._add("item",card["id"],card["title"]+" "+wire(card["record"]),card)
            self._tf = {k:Counter(tokens(d["search_text"])) for k,d in self._docs.items()}
    result = UnitIndex().search(query,limit=limit)
    result["source_retrieval"] = SearchIndex().search(query,limit=limit)
    result["ranking_executes_nothing"] = True
    return result


def curriculum():
    from nabt.derivation import pattern_catalog
    from tools.arabic_training.unit_composition import SYLLABLE_TARGETS
    patterns = pattern_catalog()["patterns"]
    stages = [{"id":"ordered_quotas_"+str(n),"request":{"op":"enumerate","max_c":n,"max_v":n,"include_pairs":False},
               "criterion":"Native exhaustion; counts are independently binomial; no Arabic role inferred"}
              for n in range(1,5)] + [
              {"id":"syllable_products","request":{"op":"shape","parts":["CV","CVV"]},
               "criterion":"Preserve order, repeated parts and all available binary trees"},
              {"id":"a116_cartesian_page","request":{"op":"cell_page","length":2,"limit":16},
               "criterion":"Page exact ordered A116 addresses; no claim that unseen pages were measured"},
              {"id":"acquired_cells","request":{"op":"compose","parts":["كَ","ا","تِبُ"],"separators":["",""]},
               "criterion":"Fresh acquired pieces; 97-state effect equality; no boundary crossing"}]
    splits = {"train":{3:"كتب",4:"دحرج"},"dev":{3:"نصر",4:"بعثر"},"test":{3:"درس",4:"زلزل"}}
    examples = [{"split":split,"pattern_id":p["id"],"source_contract":p["source_contract"],
        "request":{"op":"generate","root":roots[p["arity"]],"pattern_id":p["id"],
                   "ending":p["endings"][0] if p["endings"] else ""},
        "root_basis":"SUPPLIED_FORMAL_RADICALS_NOT_LEXICAL_ATTESTATION"}
        for split,roots in splits.items() for p in patterns]
    return {"schema":"nabt.unit-composition-curriculum.v1","stages":stages,"examples":examples,
        "split_axis":"RADICAL_TUPLE_HELD_OUT; PATTERNS_ARE_SHARED", "patterns":len(patterns),
        "syllable_targets":list(SYLLABLE_TARGETS),"examples_are_attested_words":False,
        "model_weights_trained":False,"linguistic_mastery_measured":False}

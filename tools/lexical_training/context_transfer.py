"""Learn occurrence-local cue proposals from a contrastive few-shot lesson."""
from hashlib import sha256

from nabt.alphabet import CARRIERS
from nabt.codec import encode_cells
from tools import aligned_acquisition, evidence_lifecycle_v1 as wire
from tools.grammar_catalog.operations import exact_terms

SCHEMA = "ntl.context-transfer.v1"
RESULT = "ntl.context-transfer-result.v1"
LABELS = ("literal", "figurative")
MARKS = frozenset("ًٌٍَُِّْٰ")


def bare(word):
    return "".join(c for c in word if c not in MARKS)


def identifier(text):
    return sha256(text.encode("utf-8")).hexdigest()


def arabic_word(surface):
    return bool(surface) and all(c in CARRIERS or c in "أإآؤئٱىة" or c in MARKS for c in surface)


def bounded_list(value, name, low, high):
    if type(value) is not list or not low <= len(value) <= high:
        raise ValueError(f"{name} requires {low}..{high} items")


def clause(text, term):
    """Read one affirmative clause. Preserve spelling and byte offsets for witnesses."""
    wire._text(text, "clause", 640, content=True)
    tokens = exact_terms(text)
    hits = [w for w in tokens if bare(w["surface"]) == term]
    if len(hits) != 1:
        return None, [], "TARGET_MISSING_OR_MULTIPLE"
    target = hits[0]
    body = text.strip().removesuffix(".").strip()
    if (not body or any(not (c == " " or arabic_word(c)) for c in body)
            or any(bare(t["surface"]) in {"لا","ليس","ليست","لم","لن","لست","ما","غير","دون","بل",
                                         "لو","إن","إذا","هل","قال","قالت","ربما"} for t in tokens)):
        return target, [], "OUTSIDE_CLAUSE_PROFILE"
    return target, [w for w in tokens if w is not target], None


def checked_address(text, target):
    """The occurrence can be complete even when another word is unvocalized."""
    report = aligned_acquisition.acquire(text, source_id="ntl-episode", revision=identifier(text),
                                         scope="target", ending="wasl")
    if not report["verified"]:
        return {"status": report["status"]}
    for word in report["acquisition"]["words"]:
        if target["utf8_span"] == [word["byte_start"], word["byte_end"]] and word["status"] == "ACQUIRED":
            cells = word["cells"]
            return {"status":"ACQUIRED", "cells":cells, "number":str(encode_cells(cells)), "mode":"wasl",
                    "alphabet_id":aligned_acquisition.ALPHABET_ID, "domain":"NABT_sequence_b116_big_endian"}
    return {"status":"NO_COMPLETE_TARGET_READING"}


def learn(term, examples):
    # A hypothesis is one exact cue surface shared by every example of a label
    # and absent from every contrasting example. Do not fit on probe text.
    seen = set()
    grouped = {k: [] for k in LABELS}
    explanations = {k: [] for k in LABELS}
    for example in examples:
        extra = ("meaning","relation") if type(example) is dict and "meaning" in example else ()
        wire._fields(example, ("text","label",*extra), "demonstration")
        label = example["label"]
        if label not in LABELS:
            raise ValueError("Unknown example label")
        description = None
        if extra:
            for key in extra:
                wire._text(example[key], key, 192)
            description = (example["meaning"], example["relation"])
        explanations[label].append(description)
        _, words, error = clause(example["text"], term)
        if error:
            raise ValueError("Unusable example: " + error)
        normalized = tuple(t["surface"] for t in exact_terms(example["text"]))
        if normalized in seen:
            raise ValueError("Duplicate or conflicting demonstration")
        seen.add(normalized)
        grouped[label].append({w["surface"] for w in words})
    cues = {}
    for label, other in (LABELS, LABELS[::-1]):
        cues[label] = set()
        if len(set(map(frozenset, grouped[label]))) >= 2 and len(set(map(frozenset, grouped[other]))) >= 2:
            cues[label] = set.intersection(*grouped[label]) - set.union(*grouped[other])
    descriptions = {}
    for label, entries in explanations.items():
        if entries and entries[0] and len(set(entries)) == 1:
            descriptions[label] = dict(zip(("meaning","relation"), entries[0]))
    return cues, descriptions, seen


def decide(text, term, cues, descriptions, seen):
    target, words, error = clause(text, term)
    if tuple(t["surface"] for t in exact_terms(text)) in seen:
        raise ValueError("A probe repeats a demonstration")
    row = {"text_sha256":identifier(text), "target":target, "decision":"UNRESOLVED",
           "matches":[], "authority":"LEARNED_PROPOSAL_ONLY"}
    if error:
        return {**row,"reason":error}
    address = checked_address(text, target)
    row["address"] = address
    if address["status"] != "ACQUIRED":
        return {**row,"reason":address["status"]}
    matches = [{"label":label, **word} for word in words for label in LABELS
               if word["surface"] in cues[label]]
    labels = {w["label"] for w in matches}
    row["matches"] = matches
    if len(labels) == 2:
        return {**row,"decision":"CONFLICT","reason":"COMPETING_CONTEXT_CUES"}
    if not labels:
        return {**row,"reason":"NO_LEARNED_CUE"}
    label = labels.pop()
    if {w["surface"] for w in matches} != cues[label]:
        return {**row,"reason":"INDISTINGUISHABLE_TRAINING_CUES"}
    return {**row,"decision":label,"reason":"DEMONSTRATION_BOUND_CUE",
            "interpretation_from_teacher":descriptions.get(label)}


def choose_query(pool, probes, term, cues, descriptions, seen):
    """Pick a question that best splits competing same-label cue hypotheses."""
    best, best_score = None, 0
    for i, text in enumerate(pool):
        row = decide(text, term, cues, descriptions, seen)
        if text in probes:
            raise ValueError("Query pool overlaps probes")
        if row["reason"] != "INDISTINGUISHABLE_TRAINING_CUES":
            continue
        label = row["matches"][0]["label"]
        support = len({w["surface"] for w in row["matches"]})
        score = min(support, len(cues[label]) - support)
        if score > best_score:
            best_score = score
            best = {"pool_index":i,"text":text,"text_sha256":row["text_sha256"],
                    "split":[support,len(cues[label])-support], "question":"ما استعمال اللفظ هنا؟"}
    return best


def run(lesson):
    optional = ("query_pool",) if "query_pool" in lesson else ()
    wire._fields(lesson, ("schema","term","examples","probes",*optional), "context transfer lesson")
    term = lesson["term"]
    wire._text(term, "term", 64)
    if not arabic_word(term) or bare(term) != term:
        raise ValueError("Expected one unmarked Arabic target word")
    examples, probes = lesson["examples"], lesson["probes"]
    bounded_list(examples,"examples",0,12)
    bounded_list(probes,"probes",1,24)
    cues, descriptions, seen = learn(term, examples)
    predictions = [decide(text,term,cues,descriptions,seen) for text in probes]
    query = None
    if optional:
        pool = lesson["query_pool"]
        bounded_list(pool,"query_pool",1,12)
        query = choose_query(pool, set(probes), term, cues, descriptions, seen)
    return {"schema":RESULT, "status":"COURSE_SESSION","term":term,
            "scope":"contrastive exact lexical cues in one clause and a natively checked A116 target",
            "hypotheses":{k:sorted(v) for k,v in cues.items()},
            "demonstrations":[{"sha256":identifier(e["text"]), "label":e["label"]} for e in examples],
            "predictions":predictions, "next_query":query, "world_truth_established":False, "semantic_license":False}


# The regular reader uses installed worked examples only; user-authored lessons
# have no persistent effects. A request cannot insert a label into text.read.
SEA = {"term":"بحر", "examples":[
    {"text":"هذا بَحْرٌ تتلاطم أمواجه.","label":"literal","meaning":"الماء الكثير","relation":"الوضع اللغوي"},
    {"text":"هناك بَحْرٌ تسكن أمواجه.","label":"literal","meaning":"الماء الكثير","relation":"الوضع اللغوي"},
    {"text":"هذا بَحْرٌ في العلم.","label":"figurative","meaning":"سعة علم الموصوف","relation":"المشابهة في السعة"},
    {"text":"هناك بَحْرٌ ينشر العلم.","label":"figurative","meaning":"سعة علم الموصوف","relation":"المشابهة في السعة"}]}


def reader_proposal(text):
    if not any(bare(t["surface"]) == SEA["term"] for t in exact_terms(text)):
        return None
    if len(text.encode("utf-8")) > 640:
        return None
    cues, descriptions, _ = learn(SEA["term"], SEA["examples"])
    # Reading a worked example is legitimate, but never a held-out success.
    row = decide(text, SEA["term"], cues, descriptions, set())
    row["from_worked_example"] = text in [e["text"] for e in SEA["examples"]]
    row["demonstrations"] = [identifier(e["text"]) for e in SEA["examples"]]
    return row

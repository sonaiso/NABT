"""A bounded NTL Arabic course. Installed books own evidence; learned pointers only propose."""
from hashlib import sha256
import json
import re

from nabt.source_lexicon import SourceIdentityError, SourceLexicon
from tools import lexical_testimony
from tools.grammar_catalog import classical_roles
from tools.grammar_catalog.operations import ROOT, exact_terms
from . import classical_attention

SCHEMA = "ntl.classical-books.v1"
RESULT = "ntl.classical-books-result.v1"
BOOKS = ("sibawayhi", "qatr", "maqayis")
DOMAIN_FILE = "tools/lexical_training/data/classical_books_domains_v1.json"
DEFAULT_DOMAIN = "transitive-roles"


def domains():
    catalog = json.loads((ROOT / DOMAIN_FILE).read_bytes())
    if catalog["schema"] != "ntl.classical-book-domains.v1":
        raise ValueError("Unrecognized domain catalog")
    for domain in catalog["domains"].values():
        families = set(domain["question_families"])
        # The dictionary, context and world questions are common to this course.
        if families not in ({"dictionary", "sense", "world"}, {"dictionary", "sense", "world", "roles"}):
            raise ValueError("Question family requires an installed evaluator")
        required_books = BOOKS if "roles" in families else ("maqayis",)
        if set(domain["books"]) != set(required_books):
            raise ValueError("Domain sources do not cover the evaluated questions")
    return catalog["domains"]


POLICIES = ("first_noun", "second_noun", "nominative_sign")
MAX_BYTES = 512


def source(lesson):
    if type(lesson) is not dict or lesson.get("schema") != SCHEMA:
        raise ValueError("Invalid classical lesson")
    encodings = [key for key in ("bits", "utf8_hex", "text") if key in lesson]
    if len(encodings) != 1:
        raise ValueError("Expected one source representation")
    field = encodings[0]
    required = {"schema", "source_id", field}
    if not required <= lesson.keys() or lesson.keys() - required - {"withdraw", "examples", "candidate_heading", "domain"}:
        raise ValueError("Use one source representation and only declared lesson fields")
    domain = lesson.get("domain", DEFAULT_DOMAIN)
    if type(domain) is not str or domain not in domains():
        raise ValueError("Expected an installed course domain")
    identity = lesson["source_id"]
    if type(identity) is not str or not identity.strip() or len(identity.encode()) > 120:
        raise ValueError("Expected a bounded source identity")
    text = lesson[field]
    if field == "bits":
        if type(text) is not str or len(text) > 8 * MAX_BYTES or not re.fullmatch(r"(?:[01]{8})+", text):
            raise ValueError("Expected complete eight-bit bytes in transmission order")
        text = bytes(int(text[i:i + 8], 2) for i in range(0, len(text), 8)).decode("utf-8", errors="strict")
    elif field == "utf8_hex":
        if type(text) is not str or len(text) > 2 * MAX_BYTES or not re.fullmatch(r"(?:[0-9a-f]{2})+", text):
            raise ValueError("Expected canonical lower-case UTF-8 hex bytes")
        text = bytes.fromhex(text).decode("utf-8", errors="strict")
    examples = lesson.get("examples", [])
    if type(examples) is not list or len(examples) > 4:
        raise ValueError("Expected at most four example texts")
    for item in [text, *examples]:
        if type(item) is not str or not item.strip() or len(item.encode()) > MAX_BYTES:
            raise ValueError("Expected bounded original text")
    if examples and "roles" not in domains()[domain]["question_families"]:
        raise ValueError("Role demonstrations require a domain that teaches roles")
    if len(set(examples)) != len(examples):
        raise ValueError("Repeated demonstration")
    if "candidate_heading" in lesson:
        candidate = lesson["candidate_heading"]
        if type(candidate) is not str or not re.fullmatch(r"[ء-غف-ي]{2,5}", candidate):
            raise ValueError("Expected an unmarked candidate dictionary heading")
    cuts = lesson.get("withdraw", [])
    if type(cuts) is not list or any(type(k) is not str or k not in BOOKS for k in cuts) or len(set(cuts)) != len(cuts):
        raise ValueError("Expected unique installed book IDs")
    return text, field


def syntax(text, withdrawn):
    if set(withdrawn).intersection(("sibawayhi", "qatr")):
        return None, "GRAMMAR_WITNESS_WITHDRAWN"
    try:
        graph = classical_roles.analyze(text)
    except (OSError, ValueError) as exc:
        return None, "GRAMMAR_EVIDENCE_UNAVAILABLE:" + type(exc).__name__
    return (graph, "BOUND") if graph else (None, "ROLE_BINDING_MISSING_OR_OUTSIDE_PROFILE")


def lexicon(terms, withdrawn, alignments):
    targets = [t for t in terms if t["surface"] in alignments]
    if "maqayis" in withdrawn:
        return {"status": "BOOK_WITHDRAWN", "entries": []}
    if not targets:
        return {"status": "NO_EXACT_FORM_ALIGNMENT", "entries": []}
    try:
        index = SourceLexicon.load("maqayis", ROOT / lexical_testimony.SOURCES["maqayis"][2])
    except (OSError, SourceIdentityError) as exc:
        return {"status": "DICTIONARY_UNAVAILABLE", "reason": type(exc).__name__, "entries": []}
    entries = []
    for target in targets:
        heading = alignments[target["surface"]]
        entries.append({"occurrence": target, "teaching_alignment": heading,
                        "owner": index.lookup_exact(heading)})
    return {"status": "LOOKED_UP", "entries": entries}


def question(identifier, prompt, decision, answer, evidence):
    return {"id": identifier, "question": prompt, "decision": decision,
            "answer": answer, "basis": evidence}


def opening_statement(entry):
    """Display the first sentence in one of the aligned entries, with exact source bytes."""
    raw = entry["raw_block"].encode()
    start = entry["heading_end_byte"] - entry["start_byte"]
    if raw[start:start + 2] != b"# ":
        return None
    start += 2
    stop = raw.find(b".", start, start + 512)
    if stop < 0:
        return None
    quote = raw[start:stop + 1]
    return {"quote": quote.decode(), "sha256": sha256(quote).hexdigest(),
            "utf8_span": [entry["start_byte"] + start, entry["start_byte"] + stop + 1]}


def role_questions(text, graph, reason):
    rows = []
    frame = classical_roles.source_frame(text)
    arguments = frame[0][-2:] if frame else []
    for role, ar in (("subject", "الفاعل"), ("object", "المفعول به")):
        proof = [] if not graph else [
            {"witnesses": [graph["reading"][role]["rule_ref"], "governed_roles", "object_first", "predication"],
             "occurrence": graph["reading"][role]["term"],
             "sign_span": graph["reading"][role]["sign_span"], "owner": "syntax_owner"}]
        argument = graph["reading"][role]["term"] if graph else None
        rows.append(question(role, f"أيّ لفظ شغل دور {ar} في هذه القراءة؟",
                             "SUPPORTED" if graph else "UNKNOWN",
                             argument["surface"] if argument else None, proof or [reason]))
        for i, term in enumerate(arguments):
            decision = "UNKNOWN" if not graph else (
                "SUPPORTED" if term["utf8_span"] == argument["utf8_span"] else "REFUTED")
            rows.append(question(f"{role}.{i}", f"هل «{term['surface']}» في هذا الموضع هو {ar}؟",
                                 decision, term, proof or [reason]))
    reading = graph["reading"] if graph else None
    rows.append(question("utterance", "ما أسلوب الجملة في هذا الإطار؟",
                         "SUPPORTED" if reading else "UNKNOWN",
                         {"assert": "خبر", "ask": "استفهام"}.get(reading["force"]) if reading else None,
                         [{"owner": "syntax_owner", "cue": reading["cue"]}] if reading else [reason]))
    return rows


def learner_choice(policy, text, bank):
    frame = classical_roles.source_frame(text)
    if not frame:
        return None
    terms = frame[0][-2:]
    if policy == "nominative_sign":
        if bank is None:
            return None
        options = []
        for term in terms:
            noun = classical_roles.noun_reading(term, bank["nouns"])
            if noun and any(row["case_name"] == "raf" for row in noun["case_rows"]):
                options.append(term)
        return options[0]["utf8_span"] if len(options) == 1 else None
    return terms[0 if policy == "first_noun" else 1]["utf8_span"]


def learn(examples, probe, withdrawn):
    """Fit only on owner-licensed demonstration spans. No probe answer enters elimination."""
    policies = list(POLICIES)
    history = []
    try:
        bank = classical_roles.inventory() if "qatr" not in withdrawn else None
    except (OSError, ValueError):
        bank = None
    for text in examples:
        teacher, reason = syntax(text, withdrawn)
        before = policies[:]
        if teacher:
            label = teacher["reading"]["subject"]["term"]["utf8_span"]
            policies = [p for p in before if learner_choice(p, text, bank) == label]
        history.append({"source_sha256": sha256(text.encode()).hexdigest(),
                        "teacher": teacher, "status": reason, "before": before, "after": policies[:]})
    votes = {p: learner_choice(p, probe, bank) for p in policies}
    choices = list(votes.values())
    unanimous = choices[0] if choices and all(s == choices[0] for s in choices) else None
    return {"method": "FINITE_CONTRASTIVE_ELIMINATION", "history": history, "survivors": policies,
            "probe_votes": votes, "agreed_proposal": unanimous, "seen_exact_text": probe in examples,
            "authority": "NONE"}


def run(lesson):
    text, representation = source(lesson)
    raw = text.encode("utf-8")
    terms = exact_terms(text)
    cuts = lesson.get("withdraw", [])
    domain_id = lesson.get("domain", DEFAULT_DOMAIN)
    domain = domains()[domain_id]
    teach_roles = "roles" in domain["question_families"]
    graph, reason = syntax(text, cuts) if teach_roles else (None, "OUTSIDE_DOMAIN")
    lex = lexicon(terms, cuts, domain["alignments"])
    rows = role_questions(text, graph, reason) if teach_roles else []
    for i, rec in enumerate(lex["entries"]):
        owner = rec["owner"]
        found = owner["status"] == "FOUND_SOURCE_HEADINGS"
        rows.append(question(f"heading.{i}", f"إلى أي مدخل تردّ «{rec['occurrence']['surface']}» في جدول هذا الدرس؟",
                             "SUPPORTED" if found else "UNKNOWN", owner["query"] if found else None,
                             [f"/lexical_owner/entries/{i}", rec["occurrence"]]))
        if found:
            statements = [opening_statement(e) for e in owner["alternatives"]]
            complete = all(statements)
            rows.append(question(f"opening.{i}", f"بِمَ افتتح ابن فارس مدخل «{owner['query']}»؟",
                                 "SUPPORTED" if complete else "UNKNOWN",
                                 statements if complete else None, [f"/lexical_owner/entries/{i}"]))
        if "candidate_heading" in lesson:
            candidate = lesson["candidate_heading"]
            rows.append(question(f"matches_heading.{i}",
                                 f"هل «{candidate}» هو المدخل المحاذي لهذا الوقوع في الدرس؟",
                                 ("SUPPORTED" if candidate == owner["query"] else "REFUTED") if found else "UNKNOWN",
                                 owner["query"] if found else None, [f"/lexical_owner/entries/{i}"]))
    if not lex["entries"]:
        rows.append(question("heading", "أي مدخل معجمي أمكن ربطه باللفظ؟", "UNKNOWN", None, [lex["status"]]))
    if not lex["entries"] and "candidate_heading" in lesson:
        rows.append(question("matches_heading", f"هل ثبتت محاذاة «{lesson['candidate_heading']}»؟",
                             "UNKNOWN", None, [lex["status"]]))
    rows.append(question("sense", "ما مراد المتكلم في هذا الوقوع عند الاكتفاء بالشاهد المعجمي؟",
                         "UNKNOWN", None, ["OCCURRENCE_LOCAL_SENSE_WITNESS_REQUIRED"]))
    rows.append(question("world", "هل وقع الحدث في الخارج؟", "UNKNOWN", None, ["INDEPENDENT_WORLD_WITNESS_REQUIRED"]))
    return {"schema": RESULT, "status": "COURSE_SESSION", "request": lesson, "execution_measured": True,
            "source": {"text": text, "encoding": representation, "sha256": sha256(raw).hexdigest(),
                       "utf8_hex": raw.hex(), "terms": terms},
            "syntax_owner": graph, "syntax_status": reason, "lexical_owner": lex, "questions": rows,
            "domain": {"id": domain_id, **domain},
            "learning": learn(lesson.get("examples", []), text, cuts) if teach_roles else {"status": "OUTSIDE_DOMAIN"},
            "role_attention": classical_attention.propose(text) if teach_roles else {"status": "OUTSIDE_DOMAIN"},
            "scope": domain["scope"],
            "world_truth_established": False, "complete_arabic_understanding": False}

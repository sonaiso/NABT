"""Text-only gateway view. Keep original, conditional, and cited readings distinct."""
from collections import Counter
from hashlib import sha256

from nabt.corpus_evidence import buckwalter_to_arabic, lookup_key
from nabt.corpus_sources import read_corpus
from tools.arabic_training.source_reading import compatible
from tools.linguistic_truth import runtime as usage
from . import orchestration, usage_witness
from .operations import ROOT, exact_terms

LEXICON = "examples/construction_training.tsv"
LEXICON_SHA = "06ff1e42fb60dfc45b49df9d029e197314a791f72c683ae8e692fc1e2e6f4e0e"
COMMENTARY = "src/nabt/data/source_evidence/sabban.txt"
COMMENTARY_SHA = "8b9e86da786cf65e7b32498b2524ee48a8dcf9f61b59e1bbc32b99ce7db5b396"
PROFILES = {"linguistic": "اللغوي", "customary": "العرفي", "sharia": "الشرعي"}
LAYERS = {"orthography": "الرسم والقراءة الحرفية", "morphology": "الصرف", "word_kind": "نوع الكلمة",
          "syntax": "التركيب", "mantuq": "المنطوق", "concept": "تطبيق المفهوم"}


def pinned(path, expected):
    raw = (ROOT / path).read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError("Changed text-reading evidence: " + path)
    return raw


def lexical_context(text):
    """Only names actually mentioned once become discourse-local placeholders."""
    raw = pinned(LEXICON, LEXICON_SHA)
    corpus = read_corpus(raw, format="qac", source_id="reading_lexicon")
    names = {}
    for record in corpus["records"]:
        if record["valid"] and record["fields"]["TAG"] == "PN":
            key = lookup_key(buckwalter_to_arabic(record["fields"]["FORM"]))
            names.setdefault(key, []).append(record["identity"])
    tokens = exact_terms(text)
    keys = [lookup_key(t["surface"]) for t in tokens]
    counts = Counter(keys)
    mentions = []
    for token, name in zip(tokens, keys):
        if name in names and counts[name] == 1:
            start, stop = token["utf8_span"]
            mentions.append({"id": f"name_{start}_{stop}", "name": name, "span": [start, stop],
                             "lexical_records": names[name]})
    return raw.decode(), mentions


def card(scope, degree, understood, why, pending, **evidence):
    return {"scope": scope, "degree": degree, "understood": understood, "why": why,
            "unresolved": pending, "evidence": evidence}


def predications(report, names, *, branch=None):
    owner = report["owner_reports"].get("mantuq")
    if not owner or not any(r["name"] == "mantuq" and r["closed"] for r in report["dispatch_ledger"]):
        return []
    source = report["source"]["text"]
    degree = "منطوق في التحليل المرخّص"
    premise = ""
    pending = "تعيين الشخص في الخارج وصدق الوصف يحتاجان شاهدًا مستقلاً."
    if branch:
        edits = [m for m in branch["mappings"] if m["spelling_edit"]]
        degree = "قراءة مشروطة بالضبط"
        if edits:
            degree = "قراءة مشروطة بتغيير الرسم"
            changes = "، ".join(f"من «{m['observed']}» إلى «{m['proposed']}»" for m in edits)
            premise = f"تفترض هذه القراءة تغيير الرسم {changes}. "
            pending = "لم يثبت خطأ الرسم الأصلي أو أن الكاتب أراد هذا التغيير. " + pending
    acts = {row["clause_id"]: row["force"] for row in owner["speech_acts"]}
    rows = []
    for claim in owner["claims"]:
        proofs = claim["proofs"]
        if (claim["predicate_kind"] != "property" or len(claim["args"]) != 1
                or claim["args"][0] not in names or not proofs
                or claim["time"] or claim["place"] or claim["restriction"]
                or any(acts.get(pr["clause_id"]) != "ASSERT" for pr in proofs)):
            continue
        bearer = names[claim["args"][0]]
        action = "يُسند" if claim["positive"] else "ينفي إسناد"
        rows.append(card("conditional_predication" if branch else "source_predication",
                         degree,
                         f"{action} النصّ صفة «{claim['predicate']}» إلى «{bearer}».",
                         premise + f"قُرئت «{source}» خبرًا في معجم القراءة المحلي، وربط محلّل التركيب المحمول بصاحب الاسم.",
                         pending,
                         claim_id=claim["claim_id"], proofs=proofs, reading_text=source,
                         conditional_source=branch, world_truth_established=False))
    return rows


def acquisition_checks(report):
    """Yield owner receipts at their original or proposed spelling and source span."""
    shape = report["owner_reports"]["orthography"]
    if shape["schema"] == "nabt.exact-unit-owner-transport.v1":
        from tools.arabic_training.unit_composition import read_json
        shape = read_json(shape["owner_json"].encode())
    for run in shape["result"]["written_runs"]:
        for word in run["owner_result"]["words"]:
            yield word.get("acquisition_owner", {}), run["source_span"], run["surface"], word["text"]
    for row in report.get("source_reading", {}).get("occurrences", []):
        for alt in row["alternatives"]:
            yield alt["acquisition_owner"], row["source_span"], row["surface"], alt["surface"]


ACQUISITION_FAILURES = {
    "VERIFICATION_UNAVAILABLE": "تعذّر تشغيل فاحص القراءة.",
    "VERIFICATION_FAILED": "اختلفت نتيجة الفاحص عند إعادة التحقق.",
    "SOURCE_EVIDENCE_UNAVAILABLE": "تعذّر التحقق من شاهد القراءة المثبّت.",
    "RESOURCE_EXHAUSTED": "استنفد فحص القراءة الموارد المتاحة.",
}


def grammar_failures(grammar):
    # One outage may affect many hypotheses. Keep their locations in one card
    # per owner and cause, including failures found only on a derived source.
    failures = {}
    reports = [grammar] + [b["result"] for b in grammar["conditional_readings"]]
    for report in reports:
        for owner, span, observed, proposed in acquisition_checks(report):
            status = owner.get("status")
            if status not in ACQUISITION_FAILURES:
                continue
            reason = owner.get("error") or owner.get("acquisition", {}).get("error") or status
            affected = failures.setdefault((owner["schema"], status, reason), {})
            key = (span["source_id"], span["start"], span["end"], proposed)
            affected[key] = {"span": span, "observed": observed, "proposed": proposed}
    rows = []
    for (schema, status, reason), affected in failures.items():
        locations = list(affected.values())
        first = locations[0]
        where = f"عند فحص «{first['proposed']}»"
        if first["observed"] != first["proposed"]:
            where += f" المقترحة للرسم «{first['observed']}»"
        rows.append(card("technical", status, ACQUISITION_FAILURES[status],
                         f"{where} سجّل الفاحص {reason}.",
                         "يتوقف الحكم على الأوجه المتأثرة إلى أن يكتمل فحصها.",
                         owner_schema=schema, reason=reason, locations=locations))
    recovery = grammar["source_reading"]
    if recovery["branch_status"] == "RESOURCE_LIMIT_ALL_WORD_ALTERNATIVES_RETAINED":
        rows.append(card("technical", "RESOURCE_EXHAUSTED", "تجاوز عدد القراءات المركّبة حدّ الفحص.",
                         f"بلغ عدد تراكيب البدائل {recovery['candidate_product']}.",
                         "حُفظت بدائل الكلمات وبقي فحص تراكيبها معلّقًا.",
                         reason=recovery["branch_status"], candidate_product=recovery["candidate_product"]))
    return rows


def profile_reports(text, source_id, report):
    if not report["native_checked"] or not report["acquisition_scan_complete"]:
        return {}
    profiles = {branch["profile_id"] for occurrence in report["occurrences"]
                for branch in occurrence["profile_readings"]
                if branch["conditional_result"]["certified_sense_ids"]}
    return {profile: usage_witness.run({"text": text, "source_id": source_id,
                                       "usage_context": {"profile_id": profile}})
            for profile in sorted(profiles)}


def use_cards(report, profiles):
    rows = []
    if not report["acquisition_scan_complete"] or report["status"] in {
            "RESOURCE_EXHAUSTED", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE", "INVALID_INPUT"}:
        return [card("technical", report["status"], "تعذّر استكمال فحص الاستعمال.",
                     str(report.get("reason")), "درجة الدلالة معلّقة.")]
    for profile, bridge in profiles.items():
        if bridge["status"] in {"SOURCE_UNAVAILABLE", "RESOURCE_EXHAUSTED", "VERIFICATION_UNAVAILABLE", "IDENTITY_UNAVAILABLE"}:
            rows.append(card("technical", bridge["status"], "تعذّر التحقق من شاهد الاستعمال.",
                             f"فرع الاصطلاح {PROFILES[profile]}: {bridge['reason']}",
                             "الهوية أو الفاحص غير متاح."))
    for item in report["occurrences"]:
        gloss = {s["sense_id"]: s["gloss"] for s in item["available_senses"]}
        def labels(ids):
            return " و".join(gloss[i] for i in ids)
        span = item["span"]
        ev = {"occurrence": item["occurrence_id"], "term": span, "cue": item["cue_span"],
              "available": item["available_senses"], "selected": item["selected_sense_ids"],
              "excluded": item["excluded_sense_ids"], "profile_hypotheses": report["pending_profiles"]}
        if not item["native_checked"]:
            rows.append(card("technical", "إرجاء", "تعذّر فحص هذا الوقوع.", span["raw_text"],
                             "تبقى المعاني مرشّحة.", **ev))
            continue
        if item["signed_conflict"]:
            rows.append(card("lexical_conflict", "تعارض", "تعارض الإثبات والنفي في هذا الاستعمال.",
                             item["clause_span"]["raw_text"], "تعيين المراد معلّق.", **ev))
            continue
        chosen = item["selected_sense_ids"]
        if not chosen:
            literal_senses = {c["sense_id"] for c in item["candidates"]
                              if c["use_kind"] == "literal" and c["convention"] == "linguistic"
                              and c["candidate"]["designation"]["origin"] == "original"}
            polysemy = "اللفظ مشترك في الوضع اللغوي المسجّل. " if len(literal_senses) > 1 else ""
            rows.append(card("lexical_alternatives", "مراد غير معيّن",
                             polysemy + f"في الجرد للفظ «{item['expression']}» الأوجه الآتية: {labels(gloss)}.",
                             f"ورد «{span['raw_text']}» دون قرينة موجبة كافية لاختيار المراد.",
                             "تعدد المدخلات المعجمية لا يثبت إرادة جميعها.", **ev))
            continue
        understood = ("صرّح المتكلم بإرادة المعنيين معًا" if len(chosen) == 2 else
                      "صرّح المتكلم بإرادة هذه المعاني" if len(chosen) > 2 else
                      "صرّح المتكلم بإرادة معنى") + " «" + labels(chosen) + "»."
        rows.append(card("expressed_intent", "متعيّن في عبارة التصريح المضبوطة", understood,
                         item["cue_span"]["raw_text"], "القصد المنقول مربوط بهذه العبارة.",
                         **ev))
        accepted_senses = set()
        for profile, bridge in profiles.items():
            for application in bridge["applications"]:
                if application["owner_occurrence_id"] != item["occurrence_id"]:
                    continue
                # Follow the existing owner's occurrence/candidate pointer, including lexical aliases.
                _, _, occurrence_index, _, candidate_index = application["owner_result_ref"].strip("/").split("/")
                candidate = bridge["owner_report"]["occurrences"][int(occurrence_index)]["candidates"][int(candidate_index)]
                use = "مجازية" if application["use_kind"] == "figurative" else "حقيقية"
                reason = item["cue_span"]["raw_text"]
                if application["literal_excluded"]:
                    reason += f"؛ وفي الموضع نفسه استُبعد «{labels(item['excluded_sense_ids'])}»."
                rows.append(card("conditional_use", "استعمال مشروط بالاصطلاح",
                                 f"في الاصطلاح {PROFILES[profile]} القراءة {use} للمعنى «{candidate['gloss']}».",
                                 reason, "اصطلاح المتكلم غير معيّن من خارج العبارة؛ تبقى الفروع الأخرى محفوظة.",
                                 profile_id=profile, use_kind=application["use_kind"], sense_id=candidate["sense_id"],
                                 witness_id=application["witness_id"], **ev))
                accepted_senses.add(candidate["sense_id"])
        for sense in chosen:
            if sense in accepted_senses:
                continue
            missing_exclusions = sorted({c["candidate"]["designation"]["sense"] for c in item["candidates"]
                                         if c["sense_id"] == sense and c["use_kind"] == "figurative"}
                                        - set(item["excluded_sense_ids"]))
            pending = "لم تكتمل الشواهد المطلوبة لوجه الاستعمال في هذا الوقوع."
            if missing_exclusions:
                pending += f" يحتاج وجه المجاز إلى شاهد استبعاد للمعنى «{labels(missing_exclusions)}»."
            rows.append(card("use_deferred", "إرجاء وجه الاستعمال",
                             f"قصد المتكلم معنى «{gloss[sense]}». وبقي وجه استعماله غير محسوم.",
                             item["clause_span"]["raw_text"], pending, sense_id=sense, **ev))
    return rows


def citation_card(text):
    # A bounded citation lookup, never an ellipsis rule for arbitrary Arabic.
    surface = text.strip().removesuffix(".").strip()
    words = surface.split()
    canonical = ("وَاسْأَلِ", "الْقَرْيَةَ")
    if len(words) != len(canonical) or not all(compatible(w, c) for w, c in zip(words, canonical)):
        return []
    raw = pinned(COMMENTARY, COMMENTARY_SHA)
    passage = "{واسأل القرية} [يوسف:\n~~82] ، أي أهل القرية.".encode()
    start = raw.index(passage)
    return [card("attested_ellipsis", "تفسير منقول للشاهد المحدد",
                 "المطلوب سؤال أهل القرية. وفي تفسير الصبّان قُدّر المضاف «أهل».",
                 passage.decode().replace("\n~~", " "),
                 "هذا شاهد على وجه الإضمار. احتمال دلالة اللفظ على الأهل بطريق الاشتراك يحتاج شاهد وضع مستقل.",
                 source_path=COMMENTARY, source_sha256=COMMENTARY_SHA, start_byte=start,
                 end_byte=start+len(passage), input_terms=exact_terms(text),
                 grammar_path_certified=False, estimated_word_written=False)]


def original_check_failed(source, failures):
    return any(loc["span"]["source_id"] == source["id"] and loc["observed"] == loc["proposed"]
               for failure in failures for loc in failure["evidence"].get("locations", []))


def classical_reading(text, source, failures, usage_report):
    from nabt.errors import NabtError
    from tools.lexical_training.classical_attention import propose
    from . import classical_roles

    proposal = propose(text)
    transfer = {"proposal": proposal, "authority_of_weights": "NONE", "graph": None,
                "customary_use_established": False}
    if original_check_failed(source, failures):
        return [], {**transfer, "status": "SOURCE_CHECK_UNAVAILABLE"}
    try:
        graph = classical_roles.analyze(text, proposal)
    except (OSError, ValueError, NabtError) as error:
        reason = str(error)
        return [card("technical", "SOURCE_EVIDENCE_UNAVAILABLE", "تعذّر التحقق من شاهد الربط النحوي.",
                     reason, "يؤجَّل تعيين الأدوار بهذا المسار.", law=classical_roles.LAW)], {
                         **transfer, "status": "SOURCE_EVIDENCE_UNAVAILABLE", "reason": reason}
    if graph is None:
        return [], {**transfer, "status": "NO_SCOPED_BINDING"}
    transfer["usage_handoff"] = classical_roles.usage_handoff(graph, usage_report)
    r = graph["reading"]
    v = r["verb"]["surface"]
    subject, obj = (r[k]["term"]["surface"] for k in ("subject", "object"))
    event = next(n for n in graph["nodes"] if n["kind"] == "event")
    role_names = {e["depends_on_role"]: e["value"] for e in graph["edges"] if e["type"] == "semantic_role"}
    content = f"«{subject}» {role_names['subject']} و«{obj}» {role_names['object']}."
    force = ("يسأل النص هل تصحّ هذه النسبة" if r["force"] == "ask" else "يُخبر النص بهذه النسبة")
    sign_names = {"alif": "الألف", "ya": "الياء", "damma": "الضمة", "fatha": "الفتحة"}
    why = (f"يعمل «{v}» في الاسمين. علامة رفع «{subject}» {sign_names[r['subject']['sign']]} "
           f"وعلامة نصب «{obj}» {sign_names[r['object']['sign']]}. "
           "راجعنا تعيين الدورين في الكتاب لسيبويه وعلامتيهما في قطر الندى.")
    expected = [r[k]["term"]["utf8_span"] for k in ("subject", "object")]
    expected.append(r["cue"]["utf8_span"] if r["cue"] else None)
    agrees = (proposal["status"] == "PROPOSED" and proposal["source_sha256"] == source["sha256"] and
              [proposal["heads"][h]["span"] for h in ("subject", "object", "question_cue")] == expected)
    row = card("classical_role_binding", "قراءة لغوية مشروطة بالوجه المعجمي",
               force + " في معنى " + event["masdar"] + ": " + content, why,
               "تعيين الأفراد والوقوع الخارجي والاستعمال العرفي يحتاج كلٌّ منها شاهدًا مستقلًا.",
               graph_ref="/classical_role_attention/graph", law=classical_roles.LAW,
               source_sha256=source["sha256"], force=r["force"], attention_matches=agrees)
    return [row], {**transfer, "status": "SOURCE_BOUND_READING", "graph": graph, "attention_matches": agrees}


def passive_reading(text, source, failures):
    """Compare the learned top proposal to an independent, source-local analysis."""
    from tools.lexical_training.passive_transfer import propose
    from . import passive_relation

    proposal = propose(text)
    fields = ("relation", "verb_span", "patient_span", "cue_span")
    same_source = proposal.get("source_sha256") == source["sha256"]
    observed_failed = original_check_failed(source, failures)
    readings = [] if observed_failed else passive_relation.analyze(text)
    matches = []
    for reading in readings:
        ev = reading["evidence"]
        if ev["source_sha256"] != source["sha256"]:
            raise ValueError("Passive relation witness belongs to a different source")
        if same_source and proposal["status"] == "PROPOSED" and all(proposal[k] == ev[k] for k in fields):
            matches.append(ev["event_family"])
            reading["evidence"]["neural_proposal_agrees_on_relation_and_spans"] = True
            reading["why"] += " وافق اقتراح الشبكة هذا التحليل في العلاقة ومواضع الشواهد."

    if observed_failed:
        comparison = "SOURCE_CHECK_UNAVAILABLE"
    elif proposal["status"] != "PROPOSED":
        comparison = proposal["status"]
    elif not same_source:
        comparison = "PROPOSAL_SOURCE_MISMATCH"
    elif matches:
        comparison = "MATCHES_SCOPED_READING"
    elif readings:
        comparison = "DIFFERS_FROM_SCOPED_READING"
    else:
        comparison = "NO_LICENSED_WRITTEN_WITNESS"
    return readings, {"proposal": proposal, "comparison": comparison, "compared_fields": list(fields),
                      "matching_event_families": matches, "source_sha256": source["sha256"],
                      "neural_authority": "NONE"}


def analyze(text):
    lexical, mentions = lexical_context(text)
    names = {m["id"]: m["name"] for m in mentions}
    context = {"entities": [{"id": m["id"], "name": m["name"]} for m in mentions]}
    grammar = orchestration.run({"text": text, "lexical_text": lexical, "context": context})
    # The owner enumerates all installed conventions with no supplied profile.
    usage_report = usage.acquire(text, source_id=grammar["source"]["id"])
    failures = grammar_failures(grammar)
    events, transfer = passive_reading(text, grammar["source"], failures)
    roles, classical = classical_reading(text, grammar["source"], failures, usage_report)
    cards = failures + predications(grammar, names) + events + roles
    pending_forms = [b["reading"]["text"] for b in grammar["conditional_readings"]
                     if not any(r["name"] == "mantuq" and r["closed"] for r in b["result"]["dispatch_ledger"])]
    for b in grammar["conditional_readings"]:
        conditional = predications(b["result"], names, branch=b["reading"])
        if pending_forms:
            for c in conditional:
                c["unresolved"] += " لم يثبت المنطوق للأوجه: " + "، ".join(pending_forms) + "."
        cards.extend(conditional)
    profiles = profile_reports(text, grammar["source"]["id"], usage_report)
    cards.extend(use_cards(usage_report, profiles))
    cards.extend(citation_card(text))
    stage = grammar["stopped_at"]
    if not cards:
        cards.append(card("unresolved", "إرجاء", "لم تتعيّن إفادة ضمن القراءة المتاحة.",
                          "آخر مرحلة بلغها القارئ: " + LAYERS[stage] + ".",
                          "تحتاج قراءة هذا النص إلى شواهد أو تغطية إضافية."))
    return {"schema": "nabt.text-reading.v1", "source": grammar["source"], "cards": cards,
            "grammar_stop": stage, "grammar_stop_ar": LAYERS[stage],
            "lexical_premises": {"path": LEXICON, "sha256": LEXICON_SHA, "text_local_names": mentions},
            "orchestration": grammar, "use_owner": usage_report, "conditional_use_reports": profiles,
            "passive_relation_transfer": transfer, "classical_role_attention": classical,
            "all_arabic_complete": False, "world_truth_established": False}

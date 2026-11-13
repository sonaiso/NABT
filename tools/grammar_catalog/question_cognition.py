"""Question-relative interpretation on fixed, inspectable scopes and existing owners."""
from hashlib import sha256
import re

from . import definition_network, interpretation_chains, question_frames, scoped_composition, usage_witness
from .operations import digest
from tools.lexical_training import question_ranking

LAW = "nabt.question-cognition.v1"

# Complete question forms, rather than substring triggers which could discard a restriction.
QUESTIONS = {
    "instrument": ("هل نُسب استعمال الآلة إلى الفعل؟", "هل ذُكرت آلة للفعل؟"),
    "condition": ("هل الوصول شرط للفعل؟", "هل اشترط النص الوصول؟"),
    "joint": ("هل اجتمع الشرط واستعمال الآلة؟", "هل اشترط الوصول وذُكرت الأداة؟"),
    "occurrence": ("هل وقع الحدث في الخارج؟", "هل ثبت وقوع الفعل في الواقع؟"),
    "compare": ("ما المشترك والفارق بين المعنيين؟", "بم يشترك المرشحان وبم يتميزان؟"),
    "genus": ("ماذا يرث هذا المعنى؟", "ما شبكة هذا المعنى؟"),
    "arithmetic": ("ما القيمة الحسابية؟", "ما ناتج التعبير؟"),
    "linguistic": ("ما القراءة اللغوية؟", "ما وجه الاستعمال اللغوي؟"),
    "customary": ("ما القراءة العرفية؟", "ما وجه الاستعمال العرفي؟"),
    "observation": ("ما التغير المرصود؟", "ما الفرق بين الرصدين؟"),
    "cause": ("هل ثبت السبب الفيزيائي؟", "هل يثبت الرصد سببا طبيعيا؟"),
}
LABELS = {"instrument": "نسبة استعمال الآلة إلى الفعل", "condition": "اشتراط الوصول",
          "joint": "اجتماع اشتراط الوصول واستعمال الآلة", "occurrence": "وقوع الحدث في الخارج"}
GAPS = {"OUTSIDE_SOURCE": "النص خارج صيغ العملية المعتمدة.",
        "OUTSIDE_QUESTION": "لم تُرخَّص صيغة السؤال بقيدها الكامل.",
        "OPEN": "تبقى إجابتان ممكنتين في المجال المحدد.",
        "CONFLICT": "تعارضت شواهد المحور المسؤول عنه."}


def validate(question):
    if type(question) is not str or not question.strip() or len(question.encode()) > 512:
        raise ValueError("Expected a nonempty Arabic question within 512 UTF-8 bytes")


PAIR = re.compile(r"«(?P<left>[ء-يَ-ْ]{1,40})» أو «(?P<right>[ء-يَ-ْ]{1,40})»")


def compare_definitions(text, source_id):
    pair = PAIR.fullmatch(text)
    if not pair:
        return {"status": "OUTSIDE_SOURCE"}
    owners = [definition_network.read(f"ما شبكة «{term}»؟", identity=source_id) for term in pair.groups()]
    rows = {"owners": owners, "occurrences": [interpretation_chains.witness(text, *pair.span(i))
                                              for i in (1, 2)]}
    if any(owner["status"] != "VERIFIED_CONDITIONAL_NETWORK" for owner in owners):
        return {**rows, "status": "INCOMPLETE_COMPARISON", "owner_statuses": [o["status"] for o in owners]}
    comparisons = []
    for left in owners[0]["readings"]:
        for right in owners[1]["readings"]:
            def claims(reading):
                return {(c["relation"], c["node"]): c for c in reading["claims"]}
            a, b = claims(left), claims(right)
            comparisons.append({"senses": [left["focus"], right["focus"]],
                                "shared": [{"relation": r, "node": n, "left_proofs": a[r,n]["proofs"],
                                            "right_proofs": b[r,n]["proofs"]} for r,n in sorted(a.keys() & b.keys())],
                                "left_attested_only": [a[k] for k in sorted(a.keys() - b.keys())],
                                "right_attested_only": [b[k] for k in sorted(b.keys() - a.keys())]})
    return {**rows, "status": "COMPARED", "value": comparisons, "individual_identified": False,
            "absence_from_definition_proves_exclusion": False}


def owner_view(operation, text, source_id):
    if operation == "compare":
        return compare_definitions(text, source_id)
    if operation == "arithmetic":
        report = scoped_composition.evaluate({"schema": scoped_composition.SCHEMA,
                                              "profile": "arithmetic", "text": text})
        result = {"status": report["status"], "owner": report}
        if report["chain_complete"]:
            result["value"] = report["projection"]["result"]
        return result
    if operation == "genus":
        # Use the original occurrence or synthesize a citation only for a bare lemma.
        original = definition_network.QUERY.fullmatch(text)
        if not original and not re.fullmatch(r"[ء-يَ-ْ]{1,40}", text):
            return {"status": "OUTSIDE_SOURCE"}
        query = text if original else f"ما شبكة «{text}»؟"
        if not definition_network.QUERY.fullmatch(query):
            return {"status": "OUTSIDE_SOURCE"}
        report = definition_network.read(query, identity=source_id)
        return {"status": report["status"], "owner": report, "owner_input": query,
                "citation_adapted": query != text, "original_lemma_span":
                interpretation_chains.witness(text, *(original.span(1) if original else (0, len(text)))),
                "value": [{"reading": r["focus"], "claims": r["claims"]} for r in report["readings"]]}
    if operation in ("linguistic", "customary"):
        report = usage_witness.run({"text": text, "source_id": source_id,
                                    "usage_context": {"profile_id": operation}})
        return {"status": report["status"], "owner": report, "conditional_profile": operation,
                "value": [a["concept_id"] for a in report["applications"]],
                "community_practice_established": False}
    chain = interpretation_chains.analyze(text)
    if not chain or "changes" not in chain:
        return {"status": "OUTSIDE_SOURCE"}
    if operation == "cause" and chain["status"] == "SOURCE_RELATIVE_CHAIN":
        return {"status": "OPEN", "owner": chain, "value": None,
                "missing": ["independent causal law", "applicability to this observation"],
                "scope": "recorded states and their order"}
    return {"status": chain["status"], "owner": chain,
            "value": chain["changes"] if operation == "observation" else None}


def analyze(text, question, source_id="input"):
    validate(question)
    proposal = question_ranking.propose(question)
    ranked = proposal.get("ranking", [])
    order = list(dict.fromkeys([*ranked, *QUESTIONS]))
    operation = next((op for op in order if question.strip() in QUESTIONS[op]), None)
    if operation is None:
        decision = {"status": "OUTSIDE_QUESTION"}
    elif operation in question_frames.REQUIRED:
        decision = question_frames.interpret(text, operation)
    else:
        decision = owner_view(operation, text, source_id)
    return {"schema": LAW, "source_sha256": sha256(text.encode()).hexdigest(),
            "source_id": source_id, "question": question, "operation": operation,
            "proposal": proposal, "decision": decision, "world_truth_established": False,
            "scope": "fixed question grammar and independently scoped owners"}


def cards(report):
    from .text_reading import card
    operation = report["operation"]
    decision = report["decision"]
    status = decision["status"]
    detail = GAPS.get(status, "الحالة التي أعادها الفاحص: " + status)
    pending = "القبول في هذا المسار مرتبط بالنص والسؤال ومجال الفحص."
    if operation in LABELS and "evidence" in decision:
        label = LABELS[operation]
        detail = {"SUPPORTED": "يثبت النص " + label + ".", "REFUTED": "ينفي النص " + label + ".",
                  "CONFLICT": "تعارضت الشواهد المتعلقة بـ" + label + ".",
                  "OPEN": "بقيت مسألة «" + label + "» مفتوحة."}[status]
        ids = sorted({i for s in decision["minimal_supports"] for i in s["evidence_ids"]})
        why = "، ".join("«"+decision["evidence"][i]["witness"]["text"]+"»" for i in ids)
        if not why:
            why = "تتوافق مع معطيات السؤال صورتان مختلفتان في الجواب."
    else:
        owner = decision.get("owner", {})
        why = owner.get("law_id") or owner.get("schema") or LAW
        if operation == "arithmetic" and status == "COMPUTED":
            result = decision["value"]
            if result["sort"] == "proposition":
                detail = "المساواة صحيحة." if result["truth"] else "المساواة غير صحيحة."
            else:
                value = result["value"]
                detail = f'قيمة التعبير {value["numerator"]}/{value["denominator"]}.'
        elif operation in ("linguistic", "customary") and decision.get("value"):
            detail = "القراءات المقبولة في الاصطلاح المحدد: " + "، ".join(decision["value"])
        elif operation == "genus" and decision.get("value"):
            detail = "؛ ".join(r["reading"]+" ← "+"، ".join(c["node"] for c in r["claims"])
                               for r in decision["value"])
        elif status == "COMPARED":
            detail = " / ".join(" و".join(c["senses"]) + "، المشترك: " +
                                ("، ".join(x["node"] for x in c["shared"]) or "لا شاهد مشترك") +
                                "، والمنفرد في التعريفين بالترتيب: " +
                                " / ".join("، ".join(x["node"] for x in c[k]) or "لا شاهد إضافي"
                                           for k in ("left_attested_only", "right_attested_only"))
                                for c in decision["value"])
            pending = "بقاء خاصية بلا شاهد في أحد التعريفين يترك انطباقها عليه مفتوحًا."
        elif operation == "cause" and decision.get("missing"):
            why = "الرصد يحدّد حالاته. يلزم شاهد للعلاقة السببية ولانطباقها على هذه الحالة."
        elif operation == "observation" and decision.get("value"):
            detail = "، ".join(f'{c["axis"]} ({c["from_day"]}، {c["to_day"]}): {c["status"]}'
                               for c in decision["value"])
    return [card("question_cognition", status, detail, why, pending,
                 operation=operation, question=report["question"], decision_sha256=digest(decision))]

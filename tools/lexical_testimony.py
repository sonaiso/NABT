"""Attested lexical interpretations, checked by the existing Lean calculus.

The public request supplies a dictionary index and target components, never a
replacement definition, a reliability score, a transmission grade or a proof.
Byte identity, author attribution, semantic interpretation and world truth are
separate. No new deduction rule is installed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("evidence/lexical_denotation/catalog.json")
CATALOG_SHA = "13988ecec13e541cf4f7cd242df43badbe718a26d30691fbf7584363d612df49"
SCHEMA = "nabt.lexical-testimony.v1"
LAW = "nabt.lexical-denotation.v1"
DISCLAIMER = ("يفحص التطبيق هوية النقل المحفوظ والدلالة المشروطة بالتفسير المثبت؛ "
              "لا يثبت صحة الرواية تاريخيًا، أو مراد المتكلم، أو واقع المسمى.")
SOURCES = {
    "lisan": ("ابن منظور", "لسان العرب", None),
    "maqayis": ("ابن فارس", "مقاييس اللغة", "evidence/classical_language/sources/maqayis.txt"),
    "shakhsiyya3": ("تقي الدين النبهاني", "الشخصية الإسلامية، الجزء الثالث",
                    "evidence/mantuq_mafhum/sources/shakhsiyya3.txt"),
}
THEOREMS = ["Nabt.LexicalDenotation.check_exact",
            "Nabt.LexicalDenotation.indication_sound",
            "Nabt.LexicalDenotation.no_necessity_without_ledger",
            "Nabt.LexicalDenotation.necessity_preserves_sense",
            "Nabt.LexicalDenotation.definition_does_not_assert_world"]


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_FIELD")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE")))


def _native(exe, request=None):
    result = subprocess.run([str(exe)] + (["--export"] if request is None else []),
        input=None if request is None else json.dumps(request, ensure_ascii=False) + "\n",
        text=True, capture_output=True, check=True, timeout=20)
    if len(result.stdout.encode()) > 1024 * 1024:
        raise ValueError("NATIVE_RESPONSE_LIMIT")
    return _strict_json(result.stdout)


def _citation(c, root):
    author, title, local = SOURCES[c["work"]]
    quote = c["quotation"].encode("utf-8")
    start, end = c["start_byte"], c["end_byte"]
    if type(start) is not int or type(end) is not int or not 0 <= start < end or end-start != len(quote):
        raise ValueError("CITATION_SPAN_INVALID")
    # Only retained files are read. No caller paths or implicit network fetch.
    replayed = False
    if local:
        raw = (root / local).read_bytes()
        if _sha(raw) != c["source_sha256"] or raw[start:end] != quote:
            raise ValueError("SOURCE_BYTES_CHANGED")
        replayed = True
    return {"author": author, "work_title": title, "citation": c,
            "quotation_sha256": _sha(quote),
            "retained_catalogue_matched": True,
            "source_file_replayed": replayed,
            "source_check": "RETAINED_SOURCE_BYTES_REPLAYED" if replayed else "RETAINED_QUOTATION_ONLY",
            "transmission_type": "UNASSESSED",
            "historical_authenticity_established": False}


def _indications(sense, target, necessities):
    """Finite adapter cross-check, not the source of the Lean certificate."""
    if not target:
        return []
    whole, chosen = set(sense["components"]), set(target)
    result = []
    if chosen == whole:
        result.append("mutabaqa")
    if chosen < whole:
        result.append("tadammun")
    if any(r["sense_id"] == sense["id"] and r["kind"] == "mental"
           and target == [r["target"]] and r["target"] not in whole
           and r["citation"]["quotation"] for r in necessities):
        result.append("iltizam")
    return result


def assess(entry, target, *, root=ROOT):
    """Run the pinned native catalogue; return every installed sense for entry."""
    out = {"schema": SCHEMA, "law_id": LAW, "status": "INVALID_INPUT",
           "authority": "UNVERIFIED", "native_checked": False,
           "all_installed_readings_retained": False, "rows": [],
           "world_truth_established": False, "all_arabic_complete": False,
           "intended_sense_established": False, "historical_authenticity_established": False,
           "app_disclaimer": DISCLAIMER}
    try:
        if (type(entry) is not str or not entry.strip() or len(entry.encode("utf-8")) > 128
                or type(target) is not list or len(target) > 64
                or any(type(t) is not str or not t.strip() or len(t.encode("utf-8")) > 4096 for t in target)):
            return out
    except UnicodeError:
        return out
    out.update(entry=entry, target=target)
    try:
        raw = (root / CATALOG).read_bytes()
        if _sha(raw) != CATALOG_SHA:
            raise ValueError("CATALOGUE_IDENTITY_CHANGED")
        catalogue = _strict_json(raw)
        selected = [s for s in catalogue["senses"] if s["root"] == entry]
        # Replay attribution before running Lean. No authority from an input flag.
        testimonies = {s["id"]: _citation(s["citation"], root) for s in selected}
        rules = [r for r in catalogue["necessities"] if r["sense_id"] in testimonies]
        rule_sources = [_citation(r["citation"], root) for r in rules]
    except (OSError, ValueError, KeyError):
        return {**out, "status": "SOURCE_UNAVAILABLE"}
    exe = root / "formal/.lake/build/bin/lexicalDenotation"
    try:
        binary_sha = _sha(exe.read_bytes())
        exported = _native(exe)
        expected_export = {"law_id": LAW, "authority": "CONDITIONAL_INTERPRETATION_ONLY",
            "senses": [{k:s[k] for k in ("id", "root", "citation", "components")} for s in catalogue["senses"]],
            "necessities": [{k:r[k] for k in ("sense_id", "target", "kind", "citation")} for r in catalogue["necessities"]]}
        if exported != expected_export:
            raise ValueError("NATIVE_CATALOGUE_DIFFERS")
        request = {"root": entry, "target": target, "proposed_ids": [s["id"] for s in selected]}
        checked = _native(exe, request)
        expected_rows = [{"sense": {k:s[k] for k in ("id", "root", "citation", "components")},
                          "indications": _indications(s, target, catalogue["necessities"])} for s in selected]
        common = [k for k in ("mutabaqa", "tadammun", "iltizam") if expected_rows and all(k in r["indications"] for r in expected_rows)]
        expected = {"status": "CONDITIONAL_INTERPRETATIONS" if selected else "UNMEASURED_ROOT",
                    "authority": "CONDITIONAL_INTERPRETATION_ONLY", "all_arabic_senses_enumerated": False,
                    "world_truth_asserted": False, "complete_installed_proposal": bool(selected),
                    "rows": expected_rows, "common_indications": common}
        # Canonical encoding distinguishes false/0 and true/1 in nested fields.
        if json.dumps(checked, sort_keys=True, ensure_ascii=False) != json.dumps(expected, sort_keys=True, ensure_ascii=False):
            raise ValueError("NATIVE_RESULT_DIFFERS")
        if _sha(exe.read_bytes()) != binary_sha:
            raise ValueError("NATIVE_CHANGED_DURING_EXECUTION")
    except subprocess.TimeoutExpired:
        return {**out, "status": "RESOURCE_EXHAUSTED"}
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {**out, "status": "VERIFICATION_UNAVAILABLE"}
    rows = []
    for sense, checked_row in zip(selected, checked["rows"]):
        necessity = [{"target": r["target"], "relation": "MENTAL_NECESSITY_PREMISE",
                      "source": source, "alignment_status": r["alignment_status"]}
                     for r, source in zip(rules, rule_sources) if r["sense_id"] == sense["id"]]
        rows.append({"sense_id": sense["id"], "components": sense["components"],
                     "testimony": testimonies[sense["id"]],
                     "interpretation_status": sense["interpretation_status"],
                     "indications": {k: k in checked_row["indications"] for k in ("mutabaqa", "tadammun", "iltizam")},
                     "commitment_conditions": necessity,
                     "causal_or_legal_conclusion_established": False})
    return {**out, "status": checked["status"], "authority": "CONDITIONAL_INTERPRETATION_ONLY",
            "native_checked": True, "all_installed_readings_retained": bool(selected),
            "rows": rows, "common_indications": common,
            "catalogue_sha256": CATALOG_SHA, "native_sha256": binary_sha,
            "native_request": request, "native_result": checked,
            "theorem_references": THEOREMS,
            "premises": ["التحليل الدلالي المودع تفسير مؤلف غير محكّم استقلالًا.",
                         "سلامة الدلالة مشروطة بصدق تفسير المكونات وقاعدة اللزوم في النموذج.",
                         "لا يُستنتج الاستعمال الفعلي أو السبب أو الحكم الشرعي من مجرد القيد المعجمي."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--target", action="append", default=[])
    args = parser.parse_args()
    result = assess(args.entry, args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["native_checked"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

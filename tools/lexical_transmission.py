"""Source-bound documentary reports, without inferring tawatur from book counts.

The installed catalogue identifies each report by its own reading and citation.
Its dependency ledger is empty: separate books are not proved independent, nor
are distinct meanings silently combined into support for one proposition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from nabt import foundation
from tools import lexical_testimony as testimony

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "nabt.lexical-transmission-receipt.v1"
LAW = "nabt.lexical-transmission.v1"
THEOREMS = [
    "Nabt.LexicalTransmission.invalid_reports_unassessed",
    "Nabt.LexicalTransmission.empty_reports_unassessed",
    "Nabt.LexicalTransmission.single_family_is_single",
    "Nabt.LexicalTransmission.duplicate_report_keeps_one_source",
    "Nabt.LexicalTransmission.independent_requires_review",
    "Nabt.LexicalTransmission.independent_each_pair",
    "Nabt.LexicalTransmission.pair_review_has_bound_evidence",
    "Nabt.LexicalTransmission.no_review_no_pair",
    "Nabt.LexicalTransmission.different_claim_blocks",
    "Nabt.LexicalTransmission.installed_readings_preserved",
    "Nabt.LexicalTransmission.context_preserved",
]


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _report(sense, context):
    return {"entry": sense["root"], "sense_id": sense["id"], "context": context,
            "source_family": sense["citation"]["work"], "citation": sense["citation"],
            "documentary_status": "IDENTIFIED_SINGLE_SOURCE_REPORT"}


def assess_transmission(entry, *, context=""):
    """Check the exact installed documentary inventory and preserve its scope.

    No caller supplies reports, a chain, a grade, a confidence or a checker.
    The catalogue and executable root are fixed by this installed module.
    """
    foundation.require_foundation("tools.lexical_transmission.assess_transmission")
    root = ROOT
    base = {"schema": SCHEMA, "law_id": LAW, "status": "INVALID_INPUT",
            "native_checked": False, "authority": "UNVERIFIED", "reports": [], "claims": [],
            "tawatur_established": False, "historical_authenticity_established": False,
            "intended_sense_established": False, "world_truth_established": False,
            "strict_language_accepted": False}
    try:
        if type(entry) is not str or not entry.strip() or type(context) is not str:
            return base
        if len(entry.encode("utf-8")) > 128 or len(context.encode("utf-8")) > 65536:
            return {**base, "status": "RESOURCE_EXHAUSTED", "reason": "INPUT_BYTE_LIMIT"}
    except UnicodeError:
        return base
    request = {"entry": entry, "context": context}
    base.update(request)
    try:
        raw = (root / testimony.CATALOG).read_bytes()
        if hashlib.sha256(raw).hexdigest() != testimony.CATALOG_SHA:
            raise ValueError("CATALOGUE_IDENTITY_CHANGED")
        catalog = testimony._strict_json(raw)
        selected = [s for s in catalog["senses"] if s["root"] == entry]
        sources = [testimony._citation(s["citation"], root) for s in selected]
    except (OSError, ValueError, KeyError):
        return {**base, "status": "SOURCE_UNAVAILABLE"}
    exe = root / "formal/.lake/build/bin/lexicalTransmission"
    try:
        binary_sha = hashlib.sha256(exe.read_bytes()).hexdigest()
        exported = testimony._native(exe)
        expected_export = {"law_id": LAW,
                           "reports": [_report(s, "") for s in catalog["senses"]],
                           "dependency_reviews": []}
        if _canonical(exported) != _canonical(expected_export):
            raise ValueError("NATIVE_CATALOGUE_DIFFERS")
        families = list(dict.fromkeys(s["citation"]["work"] for s in selected))
        expected = {"law_id": LAW, **request,
                    "status": "DOCUMENTARY_REPORTS" if selected else "UNMEASURED_ROOT",
                    "reports": [_report(s, context) for s in selected],
                    "source_families": families, "dependency_reviews": [],
                    "source_relationship_status": "INDEPENDENCE_UNASSESSED" if len(families) > 1
                        else "NOT_A_MULTISOURCE_ASSESSMENT",
                    "cross_source_sense_alignment_established": False,
                    "tawatur_established": False, "historical_authenticity_established": False,
                    "intended_sense_established": False, "world_truth_established": False,
                    "strict_language_accepted": False}
        checked = testimony._native(exe, request)
        if _canonical(checked) != _canonical(expected):
            raise ValueError("NATIVE_RESULT_DIFFERS")
        if hashlib.sha256(exe.read_bytes()).hexdigest() != binary_sha:
            raise ValueError("NATIVE_CHANGED_DURING_EXECUTION")
    except subprocess.TimeoutExpired:
        return {**base, "status": "RESOURCE_EXHAUSTED"}
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {**base, "status": "VERIFICATION_UNAVAILABLE"}
    scope = ("Retained, sense-specific documentary reports and conditional dependency algebra; "
             "not historical authentication, a final ahad grade, tawatur, or intended meaning.")
    claims = [{"kind": "SOURCE_BOUND_REPORT_INVENTORY_AND_DEPENDENCY_CLASSIFICATION",
               "entry": entry, "context": context,
               "sense_ids": [s["id"] for s in selected], "scope": scope,
               "catalogue_sha256": testimony.CATALOG_SHA,
               "native_sha256": binary_sha,
               "native_request_sha256": hashlib.sha256(_canonical(request).encode("utf-8")).hexdigest(),
               "native_result_sha256": hashlib.sha256(_canonical(checked).encode("utf-8")).hexdigest(),
               "proof": {"law_id": LAW, "theorems": THEOREMS},
               "unresolved_premises": ["HISTORICAL_ATTRIBUTION_UNASSESSED",
                                       "DEPENDENCY_REVIEW_NOT_ACQUIRED",
                                       "CROSS_SOURCE_SENSE_ALIGNMENT_UNASSESSED",
                                       "INTENDED_SENSE_NOT_ESTABLISHED"]}] if selected else []
    return {**base, **checked, "native_checked": True,
            "authority": "CONDITIONAL_DOCUMENTARY_CLASSIFICATION_ONLY",
            "catalogue_sha256": testimony.CATALOG_SHA,
            "native_sha256": binary_sha, "native_request": request, "native_result": checked,
            "source_replay": sources, "theorem_references": THEOREMS, "claims": claims,
            "premises": [
                "إسناد الكتاب إلى مؤلفه محفوظ من الفهرس، ولم يُحقق تاريخيًا بهذا الحساب.",
                "نقل فردي مسمى وصف للجرد؛ لا حكم بصحة الخبر أو قبول روايته أو رتبة أصولية نهائية.",
                "لم يُودع تقويم استقلال طرق النقل، ولا استنفادها عبر طبقاتها، ولا سياسة تواتر مستوفاة.",
                "مطابقة المعاني بين مصدرين التزام مستقل؛ اختلاف العبارة لا يثبت الاتفاق ولا التناقض.",
                "المقام محفوظ في الشهادة؛ لا يثبت ذلك اكتساب المراد فيه."]}


def main():
    foundation.require_foundation("tools.lexical_transmission.main")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--context", default="")
    args = parser.parse_args()
    result = assess_transmission(args.entry, context=args.context)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["native_checked"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

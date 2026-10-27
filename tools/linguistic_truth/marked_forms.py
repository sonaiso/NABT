"""Source-replayed vocalization premises for the existing bounded cue reader.

This is a reviewed acquisition bridge, not a native proof of source
interpretation. It supplies spellings only for readings already present in the
semantic inventory. It cannot introduce a designation or select its meaning.
"""
from __future__ import annotations

from hashlib import sha256
import gzip
import json
from pathlib import Path
import subprocess

from nabt import foundation


REVIEW_PATH = Path("evidence/attested_mark_recovery_v1/source_review.json")
REVIEW_SHA256 = "4b2411793136de0744a0a8cd39eeeecd44fb3ddd6bd9b59cd1481dd69f321484"
LAW_ID = "nabt.bounded-cue-vocalization.v1"
QUALIFIED_REVIEW_PATH = Path("evidence/qualified_cue_licensing_v1/source_review.json")
QUALIFIED_REVIEW_SHA256 = "22cf92779bb0d2f6e72bdd09743898bc708dbf4997749e9b55ed9c7620eafed6"
QUALIFIED_LAW_ID = "nabt.qualified-cue-licensing.v1"


class _QualifiedCueVerificationError(ValueError):
    """A source review is insufficient when its native renderer is unavailable."""


class _QualifiedCueResourceError(ValueError):
    """An execution limit cannot classify a spelling as unsupported Arabic."""


def _load_review(root: Path):
    """Reopen every installed byte source; no caller-controlled replacement."""
    raw = (root / REVIEW_PATH).read_bytes()
    if sha256(raw).hexdigest() != REVIEW_SHA256:
        raise ValueError("MARK_REVIEW_CHANGED")
    review = json.loads(raw)
    if review["schema"] != "nabt.attested-mark-review.v1":
        raise ValueError("MARK_REVIEW_SCHEMA")
    sources = {}
    for source in review["sources"]:
        source_path = (root / source["path"]).resolve()
        if not source_path.is_relative_to(root.resolve()):
            raise ValueError("MARK_SOURCE_OUTSIDE_ROOT")
        data = source_path.read_bytes()
        if source["id"] in sources or sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("MARK_SOURCE_CHANGED")
        sources[source["id"]] = data
    passages = {}
    for passage in review["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = sources[passage["source_id"]]
        if (passage["id"] in passages or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(data)):
            raise ValueError("MARK_PASSAGE_BOUNDS")
        selected = data[start:end]
        if (sha256(selected).hexdigest() != passage["sha256"]
                or selected.decode("utf-8") != passage["quote"]):
            raise ValueError("MARK_PASSAGE_CHANGED")
        passages[passage["id"]] = passage
    for rows in (review["lexemes"], review["rules"]):
        seen = set()
        for row in rows:
            if (row["id"] in seen or not row["passage_ids"]
                    or not set(row["passage_ids"]) <= passages.keys()):
                raise ValueError("MARK_REVIEW_UNBOUND")
            seen.add(row["id"])
    for lexeme in review["lexemes"]:
        foundation.validate_source(lexeme["stem"])
    return review


def _license(form, lexemes, rules, role):
    return {"form": form, "role": role, "law_id": LAW_ID,
            "lexeme_ids": [row["id"] for row in lexemes],
            "rule_ids": [row["id"] for row in rules],
            "passage_ids": sorted({p for row in [*lexemes, *rules] for p in row["passage_ids"]}),
            "review_sha256": REVIEW_SHA256,
            "authority": "REVIEWED_VOCALIZATION_AND_BOUNDED_INFLECTION",
            "native_acquisition_proof": False}


def _definite(stem, article_type):
    # This bounded review covers these five initial carriers only. A future
    # ledger must not silently turn its own category label into an all-letter
    # phonological license.
    if article_type == "lunar" and stem[0] in "أحم":
        return "الْ" + stem
    if article_type == "solar" and stem[0] in "رش":
        return "ال" + stem[0] + "ّ" + stem[1:]
    raise ValueError("MARK_REVIEW_ARTICLE_TYPE")


def _reviewed_forms(review, normal, role, *, following=None):
    """Generate only the declared simple definite-noun inflections.

    The nominative lexical citation is not reused as an accusative or genitive
    surface. That final vowel is supplied by the separately reviewed role rule.
    Unknown words, bare/indefinite nouns, irregular inflection,
    and unrelated syntactic constructions remain outside this small bridge.
    """
    if "qualified_forms" in review:
        # Conditional liaison is not a freestanding particle spelling. A
        # whole-cue parse has already supplied the adjacent token. The native
        # form receipt retains this requirement; Python discharges adjacency.
        return [row for row in review["qualified_forms"]
                if row["normal"] == normal and row["role"] == role
                and (row["next_requirement"] == "any"
                     or (type(following) is str and following.startswith("ال")))]
    rules = {row["id"]: row for row in review["rules"]}
    lexemes = review["lexemes"]
    if role == "grammar":
        return [_license(row["stem"], [row], [], role) for row in lexemes
                if row["normal"] == normal and row["inflection"] == "fixed"]
    if role == "expression":
        required = ["ba_genitive", "regular_genitive"]
        if not all(key in rules for key in required):
            return []
        return [_license("بِ" + _definite(row["stem"], row["article_type"]) + "ِ", [row],
                         [rules[k] for k in [*required, row["article_type"] + "_article"]], role)
                for row in lexemes if row["normal"] == normal
                and row["kind"] == "noun" and row["inflection"] == "regular_definite"
                and row["article_type"] + "_article" in rules]
    if role != "sense":
        return []
    words = normal.split()
    required = ["object_accusative", "regular_accusative", "adjective_agreement"]
    if len(words) != 2 or not all(key in rules for key in required):
        return []
    nouns = [row for row in lexemes if row["normal"] == words[0]
             and row["kind"] == "noun" and row["inflection"] == "regular_definite"]
    adjectives = [row for row in lexemes if row["normal"] == words[1]
                  and row["kind"] == "adjective" and row["inflection"] == "regular_definite"]
    return [_license(_definite(noun["stem"], noun["article_type"]) + "َ "
                     + _definite(adjective["stem"], adjective["article_type"]) + "َ",
                     [noun, adjective], [rules[k] for k in dict.fromkeys([*required,
                         noun["article_type"] + "_article", adjective["article_type"] + "_article"])], role)
            for noun in nouns for adjective in adjectives
            if noun["article_type"] + "_article" in rules and adjective["article_type"] + "_article" in rules]


def _qualified_table(review):
    """Independent Python recurrence for the six reviewed native recipes.

    This computes no semantic answer. It checks the reviewed roles/genders
    and renders retained stems under the named case/construction premises.
    The full result must agree with the installed Lean renderer before use.
    """
    lexemes = {row["id"]: row for row in review["lexemes"]}
    rules = {row["id"]: row for row in review["effective_rules"]}
    recipes = (
        ("head", "ayn_definite", "ayn_definite"),
        ("adjective", "ayn_definite", "basira"),
        ("idafa", "ayn_construct", "maa"),
        ("fixed", "la", "la"),
        ("fixed", "bal_sukun", "bal_sukun"),
        ("fixed", "bal_kasra", "bal_kasra"),
    )
    rows = []
    for construction, left_id, right_id in recipes:
        left, right = lexemes.get(left_id), lexemes.get(right_id)
        if left is None or right is None:
            continue
        ids = [left_id] if left_id == right_id else [left_id, right_id]
        requirement = "any"
        normal = left["normal"]
        if construction == "fixed":
            if left["kind"] != "particle" or left["inflection"] != "fixed":
                continue
            requirement = left.get("next_requirement", "any")
            if requirement not in {"any", "definite_wasl"}:
                raise ValueError("QUALIFIED_NEXT_REQUIREMENT")
            rule_ids = ["bal_connective_kasra"] if requirement == "definite_wasl" else []
            role, form = "grammar", left["stem"]
        elif construction == "head":
            if (left["kind"] != "noun" or left["inflection"] != "regular_definite"
                    or left.get("number") != "singular" or left.get("article_type") != "lunar"):
                continue
            rule_ids = ["ba_genitive", "regular_genitive", "lunar_article"]
            role, form = "expression", "بِالْ" + left["stem"] + "ِ"
        elif construction == "adjective":
            if (left["kind"] != "noun" or right["kind"] != "adjective"
                    or left["inflection"] != "regular_definite"
                    or right["inflection"] != "regular_definite"
                    or left.get("number") != "singular" or right.get("number") != "singular"
                    or left.get("gender") not in {"feminine", "masculine"}
                    or left["gender"] != right.get("gender")
                    or left.get("article_type") != "lunar"
                    or right.get("article_type") != "lunar"):
                continue
            rule_ids = ["object_accusative", "regular_accusative", "adjective_agreement", "lunar_article"]
            role, form = "sense", "الْ" + left["stem"] + "َ الْ" + right["stem"] + "َ"
            normal += " " + right["normal"]
        else:
            if (left["kind"] != "noun" or right["kind"] != "noun"
                    or left["inflection"] != "regular_construct"
                    or right["inflection"] != "regular_definite"
                    or left.get("number") != "singular" or right.get("number") != "singular"
                    or right["normal"] not in left.get("licensed_dependents", [])
                    or right.get("article_type") != "lunar"):
                continue
            rule_ids = ["object_accusative", "regular_accusative", "idafa_genitive",
                        "construct_no_article_tanwin", "regular_genitive", "lunar_article"]
            role, form = "sense", left["stem"] + "َ الْ" + right["stem"] + "ِ"
            normal += " " + right["normal"]
        if not set(rule_ids) <= rules.keys():
            continue
        rows.append({"normal": normal, "role": role, "form": form, "lexeme_ids": ids,
                     "rule_ids": rule_ids, "next_requirement": requirement})
    return rows


def _replay_qualified_review(root: Path):
    """Replay the additive review, including compressed documentary sources.

    The unchanged base review supplies existing grammatical premises. New
    reviewed interpretations (feminine agreement and the extended lunar set)
    are explicitly named overrides; neither source is silently rewritten.
    """
    raw = (root / QUALIFIED_REVIEW_PATH).read_bytes()
    if sha256(raw).hexdigest() != QUALIFIED_REVIEW_SHA256:
        raise ValueError("QUALIFIED_REVIEW_CHANGED")
    review = json.loads(raw)
    if review["schema"] != "nabt.attested-mark-review.v1":
        raise ValueError("QUALIFIED_REVIEW_SCHEMA")
    if (review["base_review"].get("path") != str(REVIEW_PATH)
            or review["base_review"].get("sha256") != REVIEW_SHA256):
        raise ValueError("QUALIFIED_BASE_REVIEW_CHANGED")
    base = _load_review(root)
    sources = {}
    for source in review["sources"]:
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("QUALIFIED_SOURCE_OUTSIDE_ROOT")
        data = path.read_bytes()
        if source["id"] in sources or sha256(data).hexdigest() != source["sha256"]:
            raise ValueError("QUALIFIED_SOURCE_CHANGED")
        if source.get("encoding") == "gzip":
            data = gzip.decompress(data)
            if sha256(data).hexdigest() != source["decoded_sha256"]:
                raise ValueError("QUALIFIED_DECODED_SOURCE_CHANGED")
        elif source.get("encoding", "utf-8") not in {"utf-8", "plain"}:
            raise ValueError("QUALIFIED_SOURCE_ENCODING")
        sources[source["id"]] = data
    passages = {}
    for passage in review["passages"]:
        start, end = passage["start_byte"], passage["end_byte"]
        data = sources[passage["source_id"]]
        if (passage["id"] in passages or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(data)):
            raise ValueError("QUALIFIED_PASSAGE_BOUNDS")
        selected = data[start:end]
        if (sha256(selected).hexdigest() != passage["sha256"]
                or selected.decode("utf-8") != passage["quote"]):
            raise ValueError("QUALIFIED_PASSAGE_CHANGED")
        passages[passage["id"]] = passage
    for rows in (review["lexemes"], review["rules"]):
        seen = set()
        for row in rows:
            if (row["id"] in seen or not row["passage_ids"]
                    or not set(row["passage_ids"]) <= passages.keys()):
                raise ValueError("QUALIFIED_REVIEW_UNBOUND")
            seen.add(row["id"])
    for lexeme in review["lexemes"]:
        foundation.validate_source(lexeme["stem"])
    effective_rules = {row["id"]: row for row in base["rules"]}
    for row in review["rules"]:
        if row["id"] in effective_rules and row.get("replaces_rule_from_base") != row["id"]:
            raise ValueError("QUALIFIED_IMPLICIT_RULE_REPLACEMENT")
        effective_rules[row["id"]] = row
    return {**review, "effective_rules": list(effective_rules.values())}


def _load_qualified_review(root: Path):
    """No caller ledger/verification flags; compare the entire native table."""
    review = _replay_qualified_review(root)
    expected = {"schema": QUALIFIED_LAW_ID, "review_sha256": QUALIFIED_REVIEW_SHA256,
                "status": "CHECKED_CONDITIONAL_FORMS", "forms": _qualified_table(review),
                "source_interpretation_kernel_proved": False,
                "intended_sense_established": False, "strict_language_accepted": False,
                "whole_arabic_complete": False}
    executable = root / "formal/.lake/build/bin/qualifiedCueLicensing"
    try:
        executable_sha256 = sha256(executable.read_bytes()).hexdigest()
        completed = subprocess.run([str(executable)],
            input=json.dumps({"review_sha256": QUALIFIED_REVIEW_SHA256}) + "\n",
            text=True, encoding="utf-8", capture_output=True, timeout=10, check=False)
        if len(completed.stdout.encode()) > 65536:
            raise _QualifiedCueResourceError("QUALIFIED_NATIVE_OUTPUT_LIMIT")
        # Canonical JSON comparison distinguishes bool from integer and checks
        # every returned field, scope limit, recipe and all surface characters.
        receipt = json.loads(completed.stdout, object_pairs_hook=_unique_native_pairs,
                             parse_constant=_reject_native_constant)
        if isinstance(receipt, dict) and receipt.get("status") == "RESOURCE_LIMIT":
            raise _QualifiedCueResourceError("QUALIFIED_NATIVE_RESOURCE_LIMIT")
        if completed.returncode != 0 or completed.stderr:
            raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_EXECUTION_FAILED")
        if sha256(executable.read_bytes()).hexdigest() != executable_sha256:
            raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_CHANGED_DURING_EXECUTION")
        canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":"), allow_nan=False)
        if canonical(receipt) != canonical(expected):
            raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_TABLE_MISMATCH")
    except subprocess.TimeoutExpired as exc:
        raise _QualifiedCueResourceError("QUALIFIED_NATIVE_TIMEOUT") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_UNAVAILABLE") from exc
    lexemes = {row["id"]: row for row in review["lexemes"]}
    rules = {row["id"]: row for row in review["effective_rules"]}
    receipt_sha256 = sha256(canonical(receipt).encode()).hexdigest()
    forms = []
    for row in expected["forms"]:
        cited = [lexemes[id_] for id_ in row["lexeme_ids"]] + [rules[id_] for id_ in row["rule_ids"]]
        forms.append({**row, "law_id": QUALIFIED_LAW_ID,
            "passage_ids": sorted({id_ for premise in cited for id_ in premise["passage_ids"]}),
            "review_sha256": QUALIFIED_REVIEW_SHA256,
            "authority": "SOURCE_REPLAYED_NATIVE_CONDITIONAL_INFLECTION",
            "native_form_derivation_checked": True, "native_acquisition_proof": False,
            "source_interpretation_kernel_proved": False, "native_receipt_sha256": receipt_sha256,
            "native_executable_sha256": executable_sha256})
    return {**review, "qualified_forms": forms, "native_derivation_receipt": receipt,
            "native_executable_sha256": executable_sha256}


def _unique_native_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_DUPLICATE_KEY")
        result[key] = value
    return result


def _reject_native_constant(value):
    raise _QualifiedCueVerificationError("QUALIFIED_NATIVE_NONFINITE_CONSTANT")

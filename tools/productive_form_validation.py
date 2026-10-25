"""Independent raw-source checks; no production parser or shape helper imported."""
from pathlib import Path
from hashlib import sha256
import json
import importlib.util
_spec = importlib.util.spec_from_file_location('productive_raw_nominal_validation',
                                              Path(__file__).with_name('source_name_validation.py'))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

POLICY_SHA256 = "faf134dabd4ce9d3718274c04660c1c7a9532d6c6f6a1072f2c1af67978e2003"
ROOT = Path(__file__).resolve().parents[1]


def policy():
    folder = ROOT / "src/nabt/data/source_evidence"
    raw = (folder / "productive_forms_v1.json").read_bytes()
    S.require(sha256(raw).hexdigest() == POLICY_SHA256, "productive source policy changed")
    result = json.loads(raw)
    for p in result["passages"]:
        source = (folder / (p["source_id"] + ".txt")).read_bytes()
        S.require(sha256(source).hexdigest() == p["source_sha256"] and
                  source[p["start"]:p["end"]].decode() == p["raw_text"], "productive passage changed")
    return result


def validate_imperative(candidate, audit):
    w = candidate["productive_derivation"]
    if w.get("law_id") == "nabt.sound-imperative-paradigm.v1":
        spec = importlib.util.spec_from_file_location('productive_paradigm_validation',
            Path(__file__).with_name('imperative_paradigm_validation.py'))
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        return validator.validate_imperative(candidate, audit)
    S.require(w["law_id"] == "nabt.productive-sound-imperative.v1" and
              w["policy_sha256"] == POLICY_SHA256 and w["target_attested"] is False and
              w["target_role_labels_used"] is False, "imperative authority changed")
    policy()
    receipts = candidate["supports"]
    S.require(receipts and sorted({r["record_id"] for r in receipts}) == w["source_support_ids"], "imperative receipts changed")
    for receipt in receipts:
        row = S._raw_support(receipt, audit)
        S.require(len([r for r in audit.records.values() if r["locator"][:3] == row["locator"][:3]]) == 1,
                  "attached source is outside productive scope")
        t = row["tokens"]
        form = S._decode(row["form"])
        root = S._decode(S._field(t, "ROOT:"), S.ROOT_BW)
        parts = S.clusters(form)
        S.require(row["tag"] == "V" and "IMPF" in t and "PASS" not in t and
                  w["source_profile"] in t and w["source_profile"] in ("3MS", "2MS", "3FS") and
                  S._field(t, "LEM:") == candidate["lemma_bw"] and
                  form == w["source_form"] and root == w["root"], "wrong imperative raw lexical premise")
        S.require(len(root) == 3 and len(set(root)) == 3 and not set(root) & set("اويءأإآؤئىة") and
                  len(parts) == 4 and parts[0] in (["ي", {"َ"}], ["ت", {"َ"}]) and
                  "".join(p[0] for p in parts[1:]) == root and parts[1][1] == {"ْ"} and
                  parts[2][1] in ({"َ"}, {"ِ"}, {"ُ"}) and parts[3][1] == {"ُ"}, "unsound imperfect template")
        vowel = "ُ" if parts[2][1] == {"ُ"} else "ِ"
        expected = [["ا", {vowel}], [root[0], {"ْ"}], parts[2], [root[2], {"ْ"}]]
        S.require(S.clusters(candidate["form"]) == expected and
                  w["generated_form"] == candidate["form"], "imperative output does not follow source")
    S.require(candidate["profile_id"] == "2MS" and candidate["aspect"] == "IMPV" and
              candidate["construction"] == "built" and not candidate["valency_witnesses"],
              "imperative acquired unsupported argument capacity")


def validate_nominal(row, inputs, audit):
    w = row["nominal_case_carrier"]
    S.require(audit is not None and w["law_id"] == "nabt.productive-accusative-alif.v1" and
              w["rule"] == "productive_accusative_alif" and w["generated_form"] is True and
              w["target_attested"] is False and w["target_role_labels_used"] is False and
              w["policy_sha256"] == POLICY_SHA256, "nominal productive authority changed")
    p = policy()
    S.require(w["source_passage"] == next(s for s in p["passages"] if s["source_id"] == "qatr" and s["line_start"] == 440),
              "nominal source passage changed")
    for name in ("base", "carrier"):
        S.check_span(w[name + "_span"], inputs, w[name + "_surface"])
    a, b = w["base_span"], w["carrier_span"]
    S.require(a["end"] == b["start"] and a["start"] == row["stem_span"]["start"] and
              b["end"] == row["stem_span"]["end"] and w["carrier_surface"] == "ا" and
              w["base_surface"] + "ا" == row["stem_surface"], "productive carrier moved")
    parts = S.clusters(w["base_surface"])
    S.require(parts[-1][1] & S.VOWELS == {"ً"} and parts[-1][0] not in "ءأإآؤئىيةاو" and
              all(m & S.VOWELS or (not m and i > 0 and c in "اوي" and
                  parts[i - 1][1] & S.VOWELS == {{"ا": "َ", "و": "ُ", "ي": "ِ"}[c]})
                  for i, (c, m) in enumerate(parts)), "productive target outside orthographic scope")
    proofs = w["base_paradigm_supports"]
    S.require(len({r["record_id"] for r in proofs}) >= 2 and w["source_supports"], "productive paired premise absent")
    first = S._raw_support(proofs[0], audit)
    features, derivation = S.raw_features(first)
    S.require(features["number"] == "singular" and features["root"] and
              all(row["lexical_features"].get(k) == features[k] for k in ("pos", "lemma", "root", "gender", "number")) and
              S.letters(features["lemma"]) == S.letters(w["base_surface"]), "nominal lexical identity changed")
    shadow = {"construction_supports": proofs, "construction_basis": "paired_lexical_terminal_realizations",
              "stem_surface": w["base_surface"]}
    S._construction_proven(shadow, features, derivation, audit)
    S.require(all(S.template(S._decode(S._raw_support(r, audit)["form"])) == S.template(w["base_surface"])
                  for r in proofs), "productive source and target internal marks differ")
    ordinary = []
    for raw in audit.records.values():
        if (raw["tag"] not in ("N", "PN", "ADJ") or raw["tokens"][0] != "STEM" or
                ":".join(map(str, raw["locator"][:2])) in audit.exclusions):
            continue
        if (S.raw_features(raw) == (features, derivation) and
                S.template(S._decode(raw["form"])) == S.template(w["base_surface"]) and
                S.clusters(S._decode(raw["form"]))[-1][1] & set("ًٌٍ")):
            ordinary.append(raw)
    S.require(ordinary, "ordinary declension lacks its own unexcluded tanwin observation")
    for receipt in [*proofs, *w["source_supports"]]:
        raw = S._raw_support(receipt, audit)
        S.require(S.raw_features(raw) == (features, derivation) and
                  len([r for r in audit.records.values() if r["locator"][:3] == raw["locator"][:3]]) == 1,
                  "productive receipt borrowed an attached or different lexical source")
    audit.walk(w)

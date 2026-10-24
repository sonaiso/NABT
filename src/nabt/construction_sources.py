"""Replay primary grammar passages for the bounded construction reader.

The passages license conditional grammatical rules. They do not contain the
answer, referent, dependency tree or case assignment for a new input sentence.
"""

from hashlib import sha1, sha256
from importlib.resources import files
import json

from .errors import NabtError

POLICY_ID = "nabt.construction-grammar-sources.v4"
EXPECTED_POLICY_SHA256 = "2faa90be033475c458eeabe61cda472c7856a0342803325bef6474c6c88b13f5"
SUPPLEMENTARY_REGISTRY = "construction_supplementary_sources_v2.json"
SUPPLEMENTARY_SCHEMA = "nabt.construction-supplementary-sources.v1"
EXPECTED_SUPPLEMENTARY_SHA256 = "96f505a0e34964e6b7fc65ed7dfaa6c0f5430c75a51766760495c25295ab1fe7"
SUPPLEMENTARY_RULES = {"sabban": ("inception_sharaa", "tamyiz_taba_nafs"),
                       "mukhtar_sihah": ("vocalized_hasiba_sense",)}
RULES = ("kana_sisters", "inna_sisters", "zanna_sisters", "kada_complement",
         "tense_aspect", "naat_agreement", "hal_attachment", "tamyiz_measure",
         "tamyiz_nisba", "badal_identity", "tawkeed_reference", "idafa_chain",
         "temporal_spatial_attachment", "counted_tens_forms", "counted_tens_specification",
         "counted_tens_paradigm", "attested_accusative_alif", "predicate_adjectival_agreement",
         "matrix_ma_negation", "explanatory_apposition", "prepositional_attachment",
         "inception_sharaa", "tamyiz_taba_nafs", "same_form_nominal_inflection",
         "vocalized_hasiba_sense")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated source-policy key")
        result[key] = value
    return result


def _supplementary_sources(directory, base_ids):
    """Replay the separate code-pinned registry; never extend the base manifest.

    These are exact bytes of a cleaned digital edition. File identity does
    not authenticate a printed page, every attribution, the proposed grammar
    interpretation, or any new event described by an input sentence.
    """
    raw = directory.joinpath(SUPPLEMENTARY_REGISTRY).read_bytes()
    if sha256(raw).hexdigest() != EXPECTED_SUPPLEMENTARY_SHA256:
        raise ValueError("Supplementary source registry pin differs")
    registry = json.loads(raw, object_pairs_hook=_unique)
    if registry["schema"] != SUPPLEMENTARY_SCHEMA or type(registry["sources"]) is not list:
        raise ValueError("Supplementary source registry schema differs")
    sources, metadata = {}, {}
    for source in registry["sources"]:
        sid = source["source_id"]
        if (sid not in SUPPLEMENTARY_RULES or sid in metadata or sid in base_ids or
                source["local_file"] != sid + ".txt" or
                source["allowed_rules"] != list(SUPPLEMENTARY_RULES[sid])):
            raise ValueError("Unregistered or repeated supplementary source")
        original = directory.joinpath(source["local_file"]).read_bytes()
        blob_sha = sha1(b"blob " + str(len(original)).encode("ascii") + b"\0" + original).hexdigest()
        if (sha256(original).hexdigest() != source["source_sha256"] or
                blob_sha != source["git_blob_sha1"] or
                type(source["bytes"]) is not int or source["bytes"] != len(original) or
                type(source["physical_lines"]) is not int or
                source["physical_lines"] != len(original.splitlines()) or
                source["source_bytes_modified_locally"] is not False):
            raise ValueError("Supplementary source bytes differ")
        sources[sid], metadata[sid] = original, source
    if set(metadata) != set(SUPPLEMENTARY_RULES):
        raise ValueError("Supplementary source inventory differs")
    return sources, metadata


def replay_construction_policy():
    """Check installed bytes, source identities, line spans and byte spans."""
    from .word_reader import replay_policy
    base = replay_policy()
    try:
        directory = files("nabt").joinpath("data/source_evidence")
        raw = directory.joinpath("construction_policy.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_POLICY_SHA256:
            raise ValueError("Construction source-policy digest differs")
        policy = json.loads(raw, object_pairs_hook=_unique)
        if (policy["policy_id"] != POLICY_ID or type(policy["schema_version"]) is not int
                or policy["schema_version"] != 1):
            raise ValueError("Construction source-policy identity differs")
        if policy.get("supplementary_source_registry") != {
                "file": SUPPLEMENTARY_REGISTRY, "sha256": EXPECTED_SUPPLEMENTARY_SHA256}:
            raise ValueError("Construction supplementary registry binding differs")
        sources, supplementary = _supplementary_sources(directory, base["sources"])
        rules, examples = {}, {}
        for passage in policy["passages"]:
            sid, rule = passage["source_id"], passage["rule"]
            if (sid not in base["sources"] and sid not in supplementary or
                    rule in rules or rule not in RULES):
                raise ValueError("Unknown source or repeated rule")
            if sid in supplementary:
                registered = supplementary[sid]
                if (rule not in registered["allowed_rules"] or
                        passage["source_commit"] != registered["commit"] or
                        passage["source_path"] != registered["path"] or
                        passage["source_sha256"] != registered["source_sha256"] or
                        passage.get("supplementary_registry_sha256") != EXPECTED_SUPPLEMENTARY_SHA256):
                    raise ValueError("Supplementary passage is not bound to its registered source")
            if sid not in sources:
                sources[sid] = directory.joinpath(sid + ".txt").read_bytes()
            original = sources[sid]
            start, end = passage["start"], passage["end"]
            lo, hi = passage["line_start"], passage["line_end"]
            lines = original.splitlines(keepends=True)
            if (type(start) is not int or type(end) is not int or
                    not 0 <= start < end <= len(original) or
                    type(lo) is not int or type(hi) is not int or not 1 <= lo <= hi <= len(lines)):
                raise ValueError("Invalid construction source span")
            excerpt = original[start:end]
            if (sha256(original).hexdigest() != passage["source_sha256"] or
                    sha256(excerpt).hexdigest() != passage["span_sha256"] or
                    excerpt.decode("utf-8") != passage["raw_text"] or
                    start != sum(map(len, lines[:lo - 1])) or end != sum(map(len, lines[:hi]))):
                raise ValueError("Construction source bytes or lines differ")
            rules[rule] = {k: passage[k] for k in ("source_id", "source_commit", "source_path",
                "source_sha256", "start", "end", "span_sha256", "line_start", "line_end", "premise_scope")}
            if sid in supplementary:
                rules[rule].update(source_layer=passage["source_layer"],
                    supplementary_registry_sha256=EXPECTED_SUPPLEMENTARY_SHA256,
                    selection_phase=passage["selection_phase"],
                    edition_authentication=supplementary[sid]["attribution"]["edition_authentication"])
            if rule == "tamyiz_nisba":
                # Acquire the two simple, explicitly exemplified verbal
                # constructions from the replayed primary paragraph. These
                # witnesses do not generalize every N after the same verb
                # into a specification; temporal and other uses remain open.
                import re
                triples = re.findall(r'[{"]([^{}"\n]+)[}"]', passage["raw_text"])
                models = [item.split() for item in triples if len(item.split()) == 3]
                examples["nisba_frames"] = [{"verb": m[0], "source_subject": m[1], "unit_form": m[2],
                                              "source_rule": rule}
                    for m in models if m[0] in ("اشتعل", "امتلأ")]
                if {m["verb"] for m in examples["nisba_frames"]} != {"اشتعل", "امتلأ"}:
                    raise ValueError("Primary nisba example structure differs")
            elif rule == "tamyiz_taba_nafs":
                import re
                model = re.search(r"نحو\s+(طاب)\s+(زيد)\s+(نفسا)\b", passage["raw_text"])
                if model is None or "والأصل طابت نفس زيد" not in passage["raw_text"]:
                    raise ValueError("Quoted transformed-subject example differs")
                examples.setdefault("nisba_frames", []).append({"verb": model[1], "source_subject": model[2],
                    "unit_form": model[3], "source_rule": rule,
                    "source_layer": passage["source_layer"], "transformation": "from_subject"})
        if set(rules) != set(RULES):
            raise ValueError("Construction source-policy inventory differs")
        return {"policy_id": POLICY_ID, "policy_sha256": EXPECTED_POLICY_SHA256,
                "supplementary_registry_sha256": EXPECTED_SUPPLEMENTARY_SHA256,
                "supplementary_source_ids": sorted(supplementary),
                "rules": rules, "examples": examples, "scope": policy["scope"]}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Construction grammar sources cannot be replayed",
                        status="DEFER") from error

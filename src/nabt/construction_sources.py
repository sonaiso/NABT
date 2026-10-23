"""Replay primary grammar passages for the bounded construction reader.

The passages license conditional grammatical rules. They do not contain the
answer, referent, dependency tree or case assignment for a new input sentence.
"""

from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError

POLICY_ID = "nabt.construction-grammar-sources.v1"
EXPECTED_POLICY_SHA256 = "51cd562baefd50a3de493fb88cb39f5b9442c648acdeedd02cdd3a75de378bb4"
RULES = ("kana_sisters", "inna_sisters", "zanna_sisters", "kada_complement",
         "tense_aspect", "naat_agreement", "hal_attachment", "tamyiz_measure",
         "tamyiz_nisba", "badal_identity", "tawkeed_reference", "idafa_chain",
         "temporal_spatial_attachment", "counted_tens_forms", "counted_tens_specification",
         "counted_tens_paradigm", "attested_accusative_alif")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated source-policy key")
        result[key] = value
    return result


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
        sources, rules, examples = {}, {}, {}
        for passage in policy["passages"]:
            sid, rule = passage["source_id"], passage["rule"]
            if sid not in base["sources"] or rule in rules or rule not in RULES:
                raise ValueError("Unknown source or repeated rule")
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
            if rule == "tamyiz_nisba":
                # Acquire the two simple, explicitly exemplified verbal
                # constructions from the replayed primary paragraph. These
                # witnesses do not generalize every N after the same verb
                # into a specification; temporal and other uses remain open.
                import re
                triples = re.findall(r'[{"]([^{}"\n]+)[}"]', passage["raw_text"])
                models = [item.split() for item in triples if len(item.split()) == 3]
                examples["nisba_frames"] = [{"verb": m[0], "source_subject": m[1], "unit_form": m[2]}
                    for m in models if m[0] in ("اشتعل", "امتلأ")]
                if {m["verb"] for m in examples["nisba_frames"]} != {"اشتعل", "امتلأ"}:
                    raise ValueError("Primary nisba example structure differs")
        if set(rules) != set(RULES):
            raise ValueError("Construction source-policy inventory differs")
        return {"policy_id": POLICY_ID, "policy_sha256": EXPECTED_POLICY_SHA256,
                "rules": rules, "examples": examples, "scope": policy["scope"]}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Construction grammar sources cannot be replayed",
                        status="DEFER") from error

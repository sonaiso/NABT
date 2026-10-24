"""Digest-checked conditional construction law, with no text acquisition.

Roles, senses, attachment and evidence are supplied premises. No function
here turns adjacency, a case sign, a caller digest, or an unobserved property
into a source license. The reader must acquire and replay those premises.
The exported role cases are constituent requirements, not actual assignments;
in particular kada's predicate is a clause with local nasb, whose internal
verb retains its independently established inflection.
"""

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError, natural

LAW_ID = "nabt.construction-evidence.v3"
EXPECTED_TABLE_SHA256 = "0d846cea228391001dfb9667dbd7358e994b012ee80fd35835ba85c2af8cd9ad"
SOURCE_POLICY_ID = "nabt.construction-grammar-sources.v4"
FAMILIES = ("kana", "inna", "zanna", "kada")
ROLES = ("kana_subject", "kana_predicate", "inna_subject", "inna_predicate",
         "zanna_subject", "zanna_object1", "zanna_object2", "kada_subject", "kada_predicate",
         "idafa_complement", "naat", "hal", "tamyiz", "badal", "tawkeed", "time_adverb", "place_adverb")
COMPATIBILITIES = ("possible", "confirmed", "conflict")
AGREEMENT_AXES = ("case", "definiteness", "gender", "number")
PREDICATE_AGREEMENT_AXES = ("gender", "number")
EVIDENCE_STATES = ("unknown", "affirmed", "denied", "conflict")
IDAFA_MODES = ("semantic", "verbal")
AN_HEADS = ("كاد", "كرب", "عسى", "أوشك", "حرى", "اخلولق", "inception")
ACTIVATION_BITS = ("identity_bound", "source_supported", "attachment_licensed",
                   "frame_complete", "sense_licensed", "unblocked")
IDENTITY_RELATIONS = ("badal_total", "badal_part", "badal_association", "tawkeed")
IDENTITY_BITS = ("relation_licensed", "identity_licensed")
SCOPES = ("belief", "certainty", "transformation", "proximity", "hope", "inception",
          "wish", "similitude", "continuation", "duration", "time_transition")
SCOPE_BITS = ("metadata_preserved", "source_supported", "frame_complete")
SCOPE_METADATA = ("family", "sense", "tense", "time", "place", "polarity", "restriction", "operator_binding")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated object key")
        result[key] = value
    return result


@lru_cache(maxsize=1)
def _table():
    try:
        raw = files("nabt").joinpath("data/construction_evidence.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("Construction law digest differs")
        table = json.loads(raw, object_pairs_hook=_unique_object)
        if (table["law_id"] != LAW_ID or type(table["schema_version"]) is not int
                or table["schema_version"] != 1 or table["source_policy_id"] != SOURCE_POLICY_ID):
            raise ValueError("Construction law identity differs")
        for key, expected in (("families", FAMILIES), ("roles", ROLES),
                              ("inherited_cases", (None, 0, 1, 2)),
                              ("compatibilities", COMPATIBILITIES), ("agreement_axes", AGREEMENT_AXES),
                              ("predicate_agreement_axes", PREDICATE_AGREEMENT_AXES),
                              ("evidence_states", EVIDENCE_STATES), ("idafa_modes", IDAFA_MODES),
                              ("activation_bits", ACTIVATION_BITS), ("identity_relations", IDENTITY_RELATIONS),
                              ("identity_bits", IDENTITY_BITS), ("scopes", SCOPES),
                              ("scope_bits", SCOPE_BITS), ("scope_metadata", SCOPE_METADATA)):
            if table[key] != list(expected):
                raise ValueError("Construction named domain differs: " + key)
        for key, size in (("operator_rows", 4), ("role_rows", 68), ("agreement_rows", 81),
                          ("predicate_agreement_rows", 18),
                          ("idafa_rows", 256), ("an_rows", 7), ("activation_rows", 256),
                          ("identity_rows", 16), ("scope_rows", 88)):
            if type(table[key]) is not list or len(table[key]) != size:
                raise ValueError("Construction finite inventory differs: " + key)
        return table
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Installed construction law cannot be replayed",
                        status="DEFER") from error


def installed_registry():
    """A copy of the checked finite law. It grants no source-reader authority."""
    return deepcopy(_table())


@lru_cache(maxsize=1)
def _indexes():
    table = _table()
    return {
        "operators": {r["family"]: r["slots"] for r in table["operator_rows"]},
        "roles": {(r["label"], r["inherited_case"]): r["case"] for r in table["role_rows"]},
        "agreement": {tuple(r[key] for key in AGREEMENT_AXES): r["status"] for r in table["agreement_rows"]},
        "predicate_agreement": {(r["regime_licensed"], r["gender"], r["number"]): r["status"]
                                for r in table["predicate_agreement_rows"]},
        "idafa": {(r["mode"], r["tanwin"], r["nun"], r["article"], r["article_exception"]): r["status"]
                  for r in table["idafa_rows"]},
        "an": {r["label"]: r for r in table["an_rows"]},
        "activation": {(r["family"], r["mask"]): r["allowed"] for r in table["activation_rows"]},
        "identity": {(r["label"], r["mask"]): r["allowed"] for r in table["identity_rows"]},
        "scope": {(r["scope"], r["mask"]): r["allowed"] for r in table["scope_rows"]},
        "bare": {r["scope"]: r["bare_projection"] for r in table["scope_rows"]},
    }


def _label(value, allowed, name):
    if type(value) is not str or value not in allowed:
        raise NabtError("INVALID_CONSTRUCTION_DOMAIN", name + " must be an installed label")
    return value


def _boolean(value, name):
    if type(value) is not bool:
        raise NabtError("INVALID_CONSTRUCTION_BOOLEAN", name + " must be an actual Boolean")
    return value


def _mask(names, values):
    return sum(int(_boolean(value, name)) << i for i, (name, value) in enumerate(zip(names, values)))


def operator_slots(family):
    """Requirements of a supplied, fully licensed operator sense and frame."""
    _label(family, FAMILIES, "operator_family")
    return deepcopy(_indexes()["operators"][family])


def role_case(label, inherited_case=None):
    """Return a constituent requirement, never an acquired role or sign.

    Naat, badal and tawkeed require a known nominal head case. This direct
    agreement law does not cover causal or exceptional adjective regimes.
    Hal and tamyiz refer to already licensed accusative nominal constructions;
    the independent numeral law still governs counted-noun case.
    """
    _label(label, ROLES, "conditional_role")
    if inherited_case is not None:
        natural(inherited_case, "inherited_nominal_case", maximum=2)
    return _indexes()["roles"][(label, inherited_case)]


def construction_allowed(family, *, identity_bound=False, source_supported=False,
                         attachment_licensed=False, frame_complete=False,
                         sense_licensed=False, unblocked=False):
    """Finite activation core. A caller Boolean is not a replayed witness."""
    _label(family, FAMILIES, "operator_family")
    mask = _mask(ACTIVATION_BITS, (identity_bound, source_supported, attachment_licensed,
                                    frame_complete, sense_licensed, unblocked))
    return _indexes()["activation"][(family, mask)]


def agreement_status(*, case="possible", definiteness="possible", gender="possible", number="possible"):
    values = (case, definiteness, gender, number)
    for axis, value in zip(AGREEMENT_AXES, values):
        _label(value, COMPATIBILITIES, axis + "_compatibility")
    return _indexes()["agreement"][values]


def predicate_agreement_status(*, regime_licensed=False, gender="possible", number="possible"):
    """Gender/number compatibility of a source-licensed direct predicate.

    A simple direct adjectival reading, its predication/reference edge and
    its agreement regime must be acquired separately. An ADJ tag, known
    gender, derivational origin or shape alone does not license the regime.
    Unlicensed regimes stay possible, including exceptional or jamid readings.
    Predicate case and definiteness are deliberately not comparison axes.
    """
    _boolean(regime_licensed, "predicate_regime_licensed")
    _label(gender, COMPATIBILITIES, "predicate_gender_compatibility")
    _label(number, COMPATIBILITIES, "predicate_number_compatibility")
    return _indexes()["predicate_agreement"][(regime_licensed, gender, number)]


def idafa_head_status(mode, tanwin="unknown", nun="unknown", article="unknown", *, article_exception=False):
    """Check supplied head evidence; ``nun`` means the inflection nun only.

    Unknown tanwin/nun does not count as their absence. A licensed verbal
    idafa article exception has no effect on canonical semantic idafa.
    """
    _label(mode, IDAFA_MODES, "idafa_mode")
    for name, value in (("tanwin", tanwin), ("inflection_nun", nun), ("article", article)):
        _label(value, EVIDENCE_STATES, name + "_evidence")
    _boolean(article_exception, "article_exception")
    return _indexes()["idafa"][(mode, tanwin, nun, article, article_exception)]


def complement_an_policy(label):
    """Policy conditional on operator sense; a preference is not prohibition."""
    return _indexes()["an"][_label(label, AN_HEADS, "an_operator")]["policy"]


def complement_an_preferred_present(label):
    return _indexes()["an"][_label(label, AN_HEADS, "an_operator")]["preferred_present"]


def complement_an_allowed(label, present):
    _label(label, AN_HEADS, "an_operator")
    _boolean(present, "an_present")
    return _indexes()["an"][label]["allows_present" if present else "allows_absent"]


def identity_preservation_allowed(label, *, relation_licensed=False, identity_licensed=False):
    """Total identity needs its own witness; part/association never imply it."""
    _label(label, IDENTITY_RELATIONS, "identity_relation")
    mask = _mask(IDENTITY_BITS, (relation_licensed, identity_licensed))
    return _indexes()["identity"][(label, mask)]


def scoped_projection_allowed(scope, *, metadata_preserved=False, source_supported=False, frame_complete=False):
    """Admit the unchanged outer scoped record, not its bare embedded claim."""
    _label(scope, SCOPES, "operator_scope")
    mask = _mask(SCOPE_BITS, (metadata_preserved, source_supported, frame_complete))
    return _indexes()["scope"][(scope, mask)]


def bare_projection_allowed(scope):
    """This conservative scoped law never exports an unqualified inner fact.

    This does not classify every lexical certainty reading as nonfactive;
    it requires any factive projection to have a separate licensed law.
    """
    return _indexes()["bare"][_label(scope, SCOPES, "operator_scope")]

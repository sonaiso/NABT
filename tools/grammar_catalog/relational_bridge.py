"""Source-bound relational licensing through the existing native reading owner.

The ledger is explicit evidence text, not a caller-supplied acceptance flag.
Lean replays that original source, fixed signed obligations and target span.
This adapter does not infer a real event or causal mechanism from morphology.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile

from tools import explainable_pilot as pilot
from tools import verified_reading as reading
from tools.evidence_lifecycle_v1 import _encoded
from .operations import ROOT

LAW = "nabt.relational-bridge.v2"
CONTINUITY_LAW = "nabt.relational-continuity.v1"
DATA = "tools/grammar_catalog/data/relational_readings_v1.json"
FRAME_FIELDS = {"reading_id", "stage", "occurrence_id", "entity", "kind", "property",
                "event", "time", "place", "cause", "start", "stop", "surface"}


def lexical_cards():
    document = json.loads((ROOT / DATA).read_text())
    return [{"id":"reading:"+r["id"], "kind":"reviewed_relational_reading",
             "label":r["label"], "description":r["description"],
             "reading":r, "source_review":document["sources"],
             "related_proof_families":["mantuq-mafhum"],
             "source_review_sha256":sha256((ROOT/DATA).read_bytes()).hexdigest(),
             "application_certified":False} for r in document["readings"]]


def contract_cards():
    rows=[("disposition","القابلية المشروطة والخواص","قابلية الجنس والفرد تحتاج ربط الخاصية وشروطها ونفي المانع؛ لا وقوع من القابلية.","capability_does_not_supply_occurrence"),
          ("occurrence","وقوع الحدث وحامل التغير","شاهد الوقوع مستقل عن المصدر الصرفي واسم الفاعل والإرادة.","licensed_obligation_derivable"),
          ("causality","السببية والمسببية والتجاور والتتابع","دليل السبب والأثر مستقل عن المكان والزمان والمصاحبة.","adjacency_and_time_do_not_supply_cause"),
          ("withdrawal","سحب شاهد السبب وإعادة التحقق","سحب الشاهد يوجب إعادة فحص المصدر؛ تبقى حقائق التجاور والتتابع والسند البديل دون ترقية.","changed_source_rejects_old_license")]
    return [{"id":"bridge:"+key,"kind":"installed_relational_contract","label":label,
             "description":description,"owner_path":"formal/Nabt/RelationalBridge.lean",
             "runtime_path":"tools/grammar_catalog/relational_bridge.py",
             "theorem_names":["Nabt.RelationalBridge."+theorem],
             "test_path":"tests/test_relational_bridge.py",
             "related_proof_families":["mantuq-mafhum"],
             "retrieval_is_application_certificate":False} for key,label,description,theorem in rows]


def validate(bridge):
    if type(bridge) is not dict or set(bridge) != {"source_text","source_id","revision","scope","frame"}:
        raise ValueError("Relational bridge requires independently retained source, identity and frame")
    _encoded(bridge, 131072)
    for name, bound in (("source_text",65536),("source_id",512),("revision",512),("scope",512)):
        value=bridge[name]
        if type(value) is not str or not value.strip() or len(value.encode())>bound:
            raise ValueError("Invalid relational bridge "+name)
    f=bridge["frame"]
    if type(f) is not dict or set(f)!=FRAME_FIELDS:
        raise ValueError("Relational frame fields differ from installed law")
    if type(f["reading_id"]) is not str or f["reading_id"] not in {r["reading"]["id"] for r in lexical_cards()}:
        raise ValueError("Unknown reviewed reading")
    if type(f["stage"]) is not str or f["stage"] not in {"disposition","occurrence","causality"}:
        raise ValueError("Unknown relational stage")
    for key in FRAME_FIELDS-{"start","stop","surface","stage"}:
        if type(f[key]) is not str or len(f[key].encode())>512 or not reading.valid_name(f[key]):
            raise ValueError("Invalid relational identity: "+key)
    for key in ("start","stop"):
        if type(f[key]) is not int or not 0<=f[key]<=8192:
            raise ValueError("Expected bounded Unicode scalar offset")
    if type(f["surface"]) is not str or not f["surface"] or len(f["surface"].encode())>512:
        raise ValueError("Invalid occurrence surface")
    return deepcopy(bridge)


def evaluate(target, bridge):
    p=validate(bridge)
    f=p["frame"]
    raw=p["source_text"].encode()
    # The fixed query only requests a full source closure from the existing
    # proposer; it cannot replace any of Lean's installed obligation profiles.
    query=("هل "+f["event"]+" وقوع "+f["entity"]+"؟\n").encode()
    result={"schema":LAW, "status":"DEFER", "licensed":False,
            "scope":"SOURCE_RELATIVE_CONTROLLED_RELATIONAL_LEDGER",
            "frame":f, "ledger":{k:p[k] for k in ("source_text","source_id","revision","scope")},
            "target_sha256":sha256(target.encode()).hexdigest(),
            "world_truth_established":False, "empirical_causality_established":False,
            "grammar_acquisition_proved":False, "reading_domain_complete_for_all_arabic":False,
            "native_receipt":None, "source_analysis":None, "kernel_certificate":None,
            "checker_sha256":None, "ontology_assertions":[]}
    try:
        c=pilot.propose_certificate(raw,query,p["source_id"],p["revision"],p["scope"])
        result["kernel_certificate"]=c
        binary=ROOT/"formal/.lake/build/bin/verifiedReading"
        fingerprint=pilot.file_sha(binary)
        with tempfile.TemporaryDirectory(prefix="nabt-relational-") as temp:
            paths=[Path(temp)/name for name in ("source","query","certificate","frame","target")]
            content=[raw,query,pilot.wire(c).encode(),pilot.wire(f).encode(),target.encode()]
            for path,data in zip(paths,content,strict=True):
                path.write_bytes(data)
            run=subprocess.run([str(binary),"relational",*map(str,paths),p["source_id"],p["revision"],p["scope"]],
                               capture_output=True,timeout=20)
        if pilot.file_sha(binary)!=fingerprint:
            raise pilot.PilotError("CHECKER_CHANGED","native checker changed")
        native=pilot.strict_json(run.stdout)
        if run.returncode!=0 or native.get("verified") is not True:
            raise pilot.PilotError(native.get("error","CERTIFICATE_REJECTED"),"native bridge rejected input")
        if (native.get("bridge_law_id")!=LAW or type(native.get("licensed")) is not bool
                or native.get("source_text")!=p["source_text"] or native.get("target_text")!=target
                or native.get("source_id")!=p["source_id"] or native.get("revision")!=p["revision"]
                or native.get("source_scope")!=p["scope"] or native.get("selected_reading")!=f["reading_id"]
                or native.get("world_truth_established") is not False):
            raise pilot.PilotError("CHECKER_PROTOCOL_ERROR","native binding mismatch")
        result.update(native_receipt=native,checker_sha256=fingerprint,
                      source_analysis=pilot.analysis(c,raw),licensed=native["licensed"])
        if native["licensed"]:
            result.update(status="SCOPED_SOURCE_LICENSE",ontology_assertions=[{
                "stage":f["stage"],"frame":deepcopy(f),"authority":"SOURCE_RELATIVE",
                "rule_reference":"Nabt.RelationalBridge.v2_event_property_derivable"}])
        elif native["qualified_verdict"]=="CONFLICT":
            result["status"]="CONFLICT"
        elif native["qualified_verdict"]=="REFUTED_PREMISE":
            result["status"]="REFUTED"
        result["missing"]=[r for r in native["requirements"] if not r["present"] or not r["clean"] or r["opposed"]]
    except pilot.PilotError as e:
        result.update(status=e.code,reason=str(e))
    except subprocess.TimeoutExpired:
        result.update(status="RESOURCE_LIMIT",reason="Native relational timeout")
    except OSError:
        result.update(status="VERIFICATION_UNAVAILABLE",reason="Native relational checker unavailable")
    _encoded(result,2*1048576)
    return result


def _schema_native(command, payload=None):
    """One native owner for schemas and structural validation, never truth."""
    binary = ROOT / "formal/.lake/build/bin/verifiedReading"
    fingerprint = pilot.file_sha(binary)
    with tempfile.TemporaryDirectory(prefix="nabt-continuity-") as temp:
        args = [str(binary), command]
        if payload is not None:
            path = Path(temp) / "request.json"
            path.write_text(pilot.wire(payload), encoding="utf-8")
            args.append(str(path))
        run = subprocess.run(args, capture_output=True, timeout=20)
    if pilot.file_sha(binary) != fingerprint:
        raise ValueError("Native schema checker changed")
    result = pilot.strict_json(run.stdout)
    if (run.returncode != 0 or result.get("verified") is not True
            or result.get("continuity_law_id") != CONTINUITY_LAW):
        raise ValueError("Native schema checker rejected input")
    result["checker_sha256"] = fingerprint
    return result


def schema_catalogue():
    result = _schema_native("relational-schemas")
    native = [(r["reading_id"], r["spellings"], r["schema"]["sense"]) for r in result["schemas"]]
    reviewed = [(r["reading"]["id"], r["reading"]["spellings"], r["reading"]["sense"])
                for r in lexical_cards()]
    if native != reviewed:
        raise ValueError("Native meaning identities and lexical review disagree")
    return result


def check_bindings(reading_id, bindings):
    """Internal structural check; a valid value still needs source evidence."""
    return _schema_native("relational-schema", {"reading_id": reading_id, "bindings": bindings})


def continuity(target, bridge_result=None):
    """Retain all installed exact readings and their open ontological slots.

    Only native, source-bound obligations can bind an occurrence. A schema
    label reference names the installed concept; it adds no grammatical reading.
    This helper has no public route accepting a caller's bridge receipt.
    """
    from .operations import exact_terms
    result = {"schema": CONTINUITY_LAW, "status": "DEFER", "occurrences": [],
              "authority": "INSTALLED_SCHEMA_STRUCTURE_ONLY", "world_truth_established": False,
              "grammar_acquisition_proved": False, "alternatives_pruned": False,
              "schema_label_is_grammatical_analysis": False}
    try:
        catalogue = schema_catalogue()
        matches = []
        for token in exact_terms(target):
            candidates = [(r, "reviewed_surface" if token["surface"] in r["spellings"] else "schema_label_reference")
                          for r in catalogue["schemas"]
                          if token["surface"] in r["spellings"] or token["surface"] == r["schema"]["sense"]]
            if candidates:
                matches.append((token, candidates))
        if sum(len(cs) for _, cs in matches) > 128:
            result.update(status="RESOURCE_LIMIT", reason="Exact schema candidates exceed 128; none truncated")
            return result
        bridge_result = bridge_result or {}
        native = bridge_result.get("native_receipt") or {}
        frame = bridge_result.get("frame", {})
        if native and bridge_result.get("checker_sha256") != catalogue["checker_sha256"]:
            raise ValueError("Schema and source checks used different native owners")
        for token, candidates in matches:
            rows = []
            for record, match_kind in candidates:
                schema = record["schema"]
                general = [{"slot": slot, "state": "unbound_variable", "value": ""}
                           for slot in schema["slots"]]
                checked = check_bindings(record["reading_id"], general)
                if (checked["checker_sha256"] != catalogue["checker_sha256"]
                        or checked.get("schema") != schema or not checked.get("structurally_valid")
                        or checked.get("binding_evidence_checked") is not False):
                    raise ValueError("Schema structure or owner mismatch")
                row = {"reading_id": record["reading_id"], "match_kind": match_kind,
                       "ontological_signature": schema, "general_bindings": general,
                       "structure_receipt": checked, "occurrence_bindings": None,
                       "occurrence_license": False}
                if (match_kind == "reviewed_surface" and native.get("occurrence_bound") is True
                        and native.get("selected_reading") == record["reading_id"]
                        and token["codepoint_span"] == [frame.get("start"), frame.get("stop")]):
                    requirements = native["requirements"]
                    # Requirements are fixed by Lean for this exact frame; every
                    # accepted binding also retains the native signed witnesses.
                    good = {q["predicate"] for q in requirements
                            if q["present"] and q["clean"] and not q["opposed"]}
                    core = {"نص", "موضع", "قراءة", "حدث", "معنى"}
                    dependencies = {
                        "event": ("event", set()),
                        "bearer": ("entity", {"حامل"}),
                        "genus": ("kind", {"حامل", "عضوية"}),
                        "property": ("property", {"حامل", "خاصية", "حالة", "يقبل", "يحول"}),
                        "time": ("time", {"زمان"}), "place": ("place", {"مكان"})}
                    bound = []
                    for slot in schema["slots"]:
                        field, extra = dependencies[slot]
                        supported = core | extra <= good
                        bound.append({"slot": slot,
                                      "state": "bound_value" if supported else "unknown_in_occurrence",
                                      "value": frame[field] if supported else ""})
                    occurrence = check_bindings(record["reading_id"], bound)
                    if (not occurrence["structurally_valid"] or occurrence["schema"] != schema
                            or occurrence["checker_sha256"] != catalogue["checker_sha256"]):
                        raise ValueError("Occurrence changed its schema")
                    row.update(occurrence_bindings=bound, occurrence_structure_receipt=occurrence,
                               binding_authority="SOURCE_RELATIVE", binding_witnesses=requirements,
                               occurrence_license=bridge_result["licensed"])
                rows.append(row)
            result["occurrences"].append({**token, "candidates": rows})
        result.update(status="SCHEMAS_RETAINED" if matches else "NO_INSTALLED_EXACT_SCHEMA",
                      checker_sha256=catalogue["checker_sha256"])
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, pilot.PilotError) as error:
        result.update(status="VERIFICATION_UNAVAILABLE", reason=type(error).__name__, occurrences=[])
    return result

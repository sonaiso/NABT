"""Execute existing ordered-unit and Arabic owners without promoting their scope."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from math import comb
from pathlib import Path
import subprocess
import tempfile

from nabt.codec import encode_cells, decode_number
from nabt.errors import NabtError
from nabt.learning.source_evidence import SourceBlob
from nabt.machine import Machine, compose_effects
from tools.evidence_lifecycle_v1 import ResourceLimit, _encoded
from .sign_curriculum import SYLLABLE_TARGETS, _check_quota

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "nabt.unit-composition-agent.v1"
MAX_REPORT = 8 * 1048576
PAIR_BASIS = ("C", "V", *SYLLABLE_TARGETS)


def wire(value):
    from tools.recursive_bridge import _application_wire
    try:
        raw = _application_wire(value)
    except NabtError as exc:
        if exc.code == "RESOURCE_LIMIT": raise ResourceLimit(exc.message) from exc
        raise
    if len(raw) > MAX_REPORT:
        raise ResourceLimit("Unit report byte budget exceeded")
    return raw.decode("utf-8")


def read_json(raw):
    from tools.recursive_bridge import load_application_bytes
    if len(raw) > MAX_REPORT:
        raise ResourceLimit("Unit JSON byte budget exceeded")
    try:
        return load_application_bytes(raw)
    except NabtError as exc:
        if exc.code == "RESOURCE_LIMIT": raise ResourceLimit(exc.message) from exc
        raise


class NativeUnavailable(Exception):
    pass


def _fields(request, required, optional=()):
    if type(request) is not dict or not set(required) <= request.keys() or set(request) - set(required) - set(optional):
        raise ValueError("Unknown or missing unit-agent request fields")


def _natural(value, maximum):
    if type(value) is not int or value < 0:
        raise ValueError("Expected a natural integer, not a Boolean")
    if value > maximum:
        raise ResourceLimit("Unit-agent enumeration budget exceeded")
    return value


def _text(value, maximum=2048):
    if type(value) is not str or not value:
        raise ValueError("Expected nonempty exact source text")
    if len(value.encode("utf-8")) > maximum:
        raise ResourceLimit("Unit-agent text budget exceeded")
    return value


class NativeSession:
    """Fixed installed entry point; preserve and validate every actual reply."""
    def __init__(self):
        self.calls = []
        self.binary_sha256 = None

    def call(self, requests):
        from tools.entropy_framework.reuse_run import entry_command
        from tools.check_progressive_units import validate_response
        if not requests or len(requests) > 128:
            raise ResourceLimit("Native batch request budget exceeded")
        _encoded(requests, 256 * 1024)
        try:
            command = entry_command("progressive", [], root=ROOT)
            executable = Path(command[0])
            before = sha256(executable.read_bytes()).hexdigest()
        except FileNotFoundError as exc:
            raise NativeUnavailable("Build the installed progressiveUnitProbe") from exc
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            try:
                run = subprocess.run(command, input=("".join(wire(r) + "\n" for r in requests)).encode(),
                    stdout=out, stderr=err, cwd=ROOT, timeout=60, check=False)
            except subprocess.TimeoutExpired as exc:
                raise ResourceLimit("Native unit probe time budget exceeded") from exc
            except FileNotFoundError as exc:
                raise NativeUnavailable("Installed progressiveUnitProbe became unavailable") from exc
            out.seek(0); raw = out.read(MAX_REPORT + 1)
            err.seek(0); errors = err.read(4096)
        if len(raw) > MAX_REPORT:
            raise ResourceLimit("Native unit probe output budget exceeded")
        if run.returncode or errors or sha256(executable.read_bytes()).hexdigest() != before:
            raise ValueError("Native unit probe execution or identity failed")
        if self.binary_sha256 not in (None, before):
            raise ValueError("Native binary changed during one operation")
        self.binary_sha256 = before
        lines = raw.splitlines()
        if len(lines) != len(requests):
            raise ValueError("Native unit response count differs")
        replies = []
        for request, line in zip(requests, lines):
            response = read_json(line)
            validate_response(request, response)
            self.calls.append({"request": deepcopy(request), "response": response})
            if response["status"] == "ERROR":
                if response["error"] == "RESOURCE_LIMIT":
                    raise ResourceLimit(response["message"])
                raise ValueError("Native owner rejected the typed unit input")
            replies.append(response)
        return replies


def _enumerate(request, native):
    _fields(request, ("op",), ("max_c", "max_v", "include_pairs"))
    c = _natural(request.get("max_c", 4), 4)
    v = _natural(request.get("max_v", 4), 4)
    pairs = request.get("include_pairs", True)
    if type(pairs) is not bool:
        raise ValueError("include_pairs must be Boolean")
    if c + v == 0:
        raise ValueError("The nonempty unit curriculum needs a positive quota")
    quotas = [{"op":"quota", "consonants":i, "vowels":j, "max_atoms":8}
              for i in range(c + 1) for j in range(v + 1) if i + j]
    products = [{"op":"compose_shapes", "parts":[a,b], "max_atoms":12}
                for a in PAIR_BASIS for b in PAIR_BASIS] if pairs else []
    replies = native.call(quotas + products)
    for q, r in zip(quotas, replies):
        _check_quota(q, r)
    return {"status":"ENUMERATED", "quota_domains":len(quotas),
        "ordered_shape_count":sum(comb(q["consonants"]+q["vowels"],q["consonants"]) for q in quotas),
        "pair_basis":list(PAIR_BASIS), "ordered_pairs":len(products),
        "syllable_pairs":len(SYLLABLE_TARGETS)**2 if pairs else 0,
        "quota_results":replies[:len(quotas)], "pair_results":replies[len(quotas):],
        "search_complete_for_declared_domain":True, "arabic_license_inferred":False}


def _shape(request, native):
    _fields(request, ("op","parts"), ("max_atoms",))
    parts = request["parts"]
    if type(parts) is not list or not 1 <= len(parts) <= 12 or any(
            type(p) is not str or not p or set(p)-{"C","V"} for p in parts):
        raise ValueError("Use a nonempty ordered list of C/V shapes")
    bound = _natural(request.get("max_atoms",12),12)
    shape = "".join(parts)
    if len(shape) > bound:
        raise ResourceLimit("Compound shape exceeds max_atoms")
    composed, forest = native.call([
        {"op":"compose_shapes","parts":parts,"max_atoms":bound},
        {"op":"forest","shape":shape,"max_atoms":8}])
    return {"status":"COMPOSED", "composition":composed, "forest":forest,
        "assembly_id":sha256(wire(parts).encode()).hexdigest(),
        "same_surface_does_not_identify_assembly":True,
        "forest_complete":forest.get("search_complete",False), "arabic_license_inferred":False}


def _cell_page(request, native):
    """Address the complete fixed-length A116 space using the installed codec.

    A page is not an exhaustive search of prior pages, or a source acquisition.
    This is the large Cartesian space, distinct from the 250 C/V shapes.
    """
    _fields(request,("op","length"),("offset","limit","mode"))
    length = _natural(request["length"],4)
    if not length: raise ValueError("Cell products are nonempty")
    total = 116**length
    offset = request.get("offset",0)
    if type(offset) is not int or not 0 <= offset < total:
        raise ValueError("Cell-page offset is outside the declared Cartesian domain")
    limit = _natural(request.get("limit",16),128)
    if not limit: raise ValueError("Cell pages are nonempty")
    mode = request.get("mode","wasl")
    if type(mode) is not str or mode not in ("wasl","waqf"):
        raise ValueError("Unknown machine ending mode")
    first_number = encode_cells([0]*length)
    stop = min(total,offset+limit)
    cells = [list(decode_number(first_number+i)) for i in range(offset,stop)]
    replies = native.call([{"op":"cell_effect","cells":c,"mode":mode,"entry":0} for c in cells])
    return {"status":"CELL_PRODUCT_PAGE","alphabet_id":"nabt.a116.v1","length":length,
        "order":"LEXICOGRAPHIC_CELL_ID","domain_count":total,"offset":offset,"count":stop-offset,
        "next_offset":stop if stop<total else None,"reached_domain_end":stop==total,
        "whole_domain_measured":offset==0 and stop==total,"numeric_first":first_number+offset,
        "cells":cells,"receipts":replies,"source_acquired":False,"arabic_role_license_granted":False}


def _read(text, source_id):
    from nabt.word_reader import read_words
    from nabt.derivation import read_derivation
    return {"word_owner":read_words(text,source_id=source_id,scope=SCHEMA),
        "derivation_owner":read_derivation(text,source_id=source_id,scope=SCHEMA)}


def _acquire_host(surface, source_id, mode):
    """Route an article citation to its installed native owner.

    The prefix only selects an owner. Its exact finite reading, pinned sources
    and fresh native replay still decide admission. Failures of the first owner
    are never recovered by trying another owner.
    """
    from tools import aligned_acquisition as base, connected_acquisition_v3 as article
    first = base.read_acquired(surface, source_id=source_id, scope=SCHEMA, ending=mode)
    if (first.get("verified") is not True or first.get("status") not in ("ACQUIRED", "DEFER")
            or not article._article_shaped(first["acquisition"]["pieces"])):
        return first, None
    selected = article.read_acquired(surface, source_id=source_id, scope=SCHEMA,
                                     ending=mode, onset="word_initial")
    return selected, first


def _compose(request, native):
    from nabt.word_reader import _scan
    _fields(request,("op","parts","separators"),("mode","source_id"))
    parts, separators = request["parts"], request["separators"]
    if type(parts) is not list or not 1 <= len(parts) <= 8:
        raise ValueError("Use one to eight exact written parts")
    if type(separators) is not list or len(separators) != len(parts)-1 or any(s not in ("", " ") for s in separators):
        raise ValueError("Supply exactly one empty or space separator per boundary")
    mode = request.get("mode","wasl")
    if type(mode) is not str or mode not in ("wasl","waqf"):
        raise ValueError("Unknown machine ending mode")
    for part in parts:
        _text(part)
        partition = _scan(SourceBlob("part",part.encode()))
        if len(partition) != 1 or partition[0]["kind"] != "written_run":
            raise ValueError("A part cannot cross word, quote or punctuation boundaries")
    text = parts[0] + "".join(s+p for s,p in zip(separators,parts[1:]))
    _text(text)
    source = SourceBlob(request.get("source_id","unit_source"),text.encode())
    pieces, groups, position = [], [[]], 0
    for i, part in enumerate(parts):
        if i:
            position += len(separators[i-1].encode())
            if separators[i-1]: groups.append([])
        end = position + len(part.encode())
        row = {"index":i,"word_index":len(groups)-1,"text":part,"span":[position,end]}
        pieces.append(row); groups[-1].append(row); position = end
    words = []
    for word_index, group in enumerate(groups):
        word_mode = mode if word_index == len(groups)-1 else "wasl"
        machine = Machine(word_mode)
        surface = "".join(p["text"] for p in group)
        row = {"text":surface,"mode":word_mode,"span":[group[0]["span"][0],group[-1]["span"][1]],
               "part_indices":[p["index"] for p in group]}
        try:
            acquisition, prior = _acquire_host(surface, source.source_id, word_mode)
            row["acquisition_owner"] = acquisition
            if prior is not None:
                row["prior_acquisition_owner"] = prior
                row["acquisition_dispatch"] = {
                    "policy": "nabt.unit-article-dispatch.v1",
                    "condition": "VERIFIED_V1_REPRESENTATION_AND_ARTICLE_SHAPED_HOST",
                    "selected_law": "nabt.sourced-acquisition.v3",
                    "onset": "word_initial", "connected_speech_established": False}
            if acquisition["status"] == "RESOURCE_EXHAUSTED":
                raise ResourceLimit("Acquisition owner resource budget exceeded")
            if not acquisition["verified"] or acquisition["status"] != "ACQUIRED":
                row["status"] = "DEFER_EXACT_A116_READING"
                words.append(row)
                continue
            acquired = acquisition["acquisition"]
            if len(acquired["words"]) != 1:
                raise ValueError("One composed host must acquire exactly one word")
            effects = []
            for part in group:
                start,end = [n-row["span"][0] for n in part["span"]]
                selected = [p for p in acquired["pieces"] if start <= p["byte_start"] and p["byte_end"] <= end]
                if not selected or "".join(p["raw"] for p in selected) != part["text"]:
                    raise ValueError("A part boundary splits an acquired source piece")
                effects.append(machine.effect(c for p in selected for c in p["cells"]))
            joined = effects[0]
            for effect in effects[1:]: joined = compose_effects(joined,effect)
            original_cells = tuple(acquired["words"][0]["cells"])
            if joined.cells != original_cells:
                raise ValueError("A part boundary splits an A116 source unit")
            reply, = native.call([{"op":"cell_effect","cells":list(joined.cells),"mode":word_mode,"entry":0}])
            if any(r["exit"] != joined.destinations[r["entry"]] or r["weight"] != joined.weights[r["entry"]]
                   for r in reply["effect"]):
                raise ValueError("Composed effect differs from native full-state replay")
            row.update(status="CELL_EFFECT_REPLAYED", unit_n=encode_cells(joined.cells),
                piece_effects=[e.as_dict() for e in effects], effect=joined.as_dict(), native_receipt=reply)
        except NabtError as exc:
            if exc.code == "RESOURCE_LIMIT": raise ResourceLimit(exc.message) from exc
            row.update(status="DEFER_EXACT_A116_READING", owner_error=exc.as_dict())
        words.append(row)
    return {"status":"COMPOSED_SOURCE", "source_id":source.source_id,"source_sha256":source.sha256,
        "text":text,"pieces":pieces,"words":words,"separators":deepcopy(separators),
        "source_restored":text.encode()==source.raw_bytes,
        "word_boundaries_preserved":True,"cross_word_effect_composed":False,
        "readings":_read(text,source.source_id),"arabic_role_license_granted":False}


def _phonology(request, native):
    from nabt.phonological_modes import realize, replay_policy, VOWELS
    _fields(request,("op","example_id"),("start","end","profile","following_id"))
    options = {k:request[k] for k in ("start","end","profile","following_id") if k in request}
    projection = realize(request["example_id"],**options)
    if projection["status"] != "CONDITIONAL_PROJECTION":
        return {"status":"DEFER","phonological_owner":projection}
    inventory = sorted({p for e in replay_policy()["examples"] for p in e["body"] if p not in VOWELS} | {"ʔ","n","h","t"})
    rows = []
    for alternative in projection["alternatives"]:
        segments = [{"kind":"vowel","quality":("a","i","u").index(p[0]),
                     "quantity":"long" if p.endswith(":") else "short"} if p in VOWELS else
                    {"kind":"consonant","id":inventory.index(p)} for p in alternative["segments"]]
        quantity, = native.call([{"op":"quantity","segments":segments}])
        expected = "".join("VV" if p.endswith(":") else "V" if p in VOWELS else "C" for p in alternative["segments"])
        if quantity.get("shape") != expected or quantity.get("source_aligned_license") is not False:
            raise ValueError("Native quantity projection differs from the supplied owner segments")
        if len(expected) > 12:
            rows.append({"quantity":quantity,"partition_status":"RESOURCE_LIMIT","syllable_partitions":None})
            continue
        shape, = native.call([{"op":"shape","shape":expected,"max_atoms":12}])
        partitions = [p for p in shape["partitions"] if all(s in SYLLABLE_TARGETS for s in p)]
        rows.append({"quantity":quantity,"partition_status":"ENUMERATED", "shape_owner":shape,
            "syllable_partitions":partitions,"phonotactic_applicability_of_each_partition":"NOT_ESTABLISHED"})
    return {"status":"SOURCE_RELATIVE_PHONOLOGICAL_PROJECTION", "phonological_owner":projection,
        "consonant_id_inventory":inventory,"alternatives":rows,"acoustic_validation":False,
        "syllable_license_granted":False}


def _source(request, native):
    from nabt.word_reader import _scan
    _fields(request,("op","text"),("source_id","mode"))
    text=_text(request['text'],8192)
    source=SourceBlob(request.get('source_id','input'),text.encode())
    segments=_scan(source)
    runs=[s for s in segments if s['kind']=='written_run']
    if len(runs)>32: raise ResourceLimit('Source-unit written-run budget exceeded')
    results=[]
    for s in runs:
        result=_compose({'op':'compose','parts':[s['surface']],'separators':[],
                         'source_id':source.source_id,'mode':request.get('mode','wasl')},native)
        results.append({'source_span':s['span'],'surface':s['surface'],'owner_result':result})
    return {'status':'SOURCE_UNIT_VIEWS','source_id':source.source_id,'source_sha256':source.sha256,
            'segments':segments,'written_runs':results,'source_restored':''.join(s['surface'] for s in segments)==text,
            'quoted_runs_acquired':False,'word_boundaries_preserved':True,'general_grammar_license':False}


def _generate(request, native):
    from nabt.derivation import generate_derivation
    _fields(request,("op","root","pattern_id"),("ending",))
    generated = generate_derivation(request["root"],request["pattern_id"],ending=request.get("ending",""))
    lower = _compose({"op":"compose","parts":[generated["surface"]],"separators":[],"mode":"wasl"},native)
    return {"status":"FORMAL_PATTERN_GENERATED", "generator_owner":generated,"lower_trace":lower,
        "weak_realization_needed":bool(set(request["root"]) & set("وي")),
        "attested_root":False,"attested_word":False,"lexical_meaning_assigned":False}


def execute(request):
    _encoded(request, 32768)
    if type(request) is not dict or type(request.get("op")) is not str:
        raise ValueError("Expected a typed unit-agent operation")
    if "source_id" in request:
        _text(request["source_id"], 256)
    from tools.grammar_catalog.operations import source_snapshot, digest
    snapshot, _ = source_snapshot()
    native = NativeSession()
    handlers = {"enumerate":_enumerate,"shape":_shape,"cell_page":_cell_page,"compose":_compose,
                "phonology":_phonology,"generate":_generate,"source":_source}
    try:
        if request["op"] in handlers:
            result = handlers[request["op"]](request,native)
        elif request["op"] == "read":
            _fields(request,("op","text"),("source_id",))
            result = {"status":"OWNER_READINGS", **_read(_text(request["text"]),request.get("source_id","unit_source"))}
        elif request["op"] == "weak_application":
            from tools.derivation_surface_bridge import evaluate_derivation_surface
            _fields(request,("op","text","application"),("source_id",))
            result = {"status":"OWNER_APPLICATION", "owner":evaluate_derivation_surface(
                _text(request["text"]),request["application"],source_id=request.get("source_id","unit_source"),scope=SCHEMA)}
        elif request["op"] == "paradigm":
            from nabt.verb_paradigm import read_verb_paradigm
            _fields(request,("op","text"),("source_id",))
            result = {"status":"OWNER_PARADIGM", "owner":read_verb_paradigm(
                _text(request["text"]),source_id=request.get("source_id","unit_source"),scope=SCHEMA)}
        else:
            raise ValueError("Unknown installed unit-agent operation")
    except NativeUnavailable as exc:
        result = {"status":"DEFER","reason":"NATIVE_PROBE_UNAVAILABLE","detail":str(exc)}
    except NabtError as exc:
        if exc.code == "RESOURCE_LIMIT": raise ResourceLimit(exc.message) from exc
        result = {"status":"OWNER_"+exc.status,"owner_error":exc.as_dict()}
    report = {"schema":SCHEMA,"request":deepcopy(request),"result":result,
        "execution_snapshot_sha256":digest(snapshot),
        "snapshot_recipe":"tools.grammar_catalog.operations.source_snapshot",
        "proof_catalog_path":snapshot["proof_catalog"],
        "framework_sha256":sha256((ROOT/"evidence/cognitive_curriculum_v1/learning_framework.json").read_bytes()).hexdigest(),
        "native_execution_performed":bool(native.calls),"native_binary_sha256":native.binary_sha256,
        "native_calls":native.calls,"authority":"SCOPED_EXISTING_OWNER_EXECUTION",
        "general_grammar_license":False,"meaning_stage_unlocked":False}
    wire(report)
    return report


def verify(report, *, expected_request):
    wire(report)
    return {"valid":wire(report)==wire(execute(expected_request)),
        "verification":"FRESH_INDEPENDENT_REQUEST_AND_OWNER_REPLAY","general_grammar_license":False}

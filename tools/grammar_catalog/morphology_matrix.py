"""Occurrence-local projection of the deposited workbook and Maqayis edition."""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
import re
import subprocess
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from nabt.source_lexicon import SourceLexicon, source_registry
from tools import lexical_testimony
from tools.arabic_training.source_reading import compatible
from .masdar_frames import candidates
from .operations import ROOT, exact_terms

DIRECTORY = "evidence/morphology_concepts_v1/"
BOOK = DIRECTORY + "NABT_Morphology_Concept_Matrix_AR.xlsx"
DEFINITIONS = DIRECTORY + "interpretations.json"
RULE = DIRECTORY + "necessity_ar.txt"
CLASSIFICATION = DIRECTORY + "classification.json"
SEALED = {
    CLASSIFICATION: "718445d49c59d386730e154b570b85d4e6d74d183c9bf7742c7d87c43245ab36",
    BOOK: "43910c3d760b2f8a0612797aac361c22d21c52d0138ac0e1181f3612e9a36c14",
    DEFINITIONS: "fd363d36c975c507110415cb7b57f940217f1c9a037317c770ae9f73a571e985",
    RULE: "9c067edc8247857ea421df721acdb180691bdd65cb115d15a30298f49e150256",
}
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def sealed(path):
    raw = (ROOT / path).read_bytes()
    if sha256(raw).hexdigest() != SEALED[path]:
        raise ValueError("Morphology matrix deposit changed: " + path)
    return raw


@lru_cache(maxsize=1)
def workbook(raw):
    """Read the signed cell values of the exact deposit. Never evaluate formulas."""
    tables = {}
    with ZipFile(BytesIO(raw)) as z:
        strings = ["".join(i.itertext()) for i in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        rels = {r.get("Id"): r.get("Target").lstrip("/") for r in
                ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        for s in ET.fromstring(z.read("xl/workbook.xml")).find(NS+"sheets"):
            rows = []
            for row in ET.fromstring(z.read(rels[s.get(RID)])).find(NS+"sheetData"):
                if int(row.get("r")) < 5:
                    continue
                values = {}
                for cell in row.findall(NS+"c"):
                    v = cell.findtext(NS+"v")
                    if v is not None:
                        column = re.match("[A-Z]+",cell.get("r"))[0]
                        values[column] = strings[int(v)] if cell.get("t") == "s" else v
                rows.append(values)
            tables[s.get("name")] = rows
    return tables


def sheet_manifest():
    """Seal the complete binary and each projection exposed by this adapter."""
    tables = workbook(sealed(BOOK))
    return {"workbook_sha256": SEALED[BOOK], "sheets": [
        {"sheet": name, "rows": len(rows), "row_values_sha256": sha256(json.dumps(
            rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
        for name, rows in tables.items()]}


@lru_cache(maxsize=1)
def edition(raw):
    return SourceLexicon("maqayis",raw)


def validate(option):
    if type(option) is not dict or set(option) != {"occurrence", "target"}:
        raise ValueError("Expected morphology matrix occurrence and target")
    idx, target = option["occurrence"], option["target"]
    if type(idx) is not int or not 1 <= idx <= 512:
        raise ValueError("Expected a one-based token index within 512")
    if type(target) is not list or len(target) > 32 or any(
        type(t) is not str or not t.strip() or len(t.encode()) > 512 for t in target
    ):
        raise ValueError("Expected bounded nonempty target components")


def _assessment(row, category, definition, blocks, source, rules, rule_bytes, target):
    if definition is None:
        return {"status":"NEEDS_SENSE_ALIGNMENT"}
    start, stop = definition["start"], definition["stop"]
    if (definition["id"] != row["A"] or definition["root"] != row["D"] or not any(
            b["heading_end_byte"] <= start < stop <= b["end_byte"] and
            b["heading"] == definition["heading"] for b in blocks)
            or source[start:stop] != definition["quote"].encode()):
        raise ValueError("Maqayis interpretation is outside its attested heading")
    citation = {"work":"maqayis","revision":"matrix-v1","source_sha256":source_registry()["sources"]["maqayis"]["sha256"],
                "start_byte":start,"end_byte":stop,"quotation":definition["quote"]}
    sense = {"id":row["A"],"root":row["D"],"citation":citation,"components":definition["components"]}
    scoped = [r for r in rules if r["id"] == row["A"]]
    for r in scoped:
        if (r["source_sha256"] != SEALED[RULE] or not 0 <= r["start"] < r["stop"] <= len(rule_bytes) or
                rule_bytes[r["start"]:r["stop"]] != r["quote"].encode()):
            raise ValueError("Unreplayable matrix necessity witness")
    result = {"sense":sense,"mental_rules":scoped,"definition_origin":"WORKBOOK_EDITORIAL_INTERPRETATION",
              "quote_scope":"DICTIONARY_WITNESS_NOT_VERBATIM_COMPONENTS"}
    if not target:
        return {**result,"status":"DEFINITION_REPLAYED"}
    try:
        native = lexical_testimony._native(ROOT/"formal/.lake/build/bin/lexicalDenotation",
            {"op":"morphology_matrix","value":{"id":row["A"],"root":row["D"],"category":category,"target":target}})
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return {**result,"status":"NATIVE_CHECK_UNAVAILABLE","failure":type(error).__name__}
    expected = lexical_testimony._indications(sense,target,[
        {"sense_id":r["id"],"kind":"mental","target":r["target"],"citation":{"quotation":r["quote"]}}
        for r in scoped])
    if (native.get("category") != category or native.get("sense") != sense or native.get("target") != target or
            native.get("authority") != "CONDITIONAL_MATRIX_DEFINITION" or native.get("indications") != expected):
        return {**result,"status":"NATIVE_CHECK_DISAGREES"}
    return {**result,"status":"NATIVE_CHECKED","indications":native["indications"]}


def _written_span(text, surface):
    if text.count(surface) != 1:
        raise ValueError("Ambiguous frame witness span")
    offset = len(text[:text.index(surface)].encode())
    return [offset, offset + len(surface.encode())]


def _source_frames(text, idx, tabs, anchors):
    frames = []
    for witness in tabs["شواهد الربط"]:
        if witness["E"] != text:
            continue
        anchor = anchors[witness["A"]]
        if anchor["occurrence"] != idx:
            continue
        frames.append({
            "witness": witness["A"], "reading_id": witness["B"], "link": anchor["link"],
            "governor": witness["C"], "head": witness["D"], "head_utf8_span": _written_span(text, witness["D"]),
            "dependent": witness["G"], "dependent_utf8_span": _written_span(text, witness["G"]),
            "relation": witness["H"], "function": witness["I"], "syntax": witness["J"],
            "case": witness["K"], "sign": witness["M"], "basis": "EXACT_DEPOSITED_SENTENCE_AND_OCCURRENCE",
        })
    return frames


def analyze(text, source_id, option):
    validate(option)
    idx, target = option["occurrence"], option["target"]
    words = exact_terms(text)
    if idx > len(words):
        raise ValueError("Morphology matrix token is outside the source")
    token = words[idx-1]
    tabs = workbook(sealed(BOOK))
    categories = {reading:group["category"] for group in json.loads(sealed(CLASSIFICATION))
                  for reading in group["readings"]}
    ledger = json.loads(sealed(DEFINITIONS))
    rule_bytes = sealed(RULE)
    spec = source_registry()["sources"]["maqayis"]
    lex = edition((ROOT/spec["checkout_default"]).read_bytes())
    if ledger["source_sha256"] != spec["sha256"]:
        raise ValueError("Maqayis edition changed")
    definitions = {r["id"]:r for r in ledger["readings"]}
    lineage_examples = ledger["lineage_examples"]
    forms = {r["canonical"] for r in candidates(token["surface"])}
    frames = _source_frames(text, idx, tabs, ledger["frame_anchors"])
    witnessed_forms = {f["reading_id"] for f in frames if f["link"] == "inflected_lexeme"}
    output = []
    for row in tabs["مصفوفة المفاهيم"]:
        if (row["A"] not in witnessed_forms and row["B"] not in forms
                and not compatible(token["surface"],row["B"])):
            continue
        ident = row["A"]
        definition = definitions.get(ident)
        heading = definition["heading"] if definition else row["D"]
        lookup = lex.lookup_exact(heading)
        blocks = lookup["alternatives"]
        slots = [{"role":s["D"],"genus":s["E"],"required_property":s["F"],
                  "description":s["G"],"direction":s["H"],"provenance":s["I"]}
                 for s in tabs["شروط الأدوار"] if s["A"] == ident]
        examples = [{"witness":s["A"],"governor":s["C"],"head":s["D"],"source":s["E"],
                     "relation":s["H"],"function":s["I"],"syntax":s["J"],"case":s["K"]}
                    for s in tabs["شواهد الربط"] if s["B"] == ident]
        output.append({"reading_id":ident,"form":row["B"],"pattern":row["C"],"root":row["D"],
            "category":row["E"],"concept_class":categories[ident],"concept":row["F"],
            "governor_candidate":row["N"],"slots":slots,
            "lineage_examples":[{"chain":s["A"], "origin":s["B"], "branch":s["C"],
                "relation":s["D"], "witness_required":s["E"], "property":s["F"],
                "inheritance":s["G"], "scope":s["H"]}
                for s in tabs["السلاسل"] if ident in lineage_examples.get(s["A"],[])],
            "role_axes":{axis:row[c] for c,axis in zip("GHIJ",("agent","patient","cause","effect")) if row[c]!="·"},
            "other_role":row["K"],"application_condition":row["L"],"frame_examples":examples,
            "heading":heading,"heading_status":lookup["status"],"source_blocks":[
                {k:v for k,v in b.items() if k!="raw_block"} for b in blocks],
            "denotation":_assessment(row,categories[ident],definition,blocks,lex.raw,ledger["necessities"],rule_bytes,target)})
    all_checked = bool(output) and all(r["denotation"]["status"]=="NATIVE_CHECKED" for r in output)
    return {"schema":"nabt.maqayis-morphology-matrix.v1","source_id":source_id,
            "source_sha256":sha256(text.encode()).hexdigest(),"occurrence":idx,"token":token,
            "target":target,"deposit_sha256":SEALED[BOOK],"maqayis_sha256":spec["sha256"],
            "governed_frames":frames,"readings":deepcopy(output),"common_indications":[k for k in ("mutabaqa","tadammun","iltizam")
                if all_checked and all(k in r["denotation"]["indications"] for r in output)],
            "scope":"SEALED_MATRIX_READINGS_ONLY","speaker_intent_established":False,
            "individual_eligibility_established":False,"world_truth_established":False}

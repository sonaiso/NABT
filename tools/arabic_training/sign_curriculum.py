"""A sign curriculum over installed NABT owners, never a second Arabic reader.

The matrix is teaching/navigation metadata. Evaluation measures agreement on
an exposed symbolic development suite; it cannot authorize linguistic roles,
certify acquisition, or unlock the meaning curriculum. No model is trained.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import re
import subprocess
import sys

from nabt.alphabet import ALPHABET_ID, CARRIERS, HARAKAT, STATE_NAMES, cell_id, cell_parts, parse_word, render_word
from nabt.codec import OccurrenceIdentity, encode_cells, pack_cells
from nabt.errors import NabtError, resource_limit
from nabt.learning.source_evidence import SourceSpan, SourceStore
from nabt.machine import Machine, STATE_COUNT
from nabt.phonological_modes import realize, replay_policy

from .sign_annotations import (CARRIER_NAMES, MARK_NAMES, SOURCE_PINS, SOURCE_WINDOWS,
                               PLACES, MANNERS, WHISPERED, COVERED, STAGES,
                               ROLE_CONTRASTS, PROBE_TEXTS)

ROOT = Path(__file__).resolve().parents[2]
VERSION = "nabt.sign-curriculum.v1"
MAX_INPUT_BYTES = 4 * 1024 * 1024
AUTHORITY = "TEACHING_AND_DEVELOPMENT_MEASUREMENT_ONLY"


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return sha256(wire(value)).hexdigest()


def _fields(value, names, where):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError(where + ": exact fields required")


def source_windows():
    store = SourceStore.from_resources("nabt", "data/source_evidence", SOURCE_PINS)
    result = []
    for key, book, first, last in SOURCE_WINDOWS:
        source = store.sources[book]
        lines = source.raw_bytes.splitlines(keepends=True)
        if not 1 <= first <= last <= len(lines):
            raise ValueError("source line window outside pinned text")
        start = sum(map(len, lines[:first - 1])); end = sum(map(len, lines[:last]))
        span = SourceSpan(book, source.sha256, start, end, sha256(source.raw_bytes[start:end]).hexdigest())
        span.extract(source)
        result.append({"key": key, "span": asdict(span), "lines_inclusive": [first, last],
                       "interpretation": "AUTHORED_SOURCE_LINKED_NOT_ACQUIRED"})
    return result


def declared_roles():
    """Navigate the existing declaration source, preserving its prerequisites.

    This intentionally reports source extraction, not a new compiled export.
    native-check compares this projection with the real existing JSONL binary.
    """
    path = ROOT / "formal/Nabt/AffixFunctions.lean"
    raw = path.read_bytes(); text = raw.decode("utf-8")
    pattern = re.compile(r'entry \.(\w+) "([^"\n]+)" "([^"\n]+)" \.(\w+)\s*'
                         r'\[([^\]]*)\]\s*\[([^\]]*)\]\s*\[([^\]]*)\]', re.S)
    positions = {"beforeStem": "before_stem", "afterStem": "after_stem",
                 "templateSlot": "template_slot", "wholeLexeme": "whole_lexeme",
                 "realization": "realization"}
    rows = []
    for match in pattern.finditer(text):
        _, key, label, layer, places, examples, requirements = match.groups()
        rows.append({"key": key, "label": label, "layer": layer,
                     "positions": [positions[p] for p in re.findall(r'\.(\w+)', places)],
                     "examples": re.findall(r'"([^"\n]*)"', examples),
                     "requirements": ["independent_interpreted_source", *re.findall(r'"([^"\n]*)"', requirements)]})
    if not rows or len(rows) != len(re.findall(r'\bentry \.', text)) or len({r['key'] for r in rows}) != len(rows):
        raise ValueError("AffixFunctions source projection needs review")
    return {"inventory_id": "nabt.declared-unit-functions.v1", "declared": True, "classifier": False,
            "declarations": rows, "source_path": path.relative_to(ROOT).as_posix(),
            "source_sha256": sha256(raw).hexdigest(), "compiled_this_run": False,
            "ordinal_domain": "source-ordered-role-index-qualified-by-source-sha256"}


def _articulation(carrier):
    place = next(p for p in PLACES if carrier in p[1])
    manner = next(name for name, letters in MANNERS if carrier in letters)
    return {"profile": "sibawayhi_description_not_modern_IPA", "place_index": place[0],
            "place_name": place[2], "voice_term": "مهموس" if carrier in WHISPERED else "مجهور",
            "manner_term": manner, "closure_term": "مطبق" if carrier in COVERED else "منفتح",
            "source_window": "sound_inventory", "annotation_status": "AUTHORED",
            "source_collation": "PENDING_LAM_NUN_LACUNA" if carrier in "لن" else "ANCHORED",
            "acoustic_validation": False}


def _cell_answer(text, position):
    cells = parse_word(text)
    if len(cells) != 1:
        raise ValueError("identity lesson requires one exact cell")
    cell = cells[0]; carrier, mark = cell_parts(cell)
    occurrence = OccurrenceIdentity("sign_curriculum", VERSION, position, cell)
    return {"cell": cell, "carrier": carrier, "carrier_name": CARRIER_NAMES[cell // 4],
            "state": STATE_NAMES[mark], "state_name": MARK_NAMES[mark],
            "state_kind": "sukun" if mark == 3 else "short_vowel",
            "local_number": occurrence.local_number}


def _cvv_rows():
    result = []
    for carrier in CARRIERS:
        if carrier == "ا":
            continue
        for mark, glide in enumerate(("ا", "و", "ي")):
            cells = (cell_id(carrier, mark), cell_id(glide, 3))
            result.append({"cells": list(cells), "a116_rendering": render_word(cells),
                           "content_number": encode_cells(cells), "quantity": ("a:", "u:", "i:")[mark],
                           "shape": "CVV", "lexical_role": "UNASSIGNED_WITHOUT_HOST"})
    return result


def matrix():
    sources = source_windows(); phonology = replay_policy(); roles = declared_roles()
    machines = {m: Machine(m) for m in ("wasl", "waqf")}
    cells = []
    for cell in range(116):
        carrier, mark = cell_parts(cell)
        text = render_word([cell])
        effect = machines["wasl"].effect([cell])
        cells.append({**_cell_answer(text, 0), "a116_rendering": text,
                      "cell_name": CARRIER_NAMES[cell // 4] + " / " + MARK_NAMES[mark],
                      "utf8_hex": text.encode().hex(), "framed_a116_hex": pack_cells([cell]).hex(),
                      "content_number": encode_cells([cell]),
                      "classification": "SUKUN_CELL" if mark == 3 else "MOVING_ALIF_REJECTED" if carrier == "ا" else "CV_CANDIDATE",
                      "articulation": _articulation(carrier),
                      "shape_from_zero": {m: machine.analyse([cell]).as_dict() for m, machine in machines.items()},
                      "entry_effect": {"states": STATE_COUNT, "destinations": list(effect.destinations), "weights": list(effect.weights)},
                      "role": "UNASSIGNED_WITHOUT_HOST", "independent_word_license": "NOT_ESTABLISHED"})
    long_rows = _cvv_rows()
    return {"schema": VERSION, "authority": AUTHORITY, "alphabet_id": ALPHABET_ID,
            "law_table_sha256": machines["wasl"].table_sha256,
            "count_domains": {"carriers": 29, "marks": 4, "short_vowels": 3,
                             "cells": len(cells), "cv_candidates": 84, "sukun_cells": 29,
                             "moving_alif_cells": 3, "cvv_templates": len(long_rows)},
            "cells": cells, "cvv_templates": long_rows, "declared_roles": roles,
            "role_addresses": [{"n":i, "key":r['key'], "label":r['label'],
                                "domain":roles['ordinal_domain'], "source_sha256":roles['source_sha256']}
                               for i,r in enumerate(roles['declarations'])],
            "source_windows": sources, "phonological_policy": {
                "law_id": phonology['law_id'], "examples": len(phonology['examples']),
                "passages": len(phonology['passages']), "acoustic_validation": False},
            "stages": [{"id": a, "name": b, "owners": c, "exit_obligation": d} for a,b,c,d in STAGES],
            "role_contrasts": [{"text": t, "distinction": d, "status": "TEACHING_TARGET_NOT_RUNTIME_LICENSE"} for t,d in ROLE_CONTRASTS],
            "syllable_targets": ["CV", "CVV", "CVC", "CVVC", "CVCC", "CVVCC"],
            "quota_requests": [{"c": c, "v": v, "unfiltered_order_count": comb(c+v,c),
                                "owner": "ProsodicUnits.quotaWords", "native_enumeration_this_run": False}
                               for c in range(1,5) for v in range(1,7)],
            "limitations": ["Encoding and shape acceptance do not assign a role.",
                            "Machine mode selects a final-state predicate, not a phonetic pause conversion.",
                            "Role and source descriptions are authored, not learned from free book prose.",
                            "Lam/nun source collation and acoustic validation remain open."],
            "meaning_stage_unlocked": False, "arabic_complete": False, "model_training_performed": False}


def _lesson(stage, task, inputs, answer):
    public = {"stage": stage, "task": task, "input": inputs}
    return {"id": digest(public), **public, "answer": answer}


def lessons():
    source_windows(); policy = replay_policy()
    rows = []
    for cell in range(116):
        text = render_word([cell]); position = (cell * 7) % 11
        rows.append(_lesson("D1", "identify_cell", {"text": text, "position": position}, _cell_answer(text, position)))
    for row in _cvv_rows():
        rows.append(_lesson("D3", "identify_long_quantity", {"a116_text": row['a116_rendering']},
                            {k: row[k] for k in ("cells", "content_number", "quantity", "shape")}))
    for example in policy['examples']:
        for start in ('ibtida', 'wasl'):
            for end in ('wasl', 'waqf'):
                for profile in ('standard_core', 'sibawayhi_attested_options'):
                    result = realize(example['example_id'], start=start, end=end, profile=profile)
                    rows.append(_lesson("D4", "symbolic_boundary_projection",
                                {"text": example['written_form'], "start": start, "end": end, "profile": profile},
                                {"segments_alternatives": [v['segments'] for v in result['alternatives']],
                                 "written_form": result['written_form'], "deleted_radicals": result['deleted_radicals']}))
    for text in ("كتب", "كَتَب", "أَ", "بَّ", "بً", "بَِ", "َب", "بَ بَ"):
        try:
            parse_word(text)
        except NabtError as error:
            rows.append(_lesson("D0", "exact_A116_input_boundary", {"text": text}, {"status": error.status, "code": error.code}))
        else:
            raise ValueError("negative control changed; review curriculum version")
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError("duplicate curriculum task identity")
    return rows


def suite():
    rows = lessons()
    # Both implementation and authored annotations bind the evaluator. A score
    # from another runtime/source snapshot is not silently reused.
    inputs = {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in (
        "tools/arabic_training/sign_curriculum.py", "tools/arabic_training/sign_annotations.py",
        "src/nabt/alphabet.py", "src/nabt/codec.py", "src/nabt/machine.py",
        "src/nabt/phonological_modes.py", "src/nabt/data/law.json",
        "src/nabt/data/source_evidence/phonological_modes_v1.json")}
    identity = digest({"version": VERSION, "inputs": inputs, "source_pins": SOURCE_PINS, "lessons": rows})
    return rows, identity, inputs


def questions():
    rows, identity, inputs = suite()
    return {"schema": VERSION + ".questions", "suite_sha256": identity,
            "evaluation_kind": "EXPOSED_SYMBOLIC_DEVELOPMENT", "authority": AUTHORITY,
            "inputs": inputs, "tasks": [{k:v for k,v in r.items() if k != 'answer'} for r in rows],
            "prediction_schema": {"schema": VERSION + ".predictions", "suite_sha256": identity,
                                  "predictor": "your-run-identity", "answers": [{"id": "task-id", "value": {}}]},
            "meaning_stage_unlocked": False}


def evaluate(predictions):
    # This also bounds direct Python callers; JSON text size is not the only API.
    if len(wire(predictions)) > MAX_INPUT_BYTES:
        raise resource_limit("prediction byte budget exceeded")
    _fields(predictions, ('schema', 'suite_sha256', 'predictor', 'answers'), 'predictions')
    if predictions['schema'] != VERSION + '.predictions':
        raise ValueError("unsupported prediction schema")
    if type(predictions['predictor']) is not str or not predictions['predictor'].strip() or len(predictions['predictor'].encode()) > 256:
        raise ValueError("bounded predictor name required")
    rows, identity, inputs = suite()
    if predictions['suite_sha256'] != identity:
        raise ValueError("prediction suite differs from freshly replayed source and runtime")
    answers = predictions['answers']; gold = {r['id']: r for r in rows}
    if type(answers) is not list or len(answers) > len(rows):
        raise ValueError("bounded answer list required")
    supplied = {}
    for row in answers:
        _fields(row, ('id','value'), 'answer')
        key = row['id']
        if type(key) is not str or key not in gold or key in supplied:
            raise ValueError("unknown or duplicate task identity")
        if type(row['value']) is not dict or len(wire(row['value'])) > 8192:
            raise ValueError("bounded answer object required")
        supplied[key] = row['value']
    by_stage = {}; errors = []
    for row in rows:
        counts = by_stage.setdefault(row['stage'], {'total':0,'answered':0,'correct':0,'missing':0})
        counts['total'] += 1
        if row['id'] not in supplied:
            counts['missing'] += 1; errors.append({'id':row['id'], 'reason':'MISSING'})
        else:
            counts['answered'] += 1
            # Typed canonical JSON distinguishes false from 0, 1.0 from 1,
            # missing fields from null and ordered alternative sets.
            if wire(supplied[row['id']]) == wire(row['answer']):
                counts['correct'] += 1
            else:
                errors.append({'id':row['id'], 'reason':'MISMATCH'})
    for counts in by_stage.values():
        counts['accuracy_over_all_tasks'] = counts['correct'] / counts['total']
        counts['coverage'] = counts['answered'] / counts['total']
    return {'schema':VERSION+'.evaluation', 'authority':AUTHORITY, 'suite_sha256':identity,
            'predictor':predictions['predictor'], 'predictor_identity_authenticated':False,
            'evaluation_kind':'EXPOSED_SYMBOLIC_DEVELOPMENT', 'inputs':inputs,
            'total':len(rows), 'correct':sum(v['correct'] for v in by_stage.values()),
            'by_stage':by_stage, 'errors':errors, 'symbolic_suite_pass':not errors,
            'model_training_performed':False, 'learning_established':False,
            'meaning_stage_unlocked':False, 'arabic_complete':False,
            'unmeasured':['acoustic_recognition','unseen_role_acquisition','independent_heldout',
                          'certified_grammar_bridge','withdrawal_of_alternative_role_evidence']}


def self_check():
    rows, identity, _ = suite()
    response = {'schema':VERSION+'.predictions', 'suite_sha256':identity,
                'predictor':'installed-reference-not-a-trained-model',
                'answers':[{'id':r['id'],'value':r['answer']} for r in rows]}
    result = evaluate(response)
    result['evaluation_kind'] = 'HARNESS_SELF_CHECK_NOT_LEARNER_RESULT'
    return result


def probes():
    from nabt.derivation import read_derivation, verify_derivation
    from nabt.word_reader import read_words, verify_word_reading
    rows = []
    for text in PROBE_TEXTS:
        word = read_words(text, source_id='sign_probe', scope=VERSION)
        derivation = read_derivation(text, source_id='sign_probe', scope=VERSION)
        rows.append({'text':text, 'word_owner_report':word, 'derivation_owner_report':derivation,
                     'word_replay':verify_word_reading(word, source=text, source_id='sign_probe', scope=VERSION),
                     'derivation_replay':verify_derivation(derivation, text=text, source_id='sign_probe', scope=VERSION)})
    return {'schema':VERSION+'.probes', 'authority':AUTHORITY, 'count':len(rows),
            'scope':'Existing finite word and derivation readers only, not all NABT consumers',
            'probes':rows, 'meaning_stage_unlocked':False}


def native_check():
    from tools.entropy_framework.reuse_run import entry_command
    command = entry_command('unit-discovery', [], root=ROOT)
    result = subprocess.run(command, input='{"op":"inventory"}\n', text=True,
                            capture_output=True, timeout=60, check=True, cwd=ROOT)
    exported = json.loads(result.stdout)
    expected = declared_roles()
    if type(exported) is not dict or any(wire(exported.get(k)) != wire(expected[k])
                                        for k in ('inventory_id','declared','classifier','declarations')):
        raise ValueError("native inventory differs from exact source projection")
    return {'schema':VERSION+'.native-check', 'declarations':len(expected['declarations']),
            'native_execution_performed':True, 'matched':True, 'scope':'DECLARED_ROLE_INVENTORY_ONLY'}


def _read_predictions(path):
    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value
    def nonfinite(_):
        raise ValueError("nonfinite JSON number")
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise resource_limit("prediction byte budget exceeded")
    return json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs, parse_constant=nonfinite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('matrix','questions','evaluate','self-check','probes','native-check'))
    parser.add_argument('--predictions', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if (args.operation == 'evaluate') != (args.predictions is not None):
            raise ValueError("only evaluate requires --predictions")
        operations = {'matrix':matrix, 'questions':questions, 'self-check':self_check,
                      'probes':probes, 'native-check':native_check}
        value = evaluate(_read_predictions(args.predictions)) if args.operation == 'evaluate' else operations[args.operation]()
        data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(data)
        else:
            print(data, end='')
        return 1 if value.get('symbolic_suite_pass') is False else 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, RecursionError,
            NabtError, subprocess.SubprocessError) as error:
        print(json.dumps({'status':getattr(error,'status','INVALID_OR_UNAVAILABLE'),
                          'reason':str(error), 'authority':'NONE', 'meaning_stage_unlocked':False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

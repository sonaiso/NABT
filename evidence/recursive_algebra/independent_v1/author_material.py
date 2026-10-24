from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/workspace/scratch/93a907621097/NABT')
OUT = ROOT / 'evidence/recursive_algebra/independent_v1'
OUT.mkdir(parents=True, exist_ok=False)

def source(text, identity=1, revision=1):
    return {'source_id': identity, 'revision': revision, 'scope_id': 1,
            'atomization_id': 'unicode_scalars_with_exact_utf8.v1', 'text': text}

def alignment(text, roles):
    # Independent Unicode oracle, not an import of any NABT function.
    assert len(text) == len(roles)
    out, cursor = [], 0
    for position, (char, role) in enumerate(zip(text, roles)):
        end = cursor + len(char.encode('utf-8'))
        out.append({'position': position, 'text': char, 'byte_span': [cursor, end], **role})
        cursor = end
    return out

def root(index): return {'origin': 'radical', 'root_index': index}
def literal(): return {'origin': 'literal'}
def boundary(): return {'origin': 'boundary'}

mafool_text = 'مَكْتُوبٌ'
mafool = {
    'source': source(mafool_text), 'reading_id': 'reading.mafool.1',
    'catalog_id': 'nabt.derivation-catalog.v1', 'template_id': 'nominal.mafool',
    'root': ['ك', 'ت', 'ب'], 'seed_kind': 'root3', 'host_byte_span': [0, 16],
    'alignment': alignment(mafool_text, [literal(), literal(), root(0), literal(), root(1),
                                       literal(), literal(), root(2), boundary()]),
    'category_claim': None, 'role_claims': [], 'witnesses': [],
}
katib_text = 'كَاتِبٌ'
katib = {
    'source': source(katib_text, 2), 'reading_id': 'reading.katib.1',
    'catalog_id': 'nabt.derivation-catalog.v1', 'template_id': 'nominal.faail',
    'root': ['ك', 'ت', 'ب'], 'seed_kind': 'root3', 'host_byte_span': [0, 10],
    'alignment': alignment(katib_text, [root(0), literal(), literal(), root(1), literal(), root(2), boundary()]),
    'category_claim': None, 'role_claims': [], 'witnesses': [],
}
# This fixture is intentionally symbolic, not an Arabic sound/word claim.
repeat_text = 'A·B·B·C'
repeat = {
    'source': source(repeat_text, 3), 'reading_id': 'reading.repeated.1',
    'catalog_id': 'independent.authored.v1', 'template_id': 'repeat-middle-slot',
    'root': ['A', 'B', 'C'], 'seed_kind': 'root3', 'host_byte_span': [0, 10],
    'alignment': alignment(repeat_text, [root(0), literal(), root(1), literal(), root(1), literal(), root(2)]),
    'category_claim': None, 'role_claims': [], 'witnesses': [],
}
quad_text = 'دَحْرَجَ'
quad = {
    'source': source(quad_text, 4), 'reading_id': 'reading.quad.1',
    'catalog_id': 'independent.authored.v1', 'template_id': 'quad-past-shape',
    'root': ['د', 'ح', 'ر', 'ج'], 'seed_kind': 'root4', 'host_byte_span': [0, 16],
    'alignment': alignment(quad_text, [root(0), literal(), root(1), literal(), root(2), literal(), root(3), literal()]),
    'category_claim': None, 'role_claims': [], 'witnesses': [],
}
lexical = {'source': source('فِي', 5), 'reading_id': 'reading.lexical.1',
           'catalog_id': 'independent.lexical.v1', 'lexical_entry_id': 'entry.fi',
           'seed_kind': 'lexical', 'host_byte_span': [0, 6], 'root': None,
           'template_id': None, 'category_claim': None, 'role_claims': [], 'witnesses': []}

tree = {'kind': 'unary', 'rule_id': 10,
        'child': {'kind': 'leaf', 'seed': {'kind': 'root3', 'values': [0, 1, 2]}}}
target = {'registry_id': 'independent.registry', 'registry_version': 1,
          'tree': tree, 'reading': mafool, 'face': {'category': 'noun', 'state': 0,
          'position': 0, 'residual': []}, 'internal_roles': [], 'external_roles': []}
support_source = source('declared source-bound fixture premise', 90)
support = {'source': support_source, 'byte_span': [0, len(support_source['text'].encode())]}
parent_receipt = {'witness_id': 'w.parent', 'target': target, 'requirement': 'application',
                  'positive': True, 'supports': [support]}
child_target = {'registry_id': 'independent.registry', 'registry_version': 1,
                'tree': tree['child'], 'reading': mafool}
child_receipt = {'witness_id': 'w.child', 'target': child_target,
                 'requirement': 'seed-allowance', 'positive': True, 'supports': [support]}
ledger = {'target': target, 'inventory': [mafool['source'], support_source],
          'interpreted': [child_receipt, parent_receipt],
          'offered': [child_receipt, parent_receipt],
          'typing': {'child_face': 'root3', 'rule_input': 'root3', 'rule_output': 'noun'}}
fixtures = {'mafool': mafool, 'katib': katib, 'repeated': repeat, 'quad': quad,
            'lexical': lexical, 'licensed_ledger': ledger,
            'seed_a': {'kind': 'leaf', 'seed': {'kind': 'lexical', 'entry': 0}},
            'seed_b': {'kind': 'leaf', 'seed': {'kind': 'lexical', 'entry': 1}}}
cases = []

def add(case_id, group, op, data, expected, contract):
    cases.append({'case_id': case_id, 'group': group, 'operation': op,
                  'input': data, 'expected': expected, 'contract': contract})

add('A01', 'alignment', 'align_reading', {'fixture': 'mafool'},
    {'alignment_valid': True, 'root_byte_spans': [[4,6],[8,10],[14,16]],
     'root_is_contiguous': False, 'source_reconstructed_exactly': True,
     'root_lexically_attested': False},
    'All literal, radical and boundary positions survive; recovering root slots is not lexical attestation.')
add('A02', 'alignment', 'join_source_spans',
    {'source': mafool['source'], 'spans': [[4,6],[8,10],[14,16]]},
    {'original_adjacency': False, 'join_licensed': False, 'gap_erased': False},
    'A radical projection cannot be passed off as an adjacent substring join.')
add('A03', 'alignment', 'align_reading', {'fixture': 'repeated'},
    {'alignment_valid': True, 'root_arity': 3, 'radical_occurrence_count': 4,
     'root_index_1_byte_spans': [[3,4],[6,7]]},
    'Repeated use of one root slot retains both surface occurrences.')
add('A04', 'alignment', 'align_reading', {'fixture': 'quad'},
    {'alignment_valid': True, 'root_arity': 4, 'root_byte_spans': [[0,2],[4,6],[8,10],[12,14]]},
    'Quadriliteral roots use an independent four-slot seed.')
add('A05', 'alignment', 'align_reading', {'fixture': 'lexical'},
    {'seed_kind': 'lexical', 'root_invented': False, 'source_reconstructed_exactly': True},
    'A lexical inlet does not acquire an artificial triliteral root.')
add('A06', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'mutations': [{'path': ['alignment',2,'byte_span'], 'value': [2,3]}]},
    {'alignment_valid': False, 'licensed': False},
    'Character indices and byte coordinates are distinct; a partial UTF8 character is invalid.')
add('A07', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'mutations': [{'path': ['alignment'], 'remove_index': 6}]},
    {'alignment_valid': False, 'unaccounted_positions': True},
    'The interleaved literal waw cannot disappear from a complete source alignment.')
add('A08', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'mutations': [{'path': ['alignment',4,'root_index'], 'value': 0}]},
    {'alignment_valid': False, 'licensed': False},
    'A source letter ta cannot be relabeled as root slot kaf.')
add('A09', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'mutations': [{'path': ['alignment',7,'byte_span'], 'value': [8,10]}]},
    {'alignment_valid': False, 'overlap_or_alias_detected': True},
    'Distinct source positions cannot borrow one interval to fabricate total coverage.')
add('A10', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'registered_source': mafool['source'],
     'mutations': [{'path': ['source','text'], 'value': 'مَكْتُوفٌ'}]},
    {'source_binding_valid': False, 'licensed': False},
    'Matching source IDs without matching source content does not preserve provenance.')
add('A11', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'registered_source': mafool['source'],
     'mutations': [{'path': ['source','revision'], 'value': 2}]},
    {'source_binding_valid': False, 'licensed': False},
    'A witness for one source revision cannot authorize another.')
add('A12', 'alignment', 'compare_readings',
    {'left_fixture': 'katib', 'right_fixture': 'katib',
     'right_mutations': [{'path': ['reading_id'], 'value': 'reading.katib.2'},
                         {'path': ['template_id'], 'value': 'grammar.sifa.faa3il'}]},
    {'same_surface': True, 'same_root': True, 'same_alignment': True,
     'same_reading_identity': False, 'retained_alternatives': 2, 'unique_analysis': False},
    'Coincident template token sequences do not erase distinct catalog/template readings.')
add('A13', 'alignment', 'compare_sources',
    {'left': source('مُعَلِّمٌ', 6), 'right': source('مُعَلِّمٌ', 6)},
    {'same_original_bytes': False, 'source_identity_equal': False,
     'normalization_grants_identity': False},
    'Canonical-looking combining-mark reorderings need an explicit correspondence, not silent identity.')
add('A14', 'alignment', 'align_reading',
    {'fixture': 'mafool', 'mutations': [{'path': ['alignment',8,'origin'], 'value': 'radical'},
                                      {'path': ['alignment',8,'root_index'], 'value': 2}]},
    {'alignment_valid': False, 'root_arity_inflated': False},
    'Tanwin at the boundary cannot become another root occurrence.')

add('W01', 'evidence', 'assess_recursive', {'fixture': 'licensed_ledger'},
    {'verdict': 'LICENSED', 'child_premises_retained': True, 'linguistic_acquisition_measured': False},
    'Positive fixture interpretations license only the exact supplied targets and interfaces.')
add('W02', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'mutations': [{'path': ['interpreted'], 'value': []}]},
    {'verdict': 'UNKNOWN', 'licensed': False},
    'Offered receipts alone do not authorize their own interpretations.')
add('W03', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'append_negative_to': 'interpreted',
     'negative_target': 'parent', 'omit_negative_from_offered': True},
    {'verdict': 'REJECTED', 'conflict': True, 'licensed': False},
    'A valid known negative cannot be hidden by omitting it from offered evidence.')
add('W04', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'remove_witness': 'w.child', 'from': ['interpreted','offered']},
    {'verdict': 'UNKNOWN', 'licensed': False},
    'A parent witness cannot discharge an unsupported child.')
add('W05', 'evidence', 'withdraw_and_reassess',
    {'fixture': 'licensed_ledger', 'withdraw': 'w.child', 'leave_offered_unchanged': True},
    {'before': 'LICENSED', 'after': 'UNKNOWN', 'stale_parent_license_reused': False},
    'Receipt withdrawal invalidates dependent certification at consumption.')
add('W06', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'target_mutations': [{'path': ['reading','reading_id'], 'value': 'reading.other'}]},
    {'licensed': False, 'foreign_reading_receipt_reused': False},
    'Equal surfaces and root slots do not permit witness reuse across reading identities.')
add('W07', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'support_mutations': [{'path': ['byte_span'], 'value': [0,9999]}]},
    {'licensed': False, 'support_valid': False},
    'A nonempty support interval beyond its actual source is invalid.')
add('W08', 'evidence', 'assess_recursive',
    {'fixture': 'licensed_ledger', 'typing_mutations': [{'path': ['rule_input'], 'value': 'root4'}]},
    {'licensed': False, 'interface_valid': False},
    'Present evidence cannot repair a mismatched typed rule interface.')

add('I01', 'identity', 'compare_tree_identity',
    {'left': tree, 'right': deepcopy(tree), 'registry_left': ['independent.registry',1],
     'registry_right': ['independent.registry',1]},
    {'same_structural_number': True, 'same_structural_tree': True},
    'Repeated identical construction has one structural number in a fixed registry.')
add('I02', 'identity', 'compare_tree_identity',
    {'left': tree, 'right': {**tree, 'rule_id': 11},
     'registry_left': ['independent.registry',1], 'registry_right': ['independent.registry',1]},
    {'same_structural_number': False},
    'Rule identity is included even if realizations happen to agree.')
add('I03', 'identity', 'compare_tree_identity',
    {'left': {'kind':'binary','rule_id':12,'left':fixtures['seed_a'],'right':fixtures['seed_b']},
     'right': {'kind':'binary','rule_id':12,'left':fixtures['seed_b'],'right':fixtures['seed_a']},
     'registry_left':['independent.registry',1], 'registry_right':['independent.registry',1]},
    {'same_structural_number': False, 'ordered_children_preserved': True},
    'Swapping distinct children changes structural identity.')
add('I04', 'identity', 'compare_tree_identity',
    {'left': tree, 'right': deepcopy(tree), 'registry_left':['independent.registry',1],
     'registry_right':['independent.registry',2]},
    {'same_structural_number': True, 'same_qualified_unit_identity': False},
    'A raw tree number does not encode registry/version and cannot authorize cross-registry sameness.')
add('I05', 'identity', 'compare_occurrence_identity',
    {'tree': tree, 'left_source': source('كَاتِبٌ كَاتِبٌ',7),
     'right_source': source('كَاتِبٌ كَاتِبٌ',7), 'left_byte_span':[0,14], 'right_byte_span':[15,29]},
    {'same_structural_number': True, 'same_occurrence': False},
    'Repeated spelling/structure in two intervals remains two source occurrences.')
add('I06', 'identity', 'compare_certificates',
    {'fixture': 'licensed_ledger', 'right_witness_id': 'w.parent.independent'},
    {'same_structural_tree': True, 'same_structural_number': True, 'same_witness_record': False},
    'Proof irrelevance of Unit.n must not erase executable evidence provenance.')

seed0 = {'kind':'lexical','entry':0}
add('E01', 'enumeration', 'enumerate_trees',
    {'seeds':[seed0], 'unary_rules':[], 'binary_rules':[], 'height':3, 'max_candidates':20},
    {'structural_count':1, 'structural_search_complete':True, 'linguistic_license_inferred':False},
    'Without rules increasing height adds no constructions.')
add('E02', 'enumeration', 'enumerate_trees',
    {'seeds':[seed0], 'unary_rules':[0], 'binary_rules':[1], 'height':2, 'max_candidates':20},
    {'structural_count':13, 'distinct_count':13, 'structural_search_complete':True},
    'At height1 the three terms are a,U(a),B(a,a); at height2 there is one leaf, three unary terms and nine ordered binary pairs.')
add('E03', 'enumeration', 'enumerate_trees',
    {'seeds':[seed0,deepcopy(seed0)], 'unary_rules':[], 'binary_rules':[], 'height':0, 'max_candidates':20},
    {'raw_kernel_count':2, 'distinct_count':1, 'two_distinct_analyses_inferred':False},
    'The supplied kernel proves membership completeness but not Nodup for duplicated inventories.')
add('E04', 'enumeration', 'enumerate_trees',
    {'seeds':[seed0], 'unary_rules':[0], 'binary_rules':[1], 'height':2,
     'max_candidates':20, 'certification_decision_procedure':'unavailable'},
    {'structural_search_complete':True, 'certified_search_complete':False,
     'all_unproved_candidates_rejected':False},
    'An unavailable certification decision procedure is not a negative gate proof.')
add('E05', 'enumeration', 'enumerate_trees',
    {'seeds':[seed0], 'unary_rules':[0], 'binary_rules':[1], 'height':2, 'max_candidates':2},
    {'resource_exhausted':True, 'search_complete':False, 'linguistic_rejection':False},
    'A truncated candidate budget never supplies an exhaustive exclusion certificate.')

add('U01', 'rewrite', 'rewrite_audit',
    {'fixture':'mafool', 'replacement':'مَكْتُبٌ', 'removed_source_byte_span':[12,14],
     'explicit_interpretation':False},
    {'source_restorable':True, 'displaced_text':'و', 'linguistically_licensed':False},
    'Recording a deletion and its residue permits restoration without proving an Arabic deletion law.')
add('U02', 'rewrite', 'rewrite_audit',
    {'fixture':'mafool', 'replacement':'مَكْتُبٌ', 'removed_source_byte_span':[12,14],
     'seen_output':'مَكْتُفٌ', 'explicit_interpretation':False},
    {'inverse_replay_accepted':False},
    'Undo requires the actual declared output, not an unrelated changed surface.')
add('U03', 'rewrite', 'rewrite_audit',
    {'fixture':'mafool', 'replacement':'', 'removed_source_byte_span':[0,18],
     'explicit_interpretation':False},
    {'source_restorable':True, 'original_source_nonempty':True, 'empty_source_occurrence_invented':False},
    'Empty output does not turn a nonempty historical source into an empty occurrence.')
add('U04', 'rewrite', 'compare_tree_identity',
    {'left':tree['child'], 'right':tree,
     'registry_left':['independent.registry',1], 'registry_right':['independent.registry',1],
     'rule_realization':'identity'},
    {'same_structural_number':False, 'same_surface_permitted':True, 'child_retained':True},
    'An output-preserving unary construction is a new structural tree with its child retained.')

add('R01', 'roles', 'align_reading', {'fixture':'mafool'},
    {'syntactic_role_assigned':False, 'case_assigned':False, 'noun_category_inferred_from_shape_alone':False},
    'A reconstructed root/template does not by itself establish section, syntactic role or case.')
add('R02', 'roles', 'lift_role_scope',
    {'inner':{'category':'verbalClause','predicate':{'category':'verb','mood':'indicative'},
              'subject':{'reading_id':'subject.1','role':'agent','case':'nominative'}},
     'outer':{'role':'complement','case':'accusative'},
     'licensed_outer_relation':True},
    {'inner_predicate_mood':'indicative', 'inner_subject_case':'nominative',
     'outer_case':'accusative', 'inner_assignments_overwritten':False},
    'The external slot of a clause does not overwrite its internal assignments.')
add('R03', 'roles', 'assess_role_binding',
    {'claim':{'role':'agent','target_reading':'subject.2','relation_id':'relation.2'},
     'witness':{'role':'agent','target_reading':'subject.1','relation_id':'relation.1'}},
    {'role_binding_licensed':False, 'foreign_relation_evidence_reused':False},
    'A role witness is bound to exact endpoint readings and relation identity.')

data = {'schema':'nabt.recursive-algebra.independent-material.v1',
        'authorship':'Independent reviewer authored inputs and expectations before opening new implementation.',
        'authored_utc':datetime.now(timezone.utc).isoformat(),
        'baseline_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_kernel_sha256':hashlib.sha256(Path('/workspace/scratch/93a907621097/recursive_import/RecursiveLicensedAlgebra.lean').read_bytes()).hexdigest(),
        'case_count':len(cases), 'fixtures':fixtures, 'cases':cases,
        'measurement_contract':[
            'Request construction may read operation/input and fixtures only; expected is used only after execution.',
            'Fixture resolution and listed mutations are deterministic input transformations, never inferred from expected.',
            'Unsupported operations or assertions remain UNMEASURED; no missing field is a successful negative.',
            'Exact source, catalog, template, registry, reading, role, child and witness identities may not be erased to fit an adapter.',
            'Positive receipts are explicitly authored fixture interpretations, not acquired Arabic evidence.',
            'No raw Tree.n equality implies registry, source occurrence or certificate identity.',
            'Raw kernel duplicates and deduplicated public candidates must be reported as separate counts.',
            'Contract fixtures are not a natural-Arabic held-out accuracy corpus.',
        ]}
assert len(cases)==40 and len({c['case_id'] for c in cases})==40
with (OUT/'material.json').open('x') as f: json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
# The authoring program is preserved so fixture generation is inspectable.
(OUT/'author_material.py').write_bytes(Path(__file__).read_bytes())
record={'schema':'nabt.recursive-algebra.independent-freeze.v1',
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'production_implementation_read':False,'case_count':40,
        'files':[{ 'path':str(p.relative_to(ROOT)), 'bytes':p.stat().st_size,
                   'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in [OUT/'material.json',OUT/'author_material.py']]}
with (OUT/'freeze.json').open('x') as f: json.dump(record,f,indent=2); f.write('\n')
print(json.dumps({'case_count':40,'material_sha256':record['files'][0]['sha256'],
                  'path':str(OUT/'material.json')}))

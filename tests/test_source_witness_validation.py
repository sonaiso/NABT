"""Adversarial checks of source witnesses without importing the production reader.

The four saved reports are post-freeze development fixtures. The expected
premises below come from independently authored raw records and the public
contract. No 24-case oracle prediction is used here. Source mutations rebuild
all raw byte/locator receipts, so semantic checks cannot pass merely by hashing.
"""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evidence/arabic_completion_v3/independent_oracle/validator_review_v1'


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_module('construction_evaluation')
D = load_module('discourse_evaluation')
V = C.source_validation


def fixture(name):
    return json.loads((FOLDER / (name + '.json')).read_text())


def audit(f):
    summary = f['report']['lexical_model']
    return C.SourceAudit(f['raw'].encode(), summary['excluded_verses'], summary['source']['id'])


def components(f):
    rows, _ = C.reading_rows(f['report'])
    return rows, f['report']['clauses'][0]['analyses'][0]


def name_parts(f):
    rows, analysis = components(f)
    ref = next(ref for ref in analysis['references'] if 'name_correspondence' in ref)
    return ref, analysis, rows


def check_name(f, module=C):
    ref, analysis, rows = name_parts(f)
    entities = {e['id']: e for e in f['inputs']['context']['entities']}
    return module.validate_reference_origin(ref, f['inputs'], entities, analysis=analysis,
        rows=rows, audit=audit(f), model_summary=f['report']['lexical_model'])


def nominal(f):
    rows, _ = components(f)
    return next(row for row in rows.values() if 'nominal_paradigm_correspondence' in row)


def check_nominal(f):
    return V.validate_nominal_correspondence(nominal(f), f['inputs'], audit(f))


def sense_parts(f):
    rows, analysis = components(f)
    relation = next(r for r in analysis['relations'] if 'independent_sense_witness' in r)
    return relation, analysis, rows


def check_sense(f):
    relation, analysis, rows = sense_parts(f)
    return V.validate_sense_witness(relation, analysis, rows, f['inputs'], audit(f))


def rebound_raw(f, changed_raw):
    """Preserve locations while rebuilding complete authenticated raw receipts."""
    f['raw'] = changed_raw
    summary = f['report']['lexical_model']
    a = C.SourceAudit(changed_raw.encode(), summary['excluded_verses'], summary['source']['id'])
    source = {'id': a.source_id, 'sha256': a.sha, 'byte_length': len(a.raw)}
    summary['source'] = source
    locations = {tuple(row['locator']): (bounds, row) for bounds, row in a.records.items()}
    def walk(value):
        if type(value) is dict:
            if {'record_id', 'byte_start', 'byte_end', 'locator'} <= set(value):
                (start, end), row = locations[tuple(value['locator'])]
                value.update(byte_start=start, byte_end=end, ordinal=row['ordinal'],
                    source_sha256=a.sha, source_id=a.source_id,
                    record_id=C.digest(['nabt.corpus-source.v1', 'qac', a.source_id, a.sha, start, end, row['ordinal']]))
            if 'lexical_source' in value:
                value['lexical_source'] = source
            for item in list(value.values()):
                walk(item)
        elif type(value) is list:
            for item in value:
                walk(item)
    walk(f['report'])
    return f


def changed_operator(f, surface):
    relation, analysis, rows = sense_parts(f)
    witness = relation['independent_sense_witness']
    f['inputs']['text'] = surface + f['inputs']['text'][len(witness['operator_surface']):]
    raw = f['inputs']['text'].encode()
    span = {**witness['operator_span'], 'source_sha256': sha256(raw).hexdigest(),
            'end': len(surface.encode()), 'span_sha256': sha256(surface.encode()).hexdigest()}
    witness['operator_span'] = relation['head_span'] = rows[witness['operator_reading_id']]['stem_span'] = span
    witness['operator_surface'] = surface
    return f


class SourceWitnessValidationTests(unittest.TestCase):
    def test_all_saved_positive_receipts_have_independent_raw_premises(self):
        for module in (C, D):
            for name in ('name_v2', 'nominal_v1', 'nominal_unmarked_v1'):
                with self.subTest(module=module.VERSION, name=name):
                    f = fixture(name)
                    module.validate_report(f['report'], f['inputs'], audit(f))
        f = fixture('sense_v1')
        C.validate_report(f['report'], f['inputs'], audit(f))
        check_sense(f)

    def test_name_receipt_is_required_in_both_evaluators(self):
        for module in (C, D):
            f = fixture('name_v2')
            ref, analysis, rows = name_parts(f)
            del ref['name_correspondence']
            with self.assertRaisesRegex(ValueError, 'Reference candidates'):
                module.validate_reference_origin(ref, f['inputs'],
                    {e['id']: e for e in f['inputs']['context']['entities']}, analysis=analysis,
                    rows=rows, audit=audit(f), model_summary=f['report']['lexical_model'])

    def test_name_cannot_drop_homonymous_context_entities(self):
        f = fixture('name_v2')
        f['inputs']['context']['entities'].append({**f['inputs']['context']['entities'][0], 'id': 'second_writer'})
        with self.assertRaisesRegex(ValueError, 'Reference candidates'):
            check_name(f)
        ref, _, _ = name_parts(f)
        ref['candidate_entity_ids'] = ['writer', 'second_writer']
        ref['bound_entity_id'] = None
        check_name(f)

    def test_name_cannot_replace_explicit_contrary_context_marks(self):
        f = fixture('name_v2')
        f['inputs']['context']['entities'][0]['name'] = 'الْمُصَنَّف'
        with self.assertRaisesRegex(ValueError, 'unvocalized'):
            check_name(f)

    def test_name_binds_the_same_analysis_reading_and_occurrence(self):
        for alteration in ('analysis', 'reading_id', 'stem', 'scope'):
            f = fixture('name_v2')
            ref, analysis, rows = name_parts(f)
            witness = ref['name_correspondence']
            if alteration == 'analysis': analysis['reading_ids'].remove(witness['reading_id'])
            if alteration == 'reading_id': witness['reading_id'] = '0' * 64
            if alteration == 'stem': witness['stem_span']['start'] += 2
            if alteration == 'scope': f['inputs']['scope'] = 'other_scope'
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                check_name(f)

    def test_name_source_model_exclusions_and_withdrawal_are_not_optional(self):
        for alteration in ('source', 'inventory', 'excluded', 'empty'):
            f = fixture('name_v2');ref, _, _ = name_parts(f);w = ref['name_correspondence']
            if alteration == 'source': w['lexical_source']['sha256'] = '0' * 64
            if alteration == 'inventory': w['inventory_sha256'] = '0' * 64
            if alteration == 'excluded': f['report']['lexical_model']['excluded_verses'] = ['1:1']
            if alteration == 'empty': w['support_records'] = []
            with self.subTest(alteration=alteration), self.assertRaises(ValueError): check_name(f)

    def test_name_same_ending_is_not_an_inflection_pair_after_rehashing_raw(self):
        f = fixture('name_v2');rebound_raw(f, f['raw'].replace('muSan~ifK', 'muSan~ifN'))
        ref, _, _ = name_parts(f);ref['name_correspondence']['source_form'] = 'مُصَنِّفٌ'
        with self.assertRaisesRegex(ValueError, 'two distinct terminal-vowel'):
            check_name(f)

    def test_name_pair_cannot_borrow_lemma_or_derivation_after_raw_rehash(self):
        for old, new in (('muSan~ifK\tN\tSTEM|POS:N|LEM:muSan~if', 'muSan~ifK\tN\tSTEM|POS:N|LEM:muSan~af'),
                         ('muSan~ifK\tN\tSTEM|POS:N', 'muSan~ifK\tN\tSTEM|ACT|PCPL|POS:N')):
            f = fixture('name_v2');rebound_raw(f, f['raw'].replace(old, new))
            with self.subTest(new=new), self.assertRaisesRegex(ValueError, 'raw profiles|raw source|lexical profile'):
                check_name(f)

    def test_name_context_does_not_supply_unobserved_shadda(self):
        f = fixture('name_v2');rebound_raw(f, f['raw'].replace('muSan~if', 'muSanif'))
        ref, _, _ = name_parts(f);w = ref['name_correspondence']
        w.update(source_form='مُصَنِفٌ', source_template='مُصَنِف')
        # The forged output also copies the new lexical lemma. The explicit
        # target shadda still has no source authority.
        row = name_parts(f)[2][w['reading_id']];row['lexical_features']['lemma'] = 'مُصَنِف'
        with self.assertRaisesRegex(ValueError, 'observed internal marks'):
            check_name(f)

    def test_name_excludes_unreviewed_number_recomposition_and_carriers(self):
        for basis in ('annotated_number_and_lemma_recomposition', 'paired_annotated_plural_letter_realizations'):
            f = fixture('name_v2');ref, _, rows = name_parts(f);w = ref['name_correspondence']
            rows[w['reading_id']]['construction_basis'] = w['construction_basis'] = basis
            with self.subTest(basis=basis), self.assertRaisesRegex(ValueError, 'paired source construction'):
                check_name(f)

    def test_nominal_recipient_own_tanwin_and_known_number_are_required(self):
        for old,new in (('nabiylK\tN\t', 'nabiyli\tN\t'), ('ROOT:nbl|MS\n','ROOT:nbl|M\n')):
            f=fixture('nominal_v1');rebound_raw(f,f['raw'].replace(old,new,1))
            with self.subTest(new=new),self.assertRaisesRegex(ValueError,'tanwin|incomplete'):
                check_nominal(f)

    def test_nominal_donor_needs_two_terminal_families_after_raw_rehash(self):
        f=fixture('nominal_v1');rebound_raw(f,f['raw'].replace('nabiylN\tADJ','nabiylK\tADJ'))
        with self.assertRaisesRegex(ValueError,'two terminal-vowel'):
            check_nominal(f)

    def test_nominal_donor_own_tanwin_cannot_be_borrowed(self):
        f=fixture('nominal_v1');w=nominal(f)['nominal_paradigm_correspondence']
        w['donors'][0]['tanwin_supports']=deepcopy(w['recipient_tanwin_supports'])
        row=nominal(f)
        row['support_records']=[deepcopy(w) if p.get('kind')=='same_form_nominal_inflection' else p
                                for p in row['support_records']]
        with self.assertRaisesRegex(ValueError,'donor changed'):
            check_nominal(f)

    def test_donor_tanwin_may_be_a_separate_occurrence_of_the_same_raw_paradigm(self):
        f=fixture('nominal_v1')
        changed=f['raw'].replace('nabiylN\tADJ','nabiylu\tADJ').replace('nabiylK\tADJ','nabiyli\tADJ')
        changed+='(1:4:1:1)\tnabiylN\tADJ\tSTEM|POS:ADJ|LEM:nabiyl|ROOT:nbl|MS\n'
        rebound_raw(f,changed)
        a=audit(f)
        (start,end),raw=next((bounds,row) for bounds,row in a.records.items() if row['locator']==[1,4,1,1])
        row=nominal(f);w=row['nominal_paradigm_correspondence']
        proof=deepcopy(w['donors'][0]['tanwin_supports'][0])
        proof.update(byte_start=start,byte_end=end,locator=raw['locator'],ordinal=raw['ordinal'],
            record_id=C.digest(['nabt.corpus-source.v1','qac',a.source_id,a.sha,start,end,raw['ordinal']]))
        w['donors'][0]['tanwin_supports']=[proof]
        row['support_records']=[deepcopy(w) if p.get('kind')=='same_form_nominal_inflection' else p
                                for p in row['support_records']]
        self.assertNotIn(proof,w['donors'][0]['paired_terminal_supports'])
        self.assertTrue(check_nominal(f))

    def test_nominal_direct_equality_covers_root_lemma_derivation_template_gender_number(self):
        replacements=[('LEM:nabiyl|ROOT:nbl|MS','LEM:nabal|ROOT:nbl|MS'),
                      ('ROOT:nbl|MS','ROOT:nql|MS'),('ROOT:nbl|MS','ROOT:nbl|FS'),
                      ('ROOT:nbl|MS','ROOT:nbl|MD'),('ROOT:nbl|MS','ROOT:nbl|MS|ACT|PCPL'),
                      ('nabiylN\tADJ','nubiylN\tADJ')]
        for old,new in replacements:
            f=fixture('nominal_v1');head,*tail=f['raw'].splitlines(keepends=True)
            # Alter donor rows only, with fully renewed raw identities.
            changed=head+''.join(line.replace(old,new) if '\tADJ\t' in line else line for line in tail)
            rebound_raw(f,changed)
            with self.subTest(new=new),self.assertRaises(ValueError): check_nominal(f)

    def test_nominal_bridge_cannot_transfer_gender_number_pos_or_semantics(self):
        for key,value in [('transferred_fields',['construction','number']),('source_pos_preserved',False),
                          ('semantic_equivalence_claimed',True),('target_role_labels_used',True)]:
            f=fixture('nominal_v1');nominal(f)['nominal_paradigm_correspondence'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'expanded its authority'): check_nominal(f)

    def test_nominal_class_and_recipient_identity_are_bound(self):
        for field,value in [('class_candidates',[5]),('variant','generated')]:
            f=fixture('nominal_v1');nominal(f)[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):check_nominal(f)
        f=fixture('nominal_v1');nominal(f)['nominal_paradigm_correspondence']['recipient_lexical_id']='0'*64
        with self.assertRaisesRegex(ValueError,'recipient identity'):check_nominal(f)

    def test_nominal_person_adapter_does_not_supply_missing_lexical_traits(self):
        f=fixture('nominal_unmarked_v1')
        rows,_=components(f)
        row=next(r for r in rows.values() if 'nominal_paradigm_correspondence' in r and r.get('person_evidence'))
        row['person_evidence']['source_person_code']='M'
        with self.assertRaisesRegex(ValueError,'independently annotated traits'):
            V.validate_nominal_correspondence(row,f['inputs'],audit(f))

    def test_selected_primary_intervals_cannot_be_changed(self):
        f=fixture('nominal_v1');nominal(f)['nominal_paradigm_correspondence']['passage']['start']+=1
        with self.assertRaisesRegex(ValueError,'selected identity'):check_nominal(f)
        f=fixture('sense_v1');sense_parts(f)[0]['independent_sense_witness']['source']['passage']['source_id']='sibawayhi'
        with self.assertRaisesRegex(ValueError,'selected identity'):check_sense(f)

    def test_hasiba_requires_all_three_explicit_active_vowels(self):
        for surface in ('حُسِبَ','حسِب','حَسَبَ','حَسُبَ','حَسِبُ','حسب'):
            with self.subTest(surface=surface),self.assertRaisesRegex(ValueError,'all three explicit'):
                check_sense(changed_operator(fixture('sense_v1'),surface))

    def test_hasiba_grammar_fallback_does_not_supply_lexical_sense(self):
        f=fixture('sense_v1');relation,_,rows=sense_parts(f)
        row=rows[relation['operator_reading_id']];row['support_records']=[{'kind':'grammar','rule':'zanna'}]
        with self.assertRaisesRegex(ValueError,'fallback alone'):check_sense(f)
        row['variant']='grammar'
        with self.assertRaisesRegex(ValueError,'fallback or another'):check_sense(f)

    def test_hasiba_raw_root_person_voice_and_vowels_are_checked_after_rehash(self):
        replacements=[('ROOT:Hsb','ROOT:Elm'),('|3MS|PERF','|2MS|PERF'),('|PERF','|PERF|PASS'),
                      ('Hasiba\tV','Husiba\tV'),('|PERF','|PERF|(II)')]
        for old,new in replacements:
            f=fixture('sense_v1');rebound_raw(f,f['raw'].replace(old,new,1))
            with self.subTest(new=new),self.assertRaisesRegex(ValueError,'raw lexical receipt'):check_sense(f)

    def test_hasiba_conflicting_or_duplicate_source_profiles_are_not_a_unique_premise(self):
        for codes in ('2MS|3MS','3MS|2MS','3MS|3MS'):
            f=fixture('sense_v1');rebound_raw(f,f['raw'].replace('|3MS|PERF','|'+codes+'|PERF',1))
            with self.subTest(codes=codes),self.assertRaisesRegex(ValueError,'raw lexical receipt'):check_sense(f)

    def test_hasiba_cannot_borrow_reading_or_project_embedded_fact(self):
        f=fixture('sense_v1');rel,a,rows=sense_parts(f)
        a['reading_ids'].remove(rel['operator_reading_id'])
        with self.assertRaisesRegex(ValueError,'another analysis'):check_sense(f)
        f=fixture('sense_v1');rel,a,rows=sense_parts(f)
        a['claims'].append({'predicate_kind':'property'})
        with self.assertRaisesRegex(ValueError,'separate assertion'):check_sense(f)

    def test_licensed_hasiba_cannot_silently_drop_its_witness(self):
        for module in (C,D):
            f=fixture('sense_v1');rel,a,rows=sense_parts(f);del rel['independent_sense_witness']
            with self.assertRaisesRegex(ValueError,'omitted its independent'):
                module.validate_new_sense_receipts(a,rows,f['inputs'],audit(f))


if __name__=='__main__':
    unittest.main()

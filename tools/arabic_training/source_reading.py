"""Source-bound reading lattice using the existing lexical/acquisition owners.

Missing marks may be proposed from supplied lexical testimony. Existing letters
and marks are never repaired silently. A native reading of a derived spelling
is conditional, not an acquisition certificate for the original unmarked text.
"""
from hashlib import sha256
from itertools import product
import json
from nabt.alphabet import ALPHABET_ID
from nabt.codec import encode_cells
from nabt.corpus_evidence import learn_qac_lexicon, lexical_index, lookup_key, buckwalter_to_arabic
from nabt.learning.source_evidence import SourceBlob
from nabt.word_reader import _scan
from tools import aligned_acquisition
from tools.evidence_lifecycle_v1 import ResourceLimit
from tools.lexical_training import shared_encoder as neural
from tools.arabic_training.unit_composition import _acquire_host

LAW = 'nabt.source-neural-reading.v1'
MAX_ALTERNATIVES, MAX_BRANCHES = 32, 16

def compatible(original, proposed):
    left,right=aligned_acquisition._pieces(original),aligned_acquisition._pieces(proposed)
    return (len(left)==len(right) and all(a['raw'][0]==b['raw'][0]
            and not aligned_acquisition._classification(a['raw'])
            and set(a['raw'][1:])<=set(b['raw'][1:]) for a,b in zip(left,right)))

def substitution(original, proposed):
    """One explicit carrier substitution; no insertion, deletion or mark repair.

    This enumerates a hypothesis, not evidence that the original is misspelled.
    A lexical source and a fresh native reading are still required.
    """
    left,right=aligned_acquisition._pieces(original),aligned_acquisition._pieces(proposed)
    if len(left)!=len(right) or any(aligned_acquisition._classification(a['raw']) or
            not set(a['raw'][1:])<=set(b['raw'][1:]) for a,b in zip(left,right)):
        return None
    changes=[i for i,(a,b) in enumerate(zip(left,right)) if a['raw'][0]!=b['raw'][0]]
    if len(changes)!=1:return None
    i=changes[0]
    return {'operation':'SUBSTITUTE_ONE_CARRIER','cluster_index':i,
            'observed':left[i]['raw'][0],'proposed':right[i]['raw'][0],
            'original_is_error_established':False}

def analyze(text, *, source_id='input', lexical_text=None, mode='wasl'):
    windows=neural.source_windows(text)
    raw=text.encode();source=SourceBlob(source_id,raw)
    segments=_scan(source)
    index,summary,source_forms={},None,{}
    if lexical_text:
        lexical=learn_qac_lexicon(lexical_text.encode(),source_id='source_reading_lexical_evidence')
        index,summary=lexical_index(lexical)
        from nabt.corpus_sources import read_corpus
        corpus=read_corpus(lexical.raw,format='qac',source_id=lexical.source_id)
        source_forms={r['identity']:buckwalter_to_arabic(r['fields']['FORM'])
                      for r in corpus['records'] if r['valid']}
    try:model,model_sha=neural.load_cell_model();model_error=None
    except (OSError,ValueError) as e:model=None;model_sha=None;model_error=type(e).__name__
    rows=[]
    for segment in segments:
        if segment['kind']!='written_run':continue
        surface=segment['surface'];forms={}
        proposed=aligned_acquisition.propose_acquisition(surface,source_id=source_id,ending=mode)
        if proposed['status']=='ACQUIRED':forms[surface]=[]
        entries=index.get(lookup_key(surface),())
        lexical_matches=0
        for encoded in entries:
            entry=json.loads(encoded)
            candidates={entry['form']}
            for support in entry['supports']:
                candidates.add(source_forms[support['record_id']])
            for candidate in candidates:
                if compatible(surface,candidate):
                    lexical_matches+=1
                    forms.setdefault(candidate,[]).append({'lexical_id':entry['lexical_id'],
                        'supports':entry['supports'],'source_summary':summary})
        # Only a failed exact lexical match opens bounded spelling suggestions.
        # Never replace existing marks or automatically select a correction.
        if not lexical_matches:
            for encoded in sorted({e for group in index.values() for e in group}):
                entry=json.loads(encoded)
                candidates={entry['form']} | {source_forms[s['record_id']] for s in entry['supports']}
                for candidate in candidates:
                    if substitution(surface,candidate) is not None:
                        forms.setdefault(candidate,[]).append({'lexical_id':entry['lexical_id'],
                            'supports':entry['supports'],'source_summary':summary})
        if len(forms)>MAX_ALTERNATIVES:raise ResourceLimit('Source reading alternatives exceeded; no neural pruning')
        row={'surface':surface,'utf8_span':[segment['span']['start'],segment['span']['end']],
             'source_span':segment['span'],'alternatives':[],
             'status':'NO_SOURCE_BACKED_READING','original_text_modified':False}
        for candidate,supports in sorted(forms.items()):
            acquired,prior=_acquire_host(candidate,source_id,mode)
            edit=substitution(surface,candidate)
            alt={'surface':candidate,'lexical_supports':supports,'acquisition_owner':acquired,
                 'is_original_surface':candidate==surface,'original_marks_preserved':True,
                 'original_carriers_preserved':edit is None,'spelling_edit':edit,
                 'interpretation_scope':('CONDITIONAL_SPELLING' if edit else
                    'EXACT_SOURCE' if candidate==surface else 'CONDITIONAL_MISSING_MARKS'),
                 'authority':'SOURCE_RELATIVE_READING_CANDIDATE','intended_reading_established':False}
            if prior is not None:alt['prior_acquisition_owner']=prior
            if acquired.get('verified') and acquired.get('status')=='ACQUIRED':
                words=acquired['acquisition']['words']
                if len(words)!=1:raise ValueError('Expected one acquired candidate word')
                cells=words[0]['cells'];ids=neural.cell_ids(cells)
                alt.update(cells=cells,unit_n_decimal=str(encode_cells(cells)),alphabet_id=ALPHABET_ID,
                           neural_input_ids=ids,neural_input_equals_kernel_cells=True,
                           source_binding={'source_sha256':source.sha256,'utf8_span':row['utf8_span'],
                               'observed':surface,'proposed':candidate})
                if model is not None:
                    scores=neural.cell_logits(model,cells)
                    alt['neural_heads']={h:[{'label':label,'score':score} for label,score in
                        zip(model['labels'][h],scores[h])] for h in scores}
                    alt['neural_authority']='NONE'
            row['alternatives'].append(alt)
        if row['alternatives']:row['status']='READING_CANDIDATES'
        rows.append(row)
    restored=''.join(s['surface'] for s in segments)==text
    result={'schema':LAW,'source_id':source_id,'source_text':text,'source_sha256':source.sha256,
            'source_windows':windows,'source_restored':restored,'segments':segments,'occurrences':rows,
            'model_sha256':model_sha,'model_error':model_error,'lexical_source':summary,
            'neural_authority':'NONE','world_truth_established':False,'original_reading_certified':False,
            'contextual_choice_established':False,'complete_for_all_arabic':False,'derived_sources':[]}
    # A native acquired reading may represent a phonotactically rejected shape;
    # subsequent orthography gates must independently check every candidate.
    eligible=[[a for a in row['alternatives'] if 'cells' in a] for row in rows]
    total=1
    for choices in eligible:total*=len(choices)
    result['candidate_product']=total if rows else 0
    result['branch_status']='UNRESOLVED_WORDS'
    if rows and all(eligible):
        if total>MAX_BRANCHES:
            result['branch_status']='RESOURCE_LIMIT_ALL_WORD_ALTERNATIVES_RETAINED'
        else:
            result['branch_status']='CONDITIONAL_SOURCES'
            for choices in product(*eligible):
                by_span={tuple(r['utf8_span']):a for r,a in zip(rows,choices)}
                derived=''.join(by_span[(s['span']['start'],s['span']['end'])]['surface']
                    if (s['span']['start'],s['span']['end']) in by_span else s['surface'] for s in segments)
                if derived==text:continue
                result['derived_sources'].append({'text':derived,'sha256':sha256(derived.encode()).hexdigest(),
                    'parent_sha256':source.sha256,'mappings':[{'parent_utf8_span':r['utf8_span'],
                        'observed':r['surface'],'proposed':a['surface'],'cells':a['cells'],
                        'spelling_edit':a['spelling_edit']} for r,a in zip(rows,choices)],
                    'authority':'CONDITIONAL_READING_NOT_ORIGINAL_SOURCE_FACT'})
    return result

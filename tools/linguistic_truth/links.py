"""Compiled contract/source cross-references, not a source translation proof."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools import proof_catalog
from .inventory import ROOT, build_inventory

SOURCE_CONTRACTS = {
    'enumeration_exact':['shakhsiyya3_linguistic_truth_selected::p422'],
    'used_sense_required':['shakhsiyya3_linguistic_truth_selected::p425'],
    'figurative_requires_relation':['shakhsiyya3_linguistic_truth_selected::p425','shakhsiyya3_linguistic_truth_selected::p435'],
    'figurative_requires_exclusion':['shakhsiyya3_linguistic_truth_selected::p491'],
    'literal_keeps_origin':['shakhsiyya3_linguistic_truth_selected::p463','shakhsiyya3_linguistic_truth_selected::p474','shakhsiyya3_linguistic_truth_selected::p480'],
    'literal_support_with_false_world':['s1.words-concepts-reality'],
}


def compose(inventory, compiled):
    declarations={r['name']:r for r in compiled['theorems']}
    passages={p['passage_id']:p for p in inventory['passages']}
    rows=[]
    for suffix,ids in SOURCE_CONTRACTS.items():
        name='Nabt.LinguisticTruth.'+suffix
        declaration=declarations[name]
        if compiled['inputs'].get(declaration['source_path']) != declaration['source_sha256']:
            raise ValueError('Unbound compiled linguistic-use declaration')
        if not set(ids) <= passages.keys():
            raise ValueError('Unbound interpreted source reference')
        rows.append({'declaration':name,'statement_sha256':declaration['statement_sha256'],
            'canonical_name':declaration['canonical_name'],'source_path':declaration['source_path'],
            'source_sha256':declaration['source_sha256'],'passage_ids':ids,
            'relation':'reviewed_design_motivation_not_proof_of_translation_fidelity'})
    module=[r for r in compiled['theorems'] if r['module']=='Nabt.LinguisticTruth']
    return {'schema':'nabt.linguistic-truth-proof-links.v1',
        'inventory_review_sha256':inventory['review_sha256'],
        'compiled_catalog_sha256':proof_catalog.digest(compiled),'references':rows,
        'counts':{'module_declarations':len(module),'reference_groups':len(rows),
                  'source_reference_edges':sum(len(r['passage_ids']) for r in rows),'unresolved':0},
        'authority':'EVIDENCE_LINK_INDEX_ONLY','source_translation_fidelity_proved':False,
        'all_arabic_complete':False,'world_truth_established':False}


def build_links(*,root=ROOT,lake='lake'):
    root=Path(root)
    compiled=proof_catalog.build_catalog(root=root,lake=lake)
    inventory=build_inventory(root)
    for path,digest in compiled['inputs'].items():
        if sha256((root/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Compiled source changed during cross-reference build')
    return compose(inventory,compiled)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lake',default='lake');parser.add_argument('--output',type=Path)
    parser.add_argument('--check',type=Path);args=parser.parse_args()
    report=build_links(lake=args.lake)
    if args.check and not proof_catalog.catalog_matches(json.loads(args.check.read_text()),report):
        raise ValueError('Stored linguistic-use contract links differ')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'ok':True,**report['counts']}))


if __name__=='__main__':
    main()

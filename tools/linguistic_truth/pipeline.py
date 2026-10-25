"""Acquisition is independent of the ordering and display of retrieved text."""
from tools.grammar_catalog.retrieval import RetrievalError, _limit
from .inventory import ROOT
from .runtime import acquire
from .retrieval import LinguisticTruthSearchIndex


def run(text, *, profile_id=None, display_limit=10, reverse_candidates=False,
        vector_scores=None, budget=None, root=ROOT, **binding):
    _limit(display_limit)
    if type(reverse_candidates) is not bool:
        raise RetrievalError('reverse_candidates must be a Boolean')
    acquisition=acquire(text,profile_id=profile_id,budget=budget,root=root,**binding)
    retrieval={'status':'NOT_ATTEMPTED','authority':'RETRIEVAL_ONLY','candidates':[]}
    if acquisition.get('status') not in {'INVALID_INPUT','SOURCE_UNAVAILABLE','RESOURCE_EXHAUSTED'}:
        try:
            query=text.decode('utf-8','strict') if type(text) is bytes else text
            index=LinguisticTruthSearchIndex(root=root)
            retrieval=index.search(query,limit=1000,vector_scores=vector_scores)
            rows=list(retrieval['candidates'])
            if reverse_candidates:
                rows.reverse()
            retrieval['candidates']=[{**row,'original_rank':row['rank'],'rank':rank}
                for rank,row in enumerate(rows[:display_limit],1)]
            retrieval.update(limit=display_limit,reversed_for_diagnostic=reverse_candidates)
        except (ValueError,OSError) as exc:
            retrieval={'status':'RETRIEVAL_UNAVAILABLE','reason':str(exc),
                       'authority':'RETRIEVAL_ONLY','candidates':[]}
    return {'schema':'nabt.linguistic-truth-pipeline.v1','acquisition':acquisition,
            'retrieval':retrieval,'display_limit_affects_inference':False,
            'all_arabic_complete':False,'world_truth_established':False,
            'no_general_arabic_acquisition_claim':True}

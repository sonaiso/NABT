"""Coherent display of untrusted scores; never a linguistic acceptance gate."""
import math

CASE_LABELS=('nasb','raf','jarr','jazm')


def project_ranking(reading, scores):
    """Rank only cases inside the proposed set, retaining every original row.

    `reading` must come from the pinned native teacher. Unknown linguistic
    premises remain obligations; score projection does not discharge them.
    """
    if len(scores)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in scores):
        raise ValueError('four finite numeric scores required')
    allowed=reading['cases']
    if any(c not in CASE_LABELS for c in allowed) or len(set(allowed))!=len(allowed):
        raise ValueError('invalid native case set')
    if {r['case'] for r in reading['rows']}!=set(allowed):
        raise ValueError('native rows and cases disagree')
    raw=CASE_LABELS[max(range(4),key=lambda i:scores[i])]
    ranking=sorted(allowed,key=lambda c:(-scores[CASE_LABELS.index(c)],CASE_LABELS.index(c)))
    return dict(status='UNVERIFIED_PROPOSAL' if ranking else 'NO_SUPPORTED_READING',
                reading_rows=[dict(r) for r in reading['rows']],
                ranked_cases=ranking,raw_case_proposal=raw,
                raw_case_outside_proposed_set=raw not in allowed,
                authority='NONE',reading_licensed=False,world_truth_established=False,
                obligations=['DECLINABILITY_UNVERIFIED','KIND_UNVERIFIED','SIGN_UNVERIFIED','CLASS_UNRESOLVED'])

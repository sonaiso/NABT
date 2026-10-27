"""Input-only transport for independently frozen licensed-inference cases."""
from __future__ import annotations
from copy import deepcopy
from typing import Any


class CapabilityUnavailable(RuntimeError):
    """The requested observable capability has not been exposed by runtime."""


def build_request(case:dict[str,Any])->dict[str,Any]:
    return deepcopy(case['input'])


def execute_request(request:dict[str,Any], *, evaluate_fn=None, budget_type=None, aggregate_fn=None):
    if request['mode']=='aggregate_fixture':
        if aggregate_fn is None:
            from tools.licensed_inference import aggregate_evidence
            aggregate_fn=aggregate_evidence
        # Each fixture is a zero-rule reading with only the explicitly supplied
        # signed target facts. Cleaning removes a target present in both signs.
        rows=[{'positive':r['positive'],'negative':r['negative'],
               'clean_positive':r['positive'] and not r['negative'],
               'clean_negative':r['negative'] and not r['positive']}
              for r in request['readings']]
        result=aggregate_fn(rows)
        return {'aggregation_calculation':result,'direct_fixture_rows':rows,
                'submitted_reading_ids':[r['id'] for r in request['readings']],
                'display_limit':request.get('display_limit'),
                'world_truth_established':False,'all_arabic_complete':False,
                'authority_origin':'CALCULATION_ON_SUPPLIED_BITS_NOT_NATURAL_READING_PROOF'}
    if evaluate_fn is None or budget_type is None:
        from tools.licensed_inference import evaluate,InferenceBudget
        evaluate_fn=evaluate_fn or evaluate
        budget_type=budget_type or InferenceBudget
    kwargs={k:request[k] for k in ('source_id','revision','scope','time') if k in request}
    if 'resource_limit' in request:
        limit=request['resource_limit']
        mapping={'input_bytes':'max_source_bytes','closure_steps':'max_closure_steps'}
        if limit['kind'] not in mapping:raise CapabilityUnavailable('Unsupported budget axis')
        try:kwargs['budget']=budget_type(**{mapping[limit['kind']]:limit['value']})
        except (ValueError,TypeError) as exc:
            return {'status':'INVALID_INPUT','boundary_rejection':{'component':'runtime.InferenceBudget','type':type(exc).__name__,'message':str(exc)},'world_truth_established':False,'all_arabic_complete':False,'authority_origin':'NO_INFERENCE_AFTER_INPUT_REJECTION'}
    return evaluate_fn(request['source_text'],request['query_text'],**kwargs)

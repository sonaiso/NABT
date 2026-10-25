"""Input-only transport for the independently frozen linguistic truth gold.

This module must never read ``expected`` or adapt a request to its answer.
Semantic sense-id aliases belong in observation normalization, not input.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


def build_request(case: dict[str, Any]) -> dict[str, Any]:
    """Return only the frozen input fields; preserve raw text and invalid types."""
    return deepcopy(case["input"])


def execute_request(
    request: dict[str, Any],
    *,
    acquire: Callable[..., Any] | None = None,
    budget_type: Callable[..., Any] | None = None,
) -> Any:
    if acquire is None or budget_type is None:
        from tools.linguistic_truth import AcquisitionBudget, acquire as runtime_acquire

        acquire = acquire or runtime_acquire
        budget_type = budget_type or AcquisitionBudget
    kwargs = {"profile_id": request.get("profile_id", "linguistic")}
    if "budget" in request:
        try:
            kwargs["budget"] = budget_type(**request["budget"])
        except (TypeError, ValueError) as exc:
            # The public runtime budget constructor rejected the request before
            # acquisition. Record the actual boundary event, not an inferred
            # linguistic rejection or an exception silently scored as success.
            return {
                "status": "INVALID_INPUT",
                "boundary_rejection": {
                    "component": "runtime.AcquisitionBudget",
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
                "occurrences": [],
                "world_truth_established": False,
                "all_arabic_complete": False,
                "authority_origin": "NO_INFERENCE_AFTER_RUNTIME_INPUT_REJECTION",
            }
    return acquire(request["text"], **kwargs)


def run_case(case: dict[str, Any], **kwargs: Any) -> Any:
    return execute_request(build_request(case), **kwargs)


def run_ranking_scenario(request: dict[str, Any], *, pipeline_fn=None) -> dict[str, Any]:
    """Run the predeclared B06 perturbation; never inspect expected labels."""
    if pipeline_fn is None:
        from tools.linguistic_truth.pipeline import run as pipeline_fn
    kwargs = {"profile_id": request.get("profile_id", "linguistic")}
    baseline = pipeline_fn(request["text"], display_limit=1000, reverse_candidates=False, **kwargs)
    perturbed = pipeline_fn(request["text"], display_limit=1, reverse_candidates=True, **kwargs)
    return {"baseline": baseline, "perturbed": perturbed}

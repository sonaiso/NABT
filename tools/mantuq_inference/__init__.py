"""Source-linked, explicitly conditional mantuq/mafhum research adapter."""
from .inventory import build_inventory
from .evaluator import EvaluationBudget, evaluate, guard_verdict, opposition_shape
from .source_bound import evaluate_source
from .source_fold import fold_source, unfold_source, verify_fold

__all__ = ["build_inventory", "EvaluationBudget", "evaluate", "guard_verdict", "opposition_shape",
           "evaluate_source", "fold_source", "unfold_source", "verify_fold"]

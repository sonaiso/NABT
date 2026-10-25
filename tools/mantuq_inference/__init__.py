"""Source-linked, explicitly conditional mantuq/mafhum research adapter."""
from .inventory import build_inventory
from .evaluator import EvaluationBudget, evaluate, guard_verdict, opposition_shape

__all__ = ["build_inventory", "EvaluationBudget", "evaluate", "guard_verdict", "opposition_shape"]

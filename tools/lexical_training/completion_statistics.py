"""Conditional statistical bounds for completion evaluations (stdlib only).

These are numerical Clopper--Pearson one-sided bounds, not linguistic licenses.
The caller must establish a sampling frame and independent Bernoulli units.
Correlated rows from one root, source, or template are not independent trials.
An exhaustive finite inventory is a different claim from population inference;
these functions cannot establish sampling validity or reference correctness.

Reference: NIST/SEMATECH, exact binomial confidence intervals:
https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
The formulas use ``alpha`` as a tail error probability (0.05 for a one-sided
95% bound), not as the confidence level.  Separate returned claims do not gain
simultaneous coverage automatically: callers allocate their error budget.

The paired difference bound uses two one-sided bounds with alpha/2 each and
the union bound.  It retains the pairing through gained/lost counts.  Inputs
must already be one paired binary outcome per independent sampling unit; no
implicit row-level independence or cluster correction is inferred here.
"""

from __future__ import annotations

import math


def _probability(value: float, name: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{name} must be a real number, not a boolean")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be finite and strictly between 0 and 1")
    return value


def _counts(count: int, n: int) -> None:
    if type(count) is not int or type(n) is not int:
        raise TypeError("count and n must be integers, not booleans")
    if n < 0 or count < 0 or count > n:
        raise ValueError("counts must satisfy 0 <= count <= n")


def _log_binomial_cdf(k: int, n: int, p: float) -> float:
    """Log P[X <= k], using a mode-scaled sum rather than tiny raw masses.

    Each tail is summed away from its largest included term.  The recurrence
    therefore avoids overflow and survives tails whose raw CDF underflows.
    This is a floating-point evaluation, not an interval-arithmetic proof.
    """
    if k >= n or p <= 0.0:
        return 0.0
    if k < 0 or p >= 1.0:
        return -math.inf
    if k == 0:
        return n * math.log1p(-p)
    mode = min(k, int((n + 1) * p))
    q = 1.0 - p
    log_peak = (
        math.lgamma(n + 1)
        - math.lgamma(mode + 1)
        - math.lgamma(n - mode + 1)
        + mode * math.log(p)
        + (n - mode) * math.log1p(-p)
    )

    def relative_masses():
        yield 1.0
        mass = 1.0
        for j in range(mode, 0, -1):
            mass *= (j / (n - j + 1)) * (q / p)
            if mass == 0.0:
                break
            yield mass
        mass = 1.0
        for j in range(mode, k):
            mass *= ((n - j) / (j + 1)) * (p / q)
            if mass == 0.0:
                break
            yield mass

    return min(0.0, log_peak + math.log(math.fsum(relative_masses())))


def _upper(errors: int, n: int, log_alpha: float) -> float | None:
    if n == 0:
        return None
    if errors == n:
        return 1.0
    if errors == 0:
        return -math.expm1(log_alpha / n)
    low, high = 0.0, 1.0
    # Bisection stops when no interior float remains.  1075 halvings also
    # covers the subnormal range; ordinary confidence bounds need about 55.
    for _ in range(1075):
        mid = (low + high) / 2.0
        if mid == low or mid == high:
            break
        if _log_binomial_cdf(errors, n, mid) > log_alpha:
            low = mid
        else:
            high = mid
    return math.nextafter(high, 1.0)


def _lower(successes: int, n: int, log_alpha: float) -> float | None:
    if n == 0:
        return None
    if successes == 0:
        return 0.0
    if successes == n:
        return math.nextafter(math.exp(log_alpha / n), 0.0)
    upper = _upper(n - successes, n, log_alpha)
    return max(0.0, math.nextafter(1.0 - upper, 0.0))


def binomial_upper(errors: int, n: int, alpha: float = 0.05) -> float | None:
    """One-sided upper Clopper--Pearson error-rate bound, or None for n=0.

    With no observed errors this is ``1 - alpha**(1/n)``.  For general counts,
    invert ``P[Binomial(n, p) <= errors] = alpha`` by monotone bisection.
    The bisection endpoint is rounded outward by one representable value.
    """
    _counts(errors, n)
    alpha = _probability(alpha, "alpha")
    return _upper(errors, n, math.log(alpha))


def binomial_lower(successes: int, n: int, alpha: float = 0.05) -> float | None:
    """One-sided lower success-rate bound; n=0 has no measured bound."""
    _counts(successes, n)
    alpha = _probability(alpha, "alpha")
    return _lower(successes, n, math.log(alpha))


def zero_error_required_n(max_rate: float, alpha: float = 0.05) -> int:
    """Minimum positive n for a zero-error upper bound <= max_rate.

    This is a planning calculation under the stated sampling assumptions.
    It neither supplies independent data nor makes a test set representative.
    """
    max_rate = _probability(max_rate, "max_rate")
    alpha = _probability(alpha, "alpha")
    ratio = math.log(alpha) / math.log1p(-max_rate)
    if not math.isfinite(ratio):
        raise OverflowError("required sample count exceeds floating-point range")
    result = max(1, math.ceil(ratio))
    # Check neighboring integers to avoid a ceil error near an integer ratio.
    while -math.expm1(math.log(alpha) / result) > max_rate:
        result += 1
    while result > 1 and -math.expm1(math.log(alpha) / (result - 1)) <= max_rate:
        result -= 1
    return result


def paired_bounds(
    parent_correct: list[bool],
    current_correct: list[bool],
    alpha: float = 0.05,
) -> dict[str, int | float | None]:
    """Compare paired binary outcomes on independently sampled units.

    ``delta_lower`` conservatively bounds P[gain] - P[loss] using a union
    of alpha/2 tail errors.  ``retention_lower`` is a separate alpha bound
    conditional on units the fixed parent got right; it is None when that
    denominator is zero.  No confidence follows from a purely authored set.
    An empty comparison reports no delta and no bounds, never perfect scores.
    """
    alpha = _probability(alpha, "alpha")
    if type(parent_correct) is not list or type(current_correct) is not list:
        raise TypeError("paired outcomes must be lists of booleans")
    if len(parent_correct) != len(current_correct):
        raise ValueError("paired outcome lists must have equal lengths")
    if any(type(x) is not bool for x in parent_correct + current_correct):
        raise TypeError("each paired outcome must be a boolean, not an integer")
    n = len(parent_correct)
    gained = sum(not before and after for before, after in zip(parent_correct, current_correct))
    lost = sum(before and not after for before, after in zip(parent_correct, current_correct))
    retained = sum(before and after for before, after in zip(parent_correct, current_correct))
    result = {
        "n": n,
        "gained": gained,
        "lost": lost,
        "retained": retained,
        "parent_correct": retained + lost,
        "current_correct": retained + gained,
        "delta": (gained - lost) / n if n else None,
        "delta_lower": None,
        "retention_lower": binomial_lower(retained, retained + lost, alpha),
    }
    if n:
        # Keep alpha/2 in log space even for the smallest positive float.
        log_half_alpha = math.log(alpha) - math.log(2.0)
        gain_lower = _lower(gained, n, log_half_alpha)
        loss_upper = _upper(lost, n, log_half_alpha)
        result["delta_lower"] = max(-1.0, gain_lower - loss_upper)
    return result

"""Ramanujan's 1914 series for 1/pi — exact SymPy reference implementation.

    1/pi = (2*sqrt(2)/9801) * sum_{k>=0} (4k)! (1103 + 26390k) / ((k!)^4 396^(4k))

Each term contributes roughly 8 correct decimal digits. This module is the
ground truth the stage-1 CUDA kernel is benchmarked against: terms are exact
rationals, so any float drift in the GPU implementation shows up immediately.
"""

import sympy as sp

#: 1/pi = SERIES_PREFACTOR * sum of series terms
SERIES_PREFACTOR = 2 * sp.sqrt(2) / 9801

#: Digits of pi gained per series term (empirical, used to size partial sums)
DIGITS_PER_TERM = 8


def series_term(k: int) -> sp.Rational:
    """Return the exact k-th term of the series as a SymPy rational."""
    if k < 0:
        raise ValueError(f"series index must be >= 0, got {k}")
    num = sp.factorial(4 * k) * (1103 + 26390 * k)
    den = sp.factorial(k) ** 4 * sp.Integer(396) ** (4 * k)
    return sp.Rational(num, den)


def partial_sum(n_terms: int) -> sp.Expr:
    """Exact partial sum of the first ``n_terms`` terms (without prefactor)."""
    if n_terms < 1:
        raise ValueError(f"need at least 1 term, got {n_terms}")
    return sum(series_term(k) for k in range(n_terms))


def pi_approximation(n_terms: int, precision: int = 50) -> sp.Float:
    """Approximate pi from the first ``n_terms`` terms, to ``precision`` digits."""
    inv_pi = SERIES_PREFACTOR * partial_sum(n_terms)
    return (1 / inv_pi).evalf(precision)


def correct_digits(n_terms: int, precision: int = 60) -> int:
    """Count how many decimal digits of pi the ``n_terms``-term approximation gets right."""
    error = abs(pi_approximation(n_terms, precision) - sp.pi.evalf(precision))
    if error == 0:
        return precision
    return int(sp.floor(-sp.log(error, 10)))

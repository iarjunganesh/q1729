import pytest
import sympy as sp

from classical.ramanujan_series import (
    DIGITS_PER_TERM,
    SERIES_PREFACTOR,
    correct_digits,
    partial_sum,
    pi_approximation,
    series_term,
)


def test_term_zero_is_1103():
    assert series_term(0) == 1103


def test_terms_are_exact_rationals():
    for k in range(4):
        assert isinstance(series_term(k), sp.Rational)


def test_negative_index_rejected():
    with pytest.raises(ValueError):
        series_term(-1)


def test_partial_sum_requires_a_term():
    with pytest.raises(ValueError):
        partial_sum(0)


def test_one_term_gives_six_digits_of_pi():
    # 2*sqrt(2)*1103/9801 alone pins pi to ~1e-7
    assert abs(pi_approximation(1) - sp.pi.evalf(50)) < sp.Float("1e-6")


def test_convergence_rate_is_about_8_digits_per_term():
    gained = correct_digits(3) - correct_digits(2)
    assert gained >= DIGITS_PER_TERM - 1


def test_ten_terms_hit_at_least_78_digits():
    assert correct_digits(10, precision=120) >= 78


def test_correct_digits_saturates_at_working_precision():
    # 10 terms pin ~80 digits; at 15-digit working precision the error
    # evaluates to exactly zero, so the count saturates at `precision`
    assert correct_digits(10, precision=15) == 15


def test_prefactor_times_infinite_sum_is_inv_pi():
    # 40 terms → ~320 digits; check against 1/pi at 100 digits
    inv_pi = (SERIES_PREFACTOR * partial_sum(40)).evalf(100)
    assert abs(inv_pi - (1 / sp.pi).evalf(100)) < sp.Float("1e-99")

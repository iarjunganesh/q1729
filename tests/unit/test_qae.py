"""Unit tests for the QAE module's mathematics and guards.

The circuit itself needs a real simulator and is covered by
``tests/integration/test_qae.py``. Everything here is provable without cudaq,
which is the point: the analytic layer is what lets the integration test assert
an exact target instead of a hand-waved tolerance.
"""

import math

import pytest

from quantum import qae


@pytest.mark.parametrize("n", [1, 2, 3, 5, 8, 16])
def test_state_prep_angles_encode_the_target_amplitude_exactly(n):
    """The whole benchmark rests on A preparing exactly pi/4 — assert it, don't assume."""
    theta0, phi = qae.state_prep_angles(n)
    assert qae.exact_amplitude(theta0, phi, n) == pytest.approx(qae.TARGET_AMPLITUDE, abs=1e-12)


def test_target_amplitude_is_a_quarter_of_pi():
    assert 4.0 * qae.TARGET_AMPLITUDE == pytest.approx(math.pi)


@pytest.mark.parametrize("n", [0, -1])
def test_state_prep_angles_rejects_empty_domain(n):
    with pytest.raises(ValueError, match="at least 1 domain qubit"):
        qae.state_prep_angles(n)


def test_true_phase_matches_the_target_amplitude():
    assert math.sin(math.pi * qae.TRUE_PHASE) ** 2 == pytest.approx(qae.TARGET_AMPLITUDE)


def test_true_phase_is_pathologically_close_to_a_ten_bit_dyadic():
    """This coincidence is why accuracy plateaus at m=10; pin it so it can't drift silently."""
    assert abs(qae.TRUE_PHASE - 355 / 1024) < 3.1e-6


@pytest.mark.parametrize(("m", "expected"), [(1, 1), (2, 3), (8, 255), (16, 65535)])
def test_grover_applications_are_two_to_the_m_minus_one(m, expected):
    assert qae.grover_applications(m) == expected


def test_total_qubits_counts_both_registers_and_the_objective():
    assert qae.total_qubits(10, 2) == 13


def test_statevector_bytes_double_with_each_added_qubit():
    assert qae.statevector_bytes(10, 2) == 2 * qae.statevector_bytes(9, 2)


def test_statevector_bytes_uses_the_given_amplitude_width():
    """fp32 amplitudes are 8 bytes; fp64 would be 16 and halve the qubit ceiling."""
    assert qae.statevector_bytes(4, 2, bytes_per_amplitude=16) == 16 * 2**7


def test_amplitude_from_outcome_recovers_a_known_value():
    # y/2^m = 1/4 -> sin^2(pi/4) = 1/2
    assert qae.amplitude_from_outcome(1, 2) == pytest.approx(0.5)


def test_phase_error_is_zero_at_the_true_phase():
    m = 20
    y = round(qae.TRUE_PHASE * 2**m)
    assert qae.phase_error(y, m) < 2.0**-m


def test_phase_error_treats_the_conjugate_branch_as_equally_correct():
    """sin^2 cannot tell p from 1-p, so QAE lands on either branch legitimately."""
    m = 20
    y = round(qae.TRUE_PHASE * 2**m)
    conjugate = 2**m - y
    assert qae.phase_error(conjugate, m) == pytest.approx(qae.phase_error(y, m), abs=1e-12)


def test_phase_error_grows_away_from_the_true_phase():
    assert qae.phase_error(0, 4) > qae.phase_error(round(qae.TRUE_PHASE * 16), 4)


@pytest.mark.parametrize("m", [0, -1])
def test_estimate_rejects_empty_counting_register(m):
    """Validation runs before cudaq is imported, so this holds on any host."""
    with pytest.raises(ValueError, match="at least 1 counting qubit"):
        qae.estimate(m)


def test_estimate_rejects_zero_shots():
    with pytest.raises(ValueError, match="at least 1 shot"):
        qae.estimate(4, shots=0)

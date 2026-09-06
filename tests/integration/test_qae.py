"""Real QAE simulation — runs wherever cudaq is installed (WSL2 / CI's qpp-cpu).

Proves the circuit in ``quantum/qae.py`` actually estimates the amplitude it
claims to. The kernel bodies are JIT-compiled and invisible to coverage, so
this file is the only thing standing between a silently wrong circuit and a
run file full of confident numbers.
"""

import math

import pytest

from quantum import backend, qae

pytestmark = pytest.mark.skipif(
    not backend.cudaq_available(),
    reason="cudaq not installed (Linux/WSL2 only — see docs/adr/002-wsl2-runtime.md)",
)


@pytest.fixture(scope="module", autouse=True)
def _target():
    backend.select_target()


def test_qae_estimates_pi_within_its_resolution():
    """8 counting qubits should place pi within a couple of digits."""
    result = qae.estimate(8, domain_qubits=2, shots=2000)
    assert result["pi_estimate"] == pytest.approx(math.pi, abs=0.05)


def test_accuracy_improves_with_counting_qubits():
    """The defining property of QAE: more precision bits, less error."""
    coarse = qae.estimate(4, domain_qubits=2, shots=2000)
    fine = qae.estimate(10, domain_qubits=2, shots=2000)
    assert fine["abs_error"] < coarse["abs_error"]


def test_phase_estimate_converges_on_the_true_phase():
    """Checked in phase space, where QAE's actual convergence guarantee lives."""
    result = qae.estimate(10, domain_qubits=2, shots=2000)
    assert result["phase_error"] < 2.0**-9


def test_measurement_concentrates_rather_than_spreading():
    """A correct inverse QFT peaks; a broken one returns near-uniform noise."""
    result = qae.estimate(8, domain_qubits=2, shots=2000)
    assert result["peak_probability"] > 0.2


def test_reported_circuit_shape_matches_the_analytic_prediction():
    result = qae.estimate(6, domain_qubits=3, shots=500)
    assert result["total_qubits"] == 10
    assert result["grover_applications"] == 63
    # statevector_bytes follows the target's *actual* reported precision since
    # P1-R2 (ADR 009); it is no longer a hardcoded fp32 assumption. A complex
    # amplitude is 8 bytes at fp32 and 16 at fp64, so the expected size depends
    # on which target this host selected: the RTX 5070 runs `nvidia` (fp32),
    # while CI runs `qpp-cpu` (fp64). Asserting 8 unconditionally passed on the
    # GPU host and failed only on CI.
    bytes_per_amplitude = 8 if result["precision"] == "fp32" else 16
    assert result["statevector_bytes"] == bytes_per_amplitude * 2**10


@pytest.mark.parametrize("domain_qubits", [1, 2, 3])
def test_state_preparation_encodes_the_target_amplitude_on_hardware(domain_qubits):
    """A 1-qubit counting register measures the amplitude coarsely but unbiasedly.

    This is the circuit-level counterpart of the analytic check in the unit
    tests: it confirms the *simulated* A, not just the closed form, carries
    pi/4 across every domain width the harness might use.
    """
    result = qae.estimate(9, domain_qubits=domain_qubits, shots=2000)
    assert result["amplitude"] == pytest.approx(qae.TARGET_AMPLITUDE, abs=0.02)


def test_the_accuracy_plateau_is_real_and_reproducible():
    """Documented in harness LIMITATIONS: past m=10 the estimate stops improving.

    If a future change made this test fail, the plateau explanation in the run
    files would have become wrong — which is worth failing a build over.
    """
    at_ten = qae.estimate(10, domain_qubits=2, shots=2000)
    at_thirteen = qae.estimate(13, domain_qubits=2, shots=2000)
    assert at_thirteen["abs_error"] == pytest.approx(at_ten["abs_error"], rel=1e-6)
    assert at_thirteen["grover_applications"] == 8 * at_ten["grover_applications"] + 7

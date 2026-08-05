"""Quantum Amplitude Estimation of pi/4 — the quantum arm of the stage-1 benchmark.

The circuit is canonical QAE (Brassard, Hoyer, Mosca & Tapp, 2002): a state
preparation ``A``, a Grover operator ``Q = A S_0 A^dag S_chi``, controlled
powers ``Q^(2^j)`` driven by an ``m``-qubit counting register, and an inverse
QFT. Measuring the counting register yields an integer ``y``, from which the
amplitude estimate is ``a_hat = sin^2(pi y / 2^m)``.

**What is being measured, and what is not.** ``A`` here prepares a state whose
"good" amplitude is exactly ``pi/4``, so ``4 * a_hat`` estimates pi. This does
*not* mean the circuit discovers pi: recovering ``a_hat`` from ``y`` already
requires pi, and the gate angles are radians. The quantity this benchmark
measures is the *resource cost* — simulator wall time and VRAM — of estimating
a known amplitude to a given precision, which is exactly what the crossover
question in the README asks. See ``docs/handbook/research-standards.md`` for
the full contract and ``benchmarks/README.md`` for the recorded limitations.

Scaling knobs, both real:

- ``counting_qubits`` (``m``) sets precision; error falls as O(2^-m) while the
  circuit applies ``2^m - 1`` Grover operators, so simulated cost grows
  exponentially in the number of precision bits.
- ``domain_qubits`` (``n``) sets how wide ``A`` is, and with it the per-Grover
  gate cost (an ``n+1``-controlled Z sits inside every one).

Total width is ``m + n + 1`` qubits, which is what bounds the run on 8GB.

Everything imports cudaq inside functions, so this module is importable on a
host with no CUDA-Q at all (ADR 002).
"""

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    # CUDA-Q injects its gate vocabulary into kernel scope at JIT time; the
    # names have no Python binding at runtime. Declaring them once here tells
    # both ruff and mypy the truth — they are real inside a kernel — instead of
    # scattering a suppression comment over every gate call, which would also
    # suppress genuine typos. Assignment, not bare annotation: ruff only counts
    # the former as a binding.
    #
    # This is needed here and not in quantum/backend.py because CUDA-Q requires
    # annotations on kernel parameters, and an annotated function is one mypy
    # actually type-checks the body of.
    _Gate = Any
    h = x = z = ry = r1 = mz = _Gate

#: The amplitude ``A`` is built to encode. ``4 * a == pi`` by construction.
TARGET_AMPLITUDE = math.pi / 4

#: Per-domain-qubit rotation scale. Chosen so ``cos(phi)**n`` stays close
#: enough to 1 that :func:`state_prep_angles` can always solve for ``theta0``
#: (the arccos argument must stay within [-1, 1]); see that function.
PHI_SCALE = 0.5

#: The eigenphase QAE is actually estimating, as a fraction of pi. The counting
#: register resolves this to ``m`` bits, so ``y / 2**m`` should approach it (or
#: its conjugate ``1 - TRUE_PHASE`` — ``sin^2`` cannot distinguish the two).
#:
#: This number has a sharp consequence for the benchmark. 0.3466827... lies
#: within 3.0e-6 of 355/1024, a *10-bit* dyadic rational. Canonical QAE reads
#: out the most likely outcome, so from m = 10 upward the additional counting
#: qubits correctly return zeros and the estimate stops improving, while the
#: circuit cost keeps doubling with every added bit. The resulting error floor
#: (~3.1e-5 in pi) is a property of this particular amplitude, not a defect and
#: not a general statement about QAE — :func:`estimate` reports the phase
#: fields so the plateau is auditable in the data instead of surprising.
TRUE_PHASE = math.asin(math.sqrt(TARGET_AMPLITUDE)) / math.pi


def state_prep_angles(domain_qubits: int) -> tuple[float, float]:
    """Return ``(theta0, phi)`` making the prepared amplitude exactly TARGET_AMPLITUDE.

    ``A`` rotates the objective qubit by ``2 * (theta0 + phi * popcount(x))``
    conditioned on the domain register ``|x>``, so over the uniform
    superposition the "good" probability has the closed form::

        a = 1/2 - 1/2 * cos(2*theta0 + n*phi) * cos(phi)**n

    which inverts for ``theta0``. Solving analytically rather than fitting is
    what lets the test suite assert the exact target instead of a tolerance.
    """
    if domain_qubits < 1:
        raise ValueError(f"need at least 1 domain qubit, got {domain_qubits}")
    phi = PHI_SCALE / domain_qubits
    cosine = (1.0 - 2.0 * TARGET_AMPLITUDE) / (math.cos(phi) ** domain_qubits)
    theta0 = (math.acos(cosine) - domain_qubits * phi) / 2.0
    return theta0, phi


def exact_amplitude(theta0: float, phi: float, domain_qubits: int) -> float:
    """The amplitude ``A`` actually prepares, from the closed form above.

    Used to verify the circuit encodes what :func:`state_prep_angles` claims,
    independently of any simulation.
    """
    return 0.5 - 0.5 * math.cos(2.0 * theta0 + domain_qubits * phi) * (math.cos(phi) ** domain_qubits)


def grover_applications(counting_qubits: int) -> int:
    """Number of Grover operators the circuit applies: ``2^m - 1``.

    The dominant cost term, and the reason precision is expensive: each extra
    bit of precision doubles the work *and* doubles the state vector.
    """
    return 2**counting_qubits - 1


def total_qubits(counting_qubits: int, domain_qubits: int) -> int:
    """Circuit width: counting register + domain register + objective qubit."""
    return counting_qubits + domain_qubits + 1


def statevector_bytes(counting_qubits: int, domain_qubits: int, bytes_per_amplitude: int = 8) -> int:
    """Statevector footprint. The ``nvidia`` target defaults to fp32, so a
    complex amplitude is 8 bytes — this is what sets the qubit ceiling on 8GB."""
    return bytes_per_amplitude * 2 ** total_qubits(counting_qubits, domain_qubits)


def amplitude_from_outcome(y: int, counting_qubits: int) -> float:
    """Map a counting-register outcome to an amplitude estimate."""
    return math.sin(math.pi * y / 2**counting_qubits) ** 2


def phase_error(y: int, counting_qubits: int) -> float:
    """Distance from the measured phase to TRUE_PHASE, up to conjugation.

    ``sin^2`` maps ``p`` and ``1 - p`` to the same amplitude, so QAE lands on
    either branch with equal right; comparing against both is the honest
    measure of how well the counting register resolved the phase.
    """
    measured = y / 2**counting_qubits
    return min(abs(measured - TRUE_PHASE), abs((1.0 - measured) - TRUE_PHASE))


def _build_circuit() -> Any:
    """Construct the QAE kernel.

    Kernels are built here rather than at module scope so that importing
    ``quantum.qae`` never requires cudaq (see the module docstring). Every
    kernel body below is JIT-compiled by CUDA-Q and therefore invisible to
    coverage; ``tests/integration/test_qae.py`` is what proves they run.
    """
    import cudaq

    @cudaq.kernel
    def prepare(domain: cudaq.qview, obj: cudaq.qubit, theta0: float, phi: float):  # pragma: no cover
        # A: uniform superposition over the domain, then a rotation on the
        # objective qubit whose angle is linear in the domain bits.
        for i in range(domain.size()):
            h(domain[i])
        ry(2.0 * theta0, obj)
        for i in range(domain.size()):
            ry.ctrl(2.0 * phi, domain[i], obj)

    @cudaq.kernel
    def unprepare(domain: cudaq.qview, obj: cudaq.qubit, theta0: float, phi: float):  # pragma: no cover
        # A^dagger: exact reverse of prepare, with negated angles.
        for i in range(domain.size()):
            ry.ctrl(-2.0 * phi, domain[i], obj)
        ry(-2.0 * theta0, obj)
        for i in range(domain.size()):
            h(domain[i])

    @cudaq.kernel
    def grover(domain: cudaq.qview, obj: cudaq.qubit, theta0: float, phi: float):  # pragma: no cover
        # Q = A S_0 A^dag S_chi, applied left-to-right as S_chi, A^dag, S_0, A.
        z(obj)  # S_chi: phase-flip the good state |1>
        unprepare(domain, obj, theta0, phi)
        for i in range(domain.size()):  # S_0: phase-flip |0...0>
            x(domain[i])
        x(obj)
        z.ctrl(domain, obj)
        x(obj)
        for i in range(domain.size()):
            x(domain[i])
        prepare(domain, obj, theta0, phi)

    @cudaq.kernel
    def circuit(m: int, n: int, theta0: float, phi: float):  # pragma: no cover
        counting = cudaq.qvector(m)
        domain = cudaq.qvector(n)
        obj = cudaq.qubit()

        h(counting)
        prepare(domain, obj, theta0, phi)

        for j in range(m):
            for _ in range(2**j):
                cudaq.control(grover, counting[j], domain, obj, theta0, phi)
                # Q as decomposed above carries a global phase of -1 relative
                # to the eigenphase convention a_hat = sin^2(pi y / 2^m).
                # A global phase is unobservable in Q itself, but becomes a
                # real relative phase once Q is controlled, and would bias
                # every estimate by exactly half the counting range. This z
                # cancels it. Verified: without it the estimator converges to
                # a_hat + 1/2, not a_hat.
                z(counting[j])

        # Inverse QFT: the exact reverse of the forward QFT, with negated
        # angles and no bit-reversal swap layer — CUDA-Q's measurement bit
        # order already matches the counting register's significance, so a
        # swap layer here would un-align it (verified against exactly
        # representable phases before this was committed).
        for i in range(m - 1, -1, -1):
            for k in range(m - 1, i, -1):
                r1.ctrl(-math.pi / (2.0 ** (k - i)), counting[k], counting[i])
            h(counting[i])

        mz(counting)

    return circuit


def estimate(counting_qubits: int, domain_qubits: int = 2, shots: int = 2000) -> dict[str, Any]:
    """Run QAE and return the estimate together with its full provenance.

    The returned dict is what the benchmark harness writes into a run file, so
    it carries the circuit's shape (qubits, Grover count) alongside the result
    — a number without the circuit that produced it is not reproducible.
    """
    if counting_qubits < 1:
        raise ValueError(f"need at least 1 counting qubit, got {counting_qubits}")
    if shots < 1:
        raise ValueError(f"need at least 1 shot, got {shots}")

    import cudaq

    theta0, phi = state_prep_angles(domain_qubits)
    circuit = _build_circuit()
    result = cudaq.sample(circuit, counting_qubits, domain_qubits, theta0, phi, shots_count=shots)
    counts = {bits: result.count(bits) for bits in result}

    best = max(counts, key=lambda bits: counts[bits])
    y = int(best, 2)
    amplitude = amplitude_from_outcome(y, counting_qubits)
    pi_estimate = 4.0 * amplitude

    return {
        "counting_qubits": counting_qubits,
        "domain_qubits": domain_qubits,
        "total_qubits": total_qubits(counting_qubits, domain_qubits),
        "grover_applications": grover_applications(counting_qubits),
        "statevector_bytes": statevector_bytes(counting_qubits, domain_qubits),
        "shots": shots,
        "outcome": y,
        "peak_probability": counts[best] / shots,
        "amplitude": amplitude,
        "pi_estimate": pi_estimate,
        "abs_error": abs(pi_estimate - math.pi),
        # Phase-space view of the same result. Recorded because the pi-space
        # error alone cannot distinguish "the register ran out of resolution"
        # from "the target phase is very close to a low-order dyadic" — see
        # TRUE_PHASE. Comparing phase_error against 2**-counting_qubits tells
        # a reader which regime a row is in.
        "phase_estimate": y / 2**counting_qubits,
        "true_phase": TRUE_PHASE,
        "phase_error": phase_error(y, counting_qubits),
        "phase_resolution": 2.0**-counting_qubits,
    }

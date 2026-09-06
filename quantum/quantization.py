"""Analytic QAE quantization: what the circuit *must* return, before it is run.

Roadmap P1-R3 requires the QAE error floor to be explained analytically rather
than asserted from a measurement, and the sampled outcome distribution to be
checked against the distribution theory predicts. Everything here is closed
form on the CPU — no cudaq, no GPU, nothing timed — so it is an independent
reference for :mod:`quantum.qae`, not a restatement of it.

Two facts do the work.

**The estimate is quantized.** Canonical QAE reports the most likely counting
outcome ``y``, and the amplitude is recovered as ``sin(pi*y/2^m)**2``. Only
``2^m`` amplitudes are therefore reachable at all. The reported value is the
one whose grid point sits nearest the true phase, so the error is set by the
distance from the true phase to the grid — not by shot noise, which only
decides how reliably that grid point wins.

**This particular phase sits very close to a coarse grid point.**
``TRUE_PHASE = 0.34668270...`` lies within 3.0e-6 of ``355/1024``, a 10-bit
dyadic rational. From ``m = 10`` the nearest grid point keeps landing on that
same value, so the estimate stops changing while the circuit cost keeps
doubling. :func:`plateau_bounds` derives where that run starts and ends
instead of quoting it; the answer is a *finite* interval, which is the
correction P1-R2 made to the earlier "improves no further" phrasing.

The distribution has two peaks, not one. Grover's operator has eigenvalues
``exp(+-2i*theta)``, so the counting register holds an equal mixture of phase
``theta`` and its conjugate ``1 - theta``. Both recover the *same* amplitude,
because ``sin(pi*(1-t)) == sin(pi*t)`` — which is why a tie between them is a
genuine tie rather than a bug, and why :func:`quantum.qae.estimate` breaks
ties by bitstring instead of leaving it to dict order.
"""

import math

from quantum.qae import TRUE_PHASE, amplitude_from_outcome

#: Largest counting register :func:`ideal_distribution` will enumerate. The
#: distribution has ``2^m`` entries, so this is a memory guard, not physics.
MAX_ENUMERATED_QUBITS = 20

#: Double precision cannot resolve a relative error below about this. Any
#: "correct digits" figure at or beyond it is a statement about the float
#: reference, not about the estimator that produced it.
DOUBLE_PRECISION_FLOOR = 2.220446049250313e-16


def ideal_outcome(counting_qubits: int) -> int:
    """The counting outcome an ideal, noiseless QAE run is most likely to give.

    The grid point nearest ``TRUE_PHASE``. Ties at exactly half a grid step
    round to even, which is :func:`round`'s documented behaviour and is stated
    here so the choice is not accidental.
    """
    require_qubits(counting_qubits)
    return round(TRUE_PHASE * 2**counting_qubits)


def ideal_estimate(counting_qubits: int) -> float:
    """The pi estimate implied by :func:`ideal_outcome` — no sampling involved."""
    return 4.0 * amplitude_from_outcome(ideal_outcome(counting_qubits), counting_qubits)


def quantization_error(counting_qubits: int) -> float:
    """Absolute error of the ideal estimate against math.pi.

    This is the floor: no number of shots reduces it, because it is the
    distance from the true phase to the reachable grid, not sampling spread.
    """
    return abs(ideal_estimate(counting_qubits) - math.pi)


def relative_quantization_error(counting_qubits: int) -> float:
    """:func:`quantization_error` as a fraction of pi.

    Reported separately because the two are routinely conflated. Absolute
    error answers "how far from pi"; relative error is what "correct digits"
    is derived from, and only the relative quantity is comparable against
    :data:`DOUBLE_PRECISION_FLOOR`.
    """
    return quantization_error(counting_qubits) / math.pi


def plateau_bounds(counting_qubits: int, search_limit: int = 64) -> tuple[int, int]:
    """Inclusive range of ``m`` sharing this ``m``'s ideal estimate.

    Walks outward from ``counting_qubits`` while the ideal estimate is
    bit-identical. Returns ``(first, last)``. A single-member plateau returns
    ``(m, m)``. ``search_limit`` bounds the walk so a pathological phase
    cannot spin forever.
    """
    require_qubits(counting_qubits)
    if search_limit < counting_qubits:
        raise ValueError("search_limit must not be below counting_qubits")
    target = ideal_estimate(counting_qubits)
    first = counting_qubits
    while first > 1 and ideal_estimate(first - 1) == target:
        first -= 1
    last = counting_qubits
    while last < search_limit and ideal_estimate(last + 1) == target:
        last += 1
    return first, last


def conjugate_outcome(outcome: int, counting_qubits: int) -> int:
    """The other peak: ``2^m - y``, which encodes the same amplitude.

    Grover's two eigenphases put equal weight on ``y`` and its conjugate, and
    ``sin(pi*(2^m - y)/2^m) == sin(pi*y/2^m)``, so both recover an identical
    estimate. Either may win a finite-shot run. ``y = 0`` is its own conjugate.
    """
    return (require_outcome(outcome, counting_qubits) - outcome) % 2**counting_qubits


def agrees_with_theory(outcome: int, counting_qubits: int, tolerance: float = 1e-12) -> bool:
    """Whether a measured outcome recovers the ideal estimate.

    True for the ideal peak *and* its conjugate, which is the honest test: a
    run that lands on the conjugate has not disagreed with theory. Compares
    the recovered estimates rather than the raw integers for exactly that
    reason.
    """
    require_outcome(outcome, counting_qubits)
    recovered = 4.0 * amplitude_from_outcome(outcome, counting_qubits)
    return abs(recovered - ideal_estimate(counting_qubits)) <= tolerance


def outcome_probability(outcome: int, counting_qubits: int) -> float:
    """Ideal probability of counting outcome ``outcome``.

    The Fejer/Dirichlet kernel of phase estimation, averaged over the two
    eigenphases ``theta`` and ``1 - theta``::

        P(y) = 1/2 * [ K(theta - y/2^m) + K(1 - theta - y/2^m) ]
        K(d) = sin(pi * 2^m * d)^2 / (2^2m * sin(pi * d)^2),  K(0) = 1

    Exact for a noiseless simulator; it says nothing about hardware noise.
    """
    size = require_outcome(outcome, counting_qubits)
    grid = outcome / size
    return 0.5 * (_kernel(TRUE_PHASE - grid, size) + _kernel(1.0 - TRUE_PHASE - grid, size))


def _kernel(delta: float, size: int) -> float:
    """Squared Dirichlet kernel at phase offset ``delta``, period 1."""
    offset = delta - math.floor(delta)
    if offset == 0.0:
        return 1.0
    denominator = size * math.sin(math.pi * offset)
    return (math.sin(math.pi * size * offset) / denominator) ** 2


def ideal_distribution(counting_qubits: int) -> dict[int, float]:
    """Every ideal outcome probability, keyed by counting outcome.

    Sums to 1 to within floating-point rounding; :func:`total_variation`
    relies on that rather than renormalizing, so a future error in
    :func:`outcome_probability` surfaces instead of being divided away.
    """
    require_qubits(counting_qubits)
    if counting_qubits > MAX_ENUMERATED_QUBITS:
        raise ValueError(f"refusing to enumerate 2^{counting_qubits} outcomes")
    return {y: outcome_probability(y, counting_qubits) for y in range(2**counting_qubits)}


def total_variation(counts: dict[str, int], counting_qubits: int) -> float:
    """Total-variation distance between sampled counts and the ideal distribution.

    ``counts`` is the bitstring histogram :func:`quantum.qae.estimate` records.
    Zero means the sample matched theory exactly; 1 means disjoint support.
    Finite-shot sampling always leaves a positive distance, so this is a
    diagnostic to be read against :func:`sampling_tolerance`, never a pass/fail
    on its own.
    """
    ideal = ideal_distribution(counting_qubits)
    shots = sum(counts.values())
    if shots <= 0:
        raise ValueError("counts must contain at least one shot")
    observed: dict[int, float] = {}
    for bits, count in counts.items():
        if count < 0:
            raise ValueError("counts must not be negative")
        if len(bits) != counting_qubits or bits.strip("01"):
            raise ValueError(f"outcome {bits!r} is not {counting_qubits} bits")
        observed[int(bits, 2)] = observed.get(int(bits, 2), 0.0) + count / shots
    keys = set(ideal) | set(observed)
    return 0.5 * math.fsum(abs(observed.get(y, 0.0) - ideal.get(y, 0.0)) for y in keys)


def sampling_tolerance(counting_qubits: int, shots: int) -> float:
    """Scale of the total-variation distance expected from finite shots alone.

    A multinomial sample of ``shots`` draws over a support of effective size
    ``k`` sits at a total-variation distance of order ``sqrt(k / shots)`` from
    its own distribution. Here ``k`` is the participating support, not ``2^m``,
    because phase estimation concentrates on a few outcomes. This is an
    order-of-magnitude reference for reading :func:`total_variation`, not a
    confidence interval and not a hypothesis test.
    """
    require_qubits(counting_qubits)
    if shots < 1:
        raise ValueError(f"need at least 1 shot, got {shots}")
    ideal = ideal_distribution(counting_qubits)
    # Participation ratio: the effective number of outcomes carrying weight.
    effective = 1.0 / math.fsum(p * p for p in ideal.values())
    return math.sqrt(effective / shots)


def require_qubits(counting_qubits: int) -> int:
    """Reject counting-register sizes the formulas do not cover; return ``2^m``."""
    if counting_qubits < 1:
        raise ValueError(f"need at least 1 counting qubit, got {counting_qubits}")
    return 2**counting_qubits


def require_outcome(outcome: int, counting_qubits: int) -> int:
    """Reject outcomes outside the counting register; return ``2^m``."""
    size = require_qubits(counting_qubits)
    if not 0 <= outcome < size:
        raise ValueError(f"outcome must lie in [0, {size}), got {outcome}")
    return size

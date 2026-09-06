"""The measurement protocol, committed before any data is collected.

Roadmap P1-R3 requires the sweep, repeats, uncertainty treatment, exclusions
and stopping rule to be fixed *before* a run, not chosen afterwards once the
numbers are visible. Putting them here as module constants means changing any
of them is a reviewable diff, the same discipline
:data:`benchmarks.harness.HYPOTHESIS` already gets.

:func:`digest` hashes the whole declaration into every run file, so a result
can be matched to the exact protocol it followed. Two runs whose protocol
digests differ were not measured the same way and must not be pooled.

The honest limits of this file: it fixes *what* will be measured and how the
numbers will be treated. It cannot make a timing boundary meaningful, and it
does not establish that the declared sweep is wide enough to answer the
question. Those are judgements the run file's limitations must carry.
"""

import hashlib
import json
import math
import statistics
from typing import Any

#: Bumped whenever any declaration below changes meaning. The digest catches
#: every edit; this number is the human-readable signal that it was deliberate.
PROTOCOL_VERSION = 1

#: What each timed phase includes and excludes. The archived stage-1 run timed
#: only ``end_to_end``, which is why its classical figures cannot be read as
#: device execution cost — the audit's "sub-millisecond" claim conflated the
#: two. Naming the boundaries is the repair; measuring them is
#: :func:`classical.cuda_kernel.time_phases`.
TIMING_BOUNDARIES = {
    "end_to_end": (
        "Host wall time around the whole Python call, measured with "
        "time.perf_counter. Includes every phase below plus interpreter "
        "overhead. This is the number the archived stage-1 run reported and "
        "the only one comparable against it."
    ),
    "kernel_handle": (
        "Acquiring the callable kernel: NVRTC source load and module "
        "construction. cupy caches compiled modules by source, so after "
        "warm-up this is wrapper cost, not compilation."
    ),
    "allocate": "Allocating the device buffer that receives block partial sums.",
    "execute": (
        "Kernel launch to completion, measured with CUDA events on the "
        "device. This is the only phase that is device execution time; "
        "everything else is host or transfer cost."
    ),
    "transfer": "Device-to-host copy of the block partial sums.",
    "host_reduce": (
        "math.fsum over the block partials on the host. Deliberately not on "
        "the device: an in-kernel atomicAdd commits in nondeterministic order."
    ),
}

#: Discarded, never recorded as a sample.
WARMUP_POLICY = (
    "Exactly one untimed warm-up call per configuration, discarded, to absorb "
    "NVRTC compilation and CUDA context creation. Warm-up does not remove "
    "per-call wrapper work, which is why that work is measured as its own "
    "phase rather than assumed negligible."
)

#: No outlier rejection. Stated positively so its absence is a decision.
EXCLUSION_RULE = (
    "No outlier rejection, trimming or winsorizing. Every timed repeat enters "
    "the summary and is retained raw in the run file. A repeat is discarded "
    "only if the arm raised, in which case the whole configuration is recorded "
    "as failed rather than partially summarized."
)

#: The anti-p-hacking clause.
STOPPING_RULE = (
    "The sweep and repeat count are fixed before the run and are not extended, "
    "truncated or re-run based on the values observed. A configuration that "
    "exceeds its wall-clock budget aborts the run; the completed configurations "
    "are archived with the abort recorded, and the sweep is not silently "
    "shortened. Re-running after a change writes a new archive alongside the "
    "old one; results are never selected across runs."
)

UNCERTAINTY_METHOD = (
    "Per configuration: mean, minimum, sample standard deviation, standard "
    "error of the mean, and a two-sided 95% confidence interval for the mean "
    "from Student's t with n-1 degrees of freedom. The interval describes the "
    "mean of repeated timings on this host under this power profile; it is not "
    "a claim about other hardware, and timing samples are not independent "
    "across thermal drift, so it is a lower bound on real uncertainty."
)

#: Two-sided 95% Student's t critical values by degrees of freedom. A short
#: table beats a scipy dependency the CPU-only requirements file must not gain.
_T95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    25: 2.060,
    30: 2.042,
    40: 2.021,
    60: 2.000,
    120: 1.980,
}

#: Above the table's reach the t distribution is within a percent of normal.
_Z95 = 1.960


def t_critical(degrees_of_freedom: int) -> float:
    """Two-sided 95% critical value, conservative between tabulated points.

    Falls back to the nearest tabulated ``df`` at or below the request, which
    overstates the interval slightly rather than understating it. Above the
    table it returns the normal value.
    """
    if degrees_of_freedom < 1:
        raise ValueError(f"need at least 1 degree of freedom, got {degrees_of_freedom}")
    if degrees_of_freedom > max(_T95):
        return _Z95
    return _T95[max(df for df in _T95 if df <= degrees_of_freedom)]


def uncertainty(samples: list[float]) -> dict[str, float]:
    """Summarize timing samples with an explicit uncertainty, keeping the raw data.

    A single repeat has no spread and no defined interval. That case reports
    zeros and carries ``repeats = 1`` so a reader can see why the interval is
    degenerate, rather than being handed a fabricated one.
    """
    if not samples:
        raise ValueError("need at least 1 sample")
    if any(not math.isfinite(value) or value < 0.0 for value in samples):
        raise ValueError("timing samples must be finite and non-negative")
    mean = statistics.fmean(samples)
    count = len(samples)
    stdev = statistics.stdev(samples) if count > 1 else 0.0
    sem = stdev / math.sqrt(count) if count > 1 else 0.0
    half_width = t_critical(count - 1) * sem if count > 1 else 0.0
    return {
        "mean_s": mean,
        "min_s": min(samples),
        "stdev_s": stdev,
        "sem_s": sem,
        "ci95_low_s": mean - half_width,
        "ci95_high_s": mean + half_width,
        "relative_stdev": stdev / mean if mean > 0.0 else 0.0,
        "repeats": count,
    }


def declaration() -> dict[str, Any]:
    """The full protocol as it will be recorded in a run file."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "timing_boundaries": dict(TIMING_BOUNDARIES),
        "warmup_policy": WARMUP_POLICY,
        "exclusion_rule": EXCLUSION_RULE,
        "stopping_rule": STOPPING_RULE,
        "uncertainty_method": UNCERTAINTY_METHOD,
    }


def digest_of(declared: Any) -> str:
    """Stable SHA-256 over any protocol declaration.

    Sorted keys and a compact separator make the hash depend on the declared
    content, not on formatting. Takes the declaration as an argument so an
    archived run can be checked against the protocol *it* recorded — hashing
    the current module instead would make every past run fail the moment this
    file changes, which is precisely backwards.
    """
    canonical = json.dumps(declared, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def digest() -> str:
    """:func:`digest_of` applied to the protocol this module currently declares.

    Runs whose digests differ were measured under different protocols and must
    not be pooled.
    """
    return digest_of(declaration())

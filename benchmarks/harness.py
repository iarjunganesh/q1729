"""Stage-1 crossover benchmark: hand-written CUDA kernel vs QAE, same silicon.

Emits a run file conforming to the research-standards contract in
``docs/handbook/research-standards.md`` — the declared question, hypothesis,
variables, controls, hardware, software versions, statistical treatment, raw
per-repeat data, and limitations all travel with the numbers, in one file.

    python -m benchmarks.harness --power-profile turbo --time-budget-s 3600 --out benchmarks/runs/<name>.json

Both arms are timed the same way: a warm-up call absorbs compilation and
context setup, then every repeat is recorded individually. Summaries are
derived from the samples; the samples themselves are never discarded, because
the narrator (ADR 003) and any later statistical treatment need the raw data,
not somebody's mean.

A run that stops early is still evidence. When the declared time budget runs
out, an arm raises, or the operator interrupts, the completed configurations
and the raw samples of the unfinished one are archived as an ``aborted``
record (ADR 011), and the run exits nonzero.
"""

import argparse
import json
import math
import signal
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from benchmarks import archive, environment, protocol, provenance, run_file

#: Term counts swept on the classical arm. Deliberately spans past the point
#: where double precision saturates, so the saturation shows up as measured
#: data rather than as a claim in prose.
CLASSICAL_TERM_COUNTS = (1, 2, 3, 4, 6, 8, 16, 64, 256, 1024, 4096, 16384)

#: Counting-register sizes swept on the quantum arm. Each step doubles both
#: the statevector and the Grover count, so the top of this range is where a
#: single run stops being minutes and starts being hours.
QUANTUM_COUNTING_QUBITS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

#: Domain-register width, held fixed across the sweep — it is a control, not
#: a variable, in this experiment.
DOMAIN_QUBITS = 2

#: The question this harness answers, restated in every run file it writes.
RESEARCH_QUESTION = (
    "On one RTX 5070, what does it cost in wall time to reach a given absolute "
    "error in pi via a hand-written CUDA C++ kernel evaluating Ramanujan's 1914 "
    "series, versus via Quantum Amplitude Estimation simulated on cuStateVec?"
)

HYPOTHESIS = (
    "The classical kernel reaches double-precision saturation (~1e-16) in under a "
    "millisecond, while simulated QAE's error falls only as O(2^-m) against a cost "
    "that doubles with every precision bit. No crossover is expected on this "
    "silicon; the deliverable is the measured shape and separation of the two curves."
)

LIMITATIONS = (
    "Simulated QAE is not a quantum computer: this measures the cost of simulating "
    "the circuit on a GPU, which is not evidence about real quantum hardware.",
    "The QAE circuit estimates an amplitude constructed to equal pi/4. Recovering pi "
    "from the outcome already uses pi, so this is a resource-cost measurement, not a "
    "computation that discovers pi. See quantum/qae.py.",
    "The classical arm is double precision and saturates near 15-16 correct digits "
    "regardless of term count; extending past that would need multi-precision "
    "arithmetic on the GPU, which this phase does not implement.",
    "Device memory is sampled before/after each configuration, not a process-specific peak.",
    "The observed m=10..16 plateau is consistent with proximity to 355/1024; it is not an infinite-precision floor.",
    "Sampled utilization does not establish a dispatch bottleneck; profiling is required before causal claims.",
    "Seeded sampling does not guarantee bitwise reproduction across hardware, targets or versions.",
    "Single machine, single GPU. The datacenter (H100) axis of roadmap Phase 1 has "
    "not been run, so nothing here establishes how the curves move on other silicon.",
)

STATISTICAL_TREATMENT = (
    "One warm-up call per configuration (discarded) to absorb NVRTC/JIT compilation "
    "and CUDA context creation, then N timed repeats recorded individually. Reported "
    "summaries are the mean, minimum, sample standard deviation, standard error and "
    "a two-sided 95% t interval for the mean over those repeats. No outlier rejection "
    "is applied; the raw samples are retained in the run file so any later treatment "
    "can be applied and audited after the fact. The full declaration — timing "
    "boundaries, warm-up, exclusions, stopping rule — is committed in "
    "benchmarks/protocol.py and travels in this file's protocol block with its digest."
)


class BudgetExceeded(RuntimeError):
    """The declared wall-clock budget ran out; the run stops at a call boundary."""


class Budget:
    """The run's declared total wall-clock budget, checked between timed calls.

    A GPU call already in flight is never interrupted — stopping one mid-flight
    would leave the device in an unknown state and the sample meaningless — so
    elapsed time can exceed the budget by at most one call. The check happens
    before every warm-up and every timed repeat, which is the finest boundary
    at which stopping keeps each recorded sample whole.
    """

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.seconds = seconds
        self._clock = clock
        self._start = clock()
        self.interrupt_requested = False

    def elapsed(self) -> float:
        return self._clock() - self._start

    def request_stop(self, signum: int, frame: Any) -> None:
        """SIGINT handler: record the request; :meth:`check` honors it.

        Raising from the handler is unsafe under CUDA-Q. Its runtime replaces
        Python's SIGINT handler with its own, which ends the process without
        an archive. Restoring Python's default handler instead lets a Ctrl-C
        land mid-JIT-compilation, where CUDA-Q aborts the compile and the
        process hangs (both reproduced on cudaq 0.16.0.post1, 2026-09-23). So
        the first Ctrl-C only sets a flag, and the run stops at the next call
        boundary exactly as it does for the budget. A second Ctrl-C raises
        immediately, the escape hatch for a call that never returns.
        """
        if self.interrupt_requested:
            raise KeyboardInterrupt("second interrupt; stopping immediately")
        self.interrupt_requested = True
        print("interrupt received; stopping at the next call boundary (Ctrl-C again to force)", flush=True)

    def check(self, before: str) -> None:
        if self.interrupt_requested:
            raise KeyboardInterrupt(f"operator interrupt, honored before {before}")
        if self.elapsed() > self.seconds:
            raise BudgetExceeded(f"time budget of {self.seconds:g} s exhausted before {before}")


class ConfigurationAborted(Exception):
    """A configuration stopped part-way; carries its raw samples to the archive.

    ``partial`` holds every sample and outcome recorded before the stop, with
    no summary statistics — an unfinished configuration is never summarized
    (protocol exclusion rule). ``cause`` is the exception that stopped it.
    """

    def __init__(self, partial: dict[str, Any], cause: BaseException) -> None:
        super().__init__(f"{type(cause).__name__}: {cause}")
        self.partial = partial
        self.cause = cause


def _check(budget: Budget | None, before: str) -> None:
    if budget is not None:
        budget.check(before)


def correct_digits(estimate: float) -> float:
    """Correct decimal digits of pi in ``estimate``, as a continuous quantity.

    Returned as a float so it can be plotted as an axis. An exact match is
    reported at double precision's ceiling rather than as infinity.
    """
    error = abs(estimate - math.pi)
    if error == 0.0:
        return 16.0
    return -math.log10(error / math.pi)


def summarize(samples: list[float]) -> dict[str, float]:
    """Summary and uncertainty for timing samples, keeping the samples themselves.

    Delegates to :func:`benchmarks.protocol.uncertainty` so the treatment a run
    file reports is literally the one the committed protocol declares, rather
    than a second implementation that could drift away from it.
    """
    summary = protocol.uncertainty(samples)
    summary.pop("repeats")  # the row carries its own repeat count
    return summary


def classical_outcome(partial: float) -> dict[str, float]:
    """The π estimate and its error, derived from one timed partial sum."""
    estimate = 1.0 / ((2.0 * math.sqrt(2.0) / 9801.0) * partial)
    return {
        "partial_sum": partial,
        "pi_estimate": estimate,
        "abs_error": abs(estimate - math.pi),
        "correct_digits": correct_digits(estimate),
    }


def measure_classical(
    term_counts: tuple[int, ...],
    repeats: int,
    budget: Budget | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Time the CUDA kernel across ``term_counts``, appending each row to ``rows``.

    The timed loop is :func:`classical.cuda_kernel.time_partial_sum`'s loop —
    one discarded warm-up, then ``perf_counter`` around each ``partial_sum``
    call — run here so the budget is checked between repeats and a stop keeps
    the samples already taken. Rows accumulate in the caller's list as each
    configuration completes, so an abort cannot discard finished work.
    """
    from classical import cuda_kernel

    rows = [] if rows is None else rows
    for n_terms in term_counts:
        samples: list[float] = []
        outcomes: list[dict[str, Any]] = []
        try:
            _check(budget, f"classical warm-up n_terms={n_terms}")
            with environment.LoadSampler() as sampler:
                cuda_kernel.partial_sum(n_terms)  # warm-up: compile + context
                for repeat in range(repeats):
                    _check(budget, f"classical n_terms={n_terms} repeat {repeat}")
                    start = time.perf_counter()
                    partial = cuda_kernel.partial_sum(n_terms)
                    elapsed = time.perf_counter() - start
                    outcome = classical_outcome(partial)
                    samples.append(elapsed)
                    outcomes.append(outcome)
            estimate = outcomes[-1]["pi_estimate"]
            row = {
                "method": "classical-cuda",
                "gpu_under_load": sampler.summary(),
                "n_terms": n_terms,
                "outcomes": outcomes,
                "pi_estimate": estimate,
                "abs_error": abs(estimate - math.pi),
                "correct_digits": correct_digits(estimate),
                "repeats": repeats,
                "samples_s": samples,
                **summarize(samples),
            }
        except (Exception, KeyboardInterrupt) as exc:
            partial_record = {
                "method": "classical-cuda",
                "n_terms": n_terms,
                "samples_s": samples,
                "outcomes": outcomes,
            }
            raise ConfigurationAborted(partial_record, exc) from exc
        rows.append(row)
    return rows


def measure_quantum(
    counting_qubits: tuple[int, ...],
    domain_qubits: int,
    shots: int,
    repeats: int,
    target: str,
    seed: int | None = None,
    budget: Budget | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Time QAE across counting-register sizes, appending each row to ``rows``.

    Same stop semantics as :func:`measure_classical`: the budget is checked
    before the warm-up and every repeat, and a stop raises
    :class:`ConfigurationAborted` carrying the samples and count
    distributions already recorded for the unfinished configuration.
    """
    from quantum import qae

    rows = [] if rows is None else rows
    for m in counting_qubits:
        samples: list[float] = []
        outcomes: list[dict[str, Any]] = []
        try:
            _check(budget, f"quantum warm-up counting_qubits={m}")
            qae.estimate(m, domain_qubits, shots=shots)  # warm-up: JIT + context

            before = environment.gpu_memory_used_mib()
            result: dict[str, Any] = {}
            with environment.LoadSampler() as sampler:
                for repeat in range(repeats):
                    _check(budget, f"quantum counting_qubits={m} repeat {repeat}")
                    start = time.perf_counter()
                    repeat_seed = None if seed is None else seed + m * repeats + repeat
                    result = qae.estimate(m, domain_qubits, shots=shots, seed=repeat_seed)
                    elapsed = time.perf_counter() - start
                    outcome = {**result, "correct_digits": correct_digits(result["pi_estimate"])}
                    samples.append(elapsed)
                    outcomes.append(outcome)
            after = environment.gpu_memory_used_mib()
            row = {
                "method": "qae-cudaq",
                "target": target,
                "outcomes": outcomes,
                "gpu_under_load": sampler.summary(),
                **result,
                "correct_digits": correct_digits(result["pi_estimate"]),
                "repeats": repeats,
                "samples_s": samples,
                "vram_used_mib_before": before,
                "vram_used_mib_after": after,
                "quantization": quantization_report(m, result, shots),
                **summarize(samples),
            }
        except (Exception, KeyboardInterrupt) as exc:
            partial_record = {"method": "qae-cudaq", "counting_qubits": m, "samples_s": samples, "outcomes": outcomes}
            raise ConfigurationAborted(partial_record, exc) from exc
        rows.append(row)
    return rows


def quantization_report(counting_qubits: int, result: dict[str, Any], shots: int) -> dict[str, Any]:
    """Compare a QAE result against what closed-form theory predicts.

    Roadmap P1-R3 asks for the quantization to be explained analytically and
    the sampled distribution to be checked, rather than the estimate being
    reported alone. :mod:`quantum.quantization` derives the ideal outcome, the
    error floor and the ideal distribution independently of the simulator, so
    a disagreement here means the run and the theory diverged — which is
    information, not a failure to hide.

    ``total_variation`` is a diagnostic read against ``sampling_tolerance``,
    not a pass/fail: finite shots always leave a positive distance. The
    validator recomputes this block from the row's own outcome and counts.
    """
    from quantum import quantization

    return quantization.report(counting_qubits, result["outcome"], result["counts"], shots)


def build_run_file(
    classical_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    power_profile: str,
    shots: int,
    domain_qubits: int,
    hardware_id: str,
    env: dict[str, Any],
    seed: int | None = None,
    status: dict[str, Any] | None = None,
    time_budget_s: float | None = None,
) -> dict[str, Any]:
    """Assemble the contract-conforming run file, complete or aborted.

    ``status`` comes from :func:`run_status`; ``configuration`` records the
    sweeps actually completed and ``status.planned`` the sweeps declared, so an
    aborted record shows exactly how far it got.
    """
    quantum_target = env.get("execution", {}).get("quantum", {}).get("target")
    return {
        "schema": run_file.CURRENT_SCHEMA,
        "synthetic": False,
        "protocol": {"declaration": protocol.declaration(), "digest": protocol.digest()},
        "provenance": env.get("source"),
        "execution": env.get("execution"),
        "configuration": {
            "classical_term_counts": [row["n_terms"] for row in classical_rows],
            "counting_qubits": [row["counting_qubits"] for row in quantum_rows],
            "seed": seed,
            "seed_schedule": "base + counting_qubits * repeats + repeat_index; warmup unseeded",
            "outcome_summary": "last timed repeat; every repeat is retained",
            "timing_boundary": "classical partial_sum wrapper; quantum estimate wrapper; warmup discarded",
            "phase_attribution": (
                "End-to-end only. Per-phase attribution is available from "
                "classical.cuda_kernel.time_phases and is not part of this sweep."
            ),
            "nvrtc_options": ["--std=c++17"],
        },
        "series": "ramanujan-1914",
        "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware_id": hardware_id,
        "question": RESEARCH_QUESTION,
        "hypothesis": HYPOTHESIS,
        "variables": {
            "classical": "n_terms — number of series terms summed on the GPU",
            "quantum": "counting_qubits (m) — precision bits, setting both circuit width and 2^m-1 Grover applications",
        },
        "controls": {
            "domain_qubits": domain_qubits,
            "shots": shots,
            "power_profile": power_profile,
            "threads_per_block": 256,
            "quantum_target": quantum_rows[0]["target"] if quantum_rows else quantum_target,
            "time_budget_s": time_budget_s,
            "precision": {"classical": "fp64", "quantum": env.get("execution", {}).get("quantum", {}).get("precision")},
        },
        "statistical_treatment": STATISTICAL_TREATMENT,
        "limitations": list(LIMITATIONS),
        # Snapshotted before timing began; per-row gpu_under_load carries the
        # clocks and temperature each measurement actually ran at.
        "environment": env,
        "status": status,
        "runs": classical_rows + quantum_rows,
    }


def run_status(
    planned_term_counts: tuple[int, ...],
    planned_counting_qubits: tuple[int, ...],
    budget: Budget,
    aborted: ConfigurationAborted | None,
) -> dict[str, Any]:
    """Describe how the run ended, for the archive's ``status`` block."""
    abort = None
    if aborted is not None:
        cause = aborted.cause
        if isinstance(cause, BudgetExceeded):
            reason = "budget"
        elif isinstance(cause, KeyboardInterrupt):
            reason = "interrupted"
        else:
            reason = "error"
        abort = {
            "reason": reason,
            "exception_type": type(cause).__name__,
            "detail": str(cause) or type(cause).__name__,
            "incomplete_configuration": aborted.partial,
        }
    return {
        "state": "complete" if aborted is None else "aborted",
        "planned": {
            "classical_term_counts": list(planned_term_counts),
            "counting_qubits": list(planned_counting_qubits),
        },
        "elapsed_s": budget.elapsed(),
        "abort": abort,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Command-line interface for the harness."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="path to write the run file")
    parser.add_argument(
        "--power-profile",
        required=True,
        help="declared vendor power/thermal mode (e.g. turbo, performance, silent) — a control, recorded verbatim",
    )
    parser.add_argument(
        "--time-budget-s",
        type=float,
        required=True,
        help="declared total wall-clock budget for both arms, in seconds — a control; exceeding it aborts the run",
    )
    parser.add_argument("--hardware-id", default=None, help="short id for this machine")
    parser.add_argument(
        "--seed", type=int, default=None, help="optional positive CUDA-Q seed; unsupported targets reject it"
    )
    parser.add_argument("--repeats", type=int, default=5, help="timed repeats per configuration")
    parser.add_argument("--shots", type=int, default=2000, help="shots per QAE circuit")
    parser.add_argument("--domain-qubits", type=int, default=DOMAIN_QUBITS)
    parser.add_argument(
        "--max-counting-qubits",
        type=int,
        default=max(QUANTUM_COUNTING_QUBITS),
        help="cap the quantum sweep; each extra bit doubles both memory and Grover count",
    )
    return parser.parse_args(argv)


#: Exit code for a run that stopped on its declared budget and archived what it
#: completed. Errors and interrupts re-raise their original exception instead.
EXIT_BUDGET_EXHAUSTED = 3


def main(argv: list[str] | None = None) -> int:
    """Run both arms and write the run file. Returns a process exit code.

    Every stop after measurement begins — budget, error or interrupt — still
    writes an ``aborted`` archive of the completed work before the original
    exception is re-raised (or, for the budget, exit code 3 is returned).
    """
    args = parse_args(argv)

    # Fail before GPU initialization/work; exclusive creation also protects
    # against a competing writer appearing after this early check.
    if args.out.exists():
        raise FileExistsError(args.out)
    for key in ("repeats", "shots", "domain_qubits"):
        run_file.integer(getattr(args, key), key)
    run_file.integer(args.max_counting_qubits, "max_counting_qubits", 2)
    run_file.text(args.power_profile, "power_profile")
    run_file.number(args.time_budget_s, "time_budget_s", 0)
    run_file.require(args.time_budget_s > 0, "time_budget_s must be positive")
    if args.hardware_id is not None:
        run_file.text(args.hardware_id, "hardware_id")
    if args.seed is not None:
        run_file.integer(args.seed, "seed")
        run_file.require(args.seed + 17 * args.repeats < 2**32, "seed schedule exceeds 32-bit range")

    from quantum import backend

    target = backend.select_target()
    print(f"CUDA-Q target: {target}")

    execution = provenance.execution()
    if execution["quantum"]["target"] != target:
        raise ValueError("selected target disagrees with CUDA-Q runtime")
    environment.GPU_SELECTOR = execution["classical"]["pci_bus_id"]
    env = environment.collect(args.power_profile)
    run_file.require(isinstance(env["gpu"], dict) and bool(env["gpu"].get("uuid")), "selected GPU UUID unavailable")
    execution["classical"]["uuid"] = env["gpu"]["uuid"]
    execution["quantum"]["uuid"] = None if target == "qpp-cpu" else env["gpu"]["uuid"]
    env.update(source=provenance.source(), packages=provenance.packages(), execution=execution)
    if args.seed is not None and target == "tensornet":
        raise ValueError("tensornet protocol does not support seeded sampling")
    counting = tuple(m for m in QUANTUM_COUNTING_QUBITS if m <= args.max_counting_qubits)

    budget = Budget(args.time_budget_s)
    classical_rows: list[dict[str, Any]] = []
    quantum_rows: list[dict[str, Any]] = []
    aborted: ConfigurationAborted | None = None
    # Installed after target selection has imported CUDA-Q, so it replaces the
    # runtime's own SIGINT handler (see Budget.request_stop).
    previous_handler = signal.signal(signal.SIGINT, budget.request_stop)
    try:
        print(f"classical arm: {len(CLASSICAL_TERM_COUNTS)} configurations")
        classical_rows = measure_classical(CLASSICAL_TERM_COUNTS, args.repeats, budget=budget, rows=classical_rows)

        print(f"quantum arm: {len(counting)} configurations")
        quantum_rows = measure_quantum(
            counting,
            args.domain_qubits,
            args.shots,
            args.repeats,
            target,
            args.seed,
            budget=budget,
            rows=quantum_rows,
        )
    except ConfigurationAborted as exc:
        aborted = exc
        print(f"run aborted: {exc}; archiving the completed configurations")
    finally:
        signal.signal(signal.SIGINT, previous_handler)

    payload = build_run_file(
        classical_rows,
        quantum_rows,
        power_profile=args.power_profile,
        shots=args.shots,
        domain_qubits=args.domain_qubits,
        hardware_id=args.hardware_id or env["gpu"]["uuid"],
        env=env,
        seed=args.seed,
        status=run_status(CLASSICAL_TERM_COUNTS, counting, budget, aborted),
        time_budget_s=args.time_budget_s,
    )

    try:
        write_archive(payload, args.out)
    except BaseException as write_error:
        if aborted is None:
            raise
        # Losing the archive must not hide why the run stopped.
        raise write_error from aborted.cause
    print(f"wrote {args.out} ({len(payload['runs'])} rows, {payload['status']['state']})")
    if aborted is None:
        return 0
    if isinstance(aborted.cause, BudgetExceeded):
        return EXIT_BUDGET_EXHAUSTED
    raise aborted.cause


def write_archive(payload: dict[str, Any], out: Path) -> None:
    """Validate and exclusively create the run file; never overwrite evidence."""
    if provenance.source() != payload["environment"]["source"]:
        raise ValueError("source changed during measurement; no archive written")
    run_file.validate(payload, allow_legacy=False, allow_incomplete=True)
    encoded = (json.dumps(payload, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with archive.create_outputs([out]) as streams:
        streams[0].write(encoded)


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage-1 crossover benchmark: hand-written CUDA kernel vs QAE, same silicon.

Emits a run file conforming to the research-standards contract in
``docs/handbook/research-standards.md`` — the declared question, hypothesis,
variables, controls, hardware, software versions, statistical treatment, raw
per-repeat data, and limitations all travel with the numbers, in one file.

    python -m benchmarks.harness --power-profile turbo --out benchmarks/runs/<name>.json

Both arms are timed the same way: a warm-up call absorbs compilation and
context setup, then every repeat is recorded individually. Summaries are
derived from the samples; the samples themselves are never discarded, because
the narrator (ADR 003) and any later statistical treatment need the raw data,
not somebody's mean.
"""

import argparse
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

from benchmarks import archive, environment, provenance, run_file

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
    "summaries are the mean, the minimum, and the sample standard deviation over "
    "those repeats. No outlier rejection is applied; the raw samples are retained in "
    "the run file so any later treatment can be applied and audited after the fact."
)


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
    """Mean/min/stdev over timing samples, keeping the samples themselves."""
    return {
        "mean_s": statistics.fmean(samples),
        "min_s": min(samples),
        "stdev_s": statistics.stdev(samples) if len(samples) > 1 else 0.0,
    }


def measure_classical(term_counts: tuple[int, ...], repeats: int) -> list[dict[str, Any]]:
    """Time the CUDA kernel across ``term_counts``."""
    from classical import cuda_kernel

    rows: list[dict[str, Any]] = []
    for n_terms in term_counts:
        with environment.LoadSampler() as sampler:
            timing = cuda_kernel.time_partial_sum(n_terms, repeats=repeats)
        outcomes = []
        for partial in timing["partial_sums"]:
            estimate = 1.0 / ((2.0 * math.sqrt(2.0) / 9801.0) * partial)
            outcomes.append(
                {
                    "partial_sum": partial,
                    "pi_estimate": estimate,
                    "abs_error": abs(estimate - math.pi),
                    "correct_digits": correct_digits(estimate),
                }
            )
        estimate = outcomes[-1]["pi_estimate"]
        rows.append(
            {
                "method": "classical-cuda",
                "gpu_under_load": sampler.summary(),
                "n_terms": n_terms,
                "outcomes": outcomes,
                "pi_estimate": estimate,
                "abs_error": abs(estimate - math.pi),
                "correct_digits": correct_digits(estimate),
                "repeats": repeats,
                "samples_s": timing["samples_s"],
                **summarize(timing["samples_s"]),
            }
        )
    return rows


def measure_quantum(
    counting_qubits: tuple[int, ...],
    domain_qubits: int,
    shots: int,
    repeats: int,
    target: str,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Time QAE across counting-register sizes on the selected CUDA-Q target."""
    from quantum import qae

    rows: list[dict[str, Any]] = []
    for m in counting_qubits:
        qae.estimate(m, domain_qubits, shots=shots)  # warm-up: JIT + context

        before = environment.gpu_memory_used_mib()
        samples: list[float] = []
        result: dict[str, Any] = {}
        outcomes: list[dict[str, Any]] = []
        with environment.LoadSampler() as sampler:
            for repeat in range(repeats):
                start = time.perf_counter()
                repeat_seed = None if seed is None else seed + m * repeats + repeat
                result = qae.estimate(m, domain_qubits, shots=shots, seed=repeat_seed)
                samples.append(time.perf_counter() - start)
                outcomes.append({**result, "correct_digits": correct_digits(result["pi_estimate"])})
        after = environment.gpu_memory_used_mib()

        rows.append(
            {
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
                **summarize(samples),
            }
        )
    return rows


def build_run_file(
    classical_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
    power_profile: str,
    shots: int,
    domain_qubits: int,
    hardware_id: str,
    env: dict[str, Any],
    seed: int | None = None,
) -> dict[str, Any]:
    """Assemble the complete, contract-conforming run file."""
    return {
        "schema": run_file.CURRENT_SCHEMA,
        "synthetic": False,
        "provenance": env.get("source"),
        "execution": env.get("execution"),
        "configuration": {
            "classical_term_counts": [row["n_terms"] for row in classical_rows],
            "counting_qubits": [row["counting_qubits"] for row in quantum_rows],
            "seed": seed,
            "seed_schedule": "base + counting_qubits * repeats + repeat_index; warmup unseeded",
            "outcome_summary": "last timed repeat; every repeat is retained",
            "timing_boundary": "classical partial_sum wrapper; quantum estimate wrapper; warmup discarded",
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
            "quantum_target": quantum_rows[0]["target"] if quantum_rows else None,
            "precision": {"classical": "fp64", "quantum": env.get("execution", {}).get("quantum", {}).get("precision")},
        },
        "statistical_treatment": STATISTICAL_TREATMENT,
        "limitations": list(LIMITATIONS),
        # Snapshotted before timing began; per-row gpu_under_load carries the
        # clocks and temperature each measurement actually ran at.
        "environment": env,
        "runs": classical_rows + quantum_rows,
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


def main(argv: list[str] | None = None) -> int:
    """Run both arms and write the run file. Returns a process exit code."""
    args = parse_args(argv)

    # Fail before GPU initialization/work; exclusive creation also protects
    # against a competing writer appearing after this early check.
    if args.out.exists():
        raise FileExistsError(args.out)
    for key in ("repeats", "shots", "domain_qubits"):
        run_file.integer(getattr(args, key), key)
    run_file.integer(args.max_counting_qubits, "max_counting_qubits", 2)
    run_file.text(args.power_profile, "power_profile")
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

    print(f"classical arm: {len(CLASSICAL_TERM_COUNTS)} configurations")
    classical_rows = measure_classical(CLASSICAL_TERM_COUNTS, args.repeats)

    print(f"quantum arm: {len(counting)} configurations")
    quantum_rows = measure_quantum(counting, args.domain_qubits, args.shots, args.repeats, target, args.seed)

    payload = build_run_file(
        classical_rows,
        quantum_rows,
        power_profile=args.power_profile,
        shots=args.shots,
        domain_qubits=args.domain_qubits,
        hardware_id=args.hardware_id or env["gpu"]["uuid"],
        env=env,
        seed=args.seed,
    )

    if provenance.source() != env["source"]:
        raise ValueError("source changed during measurement; no archive written")
    run_file.validate(payload, allow_legacy=False)
    encoded = (json.dumps(payload, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with archive.create_outputs([args.out]) as streams:
        streams[0].write(encoded)
    print(f"wrote {args.out} ({len(payload['runs'])} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

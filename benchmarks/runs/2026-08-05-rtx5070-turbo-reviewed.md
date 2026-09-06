# Reviewed interpretation of the 2026-08-05 RTX 5070 run

Review date: 2026-09-06. Source: [unchanged measured JSON](2026-08-05-rtx5070-turbo.json).
This supersedes the interpretation in the [original narrator draft](2026-08-05-rtx5070-turbo-findings.md).
No new GPU run was performed by this review.

## What was recorded

27 rows: 12 classical configurations and 15 QAE configurations; five timing
repeats per row, 4000 shots per QAE estimate, turbo profile. Timing samples
are retained, but each row keeps only the final numerical outcome; per-repeat
QAE counts and seeds are absent. The archive does not record a source revision.

| Configuration | Mean wall time | Absolute error against `math.pi` |
| --- | --- | --- |
| Classical n=1 | 2.675 ms | 7.64235e-8 |
| Classical n=2 | 2.714 ms | 4.44089e-16 |
| Classical n=3 | 2.818 ms | 0 at Python float precision |
| QAE m=10 | 0.441 s | 3.11618e-5 |
| QAE m=16 | 9.290 s | 3.11618e-5 |

The harness uses relative-error digits against floating-point `math.pi`;
the exact-series helper uses an absolute-error metric. Zero float error does
not prove equality to transcendental π. The 2-term row has 15.85 relative-error
digits, not exactly 16 independently verified decimal digits.

## Supported conclusions and limits

No crossing was observed in the tested configurations. The selected n=2/m=10
wall-time ratio is about 162.5× at different accuracies; it is not a fair
matched-accuracy speedup or proof that no crossover can exist elsewhere.

The QAE circuit encodes known `math.pi / 4`, so it studies simulation and
estimation behavior rather than independently discovering π. The ideal nearest
dyadic estimate is unchanged from m=10 through m=17. Analytic estimates improve
at m=18 and m=20; those are calculations, not additional measured GPU rows.
Shot noise and the estimator's outcome selection also belong in the analysis.

QAE sampled utilization peaks of 12–20% do not prove a dispatch bottleneck.
The classical 95% peak occurs at n=16384; the n=2 row records 2%, so combining
95% with the fastest high-accuracy row is misleading. `nvidia-smi` utilization
measures the fraction of a sampling interval during which kernels execute,
not arithmetic saturation; see [NVIDIA's definition](https://docs.nvidia.com/deploy/nvidia-smi/index.html).
Profiling is needed to assign causes or predict H100 speed.

Wall times include wrapper work, allocation and related overhead; a warmup
does not isolate kernel-only execution. The classical running-product work
grows quadratically with the maximum term count even after useful fp64 accuracy
saturates. QAE gate counts grow exponentially with counting bits, but bits
are not decimal digits and finite timing ratios need not be exactly two.

Before/after device memory values are not process-specific peak allocation.
The largest circuit has 19 qubits: 4 MiB bare fp32 statevector storage, far
below the GPU's capacity. Neither a measured usable qubit ceiling nor a
datacenter scaling claim follows from this archive.

The hypothesis constant and archive first appear together in reachable history;
that does not substantiate pre-run commitment. Treat this run as exploratory.
Follow [Phase 1 repair gates](../../docs/roadmap.md#phase-1--the-first-real-result)
before collecting a prospective repeat. Preserve this archive and both writeups.

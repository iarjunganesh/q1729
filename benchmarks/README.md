# benchmarks/

The stage-1 crossover benchmark: a hand-written CUDA C++ kernel and a
CUDA-Q Quantum Amplitude Estimation circuit, measured against each other on
the same GPU. This directory holds both the tooling and the **real measured
results** that roadmap [Phase 1](../docs/roadmap.md#phase-1--the-first-real-result)
produced.

## Contents

| Path | What it is |
| --- | --- |
| `harness.py` | Runs both arms and writes a contract-conforming run file |
| `environment.py` | Captures hardware, software versions, and GPU load *during* the run |
| `plot.py` | Renders the crossover figure in light and dark themes |
| `runs/` | Measured run files and their narrated writeups |
| `plots/` | Generated figures — edit `plot.py`, never the SVGs |

## The measured runs

| Run file | Hardware | Date | Notes |
| --- | --- | --- | --- |
| [`2026-08-05-rtx5070-turbo.json`](runs/2026-08-05-rtx5070-turbo.json) | RTX 5070 Laptop GPU 8GB | 2026-08-05 | Power profile `turbo`, 5 repeats/config, 4000 shots. Narrated writeup: [`…-findings.md`](runs/2026-08-05-rtx5070-turbo-findings.md) |

`data/sample_run.json` is **not** here and never will be: it is synthetic
demonstration data, labeled `"synthetic": true` in the file itself, and
`plot.py` raises rather than plotting it.

## What the first run found

- **No crossover on this silicon.** The classical kernel reaches double
  precision's 16-digit ceiling in ~2.6 ms with 2 series terms. Simulated QAE
  reaches 5.0 digits, and takes 0.44 s to do it.
- **The quantum arm never saturates the GPU** — 12–20% utilization against
  the classical kernel's 95%. Its wall time is per-gate dispatch overhead, not
  statevector arithmetic. That reframes the datacenter question: an H100 would
  not move these numbers much, because the device was never the bottleneck.
  Wider circuits would.
- **Accuracy plateaus at m = 10 while cost keeps doubling.** The eigenphase
  0.34668271 lies within 3.0 × 10⁻⁶ of the 10-bit dyadic 355/1024, so further
  counting qubits correctly return zeros. Every quantum row carries
  `phase_error` and `phase_resolution`; comparing them shows which regime the
  row is in. A different target amplitude would move this plateau — it is a
  property of estimating π/4, not a defect in the circuit.

## Reproducing

The power profile is a **required** argument, not a default: on a laptop the
vendor power/thermal mode changes every timing in the output, so it is a
declared control (see [research standards](../docs/handbook/research-standards.md)).

```bash
# WSL2, with the GPU stack installed (requirements-gpu.txt)
make benchmark POWER_PROFILE=turbo
make plot RUN=benchmarks/runs/<file>.json
```

If your numbers disagree with the archived run beyond its recorded standard
deviation, that disagreement is a result — record it alongside rather than
re-running until it agrees. Never edit a run file's numbers by hand.

## Adding a run from other hardware

The run-file schema is hardware-agnostic; `hardware_id` and the `environment`
block are what let curves from different machines land in one analysis. Open
an issue with the [benchmark submission template](../.github/ISSUE_TEMPLATE/benchmark_submission.yml).

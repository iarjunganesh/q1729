# ADR 001 — CUDA-Q as the quantum programming platform

**Status:** Accepted — July 2026

## Context

The project went through two earlier framings before settling:

1. **QRM (PennyLane VQE)** — a variational circuit minimizing a cost against a
   Ramanujan-derived target constant. The current `scripts/` code is this era.
2. **ramanujan-cuda-quantum (Qiskit + cuQuantum)** — a π benchmark plan using
   Qiskit circuits simulated through raw cuStateVec calls.

Both put the framework between the code and the NVIDIA simulation stack. The
project's whole premise is squeezing research-grade results out of one consumer
GPU, so the platform should be the one NVIDIA builds *for* that stack, not one
that adapts to it.

## Decision

Standardize on **CUDA-Q** (kernels, sampling, observables) with **CUDA-QX**
extensions (Solvers, QEC) and cuQuantum's `nvidia` / `tensornet` backends.
Stage 3 (Ramanujan-graph qLDPC codes) depends on CUDA-Q QEC specifically —
neither PennyLane nor Qiskit has an equivalent GPU-decoder path.

The legacy PennyLane scaffold (`scripts/`, PennyLane requirements) was cut
over on 2026-07-10 rather than kept runnable alongside: maintaining two stacks
meant every piece of hygiene work (tests, CI, deps) invested in code already
marked for deletion. The stage-1 layout (`classical/` / `quantum/`, with
`analysis/` arriving with the first results) replaces it.

## Consequences

- CUDA-Q is Linux-only → forces the WSL2 runtime decision (ADR 002)
- Qiskit-era planning docs and the PennyLane code/deps were deleted rather
  than maintained alongside
- `classical/ramanujan_series.py` (exact SymPy) is the ground truth the
  stage-1 CUDA kernel benchmarks against; `quantum/backend.py` owns CUDA-Q
  target selection

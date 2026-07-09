# ADR 002 — WSL2 (or NGC container) as the GPU runtime

**Status:** Accepted — July 2026

## Context

Development happens on a Windows 11 machine (RTX 5070 8GB, CUDA 13.x). The GPU
quantum-simulation stack does not meet Windows halfway:

- **CUDA-Q** ships Linux-only (pip wheels and the
  `nvcr.io/nvidia/quantum/cuda-quantum` NGC container)
- **cuQuantum / cuStateVec** and CuPy's CUDA 13 stack have no reliable native
  Windows path; the earlier conda-on-Windows recipe (PennyLane era) proved
  fragile and was abandoned

## Decision

All CUDA-Q runs happen inside **WSL2** (or the NGC container). The Windows
host is for editing, the pure-math classical reference, unit tests, and
CI-equivalent checks. `requirements-gpu.txt` is a WSL2-only install; even
without GPU passthrough, cudaq's `qpp-cpu` target runs there and in CI.

## Consequences

- `requirements.txt` must stay installable on a CPU-only host — the CUDA-Q
  stack lives exclusively in `requirements-gpu.txt`
- `quantum/backend.py` must degrade gracefully: report unavailability on
  Windows, fall through `nvidia` → `tensornet` → `qpp-cpu` where cudaq exists
- CI installs cudaq and runs `tests/integration` on `qpp-cpu`; GPU benchmark
  numbers are produced manually in WSL2 and committed as results, not
  regenerated in CI

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

## 2026-09-06 audit amendment

WSL2 remains the chosen Windows GPU workflow, but the configured disk could not be attached in this audit. Historical success is not fresh verification. Native Windows wheel availability for individual packages does not verify the complete repository GPU path. See ../setup.md for separate host environments and current target order.

## 2026-09-23 amendment — one interpreter line, named distro

The 2026-09-06 "could not attach" finding had a mundane cause. The distro that
was rebuilt that day is registered as `Ubuntu` (Ubuntu 26.04), but the WSL
default remained a stale `Ubuntu-22.04` registration whose `ext4.vhdx` no
longer exists. A bare `wsl -e` targets the default and fails with
`HCS/ERROR_PATH_NOT_FOUND`; `wsl -d Ubuntu` works. Documented commands now
name the distro explicitly. Removing the stale registration is left to the
owner.

The owner also decided that the repository uses **one Python line on every
host: 3.14**. CUDA-Q 0.16.0.post1 publishes cp314 Linux wheels (paired with
CuPy 14.x), so the WSL2 venv was rebuilt on uv-managed Python 3.14.7 to match
the Windows `.venv` and CI. `requires-python` is now `>=3.14`, and Ruff/mypy
target 3.14. The WSL2 GPU suite passed on it: 347 passed, 1 skipped, 100.00%
coverage. The decision to use WSL2 for the GPU path is unchanged.

# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] — 2026-07-10 — Hybrid cloud: NIM/Nemotron narrator + datacenter benchmark axis

### Added

- **NIM/Nemotron findings narrator (ADR 003)** — `analysis/narrator.py` sends benchmark run files to a Nemotron model via the NVIDIA NIM chat-completions API and returns a findings draft; every number comes from the run file, never from the model. `make narrate` demonstrates it on `data/sample_run.json` (clearly-labeled synthetic data defining the run-file schema, including the `hardware` field that lets consumer and datacenter results land in one analysis). Degrades exactly like the cudaq path: no `NVIDIA_API_KEY`, no narrator, nothing else breaks
- **Cloud-GPU benchmark axis (ADR 003)** — the stage-1 benchmark now targets both the local RTX 5070 and a rented H100/multi-GPU box; same CUDA-Q code, second `hardware` entry in the run files. README architecture, roadmap, and hardware sections widened accordingly
- **First secret, handled properly**: `.env.example` (placeholders), `.env` gitignored, SECURITY.md secrets-handling section
- **10 narrator unit tests** (httpx mocked at the module boundary: prompt assembly carries numbers verbatim, env overrides, missing-key and HTTP-error paths) + **1 live NIM integration test** (skips without a key) — coverage stays at 100% measured
- `main.py` status check now also reports NIM narrator availability

### Fixed

- **GPU-less hosts crashed instead of falling back.** On a machine with no CUDA driver (e.g. the CI runner), `cudaq.set_target("nvidia")` does not raise a catchable error — it hard-aborts the entire Python process. `select_target` now checks `cudaq.num_available_gpus()` and skips GPU targets up front (`GPU_TARGETS`), which is what lets the integration suite run on `qpp-cpu` in CI. Caught by CI's first run; invisible locally because WSL2 sees the RTX 5070
- NIM default model updated to `nvidia/nemotron-3-super-120b-a12b` — the previous default (`llama-3.1-nemotron-70b-instruct`) is listed by `/v1/models` but 404s on invoke (retired for this account); `.env.example` now warns that catalog listing ≠ invocability
- `python -m analysis.narrator` no longer crashes on Windows consoles (cp1252) when the model's output contains non-Latin-1 typography — stdout is reconfigured to UTF-8

### Changed

- `httpx` added to core requirements (CPU-safe everywhere); `Makefile` gains `narrate` and fixes `gpu-check` to the new `python -m quantum.backend` diagnostic

## [0.1.0] — 2026-07-10 — Stage-1 cutover: CUDA-Q structure, sibling-repo hygiene

### Added

- **Stage-1 layout** per the README roadmap: `classical/ramanujan_series.py` (exact SymPy implementation of the 1914 1/π series — terms are exact rationals, the ground truth the CUDA kernel benchmarks against) and `quantum/backend.py` (CUDA-Q target selection `nvidia` → `tensornet` → `qpp-cpu` with graceful degradation on hosts without cudaq; doubles as an environment diagnostic via `python -m quantum.backend`)
- **Test suite**: 16 unit tests (series math exact-value and convergence checks; backend fall-through logic against a fake `cudaq` module) + 2 integration tests that run a real Bell-pair simulation on the selected CUDA-Q target, skipping cleanly where cudaq is absent. Verified 2026-07-10 on WSL2: cudaq 0.15 selects the **`nvidia`** target (RTX 5070 passthrough works) and the whole suite passes at **100% measured coverage** (CI gate 95%; the only exclusion is the JIT-compiled kernel body, proven by the integration test)
- **Repo hygiene to sibling-repo standard** (`continuum`, `bankers-wrapped`): `Makefile` (source of truth for commands), `pyproject.toml` (ruff / pytest / coverage config), CI quality gate (`ruff` + pytest with cudaq's `qpp-cpu` target + 90% coverage gate + Codecov), tag-driven release workflow, `CLAUDE.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, ADRs (`docs/adr/001` CUDA-Q over PennyLane/Qiskit, `002` WSL2 runtime)

### Removed

- **The legacy PennyLane scaffold** (`scripts/quantum_engine.py`, `scripts/math_logic.py`, `scripts/gpu_check.py`, PennyLane deps) — the README marked it "pending replacement"; maintaining it meant investing hygiene work in code already slated for deletion (ADR 001)
- **Four stale planning docs** (`docs/gpu_setup.md`, `docs/qrm.md`, `docs/ramanujan-cuda-quantum.md`, `docs/ramanujan-cuda-quantum-summary.md`) — QRM/VQE and Qiskit-era brainstorms superseded by the README roadmap; the decisions they recorded live on as ADRs

### Changed

- `requirements.txt` is now CPU-safe everywhere (sympy/numpy + dev tools); the CUDA-Q stack moved to `requirements-gpu.txt` (WSL2-only, previously duplicated cupy across both files)
- `main.py` status check now reports the classical series sanity plus CUDA-Q availability, and is required to run on hosts with or without cudaq

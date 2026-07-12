# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-07-12 — Initial release: CUDA-Q stage-1 skeleton, NIM narrator, hybrid-cloud scaffolding

First tagged release. The repo is an honest stage-1 skeleton — exact classical
ground truth, CUDA-Q target selection, and an AI findings narrator are in place;
the hand-written CUDA kernel, the QAE circuit, and the first measured benchmark
run are roadmap **Phase 1** (see `docs/roadmap.md`).

### Added

- **Exact classical ground truth** — `classical/ramanujan_series.py`: the 1914 1/π series as exact SymPy rationals (not floats), the reference the future CUDA kernel will be benchmarked against.
- **CUDA-Q target selection** — `quantum/backend.py`: `select_target()` walks `nvidia-mgpu` → `nvidia` → `tensornet` → `qpp-cpu`, degrades gracefully on hosts without cudaq, and doubles as an environment diagnostic (`python -m quantum.backend`). GPU targets are skipped up front via `cudaq.num_available_gpus()` because `cudaq.set_target()` hard-aborts (not raises) on a driverless host — this is what lets CI run the integration suite on `qpp-cpu`. `nvidia-mgpu` is gated on 2+ visible GPUs and uses the modern `cudaq.set_target("nvidia", option="mgpu,fp32")` call; the single-GPU MPI-plugin failure is a normal catchable `RuntimeError` (the multi-GPU success path is untested — no such hardware). Verified 2026-07-10 on WSL2: cudaq 0.15 selects `nvidia` on the RTX 5070.
- **NIM/Nemotron findings narrator (ADR 003)** — `analysis/narrator.py` sends benchmark run files to a Nemotron model via the NVIDIA NIM chat-completions API and returns a findings draft or, given a research question, a structured Observation / Interpretation / Suggested-next-experiment answer. Every number comes from the run file, never the model. Optional: no `NVIDIA_API_KEY`, no narrator, nothing else breaks. `main.py`'s status check reports its availability.
- **Benchmark run-file schema** — `data/sample_run.json` (clearly-labeled synthetic demo data) defines the schema, including the `hardware` field that lets consumer-RTX and datacenter-H100 results land in one analysis.
- **Community benchmark submission template** — `.github/ISSUE_TEMPLATE/benchmark_submission.yml` (GPU/VRAM, driver/CUDA version, CUDA-Q backend, environment, qubit ceiling, run file, notes).
- **Documentation** — `docs/roadmap.md` (single vision + evidence-sequenced roadmap, absorbing the former Blueprint v1.0), `docs/nvidia-access.md`, `docs/onboarding.md`, `docs/setup.md`, `docs/adr/README.md`, and a Test Coverage section in `CONTRIBUTING.md` — all built from commands actually run on this machine, not assumed behavior. ADRs 001 (CUDA-Q over PennyLane/Qiskit), 002 (WSL2 runtime), 003 (hybrid cloud + NIM).
- **Tests** — unit (series exact-value and convergence checks; backend fall-through against a fake `cudaq` module; narrator mocked at the httpx boundary, verifying run-file numbers travel verbatim) + integration (a real Bell-pair simulation on the selected CUDA-Q target; a live NIM smoke test) — each skips cleanly where its backend is absent. ~100% measured coverage; CI gates at 95% (the only exclusion is the JIT-compiled kernel body, exercised by an integration test).
- **Repo hygiene to sibling-repo standard** (`continuum`, `bankers-wrapped`): `Makefile` (source of truth for commands), `pyproject.toml` (ruff / pytest / coverage config), CI quality gate (ruff + pytest on cudaq's `qpp-cpu` target + Codecov), tag-driven release workflow, `CLAUDE.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, and secret handling (`.env` gitignored, `.env.example` documents `NVIDIA_API_KEY` / `NIM_BASE_URL` / `NIM_MODEL`).

### Removed

- **Legacy PennyLane scaffold** (`scripts/quantum_engine.py`, `scripts/math_logic.py`, `scripts/gpu_check.py`, PennyLane deps) — superseded by the CUDA-Q structure; maintaining code slated for deletion was wasted effort (ADR 001).
- **Stale planning docs** (`docs/gpu_setup.md`, `docs/qrm.md`, `docs/ramanujan-cuda-quantum.md`, `docs/ramanujan-cuda-quantum-summary.md`) — QRM/VQE and Qiskit-era brainstorms superseded by the roadmap; the decisions they recorded live on as ADRs.

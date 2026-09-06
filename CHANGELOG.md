# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Documentation

- Audited all 26 authored Markdown files (3379 original lines); reconciled live status/setup, added evidence-first phase gates and ADR 007, and separated reviewed findings from the preserved narrator draft. Historical ADR/session/release records and measured JSON remain intact. Code repair gates remain open; see `docs/markdown-audit-2026-09-06.md`.

- Recorded a repository-wide audit in `docs/sessions.md`: checked the current Windows quality gates, archived timing summaries, public CI/release state, and Phase 2 construction feasibility. The audit identified open evidence, archive-safety, validation, and documentation issues; no implementation or measured artifacts were changed. Fresh WSL2/GPU verification was unavailable because the configured virtual disk could not be attached.

### Added

- **[ADR 006](docs/adr/006-rocm-as-phase-4-second-backend.md)** — ROCm/MI300 is adopted as the designated roadmap **Phase 4** second backend, and explicitly stays behind Phases 2 and 3. Scouting established that the classical arm is already portable (`ramanujan_kernel.cu` uses no NVIDIA-specific intrinsics; `cupy.RawModule` has a hipRTC path) while the quantum arm **cannot** cross vendors inside CUDA-Q, whose GPU targets are all cuQuantum-based. An AMD run is therefore a **portability result, not a crossover point** — the invalid artifact to avoid is plotting a GPU classical arm against a `qpp-cpu` quantum fallback on one axis. Adding a second quantum simulator (Qiskit Aer on ROCm, qsim-HIP) to work around that requires its own ADR *and* a same-GPU simulator-vs-simulator control run, so the confound is measured before it is tolerated. No AMD hardware was rented and no timing on AMD silicon is claimed anywhere.
- **`classical/ramanujan_graph.py` — roadmap Phase 2 begins.** The Lubotzky-Phillips-Sarnak construction of Ramanujan expander graphs: Jacobi four-square generators, a square root of −1 mod `q`, and a breadth-first walk of the subgroup they generate inside `PGL(2, q)`. The graph is not asserted to be correct, it is *checked* — the generated subgroup's order is compared against the Legendre symbol `(p|q)`'s prediction (`PSL(2,q)` for a residue, `PGL(2,q)` otherwise), and the Ramanujan property is verified from the actual adjacency spectrum against the Alon-Boppana bound `2*sqrt(k-1)`. Verified 2026-08-05: `PSL(2,13)` (1092 vertices, 18-regular, λ₂ = 7.851 ≤ 8.246) and the canonical bipartite `PGL(2,13)` (2184 vertices, 6-regular, λ₂ = 4.250 ≤ 4.472) are both Ramanujan. The modular construction is exact; its floating-point spectral checks are numerical verification, not an exact spectral proof. It is CPU-only, with no CUDA or benchmark timing. **Phase 2 is started, not delivered** — no qLDPC code, decoder, or second run file exists yet.
- **30 tests for it, at 100% coverage with no `# pragma: no cover`.** The three internal consistency guards (Jacobi's count, generator collision, subgroup order) are each driven to fire by a real test rather than excluded from coverage, per [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md). The collision test uses `(p, q) = (29, 5)`, found by sweeping — violating `q > 2*sqrt(p)` turns out to be necessary but *not* sufficient for a collision, so the guard is a genuine second line of defence rather than dead code behind the validator.
- **A HIP-portability constraint on `classical/ramanujan_kernel.cu`** — recorded in the kernel's own header comment and in `AGENTS.md`, not only in the ADR, so it is visible at the point of edit: no `__shfl_*`, cooperative groups, PTX inline asm, `__nv_*` intrinsics, or device-side CUDA library calls without amending ADR 006. Costs nothing today and keeps a Phase 4 port a shim rather than a rewrite.

## [0.2.0] — 2026-08-05 — Phase 0 + Phase 1: the first real measured crossover

The release the repo was built to produce. `0.1.x` was an honest skeleton with
no `.cu` kernel and no measurement; `0.2.0` has both, plus the standard of
evidence they are held to. Roadmap **Phase 0 is complete** and **Phase 1 is
delivered on the consumer axis** (the optional H100 axis is not).

### Added

- **A real hand-written CUDA C++ kernel** — `classical/ramanujan_kernel.cu`: one Ramanujan series term per thread, shared-memory tree reduction, one partial sum per block. The term is built as an interleaved running product so the accumulator never leaves double's exponent range (computing `(4k)!` first overflows around k = 43). Block partials are summed on the host with `math.fsum` rather than in-kernel `atomicAdd`, so results are bit-identical across runs — a benchmark whose output moves between identical runs is not evidence.
- **`classical/cuda_kernel.py`** — compiles, launches, and times the kernel, degrading cleanly on hosts with no GPU. Includes an NVRTC preload shim: cupy 13.x resolves `libnvrtc` by bare soname and does not look inside the wheel that ships it, so a pip-only CUDA install could not otherwise compile anything.
- **`quantum/qae.py`** — canonical Quantum Amplitude Estimation (Brassard et al.): state preparation `A`, Grover operator `Q = A S₀ A† S_χ`, controlled powers `Q^(2^j)`, inverse QFT. Kernels are defined *inside* a function so importing the module never requires cudaq. The module states plainly what the circuit does **not** prove: recovering π from the outcome already uses π, so this measures the resource cost of estimating a known amplitude, not a computation that discovers π.
- **`benchmarks/`** — `harness.py` (runs both arms, emits a contract-conforming run file), `environment.py` (hardware, versions, and a background GPU load sampler), `plot.py` (theme-aware crossover figures that refuse synthetic input).
- **The first real measured run** — `benchmarks/runs/2026-08-05-rtx5070-turbo.json`, with its narrator-drafted findings and light/dark crossover plots.
- **Roadmap Phase 0 handbook** — `docs/handbook/principles.md` (the six principles, each citing where it is actually enforced) and `docs/handbook/research-standards.md` (the nine-field contract every experiment must satisfy before it runs), linked from the README and the ADR index.
- **[ADR 005](docs/adr/005-cuda-kernel-via-nvrtc.md)** — compile the kernel with NVRTC rather than an `nvcc` build step, so the whole GPU toolchain is `pip install` and CI needs no compiler.
- **New CI gates** — `CLAUDE.md` must stay a bare `@AGENTS.md` import; submission/hackathon directories are rejected; `data/sample_run.json` must stay labeled synthetic; every measured run file must carry all nine research-standards fields. Plus `concurrency` cancellation and `ruff --output-format=github` annotations.
- **`make format`, `make cuda-check`, `make benchmark`, `make plot`** targets. `make benchmark` *requires* `POWER_PROFILE` — on a laptop the vendor power mode changes every timing, so it is a declared control, not a default.

### Changed

- **Run-file schema is now `q1729/run-file/1`** — carries `synthetic`, `hardware_id`, and the full research-standards contract. `data/sample_run.json` was migrated to it and remains explicitly synthetic; `analysis/narrator.py` validates against the same schema, so the narrator reads exactly what the harness writes.
- **Coverage now includes `benchmarks/`** — measured **100% across 156 tests** on WSL2/CI (was 100% across a smaller suite). Windows measures 96% with 28 integration tests skipped, as expected.
- **CI Python moved 3.12 → 3.13**, verified against cudaq's actually-published wheels (`cuda-quantum-cu13` 0.15.1 ships cp311/cp312/cp313 — there is no 3.14 wheel). The WSL2 venv stays on 3.12 because bumping it means installing an interpreter on the owner's machine.
- **Every dependency floor raised to the current stable release**, each verified with a real lookup: sympy 1.14, numpy 2.5, httpx 0.28, pytest 9.1, pytest-cov 7.1, ruff 0.16, mypy 2.3, cudaq 0.15.1, cupy 13.6. Added matplotlib (core, CPU-safe) and `nvidia-cuda-nvrtc` (GPU-only).
- **README rewritten** around the measured result — regrouped badge rows with pinned versions, a findings section with the crossover figure, and a corrected hardware table (the GPU is an RTX 5070 **Laptop** GPU on driver 610.88 / CUDA 13.3, not a desktop 5070 on 610.53).
- **`AGENTS.md` substantially hardened** — a Benchmark integrity section (never hand-edit a run file, never delete a measured run, the hypothesis is committed before the run), a tag-reachability rule, the CUDA-Q kernel-scope constraint, and standing rules that this is not a hackathon project and that no other repository is ever named here.
- **mypy now type-checks `benchmarks/`** too. CUDA-Q's gate vocabulary is declared once under `TYPE_CHECKING` in `quantum/qae.py` instead of suppressing errors on every gate call — kernel parameter annotations are what make mypy check those bodies at all.

### Fixed

- **`v0.1.0` and `v0.1.1` pointed at orphaned commits** left behind by an earlier history rewrite: the GitHub releases existed but the tags were unreachable from any branch. Both were re-pointed at the equivalent `main` commits — verified byte-identical trees — with their original annotation text and dates preserved, and force-pushed. `AGENTS.md` now carries a reachability check to run before pushing any tag.
- **The first two capture attempts recorded misleading GPU state.** The environment block was collected *after* the sweep, reporting idle clocks (847 MHz) for a run that was never throttled. Environment is now snapshotted before timing, and a background sampler records peak clocks, temperature and utilization *during* each configuration. This is what surfaced the finding that the quantum arm never exceeds 20% GPU utilization.

### Notes on the result

Three findings, all reproducible from the archived run file:

1. **No crossover exists on this silicon** — the classical kernel reaches 16 digits in 2.6 ms; simulated QAE reaches 5.0 digits in 0.44 s.
2. **The quantum arm is dispatch-bound, not compute-bound** (12–20% utilization vs the kernel's 95%), which reframes the datacenter axis as a question about qubit ceiling rather than speed.
3. **QAE accuracy plateaus at m = 10 while cost keeps doubling** — the eigenphase lies within 3.0 × 10⁻⁶ of the 10-bit dyadic 355/1024, so further counting qubits correctly return zeros. Recorded as a declared limitation with `phase_error`/`phase_resolution` on every row so a reader can verify it.

## [0.1.1] — 2026-07-22 — Repo hygiene bar-raise: AGENTS.md, 100% coverage floor, theme-aware brand/diagram assets, badge fixes

A housekeeping release, deliberately versioned as a patch, not a minor: no
capability changed (still no `.cu` kernel, no real benchmark run — the same
stage-1 skeleton as 0.1.0). Everything below is tooling, documentation, CI,
and visual identity, done ahead of roadmap **Phase 1** (see
`docs/roadmap.md`).

### Added

- **`AGENTS.md`** — cross-tool discipline for keeping version numbers, status-bearing docs, and coverage claims honest before every commit to `main` and every tag; also now the single home for project instructions (commands, two-host workflow, non-negotiable constraints) previously only in `CLAUDE.md`. `CLAUDE.md` is a real `@AGENTS.md` import (Claude Code auto-loads `CLAUDE.md` only, never `AGENTS.md` directly — the initial prose-pointer version didn't actually import anything; see [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md)'s 2026-07-21 amendment).
- **`AGENTS.md` Git History rule**: never add an AI co-author trailer to a commit or otherwise cause an agent to appear in the GitHub Contributors graph — explicit owner preference.
- **`SECURITY.md`**: CI permission scoping (`contents: read` at the workflow level, `contents: write` scoped only to the release job) and the local-only Node/`@mermaid-js/mermaid-cli` build dependency for regenerating diagram/banner assets.
- **Theme-aware brand and diagram assets** — `assets/architecture/` (the README pipeline diagram, now a canonical Mermaid source + generated light/dark SVGs) and `assets/brand/` (an original q1729 hero banner sharing the diagram's palette), both code-generated, both embedded in the README via `<picture>` + `prefers-color-scheme`.
- **`docs/sessions.md`** — dated log of what each work session changed and verified.
- **`docs/adr/004-repo-hygiene-and-agent-sync.md`** — records this batch of hygiene decisions.
- **`benchmarks/README.md`** — placeholder documenting the real measured run files roadmap Phase 1 will place there.
- **mypy as a real, enforced CI gate** (`typecheck` job) — `pyproject.toml`'s `[tool.mypy]` config previously ran nowhere; wiring it in found and fixed one genuine finding in `analysis/narrator.py`.
- **`codecov.yml`** — 100% target, 0% threshold, matching the CI gate.

### Changed

- **CI coverage gate raised from a 95%-buffered floor to a literal `--cov-fail-under=100`** — real coverage on the cudaq-capable host was already 100%; this removes the deliberate buffer rather than chasing a new number.
- **CI split into four jobs** (`lint`, `typecheck`, `tests`, `docs`) instead of one monolithic job, so a failure names the specific gate that broke.
- **GitHub Actions bumped to current latest major tags**, verified against each action's published tags: `actions/checkout@v4→v7`, `actions/setup-python@v5→v7`, `codecov/codecov-action@v5→v7`, `softprops/action-gh-release@v2→v3`.
- Every "95%"/coverage-rationale mention across README, CLAUDE.md, CONTRIBUTING.md, `docs/setup.md`, `docs/roadmap.md` updated to describe the 100% gate.
- README hardware table and CUDA C++ badge updated from generic "CUDA 13.x" to the precise, verified figure (CUDA 13.3, driver 610.53) after checking the actual installed driver via `nvidia-smi` in WSL2.
- **README badges reworked**: Release badge is now a live GitHub-release badge instead of static "latest" text; added CUDA-QX, mypy, and pytest badges (every technology named in the Stack section now has one); grouped into four labeled rows (quality gate/release/license, NVIDIA stack, hardware axes, language/tooling) instead of unlabeled rows.
- **Fixed inverted badge label/message order**: `Ruff` (was `lint | Ruff`, now `Ruff | lint + format`), `mypy` (was `type-checked | mypy`, now `mypy | 2.3`), `pytest` (was `tests | pytest`, now `pytest | 9.1`) — every badge now follows the same name-first convention, verified by fetching each badge's actual rendered SVG text, not just checking the URL responds.
- **Local GPU / Cloud GPU badges** now link directly to the NVIDIA product pages (RTX 5070 family, H100) instead of the ADR docs.
- **`ruff format --check .` is now a real, enforced CI step** (in the `lint` job, alongside `ruff check .`) and a `make lint` step — the Ruff badge's "+ format" claim was false until this landed; reformatted the 2 files (`assets/brand/build_banner.py`, `tests/unit/test_backend.py`) that weren't yet compliant (whitespace-only, no logic change).
- **Release badge** reverted to static `release | latest` instead of a live version lookup, linking to the GitHub releases page. **SymPy badge** changed from `SymPy | exact math` to `SymPy | latest`, now linking to `github.com/sympy/sympy/releases` instead of sympy.org.
- **Badge grouping split**: the former single "Python + tooling" row is now two — Python/SymPy (language + the exact-math ground truth dependency) and Ruff/mypy/pytest (the three CI-enforced quality gates) — five labeled rows total instead of four.

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
- **Repo hygiene bar-raise**: `Makefile` (source of truth for commands), `pyproject.toml` (ruff / pytest / coverage config), CI quality gate (ruff + pytest on cudaq's `qpp-cpu` target + Codecov), tag-driven release workflow, `CLAUDE.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, and secret handling (`.env` gitignored, `.env.example` documents `NVIDIA_API_KEY` / `NIM_BASE_URL` / `NIM_MODEL`).

### Removed

- **Legacy PennyLane scaffold** (`scripts/quantum_engine.py`, `scripts/math_logic.py`, `scripts/gpu_check.py`, PennyLane deps) — superseded by the CUDA-Q structure; maintaining code slated for deletion was wasted effort (ADR 001).
- **Stale planning docs** (`docs/gpu_setup.md`, `docs/qrm.md`, `docs/ramanujan-cuda-quantum.md`, `docs/ramanujan-cuda-quantum-summary.md`) — QRM/VQE and Qiskit-era brainstorms superseded by the roadmap; the decisions they recorded live on as ADRs.

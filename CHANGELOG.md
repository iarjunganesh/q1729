# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
- **Release badge** reverted to static `release | latest` (matching sibling repo `drift`'s convention) instead of a live version lookup, linking to the GitHub releases page. **SymPy badge** changed from `SymPy | exact math` to `SymPy | latest`, now linking to `github.com/sympy/sympy/releases` instead of sympy.org.
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
- **Repo hygiene to sibling-repo standard** (`continuum`, `bankers-wrapped`): `Makefile` (source of truth for commands), `pyproject.toml` (ruff / pytest / coverage config), CI quality gate (ruff + pytest on cudaq's `qpp-cpu` target + Codecov), tag-driven release workflow, `CLAUDE.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, and secret handling (`.env` gitignored, `.env.example` documents `NVIDIA_API_KEY` / `NIM_BASE_URL` / `NIM_MODEL`).

### Removed

- **Legacy PennyLane scaffold** (`scripts/quantum_engine.py`, `scripts/math_logic.py`, `scripts/gpu_check.py`, PennyLane deps) — superseded by the CUDA-Q structure; maintaining code slated for deletion was wasted effort (ADR 001).
- **Stale planning docs** (`docs/gpu_setup.md`, `docs/qrm.md`, `docs/ramanujan-cuda-quantum.md`, `docs/ramanujan-cuda-quantum-summary.md`) — QRM/VQE and Qiskit-era brainstorms superseded by the roadmap; the decisions they recorded live on as ADRs.

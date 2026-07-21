# q1729 — the quantum taxicab

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/q1729-banner-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/brand/q1729-banner-light.svg">
    <img width="900" src="assets/brand/q1729-banner-light.svg"
         alt="q1729 — Ramanujan's mathematics meets the NVIDIA stack. How fast can a GPU compute π, classically and as a quantum computer? Consumer RTX to datacenter H100, with an AI layer that writes up what the numbers show."/>
  </picture>
</p>

> Ramanujan's mathematics meets the NVIDIA stack, end to end: CUDA C++, CUDA-Q/cuQuantum simulation, and NIM/Nemotron analysis — local silicon to cloud.

<!-- Row 1 — quality gate, release, license -->
[![CI](https://github.com/iarjunganesh/q1729/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/iarjunganesh/q1729/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/iarjunganesh/q1729/graph/badge.svg)](https://codecov.io/gh/iarjunganesh/q1729)
[![Release](https://img.shields.io/badge/release-latest-2ea44f?logo=github&logoColor=white)](https://github.com/iarjunganesh/q1729/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- Row 2 — the NVIDIA stack, in the order README's Stack section names it -->
[![CUDA-Q](https://img.shields.io/badge/NVIDIA-CUDA--Q-76B900?logo=nvidia&logoColor=white)](https://nvidia.github.io/cuda-quantum/)
[![CUDA-QX](https://img.shields.io/badge/NVIDIA-CUDA--QX-76B900?logo=nvidia&logoColor=white)](https://github.com/NVIDIA/cudaqx)
[![cuQuantum](https://img.shields.io/badge/NVIDIA-cuQuantum-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuquantum-sdk)
[![NIM](https://img.shields.io/badge/NVIDIA-NIM_%C2%B7_Nemotron-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![CUDA C++](https://img.shields.io/badge/CUDA_C%2B%2B-13.3-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)

<!-- Row 3 — the two hardware axes this project measures -->
[![Local GPU](https://img.shields.io/badge/local-RTX_5070_8GB-1F2937?logo=nvidia&logoColor=76B900)](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/)
[![Cloud GPU](https://img.shields.io/badge/cloud-H100_80GB-1F2937?logo=nvidia&logoColor=76B900)](https://www.nvidia.com/en-us/data-center/h100/)
[![WSL2](https://img.shields.io/badge/runtime-WSL2-0078D4?logo=linux&logoColor=white)](docs/adr/002-wsl2-runtime.md)

<!-- Row 4 — Python + the exact-math dependency that is the project's ground truth -->
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SymPy](https://img.shields.io/badge/SymPy-latest-3B5526?logo=sympy&logoColor=white)](https://github.com/sympy/sympy/releases)

<!-- Row 5 — every CI-enforced quality gate, in the order ci.yml runs them -->
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%2B%20format-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![mypy](https://img.shields.io/badge/mypy-2.3-2A6DB2?logo=python&logoColor=white)](https://mypy-lang.org/)
[![pytest](https://img.shields.io/badge/pytest-9.1-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## Why q1729?

When G. H. Hardy visited Srinivasa Ramanujan, he remarked that his taxicab's number, **1729**, seemed rather dull. Ramanujan replied instantly: *"No, it is a very interesting number; it is the smallest number expressible as the sum of two cubes in two different ways"* — 1729 = 1³ + 12³ = 9³ + 10³. The `q` is for quantum. This repo carries that spirit: taking mathematics that looks ordinary from the outside and finding the structure inside it.

The mathematics is not decoration. Ramanujan's 1914 series delivers **~8 correct digits of π per term** — still among the fastest-converging classical algorithms known — and each term is independent, so it parallelizes perfectly across CUDA cores:

$$\frac{1}{\pi} = \frac{2\sqrt{2}}{9801} \sum_{k=0}^{\infty} \frac{(4k)!\,(1103 + 26390k)}{(k!)^4\, 396^{4k}}$$

And the thread doesn't stop at π: the same territory — modular forms, Ramanujan expander graphs — underpins modern **quantum LDPC error-correcting codes**, which is where this project is ultimately headed (stage 3).

## The central question

> **At what problem size does quantum simulation stop being competitive with a hand-written CUDA kernel — on the same silicon — and does datacenter silicon move the crossover, or just postpone it?**

Classical wins locally; that's not the finding. The finding is the *crossover analysis*: the measured shape of that loss on a consumer RTX 5070 (8GB, ~30-qubit ceiling) versus a cloud H100 (80GB, ~33 qubits on one card, ~34 needs a second GPU — see [docs/nvidia-access.md](docs/nvidia-access.md)), and what a real quantum device would need to beat either at its own game.

## Architecture — one codebase, consumer to datacenter

<p align="center">
  <a href="assets/architecture/pipeline-light.svg" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/architecture/pipeline-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="assets/architecture/pipeline-light.svg">
      <img width="960" src="assets/architecture/pipeline-light.svg"
           alt="q1729 pipeline: Ramanujan's 1914 series feeds one CUDA-Q codebase that picks its target — a hand-written CUDA kernel and a QAE circuit locally on an RTX 5070, the same QAE circuit again on a cloud H100 — into a crossover analysis, validated throughout by the exact SymPy ground truth, then narrated by NIM/Nemotron into a findings draft."/>
    </picture>
  </a>
</p>

<p align="center"><sub>Source: <a href="assets/architecture/pipeline.mmd">Mermaid</a> · renders: <a href="assets/architecture/pipeline-light.svg">light SVG</a> / <a href="assets/architecture/pipeline-dark.svg">dark SVG</a></sub></p>

Two rules keep the hybrid honest (ADR 003):

1. **NIM/Nemotron is the analysis layer, never the simulator.** The narrator turns benchmark run files into findings drafts — every number comes from the run file, never from the model.
2. **Cloud is a second axis, not a replacement.** The same `quantum/backend.py` code selects `nvidia` on the RTX 5070 in WSL2, `qpp-cpu` in CI, and H100/multi-GPU targets on a rented cloud box — run files carry a `hardware` field so the curves land in one analysis.

## Roadmap

The three stages below are the research thread. The full evidence-sequenced plan — how each stage is *earned*, phase by phase, and everything from the original Blueprint — lives in **[docs/roadmap.md](docs/roadmap.md)** (Stage 1 = Phase 1, Stage 3 = Phase 2). This table is the summary; that document is authoritative for ordering.

| Stage | Focus | Deliverable |
| --- | --- | --- |
| **1 — π benchmark** | Ramanujan's 1914 1/π series as a hand-written CUDA kernel vs Quantum Amplitude Estimation with CUDA-Q, on the `nvidia` (cuStateVec) and `tensornet` (cuTensorNet) backends — run on both the RTX 5070 and a cloud H100 | Reproducible benchmark, consumer-vs-datacenter crossover analysis, NIM-drafted technical writeup |
| **2 — community** | Upstream contributions to CUDA-Q / CUDA-Q Academic; publish results; invite benchmark submissions from other GPUs (the run-file schema is hardware-agnostic) | Merged contributions, published writeup |
| **3 — Ramanujan graphs → qLDPC** | Ramanujan expander graphs underpin modern quantum LDPC codes. Simulate and decode them with CUDA-Q QEC (CUDA-QX) plus custom CUDA kernels | Open, reproducible QEC experiment lab |

## Stack

- **CUDA-Q** — core quantum programming platform (kernels, sampling, observables)
- **CUDA-QX** — extension libraries: Solvers (VQE/ADAPT) and QEC (codes + GPU decoders)
- **cuQuantum** — cuStateVec / cuTensorNet, the simulation engines behind CUDA-Q's backends
- **CUDA C++** — classical baseline kernels
- **NIM / Nemotron** — findings narrator via the NVIDIA NIM chat-completions API (`analysis/narrator.py`)
- **SymPy** — exact-rational reference implementation; any float drift in a GPU kernel shows up immediately

Runtime: CUDA-Q is Linux-only — on Windows, develop inside **WSL2** or the NGC container (`nvcr.io/nvidia/quantum/cuda-quantum`). ✅ **Verified on this machine**: cudaq 0.15 inside WSL2 initializes the `nvidia` (cuStateVec) target on the RTX 5070.

## Built to be trusted

- **Exact ground truth** — series terms are exact SymPy rationals, not floats; every GPU path is benchmarked against mathematics, not against another approximation
- **The AI layer can't invent results** — the narrator receives run-file numbers verbatim and only narrates; it is optional and degrades cleanly without a key (ADR 003)
- **Real-backend integration tests** — a Bell pair is actually simulated on the selected CUDA-Q target (CI: `qpp-cpu`; WSL2: `nvidia`), and the narrator is smoke-tested against the live NIM API when a key is present; unit tests mock only at the module boundary
- **100% coverage, no buffer** — measured 100% on WSL2/CI; CI gates at 100% with zero threshold (`.github/workflows/ci.yml`, `codecov.yml`, [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md))
- **Decisions are written down** — `docs/adr/`: CUDA-Q over PennyLane/Qiskit (001), WSL2 runtime (002), hybrid cloud + NIM (003)

## Project structure

- `classical/ramanujan_series.py` — the 1914 series, exact SymPy (ground truth for the CUDA kernel)
- `quantum/backend.py` — CUDA-Q target selection (`nvidia-mgpu` → `nvidia` → `tensornet` → `qpp-cpu`) + environment diagnostic
- `analysis/narrator.py` — NIM/Nemotron findings narrator (`make narrate`)
- `data/sample_run.json` — synthetic sample run file demonstrating the benchmark schema
- `benchmarks/` — real measured run files + crossover plots (roadmap Phase 1 deliverable; placeholder until then)
- `main.py` — status check; runs on any host, with or without cudaq / a NIM key
- `tests/` — `unit/` (any host) + `integration/` (real CUDA-Q simulation, live NIM; each skips where unavailable)
- `docs/adr/` — architecture decision records
- `docs/sessions.md` — dated log of what each work session changed and verified
- `assets/architecture/`, `assets/brand/` — theme-aware diagram and banner sources (edit the `.mmd`/`.py`, never the SVG)
- `AGENTS.md` — cross-tool discipline for keeping this README, `CLAUDE.md`, and every status-bearing doc in sync before commits and tags

## Quickstart

Any host (CPU-safe — classical math, narrator, unit tests, lint):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
pytest tests
```

NIM findings narrator (any host; key from [build.nvidia.com](https://build.nvidia.com)):

```bash
cp .env.example .env           # or: export NVIDIA_API_KEY=nvapi-...
make narrate                   # drafts findings from data/sample_run.json
```

CUDA-Q (WSL2 / Linux only):

```bash
pip install -r requirements-gpu.txt
python -m quantum.backend      # diagnostic: which target initialized
pytest tests                   # now includes the real-simulator integration tests
```

`make install` / `make test` / `make lint` / `make coverage` wrap the same commands (see `Makefile`).

## Hardware

| Axis | Component | Spec |
| --- | --- | --- |
| Local | GPU | NVIDIA RTX 5070 8GB (Blackwell), CUDA 13.3, driver 610.53 (verified 2026-07-21) |
| Local | CPU / RAM / OS | AMD Ryzen 9, 32GB DDR5, Windows 11 + WSL2 |
| Cloud | GPU | NVIDIA H100 80GB (rented per-run for the datacenter axis) |
| Cloud | AI | NVIDIA NIM API — Nemotron (findings narrator) |

8GB VRAM caps statevector simulation at roughly 29–30 qubits at the `nvidia` target's default fp32 precision; a single 80GB H100 moves that to ~33, and reaching ~34 needs a second GPU (`nvidia-mgpu`, see [docs/nvidia-access.md](docs/nvidia-access.md)). The gap between those ceilings — and what it does to the crossover — is itself one of the research questions.

## Contributing

Stage 2 opens this up properly. Until then: issues and benchmark-idea discussions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

---

*Author: Arjun Ganesh — [github.com/iarjunganesh](https://github.com/iarjunganesh)*

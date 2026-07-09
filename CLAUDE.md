# CLAUDE.md

Project context for Claude Code / agentic coding assistants working in this repo.

## What this project is
q1729 — Ramanujan's mathematics meets the NVIDIA stack end to end: CUDA C++, CUDA-Q/cuQuantum quantum simulation, and NIM/Nemotron analysis, from a local RTX 5070 8GB to cloud H100s. Three-stage roadmap in the README: (1) Ramanujan's 1914 1/π series as a CUDA kernel vs Quantum Amplitude Estimation via CUDA-Q — on consumer *and* datacenter silicon, (2) community contributions + published results, (3) Ramanujan expander graphs → qLDPC codes with CUDA-Q QEC.

**The README is the bible.** The roadmap there is authoritative; anything that contradicts it (especially anything PennyLane-flavored — that scaffold was cut on 2026-07-10, ADR 001) gets removed, not polished.

**Current phase**: stage-1 skeleton + hybrid cloud layer in place — `classical/ramanujan_series.py` (exact SymPy ground truth), `quantum/backend.py` (CUDA-Q target selection), `analysis/narrator.py` (NIM/Nemotron findings narrator, ADR 003), tests green on both hosts. Verified 2026-07-10: cudaq 0.15 in WSL2 selects the **`nvidia`** target (RTX 5070 GPU passthrough works). Next: the hand-written CUDA kernel, the QAE circuit, the benchmark harness that emits run files (schema: `data/sample_run.json`), and the first cloud-H100 comparison run.

## Key Commands
```bash
make install      # pip install -r requirements.txt (CPU-safe, any host)
make install-gpu  # pip install -r requirements-gpu.txt (WSL2 ONLY)
make run          # python main.py — status check, works with or without cudaq/NIM key
make gpu-check    # python -m quantum.backend — environment diagnostic
make narrate      # NIM narrator on data/sample_run.json (needs NVIDIA_API_KEY)
make test         # pytest tests -v (integration skips without cudaq)
make lint         # ruff check .
make coverage     # pytest tests --cov --cov-report=term-missing
```
No `make` on the Windows host: run the underlying commands directly (they're one-liners).

## Two-host workflow (ADR 002)
- **Windows host** (Python 3.14, `.venv/`): editing, classical math, unit tests, lint. cudaq does not install here — `quantum/backend.py` must always degrade gracefully.
- **WSL2 Ubuntu** (Python 3.12, venv at `~/q1729-cudaq`): everything CUDA-Q. Run tests there with
  `wsl -e bash -c "cd /mnt/c/ws/q1729 && ~/q1729-cudaq/bin/python -m pytest tests -q -p no:cacheprovider"`.
- CI (ubuntu, Python 3.12) installs cudaq and runs the integration suite on the `qpp-cpu` target — real simulator, no GPU.

## Non-negotiable constraints
- **NIM/Nemotron is the analysis layer, never the simulator (ADR 003).** The narrator narrates numbers from run files — it must never generate, estimate, or "fill in" measurements. Don't route any quantum/classical computation through an LLM.
- **`requirements.txt` must stay installable on a CPU-only host.** The CUDA-Q stack lives exclusively in `requirements-gpu.txt`. Don't add cudaq/cupy to the core file. (`httpx` is core — the narrator runs anywhere.)
- **`quantum/` and `analysis/` must never raise at import time when their backing service is absent.** `import cudaq` happens inside functions; `cudaq_available()` / `nim_configured()` gate everything. `main.py` is required to run everywhere (unit-tested).
- **`classical/ramanujan_series.py` is exact SymPy on purpose** — it is the ground truth the CUDA kernel will be benchmarked against. Don't "optimize" it with floats; float speed belongs in the CUDA kernel.
- **Target preference order is `nvidia` → `tensornet` → `qpp-cpu`** (`PREFERRED_TARGETS`) — the stage-1 benchmark matrix. GPU targets raise at set-time on non-GPU hosts; `select_target` walks the order rather than trusting availability. Cloud boxes use the same code (H100: `nvidia`/`nvidia-mgpu`); run files carry a `hardware` field instead of the code forking per machine.
- **Secrets**: only `NVIDIA_API_KEY` exists; `.env` is gitignored, `.env.example` documents it, the key is read from the environment at call time and never logged.

## Style / conventions (matching sibling repos `continuum`, `bankers-wrapped`)
- Makefile targets are the source of truth for how to run anything — keep the README Quick Start in sync with the Makefile, not the other way around
- ADRs go in `docs/adr/`, numbered sequentially, one decision per file
- CHANGELOG.md follows Keep a Changelog; the release workflow extracts the tagged version's notes from it
- Tests: `tests/unit/` mocks at the module boundary (fake `cudaq` module via `monkeypatch.setitem(sys.modules, ...)`, never mock the function under test); `tests/integration/` runs the real backend and skips cleanly where cudaq is absent
- Ruff is the only lint gate (`line-length 120`, `E,F,I,W,B`)
- **Near-100% test coverage is the standard** (owner's explicit requirement): measured 100% at the 0.1.0 cutover, CI gate at 95% (`--cov-fail-under=95`) to absorb churn. Every new module ships with tests that cover it fully. The only permitted exclusion is a JIT-compiled CUDA-Q kernel body (`# pragma: no cover` — coverage can't trace it), and each one must be exercised by a `tests/integration/` test instead. Measure where cudaq exists (WSL2/CI); Windows-local runs under-count `quantum/`

## Where things live
- Series math (exact): `classical/ramanujan_series.py`
- CUDA-Q target selection + diagnostic: `quantum/backend.py`
- NIM findings narrator: `analysis/narrator.py`; benchmark run-file schema: `data/sample_run.json` (synthetic, labeled)
- Decisions: `docs/adr/` — 001 (CUDA-Q over PennyLane/Qiskit), 002 (WSL2 runtime), 003 (hybrid cloud + NIM)
- CI quality gate: `.github/workflows/ci.yml`; releases: tag `v*.*.*` → `release.yml`

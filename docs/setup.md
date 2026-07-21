# Environment Setup Guide

Setup instructions across all supported environments. Everything under
"Windows" and "WSL2" below has been run and verified on this machine
(2026-07-10); the "Cloud H100" section is marked clearly where it's
unverified — no H100 run has happened yet (see
[docs/nvidia-access.md](nvidia-access.md)). This guide documents environments
that exist today; what is not built yet — the benchmark harness, the H100 run
— is sequenced in the [roadmap](roadmap.md), the single authority for ordering.

---

## 1. Windows (CPU-safe baseline)

No CUDA-Q, no GPU required. Runs classical math and the narrator.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
pytest tests/unit
```

---

## 2. WSL2 + NVIDIA GPU (primary dev environment)

Required for CUDA-Q quantum simulation on your local RTX.

### Prerequisites

- Windows 11 with WSL2 enabled
- NVIDIA driver with WSL2 GPU passthrough (verified 2026-07-21 via `nvidia-smi`
  inside WSL2: driver 610.53, CUDA 13.3 — NVIDIA's r610 driver branch is the
  floor CUDA Toolkit 13.3 itself requires)
- CUDA-Q installed inside the WSL2 venv via `requirements-gpu.txt`

### Step-by-step

```bash
# Inside WSL2 terminal

# 1. Verify GPU passthrough
nvidia-smi   # should show your RTX

# 2. Clone and install
git clone https://github.com/iarjunganesh/q1729
cd q1729
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-gpu.txt   # installs cudaq, cuquantum

# 3. Verify CUDA-Q target
python -m quantum.backend
```

Actual output on this machine (single RTX 5070):

```
cudaq_available: True
target: nvidia
```

Target selection is automatic (`quantum/backend.py`'s `PREFERRED_TARGETS`) —
there is no environment variable to force a different target. It tries
`nvidia-mgpu` first, but only when 2+ GPUs are visible; with one GPU it goes
straight to plain `nvidia`.

```bash
# 4. Run the full test suite
pytest tests -q
```

Actual result: full suite passes (one test skips — the WSL2 host doesn't run
every optional integration path).

### Known WSL2 issues

| Issue | Fix |
|---|---|
| `nvidia-smi` not found in WSL2 | Update the Windows NVIDIA driver; CUDA in WSL2 comes from the Windows driver |
| `cudaq` import fails | Ensure `requirements-gpu.txt` is installed inside the **WSL2** venv, not the Windows one — they're separate environments (ADR 002) |
| Narrator reports `nim_configured: False` in WSL2 despite the key being set on Windows | `NVIDIA_API_KEY` is a Windows env var; WSL2 doesn't inherit it unless it's in `WSLENV` (`setx WSLENV "NVIDIA_API_KEY/u"`) — see [docs/nvidia-access.md](nvidia-access.md) |

See ADR-002 for architectural rationale.

---

## 3. Cloud H100 (datacenter axis) — unverified, not yet run

In roadmap terms this is the optional datacenter axis of **Phase 1**, which
rolls into **Phase 2** if it is time-boxed out — it never blocks the local
RTX result ([roadmap.md](roadmap.md)).

**Nothing in this section has been executed.** No benchmark harness exists
yet (`main.py` has no CLI flags at all — the harness is **roadmap Phase 1**),
and no H100 instance has been rented for this project. This is what setup
would look like based on the code that exists today:

```bash
# On a rented H100 instance (Lambda, RunPod, vast.ai)
git clone https://github.com/iarjunganesh/q1729
cd q1729
pip install -r requirements.txt
pip install -r requirements-gpu.txt

python -m quantum.backend
# quantum/backend.py auto-detects GPU count; with 2+ GPUs it now tries the
# nvidia-mgpu path first (added 2026-07-10) — but that path itself has only
# been tested against a single-GPU failure mode (MPI plugin missing), never
# a real multi-GPU success. Confirm this actually works before trusting it.
```

Cost estimate and the multi-GPU caveat in detail: see
[docs/nvidia-access.md](nvidia-access.md).

There is currently no way to save a benchmark run file — that requires the
benchmark harness (**roadmap Phase 1**), which doesn't exist yet.

---

## 4. NIM Narrator setup

Works on any host (Windows, WSL2, cloud) — verified on both Windows and WSL2.

```bash
# 1. Get a free API key from build.nvidia.com
# 2. Add to .env
cp .env.example .env
echo "NVIDIA_API_KEY=nvapi-your-key-here" >> .env

# 3. Narrate a run file
make narrate
# or: python -m analysis.narrator data/sample_run.json
```

Without a key, the narrator raises `RuntimeError: NVIDIA_API_KEY is not set`
if you call it directly; `main.py`'s status check just reports
`nim_configured: False` instead of failing.

---

## 5. CI environment

`.github/workflows/ci.yml` runs four jobs: `lint` (ruff), `typecheck` (mypy),
`tests` (installs the CPU `cudaq` wheel and runs the full suite with a
literal `--cov-fail-under=100`, no buffer — [ADR 004](adr/004-repo-hygiene-and-agent-sync.md)),
and `docs` (required-file + stale-marker hygiene). The `tests` job does
**not** set any target-selection environment variable — CI runners have no
GPU, so `quantum/backend.py`'s existing `cudaq.num_available_gpus() == 0`
guard skips every GPU target automatically and lands on `qpp-cpu`. There is
no `CUDA_Q_TARGET` variable anywhere in the codebase.

```bash
# Reproduce CI locally (only meaningful without a GPU visible)
pytest tests
```

# Onboarding Guide

Get your first successful run within 10 minutes. Every command and output
below was actually run on 2026-07-10 (Windows `.venv`, WSL2, or both, as
noted) — nothing here is a hypothetical example. This guide documents only
what runs **today**; anything called out below as not-yet-built is sequenced
in the [roadmap](roadmap.md), which is the single authority for what gets
built and in what order.

---

## 1. Install and run (CPU-safe, any host)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
python main.py
```

Actual output on this Windows host (no cudaq installed, `NVIDIA_API_KEY` set):

```
--- q1729: status ---
Ramanujan series term 0: 1103
pi from 2 terms: 3.1415926535897938780 (15 digits correct)
cudaq cudaq_available: False
cudaq hint: CUDA-Q is Linux-only; run inside WSL2 (docs/adr/002-wsl2-runtime.md)
nim nim_configured: True
nim model: nvidia/nemotron-3-super-120b-a12b
```

Without a key, the last two lines instead read `nim nim_configured: False` and
`nim hint: set NVIDIA_API_KEY to enable the findings narrator (ADR 003)`.

### What the output means

| Field | Meaning |
|---|---|
| `cudaq cudaq_available: False` | Expected on Windows — CUDA-Q is Linux-only. Use WSL2 (below). |
| `nim nim_configured` | Narrator is optional. Benchmarks/tests run without it either way. |
| `pi from 2 terms` | SymPy exact-rational baseline — always available, no GPU or key needed. |

---

## 2. CUDA-Q diagnostic (WSL2 / Linux only)

```bash
pip install -r requirements-gpu.txt
python -m quantum.backend
```

Actual output in WSL2 on this machine (single RTX 5070):

```
cudaq_available: True
target: nvidia
```

`nvidia-mgpu` is tried first internally but only when 2+ GPUs are visible —
see [docs/nvidia-access.md](nvidia-access.md) for why, and for what happens on
a genuinely multi-GPU box (untested here; only one GPU is available locally).
On Windows (no cudaq), this instead prints:

```
cudaq_available: False
hint: CUDA-Q is Linux-only; run inside WSL2 (docs/adr/002-wsl2-runtime.md)
```

---

## 3. NIM Narrator

```bash
cp .env.example .env        # add your NVIDIA_API_KEY
make narrate                 # or: python -m analysis.narrator data/sample_run.json
```

Actual (real, live) narrator output against `data/sample_run.json` — this is
an unedited excerpt from a real NIM API call, not a mock:

```
## Findings

- **Classical CUDA implementation** on the consumer RTX 5070 8 GB computes 1 000 π digits in **0.004 s**, demonstrating extremely low latency for high-precision output.

- **Quantum Amplitude Estimation (QAE)** on the same RTX 5070 8 GB:
  - 20 qubits → 6 π digits in **2.9 s** (VRAM 1.2 GB)
  - 28 qubits → 8 π digits in **41.0 s** (VRAM 6.8 GB)
  - Increasing qubits by 8 yields only **+2 digits** while runtime grows by **≈13×** and VRAM by **≈5.7×**.
```

The narrator only prints to stdout — it does not save a file anywhere.
`data/sample_run.json` is explicitly labeled synthetic demo data in the file
itself, not a real measurement.

---

## Hardware Capability Matrix

| Hardware | Classical Kernel | Quantum Sim | Narrator | Notes |
|---|---|---|---|---|
| **Windows (no WSL2)** | ✅ via SymPy | ❌ | ✅ with key | CPU-only classical; verified above |
| **WSL2 + RTX 5070 8GB** | not yet built | ✅ `nvidia` (~29–30 qubits, fp32) | ✅ with key | Verified above; this is the only hardware actually tested |
| **Cloud H100 80GB** | not yet built | `nvidia-mgpu` path exists in code but is **unverified** — no multi-GPU hardware tested it | ✅ with key | See [docs/nvidia-access.md](nvidia-access.md) for cost + the untested-path caveat |
| **CI (no GPU)** | n/a | ✅ `qpp-cpu` (CPU sim) | ⚠️ narrator skipped, no key in CI | `.github/workflows/ci.yml` |

The hand-written CUDA classical kernel and the QAE circuit are **roadmap
Phase 1** ([roadmap.md](roadmap.md)) — only the SymPy reference implementation
exists today, not a CUDA kernel. Community-reported hardware rows (other
GPUs/VRAM sizes) aren't included here because none have been submitted yet:
soliciting them is **roadmap Phase 2**, which opens once Phase 1 produces a
real result worth submitting against.

### Backend fallback order (verified against `quantum/backend.py`)

```
nvidia-mgpu (multi-GPU cuStateVec, only if 2+ GPUs visible)
  → nvidia (single-GPU cuStateVec, fp32 default)
    → tensornet (cuTensorNet, different memory model — not a plain statevector)
      → qpp-cpu (CPU, always available)
```

`quantum/backend.py`'s `select_target()` walks this list automatically; no
code change or environment variable is needed between hosts.

# NVIDIA Access Notes

Operational reference for what NVIDIA developer/cloud access q1729 actually has,
how it's wired up, and where the real limits are. ADR 003 covers the design
decision (NIM as analysis layer, cloud GPU as a second benchmark axis); this
doc is the "how it's actually configured, and what still blocks us" reference.
For *when* the H100 run happens relative to everything else, the
[roadmap](roadmap.md) is the authority — this doc only covers configuration
and blockers, not sequencing.

## NIM / Nemotron (narrator layer) — working, no blocker

- **What it's for**: `analysis/narrator.py` only — narrates run-file numbers,
  never simulates (ADR 003). Nothing else in the repo touches NVIDIA's cloud API.
- **Key**: `NVIDIA_API_KEY`, from the free NVIDIA Developer Program signup at
  build.nvidia.com (`nvapi-...`). Stored in `.env` (gitignored, see
  `.env.example`); also present as a Windows **Machine**-level environment
  variable on this dev box.
- **Model**: `nvidia/nemotron-3-super-120b-a12b` (`narrator.py` `DEFAULT_MODEL`).
  NIM's `/v1/models` catalog lists entries that 404 on invoke —
  `llama-3.1-nemotron-70b-instruct` did exactly that (2026-07-10). Verify any
  new model with `make narrate` before switching the default.
- **Free tier**: 1,000 inference credits at signup (up to 5,000 on request),
  capped at 40 requests/minute per model (200 RPM available on request). q1729
  makes one narrator call per benchmark run — nowhere near this ceiling.
- **Verified working end-to-end 2026-07-10** on both hosts: Windows `.venv` and
  the WSL2 `~/q1729-cudaq` venv.

## Windows → WSL2 key propagation (gotcha)

- `NVIDIA_API_KEY` lives at the Windows **Machine** env-var level. WSL2 does
  **not** inherit Windows environment variables by default.
- Fix in place: `WSLENV` includes `NVIDIA_API_KEY` (`setx WSLENV
  "NVIDIA_API_KEY/u"`, User scope), so it crosses into WSL2.
- Without this, `quantum/backend.py` (cudaq) works fine in WSL2, but the
  narrator silently reports `nim_configured: False` there — reads like "NIM
  isn't connecting" when it's really "the key never arrived."
- If `WSLENV` is ever reset or overwritten by another tool, re-add
  `NVIDIA_API_KEY` to it — no code change needed, just the env var.

## Cloud H100 (stage-1 datacenter axis) — the real blocker

- **Not covered by the NIM API key above.** That key buys inference credits
  only, not GPU compute — a separate NVIDIA product line.
- The README/roadmap already assume a **rented** H100 instance (Lambda,
  RunPod, vast.ai, or AWS/Azure) for the `nvidia-mgpu` benchmark run —
  pay-per-use, no discount from the basic developer signup.
- **NVIDIA Inception** is a separate, free startup-accelerator program that
  can unlock real H100 hours (DGX Cloud credits, AWS Activate, Nebius AI
  Lift), but requires an incorporated company, an active AI product, and a
  working website, with a 1–4 week review — not the same tier as the
  build.nvidia.com signup already in use for NIM.
- **Status for q1729**: no H100 run has happened yet. This — cost/access to a
  rented H100, not code — is what's actually blocking the "cloud-H100
  comparison run", the optional datacenter axis of roadmap **Phase 1**
  ([roadmap.md](roadmap.md)).

## `nvidia-mgpu` is deprecated in cudaq 0.15 (verified 2026-07-10)

Tested directly against the installed WSL2 cudaq 0.15.0 (`cudaq.get_targets()`,
single RTX 5070):

- The bare `nvidia-mgpu` target name still exists but is **deprecated** — cudaq
  emits a warning telling you to use `cudaq.set_target("nvidia", option="mgpu,...")`
  instead.
- **Both** the deprecated name and its replacement raise the same
  `RuntimeError: Unable to create MPI plugin` on this single-GPU box — multi-GPU
  mode needs a working MPI plugin, not just 2+ visible GPUs. This exception is
  a normal, catchable `RuntimeError` (confirmed by testing it directly), not
  the process hard-abort that `GPU_TARGETS` guards against for driverless hosts.
- The single-GPU `nvidia` target's **actual default precision is fp32**
  (`cusvsim_fp32`, confirmed via `cudaq.get_target()`) — not fp64/complex128 as
  an earlier version of this doc assumed. `tensornet` defaults to fp64, but it's
  a fundamentally different memory model (tensor-network contraction, not a
  full statevector), so it doesn't fit the same VRAM formula at all.
- `quantum/backend.py` now handles this: `PREFERRED_TARGETS` tries
  `nvidia-mgpu` first (using the modern `option="mgpu,fp32"` call, matching
  single-GPU precision), but only when 2+ GPUs are visible, and falls back to
  plain `nvidia` on any `RuntimeError` — including the MPI-plugin failure above.
  **This fallback logic is tested (`tests/unit/test_backend.py`) and confirmed
  correct against real single-GPU behavior, but the actual multi-GPU success
  path has never run on real multi-GPU hardware** — verify on the H100 node
  before trusting it blindly.

## Estimated cost for the stage-1 H100 run

VRAM math for a full statevector at the `nvidia` target's real default
precision (fp32 / `complex64`, 8 bytes/amplitude — confirmed above, not
assumed): `2^qubits × 8 bytes`.

| Qubits | Statevector size | Fits on one 80GB H100?            |
|--------|------------------|-----------------------------------|
| 30     | 8.6 GB           | yes                               |
| 31     | 17.2 GB          | yes                               |
| 32     | 34.4 GB          | yes                               |
| 33     | 68.7 GB          | yes (near the ceiling)            |
| 34     | 137.4 GB         | no — needs 2 GPUs (`nvidia-mgpu`) |

So **~33 qubits is roughly the ceiling for a single H100 at the default
precision**; 34 needs a 2-GPU node. (`data/sample_run.json`'s `68.0 GB` at 32
qubits is explicitly labeled synthetic demo data in the file itself — it does
not confirm either precision assumption and shouldn't be read as measured
evidence.)

- **Single H100, up to ~33 qubits**: ~$2–4/hr on-demand/spot (RunPod, Vast.ai
  on the low end; Lambda SXM ~$3–4.3/hr). A full session — setup plus a
  qubit-count sweep — is realistically 30–90 minutes. **~$1–6 per session,**
  up to ~$10–20 with setup friction.
- **2-GPU node, 34 qubits**: ~$6–8/hr for a 2× H100 node (roughly linear in
  GPU count). Same time budget → **~$3–12 per session** — and only once the
  multi-GPU path above is actually confirmed working on real hardware.
- **Practical guidance**: no benchmark harness exists yet (roadmap **Phase 1**,
  [roadmap.md](roadmap.md)) — build and debug it for free against the RTX 5070 (`nvidia`)
  or `qpp-cpu` first, and only rent the H100 for the final verified run. Both
  RunPod and Vast.ai bill per-minute, so a short, deliberate session stays in
  the few-dollar range.

## Where this is wired in code

- `analysis/narrator.py` — `nim_configured()`, `narrate()`, `report()`
- `quantum/backend.py` — target selection (`PREFERRED_TARGETS`,
  `MULTI_GPU_TARGETS`, `select_target()`); independent of NIM, never touches
  `NVIDIA_API_KEY`
- `.env.example` — documents `NVIDIA_API_KEY`, `NIM_BASE_URL`, `NIM_MODEL`
  overrides

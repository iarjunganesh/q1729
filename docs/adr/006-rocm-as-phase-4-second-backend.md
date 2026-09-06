# ADR 006 — ROCm / MI300 is the designated Phase 4 second backend, not a Phase 1 detour

- **Status**: Accepted
- **Date**: 2026-08-05
- **Supersedes / amends**: none. Constrains [ADR 001](001-cuda-q-over-pennylane.md)
  (CUDA-Q over PennyLane/Qiskit) by naming the condition under which a second
  quantum simulator could enter the repo, and complements
  [ADR 005](005-cuda-kernel-via-nvrtc.md) (NVRTC compilation).

## Context

The owner asked whether q1729 should target AMD ROCm and cloud MI300-series
GPUs. The machine that produced the first measured result is an AMD CPU with an
NVIDIA GPU, so there is no local AMD GPU: every ROCm iteration would be rented
cloud time with no local development loop.

[Roadmap Phase 4](../roadmap.md#phase-4--backend-independence) already names
ROCm as a candidate second backend, and the Anti-Roadmap already forbids
"chasing every accelerator without a concrete experimental need." What was
missing was a decision about *which half of the benchmark can actually cross
vendors*, recorded before anyone spends money on an instance.

Four facts were established by inspection and by lookup on 2026-08-05:

1. **The classical arm is already portable.**
   `classical/ramanujan_kernel.cu` uses only `extern __shared__`,
   `__syncthreads()`, `blockIdx`/`threadIdx`/`blockDim`, and double arithmetic.
   Every one of those has a 1:1 HIP equivalent; `hipify` on this file is close
   to an identity transform. There are no warp intrinsics, no `atomicAdd` (ruled
   out for determinism, not portability), no cooperative groups, no
   vendor-specific math.
2. **The compile path is already portable.** `classical/cuda_kernel.py` compiles
   via `cupy.RawModule(backend="nvrtc")`. CuPy's ROCm build serves `RawModule`
   through **hipRTC** with the same API, and CuPy v14 (January 2026) supports
   ROCm 6.4. CuPy still labels ROCm support *experimental*.
3. **The quantum arm cannot cross vendors inside CUDA-Q.** Every GPU target
   CUDA-Q exposes — `nvidia`, `nvidia option=mgpu`, `nvidia option=mqpu`,
   `tensornet` — is built on cuQuantum/cuStateVec and is NVIDIA-only. There is
   no ROCm target. On an MI300X, `select_target` would fall through
   `PREFERRED_TARGETS` and land on `qpp-cpu`.
4. **A ROCm state-vector path does exist — outside CUDA-Q.** Qiskit Aer builds
   against ROCm (source build; there is no ROCm pip wheel equivalent to
   `qiskit-aer-gpu`), and AMD's own ROCm blog runs Aer's `statevector` method
   on an **MI300X under ROCm 7.2**, dated 2026-05-29. Google's qsim has a HIP
   backend contributed for Frontier (SC '23), reported at 7–9× over CPU and
   behind qsim-CUDA.

Fact 4 is why this ADR exists rather than a one-line roadmap note. It means the
tempting move — "rent an MI300X, run both arms, publish a second crossover" — is
available and would produce a plausible-looking, invalid result.

## Decision

**ROCm/MI300 is adopted as the designated Phase 4 second backend, and stays
behind Phases 2 and 3.** Four specific commitments:

### 1. The phase order does not change

No ROCm work begins before the Phase 3 experiment engine exists. Building a
backend abstraction now would shape it around one experiment and one
imagined vendor — precisely the speculative generality Phase 4's *"why not
earlier"* rules out. The outstanding H100 axis also comes first: reproducing on
a second **NVIDIA** machine is a smaller claim than reproducing on a second
**vendor**, and it is the one Phase 1 already promised.

### 2. An MI300 run is a portability result, not a crossover point

Until and unless the conditions in (3) are met, any AMD run publishes the
**classical arm only**, and its `limitations` field must state that the quantum
arm was not run and that the file is not a crossover measurement. The run-file
schema already carries `hardware_id` and a full environment block, so this needs
no schema change — it needs the discipline to not overclaim.

The invalid version, named here so it is recognizable later: running the
classical kernel on MI300X and the QAE circuit on `qpp-cpu`, then plotting them
on one axis. That is *GPU classical vs CPU quantum* wearing the crossover's
clothes, and the crossing point it shows is an artifact of the CPU fallback.

### 3. A second quantum simulator requires its own ADR

Introducing Qiskit Aer or qsim-HIP to get a GPU quantum arm on AMD would
partially reverse ADR 001, which chose CUDA-Q specifically to avoid a
translation layer. It is not forbidden — but it is a separate decision, and it
carries a hard prerequisite:

> **The confound must be measured before it is tolerated.** Aer-on-NVIDIA vs
> CUDA-Q-on-NVIDIA must be run on the *same* GPU first, so the simulator's
> contribution to the timing is a known quantity. Without that control, an
> AMD-vs-NVIDIA quantum comparison varies vendor *and* simulator at once and
> can attribute neither.

### 4. The classical kernel stays inside the HIP-portable CUDA subset

`classical/ramanujan_kernel.cu` may not acquire NVIDIA-specific constructs
(warp-level primitives such as `__shfl_*`, cooperative groups, PTX inline
assembly, `__nv_*` intrinsics, or CUDA-library calls from device code) without
amending this ADR. This costs nothing today — the kernel already satisfies it —
and it is what keeps a Phase 4 port cheap instead of turning it into a rewrite.
The constraint is recorded in the kernel's header comment and in `AGENTS.md`, so
it is visible at the point of edit rather than only here.

## Consequences

**Good:**

- The expensive question ("is the quantum arm portable?") is answered *before*
  anyone rents an instance, and the answer is written down: not inside CUDA-Q.
- The cheap half stays cheap. A Phase 4 classical port is a device shim, a ROCm
  requirements file, and a hipRTC preload analogous to `_preload_nvrtc` — not a
  kernel rewrite — for as long as constraint (4) holds.
- Phase 4's stated value ("a proven two-backend interface is a reference design
  for accelerator-portable benchmarking") gains a concrete, already-scouted
  target instead of a list of candidates.
- The most likely way this project could publish a wrong result is now named,
  with the mechanism spelled out.

**Costs, accepted:**

- **The MI300X memory ceiling stays unmeasured for now.** The first run's most
  interesting finding was that the quantum arm peaks at 12–20% GPU utilization,
  making the datacenter question one of *qubit ceiling*, not speed. MI300X's
  192 GB HBM is a substantially larger state-vector ceiling than H100's 80 GB,
  and Aer-on-ROCm could in principle reach it. Deferring means the best
  available answer to the ceiling question goes unclaimed for two phases. This
  is accepted because the answer would arrive with an unmeasured
  simulator confound attached, and a wrong number published early costs more
  than a right number published late.
- **No local AMD hardware.** Every ROCm iteration is rented and untestable
  offline, so Phase 4 will be slower per iteration than any prior phase. The
  two-host workflow (ADR 002) becomes a three-host workflow at that point.
- **ROCm CuPy is experimental**, and Aer-on-ROCm has no binary wheel. Phase 4
  must budget for a source build, which is a real departure from ADR 005's
  "no build step anywhere" property. That property is preserved on NVIDIA and
  will not be preserved on AMD.

## Alternatives considered

- **Start ROCm now, in place of the H100 axis.** Rejected: it reproduces on a
  second vendor before reproducing on a second machine of the *same* vendor,
  and it builds the backend interface off one experiment. Both are ordering
  errors the roadmap already argues against.
- **Add ROCm as a third arm of the existing Phase 1 benchmark.** Rejected: the
  Phase 1 hypothesis is a committed module constant in `benchmarks/harness.py`
  about a classical-vs-quantum crossover on one machine. Adding a vendor axis
  to it would mean editing that hypothesis after the fact — the one edit
  `AGENTS.md` forbids outright.
- **Declare ROCm out of scope permanently.** Rejected: the classical arm is
  genuinely portable, the Anti-Roadmap objects to *unmotivated* accelerator
  chasing rather than to portability itself, and Phase 4 needs exactly one
  second backend to prove its interface. ROCm is the strongest candidate on
  the list precisely because half the work is already done.
- **Wait for an official CUDA-Q ROCm backend.** Rejected as a plan: there is no
  published intent to build one, and cuQuantum is NVIDIA's product. If one ever
  ships, this ADR gets an amendment and Phase 4 gets dramatically cheaper.

## Verification

Established 2026-08-05:

- `classical/ramanujan_kernel.cu` read in full and confirmed to contain no
  NVIDIA-specific intrinsics — the portability claim in (1) is from inspection
  of the actual file, not from assumption.
- CUDA-Q's published simulator-backend list checked directly: all GPU targets
  are cuQuantum-based and NVIDIA-only; no ROCm/HIP target is offered.
- Qiskit Aer on ROCm confirmed against AMD's own ROCm blog running Aer
  `statevector` on MI300X under ROCm 7.2 (post dated 2026-05-29), and against
  the qsim HIP backend published at SC '23.
- CuPy ROCm/hipRTC `RawModule` support confirmed from CuPy's installation
  documentation and v14 release notes (ROCm 6.4, January 2026); still marked
  experimental.

**Not verified, and not claimed:** nothing in this ADR has been executed on AMD
hardware. No MI300X instance was rented, no ROCm build was attempted, and no
timing on AMD silicon is asserted anywhere in this repo. The portability claims
above are claims about *source-level compatibility*, which is the only thing
inspection can establish.

## 2026-09-06 audit amendment

ROCm remains Phase 4 with the existing same-vendor reproduction prerequisite. Source inspection suggests a portable subset; it does not verify a working port or its cost. No AMD run exists. Utilization alone does not establish dispatch as the current bottleneck or predict datacenter speed. ADR 007 adds evidence gates without authorizing hardware rental.

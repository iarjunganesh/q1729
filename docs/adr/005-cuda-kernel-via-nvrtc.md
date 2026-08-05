# ADR 005 — Compile the CUDA C++ kernel with NVRTC, not an nvcc build step

- **Status**: Accepted
- **Date**: 2026-08-05
- **Supersedes / amends**: none. Complements [ADR 002](002-wsl2-runtime.md) (WSL2 runtime).

## Context

Roadmap Phase 1 requires a real, hand-written CUDA C++ kernel as the classical
arm of the crossover benchmark. The obvious shape for that is a `.cu` file
compiled by `nvcc` into a shared library or a Python extension at build time.

Two facts about this repo's actual environment made that the wrong default:

1. **There is no CUDA Toolkit in WSL2 on this machine, and installing one is a
   multi-gigabyte system-level change.** WSL2 provides the *driver* through GPU
   passthrough; it does not provide `nvcc`. Verified 2026-08-05: `which nvcc`
   returns nothing and `/usr/local/cuda*` does not exist, while
   `nvidia-smi` reports a working RTX 5070 Laptop GPU on driver 610.88.
2. **An `nvcc` build step would put a compiler toolchain in the dependency
   path of every contributor and of CI.** CI runs on CPU-only GitHub runners.
   A build step that cannot run there either gets skipped — making the kernel
   untested in CI — or forces a toolkit install into every job.

Meanwhile `cupy`, which is already a Phase 1 dependency for GPU array handling,
exposes `RawModule(..., backend="nvrtc")`: NVRTC compiles CUDA C++ source at
runtime, in-process, with no toolkit and no build step.

## Decision

**The kernel lives in a real `.cu` file and is compiled at runtime by NVRTC
through `cupy.RawModule`.**

Specifically:

- `classical/ramanujan_kernel.cu` is ordinary, standalone CUDA C++ — not a
  Python string literal, not a template. It can be read, diffed, linted, and
  handed to `nvcc` unchanged if that ever becomes desirable.
- `classical/cuda_kernel.py` reads that file and compiles it. Nothing about
  the kernel source is generated.
- NVRTC itself comes from the `nvidia-cuda-nvrtc` wheel, pinned in
  `requirements-gpu.txt`. `cupy-cuda13x` does **not** bundle it; without the
  wheel every compile fails with `failed to load libnvrtc.so.13`.
- `classical/cuda_kernel.py::_preload_nvrtc` locates that wheel's library and
  `dlopen`s it with `RTLD_GLOBAL` before cupy looks for it. cupy 13.x resolves
  NVRTC by bare soname and does not search the wheel, so a pip-only CUDA
  install would otherwise be unable to compile anything.

## Consequences

**Good:**

- The whole GPU toolchain is `pip install -r requirements-gpu.txt`. No system
  package, no toolkit, no build step, no compiler in `PATH`.
- The `.cu` file stays honest CUDA C++ rather than becoming a string blob.
- Compilation is exercised by `tests/integration/test_cuda_kernel.py` on any
  machine with a GPU, so a syntax error in the kernel fails a test rather than
  a build nobody runs.

**Costs, accepted:**

- **First call pays compilation.** NVRTC compiles on first launch, which is
  why `time_partial_sum` discards a warm-up run before timing. That warm-up is
  declared in the run file's `statistical_treatment`, not hidden.
- **CI still cannot execute the kernel.** GitHub runners have no GPU, so the
  integration tests skip there exactly as the CUDA-Q ones do. Coverage of
  `classical/cuda_kernel.py` on CI comes from the mocked unit tests; the real
  numeric correctness check runs on WSL2. This is the same split ADR 002
  already established, not a new gap.
- **A cupy-version dependency in the preload shim.** If cupy later resolves
  NVRTC from the wheel itself, `_preload_nvrtc` becomes redundant. It returns
  `None` harmlessly in that case; it should be deleted, not left to rot.

## Alternatives considered

- **Install the CUDA Toolkit in WSL2 and build with `nvcc`.** Rejected for
  Phase 1: multi-gigabyte system change on the owner's machine for no gain in
  what is being measured. Not rejected forever — if a future phase needs
  features NVRTC lacks (separate compilation, device linking, CUDA libraries
  like cuBLAS in the kernel), this ADR should be amended rather than worked
  around.
- **Write the kernel as a Python string and `cupy.RawKernel` it inline.**
  Rejected: it makes the CUDA unreadable, unlintable, and invisible to
  `git ls-files '*.cu'` — which `AGENTS.md` uses as the check for whether a
  real kernel exists.
- **Use `numba.cuda` instead of CUDA C++.** Rejected: the roadmap deliverable
  is explicitly a *hand-written CUDA C++* baseline. A Python-JIT kernel would
  measure Numba's code generation, not a kernel a CUDA programmer wrote.

## Verification

Verified on 2026-08-05, WSL2, RTX 5070 Laptop GPU, cupy 13.6.0, NVRTC 13.3.33:

- `classical/ramanujan_kernel.cu` compiles through NVRTC and runs.
- Partial sums match `classical/ramanujan_series.py`'s exact SymPy rationals to
  1e-15 relative for 1, 2, 3, 5, 10 and 64 terms.
- `pi_approximation(3)` returns 3.141592653589793 — π to every digit a double
  carries.
- Results are bit-identical across repeated runs and across block sizes 32–512.

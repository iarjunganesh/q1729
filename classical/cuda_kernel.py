"""Hand-written CUDA C++ baseline for Ramanujan's 1914 series.

This is the *classical* arm of the stage-1 crossover benchmark: the kernel in
``classical/ramanujan_kernel.cu`` computes one series term per GPU thread and
reduces them, and this module compiles it, launches it, and times it.

Compilation goes through NVRTC (cupy's ``RawModule``) rather than an ``nvcc``
build step — see ``docs/adr/005-cuda-kernel-via-nvrtc.md``. The ``.cu`` file is
ordinary CUDA C++ either way; nothing here is CUDA-Q.

Like ``quantum/backend.py``, this module never raises at import time on a host
without the backing stack: ``import cupy`` happens inside functions and
``cuda_available()`` gates everything. On the Windows side of the two-host
workflow (ADR 002) it simply reports unavailability.

Run ``python -m classical.cuda_kernel`` for an environment diagnostic.
"""

import ctypes
import importlib.util
import math
from pathlib import Path
from typing import Any

#: The hand-written CUDA C++ source, kept as a real ``.cu`` file so it stays
#: readable (and greppable) as CUDA rather than a Python string literal.
KERNEL_PATH = Path(__file__).with_name("ramanujan_kernel.cu")

#: Entry point exported by ``KERNEL_PATH`` with C linkage.
KERNEL_NAME = "ramanujan_terms"

#: Threads per block. Must be a power of two — the kernel's tree reduction
#: halves ``blockDim.x`` and assumes it never hits an odd stride.
THREADS_PER_BLOCK = 256

#: NVRTC options. ``--std=c++17`` matches the CUDA 13 default and keeps the
#: kernel compiling identically whether NVRTC or nvcc builds it.
NVRTC_OPTIONS = ("--std=c++17",)


def cuda_available() -> bool:
    """True when cupy is importable *and* a CUDA device is actually visible.

    Importability alone is not enough: ``cupy`` installs fine on a driverless
    host and only fails when it first touches the runtime, which would turn a
    capability check into a crash.
    """
    try:
        import cupy
    except ImportError:
        return False
    try:
        return bool(cupy.cuda.runtime.getDeviceCount())
    except Exception:  # noqa: BLE001 — any driver-level failure means "no CUDA"
        return False


def kernel_source() -> str:
    """Return the CUDA C++ source text. Works on every host, GPU or not."""
    return KERNEL_PATH.read_text(encoding="utf-8")


def _preload_nvrtc() -> str | None:
    """Make ``libnvrtc`` resolvable by soname, returning the path preloaded.

    cupy 13.x dlopens NVRTC by bare soname (``libnvrtc.so.13``) and does not
    look inside the ``nvidia-cuda-nvrtc`` wheel that ships it, so a
    pip-only CUDA install fails to compile any RawModule unless the library
    directory happens to be on ``LD_LIBRARY_PATH``. Loading it here with
    ``RTLD_GLOBAL`` puts the soname in the process's already-loaded set, which
    is what cupy's dlopen then finds — no environment variable, no system
    CUDA toolkit. Returns None when nothing needed preloading (a system
    toolkit is present, or this host has no CUDA at all).
    """
    spec = importlib.util.find_spec("nvidia")
    if spec is None or not spec.submodule_search_locations:
        return None
    for root in spec.submodule_search_locations:
        # Deliberately loose: wheel layouts version the soname inconsistently
        # (libnvrtc.so.13, libnvrtc.so.13.3.33). The cost of the loose pattern
        # is that it also matches libnvrtc-builtins, a companion blob that is
        # not the API cupy needs — hence the skip below.
        for path in sorted(Path(root).rglob("libnvrtc*.so*")):
            if "builtins" in path.name:
                continue
            ctypes.CDLL(str(path), mode=getattr(ctypes, "RTLD_GLOBAL", 0))
            return str(path)
    return None


def _load_kernel() -> Any:
    """Compile ``KERNEL_PATH`` with NVRTC and return the callable kernel."""
    import cupy

    _preload_nvrtc()
    module = cupy.RawModule(code=kernel_source(), backend="nvrtc", options=NVRTC_OPTIONS)
    return module.get_function(KERNEL_NAME)


def partial_sum(n_terms: int, threads_per_block: int = THREADS_PER_BLOCK) -> float:
    """Sum the first ``n_terms`` series terms on the GPU (prefactor not applied).

    Block partials are summed on the host with :func:`math.fsum` — exact for
    the handful of doubles involved, and deterministic, which an in-kernel
    ``atomicAdd`` would not be.
    """
    if n_terms < 1:
        raise ValueError(f"need at least 1 term, got {n_terms}")
    if threads_per_block < 1 or threads_per_block & (threads_per_block - 1):
        raise ValueError(f"threads_per_block must be a power of two, got {threads_per_block}")

    import cupy

    blocks = math.ceil(n_terms / threads_per_block)
    block_sums = cupy.zeros(blocks, dtype=cupy.float64)
    kernel = _load_kernel()
    kernel(
        (blocks,),
        (threads_per_block,),
        (n_terms, block_sums),
        shared_mem=threads_per_block * 8,
    )
    cupy.cuda.runtime.deviceSynchronize()
    return math.fsum(block_sums.get().tolist())


def pi_approximation(n_terms: int, threads_per_block: int = THREADS_PER_BLOCK) -> float:
    """Approximate pi in double precision from the GPU partial sum.

    Double precision saturates near 15–16 correct digits regardless of how
    many terms are summed; that ceiling is a measured result of this benchmark,
    not a defect (see ``benchmarks/README.md``).
    """
    prefactor = 2.0 * math.sqrt(2.0) / 9801.0
    return 1.0 / (prefactor * partial_sum(n_terms, threads_per_block))


def time_partial_sum(
    n_terms: int,
    repeats: int = 5,
    threads_per_block: int = THREADS_PER_BLOCK,
) -> dict[str, Any]:
    """Time :func:`partial_sum` over ``repeats`` runs after one warm-up run.

    The warm-up absorbs NVRTC compilation and context creation, which would
    otherwise dominate the first measurement by orders of magnitude. Returns
    every sample, not just the mean — the research-standards contract requires
    the raw data, not a summary of it.
    """
    if repeats < 1:
        raise ValueError(f"need at least 1 repeat, got {repeats}")

    import time

    partial_sum(n_terms, threads_per_block)  # warm-up: compile + context

    samples: list[float] = []
    values: list[float] = []
    value = 0.0
    for _ in range(repeats):
        start = time.perf_counter()
        value = partial_sum(n_terms, threads_per_block)
        samples.append(time.perf_counter() - start)
        values.append(value)

    return {
        "n_terms": n_terms,
        "threads_per_block": threads_per_block,
        "repeats": repeats,
        "partial_sum": value,
        "partial_sums": values,
        "samples_s": samples,
        "mean_s": math.fsum(samples) / len(samples),
        "min_s": min(samples),
    }


def device_info() -> dict[str, Any]:
    """Describe the CUDA device the kernel will run on."""
    import cupy

    props = cupy.cuda.runtime.getDeviceProperties(cupy.cuda.runtime.getDevice())
    name = props["name"]
    return {
        "gpu": name.decode() if isinstance(name, bytes) else str(name),
        "vram_gb": round(props["totalGlobalMem"] / 1024**3, 2),
        "compute_capability": f"{props['major']}.{props['minor']}",
        "cuda_runtime": cupy.cuda.runtime.runtimeGetVersion(),
        "cupy": cupy.__version__,
    }


def report() -> dict[str, object]:
    """Environment diagnostic used by main.py and ``python -m classical.cuda_kernel``."""
    info: dict[str, object] = {"cuda_available": cuda_available()}
    if info["cuda_available"]:
        info.update(device_info())
    else:
        info["hint"] = "needs cupy + a visible CUDA device; run inside WSL2 (docs/adr/002-wsl2-runtime.md)"
    return info


if __name__ == "__main__":
    for key, value in report().items():
        print(f"{key}: {value}")

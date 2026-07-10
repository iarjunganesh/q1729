"""CUDA-Q target selection with graceful degradation.

Preference order mirrors the stage-1 benchmark matrix (README roadmap):
`nvidia-mgpu` (multi-GPU cuStateVec, only attempted with 2+ visible GPUs) ->
`nvidia` (single-GPU cuStateVec) -> `tensornet` (cuTensorNet) -> `qpp-cpu`
(CPU fallback, what CI runs). On hosts without CUDA-Q (the Windows side of
this machine), everything here reports unavailability instead of raising at
import time.

Run ``python -m quantum.backend`` for an environment diagnostic.
"""

import importlib.util

#: Stage-1 benchmark targets, in preference order. qpp-cpu is the CI/CPU fallback.
PREFERRED_TARGETS = ("nvidia-mgpu", "nvidia", "tensornet", "qpp-cpu")

#: Targets that require a CUDA device. On a driverless machine these do NOT
#: raise — cudaq.set_target hard-aborts the whole process (seen in CI), so
#: they must be skipped up front, never attempted-and-caught.
GPU_TARGETS = frozenset({"nvidia", "tensornet", "nvidia-mgpu"})

#: Targets that additionally need 2+ visible GPUs. Skipped outright below that
#: count — cheaper than an attempt, and avoids cudaq's stderr deprecation
#: warning on every single-GPU run.
MULTI_GPU_TARGETS = frozenset({"nvidia-mgpu"})


def cudaq_available() -> bool:
    """True when the cudaq package is importable (Linux/WSL2 only)."""
    return importlib.util.find_spec("cudaq") is not None


def select_target(preferred: tuple[str, ...] = PREFERRED_TARGETS) -> str:
    """Set and return the first CUDA-Q target that initializes.

    GPU targets are only attempted when a CUDA device is visible
    (``cudaq.num_available_gpus()``); see GPU_TARGETS for why.

    ``nvidia-mgpu`` also needs 2+ GPUs and a working MPI plugin. Verified
    2026-07-10 on cudaq 0.15 with a single RTX 5070: the bare ``nvidia-mgpu``
    target name is deprecated (cudaq warns to use ``nvidia`` with
    ``option="mgpu,..."`` instead), and *both* forms raise a normal, catchable
    ``RuntimeError: Unable to create MPI plugin`` on this box — not the
    process hard-abort GPU_TARGETS guards against — so it falls through via
    the same try/except as any other target. This path is otherwise untested:
    no multi-GPU hardware was available to confirm it actually succeeds.
    """
    import cudaq

    gpu_count = cudaq.num_available_gpus()
    errors: dict[str, str] = {}
    for name in preferred:
        if name in GPU_TARGETS and gpu_count == 0:
            errors[name] = "no CUDA GPU visible"
            continue
        if name in MULTI_GPU_TARGETS and gpu_count < 2:
            errors[name] = f"needs 2+ GPUs, {gpu_count} visible"
            continue
        try:
            if name == "nvidia-mgpu":
                # fp32 matches the single-GPU "nvidia" target's default
                # precision (verified via cudaq.get_target()) so switching
                # backends doesn't silently change simulation precision.
                cudaq.set_target("nvidia", option="mgpu,fp32")
            else:
                cudaq.set_target(name)
            return name
        except RuntimeError as exc:
            errors[name] = str(exc)
    raise RuntimeError(f"no CUDA-Q target could be initialized: {errors}")


def bell_counts(shots: int = 1000) -> dict[str, int]:
    """Sample a Bell pair on the selected target — the smallest end-to-end check.

    A working simulator returns only '00' and '11' in roughly equal counts;
    anything else means the target is broken, not just slow.
    """
    import cudaq

    # Kernel body is JIT-compiled by cudaq — invisible to coverage; proven to
    # execute by tests/integration/test_cudaq_smoke.py
    @cudaq.kernel
    def bell():  # pragma: no cover
        qubits = cudaq.qvector(2)
        h(qubits[0])  # noqa: F821 — CUDA-Q kernel DSL, resolved at JIT time
        x.ctrl(qubits[0], qubits[1])  # noqa: F821
        mz(qubits)  # noqa: F821

    result = cudaq.sample(bell, shots_count=shots)
    return {bits: result.count(bits) for bits in result}


def report() -> dict[str, object]:
    """Environment diagnostic used by main.py and ``python -m quantum.backend``."""
    info: dict[str, object] = {"cudaq_available": cudaq_available()}
    if info["cudaq_available"]:
        try:
            info["target"] = select_target()
        except RuntimeError as exc:
            info["target_error"] = str(exc)
    else:
        info["hint"] = "CUDA-Q is Linux-only; run inside WSL2 (docs/adr/002-wsl2-runtime.md)"
    return info


if __name__ == "__main__":
    for key, value in report().items():
        print(f"{key}: {value}")

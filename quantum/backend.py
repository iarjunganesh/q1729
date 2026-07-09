"""CUDA-Q target selection with graceful degradation.

Preference order mirrors the stage-1 benchmark matrix (README roadmap):
`nvidia` (cuStateVec) -> `tensornet` (cuTensorNet) -> `qpp-cpu` (CPU fallback,
what CI runs). On hosts without CUDA-Q (the Windows side of this machine),
everything here reports unavailability instead of raising at import time.

Run ``python -m quantum.backend`` for an environment diagnostic.
"""

import importlib.util

#: Stage-1 benchmark targets, in preference order. qpp-cpu is the CI/CPU fallback.
PREFERRED_TARGETS = ("nvidia", "tensornet", "qpp-cpu")


def cudaq_available() -> bool:
    """True when the cudaq package is importable (Linux/WSL2 only)."""
    return importlib.util.find_spec("cudaq") is not None


def select_target(preferred: tuple[str, ...] = PREFERRED_TARGETS) -> str:
    """Set and return the first CUDA-Q target that initializes.

    GPU targets raise at set-time on machines without a CUDA device, so this
    walks the preference order rather than trusting target availability.
    """
    import cudaq

    errors: dict[str, str] = {}
    for name in preferred:
        try:
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

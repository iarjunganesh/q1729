"""Capture reproducible source, installed software and selected execution devices."""

import hashlib
import os
import subprocess
from importlib.metadata import distributions
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, timeout=30).strip()


def source() -> dict[str, Any]:
    """Hash relevant working source, including untracked code, without storing diffs."""
    paths = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
    files = {}
    for name in sorted(set(paths)):
        path = ROOT / name
        if name and path.is_file() and (path.suffix in (".py", ".cu", ".toml", ".txt", ".yml") or name == "Makefile"):
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "revision": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=normal")),
        "files_sha256": files,
    }


def packages() -> dict[str, str]:
    """Resolved installed distributions; no URLs, credentials or environment dump."""
    return dict(sorted((dist.metadata["Name"], dist.version) for dist in distributions()))


def execution() -> dict[str, Any]:
    """Identify the actual CuPy device and query CUDA-Q rather than assuming fp32.

    This harness is a single-device comparison. Multi-GPU configurations need
    their own protocol/device mapping, so ambiguous GPU visibility is rejected.
    """
    import cudaq
    import cupy

    device = cupy.cuda.Device()
    target = cudaq.get_target()
    precision = str(target.get_precision()).split(".")[-1].lower()
    if precision not in ("fp32", "fp64"):
        raise ValueError(f"unsupported reported simulator precision: {precision}")
    if cupy.cuda.runtime.getDeviceCount() != 1 or (target.name != "qpp-cpu" and cudaq.num_available_gpus() != 1):
        raise ValueError("single-device protocol requires one visible CUDA device; select it before Python starts")
    return {
        "classical": {
            "backend": "cuda-nvrtc",
            "precision": "fp64",
            "ordinal": device.id,
            "pci_bus_id": device.pci_bus_id,
            "cuda_runtime": cupy.cuda.runtime.runtimeGetVersion(),
            "cuda_driver": cupy.cuda.runtime.driverGetVersion(),
        },
        "quantum": {
            "target": target.name,
            "precision": precision,
            "processor": "cpu" if target.name == "qpp-cpu" else "gpu",
            "pci_bus_id": None if target.name == "qpp-cpu" else device.pci_bus_id,
            "device_mapping": "shared single visible CUDA device" if target.name != "qpp-cpu" else "CPU fallback",
        },
        "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
        "runtime_controls": {
            key: os.getenv(key)
            for key in (
                "CUDA_DEVICE_ORDER",
                "OMP_NUM_THREADS",
                "CUDAQ_TENSORNET_FIND_DETERMINISTIC",
                "CUDAQ_TENSORNET_FIND_THREADS",
                "CUDAQ_TENSORNET_NUM_HYPER_SAMPLES",
                "CUDAQ_TENSORNET_SCRATCH_SIZE_PERCENTAGE",
                "CUDAQ_TENSORNET_CONTROLLED_RANK",
                "CUDAQ_TENSORNET_OBSERVE_CONTRACT_PATH_REUSE",
                "CUDAQ_TENSORNET_FIND_LIMIT",
            )
        },
    }

"""Capture the machine and software state a run file has to declare.

The research-standards contract (``docs/handbook/research-standards.md``)
requires every run to record its hardware, its software versions, and the
controls held fixed. This module collects those automatically, because a
contract that depends on someone remembering to paste `nvidia-smi` output by
hand is a contract that will be wrong within two runs.

Everything here degrades to ``None``/absent rather than raising: a run file
produced on a machine without a GPU is still a valid run file (it just cannot
carry GPU rows), and the harness must not die collecting metadata.
"""

import platform
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

#: Packages whose versions materially affect a measurement and therefore
#: belong in every run file.
TRACKED_PACKAGES = ("cudaq", "cupy-cuda13x", "numpy", "sympy")

#: Fields queried from nvidia-smi. Clocks and temperature are here so a reader
#: can see whether the GPU was thermally throttled during the run rather than
#: having to trust that it was not — on a laptop this is the difference between
#: a reproducible number and a number.
#:
#: Utilization is here for a subtler reason: a low clock has two completely
#: different causes, and only utilization separates them. A hot GPU at low
#: clocks is throttling and the timing is suspect; an *idle* GPU at low clocks
#: means the workload never saturated the device and the timing is measuring
#: dispatch overhead. Both occur in this benchmark, on different arms.
NVIDIA_SMI_FIELDS = (
    "name",
    "memory.total",
    "driver_version",
    "clocks.current.graphics",
    "clocks.max.graphics",
    "temperature.gpu",
    "power.draw",
    "power.limit",
    "utilization.gpu",
    "utilization.memory",
)


def package_versions() -> dict[str, str]:
    """Installed versions of TRACKED_PACKAGES; absent packages are omitted."""
    found: dict[str, str] = {}
    for name in TRACKED_PACKAGES:
        try:
            found[name] = version(name)
        except PackageNotFoundError:
            continue
    return found


def nvidia_smi() -> dict[str, str] | None:
    """Query NVIDIA_SMI_FIELDS, or None when nvidia-smi is unavailable."""
    binary = shutil.which("nvidia-smi")
    if binary is None:
        return None
    query = f"--query-gpu={','.join(NVIDIA_SMI_FIELDS)}"
    try:
        completed = subprocess.run(
            [binary, query, "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    first_gpu = completed.stdout.strip().splitlines()[0]
    values = [value.strip() for value in first_gpu.split(",")]
    return dict(zip(NVIDIA_SMI_FIELDS, values, strict=False))


def gpu_memory_used_mib() -> int | None:
    """Currently used VRAM in MiB, or None without nvidia-smi.

    Sampled either side of a simulation to get a measured footprint to set
    against the analytically predicted statevector size.
    """
    binary = shutil.which("nvidia-smi")
    if binary is None:
        return None
    try:
        completed = subprocess.run(
            [binary, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return int(completed.stdout.strip().splitlines()[0])


def gpu_sample() -> dict[str, str] | None:
    """A point-in-time GPU reading, for sampling *during* a run.

    :func:`collect` snapshots the machine before timing starts, when the GPU is
    idle and its clocks say nothing about the run.
    """
    return nvidia_smi()


def _numeric(value: str) -> float | None:
    """Leading number out of an nvidia-smi value like ``'2835 MHz'`` or ``'[N/A]'``."""
    head = value.strip().split()[0] if value.strip() else ""
    try:
        return float(head)
    except ValueError:
        return None


class LoadSampler:
    """Poll the GPU on a background thread for the duration of a measurement.

    Sampling once after a timed loop finishes races the GPU back to idle and
    reports whatever it happens to catch — which is how the first capture of
    this benchmark ended up claiming 847 MHz for a run that was never
    throttled. Polling throughout and keeping the peak is the only reading that
    describes the measurement rather than the moment after it.

    Used as a context manager; degrades to an empty summary where nvidia-smi is
    absent, so the harness runs unchanged on a machine without one::

        with LoadSampler() as sampler:
            ...timed work...
        row["gpu_under_load"] = sampler.summary()
    """

    def __init__(self, interval_s: float = 0.25) -> None:
        self.interval_s = interval_s
        self.samples: list[dict[str, str]] = []
        self._stop: Any = None
        self._thread: Any = None

    def _poll(self) -> None:
        while not self._stop.is_set():
            reading = nvidia_smi()
            if reading is not None:
                self.samples.append(reading)
            self._stop.wait(self.interval_s)

    def __enter__(self) -> "LoadSampler":
        import threading

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def summary(self) -> dict[str, Any] | None:
        """Peak readings across the sampling window, or None if nothing sampled.

        Peaks rather than means: the question these answer is "did this workload
        ever saturate the device, and did it ever get hot", and an average over
        a window that includes setup would understate both.
        """
        if not self.samples:
            return None
        peaks: dict[str, Any] = {"samples": len(self.samples)}
        for field in ("utilization.gpu", "clocks.current.graphics", "temperature.gpu", "power.draw"):
            values = [n for n in (_numeric(s.get(field, "")) for s in self.samples) if n is not None]
            if values:
                peaks[f"peak_{field}"] = max(values)
        return peaks


def collect(power_profile: str) -> dict[str, Any]:
    """Assemble the full environment block for a run file.

    ``power_profile`` is passed in rather than detected: on a laptop the
    vendor power/thermal mode is a declared *control*, and no reliable
    cross-platform way to read it exists. Recording it as an explicit,
    operator-supplied value is more honest than silently omitting a variable
    that measurably changes every timing in the file.
    """
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "packages": package_versions(),
        "gpu": nvidia_smi(),
        "power_profile": power_profile,
    }

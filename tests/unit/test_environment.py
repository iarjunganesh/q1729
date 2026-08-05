"""Unit tests for run-file environment capture.

Every function here must degrade rather than raise: a machine with no
nvidia-smi still has to produce a valid run file, or the harness becomes
un-runnable exactly where it is most useful (CI, a fresh clone, a CPU host).
"""

import subprocess

import pytest

from benchmarks import environment

SMI_LINE = "NVIDIA GeForce RTX 5070 Laptop GPU, 8151 MiB, 610.88, 2835 MHz, 3090 MHz, 65, 46.97 W, [N/A], 99 %, 40 %\n"


def _fake_smi(monkeypatch, stdout=SMI_LINE, found=True, raises=None):
    monkeypatch.setattr(environment.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if found else None)

    def fake_run(cmd, **kwargs):
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(environment.subprocess, "run", fake_run)


def test_package_versions_reports_installed_packages():
    versions = environment.package_versions()
    # numpy and sympy are core requirements, so they exist on every host.
    assert "numpy" in versions
    assert "sympy" in versions


def test_package_versions_skips_absent_packages(monkeypatch):
    monkeypatch.setattr(environment, "TRACKED_PACKAGES", ("definitely-not-a-real-package",))
    assert environment.package_versions() == {}


def test_nvidia_smi_parses_every_requested_field(monkeypatch):
    _fake_smi(monkeypatch)
    reading = environment.nvidia_smi()
    assert reading is not None
    assert reading["name"] == "NVIDIA GeForce RTX 5070 Laptop GPU"
    assert reading["driver_version"] == "610.88"
    assert reading["utilization.gpu"] == "99 %"
    assert set(reading) == set(environment.NVIDIA_SMI_FIELDS)


def test_nvidia_smi_returns_none_without_the_binary(monkeypatch):
    _fake_smi(monkeypatch, found=False)
    assert environment.nvidia_smi() is None


@pytest.mark.parametrize("error", [subprocess.SubprocessError("boom"), OSError("boom")])
def test_nvidia_smi_returns_none_when_the_call_fails(monkeypatch, error):
    _fake_smi(monkeypatch, raises=error)
    assert environment.nvidia_smi() is None


def test_nvidia_smi_reads_only_the_first_gpu(monkeypatch):
    _fake_smi(monkeypatch, stdout=SMI_LINE + SMI_LINE.replace("5070", "4090"))
    reading = environment.nvidia_smi()
    assert reading is not None
    assert "5070" in reading["name"]


def test_gpu_memory_used_returns_an_integer(monkeypatch):
    _fake_smi(monkeypatch, stdout="1729\n")
    assert environment.gpu_memory_used_mib() == 1729


def test_gpu_memory_used_returns_none_without_the_binary(monkeypatch):
    _fake_smi(monkeypatch, found=False)
    assert environment.gpu_memory_used_mib() is None


@pytest.mark.parametrize("error", [subprocess.SubprocessError("boom"), OSError("boom")])
def test_gpu_memory_used_returns_none_when_the_call_fails(monkeypatch, error):
    _fake_smi(monkeypatch, raises=error)
    assert environment.gpu_memory_used_mib() is None


def test_gpu_sample_delegates_to_nvidia_smi(monkeypatch):
    _fake_smi(monkeypatch)
    assert environment.gpu_sample() == environment.nvidia_smi()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2835 MHz", 2835.0), ("46.97 W", 46.97), ("65", 65.0), ("[N/A]", None), ("", None), ("   ", None)],
)
def test_numeric_extracts_leading_values_and_tolerates_na(raw, expected):
    assert environment._numeric(raw) == expected


def test_collect_records_the_declared_power_profile(monkeypatch):
    _fake_smi(monkeypatch)
    block = environment.collect("turbo")
    assert block["power_profile"] == "turbo"
    assert block["gpu"]["name"].startswith("NVIDIA")
    assert "python" in block
    assert "numpy" in block["packages"]


def test_collect_works_without_a_gpu(monkeypatch):
    """A CPU-only host still produces a valid environment block."""
    _fake_smi(monkeypatch, found=False)
    block = environment.collect("n/a")
    assert block["gpu"] is None
    assert block["power_profile"] == "n/a"


def _wait_for_samples(sampler, count, timeout_s=10.0):
    """Block until the sampler thread has collected ``count`` readings.

    Bounded so a broken sampler fails the test instead of hanging the suite.
    """
    import time

    deadline = time.monotonic() + timeout_s
    while len(sampler.samples) < count:
        if time.monotonic() > deadline:
            raise AssertionError(f"sampler produced {len(sampler.samples)} of {count} samples before timing out")
        time.sleep(0.01)


def test_load_sampler_collects_peaks_across_the_window(monkeypatch):
    """The peak is what matters: a mean over the window would hide saturation."""
    idle = {
        "utilization.gpu": "3 %",
        "clocks.current.graphics": "700 MHz",
        "temperature.gpu": "50",
        "power.draw": "8 W",
    }
    busy = {
        "utilization.gpu": "99 %",
        "clocks.current.graphics": "2835 MHz",
        "temperature.gpu": "65",
        "power.draw": "47 W",
    }
    readings = iter([idle])
    monkeypatch.setattr(environment, "nvidia_smi", lambda: next(readings, busy))

    with environment.LoadSampler(interval_s=0.01) as sampler:
        _wait_for_samples(sampler, 2)

    summary = sampler.summary()
    assert summary is not None
    assert summary["peak_utilization.gpu"] == 99.0
    assert summary["peak_clocks.current.graphics"] == 2835.0
    assert summary["peak_temperature.gpu"] == 65.0
    assert summary["samples"] >= 2


def test_load_sampler_summary_is_none_without_a_gpu(monkeypatch):
    """No nvidia-smi means no samples — the harness must still complete."""
    monkeypatch.setattr(environment, "nvidia_smi", lambda: None)
    with environment.LoadSampler(interval_s=0.01) as sampler:
        pass
    assert sampler.summary() is None


def test_load_sampler_omits_fields_that_never_parsed(monkeypatch):
    monkeypatch.setattr(environment, "nvidia_smi", lambda: {"utilization.gpu": "[N/A]"})
    with environment.LoadSampler(interval_s=0.01) as sampler:
        _wait_for_samples(sampler, 1)
    summary = sampler.summary()
    assert summary is not None
    assert "peak_utilization.gpu" not in summary

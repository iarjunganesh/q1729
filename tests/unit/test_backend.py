import sys
import types

import pytest

from quantum import backend


def test_cudaq_available_matches_find_spec():
    # On the Windows dev host this is False; inside WSL2/CI with cudaq it's True.
    assert backend.cudaq_available() == (
        __import__("importlib.util", fromlist=["util"]).find_spec("cudaq") is not None
    )


def test_report_without_cudaq(monkeypatch):
    monkeypatch.setattr(backend, "cudaq_available", lambda: False)
    info = backend.report()
    assert info["cudaq_available"] is False
    assert "WSL2" in info["hint"]


def test_report_with_cudaq_surfaces_target(monkeypatch):
    monkeypatch.setattr(backend, "cudaq_available", lambda: True)
    monkeypatch.setattr(backend, "select_target", lambda: "qpp-cpu")
    info = backend.report()
    assert info["target"] == "qpp-cpu"


def test_report_with_cudaq_surfaces_error(monkeypatch):
    def boom():
        raise RuntimeError("no target")

    monkeypatch.setattr(backend, "cudaq_available", lambda: True)
    monkeypatch.setattr(backend, "select_target", boom)
    info = backend.report()
    assert info["target_error"] == "no target"


def _fake_cudaq(monkeypatch, gpus, set_target):
    fake = types.ModuleType("cudaq")
    fake.num_available_gpus = lambda: gpus
    fake.set_target = set_target
    monkeypatch.setitem(sys.modules, "cudaq", fake)
    return fake


def test_select_target_walks_preference_order(monkeypatch):
    """With a GPU visible but GPU targets failing, fall through — don't raise."""
    calls = []

    def fake_set_target(name):
        calls.append(name)
        if name != "qpp-cpu":
            raise RuntimeError(f"{name} unavailable")

    _fake_cudaq(monkeypatch, gpus=1, set_target=fake_set_target)

    assert backend.select_target() == "qpp-cpu"
    assert calls == ["nvidia", "tensornet", "qpp-cpu"]


def test_select_target_never_attempts_gpu_targets_without_gpu(monkeypatch):
    """On driverless hosts set_target(GPU) hard-aborts the process (seen in CI),
    so GPU targets must be skipped before the call, not attempted-and-caught."""
    calls = []

    def fake_set_target(name):
        calls.append(name)

    _fake_cudaq(monkeypatch, gpus=0, set_target=fake_set_target)

    assert backend.select_target() == "qpp-cpu"
    assert calls == ["qpp-cpu"]


def test_select_target_raises_when_nothing_initializes(monkeypatch):
    def always_fail(name):
        raise RuntimeError("nope")

    _fake_cudaq(monkeypatch, gpus=1, set_target=always_fail)

    with pytest.raises(RuntimeError, match="no CUDA-Q target"):
        backend.select_target()


def test_select_target_skips_mgpu_with_only_one_gpu(monkeypatch):
    """nvidia-mgpu needs 2+ GPUs — a single GPU goes straight to plain nvidia."""
    calls = []

    def fake_set_target(name, **kwargs):
        calls.append((name, kwargs))

    _fake_cudaq(monkeypatch, gpus=1, set_target=fake_set_target)

    assert backend.select_target() == "nvidia"
    assert calls == [("nvidia", {})]


def test_select_target_prefers_nvidia_mgpu_with_multiple_gpus(monkeypatch):
    """With 2+ GPUs, the modern option-based multi-GPU call is tried first —
    not the deprecated bare "nvidia-mgpu" target name."""
    calls = []

    def fake_set_target(name, **kwargs):
        calls.append((name, kwargs))

    _fake_cudaq(monkeypatch, gpus=2, set_target=fake_set_target)

    assert backend.select_target() == "nvidia-mgpu"
    assert calls == [("nvidia", {"option": "mgpu,fp32"})]


def test_select_target_falls_back_when_mgpu_unavailable(monkeypatch):
    """Verified 2026-07-10: cudaq 0.15 raises a catchable RuntimeError (missing
    MPI plugin) rather than hard-aborting when multi-GPU init fails — must
    fall through to plain nvidia, not crash."""
    calls = []

    def fake_set_target(name, **kwargs):
        calls.append((name, kwargs))
        if kwargs.get("option") == "mgpu,fp32":
            raise RuntimeError("Unable to create MPI plugin")

    _fake_cudaq(monkeypatch, gpus=2, set_target=fake_set_target)

    assert backend.select_target() == "nvidia"
    assert calls == [
        ("nvidia", {"option": "mgpu,fp32"}),
        ("nvidia", {}),
    ]

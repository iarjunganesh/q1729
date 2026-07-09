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


def test_select_target_walks_preference_order(monkeypatch):
    """GPU targets fail on this host; select_target must fall through, not raise."""
    calls = []

    def fake_set_target(name):
        calls.append(name)
        if name != "qpp-cpu":
            raise RuntimeError(f"{name} unavailable")

    fake_cudaq = types.ModuleType("cudaq")
    fake_cudaq.set_target = fake_set_target
    monkeypatch.setitem(sys.modules, "cudaq", fake_cudaq)

    assert backend.select_target() == "qpp-cpu"
    assert calls == ["nvidia", "tensornet", "qpp-cpu"]


def test_select_target_raises_when_nothing_initializes(monkeypatch):
    fake_cudaq = types.ModuleType("cudaq")

    def always_fail(name):
        raise RuntimeError("nope")

    fake_cudaq.set_target = always_fail
    monkeypatch.setitem(sys.modules, "cudaq", fake_cudaq)

    with pytest.raises(RuntimeError, match="no CUDA-Q target"):
        backend.select_target()

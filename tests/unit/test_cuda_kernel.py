"""Unit tests for the CUDA kernel loader.

Mocked at the module boundary (a fake ``cupy`` in ``sys.modules``), never at
the function under test — same convention as ``test_backend.py``. The kernel
actually computing the right numbers is proven in
``tests/integration/test_cuda_kernel.py``, which needs a real GPU.
"""

import sys
import types

import pytest

from classical import cuda_kernel


def _fake_cupy(monkeypatch, device_count=1, block_sums=(1103.0,)):
    """Install a fake cupy exposing only what cuda_kernel touches."""
    launched: dict[str, object] = {}

    class FakeArray:
        def __init__(self, values):
            self._values = list(values)

        def get(self):
            return self

        def tolist(self):
            return self._values

    class FakeKernel:
        def __call__(self, grid, block, args, shared_mem=0):
            launched["grid"] = grid
            launched["block"] = block
            launched["args"] = args
            launched["shared_mem"] = shared_mem

    class FakeModule:
        def __init__(self, code, backend, options):
            launched["code"] = code
            launched["backend"] = backend
            launched["options"] = options

        def get_function(self, name):
            launched["kernel_name"] = name
            return FakeKernel()

    fake = types.ModuleType("cupy")
    fake.__version__ = "13.6.0"
    fake.float64 = "float64"
    fake.zeros = lambda n, dtype: FakeArray(block_sums)
    fake.RawModule = FakeModule
    fake.cuda = types.SimpleNamespace(
        runtime=types.SimpleNamespace(
            getDeviceCount=lambda: device_count,
            getDevice=lambda: 0,
            deviceSynchronize=lambda: None,
            runtimeGetVersion=lambda: 13000,
            getDeviceProperties=lambda i: {
                "name": b"NVIDIA GeForce RTX 5070 Laptop GPU",
                "totalGlobalMem": 8547991552,
                "major": 12,
                "minor": 0,
            },
        )
    )

    class FakeEvent:
        """CUDA event stub: time_phases only records and synchronizes."""

        def record(self):
            launched["events"] = launched.get("events", 0) + 1

        def synchronize(self):
            launched["synchronized"] = launched.get("synchronized", 0) + 1

    fake.cuda.Event = FakeEvent
    # get_elapsed_time reports milliseconds; 2.0 ms must surface as 0.002 s.
    fake.cuda.get_elapsed_time = lambda begin, end: 2.0
    monkeypatch.setitem(sys.modules, "cupy", fake)
    return launched


def test_kernel_source_is_real_cuda_and_readable_anywhere():
    """The .cu file must be loadable on any host, GPU or not."""
    source = cuda_kernel.kernel_source()
    assert "__global__" in source
    assert cuda_kernel.KERNEL_NAME in source
    assert 'extern "C"' in source


def test_cuda_available_false_without_cupy(monkeypatch):
    monkeypatch.setitem(sys.modules, "cupy", None)

    def no_cupy(name, *args, **kwargs):
        if name == "cupy":
            raise ImportError("no cupy here")
        return original(name, *args, **kwargs)

    original = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    monkeypatch.setattr("builtins.__import__", no_cupy)
    assert cuda_kernel.cuda_available() is False


def test_cuda_available_false_when_no_device(monkeypatch):
    _fake_cupy(monkeypatch, device_count=0)
    assert cuda_kernel.cuda_available() is False


def test_cuda_available_false_when_driver_raises(monkeypatch):
    """A driverless host makes cupy raise on first runtime touch — not a crash."""
    fake = types.ModuleType("cupy")

    def boom():
        raise RuntimeError("CUDA driver not found")

    fake.cuda = types.SimpleNamespace(runtime=types.SimpleNamespace(getDeviceCount=boom))
    monkeypatch.setitem(sys.modules, "cupy", fake)
    assert cuda_kernel.cuda_available() is False


def test_cuda_available_true_with_device(monkeypatch):
    _fake_cupy(monkeypatch, device_count=1)
    assert cuda_kernel.cuda_available() is True


def test_partial_sum_launches_kernel_with_expected_geometry(monkeypatch):
    launched = _fake_cupy(monkeypatch, block_sums=(1000.0, 103.0))
    monkeypatch.setattr(cuda_kernel, "_preload_nvrtc", lambda: None)

    total = cuda_kernel.partial_sum(300, threads_per_block=256)

    assert total == pytest.approx(1103.0)
    assert launched["grid"] == (2,)  # ceil(300 / 256)
    assert launched["block"] == (256,)
    assert launched["shared_mem"] == 256 * 8  # one double per thread
    assert launched["kernel_name"] == cuda_kernel.KERNEL_NAME
    assert launched["backend"] == "nvrtc"


@pytest.mark.parametrize("n_terms", [0, -1])
def test_partial_sum_rejects_non_positive_terms(n_terms):
    with pytest.raises(ValueError, match="at least 1 term"):
        cuda_kernel.partial_sum(n_terms)


@pytest.mark.parametrize("threads", [0, 100, 255])
def test_partial_sum_rejects_non_power_of_two_blocks(threads, monkeypatch):
    """The kernel's tree reduction halves blockDim.x and assumes it stays even."""
    with pytest.raises(ValueError, match="power of two"):
        cuda_kernel.partial_sum(10, threads_per_block=threads)


def test_pi_approximation_applies_the_prefactor(monkeypatch):
    monkeypatch.setattr(cuda_kernel, "partial_sum", lambda n, t=256: 1103.0000268319745)
    assert cuda_kernel.pi_approximation(5) == pytest.approx(3.141592653589793, abs=1e-12)


def test_time_partial_sum_discards_warm_up_and_keeps_every_sample(monkeypatch):
    calls = []

    def counting_partial_sum(n_terms, threads_per_block=256):
        calls.append(n_terms)
        return 1103.0

    monkeypatch.setattr(cuda_kernel, "partial_sum", counting_partial_sum)
    timing = cuda_kernel.time_partial_sum(64, repeats=3)

    assert len(calls) == 4  # 1 warm-up + 3 timed
    assert len(timing["samples_s"]) == 3
    assert timing["repeats"] == 3
    assert timing["partial_sum"] == 1103.0
    assert timing["min_s"] <= timing["mean_s"]


def test_time_partial_sum_rejects_zero_repeats():
    with pytest.raises(ValueError, match="at least 1 repeat"):
        cuda_kernel.time_partial_sum(10, repeats=0)


def test_device_info_decodes_byte_names(monkeypatch):
    _fake_cupy(monkeypatch)
    info = cuda_kernel.device_info()
    assert info["gpu"] == "NVIDIA GeForce RTX 5070 Laptop GPU"
    assert info["compute_capability"] == "12.0"
    assert info["vram_gb"] == pytest.approx(7.96, abs=0.05)


def test_device_info_accepts_str_names(monkeypatch):
    """Some cupy builds return str, not bytes."""
    _fake_cupy(monkeypatch)
    import cupy

    monkeypatch.setattr(
        cupy.cuda.runtime,
        "getDeviceProperties",
        lambda i: {"name": "Some GPU", "totalGlobalMem": 1024**3, "major": 8, "minor": 6},
    )
    assert cuda_kernel.device_info()["gpu"] == "Some GPU"


def test_report_without_cuda(monkeypatch):
    monkeypatch.setattr(cuda_kernel, "cuda_available", lambda: False)
    info = cuda_kernel.report()
    assert info["cuda_available"] is False
    assert "WSL2" in info["hint"]


def test_report_with_cuda_includes_device(monkeypatch):
    monkeypatch.setattr(cuda_kernel, "cuda_available", lambda: True)
    monkeypatch.setattr(cuda_kernel, "device_info", lambda: {"gpu": "fake"})
    info = cuda_kernel.report()
    assert info["cuda_available"] is True
    assert info["gpu"] == "fake"


def test_preload_nvrtc_returns_none_without_nvidia_package(monkeypatch):
    monkeypatch.setattr(cuda_kernel.importlib.util, "find_spec", lambda name: None)
    assert cuda_kernel._preload_nvrtc() is None


def test_preload_nvrtc_returns_none_when_spec_has_no_paths(monkeypatch):
    monkeypatch.setattr(
        cuda_kernel.importlib.util,
        "find_spec",
        lambda name: types.SimpleNamespace(submodule_search_locations=[]),
    )
    assert cuda_kernel._preload_nvrtc() is None


def test_preload_nvrtc_skips_builtins_and_loads_the_api_library(monkeypatch, tmp_path):
    """libnvrtc-builtins is a companion blob, not the API cupy needs."""
    lib = tmp_path / "lib"
    lib.mkdir()
    # Sorts before the real library, so the skip is genuinely exercised.
    (lib / "libnvrtc-builtins.so.13.3").write_text("")
    (lib / "libnvrtc.so.13").write_text("")

    monkeypatch.setattr(
        cuda_kernel.importlib.util,
        "find_spec",
        lambda name: types.SimpleNamespace(submodule_search_locations=[str(tmp_path)]),
    )
    loaded: list[str] = []
    monkeypatch.setattr(cuda_kernel.ctypes, "CDLL", lambda path, mode=0: loaded.append(path))

    result = cuda_kernel._preload_nvrtc()
    assert result is not None
    assert result.endswith("libnvrtc.so.13")
    assert loaded == [result]


def test_preload_nvrtc_returns_none_when_no_library_present(monkeypatch, tmp_path):
    monkeypatch.setattr(
        cuda_kernel.importlib.util,
        "find_spec",
        lambda name: types.SimpleNamespace(submodule_search_locations=[str(tmp_path)]),
    )
    assert cuda_kernel._preload_nvrtc() is None


def test_module_main_prints_report(monkeypatch, capsys):
    monkeypatch.setattr(cuda_kernel, "cuda_available", lambda: False)
    for key, value in cuda_kernel.report().items():
        print(f"{key}: {value}")
    assert "cuda_available" in capsys.readouterr().out


def test_time_phases_attributes_cost_to_each_stage(monkeypatch):
    """P1-R3: the end-to-end number must decompose into named phases."""
    launched = _fake_cupy(monkeypatch, block_sums=(1000.0, 103.0))

    result = cuda_kernel.time_phases(512, repeats=3, threads_per_block=256)

    assert result["repeats"] == 3
    assert result["blocks"] == 2
    assert set(result["phases_s"]) == set(cuda_kernel.PHASE_NAMES)
    for name in cuda_kernel.PHASE_NAMES:
        assert len(result["phases_s"][name]) == 3
    # Device time comes from CUDA events in milliseconds, not perf_counter.
    assert result["phases_s"]["execute"] == [0.002, 0.002, 0.002]
    # One event pair recorded per repeat, each synchronized once.
    assert launched["events"] == 6
    assert launched["synchronized"] == 3
    assert result["partial_sums"] == [1103.0, 1103.0, 1103.0]
    assert len(result["samples_s"]) == 3


def test_time_phases_reports_unattributed_time_rather_than_hiding_it(monkeypatch):
    """The parts must not be silently scaled up to match the whole."""
    _fake_cupy(monkeypatch)

    result = cuda_kernel.time_phases(1, repeats=2)

    for index, total in enumerate(result["samples_s"]):
        attributed = sum(result["phases_s"][name][index] for name in cuda_kernel.PHASE_NAMES)
        # execute is device time, so the host total need not exceed the sum;
        # what matters is that the gap is reported, not absorbed.
        assert result["unattributed_s"][index] == pytest.approx(total - attributed)
    assert len(result["unattributed_s"]) == 2


@pytest.mark.parametrize(("n_terms", "repeats"), [(0, 1), (1, 0)])
def test_time_phases_rejects_degenerate_requests(monkeypatch, n_terms, repeats):
    """Refuse before touching the GPU, like the rest of the module."""
    _fake_cupy(monkeypatch)
    with pytest.raises(ValueError, match="at least 1"):
        cuda_kernel.time_phases(n_terms, repeats=repeats)

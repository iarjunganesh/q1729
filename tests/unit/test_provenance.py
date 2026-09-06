import subprocess
import sys
from types import SimpleNamespace

import pytest

from benchmarks import environment, provenance
from quantum import qae


def test_source_hashes_dirty_and_untracked_code(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("x=1")
    (tmp_path / "extra.py").write_text("y=2")
    (tmp_path / "notes.md").write_text("not execution source")
    monkeypatch.setattr(provenance, "ROOT", tmp_path)

    def fake_output(cmd, **kwargs):
        if "ls-files" in cmd:
            return "main.py\0extra.py\0notes.md\0gone.py\0"
        if "rev-parse" in cmd:
            return "a" * 40
        return " M main.py"

    monkeypatch.setattr(provenance.subprocess, "check_output", fake_output)
    first = provenance.source()
    assert first["dirty"] is True and set(first["files_sha256"]) == {"main.py", "extra.py"}
    (tmp_path / "extra.py").write_text("y=3")
    assert provenance.source()["files_sha256"] != first["files_sha256"]


def test_packages_capture_resolved_transitive_versions(monkeypatch):
    monkeypatch.setattr(
        provenance, "distributions", lambda: [SimpleNamespace(metadata={"Name": "cuda-runtime"}, version="13.3")]
    )
    assert provenance.packages() == {"cuda-runtime": "13.3"}


@pytest.fixture
def backends(monkeypatch):
    target = SimpleNamespace(name="nvidia", get_precision=lambda: "SimulationPrecision.fp32")
    seeds = []
    cudaq = SimpleNamespace(
        get_target=lambda: target,
        num_available_gpus=lambda: 1,
        set_random_seed=seeds.append,
        kernel=lambda fn: fn,
        qview=object,
        qubit=object,
        sample=lambda *args, **kwargs: {"01": 5, "11": 5},
    )

    class Counts(dict):
        def count(self, bits):
            return self[bits]

    cudaq.sample = lambda *args, **kwargs: Counts({"01": 5, "11": 5})
    cupy = SimpleNamespace(
        cuda=SimpleNamespace(
            Device=lambda: SimpleNamespace(id=0, pci_bus_id="0000:02:00.0"),
            runtime=SimpleNamespace(
                getDeviceCount=lambda: 1, runtimeGetVersion=lambda: 13030, driverGetVersion=lambda: 13030
            ),
        )
    )
    monkeypatch.setitem(sys.modules, "cudaq", cudaq)
    monkeypatch.setitem(sys.modules, "cupy", cupy)
    return target, cudaq, cupy, seeds


@pytest.mark.parametrize("cpu", [True, False])
def test_execution_uses_actual_precision_and_selected_pci_device(backends, cpu):
    target, _, _, _ = backends
    target.name = "qpp-cpu" if cpu else "nvidia"
    result = provenance.execution()
    assert result["classical"]["pci_bus_id"] == "0000:02:00.0"
    assert result["quantum"]["processor"] == ("cpu" if cpu else "gpu")
    assert result["quantum"]["precision"] == "fp32"


def test_unknown_precision_and_ambiguous_devices_are_rejected(backends):
    target, _, cupy, _ = backends
    target.get_precision = lambda: "unknown"
    with pytest.raises(ValueError, match="precision"):
        provenance.execution()
    with pytest.raises(ValueError, match="precision"):
        qae.estimate(2)
    target.get_precision = lambda: "fp64"
    cupy.cuda.runtime.getDeviceCount = lambda: 2
    with pytest.raises(ValueError, match="one visible"):
        provenance.execution()


@pytest.mark.parametrize("seed", [None, 123])
def test_qae_retains_counts_seeds_precision_and_resolves_ties(backends, seed):
    target, _, _, seeds = backends
    target.get_precision = lambda: "fp64"
    outcome = qae.estimate(2, shots=10, seed=seed)
    assert outcome["counts"] == {"01": 5, "11": 5}
    assert outcome["outcome"] == 1
    assert outcome["statevector_bytes"] == 16 * 2**5
    assert seeds == ([] if seed is None else [seed])


def test_seed_protocol_rejects_invalid_and_unsupported_seeds(backends):
    target, _, _, _ = backends
    with pytest.raises(ValueError, match="32-bit"):
        qae.estimate(2, seed=0)
    target.name = "tensornet"
    with pytest.raises(ValueError, match="not supported"):
        qae.estimate(2, seed=1)


def test_sampler_queries_selected_device(monkeypatch):
    monkeypatch.setattr(environment, "GPU_SELECTOR", "0000:02:00.0")
    monkeypatch.setattr(environment.shutil, "which", lambda name: "nvidia-smi")
    calls = []

    def fake(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="12\n")

    monkeypatch.setattr(environment.subprocess, "run", fake)
    environment.nvidia_smi()
    assert environment.gpu_memory_used_mib() == 12
    assert all("--id=0000:02:00.0" in call for call in calls)

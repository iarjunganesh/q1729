import copy

import pytest

from benchmarks import harness, provenance, run_file


@pytest.mark.parametrize(
    "path,value",
    [
        (("provenance", "revision"), "unknown"),
        (("provenance", "dirty"), "false"),
        (("provenance", "files_sha256"), {}),
        (("execution", "quantum", "precision"), "assumed"),
        (("execution", "quantum", "uuid"), "wrong-device"),
        (("execution", "quantum", "processor"), "cpu"),
        (("configuration", "classical_term_counts"), [123]),
        (("runs", 0, "outcomes"), []),
        (("runs", 0, "outcomes", 0, "partial_sum"), 1),
        (("runs", 0, "outcomes", 0, "correct_digits"), 999),
        (("runs", 12, "outcomes", 0, "counts"), {"xx": 4000}),
        (("runs", 12, "outcomes", 0, "counts"), {"11": 1}),
        (("runs", 12, "outcomes", 0, "counts"), {"11": True}),
        (("runs", 12, "outcomes", 0, "target"), "qpp-cpu"),
        (("runs", 12, "outcomes", 0, "seed"), 123),
        (("runs", 12, "outcomes", 0, "outcome"), 0),
    ],
)
def test_schema3_rejects_broken_traceability(current_run, path, value):
    parent = current_run
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError):
        run_file.validate(current_run)


def test_seed_schedule_and_cpu_backend_validate(current_run):
    current_run["configuration"]["seed"] = 100
    execution = current_run["execution"]
    execution["quantum"].update(target="qpp-cpu", processor="cpu", uuid=None, pci_bus_id=None)
    current_run["controls"]["quantum_target"] = "qpp-cpu"
    for row in current_run["runs"][12:]:
        row["target"] = "qpp-cpu"
        for i, outcome in enumerate(row["outcomes"]):
            outcome.update(target="qpp-cpu", seed=100 + row["counting_qubits"] * row["repeats"] + i)
        row["seed"] = row["outcomes"][-1]["seed"]
    run_file.validate(current_run)


@pytest.mark.parametrize("failure", ["target", "source", "tensornet", "seed-range"])
def test_harness_blocks_inconsistent_provenance_before_archiving(
    current_run, fake_provenance, tmp_path, monkeypatch, failure
):
    from benchmarks import environment
    from quantum import backend

    out = tmp_path / "new.json"
    target = "tensornet" if failure == "tensornet" else "nvidia"
    monkeypatch.setattr(backend, "select_target", lambda: target)
    if failure != "target":
        current_run["execution"]["quantum"]["target"] = target
    else:
        current_run["execution"]["quantum"]["target"] = "qpp-cpu"
    monkeypatch.setattr(environment, "collect", lambda profile: current_run["environment"])
    monkeypatch.setattr(harness, "measure_classical", lambda *args: current_run["runs"][:1])
    monkeypatch.setattr(harness, "measure_quantum", lambda *args: current_run["runs"][12:13])
    if failure == "source":
        changed = copy.deepcopy(current_run["provenance"])
        changed["revision"] = "c" * 40
        values = iter([current_run["provenance"], changed])
        monkeypatch.setattr(provenance, "source", lambda: next(values))
    with pytest.raises(ValueError):
        harness.main(
            [
                "--out",
                str(out),
                "--power-profile",
                "turbo",
                "--hardware-id",
                "device",
                "--seed",
                str(2**32 if failure == "seed-range" else 123),
            ]
        )
    assert not out.exists()


def test_classical_retains_timed_values_without_post_timing_recomputation(monkeypatch):
    from classical import cuda_kernel

    monkeypatch.setattr(
        cuda_kernel,
        "time_partial_sum",
        lambda *args, **kwargs: {"samples_s": [0.1, 0.2], "partial_sums": [1103.0, 1104.0]},
    )
    monkeypatch.setattr(cuda_kernel, "pi_approximation", lambda *args: pytest.fail("extra untimed computation"))
    row = harness.measure_classical((1,), 2)[0]
    assert [o["partial_sum"] for o in row["outcomes"]] == [1103.0, 1104.0]
    assert row["pi_estimate"] == row["outcomes"][-1]["pi_estimate"]


def test_quantum_seed_schedule_and_each_outcome_are_retained(monkeypatch):
    from benchmarks import environment

    monkeypatch.setattr(environment, "nvidia_smi", lambda: None)
    monkeypatch.setattr(environment, "gpu_memory_used_mib", lambda: None)
    import math

    from quantum import qae

    calls = []

    def estimate(m, n, shots, seed=None):
        calls.append(seed)
        return {
            "pi_estimate": math.pi,
            "seed": seed,
            "counts": {"001": shots},
            "outcome": 1,
            "target": "qpp-cpu",
        }

    monkeypatch.setattr(qae, "estimate", estimate)
    row = harness.measure_quantum((3,), 2, 10, 2, "qpp-cpu", seed=100)[0]
    assert calls == [None, 106, 107]
    assert [outcome["seed"] for outcome in row["outcomes"]] == [106, 107]
    assert row["outcomes"][0]["counts"] == {"001": 10}


def test_schema2_is_readable_but_not_writable(measured_run):
    measured_run["schema"] = run_file.PREVIOUS_SCHEMA
    measured_run["controls"]["quantum_target"] = "nvidia"
    assert run_file.validate(measured_run) is measured_run
    with pytest.raises(ValueError, match="legacy"):
        run_file.validate(measured_run, allow_legacy=False)


def test_plot_labels_actual_cpu_target_and_precision(current_run, tmp_path):
    from benchmarks import plot

    current_run["execution"]["quantum"].update(target="qpp-cpu", processor="cpu", uuid=None, pci_bus_id=None)
    current_run["controls"]["quantum_target"] = "qpp-cpu"
    for row in current_run["runs"][12:]:
        row["target"] = "qpp-cpu"
        for outcome in row["outcomes"]:
            outcome["target"] = "qpp-cpu"
    for path in plot.render(current_run, tmp_path):
        assert "QAE: qpp-cpu / CPU / fp32" in path.read_text(encoding="utf-8")

"""Unit tests for the benchmark harness.

Both measurement arms are mocked at the module boundary — the point here is
that the harness assembles a *contract-conforming* run file and never silently
drops raw data, not that the GPU is fast. The real arms run in
``tests/integration/``.
"""

import json
import math

import pytest

from benchmarks import environment, harness


@pytest.fixture
def no_gpu_sampling(monkeypatch):
    """Neutralize nvidia-smi so tests never depend on the host having a GPU."""
    monkeypatch.setattr(environment, "nvidia_smi", lambda: None)
    monkeypatch.setattr(environment, "gpu_memory_used_mib", lambda: None)


def test_correct_digits_counts_significant_not_decimal_digits():
    """Relative error, so 3.14 scores ~3.3 (it agrees with pi to 3 significant figures)."""
    assert harness.correct_digits(3.14) == pytest.approx(3.30, abs=0.05)
    assert harness.correct_digits(3.1415) == pytest.approx(4.53, abs=0.05)
    # More accurate estimates must always score higher.
    assert harness.correct_digits(3.1415) > harness.correct_digits(3.14)


def test_correct_digits_caps_an_exact_match_at_double_precision():
    """Infinity is not a digit count — double precision tops out near 16."""
    assert harness.correct_digits(math.pi) == 16.0


def test_summarize_reports_mean_min_and_spread():
    stats = harness.summarize([1.0, 2.0, 3.0])
    assert stats["mean_s"] == 2.0
    assert stats["min_s"] == 1.0
    assert stats["stdev_s"] == pytest.approx(1.0)


def test_summarize_handles_a_single_sample():
    """One repeat has no spread — must not raise."""
    assert harness.summarize([1.5]) == {"mean_s": 1.5, "min_s": 1.5, "stdev_s": 0.0}


def test_measure_classical_keeps_every_raw_sample(monkeypatch, no_gpu_sampling):
    from classical import cuda_kernel

    monkeypatch.setattr(
        cuda_kernel,
        "time_partial_sum",
        lambda n, repeats=5, threads_per_block=256: {"samples_s": [0.1, 0.2]},
    )
    monkeypatch.setattr(cuda_kernel, "pi_approximation", lambda n, t=256: math.pi)

    rows = harness.measure_classical((1, 4), repeats=2)

    assert [row["n_terms"] for row in rows] == [1, 4]
    assert all(row["method"] == "classical-cuda" for row in rows)
    assert all(row["samples_s"] == [0.1, 0.2] for row in rows)
    assert rows[0]["mean_s"] == pytest.approx(0.15)


def test_measure_quantum_records_circuit_shape_and_warms_up(monkeypatch, no_gpu_sampling):
    from quantum import qae

    calls = []

    def fake_estimate(m, n, shots):
        calls.append(m)
        return {"counting_qubits": m, "pi_estimate": math.pi, "grover_applications": 2**m - 1}

    monkeypatch.setattr(qae, "estimate", fake_estimate)

    rows = harness.measure_quantum((3, 4), domain_qubits=2, shots=100, repeats=2, target="qpp-cpu")

    # one warm-up plus two timed repeats, per configuration
    assert calls == [3, 3, 3, 4, 4, 4]
    assert [row["counting_qubits"] for row in rows] == [3, 4]
    assert rows[0]["target"] == "qpp-cpu"
    assert len(rows[0]["samples_s"]) == 2


def test_build_run_file_satisfies_the_research_standards_contract():
    payload = harness.build_run_file(
        classical_rows=[{"method": "classical-cuda"}],
        quantum_rows=[{"method": "qae-cudaq", "target": "nvidia"}],
        power_profile="turbo",
        shots=4000,
        domain_qubits=2,
        hardware_id="rtx-5070-laptop-8gb",
        env={"gpu": None},
    )

    # The nine required fields of docs/handbook/research-standards.md
    assert payload["question"]
    assert payload["hypothesis"]
    assert payload["variables"]["classical"] and payload["variables"]["quantum"]
    assert payload["controls"]["power_profile"] == "turbo"
    assert payload["hardware_id"] == "rtx-5070-laptop-8gb"
    assert payload["environment"] == {"gpu": None}
    assert payload["statistical_treatment"]
    assert payload["limitations"]
    assert len(payload["runs"]) == 2


def test_build_run_file_marks_measured_data_as_not_synthetic():
    """The flag plot.py keys off — a real run must never be mistakable for the sample."""
    payload = harness.build_run_file([], [], "turbo", 1, 2, "id", {})
    assert payload["synthetic"] is False
    assert payload["schema"] == "q1729/run-file/2"


def test_limitations_name_the_accuracy_plateau_and_the_dispatch_bound():
    """Two findings a reader could otherwise mistake for bugs; they must stay declared."""
    text = " ".join(harness.LIMITATIONS)
    assert "355/1024" in text
    assert "utilization" in text


def test_parse_args_requires_a_declared_power_profile():
    """Power profile is a control, so the harness refuses to guess it."""
    with pytest.raises(SystemExit):
        harness.parse_args(["--out", "x.json"])


def test_parse_args_defaults_are_the_documented_ones():
    args = harness.parse_args(["--out", "x.json", "--power-profile", "turbo"])
    assert args.repeats == 5
    assert args.shots == 2000
    assert args.domain_qubits == harness.DOMAIN_QUBITS


def test_main_writes_a_run_file_and_caps_the_quantum_sweep(monkeypatch, tmp_path, no_gpu_sampling, measured_run):
    from quantum import backend

    monkeypatch.setattr(backend, "select_target", lambda: "qpp-cpu")
    monkeypatch.setattr(environment, "collect", lambda profile: measured_run["environment"])
    monkeypatch.setattr(harness, "measure_classical", lambda counts, repeats: [measured_run["runs"][0]])

    captured = {}

    def fake_measure_quantum(counting, domain_qubits, shots, repeats, target):
        captured["counting"] = counting
        row = measured_run["runs"][12]
        row.update(target=target, shots=shots)
        return [row]

    monkeypatch.setattr(harness, "measure_quantum", fake_measure_quantum)

    out = tmp_path / "nested" / "run.json"
    assert harness.main(["--out", str(out), "--power-profile", "turbo", "--max-counting-qubits", "4"]) == 0

    assert captured["counting"] == (2, 3, 4)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["controls"]["power_profile"] == "turbo"
    assert len(payload["runs"]) == 2

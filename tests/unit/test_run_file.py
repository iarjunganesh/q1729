"""Exercise corrupt records through the shared validator and public boundaries."""

import copy
import json
from pathlib import Path

import pytest

from analysis import narrator
from benchmarks import archive, harness, plot, run_file


def test_archive_and_labeled_demo_remain_readable(measured_run):
    original = copy.deepcopy(measured_run)
    assert run_file.validate(measured_run) is measured_run
    assert measured_run == original
    assert run_file.load("data/sample_run.json", allow_synthetic=True)["synthetic"] is True
    with pytest.raises(ValueError, match="legacy"):
        run_file.validate(measured_run, allow_legacy=False)


def test_current_schema_and_single_repeat(current_run):
    measured_run = current_run
    measured_run["schema"] = run_file.CURRENT_SCHEMA
    measured_run["controls"]["quantum_target"] = "nvidia"
    for row in measured_run["runs"]:
        row["outcomes"] = row["outcomes"][-1:]
        row.update(repeats=1, samples_s=[0.1], mean_s=0.1, min_s=0.1, stdev_s=0.0)
    assert run_file.validate(measured_run, allow_legacy=False) is measured_run


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("synthetic",), None),
        (("synthetic",), "false"),
        (("synthetic",), 0),
        (("schema",), "q1729/run-file/99"),
        (("question",), " "),
        (("series",), "other"),
        (("hypothesis",), None),
        (("variables",), None),
        (("variables", "classical"), []),
        (("controls",), None),
        (("controls", "shots"), True),
        (("controls", "domain_qubits"), 0),
        (("limitations",), []),
        (("limitations",), "text"),
        (("limitations", 0), ""),
        (("recorded_utc",), "2026-09-06"),
        (("recorded_utc",), "invalidZ"),
        (("environment",), None),
        (("environment", "power_profile"), "silent"),
        (("environment", "packages"), {}),
        (("environment", "packages", "cudaq"), None),
        (("environment", "gpu"), None),
        (("environment", "gpu", "driver_version"), ""),
        (("runs",), []),
        (("runs",), {}),
        (("runs", 0), []),
        (("runs", 0, "method"), "invented"),
        (("runs", 0, "n_terms"), -1),
        (("runs", 0, "mean_s"), "1"),
        (("runs", 0, "mean_s"), 0),
        (("runs", 0, "mean_s"), float("nan")),
        (("runs", 0, "correct_digits"), float("inf")),
        (("runs", 0, "repeats"), 3),
        (("runs", 0, "samples_s"), None),
        (("runs", 0, "samples_s", 0), -1),
        (("runs", 0, "samples_s", 0), 0),
        (("runs", 0, "mean_s"), 123),
        (("runs", 0, "abs_error"), 0.5),
        (("runs", 0, "correct_digits"), 123),
        (("runs", 12, "target"), "unknown"),
        (("runs", 12, "shots"), 1),
        (("runs", 12, "domain_qubits"), 1),
        (("runs", 12, "total_qubits"), 2),
        (("runs", 12, "grover_applications"), 5),
        (("runs", 12, "target"), "qpp-cpu"),
        (("environment", "extra"), {"nested": [float("inf")]}),
    ],
)
def test_corrupt_measured_records_rejected_everywhere(measured_run, tmp_path, monkeypatch, path, value):
    parent = measured_run
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(measured_run), encoding="utf-8")
    monkeypatch.setenv("NVIDIA_API_KEY", "test-only")

    def no_network(*args, **kwargs):
        pytest.fail("invalid evidence reached the external service")

    monkeypatch.setattr(narrator.httpx, "post", no_network)
    for call in (
        lambda: run_file.main([str(bad)]),
        lambda: plot.main([str(bad)]),
        lambda: narrator.narrate(bad),
    ):
        with pytest.raises(ValueError):
            call()
    assert not (tmp_path / "plots").exists()


def test_top_level_duplicate_and_missing_arm_rejected(measured_run):
    with pytest.raises(ValueError, match="object"):
        run_file.validate([])
    measured_run["runs"].append(measured_run["runs"][0])
    with pytest.raises(ValueError, match="duplicate"):
        run_file.validate(measured_run)
    measured_run["runs"] = measured_run["runs"][:1]
    with pytest.raises(ValueError, match="both"):
        run_file.validate(measured_run)


def test_current_target_and_synthetic_rules(measured_run):
    measured_run["schema"] = run_file.CURRENT_SCHEMA
    with pytest.raises(ValueError, match="quantum_target"):
        run_file.validate(measured_run)
    measured_run["synthetic"] = True
    with pytest.raises(ValueError, match="legacy demo"):
        run_file.validate(measured_run, allow_synthetic=True)
    sample = run_file.load("data/sample_run.json", allow_synthetic=True)
    sample["note"] = "Unlabeled numbers"
    with pytest.raises(ValueError, match="identify synthetic"):
        run_file.validate(sample, allow_synthetic=True)


def test_ci_entrypoint_accepts_existing_archive(capsys):
    assert run_file.main(["benchmarks/runs/2026-08-05-rtx5070-turbo.json"]) == 0
    assert "validated" in capsys.readouterr().out


def test_existing_json_is_rejected_before_gpu_work(tmp_path, monkeypatch):
    out = tmp_path / "existing.json"
    out.write_bytes(b"original evidence")
    from quantum import backend

    monkeypatch.setattr(backend, "select_target", lambda: pytest.fail("GPU initialized before collision check"))
    with pytest.raises(FileExistsError):
        harness.main(["--out", str(out), "--power-profile", "turbo"])
    assert out.read_bytes() == b"original evidence"


@pytest.mark.parametrize("flag,value", [("--repeats", "0"), ("--shots", "-1"), ("--max-counting-qubits", "1")])
def test_invalid_protocol_rejected_before_work(tmp_path, flag, value):
    with pytest.raises(ValueError):
        harness.main(["--out", str(tmp_path / "x.json"), "--power-profile", "turbo", flag, value])
    assert not (tmp_path / "x.json").exists()


def test_exclusive_creation_preserves_competing_output(tmp_path):
    first, second = tmp_path / "light.svg", tmp_path / "dark.svg"
    second.write_bytes(b"old dark")
    with pytest.raises(FileExistsError), archive.create_outputs([first, second]):
        pytest.fail("must not yield a partially reserved pair")
    assert not first.exists()
    assert second.read_bytes() == b"old dark"


def test_failed_write_removes_only_owned_outputs(tmp_path):
    path = tmp_path / "new.json"
    with pytest.raises(RuntimeError, match="interrupted"), archive.create_outputs([path]) as streams:
        streams[0].write(b"partial")
        raise RuntimeError("interrupted")
    assert not path.exists()


def test_render_validates_direct_calls_and_preserves_both_themes(measured_run, tmp_path):
    with pytest.raises(ValueError, match="filename"):
        plot.render(measured_run, tmp_path, "../outside")
    measured_run["synthetic"] = True
    with pytest.raises(ValueError, match="synthetic"):
        plot.render(measured_run, tmp_path)
    measured_run["synthetic"] = False
    paths = plot.render(measured_run, tmp_path)
    before = [p.read_bytes() for p in paths]
    with pytest.raises(FileExistsError):
        plot.render(measured_run, tmp_path)
    assert [p.read_bytes() for p in paths] == before


def test_plot_default_directory_is_run_specific(measured_run, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path("unique-run.json")
    path.write_text(json.dumps(measured_run), encoding="utf-8")
    assert plot.main([str(path)]) == 0
    assert Path("benchmarks/plots/unique-run/crossover-dark.svg").is_file()


@pytest.mark.parametrize("competing_writer", [False, True])
def test_writer_rejects_invalid_outcomes_and_late_collisions(
    current_run, tmp_path, monkeypatch, competing_writer, fake_provenance
):
    measured_run = current_run
    from benchmarks import environment
    from quantum import backend

    out = tmp_path / "run.json"
    monkeypatch.setattr(backend, "select_target", lambda: "nvidia")
    monkeypatch.setattr(environment, "collect", lambda profile: measured_run["environment"])
    monkeypatch.setattr(harness, "measure_classical", lambda counts, repeats: measured_run["runs"][:1])

    def measured_quantum(*args):
        if competing_writer:
            out.write_bytes(b"other writer owns this path")
        else:
            measured_run["runs"][12]["samples_s"] = []
        return measured_run["runs"][12:13]

    monkeypatch.setattr(harness, "measure_quantum", measured_quantum)
    with pytest.raises(FileExistsError if competing_writer else ValueError):
        harness.main(["--out", str(out), "--power-profile", "turbo", "--shots", "4000"])
    if competing_writer:
        assert out.read_bytes() == b"other writer owns this path"
    else:
        assert not out.exists()


def test_failed_render_preserves_original_archive(measured_run, tmp_path, monkeypatch):
    from matplotlib.figure import Figure

    def fail_save(*args, **kwargs):
        raise OSError("render interrupted")

    monkeypatch.setattr(Figure, "savefig", fail_save)
    with pytest.raises(OSError, match="interrupted"):
        plot.render(measured_run, tmp_path)
    assert list(tmp_path.glob("*.svg")) == []

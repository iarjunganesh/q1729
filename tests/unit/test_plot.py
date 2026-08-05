"""Unit tests for the crossover plotter.

The load guard matters more than the drawing: refusing synthetic input is the
mechanism that stops a demo file from ever being presented as a result.
"""

import json

import pytest

from benchmarks import plot

MEASURED = {
    "schema": "q1729/run-file/1",
    "synthetic": False,
    "controls": {"power_profile": "turbo"},
    "environment": {"gpu": {"name": "NVIDIA GeForce RTX 5070 Laptop GPU"}},
    "runs": [
        {"method": "classical-cuda", "n_terms": 2, "mean_s": 0.0026, "correct_digits": 15.85},
        {"method": "classical-cuda", "n_terms": 4096, "mean_s": 0.0137, "correct_digits": 16.0},
        {
            "method": "qae-cudaq",
            "counting_qubits": 8,
            "grover_applications": 255,
            "mean_s": 0.37,
            "correct_digits": 2.5,
        },
        {
            "method": "qae-cudaq",
            "counting_qubits": 16,
            "grover_applications": 65535,
            "mean_s": 9.29,
            "correct_digits": 5.0,
        },
    ],
}


def _write(tmp_path, payload, name="run.json"):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_runs_accepts_measured_data(tmp_path):
    assert plot.load_runs(_write(tmp_path, MEASURED))["synthetic"] is False


def test_load_runs_refuses_synthetic_data(tmp_path):
    """data/sample_run.json must never be plottable as if it were a result."""
    path = _write(tmp_path, {**MEASURED, "synthetic": True})
    with pytest.raises(ValueError, match="synthetic"):
        plot.load_runs(path)


def test_load_runs_refuses_a_file_that_does_not_declare_itself(tmp_path):
    """Absent flag is treated as synthetic — fail closed, not open."""
    payload = {k: v for k, v in MEASURED.items() if k != "synthetic"}
    with pytest.raises(ValueError, match="synthetic"):
        plot.load_runs(_write(tmp_path, payload))


def test_the_repos_sample_run_is_still_labeled_synthetic():
    """Guards the labeling of the real file in the repo, not just a fixture."""
    from pathlib import Path

    sample = json.loads(Path("data/sample_run.json").read_text(encoding="utf-8"))
    assert sample["synthetic"] is True
    with pytest.raises(ValueError, match="synthetic"):
        plot.load_runs(Path("data/sample_run.json"))


def test_split_arms_partitions_by_method():
    classical, quantum = plot.split_arms(MEASURED)
    assert len(classical) == 2
    assert len(quantum) == 2
    assert all(row["method"] == "qae-cudaq" for row in quantum)


def test_render_writes_both_themes(tmp_path):
    paths = plot.render(MEASURED, tmp_path)
    assert [p.name for p in paths] == ["crossover-light.svg", "crossover-dark.svg"]
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)


def test_render_themes_actually_differ(tmp_path):
    """A theme-aware asset that renders identically in both themes is a bug."""
    light, dark = plot.render(MEASURED, tmp_path)
    assert light.read_bytes() != dark.read_bytes()
    assert "0d1117" in dark.read_text(encoding="utf-8")


def test_render_survives_a_run_file_without_gpu_metadata(tmp_path):
    """A CPU-only run is still plottable; the title just says so."""
    payload = {**MEASURED, "environment": {"gpu": None}}
    assert len(plot.render(payload, tmp_path)) == 2


def test_render_honours_a_custom_stem(tmp_path):
    paths = plot.render(MEASURED, tmp_path, stem="phase1")
    assert [p.name for p in paths] == ["phase1-light.svg", "phase1-dark.svg"]


def test_main_renders_from_the_command_line(tmp_path, capsys):
    run_file = _write(tmp_path, MEASURED)
    assert plot.main([str(run_file), "--out-dir", str(tmp_path / "plots")]) == 0
    assert "crossover-light.svg" in capsys.readouterr().out


def test_parse_args_defaults_to_the_benchmarks_plots_directory():
    from pathlib import Path

    args = plot.parse_args(["some/run.json"])
    assert args.out_dir == Path("benchmarks/plots")
    assert args.stem == "crossover"

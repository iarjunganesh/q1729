"""Unit tests for the crossover plotter.

The load guard matters more than the drawing: refusing synthetic input is the
mechanism that stops a demo file from ever being presented as a result.
"""

import json
from pathlib import Path

import pytest

from benchmarks import plot

MEASURED = json.loads(Path("benchmarks/runs/2026-08-05-rtx5070-turbo.json").read_text(encoding="utf-8"))
MEASURED["runs"] = MEASURED["runs"][:2] + MEASURED["runs"][12:14]


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


def test_render_rejects_classical_cuda_evidence_without_gpu_metadata(tmp_path):
    """The CUDA arm cannot substantiate its hardware without device metadata."""
    payload = {**MEASURED, "environment": {**MEASURED["environment"], "gpu": None}}
    with pytest.raises(ValueError, match="GPU metadata"):
        plot.render(payload, tmp_path)


def test_render_honours_a_custom_stem(tmp_path):
    paths = plot.render(MEASURED, tmp_path, stem="phase1")
    assert [p.name for p in paths] == ["phase1-light.svg", "phase1-dark.svg"]


def test_main_renders_from_the_command_line(tmp_path, capsys):
    run_file = _write(tmp_path, MEASURED)
    assert plot.main([str(run_file), "--out-dir", str(tmp_path / "plots")]) == 0
    assert "crossover-light.svg" in capsys.readouterr().out


def test_parse_args_defaults_to_the_benchmarks_plots_directory():
    args = plot.parse_args(["some/run.json"])
    assert args.out_dir is None
    assert args.stem == "crossover"

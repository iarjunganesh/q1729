"""Use real archive structure for evidence-boundary tests; never publish fixtures."""

import copy
import json
import math
from pathlib import Path

import pytest


@pytest.fixture
def measured_run():
    return json.loads(Path("benchmarks/runs/2026-08-05-rtx5070-turbo.json").read_text(encoding="utf-8"))


@pytest.fixture
def current_run(measured_run):
    """Artificial schema-3 fixture, never written into the measured archive."""
    from benchmarks import run_file

    p = measured_run
    p["schema"] = run_file.CURRENT_SCHEMA
    p["provenance"] = {"revision": "a" * 40, "dirty": False, "files_sha256": {"main.py": "b" * 64}}
    p["execution"] = {
        "classical": {
            "backend": "cuda-nvrtc",
            "precision": "fp64",
            "uuid": "GPU-test",
            "pci_bus_id": "0000:01:00.0",
            "ordinal": 0,
            "cuda_runtime": 13030,
            "cuda_driver": 13030,
        },
        "quantum": {
            "target": "nvidia",
            "precision": "fp32",
            "processor": "gpu",
            "uuid": "GPU-test",
            "pci_bus_id": "0000:01:00.0",
        },
    }
    p["controls"].update(quantum_target="nvidia", precision={"classical": "fp64", "quantum": "fp32"})
    p["environment"]["gpu"].update(uuid="GPU-test")
    p["environment"].update(source=p["provenance"], execution=p["execution"])
    p["configuration"] = {
        "classical_term_counts": [r["n_terms"] for r in p["runs"][:12]],
        "counting_qubits": [r["counting_qubits"] for r in p["runs"][12:]],
        "seed": None,
        "seed_schedule": "unseeded",
        "outcome_summary": "last timed repeat",
        "timing_boundary": "wrapper",
    }
    for r in p["runs"]:
        if r["method"] == "classical-cuda":
            outcome = {k: r[k] for k in ("pi_estimate", "abs_error", "correct_digits")}
            outcome["partial_sum"] = 1 / ((2 * math.sqrt(2) / 9801) * r["pi_estimate"])
        else:
            r.update(
                precision="fp32",
                peak_probability=1.0,
                seed=None,
                seed_policy="unseeded",
                reproducibility_limit="stochastic fixture",
                counts={format(r["outcome"], f"0{r['counting_qubits']}b"): r["shots"]},
            )
            outcome = {k: v for k, v in r.items() if k not in ("samples_s", "repeats", "method")}
        r["outcomes"] = [copy.deepcopy(outcome) for _ in range(r["repeats"])]
    return p


@pytest.fixture
def fake_provenance(monkeypatch, current_run):
    from benchmarks import environment, provenance

    monkeypatch.setattr(provenance, "execution", lambda: current_run["execution"])
    monkeypatch.setattr(provenance, "source", lambda: current_run["provenance"])
    monkeypatch.setattr(provenance, "packages", lambda: current_run["environment"]["packages"])
    monkeypatch.setattr(environment, "GPU_SELECTOR", None)

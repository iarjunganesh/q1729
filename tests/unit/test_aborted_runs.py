"""A run that stops early still leaves evidence (ADR 011).

The late-failure tests drive :func:`benchmarks.harness.main` end to end with
both arms faked at the module boundary (``cuda_kernel.partial_sum`` and
``qae.estimate``), inject a stop at a chosen point, and then read the archive
back through the same validator CI uses.
"""

import copy
import itertools
import json
import math

import pytest

from analysis import narrator
from benchmarks import environment, harness, plot, run_file
from quantum import quantization

REAL_BUDGET = harness.Budget


@pytest.fixture
def faked_arms(monkeypatch, current_run, fake_provenance):
    """Fake both arms and the host so ``harness.main`` runs anywhere, deterministically."""
    from classical import cuda_kernel
    from quantum import backend, qae

    monkeypatch.setattr(environment, "nvidia_smi", lambda: None)
    monkeypatch.setattr(environment, "gpu_memory_used_mib", lambda: None)
    monkeypatch.setattr(backend, "select_target", lambda: "nvidia")
    monkeypatch.setattr(environment, "collect", lambda profile: current_run["environment"])
    ticks = itertools.count(0.0, 0.001)
    monkeypatch.setattr(harness.time, "perf_counter", lambda: next(ticks))

    arms = {"classical_calls": 0, "quantum_calls": {}, "classical_fault": None, "quantum_fault": None}

    def partial_sum(n_terms):
        arms["classical_calls"] += 1
        if arms["classical_fault"]:
            arms["classical_fault"](n_terms, arms["classical_calls"])
        return 1103.0

    def estimate(m, domain_qubits, shots, seed=None):
        calls = arms["quantum_calls"][m] = arms["quantum_calls"].get(m, 0) + 1
        if arms["quantum_fault"]:
            arms["quantum_fault"](m, calls)
        outcome = quantization.ideal_outcome(m)
        pi_estimate = 4 * math.sin(math.pi * outcome / 2**m) ** 2
        return {
            "counting_qubits": m,
            "domain_qubits": domain_qubits,
            "total_qubits": m + domain_qubits + 1,
            "grover_applications": 2**m - 1,
            "target": "nvidia",
            "precision": "fp32",
            "counts": {format(outcome, f"0{m}b"): shots},
            "seed": seed,
            "seed_policy": "unseeded; stochastic outcomes",
            "reproducibility_limit": "fake arm",
            "shots": shots,
            "outcome": outcome,
            "peak_probability": 1.0,
            "pi_estimate": pi_estimate,
            "abs_error": abs(pi_estimate - math.pi),
        }

    monkeypatch.setattr(cuda_kernel, "partial_sum", partial_sum)
    monkeypatch.setattr(qae, "estimate", estimate)
    return arms


def run_main(out, *extra):
    argv = ["--out", str(out), "--power-profile", "turbo", "--time-budget-s", "60"]
    return harness.main([*argv, "--repeats", "2", "--shots", "100", "--max-counting-qubits", "4", *extra])


def test_complete_run_covers_its_planned_sweep(faked_arms, tmp_path):
    out = tmp_path / "complete.json"
    assert run_main(out) == 0
    payload = run_file.load(out)
    assert payload["schema"] == run_file.CURRENT_SCHEMA
    assert payload["status"]["state"] == "complete"
    assert payload["status"]["abort"] is None
    assert payload["configuration"]["counting_qubits"] == [2, 3, 4]


def test_injected_late_failure_leaves_an_auditable_archive(faked_arms, tmp_path, capsys):
    def fail_late(m, calls):
        if m == 4 and calls == 3:  # warm-up, first repeat, then the second repeat fails
            raise RuntimeError("injected late failure")

    faked_arms["quantum_fault"] = fail_late
    out = tmp_path / "aborted.json"
    with pytest.raises(RuntimeError, match="injected late failure"):
        run_main(out)

    payload = run_file.load(out, allow_incomplete=True)
    status = payload["status"]
    assert status["state"] == "aborted"
    assert status["abort"]["reason"] == "error"
    assert status["abort"]["exception_type"] == "RuntimeError"
    assert status["planned"]["counting_qubits"] == [2, 3, 4]
    # Every completed configuration survives the failure, summarized as usual...
    assert len(payload["runs"]) == len(harness.CLASSICAL_TERM_COUNTS) + 2
    assert payload["configuration"]["counting_qubits"] == [2, 3]
    # ...and the unfinished one keeps its raw sample and counts, unsummarized.
    partial = status["abort"]["incomplete_configuration"]
    assert partial["counting_qubits"] == 4
    assert len(partial["samples_s"]) == len(partial["outcomes"]) == 1
    assert partial["outcomes"][0]["counts"] == {format(quantization.ideal_outcome(4), "04b"): 100}
    assert "mean_s" not in partial

    # An audit record, not a result: result consumers refuse it by default.
    with pytest.raises(ValueError, match="audit record"):
        run_file.load(out)
    with pytest.raises(ValueError, match="audit record"):
        plot.render(payload, tmp_path / "plots")
    with pytest.raises(ValueError, match="audit record"):
        narrator.load_run(out)
    assert run_file.main([str(out)]) == 0
    assert "aborted audit record" in capsys.readouterr().out


def test_budget_exhaustion_archives_and_exits_with_its_own_code(faked_arms, monkeypatch, tmp_path):
    # 1.5 s per check: the 36 classical checks end at 54 s, and the budget of
    # 60 s runs out at the first timed repeat of counting_qubits=3.
    ticks = itertools.count(0.0, 1.5)
    monkeypatch.setattr(harness, "Budget", lambda seconds: REAL_BUDGET(seconds, clock=lambda: next(ticks)))
    out = tmp_path / "budget.json"
    assert run_main(out) == harness.EXIT_BUDGET_EXHAUSTED

    payload = run_file.load(out, allow_incomplete=True)
    status = payload["status"]
    assert status["abort"]["reason"] == "budget"
    assert status["abort"]["exception_type"] == "BudgetExceeded"
    assert status["elapsed_s"] > payload["controls"]["time_budget_s"] == 60.0
    assert payload["configuration"]["counting_qubits"] == [2]
    partial = status["abort"]["incomplete_configuration"]
    assert (partial["method"], partial["counting_qubits"], partial["samples_s"]) == ("qae-cudaq", 3, [])


def test_interrupt_before_any_result_still_leaves_a_record(faked_arms, tmp_path):
    def interrupt(n_terms, calls):
        raise KeyboardInterrupt

    faked_arms["classical_fault"] = interrupt
    out = tmp_path / "interrupted.json"
    with pytest.raises(KeyboardInterrupt):
        run_main(out)

    payload = run_file.load(out, allow_incomplete=True)
    assert payload["runs"] == []
    assert payload["status"]["abort"]["reason"] == "interrupted"
    assert payload["status"]["abort"]["detail"] == "KeyboardInterrupt"
    partial = payload["status"]["abort"]["incomplete_configuration"]
    assert partial == {"method": "classical-cuda", "n_terms": 1, "samples_s": [], "outcomes": []}


def test_ctrl_c_is_honored_at_the_next_call_boundary(faked_arms, tmp_path):
    """The handler the harness installs defers the stop; the call in flight completes and is kept."""
    import signal

    before = signal.getsignal(signal.SIGINT)

    def press_ctrl_c(m, calls):
        if m == 3 and calls == 2:  # during the first timed repeat of counting_qubits=3
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)

    faked_arms["quantum_fault"] = press_ctrl_c
    out = tmp_path / "ctrl-c.json"
    with pytest.raises(KeyboardInterrupt, match="honored before quantum counting_qubits=3 repeat 1"):
        run_main(out)
    assert signal.getsignal(signal.SIGINT) is before

    payload = run_file.load(out, allow_incomplete=True)
    assert payload["status"]["abort"]["reason"] == "interrupted"
    assert payload["configuration"]["counting_qubits"] == [2]
    partial = payload["status"]["abort"]["incomplete_configuration"]
    assert (partial["counting_qubits"], len(partial["samples_s"])) == (3, 1)


def test_second_ctrl_c_forces_an_immediate_stop():
    budget = harness.Budget(60.0)
    budget.request_stop(2, None)
    assert budget.interrupt_requested
    with pytest.raises(KeyboardInterrupt, match="second interrupt"):
        budget.request_stop(2, None)


def test_abort_never_overwrites_a_competing_file_and_keeps_its_cause(faked_arms, tmp_path):
    out = tmp_path / "contested.json"

    def compete_then_fail(n_terms, calls):
        if calls == 5:
            out.write_bytes(b"other writer owns this path")
            raise RuntimeError("arm failed")

    faked_arms["classical_fault"] = compete_then_fail
    with pytest.raises(FileExistsError) as raised:
        run_main(out)
    assert isinstance(raised.value.__cause__, RuntimeError)
    assert out.read_bytes() == b"other writer owns this path"


def test_budget_checks_between_calls_only():
    ticks = iter([0.0, 5.0, 11.0])
    budget = harness.Budget(10.0, clock=lambda: next(ticks))
    budget.check("first call")  # 5 s elapsed of 10
    with pytest.raises(harness.BudgetExceeded, match="10 s exhausted before second call"):
        budget.check("second call")


def test_existing_archives_still_validate():
    for path in (
        "benchmarks/runs/2026-08-05-rtx5070-turbo.json",
        "benchmarks/runs/2026-09-06-1286200412954fb4a59cac02c27a06df.json",
    ):
        assert run_file.load(path)["schema"] != run_file.CURRENT_SCHEMA


# --------------------------------------------------------------------------
# Validator boundaries for the schema-5 status block
# --------------------------------------------------------------------------


@pytest.fixture
def aborted_run(current_run):
    """Artificial aborted record: classical arm done, quantum stopped at m=4."""
    p = current_run
    p["runs"] = p["runs"][:14]
    p["configuration"]["counting_qubits"] = [2, 3]
    p["status"].update(
        state="aborted",
        abort={
            "reason": "error",
            "exception_type": "RuntimeError",
            "detail": "injected",
            "incomplete_configuration": {
                "method": "qae-cudaq",
                "counting_qubits": 4,
                "samples_s": [0.5],
                "outcomes": [{"pi_estimate": 3.0}],
            },
        },
    )
    return p


def test_aborted_record_validates_only_when_asked(aborted_run):
    assert run_file.validate(aborted_run, allow_incomplete=True) is aborted_run
    with pytest.raises(ValueError, match="audit record"):
        run_file.validate(aborted_run)


def test_budget_abort_and_classical_stage_abort_validate(aborted_run):
    aborted_run["status"]["abort"]["reason"] = "budget"
    aborted_run["status"]["elapsed_s"] = 3600.5
    run_file.validate(aborted_run, allow_incomplete=True)

    early = copy.deepcopy(aborted_run)
    early["runs"] = early["runs"][:5]
    early["configuration"].update(classical_term_counts=early["configuration"]["classical_term_counts"][:5])
    early["configuration"]["counting_qubits"] = []
    stopped = early["status"]["planned"]["classical_term_counts"][5]
    early["status"]["abort"]["incomplete_configuration"] = {
        "method": "classical-cuda",
        "n_terms": stopped,
        "samples_s": [],
        "outcomes": [],
    }
    run_file.validate(early, allow_incomplete=True)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("status",), None),
        (("status", "state"), "partial"),
        (("status", "elapsed_s"), -1),
        (("controls", "time_budget_s"), 0),
        (("status", "planned"), None),
        (("status", "planned", "counting_qubits"), []),
        (("status", "planned", "counting_qubits"), [2, 2, 3, 4]),
        (("status", "planned", "counting_qubits"), [3, 2, 4]),
        (("status", "planned", "counting_qubits"), [2, 3]),
        (("status", "planned", "classical_term_counts"), [1, 2, 3, 4, 6, 8, 16, 64, 256, 1024, 4096, 16384, 65536]),
        (("status", "abort"), None),
        (("status", "abort", "reason"), "unknown"),
        (("status", "abort", "reason"), "budget"),
        (("status", "abort", "detail"), ""),
        (("status", "abort", "incomplete_configuration"), None),
        (("status", "abort", "incomplete_configuration", "counting_qubits"), 5),
        (("status", "abort", "incomplete_configuration", "method"), "classical-cuda"),
        (("status", "abort", "incomplete_configuration", "samples_s"), []),
        (("status", "abort", "incomplete_configuration", "samples_s", 0), 0),
        (("status", "abort", "incomplete_configuration", "outcomes", 0), "x"),
        (("status", "abort", "incomplete_configuration", "mean_s"), 0.5),
    ],
)
def test_corrupt_status_is_rejected(aborted_run, path, value):
    parent = aborted_run
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError):
        run_file.validate(aborted_run, allow_incomplete=True)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("status", "abort"), {"reason": "error"}),
        (("status", "planned", "counting_qubits"), list(range(2, 18))),
        (("runs",), []),
    ],
)
def test_complete_record_must_be_complete(current_run, path, value):
    parent = current_run
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError):
        run_file.validate(current_run)


def test_aborted_archive_is_plain_json(faked_arms, tmp_path):
    """The record must be readable without this repository's code."""

    def fail(n_terms, calls):
        if calls == 3:
            raise OSError("device lost")

    faked_arms["classical_fault"] = fail
    out = tmp_path / "plain.json"
    with pytest.raises(OSError, match="device lost"):
        run_main(out)
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["status"]["abort"]["detail"] == "device lost"
    assert raw["status"]["abort"]["incomplete_configuration"]["samples_s"] == [pytest.approx(0.001)]

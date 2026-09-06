"""P1-R3: the committed protocol and the analytic QAE reference.

Neither module touches a GPU or a simulator, so these are ordinary CPU unit
tests. The point of :mod:`quantum.quantization` is that it derives what QAE
must return *independently* of ``quantum.qae`` running — so the strongest test
available here is that its predictions match the real archived measurements,
which is asserted below against the committed run file.
"""

import json
import math
from pathlib import Path

import pytest

from benchmarks import protocol, run_file
from quantum import qae, quantization

ARCHIVE = Path("benchmarks/runs/2026-08-05-rtx5070-turbo.json")


# --------------------------------------------------------------------------
# The committed protocol
# --------------------------------------------------------------------------


def test_declaration_covers_every_required_element():
    """A protocol missing any of these cannot be said to be committed."""
    declared = protocol.declaration()
    assert declared["protocol_version"] == protocol.PROTOCOL_VERSION
    for key in ("warmup_policy", "exclusion_rule", "stopping_rule", "uncertainty_method"):
        assert declared[key].strip()
    assert set(declared["timing_boundaries"]) >= {"end_to_end", "execute"}


def test_timing_boundaries_match_the_phases_actually_measured():
    """``classical`` must not import ``benchmarks``, so agreement is asserted here."""
    from classical import cuda_kernel

    declared = set(protocol.TIMING_BOUNDARIES) - {"end_to_end"}
    assert declared == set(cuda_kernel.PHASE_NAMES)


def test_digest_is_stable_and_content_addressed():
    assert protocol.digest() == protocol.digest()
    assert protocol.digest() == protocol.digest_of(protocol.declaration())
    assert len(protocol.digest()) == 64


def test_digest_changes_when_any_declaration_changes():
    """Editing the protocol must be visible in every run file that followed it."""
    altered = protocol.declaration()
    altered["stopping_rule"] = altered["stopping_rule"] + " (amended)"
    assert protocol.digest_of(altered) != protocol.digest()


def test_uncertainty_reports_an_interval_around_the_mean():
    summary = protocol.uncertainty([0.10, 0.12, 0.11, 0.13, 0.10])
    assert summary["repeats"] == 5
    assert summary["min_s"] == 0.10
    assert summary["ci95_low_s"] < summary["mean_s"] < summary["ci95_high_s"]
    assert summary["sem_s"] == pytest.approx(summary["stdev_s"] / math.sqrt(5))
    assert summary["relative_stdev"] == pytest.approx(summary["stdev_s"] / summary["mean_s"])


def test_uncertainty_of_a_single_repeat_is_degenerate_not_invented():
    summary = protocol.uncertainty([0.25])
    assert summary["repeats"] == 1
    assert summary["stdev_s"] == summary["sem_s"] == 0.0
    assert summary["ci95_low_s"] == summary["ci95_high_s"] == 0.25


def test_uncertainty_of_all_zero_samples_does_not_divide_by_zero():
    """Degenerate but legal input; a zero mean must not produce a nan."""
    summary = protocol.uncertainty([0.0, 0.0])
    assert summary["relative_stdev"] == 0.0


@pytest.mark.parametrize("samples", [[], [float("nan")], [float("inf")], [-0.1]])
def test_uncertainty_rejects_unusable_samples(samples):
    with pytest.raises(ValueError):
        protocol.uncertainty(samples)


@pytest.mark.parametrize(
    ("degrees_of_freedom", "expected"),
    [(1, 12.706), (4, 2.776), (22, 2.086), (120, 1.980)],
)
def test_t_critical_uses_the_table_conservatively(degrees_of_freedom, expected):
    """Between tabulated points it must overstate the interval, never understate."""
    assert protocol.t_critical(degrees_of_freedom) == expected


def test_t_critical_falls_back_to_normal_beyond_the_table():
    assert protocol.t_critical(10_000) == 1.960


def test_t_critical_rejects_zero_degrees_of_freedom():
    with pytest.raises(ValueError, match="degree of freedom"):
        protocol.t_critical(0)


# --------------------------------------------------------------------------
# Analytic QAE quantization
# --------------------------------------------------------------------------


def test_the_plateau_is_derived_and_finite():
    """P1-R2 corrected 'improves no further' to a bounded claim; prove the bound."""
    assert quantization.plateau_bounds(12) == (10, 17)
    assert quantization.ideal_estimate(17) == quantization.ideal_estimate(10)
    assert quantization.ideal_estimate(18) != quantization.ideal_estimate(17)


def test_plateau_of_a_single_member_returns_itself():
    assert quantization.plateau_bounds(2) == (2, 2)


def test_plateau_search_limit_must_not_precede_the_request():
    with pytest.raises(ValueError, match="search_limit"):
        quantization.plateau_bounds(12, search_limit=4)


def test_the_error_floor_matches_the_documented_value():
    """~3.1e-5 in pi, from 355/1024 — a property of this amplitude, not of QAE."""
    assert quantization.ideal_outcome(10) == 355
    assert quantization.quantization_error(12) == pytest.approx(3.1161815e-05, rel=1e-6)
    assert quantization.relative_quantization_error(12) == pytest.approx(quantization.quantization_error(12) / math.pi)


def test_relative_error_is_the_quantity_comparable_to_the_float_floor():
    """Absolute and relative error are routinely conflated; keep them distinct."""
    assert quantization.relative_quantization_error(12) > quantization.DOUBLE_PRECISION_FLOOR
    assert quantization.relative_quantization_error(12) != quantization.quantization_error(12)


def test_conjugate_outcomes_encode_the_same_amplitude():
    """Grover's two eigenphases: 2^m - y recovers an identical estimate."""
    for m in (4, 6, 10):
        ideal = quantization.ideal_outcome(m)
        conjugate = quantization.conjugate_outcome(ideal, m)
        assert conjugate != ideal
        assert qae.amplitude_from_outcome(conjugate, m) == pytest.approx(qae.amplitude_from_outcome(ideal, m))
        assert quantization.agrees_with_theory(conjugate, m)


def test_zero_is_its_own_conjugate():
    assert quantization.conjugate_outcome(0, 4) == 0


def test_a_wrong_outcome_does_not_agree_with_theory():
    assert not quantization.agrees_with_theory(quantization.ideal_outcome(10) + 3, 10)


def test_ideal_distribution_is_normalized():
    for m in (2, 4, 8):
        assert math.fsum(quantization.ideal_distribution(m).values()) == pytest.approx(1.0, abs=1e-12)


def test_the_ideal_peak_carries_most_of_the_weight():
    distribution = quantization.ideal_distribution(10)
    ideal = quantization.ideal_outcome(10)
    conjugate = quantization.conjugate_outcome(ideal, 10)
    assert distribution[ideal] + distribution[conjugate] > 0.99


def test_outcome_probability_is_exact_on_a_grid_point():
    """When the phase lands exactly on the grid the kernel must return 1, not nan."""
    assert quantization._kernel(0.0, 16) == 1.0


def test_total_variation_is_zero_against_the_ideal_distribution_itself():
    ideal = quantization.ideal_distribution(4)
    counts = {format(y, "04b"): round(p * 10**9) for y, p in ideal.items()}
    assert quantization.total_variation(counts, 4) < 1e-8


def test_total_variation_is_one_for_disjoint_support():
    """A sample entirely off the ideal support is maximally distant."""
    distance = quantization.total_variation({"0000": 100}, 4)
    assert 0.0 < distance <= 1.0


def test_sampling_tolerance_shrinks_with_more_shots():
    assert quantization.sampling_tolerance(6, 40_000) < quantization.sampling_tolerance(6, 400)


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (lambda: quantization.ideal_outcome(0), "counting qubit"),
        (lambda: quantization.outcome_probability(16, 4), "outcome must lie"),
        (lambda: quantization.conjugate_outcome(-1, 4), "outcome must lie"),
        (lambda: quantization.ideal_distribution(21), "refusing to enumerate"),
        (lambda: quantization.total_variation({"0000": 0}, 4), "at least one shot"),
        (lambda: quantization.total_variation({"0000": -1, "0001": 5}, 4), "not be negative"),
        (lambda: quantization.total_variation({"000": 5}, 4), "is not 4 bits"),
        (lambda: quantization.total_variation({"00x0": 5}, 4), "is not 4 bits"),
        (lambda: quantization.sampling_tolerance(4, 0), "at least 1 shot"),
    ],
)
def test_quantization_rejects_impossible_inputs(call, match):
    with pytest.raises(ValueError, match=match):
        call()


# --------------------------------------------------------------------------
# The strongest available check: theory against the real archive
# --------------------------------------------------------------------------


def test_every_archived_qae_outcome_agrees_with_closed_form_theory():
    """15 measured rows, zero free parameters, no simulator involved here.

    Eight of them landed on the conjugate peak rather than the nearest grid
    point. That is expected — both peaks carry equal weight — and is why
    agreement is checked on the recovered estimate, not the raw integer.
    """
    payload = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    rows = [row for row in payload["runs"] if row["method"] == "qae-cudaq"]
    assert len(rows) == 15

    conjugates = 0
    for row in rows:
        m, outcome = row["counting_qubits"], row["outcome"]
        assert quantization.agrees_with_theory(outcome, m), f"m={m} disagrees with theory"
        assert row["pi_estimate"] == pytest.approx(quantization.ideal_estimate(m), abs=1e-12)
        conjugates += outcome != quantization.ideal_outcome(m)
    assert conjugates == 8


def test_the_archive_still_validates_under_the_current_reader():
    """Schema 4 must not orphan the only measured run this repo has."""
    assert run_file.load(ARCHIVE)["schema"] == run_file.LEGACY_SCHEMA


def test_cli_skips_review_sidecars_that_share_the_json_suffix(tmp_path, capsys):
    """CI expands benchmarks/runs/*.json, which now also matches a review record.

    The sidecar has its own schema and its own validator (analysis.review), so
    handing it to the run-file validator must skip it rather than reject it —
    otherwise adding the first reviewed findings document breaks CI.
    """
    sidecar = tmp_path / "run-findings.review.json"
    sidecar.write_text('{"schema": "q1729/findings-review/1"}', encoding="utf-8")

    assert run_file.main([str(sidecar)]) == 0
    assert "skipped" in capsys.readouterr().out


def test_cli_still_validates_real_run_files_alongside_a_sidecar(tmp_path, capsys):
    """Skipping the sidecar must not skip the archive it sits next to."""
    sidecar = tmp_path / "x.review.json"
    sidecar.write_text("{}", encoding="utf-8")

    assert run_file.main([str(sidecar), str(ARCHIVE)]) == 0
    out = capsys.readouterr().out
    assert "skipped" in out
    assert f"validated {ARCHIVE}" in out


def test_cli_rejects_a_malformed_run_file(tmp_path):
    """The skip is keyed on the sidecar suffix only, not on being unparseable."""
    bad = tmp_path / "broken.json"
    bad.write_text('{"schema": "q1729/run-file/4"}', encoding="utf-8")
    with pytest.raises(ValueError):
        run_file.main([str(bad)])

"""Findings reviews bind every cited archive; derived QAE fields are recomputed."""

import json
import shutil
from pathlib import Path

import pytest

from analysis import review
from benchmarks import run_file
from quantum import quantization

RUNS = Path("benchmarks/runs")
AUGUST = "2026-08-05-rtx5070-turbo.json"
SEPTEMBER = "2026-09-06-1286200412954fb4a59cac02c27a06df"


def reformat(path: Path) -> None:
    """Change a run file's bytes while keeping it a valid, identical record."""
    path.write_text(json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=1), encoding="utf-8")


@pytest.fixture
def approved_comparison(tmp_path):
    """Copy the approved 2026-09-06 comparison and both archives it cites."""
    for name in (AUGUST, f"{SEPTEMBER}.json", f"{SEPTEMBER}-findings.md", f"{SEPTEMBER}-findings.review.json"):
        shutil.copyfile(RUNS / name, tmp_path / name)
    return tmp_path


def test_approved_comparison_is_bound_to_both_cited_archives(approved_comparison):
    review.check_archive(approved_comparison)
    assert review.cited_runs(approved_comparison / f"{SEPTEMBER}-findings.md") == {AUGUST, f"{SEPTEMBER}.json"}


@pytest.mark.parametrize("altered", [AUGUST, f"{SEPTEMBER}.json"])
def test_altering_either_cited_archive_invalidates_the_review(approved_comparison, altered):
    reformat(approved_comparison / altered)
    run_file.load(approved_comparison / altered)  # still a valid run file...
    with pytest.raises(ValueError, match="stale"):  # ...but no longer the one that was reviewed
        review.check_archive(approved_comparison)


def test_legacy_review_cannot_leave_a_citation_unbound(approved_comparison):
    draft = approved_comparison / f"{SEPTEMBER}-findings.md"
    renamed = approved_comparison / "renamed-findings.md"
    draft.rename(renamed)
    (approved_comparison / f"{SEPTEMBER}-findings.review.json").rename(renamed.with_suffix(".review.json"))
    with pytest.raises(ValueError, match="does not bind"):
        review.check_archive(approved_comparison)


@pytest.fixture
def comparison(tmp_path, measured_run):
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    for path in (first, second):
        path.write_text(json.dumps(measured_run), encoding="utf-8")
    draft = tmp_path / "compare-findings.md"
    draft.write_text("# Compare\n\n`first.json` against `second.json`: no difference.", encoding="utf-8")
    return first, second, draft


def approve(record: Path) -> None:
    data = json.loads(record.read_text(encoding="utf-8"))
    data.update(reviewer="Test reviewer", status="approved")
    for paragraph in data["paragraphs"]:
        paragraph.update(assessment="Test-only review", evidence="Test source locator")
    record.write_text(json.dumps(data), encoding="utf-8")


def test_new_reviews_bind_every_citation(comparison):
    first, second, draft = comparison
    record = draft.with_suffix(".review.json")
    with pytest.raises(ValueError, match=r"cites \['second.json'\]"):
        review.main([str(draft), "--run", str(first), "--review", str(record)])
    assert not record.exists()

    assert review.main([str(draft), "--run", str(first), "--run", str(second), "--review", str(record)]) == 0
    data = json.loads(record.read_text(encoding="utf-8"))
    assert data["schema"] == review.SCHEMA
    assert [source["run_file"] for source in data["sources"]] == ["first.json", "second.json"]
    approve(record)
    review.check_archive(draft.parent)

    reformat(second)
    with pytest.raises(ValueError, match="stale"):
        review.check_archive(draft.parent)


@pytest.mark.parametrize(
    "sources",
    [[], None, ["first.json"], [{"run_file": "../first.json", "sha256": "x"}], [{"run_file": "first.json"}] * 2],
)
def test_malformed_review_sources_fail(comparison, sources):
    first, second, draft = comparison
    record = draft.with_suffix(".review.json")
    review.main([str(draft), "--run", str(first), "--run", str(second), "--review", str(record)])
    data = json.loads(record.read_text(encoding="utf-8"))
    data["sources"] = sources
    record.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        review.validate(draft, record)


def test_review_requires_a_source_and_a_known_schema(comparison):
    first, second, draft = comparison
    with pytest.raises(ValueError, match="at least one source"):
        review.template([], draft)
    record = draft.with_suffix(".review.json")
    record.write_text(json.dumps({"schema": "q1729/findings-review/99"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown review schema"):
        review.validate(draft, record)


# --------------------------------------------------------------------------
# Derived QAE diagnostics
# --------------------------------------------------------------------------


def test_conjugate_landing_means_the_conjugate_peak_only():
    m = 4
    ideal = quantization.ideal_outcome(m)
    conjugate = quantization.conjugate_outcome(ideal, m)
    elsewhere = next(y for y in range(2**m) if y not in (ideal, conjugate))
    counts = {format(ideal, "04b"): 10}
    assert quantization.report(m, ideal, counts, 10)["landed_on_conjugate"] is False
    assert quantization.report(m, conjugate, counts, 10)["landed_on_conjugate"] is True
    wrong = quantization.report(m, elsewhere, counts, 10)
    # A wrong outcome is a disagreement with theory, not a conjugate landing.
    assert (wrong["landed_on_conjugate"], wrong["agrees_with_theory"]) == (False, False)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("ideal_outcome", "+1"),
        ("conjugate_outcome", 0),
        ("landed_on_conjugate", "flip"),
        ("agrees_with_theory", False),
        ("agrees_with_theory", 1),
        ("quantization_error", 1.0),
        ("total_variation", 0.5),
        ("sampling_tolerance", "0.1"),
        ("plateau_first_m", 3),
        ("interpretation", "edited"),
        ("unexpected", 1),
    ],
)
def test_corrupt_quantization_fields_fail(current_run, key, value):
    block = current_run["runs"][12]["quantization"]
    if value == "+1":
        value = block[key] + 1
    elif value == "flip":
        value = not block[key]
    block[key] = value
    with pytest.raises(ValueError, match="quantization"):
        run_file.validate(current_run)


def test_quantization_block_and_integer_outcome_are_required(current_run):
    del current_run["runs"][13]["quantization"]
    with pytest.raises(ValueError, match="quantization block"):
        run_file.validate(current_run)
    current_run["runs"][13]["quantization"] = current_run["runs"][14]["quantization"]
    with pytest.raises(ValueError, match="quantization"):
        run_file.validate(current_run)

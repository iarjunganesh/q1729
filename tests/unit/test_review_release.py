import json
import subprocess
from pathlib import Path

import pytest

from analysis import review
from scripts import release_check


@pytest.fixture
def findings(tmp_path, measured_run):
    run = tmp_path / "run.json"
    run.write_text(json.dumps(measured_run), encoding="utf-8")
    draft = tmp_path / "findings.md"
    draft.write_text("# Findings\n\nAn observed result.\n\nA qualified interpretation.", encoding="utf-8")
    record = tmp_path / "findings.review.json"
    assert review.main([str(draft), "--run", str(run), "--review", str(record)]) == 0
    return draft, record


def approve(record):
    data = json.loads(record.read_text())
    data.update(reviewer="Test reviewer", status="approved")
    for paragraph in data["paragraphs"]:
        paragraph.update(assessment="Test-only review", evidence="Test source locator and reasoning")
    record.write_text(json.dumps(data))


def test_review_requires_human_action_and_is_bound_to_exact_data(findings):
    draft, record = findings
    with pytest.raises(ValueError):
        review.validate(draft, record)
    approve(record)
    assert review.main([str(draft), "--review", str(record)]) == 0
    assert review.main(["--archive", str(draft.parent)]) == 0
    draft.write_text(draft.read_text() + "\n\nAn unreviewed claim.")
    with pytest.raises(ValueError, match="stale"):
        review.check_archive(draft.parent)


@pytest.mark.parametrize("change", ["pending", "missing", "changed", "evidence", "source"])
def test_incomplete_or_stale_reviews_fail(findings, change):
    draft, record = findings
    approve(record)
    data = json.loads(record.read_text())
    if change == "pending":
        data["status"] = "pending"
    elif change == "missing":
        data["paragraphs"].pop()
    elif change == "changed":
        data["paragraphs"][0]["text"] = "different"
    elif change == "evidence":
        data["paragraphs"][0]["evidence"] = ""
    else:
        run = draft.parent / "run.json"
        run.write_text(run.read_text() + "\n")
    record.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        review.validate(draft, record)


def test_historical_findings_read_without_relabeling():
    assert review.main(["--archive", "benchmarks/runs"]) == 0


@pytest.fixture
def release_repo(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.2.3"\n')
    (tmp_path / "CHANGELOG.md").write_text("## [1.2.3] - date\n\nReal changes.\n\n## [1.2.2]\nOlder.")
    calls = []

    def output(cmd, **kwargs):
        calls.append(cmd)
        return "a" * 40 + "\n"

    def run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(release_check.subprocess, "check_output", output)
    monkeypatch.setattr(release_check.subprocess, "run", run)
    return tmp_path, calls


def test_release_requires_matching_tag_and_main_ancestry(release_repo):
    root, calls = release_repo
    out = root / "notes.md"
    assert release_check.main(["v1.2.3", "--root", str(root), "--out", str(out)]) == 0
    assert out.read_text() == "Real changes.\n"
    assert calls[-1] == ["git", "merge-base", "--is-ancestor", "a" * 40, "origin/main"]


@pytest.mark.parametrize("tag", ["v1.2", "v1.2.3-rc1", "v1.2.4"])
def test_invalid_or_mismatched_tag_rejected(release_repo, tag):
    with pytest.raises(ValueError):
        release_check.check(release_repo[0], tag)


@pytest.mark.parametrize("notes", ["## [1.2.4]\nWrong", "## [1.2.3]\n", "## [1.2.3]\nOne\n## [1.2.3]\nTwo"])
def test_missing_empty_or_ambiguous_release_notes_fail(release_repo, notes):
    root, _ = release_repo
    (root / "CHANGELOG.md").write_text(notes)
    with pytest.raises(ValueError):
        release_check.check(root, "v1.2.3")


def test_wrong_checkout_and_orphan_commit_fail(release_repo, monkeypatch):
    root, _ = release_repo
    monkeypatch.setattr(
        release_check.subprocess, "check_output", lambda cmd, **kwargs: "a" if cmd[-1] == "HEAD" else "b"
    )
    with pytest.raises(ValueError, match="checkout"):
        release_check.check(root, "v1.2.3")
    monkeypatch.setattr(release_check.subprocess, "check_output", lambda *args, **kwargs: "a")

    def orphan(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(release_check.subprocess, "run", orphan)
    with pytest.raises(subprocess.CalledProcessError):
        release_check.check(root, "v1.2.3")


def test_release_workflow_depends_on_reusable_quality_gate():
    workflow = Path(".github/workflows/release.yml").read_text()
    assert "uses: ./.github/workflows/ci.yml" in workflow
    assert "needs: [preflight, quality]" in workflow
    assert "fetch-depth: 0" in workflow
    assert "workflow_call:" in Path(".github/workflows/ci.yml").read_text()

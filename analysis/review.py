"""Bind human findings review to exact draft paragraphs and every cited source's hash."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from benchmarks import archive, run_file

#: Written by :func:`template`: binds every run archive the draft cites.
SCHEMA = "q1729/findings-review/2"

#: Read-only: binds a single run archive (``run_file``/``run_sha256``).
LEGACY_SCHEMA = "q1729/findings-review/1"

# Historical pre-sidecar documents; changing either requires a new review.
LEGACY_FINDINGS = {
    "2026-08-05-rtx5070-turbo-findings.md": "67a7ce0dc4590466967cbf614abed68aaea662ae4974eb1cd744d1d0a58b1e6a",
    "2026-08-05-rtx5070-turbo-reviewed.md": "ce4d1cf61189172bf508cee62abe57ffa84ff0f54a0e7bf7afd054df2d15e56e",
}

#: Schema-1 reviews hash only their own run file. Where an approved draft also
#: cites another archive, that archive's hash when it was approved is pinned
#: here, so altering it invalidates the approval — without anyone re-approving
#: on the reviewer's behalf. The 2026-08-05 archive is unchanged since its only
#: commit (f88a926, 2026-08-05), before the 2026-09-06 review was approved.
LEGACY_CITED_SOURCES = {
    "2026-09-06-1286200412954fb4a59cac02c27a06df-findings.md": {
        "2026-08-05-rtx5070-turbo.json": "ea97c06505153e4d8971320a19b19739a2aa67328df34545f595814c5eaa396d",
    },
}


def digest(path: Path) -> str:
    """Normalize checkout line endings for portable text-artifact identity."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def paragraphs(path: Path) -> list[str]:
    return [block.strip() for block in path.read_text(encoding="utf-8").split("\n\n") if block.strip()]


def cited_runs(draft: Path) -> set[str]:
    """Adjacent run archives the draft names — every one needs a bound hash."""
    content = draft.read_text(encoding="utf-8")
    return {
        path.name
        for path in draft.parent.glob("*.json")
        if not path.name.endswith(run_file.SIDECAR_SUFFIX) and path.name in content
    }


def source_name(name: object) -> str:
    run_file.text(name, "review source")
    text = str(name)
    run_file.require(Path(text).name == text and text.endswith(".json"), "review source must be an adjacent run JSON")
    return text


def template(runs: list[Path], draft: Path) -> dict:
    """A pending review binding the draft and every run archive it cites."""
    run_file.require(bool(runs), "a review needs at least one source run")
    names = [run.name for run in runs]
    run_file.require(len(set(names)) == len(names), "duplicate review source")
    for run in runs:
        run_file.require(run.parent.resolve() == draft.parent.resolve(), "source and draft must be adjacent")
        run_file.load(run)
    unbound = cited_runs(draft) - set(names)
    run_file.require(not unbound, f"draft cites {sorted(unbound)} but the review does not bind it")
    blocks = paragraphs(draft)
    run_file.require(bool(blocks), "draft must contain text")
    return {
        "schema": SCHEMA,
        "sources": [{"run_file": run.name, "sha256": digest(run)} for run in runs],
        "draft_sha256": digest(draft),
        "reviewer": "",
        "status": "pending",
        "paragraphs": [{"text": block, "assessment": "", "evidence": ""} for block in blocks],
    }


def recorded_sources(review: dict, draft: Path) -> list[dict]:
    """The (name, hash) pairs a review binds, from either schema."""
    if review.get("schema") == LEGACY_SCHEMA:
        pinned = LEGACY_CITED_SOURCES.get(draft.name, {})
        own = {"run_file": source_name(review.get("run_file")), "sha256": review.get("run_sha256")}
        return [own] + [{"run_file": name, "sha256": sha} for name, sha in pinned.items()]
    sources: Any = review.get("sources")
    run_file.require(isinstance(sources, list) and bool(sources), "review sources must be a nonempty array")
    for source in sources:
        run_file.require(isinstance(source, dict), "review source must be an object")
        source_name(source.get("run_file"))
    return sources


def validate(draft: Path, review_path: Path) -> None:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    run_file.require(isinstance(review, dict), "review must be an object")
    run_file.require(review.get("schema") in (SCHEMA, LEGACY_SCHEMA), "unknown review schema")
    sources = recorded_sources(review, draft)
    expected = template([draft.parent / source["run_file"] for source in sources], draft)
    for source, current in zip(sources, expected["sources"], strict=True):
        run_file.require(source.get("sha256") == current["sha256"], "review is stale: source or draft changed")
    run_file.require(review.get("draft_sha256") == expected["draft_sha256"], "review is stale: source or draft changed")
    run_file.text(review.get("reviewer"), "human reviewer")
    run_file.require(review.get("status") == "approved", "findings review is pending")
    entries = review.get("paragraphs")
    run_file.require(
        isinstance(entries, list) and len(entries) == len(expected["paragraphs"]), "every paragraph needs review"
    )
    for entry, original in zip(entries, expected["paragraphs"], strict=True):
        run_file.require(
            isinstance(entry, dict) and entry.get("text") == original["text"], "reviewed paragraph mismatch"
        )
        for key in ("assessment", "evidence"):
            run_file.text(entry.get(key), key)


def check_archive(directory: Path) -> None:
    run_file.require(directory.is_dir(), "archive directory missing")
    for draft in directory.glob("*.md"):
        if LEGACY_FINDINGS.get(draft.name) == digest(draft):
            continue
        validate(draft, draft.with_suffix(".review.json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, nargs="?")
    parser.add_argument("--archive", type=Path)
    parser.add_argument(
        "--run", type=Path, action="append", help="create a pending template binding this source (repeat per citation)"
    )
    parser.add_argument("--review", type=Path)
    args = parser.parse_args(argv)
    if args.archive:
        check_archive(args.archive)
        return 0
    run_file.require(args.draft is not None and args.review is not None, "draft and --review are required")
    if args.run:
        data = (json.dumps(template(args.run, args.draft), indent=2) + "\n").encode()
        with archive.create_outputs([args.review]) as streams:
            streams[0].write(data)
    else:
        validate(args.draft, args.review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

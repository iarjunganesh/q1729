"""Bind human findings review to exact draft paragraphs and source data hashes."""

import argparse
import hashlib
import json
from pathlib import Path

from benchmarks import archive, run_file

# Historical pre-sidecar documents; changing either requires a new review.
LEGACY_FINDINGS = {
    "2026-08-05-rtx5070-turbo-findings.md": "67a7ce0dc4590466967cbf614abed68aaea662ae4974eb1cd744d1d0a58b1e6a",
    "2026-08-05-rtx5070-turbo-reviewed.md": "ce4d1cf61189172bf508cee62abe57ffa84ff0f54a0e7bf7afd054df2d15e56e",
}


def digest(path: Path) -> str:
    """Normalize checkout line endings for portable text-artifact identity."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def paragraphs(path: Path) -> list[str]:
    return [block.strip() for block in path.read_text(encoding="utf-8").split("\n\n") if block.strip()]


def template(run: Path, draft: Path) -> dict:
    run_file.require(run.parent.resolve() == draft.parent.resolve(), "source and draft must be adjacent")
    run_file.load(run)
    blocks = paragraphs(draft)
    run_file.require(bool(blocks), "draft must contain text")
    return {
        "schema": "q1729/findings-review/1",
        "run_file": run.name,
        "run_sha256": digest(run),
        "draft_sha256": digest(draft),
        "reviewer": "",
        "status": "pending",
        "paragraphs": [{"text": block, "assessment": "", "evidence": ""} for block in blocks],
    }


def validate(draft: Path, review_path: Path) -> None:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    run_file.require(isinstance(review, dict), "review must be an object")
    run_file.require(review.get("schema") == "q1729/findings-review/1", "unknown review schema")
    run_file.text(review.get("run_file"), "review run_file")
    name = review["run_file"]
    run_file.require(Path(name).name == name and name.endswith(".json"), "review source must be an adjacent run JSON")
    expected = template(draft.parent / name, draft)
    for key in ("run_sha256", "draft_sha256"):
        run_file.require(review.get(key) == expected[key], "review is stale: source or draft changed")
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
    parser.add_argument("--run", type=Path, help="create a pending template for this source")
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

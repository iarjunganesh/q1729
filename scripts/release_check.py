"""Fail closed on tag/version/notes/ancestry mismatches before release publication."""

import argparse
import re
import subprocess
import tomllib
from pathlib import Path


def check(root: Path, tag: str) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("release tag must be vMAJOR.MINOR.PATCH")
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if tag != f"v{version}":
        raise ValueError("tag and project version disagree")
    lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    headings = [i for i, line in enumerate(lines) if re.match(rf"^## \[{re.escape(version)}\](?:\s|$)", line)]
    if len(headings) != 1:
        raise ValueError("exactly one matching changelog section required")
    start = headings[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## [")), len(lines))
    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise ValueError("release notes are empty")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    tagged = subprocess.check_output(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=root, text=True).strip()
    if tagged != head:
        raise ValueError("checkout does not match the tagged commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", head, "origin/main"], cwd=root, check=True)
    return notes + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=Path("release_notes.md"))
    args = parser.parse_args(argv)
    args.out.write_text(check(args.root, args.tag), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

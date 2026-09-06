# Reviewing findings before publication

NIM output is an unreviewed draft. A human reviewer must assess every numerical
and causal claim against the run data, method and limitations. Agents must not
fill an approval record on the human's behalf. Record corrections in a revised
draft; do not rewrite measured JSON. The narrator CLI labels its output unreviewed.

Keep the measured JSON and draft in the same directory. Generate a pending
record, then have the reviewer complete it:

```bash
python -m analysis.review benchmarks/runs/new-findings.md --run benchmarks/runs/new.json --review benchmarks/runs/new-findings.review.json
```

The record includes normalized text SHA-256 hashes and every draft paragraph.
The human fills `reviewer`, gives each paragraph an `assessment` and `evidence`
(row/field locator or a relevant method/reference with reasoning), and sets
`status` to `approved` only when the whole document is supported. Mark headings
or non-claim paragraphs as such with a reason. Unsupported causal claims must
be removed, qualified or supported by appropriate evidence; timing alone is not
a profiler. No new reviewer approvals were issued during P1-R2 implementation.

```bash
python -m analysis.review benchmarks/runs/new-findings.md --review benchmarks/runs/new-findings.review.json
python -m analysis.review --archive benchmarks/runs
```

CI requires a valid adjacent `.review.json` for each new Markdown document in
the run archive. Missing, pending, incomplete or stale review records fail.
Changing the draft or source invalidates the approval hashes. Existing review
files are not overwritten when generating a template; use a new path while
revising. The two historical pre-sidecar documents are accepted at fixed hashes;
they retain their existing historical/reviewed status without invented approvals.

These checks enforce a recorded review process. They cannot establish a
reviewer's identity, the quality of their reasoning or the truth of every claim.

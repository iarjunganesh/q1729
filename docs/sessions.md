# Session log

Dated record of what each work session changed and what it was verified
against. Kept per `AGENTS.md`'s mandatory session-synchronization discipline
— append one entry before handing off, don't rewrite prior entries.

## 2026-07-21 — Repo hygiene bar-raise: AGENTS.md, 100% coverage floor, theme-aware brand/diagram assets

**What changed:**

- Added `AGENTS.md`: cross-tool discipline for keeping version numbers,
  status-bearing docs, and coverage claims honest before every commit to
  `main` and every tag. `CLAUDE.md` now points to it instead of duplicating
  it.
- Raised the CI coverage gate from a 95%-buffered floor to a literal
  `--cov-fail-under=100` (`.github/workflows/ci.yml`, `codecov.yml`) — real
  measured coverage on the cudaq-capable host (WSL2, verified this session)
  was already 100%, so this removes the buffer rather than chasing a new
  number.
- Split CI into four jobs: `lint` (ruff), `typecheck` (mypy, newly wired
  in — found and fixed one real finding in `analysis/narrator.py`'s
  `sys.stdout.reconfigure` typeshed gap), `tests` (pytest + coverage), and
  `docs` (required-file + stale-marker hygiene check).
- Bumped GitHub Actions to their current latest major tags, verified against
  each action's actual published tags rather than assumed:
  `actions/checkout@v4→v7`, `actions/setup-python@v5→v7`,
  `codecov/codecov-action@v5→v7`, `softprops/action-gh-release@v2→v3`.
- Added theme-aware, code-generated SVG assets, modeled on (not copied from)
  a sibling hackathon repo's pattern: `assets/architecture/` (Mermaid source
  + light/dark renders of the existing pipeline diagram, backgrounds matched
  to GitHub's own light/dark README canvas) and `assets/brand/` (an original
  q1729 hero banner — wordmark, the taxicab-number identity, a
  pipeline-at-a-glance panel reusing the diagram's own palette). README now
  embeds both via `<picture>` + `prefers-color-scheme`.
- Added `benchmarks/README.md` as an explicit placeholder for the real
  measured run files roadmap Phase 1 will produce.
- Added `docs/adr/004-repo-hygiene-and-agent-sync.md` recording this batch as
  a decision, per the project's own ADR convention.
- Swept every "95%"/"CI gates at 95%" mention across README, CLAUDE.md,
  CHANGELOG.md, CONTRIBUTING.md, docs/setup.md, docs/roadmap.md to say 100%.

**Why:** requested explicitly, ahead of starting roadmap Phase 1 work, to
raise the repo's engineering-hygiene bar to match sibling-repo standards
before adding the CUDA kernel / QAE / real-benchmark surface area.

**Verified against:** `ruff check .` clean; `mypy classical quantum
analysis` clean; `pytest tests --cov --cov-fail-under=100` green at 100% on
both Windows (`quantum/backend.py` under-counts there as documented — see
CLAUDE.md) and WSL2 (full 100%, `cudaq` real target); generated SVGs
validated as well-formed XML and spot-checked visually via a headless-Edge
screenshot (not committed).

## 2026-07-21 (follow-up round) — Fixed the CLAUDE.md/AGENTS.md split, README badges, SECURITY.md, no-AI-contributor rule

**What changed:**

- **Corrected a real bug from the same-day earlier round**: `CLAUDE.md`'s
  "See AGENTS.md for..." was a prose sentence, not an import — Claude Code
  auto-loads only `CLAUDE.md` and never reads `AGENTS.md` on its own
  (verified against `code.claude.com/docs/en/memory`, which documents the
  `@AGENTS.md` import as the correct pattern). Fixed: `CLAUDE.md` is now a
  literal `@AGENTS.md` import plus an HTML-comment explanation (stripped
  before injection); all content that used to live only in `CLAUDE.md` —
  key commands, two-host workflow, non-negotiable constraints,
  style/conventions — merged into `AGENTS.md`. Recorded as a dated amendment
  to [ADR 004](adr/004-repo-hygiene-and-agent-sync.md) rather than editing
  the original decision text away.
- Added an `AGENTS.md` Git History rule: never add an AI co-author trailer
  to a commit or otherwise put an agent in the GitHub Contributors graph —
  explicit owner preference, applies to every agent, not just Claude Code.
- Updated `SECURITY.md`: documented CI's permission scoping
  (`contents: read` workflow-wide, `contents: write` scoped only to the
  release job) and the local-only Node/`@mermaid-js/mermaid-cli` build
  dependency introduced by `assets/architecture/` and `assets/brand/`
  (never runs in CI, never touches a secret).
- Reworked README badges: Release badge is now a live
  `img.shields.io/github/v/release/...` badge instead of static "latest"
  text (verified it resolves, HTTP 200); added CUDA-QX (verified
  `github.com/NVIDIA/cudaqx` is the real, active repo), mypy, and pytest
  badges so every technology named in the Stack section has one; grouped
  into four HTML-comment-labeled rows instead of unlabeled ones.

**Why:** the owner asked, before greenlighting Phase 1: (1) whether
`CLAUDE.md` was still needed now that `AGENTS.md` exists, (2) whether
`SECURITY.md` needed updating, (3) for a more complete/better-organized
README badge set, and (4) for an explicit no-AI-contributor commit rule —
then asked for a fresh deep audit before giving the go-ahead.

**Verified against:** re-ran `ruff check .`, `mypy classical quantum
analysis`, and `pytest tests --cov --cov-report=term-missing` on Windows
(all clean, coverage unchanged at 97%/100% split as before — no `.py` files
changed this round); re-ran the CI docs-hygiene grep dry run (clean); curled
the three new/changed badge URLs and the CUDA-QX repo link directly (all
HTTP 200); confirmed via `gh repo view` / `gh release list` that
`iarjunganesh/q1729` is public with a real `v0.1.0` release, so the dynamic
release badge has something real to show.

## 2026-07-22 — GPU badge links, then a real badge-correctness bug fix

**What changed:**

- Local GPU / Cloud GPU badges now link to the NVIDIA product pages
  (RTX 5070 family, H100) instead of the ADR docs, per owner request. Fixed
  the RTX link's locale to `en-us` (owner initially supplied `sv-se`, then
  asked for `us-en` to match the H100 link — verified `us-en` 404s on
  NVIDIA's site and `en-us` is the real code, so both badges use `en-us`).
- **Found and fixed a real bug**: fetched every badge's actual rendered SVG
  text (not just the HTTP status) and compared byte-for-byte against
  `drift`'s working badges. `Ruff`, `mypy`, and `pytest` had label/message in
  the wrong order — `Ruff` had been backwards (`lint | Ruff`) since before
  this session's hygiene pass even started, and the `mypy`/`pytest` badges I
  added inherited the same inversion instead of drift's `Name-Version`
  convention. All three fixed and re-verified by fetching the rendered SVG
  text again, not just trusting the URL syntax.
- The `Ruff` badge's "lint + format" claim was false when I first wrote it —
  `ruff format --check .` failed on 2 files. Fixed for real rather than just
  changing the label: ran `ruff format .` (whitespace-only changes, no logic
  change, re-verified tests still pass), added `ruff format --check .` as a
  real CI step in the `lint` job and to `make lint`.
- Answered a direct question rather than changing anything: q1729 doesn't
  use FastAPI and shouldn't — there's no API surface to expose (no frontend,
  no live app, per the earlier Vercel/Railway/HF Spaces discussion). No
  FastAPI badge or dependency added.

**Why:** the owner flagged that badges looked wrong ("nonsense text") and
asked me to check against `drift` carefully rather than re-guess.

**Verified against:** fetched and grep'd the actual `<text>` content of
every badge SVG in the README (not just HTTP status) before and after the
fix; `ruff check .`, `ruff format --check .`, `mypy classical quantum
analysis`, and `pytest --cov --cov-fail-under=100` all green on both Windows
(97% — expected `quantum/backend.py` gap) and WSL2 (100%, real `cudaq`,
mirrors what CI now runs including the new format-check step).

## 2026-07-22 (follow-up) — Release/SymPy badge content, five-row regroup

**What changed:**

- Release badge reverted from a live version lookup back to static
  `release | latest` (matching sibling repo `drift`'s convention), per owner
  request — still links to the GitHub releases page.
- SymPy badge changed from `SymPy | exact math` to `SymPy | latest`, now
  linking to `github.com/sympy/sympy/releases` instead of sympy.org — same
  "latest, link to the project's own releases" treatment as the Release
  badge, per owner request. Trade-off worth naming: this drops the
  `exact math` framing that explained *why* SymPy is used (the project's
  exact-rational ground truth) in favor of consistency with the Release
  badge's convention.
- Split the former single Python/tooling row into two: Python + SymPy
  (language and the exact-math ground-truth dependency) and Ruff/mypy/pytest
  (the three CI-enforced quality gates) — five labeled rows total.

**Why:** owner asked for the two badges above to say "latest" and link to
their project's releases page, and separately asked whether badge
ordering/grouping needed another pass, "esp on python stuff."

**Verified against:** fetched both changed badges' rendered SVG `<text>`
content directly (`release`/`latest`, `SymPy`/`latest`); curled
`github.com/sympy/sympy/releases` (HTTP 200). No `.py` files changed this
round, so lint/type/test/coverage state is unchanged from the prior entry.

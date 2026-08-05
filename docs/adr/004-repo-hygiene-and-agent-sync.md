# ADR 004 — Repo hygiene bar-raise: AGENTS.md, 100% coverage floor, theme-aware brand/diagram assets

**Status:** Accepted — July 2026

## Context

q1729 was about to start roadmap Phase 1 (the hand-written CUDA kernel, the
real QAE run, the first measured crossover) — real, load-bearing engineering
work that will touch every surface documented in the README, CLAUDE.md, and
`docs/roadmap.md`. Before adding that surface area, the owner asked for the
repo's engineering hygiene raised on several fronts
at once: theme-aware architecture diagrams and a banner, project structure,
documentation, ADR/decision records, badges, CI gates, and coverage.

Several existing patterns were reviewed as references: a mandatory
version/documentation-synchronization discipline expressed as an `AGENTS.md`,
code-generated light/dark SVG assets sharing one palette, and a multi-job CI
split (lint / typecheck / tests / docs-hygiene). No content was copied — the
references were application repos with frontends, deployed services, and
submission material, none of which q1729 has or needs. Only the *patterns*
were adapted, scoped down to q1729's actual surface area.

## Decision

1. **`AGENTS.md`** is the canonical, cross-tool home for the discipline that
   keeps q1729's dated, specific, verifiable claims about itself actually
   true — before every commit to `main` and every tag. `CLAUDE.md` keeps its
   Claude-Code-specific commands and non-negotiable constraints, and points
   to `AGENTS.md` instead of duplicating the sync discipline.
2. **The CI coverage gate moves from a 95%-buffered floor to a literal
   `--cov-fail-under=100`**, matched by a new `codecov.yml` (`target: 100%`,
   `threshold: 0%`). Real coverage on the cudaq-capable host was already
   100% at the time of this decision (verified on WSL2 the same session) —
   this removes the deliberate buffer the 0.1.0-era CLAUDE.md documented,
   rather than chasing a new number that wasn't already true.
3. **mypy becomes a real, enforced CI gate** (`typecheck` job), not
   dead config — `pyproject.toml` already carried `[tool.mypy]` settings
   that nothing ran. Wiring it in surfaced one genuine finding
   (`analysis/narrator.py`'s `sys.stdout.reconfigure` against the `TextIO`
   typeshed stub), fixed with a scoped `# type: ignore[union-attr]`.
4. **CI splits into four jobs** — `lint`, `typecheck`, `tests`, `docs` (the
   last requiring core doc files to exist and rejecting unfinished-work
   placeholder markers, see the grep pattern in `ci.yml`'s `docs` job
   directly) — instead of one monolithic job, so a failure names the specific
   gate that broke.
5. **Theme-aware SVG assets**, code-generated and checked in as source +
   render: `assets/architecture/` converts the existing README Mermaid
   diagram into a canonical `.mmd` plus light/dark renders (backgrounds
   matched to GitHub's own light/dark canvas so they sit flush against the
   page); `assets/brand/` adds an original q1729 hero banner sharing the
   diagram's exact six-role palette. Both are Python/Mermaid-CLI generated —
   no paid design tool, no external image-generation service ("at no cost").
   PNG rasterization was deliberately left out — q1729 has no video/deck
   need today, unlike the references reviewed.
6. **`benchmarks/README.md`** is added now, ahead of any real data, because
   `docs/roadmap.md` already names `benchmarks/` as the Phase 1 exit
   artifact location — the placeholder documents intent without building
   speculative infrastructure ahead of it.
7. **GitHub Actions pins move to their current latest major tags**
   (`actions/checkout@v7`, `actions/setup-python@v7`,
   `codecov/codecov-action@v7`, `softprops/action-gh-release@v3`), verified
   against each action's actual published tags rather than left at whatever
   version they were first added with.

## Consequences

- Every status-bearing document that mentioned "95%" or the old coverage
  rationale was swept to say 100% in the same change: README, CLAUDE.md,
  CHANGELOG.md, CONTRIBUTING.md, `docs/setup.md`, `docs/roadmap.md`.
- Any future PR that drops coverage below 100%, even by one line, now fails
  CI outright — there is no more absorb-churn buffer. This raises the bar
  Phase 1's CUDA-kernel and QAE-circuit work will be held to.
- `AGENTS.md` and `docs/sessions.md` add a standing obligation: every session
  that changes versions, features, or the roadmap phase must sweep the
  status-bearing documents and append a session-log entry. This is discipline
  overhead, accepted deliberately in exchange for the repo's claims about
  itself staying trustworthy as Phase 1's real surface area lands.
- `AGENTS.md` also establishes that dependency/tooling pins should track
  latest-free-and-verified by default, with cudaq's Python-version
  compatibility as the one pin requiring evidence before moving (ADR 002).

## Amendment — 2026-07-21: `CLAUDE.md` was not actually importing `AGENTS.md`

Decision 1 above said `CLAUDE.md` "points to `AGENTS.md` instead of
duplicating" the sync discipline. The initial implementation did this with a
prose sentence ("See AGENTS.md for..."), which reads fine to a human but
does **not** cause Claude Code to load `AGENTS.md`'s content into any
session — confirmed against Claude Code's own documentation
(`code.claude.com/docs/en/memory`): Claude Code auto-loads only `CLAUDE.md`
and never reads `AGENTS.md` on its own. The fix is Claude Code's documented
pattern: `CLAUDE.md` now contains a real `@AGENTS.md` import (plus an
HTML-comment explanation for human maintainers, stripped before injection)
and nothing else. All content that previously lived only in `CLAUDE.md` —
key commands, the two-host workflow, non-negotiable constraints,
style/conventions — was merged into `AGENTS.md`, which is now the single
place either file's content actually lives. No decision changed; only the
mechanism that was silently not working.

Also added in this pass: `AGENTS.md`'s Git History section now states a
standing rule against adding an AI co-author trailer to any commit (owner
preference, not a framework default), and `SECURITY.md` gained a section
covering the CI permission scoping and the local-only Node/mermaid-cli
build dependency introduced by `assets/architecture/` and `assets/brand/`.

## Addendum — 2026-08-05 — pattern references de-named

The Context section above originally named the specific repository whose
`AGENTS.md`, asset generation, and multi-job CI were reviewed as pattern
references. Those names were removed at the owner's explicit instruction:
this repository must not reference sibling or unrelated projects anywhere in
its files, docs, or history going forward.

Nothing about the decision changed — the same patterns were adopted, for the
same reasons, and the paragraph still records that they came from external
references rather than being invented here. Only the proper nouns are gone.
The standing rule now lives in `AGENTS.md` under Git History ("Never
reference another repository by name"), so this does not recur.

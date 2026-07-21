# AGENTS.md

Instructions for any coding agent working in this repo — Claude Code, Codex,
or otherwise. This is the single source of truth; **`CLAUDE.md` is
deliberately just `@AGENTS.md` plus nothing else**, because Claude Code only
auto-loads `CLAUDE.md` and does not read `AGENTS.md` on its own (confirmed
against Claude Code's own docs, 2026-07-21) — the import is what makes this
file load every session, not a prose pointer. Don't duplicate content back
into `CLAUDE.md`; if a tool needs something Claude-specific, add a short
section below the import in `CLAUDE.md` itself, not here.

## What this project is

q1729 — Ramanujan's mathematics meets the NVIDIA stack end to end: CUDA C++,
CUDA-Q/cuQuantum quantum simulation, and NIM/Nemotron analysis, from a local
RTX 5070 8GB to cloud H100s. Three-stage roadmap in the README: (1)
Ramanujan's 1914 1/π series as a CUDA kernel vs Quantum Amplitude Estimation
via CUDA-Q — on consumer *and* datacenter silicon, (2) community
contributions + published results, (3) Ramanujan expander graphs → qLDPC
codes with CUDA-Q QEC.

**The README is the bible.** The roadmap there is authoritative; anything
that contradicts it (especially anything PennyLane-flavored — that scaffold
was cut on 2026-07-10, ADR 001) gets removed, not polished.

**Current phase**: stage-1 skeleton + hybrid cloud layer + repo-hygiene bar
(AGENTS.md, 100% coverage, theme-aware assets — ADR 004) in place —
`classical/ramanujan_series.py` (exact SymPy ground truth),
`quantum/backend.py` (CUDA-Q target selection), `analysis/narrator.py`
(NIM/Nemotron findings narrator, ADR 003), tests green on both hosts.
Verified 2026-07-10: cudaq 0.15 in WSL2 selects the **`nvidia`** target (RTX
5070 GPU passthrough works). Next — this is **Phase 1 of `docs/roadmap.md`**,
the evidence-sequenced plan for all future work; keep the two in sync: the
hand-written CUDA kernel, the QAE circuit, the benchmark harness that emits
run files (schema: `data/sample_run.json`), and the first cloud-H100
comparison run (the optional datacenter axis of Phase 1). The README's
3-stage table stays the authoritative summary; `docs/roadmap.md` is its full
expansion and must not contradict it.

## Key commands

```bash
make install      # pip install -r requirements.txt (CPU-safe, any host)
make install-gpu  # pip install -r requirements-gpu.txt (WSL2 ONLY)
make run          # python main.py — status check, works with or without cudaq/NIM key
make gpu-check    # python -m quantum.backend — environment diagnostic
make narrate      # NIM narrator on data/sample_run.json (needs NVIDIA_API_KEY)
make test         # pytest tests -v (integration skips without cudaq)
make lint         # ruff check . && ruff format --check .
make typecheck    # mypy classical quantum analysis
make coverage     # pytest tests --cov --cov-report=term-missing --cov-fail-under=100
```

No `make` on the Windows host: run the underlying commands directly (they're
one-liners).

## Two-host workflow (ADR 002)

- **Windows host** (Python 3.14, `.venv/`): editing, classical math, unit
  tests, lint. cudaq does not install here — `quantum/backend.py` must always
  degrade gracefully.
- **WSL2 Ubuntu** (Python 3.12, venv at `~/q1729-cudaq`): everything CUDA-Q.
  Run tests there with
  `wsl -e bash -c "cd /mnt/c/ws/q1729 && ~/q1729-cudaq/bin/python -m pytest tests -q -p no:cacheprovider"`.
- CI (ubuntu, Python 3.12) installs cudaq and runs the integration suite on
  the `qpp-cpu` target — real simulator, no GPU.

## Why the sync-discipline sections below exist

q1729's docs make dated, specific, verified claims: "cudaq 0.15 selects
`nvidia` on the RTX 5070, verified 2026-07-10," "measured 100% coverage,"
"no `.cu` kernel exists yet." That specificity is the whole value of the
documentation — a vague doc can't go stale, but it also can't be trusted.
Every session that touches code, tests, or a version number is expected to
re-verify and correct the claims it's now responsible for, not carry them
forward from memory.

## Session start

Before making any claim about the repo's current state or writing any code:

- Read `git status` / recent `git log`, `docs/roadmap.md`'s **"Where the repo
  actually is"** section, `docs/sessions.md`'s most recent entry, and
  `CHANGELOG.md`'s top entry.
- Treat what those say as ground truth only until you've personally verified
  it this session. If you're about to state a fact about behavior on a host
  you haven't actually run code on this session — WSL2/cudaq, a live NIM call,
  a rented H100 — either run it or say explicitly that it's unverified. Don't
  restate an old "verified on `<date>`" claim as if you just checked it.

## Tech stack currency (check often, act without hesitation)

Every dependency, GitHub Action, and toolchain pin in this repo should track
the latest free, stable release — not a conservative floor kept out of
habit. This covers `requirements.txt` / `requirements-gpu.txt` floors
(sympy, numpy, httpx, pytest, pytest-cov, ruff, mypy, cudaq, cupy),
`.github/workflows/*.yml` action versions (`actions/checkout`,
`actions/setup-python`, `codecov/codecov-action`,
`softprops/action-gh-release` — pin the latest floating major tag, e.g.
`@v7`), and the Node.js/`@mermaid-js/mermaid-cli` toolchain used to
regenerate `assets/architecture/` renders.

When a session touches any of these, check the actual current release before
leaving a pin as-is — don't defer a bump just because the existing pin still
works. Verify with a real lookup (`gh api repos/<owner>/<repo>/tags`, `pip
index versions <package>`, or equivalent), never from memory — a
remembered "latest" is frequently stale by the time you use it. "At no
cost" means free/open-source packages and officially published GitHub
Actions only; never chase a version bump into a paid tier or license.

**The one deliberate exception:** `PYTHON_VERSION: "3.12"` in
`.github/workflows/ci.yml` and the WSL2 venv are pinned to match cudaq's
actually-published wheel compatibility (ADR 002), not held back by default
caution. Before bumping it, verify a newer cudaq wheel genuinely exists for
the target Python version — check the real release, don't assume. Bumping
the WSL2 venv itself (not just CI) additionally means installing a new
Python interpreter on the user's actual machine — a system-level change, not
a repo-file change, so confirm with the user before doing it rather than
just because a newer cudaq-compatible Python exists. Every other pin in this
repo should move without that extra scrutiny.

## Non-negotiable constraints

- **NIM/Nemotron is the analysis layer, never the simulator (ADR 003).** The
  narrator narrates numbers from run files — it must never generate,
  estimate, or "fill in" measurements. Don't route any quantum/classical
  computation through an LLM.
- **`requirements.txt` must stay installable on a CPU-only host.** The
  CUDA-Q stack lives exclusively in `requirements-gpu.txt`. Don't add
  cudaq/cupy to the core file. (`httpx` is core — the narrator runs
  anywhere.)
- **`quantum/` and `analysis/` must never raise at import time when their
  backing service is absent.** `import cudaq` happens inside functions;
  `cudaq_available()` / `nim_configured()` gate everything. `main.py` is
  required to run everywhere (unit-tested).
- **`classical/ramanujan_series.py` is exact SymPy on purpose** — it is the
  ground truth the CUDA kernel will be benchmarked against. Don't "optimize"
  it with floats; float speed belongs in the CUDA kernel.
- **Target preference order is `nvidia-mgpu` → `nvidia` → `tensornet` →
  `qpp-cpu`** (`PREFERRED_TARGETS`) — the stage-1 benchmark matrix. **On a
  driverless host, `cudaq.set_target()` on a GPU target hard-aborts the
  whole Python process — it does not raise** (this killed CI once).
  `select_target` therefore checks `cudaq.num_available_gpus()` and skips
  `GPU_TARGETS` up front; never "simplify" that guard into try/except.
  `nvidia-mgpu` additionally needs `MULTI_GPU_TARGETS` (2+ GPUs) — verified
  2026-07-10 on cudaq 0.15 that the bare `nvidia-mgpu` target name is
  deprecated in favor of `cudaq.set_target("nvidia", option="mgpu,fp32")`,
  and both forms raise a normal catchable `RuntimeError: Unable to create
  MPI plugin` on a single-GPU box (handled by the existing try/except, not a
  special case) — the success path itself is untested without real
  multi-GPU hardware, see `docs/nvidia-access.md`. Cloud boxes use the same
  code; run files carry a `hardware` field instead of the code forking per
  machine.
- **Secrets**: only `NVIDIA_API_KEY` exists; `.env` is gitignored,
  `.env.example` documents it, the key is read from the environment at call
  time and never logged.

## Style / conventions (matching sibling repos `continuum`, `bankers-wrapped`, `drift`)

- Makefile targets are the source of truth for how to run anything — keep
  the README Quick Start in sync with the Makefile, not the other way around.
- ADRs go in `docs/adr/`, numbered sequentially, one decision per file,
  immutable once merged — amend via a dated addendum, never edit history away.
- CHANGELOG.md follows Keep a Changelog; the release workflow extracts the
  tagged version's notes from it.
- Tests: `tests/unit/` mocks at the module boundary (fake `cudaq` module via
  `monkeypatch.setitem(sys.modules, ...)`, never mock the function under
  test); `tests/integration/` runs the real backend and skips cleanly where
  cudaq is absent.
- Ruff (`line-length 120`, `E,F,I,W,B`, plus `ruff format --check`) and mypy
  are the lint/format/type gates — all three run as separate CI jobs.
- **100% test coverage is the CI gate, no buffer** (owner's explicit
  requirement, raised from the 0.1.0 cutover's 95% buffered gate — see
  [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md)):
  `--cov-fail-under=100`, matched by `codecov.yml`. Every new module ships
  with tests that cover it fully. The only permitted exclusion is a
  JIT-compiled CUDA-Q kernel body (`# pragma: no cover` — coverage can't
  trace it), and each one must be exercised by a `tests/integration/` test
  instead. Measure where cudaq exists (WSL2/CI); Windows-local runs
  under-count `quantum/` and will show slightly below 100% there — that's
  expected, not a gate failure (CI is what's authoritative).

## Version & release synchronization (mandatory before tagging)

q1729 has no deployed service and no second version file to chase — no
frontend, no `/health` endpoint, no runtime `__version__`. The list is short
on purpose; don't invent more fields to bump than actually exist.

Fields that move together in the **same commit**, before a tag is created:

- `pyproject.toml` — `version`
- `CHANGELOG.md` — a new `## [x.y.z] — <date> — <summary>` heading. This is
  not optional: `.github/workflows/release.yml` extracts the GitHub release
  body from the heading matching the pushed tag via `awk`; a missing or
  mismatched heading ships a release with an empty body.
- git tag `vX.Y.Z` — annotated, created only after the above two are on
  `main`. If a local tag ever ends up pointing at an amended commit, recreate
  the tag before pushing it.

## Status-bearing documents (sweep before every commit to `main`)

These assert facts about the repo's current state, not just static
explanation. A stale sentence in any of them is a defect, not a cosmetic
nit:

- **This file (`AGENTS.md`)** — everything above: current phase, target
  preference order, coverage gate number, two-host workflow. `CLAUDE.md`
  itself never goes stale because it's just the import — don't add facts
  there that would need separate upkeep.
- **README.md** — badges, the "Built to be trusted" coverage claim, the
  Project structure list, the Hardware table, any `Verified on this machine`
  claim.
- **CONTRIBUTING.md** — the per-module coverage table (regenerate the
  numbers, don't hand-edit them).
- **SECURITY.md** — scope and secrets-handling stay accurate as the repo
  gains new build-time or runtime dependencies.
- **docs/roadmap.md** — the **"Where the repo actually is (vX.Y.Z)"** section
  is the single paragraph most likely to go stale; if this session changed
  which roadmap phase is current (a `.cu` kernel landed, a real run file
  exists, `benchmarks/` stopped being empty), edit it in the same commit.
- **docs/adr/README.md** — the ADR index table, whenever an ADR is added.
- **docs/setup.md, docs/onboarding.md, docs/nvidia-access.md** — these carry
  literal command output and dated "verified on `<date>`" claims. A new
  verification *replaces* the old date and output, it doesn't get appended
  alongside it.

## Counts and claims that drift silently — verify, never carry forward

- Coverage percentage and test count — run the commands, don't remember them.
- Whether `classical/` has a real `.cu` kernel yet (roadmap Phase 1) — `git
  ls-files '*.cu'` before asserting either way.
- Whether `benchmarks/` holds a real measured run yet, or is still the
  placeholder from before Phase 1.
- Whether `data/sample_run.json` is still the only run file in the repo (it
  is explicitly synthetic and must stay labeled as such even after real run
  files exist alongside it).
- The version/tag cited in any prose sentence outside `CHANGELOG.md` itself.

## Before handing off / before every commit to `main`

1. Run the verification commands from Key Commands above (`ruff`, `mypy`,
   `pytest --cov --cov-fail-under=100`) on whichever host the change touches;
   run the WSL2 command too if `quantum/backend.py` or its tests changed —
   Windows alone cannot measure that module's real coverage.
2. Grep the repo for the previous coverage percentage, test count, or version
   string you're about to change, and resolve every hit: update it, or
   confirm it's an intentional historical record (a dated CHANGELOG or
   `docs/sessions.md` entry) and leave it alone.
3. Append one entry to `docs/sessions.md`: date, what changed, why, what you
   verified it against. A skipped or vague entry defeats the point of the
   file — write it like the next agent has no other context, because it
   won't.
4. Update the relevant ADR (a new one if an architectural boundary changed, an
   amendment section if an existing decision evolved — never rewrite decision
   history to conceal what was actually done) and `CHANGELOG.md`.
5. Re-read `docs/roadmap.md`'s honest-baseline section one more time before
   committing — it's the easiest thing in the repo to forget.

## Git history

- Write a commit subject that names the substantive change; never a bare
  `release: vX.Y.Z` with no content description.
- Tag only after the version/changelog commit has landed on `main`.
- **Never add a `Co-Authored-By: Claude...` (or any AI-attribution) trailer
  to a commit, and never otherwise cause an AI agent to appear in this
  repo's GitHub Contributors graph.** This is a deliberate, explicit owner
  preference, not the default some tools ship with — commits are authored
  and attributed to the human owner alone. This applies regardless of which
  agent makes the commit.

## Repository surfaces

- `README.md` — public-facing pitch, quickstart, roadmap summary, badges.
- `CLAUDE.md` — a one-line `@AGENTS.md` import; add Claude-Code-specific
  content below the import only if something is genuinely tool-specific,
  never a duplicate of what's here.
- `AGENTS.md` (this file) — canonical instructions and the discipline for
  keeping everything below honest over time.
- `docs/roadmap.md` — single source of truth for sequencing; see Session
  start above.
- `docs/adr/` — durable architecture decisions, one per file, immutable once
  merged; amend via a dated addendum, never edit history away.
- `docs/sessions.md` — dated log of what each work session changed and
  verified it against.
- `docs/setup.md`, `docs/onboarding.md`, `docs/nvidia-access.md` — operational
  how-tos with dated, literal "verified" evidence.
- `classical/ramanujan_series.py` — the 1914 series, exact SymPy (ground
  truth for the CUDA kernel).
- `quantum/backend.py` — CUDA-Q target selection + environment diagnostic.
- `analysis/narrator.py` — NIM/Nemotron findings narrator (`make narrate`).
- `data/sample_run.json` — synthetic demo data only, never a real measurement.
- `assets/architecture/` — Mermaid source + generated light/dark diagram
  SVGs. Edit the `.mmd`, never the SVG; regenerate both themes together.
- `assets/brand/` — banner source of truth. Edit `build_banner.py`, never the
  SVG; regenerate both themes together.
- `benchmarks/` — real measured run files + crossover plots (roadmap Phase 1
  deliverable). Empty/placeholder until Phase 1 lands a real run.
- CI quality gate: `.github/workflows/ci.yml`; releases: tag `v*.*.*` →
  `release.yml`; coverage target: `codecov.yml`.

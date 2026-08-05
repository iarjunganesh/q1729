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
RTX 5070 Laptop GPU to cloud H100s. Three-stage roadmap in the README:
(1) Ramanujan's 1914 1/π series as a CUDA kernel vs Quantum Amplitude
Estimation via CUDA-Q — on consumer *and* datacenter silicon, (2) community
contributions + published results, (3) Ramanujan expander graphs → qLDPC
codes with CUDA-Q QEC.

**The README is the bible.** The roadmap there is authoritative; anything
that contradicts it (especially anything PennyLane-flavored — that scaffold
was cut on 2026-07-10, ADR 001) gets removed, not polished.

**This is not a hackathon project.** It has no submission deadline, no demo
video, no judging criteria, and no `submission/` directory. Never add
submission material, devpost-style write-ups, or "built in N hours" framing.
It is a research repo whose value is measured claims that stay true.

**Current phase**: roadmap **Phase 1 is delivered** on the consumer axis and
**Phase 0 is complete**. Present in the repo, verified 2026-08-05:

- `classical/ramanujan_kernel.cu` — real hand-written CUDA C++, compiled via
  NVRTC (ADR 005), validated against exact SymPy to 1e-15 relative.
- `quantum/qae.py` — canonical Quantum Amplitude Estimation, converging on π.
- `benchmarks/` — harness, environment capture, plotter, and a **real measured
  run file** (`benchmarks/runs/2026-08-05-rtx5070-turbo.json`) plus its
  narrated writeup and theme-aware crossover plots.
- `docs/handbook/` — Phase 0 principles + the nine-field research-standards
  contract.
- 156 tests, 100% coverage on WSL2/CI.

**Next**: the optional cloud-H100 axis of Phase 1, then roadmap Phase 2 (the
qLDPC second experiment). `docs/roadmap.md` is the evidence-sequenced plan and
must not contradict the README's 3-stage table.

## Key commands

```bash
make install      # pip install -r requirements.txt (CPU-safe, any host)
make install-gpu  # pip install -r requirements-gpu.txt (WSL2 ONLY)
make run          # python main.py — status check, works with or without cudaq/cupy/NIM key
make gpu-check    # python -m quantum.backend — CUDA-Q target diagnostic
make cuda-check   # python -m classical.cuda_kernel — CUDA kernel/GPU diagnostic
make narrate      # NIM narrator on data/sample_run.json (needs NVIDIA_API_KEY)
make benchmark POWER_PROFILE=turbo   # stage-1 crossover run -> benchmarks/runs/
make plot RUN=benchmarks/runs/<f>.json  # theme-aware crossover SVGs
make test         # pytest tests -v (integration skips without cudaq/GPU)
make lint         # ruff check . && ruff format --check .
make format       # ruff check --fix . && ruff format .  (applies what lint checks)
make typecheck    # mypy classical quantum analysis benchmarks
make coverage     # pytest tests --cov --cov-report=term-missing --cov-fail-under=100
```

No `make` on the Windows host: run the underlying commands directly (they're
one-liners).

## Two-host workflow (ADR 002)

- **Windows host** (Python 3.14, `.venv/`): editing, classical math, unit
  tests, lint. Neither cudaq nor a usable cupy installs here —
  `quantum/backend.py`, `quantum/qae.py` and `classical/cuda_kernel.py` must
  all degrade gracefully. Expect **128 passed, 28 skipped**.
- **WSL2 Ubuntu** (Python 3.12, venv at `~/q1729-cudaq`): everything CUDA-Q
  and everything CUDA. Run tests there with
  `wsl -e bash -c "cd /mnt/c/ws/q1729 && ~/q1729-cudaq/bin/python -m pytest tests -q -p no:cacheprovider"`.
  Expect **156 passed**.
- CI (ubuntu, Python 3.13) installs cudaq and runs the CUDA-Q integration
  suite on the `qpp-cpu` target — real simulator, no GPU. The CUDA-kernel
  integration tests skip there (no GPU); that split is ADR 005, not a gap.

## Why the sync-discipline sections below exist

q1729's docs make dated, specific, verified claims: "cudaq 0.15.1 selects
`nvidia` on the RTX 5070, verified 2026-08-05," "156 tests, 100% coverage,"
"the QAE arm peaks at 12–20% GPU utilization." That specificity is the whole
value of the documentation — a vague doc can't go stale, but it also can't be
trusted. Every session that touches code, tests, or a version number is
expected to re-verify and correct the claims it's now responsible for, not
carry them forward from memory.

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
(sympy, numpy, httpx, matplotlib, pytest, pytest-cov, ruff, mypy, cudaq,
cupy, nvidia-cuda-nvrtc), `.github/workflows/*.yml` action versions
(`actions/checkout`, `actions/setup-python`, `codecov/codecov-action`,
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

**The one deliberate exception:** the Python version is capped by cudaq's
actually-published wheels, not by caution. Verified 2026-08-05: `cudaq`
0.15.1 resolves to `cuda-quantum-cu13` wheels built for **cp311, cp312,
cp313 only** — there is no 3.14 wheel. CI therefore runs 3.13 (the newest
supported) and `requires-python` floors at 3.12. Before bumping either,
check the real wheel tags; don't assume. Bumping the **WSL2 venv** (still
3.12) additionally means installing a new Python interpreter on the owner's
actual machine — a system-level change, not a repo-file change, so confirm
with the owner before doing it. Every other pin in this repo should move
without that extra scrutiny.

## Non-negotiable constraints

- **NIM/Nemotron is the analysis layer, never the simulator (ADR 003).** The
  narrator narrates numbers from run files — it must never generate,
  estimate, or "fill in" measurements. Don't route any quantum/classical
  computation through an LLM.
- **`requirements.txt` must stay installable on a CPU-only host.** The
  CUDA stack (cudaq, cupy, nvidia-cuda-nvrtc) lives exclusively in
  `requirements-gpu.txt`. Don't add any of them to the core file. (`httpx`
  and `matplotlib` are core — the narrator and the plotter run anywhere.)
- **`quantum/` and `classical/cuda_kernel.py` and `analysis/` must never
  raise at import time when their backing service is absent.** `import
  cudaq` / `import cupy` happen inside functions; `cudaq_available()` /
  `cuda_available()` / `nim_configured()` gate everything. `main.py` is
  required to run everywhere (unit-tested). **CUDA-Q kernels are defined
  inside functions**, never at module scope — a module-level `@cudaq.kernel`
  would require cudaq at import and break this.
- **`classical/ramanujan_series.py` is exact SymPy on purpose** — it is the
  ground truth the CUDA kernel is benchmarked against. Don't "optimize" it
  with floats; float speed belongs in the CUDA kernel. The integration test
  asserting kernel-vs-SymPy agreement to 1e-15 is the drift alarm for the
  whole classical arm — never weaken its tolerance to make a change pass.
- **The CUDA kernel sums block partials on the host, not with `atomicAdd`.**
  This is deliberate: atomic float accumulation commits in nondeterministic
  order, and a benchmark whose output moves between identical runs is not
  evidence. Don't "optimize" this into an atomic reduction.
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
  code; run files carry a `hardware_id` field and an environment block
  instead of the code forking per machine.
- **Synthetic data stays labeled and unplottable.** `data/sample_run.json`
  carries `"synthetic": true` and `benchmarks/plot.py` raises on it. Never
  relax that guard, and never let a synthetic file lose its label because
  real run files now exist alongside it.
- **Secrets**: only `NVIDIA_API_KEY` exists; `.env` is gitignored,
  `.env.example` documents it, the key is read from the environment at call
  time and never logged.

## Benchmark integrity (the thing this repo exists to protect)

A measured claim in this repo is only worth what its provenance is worth.

- **Every run file must satisfy the nine-field contract** in
  `docs/handbook/research-standards.md`: question, hypothesis, variables,
  controls, hardware, software versions, statistical treatment, raw data,
  limitations. `benchmarks/harness.py` emits all nine — if you add a field to
  the schema, add it there, not by hand-editing JSON.
- **The hypothesis is committed before the run.** It lives as a module
  constant in `benchmarks/harness.py` so changing it is a visible diff.
  Never edit it to match a result.
- **Raw per-repeat samples are never discarded** in favour of summaries.
- **The power/thermal profile is a required argument, not a default.** On a
  laptop it changes every timing. `make benchmark` refuses to run without it.
- **Never hand-edit a run file's numbers.** If a run is wrong, re-run it and
  say so. A run file is a record of something that happened.
- **Don't delete or overwrite an existing measured run file** to make a
  newer one look like the only result. Add alongside; the archive is the
  point.

## Style / conventions

- Makefile targets are the source of truth for how to run anything — keep
  the README Quick Start in sync with the Makefile, not the other way around.
- ADRs go in `docs/adr/`, numbered sequentially, one decision per file,
  immutable once merged — amend via a dated addendum, never edit history away.
- CHANGELOG.md follows Keep a Changelog; the release workflow extracts the
  tagged version's notes from it.
- Tests: `tests/unit/` mocks at the module boundary (fake `cudaq`/`cupy`
  module via `monkeypatch.setitem(sys.modules, ...)`, never mock the function
  under test); `tests/integration/` runs the real backend and skips cleanly
  where cudaq or a GPU is absent.
- **No unbounded busy-waits in tests.** Anything that waits on a background
  thread uses a bounded helper that fails with a message instead of hanging
  the suite.
- Ruff (`line-length 120`, `E,F,I,W,B`, plus `ruff format --check`) and mypy
  are the lint/format/type gates — all three run as separate CI jobs.
- **100% test coverage is the CI gate, no buffer** (owner's explicit
  requirement — see [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md)):
  `--cov-fail-under=100`, matched by `codecov.yml`. Coverage sources are
  `classical`, `quantum`, `analysis`, `benchmarks`. Every new module ships
  with tests that cover it fully. The only permitted exclusion is a
  JIT-compiled CUDA-Q kernel body (`# pragma: no cover` — coverage can't
  trace it), and each one must be exercised by a `tests/integration/` test
  instead. Measure where cudaq exists (WSL2/CI); Windows-local runs
  under-count `quantum/` and will show ~96% there — that's expected, not a
  gate failure (CI is what's authoritative).
- **A `# pragma: no cover` that isn't a CUDA-Q kernel body is a bug.** Don't
  reach for it to close a coverage gap; write the test.

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
  `main`.

**Tags must point at commits reachable from `main`.** On 2026-08-05 both
`v0.1.0` and `v0.1.1` were found pointing at orphaned commits left behind by
an earlier history rewrite; the releases existed on GitHub but the tags were
unreachable from any branch. They were re-pointed at the equivalent
`main` commits (byte-identical trees) and force-pushed, with the original
annotation text and dates preserved. Before pushing any tag, verify:

```bash
git merge-base --is-ancestor "$(git rev-list -n1 vX.Y.Z)" main && echo reachable
```

If you ever rewrite history that a tag points into, re-point the tag in the
same session — don't leave it for a later one to discover.

## Status-bearing documents (sweep before every commit to `main`)

These assert facts about the repo's current state, not just static
explanation. A stale sentence in any of them is a defect, not a cosmetic
nit:

- **This file (`AGENTS.md`)** — everything above: current phase, target
  preference order, coverage gate number, test counts, two-host workflow.
  `CLAUDE.md` itself never goes stale because it's just the import — don't
  add facts there that would need separate upkeep.
- **README.md** — badges (including pinned versions in badge text), the
  "first real result" numbers, the "Built to be trusted" coverage and test
  counts, the Project structure list, the Hardware table, the roadmap status
  column, any `Verified on this machine` claim.
- **CONTRIBUTING.md** — the per-module coverage table (regenerate the
  numbers, don't hand-edit them).
- **SECURITY.md** — scope and secrets-handling stay accurate as the repo
  gains new build-time or runtime dependencies.
- **docs/roadmap.md** — the **"Where the repo actually is (vX.Y.Z)"** section
  is the single paragraph most likely to go stale, and the phase table's
  status column with it.
- **docs/handbook/** — principles and research standards each cite concrete
  enforcement points in the code; if the enforcement moves, the citation moves.
- **docs/adr/README.md** — the ADR index table, whenever an ADR is added.
- **benchmarks/README.md** — describes what is actually in `benchmarks/`.
- **docs/setup.md, docs/onboarding.md, docs/nvidia-access.md** — these carry
  literal command output and dated "verified on `<date>`" claims. A new
  verification *replaces* the old date and output, it doesn't get appended
  alongside it.

## Counts and claims that drift silently — verify, never carry forward

- Coverage percentage and test count — run the commands, don't remember them.
- Whether `classical/` has a real `.cu` kernel — `git ls-files '*.cu'`.
  (It does, since 2026-08-05.)
- What is actually in `benchmarks/runs/` and `benchmarks/plots/` — `ls`, don't
  assume.
- Whether `data/sample_run.json` is still the only run file (it is not, since
  2026-08-05 — and it must stay labeled synthetic regardless).
- The version/tag cited in any prose sentence outside `CHANGELOG.md` itself.
- Driver, CUDA, and package versions quoted in the README Hardware table —
  `nvidia-smi` and `pip list`, not memory. The GPU is an **RTX 5070 Laptop
  GPU**, not a desktop 5070; don't let that drift back.

## Before handing off / before every commit to `main`

1. Run the verification commands from Key Commands above (`ruff check`,
   `ruff format --check`, `mypy`, `pytest --cov --cov-fail-under=100`) on
   whichever host the change touches; run the WSL2 command too if anything
   under `quantum/`, `classical/cuda_kernel.py`, `benchmarks/` or their tests
   changed — Windows alone cannot measure those modules' real coverage.
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
  `release: vX.Y.Z` with no content description, and never a version number
  as the whole subject — versions live in tags and `CHANGELOG.md`.
- Tag only after the version/changelog commit has landed on `main`, and only
  at a commit reachable from `main` (see the reachability check above).
- **Never add a `Co-Authored-By: Claude...` (or any AI-attribution) trailer
  to a commit, and never otherwise cause an AI agent to appear in this
  repo's GitHub Contributors graph.** This is a deliberate, explicit owner
  preference, not the default some tools ship with — commits are authored
  and attributed to the human owner alone. This applies regardless of which
  agent makes the commit.
- **Never reference another repository by name** in this repo's files,
  commits, or docs. Conventions borrowed from elsewhere get described on
  their merits, not by citation.

## Repository surfaces

- `README.md` — public-facing pitch, quickstart, the measured result, roadmap
  summary, badges.
- `CLAUDE.md` — a one-line `@AGENTS.md` import; add Claude-Code-specific
  content below the import only if something is genuinely tool-specific,
  never a duplicate of what's here.
- `AGENTS.md` (this file) — canonical instructions and the discipline for
  keeping everything below honest over time.
- `docs/roadmap.md` — single source of truth for sequencing; see Session
  start above.
- `docs/handbook/` — Phase 0 constitution: `principles.md` and
  `research-standards.md`.
- `docs/adr/` — durable architecture decisions, one per file, immutable once
  merged; amend via a dated addendum, never edit history away.
- `docs/sessions.md` — dated log of what each work session changed and
  verified it against.
- `docs/setup.md`, `docs/onboarding.md`, `docs/nvidia-access.md` — operational
  how-tos with dated, literal "verified" evidence.
- `classical/ramanujan_kernel.cu` — the hand-written CUDA C++ kernel.
- `classical/cuda_kernel.py` — NVRTC compile/launch/timing wrapper (ADR 005).
- `classical/ramanujan_series.py` — the 1914 series, exact SymPy (ground
  truth for the CUDA kernel).
- `quantum/qae.py` — canonical Quantum Amplitude Estimation circuit.
- `quantum/backend.py` — CUDA-Q target selection + environment diagnostic.
- `analysis/narrator.py` — NIM/Nemotron findings narrator (`make narrate`).
- `benchmarks/` — harness, environment capture, plotter, and the measured
  `runs/` + `plots/` archive.
- `data/sample_run.json` — synthetic demo data only, never a real measurement.
- `assets/architecture/` — Mermaid source + generated light/dark diagram
  SVGs. Edit the `.mmd`, never the SVG; regenerate both themes together.
- `assets/brand/` — banner source of truth. Edit `build_banner.py`, never the
  SVG; regenerate both themes together.
- CI quality gate: `.github/workflows/ci.yml`; releases: tag `v*.*.*` →
  `release.yml`; coverage target: `codecov.yml`.

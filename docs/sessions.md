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
  an external reference pattern: `assets/architecture/` (Mermaid source
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
raise the repo's engineering-hygiene bar
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
  a known-good badge set. `Ruff`, `mypy`, and `pytest` had label/message in
  the wrong order — `Ruff` had been backwards (`lint | Ruff`) since before
  this session's hygiene pass even started, and the `mypy`/`pytest` badges I
  added inherited the same inversion instead of the `Name-Version`
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
asked me to check against a known-good reference carefully rather than re-guess.

**Verified against:** fetched and grep'd the actual `<text>` content of
every badge SVG in the README (not just HTTP status) before and after the
fix; `ruff check .`, `ruff format --check .`, `mypy classical quantum
analysis`, and `pytest --cov --cov-fail-under=100` all green on both Windows
(97% — expected `quantum/backend.py` gap) and WSL2 (100%, real `cudaq`,
mirrors what CI now runs including the new format-check step).

## 2026-07-22 (follow-up) — Release/SymPy badge content, five-row regroup

**What changed:**

- Release badge reverted from a live version lookup back to static
  `release | latest`, per owner
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

## 2026-08-05 — Roadmap Phase 0 + Phase 1: the first real measured crossover

**What changed:**

- **Phase 0 (constitution)** — added `docs/handbook/principles.md` (the six
  North Star principles, each citing the concrete place it is enforced rather
  than restating it as an aspiration) and `docs/handbook/research-standards.md`
  (the nine-field contract). Linked from the README and `docs/adr/README.md`.
  The contract is enforced in code, not just documented: `benchmarks/harness.py`
  emits all nine fields and a new CI step rejects a measured run file missing
  any of them.
- **Phase 1 (the first real result)** — all five non-optional deliverables:
  1. `classical/ramanujan_kernel.cu`, a genuine hand-written CUDA C++ kernel
     (one term per thread, shared-memory tree reduction), plus
     `classical/cuda_kernel.py` to compile/launch/time it.
  2. `quantum/qae.py`, canonical Quantum Amplitude Estimation running on the
     `nvidia` cuStateVec target.
  3. A real measured run file, `benchmarks/runs/2026-08-05-rtx5070-turbo.json`.
  4. Theme-aware crossover plots in `benchmarks/plots/`.
  5. A narrator-drafted writeup beside the run file.
  The optional H100 axis was **not** done and is recorded as outstanding.
- **Restored two broken release tags.** `v0.1.0` and `v0.1.1` pointed at
  orphaned commits from an earlier history rewrite — the GitHub releases
  existed but the tags were unreachable from any branch, which is why they
  appeared missing. Re-pointed at the equivalent `main` commits after
  confirming byte-identical trees, original annotation text and dates
  preserved, force-pushed. Old tag objects kept locally under `refs/backup/*`.
- **Tech stack brought to current** across both requirements files and CI,
  every version confirmed with a real lookup rather than from memory. CI
  Python 3.12 → 3.13 after checking cudaq's published wheel tags
  (cp311/cp312/cp313; no 3.14 wheel exists, so the cap is real).
- **README, AGENTS.md, CI hardened**; all sibling-repo names removed
  repo-wide per owner instruction, with a dated addendum on ADR 004 recording
  the redaction rather than editing the decision silently.

**Three debugging findings worth recording, because each was initially
mistaken for something else:**

1. **The QAE circuit was wrong twice before it was right.** The Grover
   operator was correct from the start (verified independently: P(good) after
   p iterations matched sin²((2p+1)θ) exactly), which localized the fault to
   the phase-estimation half. First fault: a bit-reversal swap layer in the
   inverse QFT that CUDA-Q's measurement ordering already accounts for —
   found by testing QPE against exactly-representable phases, where a correct
   implementation must peak at probability 1.00 and mine peaked at 0.22.
   Second fault: the decomposed Grover operator carries a global −1 that is
   unobservable in Q itself but becomes a real relative phase once controlled,
   biasing every estimate by exactly half the counting range. Both fixes are
   commented at the site.
2. **The accuracy plateau at m = 10 is real, not a bug.** Errors stopped
   improving past 10 counting qubits in *both* fp32 and fp64, which initially
   looked like a simulator precision limit. It is not: the eigenphase
   0.34668271 lies within 3.0e-6 of the 10-bit dyadic 355/1024, so additional
   counting qubits correctly return zeros. Now recorded as a declared
   limitation with `phase_error`/`phase_resolution` on every row so a reader
   can check it instead of trusting the prose.
3. **The first two capture attempts recorded misleading GPU state.** The
   environment block was collected after the sweep and reported idle clocks
   (847 MHz) for a run that never throttled. Fixed by snapshotting before
   timing and adding a background `LoadSampler`. That change is what surfaced
   the most interesting result in the run: the quantum arm peaks at 12–20%
   GPU utilization against the classical kernel's 95%, so its cost is
   dispatch overhead rather than statevector arithmetic — which means the
   H100 question is about qubit ceiling, not speed.

**Why:** the owner asked to start Phases 0 and 1, upgrade the stack, fix badge
grouping, harden the agent instructions, and sweep stale docs. The owner also
flagged mid-session that the release tags appeared missing, and confirmed
switching the laptop to Turbo before the measured run.

**Power profile note:** the benchmark was captured on Armoury Crate **Turbo**,
verified under load at 2835 MHz sustained (vs 1710 MHz on Silent) with temps
flat at 65 °C. The profile is recorded in the run file as a declared control.

**Verified against:** `ruff check .`, `ruff format --check .`, and
`mypy classical quantum analysis benchmarks` all clean on Windows;
**156 passed / 100.00% coverage** on WSL2 (cudaq 0.15.1, real RTX 5070 Laptop
GPU), **128 passed / 28 skipped / 96%** on Windows as expected. Kernel output
checked against exact SymPy partial sums to 1e-15 relative and confirmed
bit-identical across repeats and across block sizes 32–512. All 13 README
badge URLs fetched and their rendered SVG text inspected, not just their HTTP
status. Both restored tags re-checked with `git merge-base --is-ancestor`
against `main` and both GitHub releases re-read to confirm notes and dates
survived.

---

## 2026-08-05 (follow-up) — Scouted AMD ROCm/MI300 and recorded the answer as ADR 006

**What changed:** the owner asked whether q1729 should target AMD ROCm and
cloud MI300-series GPUs, given that the laptop is an AMD CPU with an NVIDIA
GPU. Answered by scouting first and writing the decision down, without touching
any measured artifact:

1. **[ADR 006](adr/006-rocm-as-phase-4-second-backend.md)** — ROCm/MI300 is the
   designated roadmap **Phase 4** second backend, staying behind Phases 2 and 3.
   It records four commitments: the phase order does not change (the outstanding
   H100 axis comes first — reproducing on a second machine of the same vendor is
   a smaller claim than a second vendor); an AMD run publishes the classical arm
   only and is labeled a portability result; a second quantum simulator needs its
   own ADR plus a same-GPU control run; and the kernel stays HIP-portable.
2. **Portability constraint on `classical/ramanujan_kernel.cu`** — written into
   the kernel's header comment *and* `AGENTS.md`, not only the ADR, so the next
   person to edit the kernel sees it there rather than having to know an ADR
   exists.
3. Roadmap Phase 4 now names ROCm as *the* chosen backend and summarizes what
   ADR 006 settled, so Phase 4 does not re-litigate it. ADR index and CHANGELOG
   `[Unreleased]` updated.

**Why:** the tempting move — rent an MI300X, run both arms, publish a second
crossover — is available and would produce a plausible-looking invalid result.
CUDA-Q has no ROCm target, so on AMD silicon `select_target` falls through to
`qpp-cpu`, and a "crossover" plot would really be GPU classical vs CPU quantum
with a crossing point that is an artifact of the fallback. Naming that failure
mode before any money is spent was the whole point of the session.

**Verified against:** `classical/ramanujan_kernel.cu` read in full and confirmed
free of NVIDIA-specific intrinsics — no `__shfl_*`, no cooperative groups, no
PTX asm — which is what makes the portability claim inspection rather than
assumption. CUDA-Q's published simulator-backend list checked directly: all GPU
targets (`nvidia`, `nvidia option=mgpu/mqpu`, `tensornet`) are cuQuantum-based
and NVIDIA-only. Qiskit Aer on ROCm confirmed against AMD's own ROCm blog
running Aer `statevector` on MI300X under ROCm 7.2 (dated 2026-05-29), and the
qsim HIP backend against its SC '23 paper. CuPy ROCm/hipRTC `RawModule` support
confirmed from CuPy's install docs and v14 release notes (ROCm 6.4, Jan 2026),
still marked experimental.

**Not verified, and not claimed anywhere:** nothing was executed on AMD
hardware. No MI300X instance was rented, no ROCm build attempted, no timing on
AMD silicon asserted. The portability claims are source-level compatibility
claims only. Docs-only session — no Python changed, so the 156-test/100%
coverage figures from the entry above stand unretested and unrestated here.

---

## 2026-08-05 (follow-up 2) — Roadmap Phase 2 begins: LPS Ramanujan expander graphs

**What changed:**

1. **`classical/ramanujan_graph.py`** — the Lubotzky-Phillips-Sarnak
   construction. Jacobi four-square generators, `sqrt(-1) mod q`, and a
   breadth-first walk of the subgroup those matrices generate inside
   `PGL(2, q)`. The design choice worth keeping: BFS *discovers* the vertex
   set instead of enumerating the group and filtering for subgroup
   membership, and the resulting order is then compared against the Legendre
   symbol `(p|q)`'s prediction — so a construction bug fails an assertion
   instead of silently producing a wrong graph.
2. **`tests/unit/test_ramanujan_graph.py`** — 30 tests, 100% coverage of the
   new module, **no `# pragma: no cover`**. The three internal guards are each
   driven to fire by monkeypatching the *upstream* check rather than being
   excluded from coverage, per ADR 004's rule that a pragma outside a CUDA-Q
   kernel body is a bug.
3. Status sweep: test counts 156 → 186 (WSL2) and 128 → 158 passed (Windows)
   across `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `docs/roadmap.md`;
   Windows total coverage re-measured 96% → 97%; roadmap phase table, "Where
   the repo actually is", and the Phase 2 build list updated; `AGENTS.md`
   repository-surfaces list extended.
4. Recorded the deferred **`q1729.arjunganesh.dev` results site** in roadmap
   Phase 6 with an explicit trigger (multiple runs across multiple
   `hardware_id`s) and the binding constraint that it must be *generated* from
   `benchmarks/runs/*.json` with zero hand-authored numbers.

**Why:** the owner asked to start Phase 2. The expander graph is the correct
first brick because everything downstream — parity-check matrices, the
hypergraph-product qLDPC code, the decoder — is checked *against* it, exactly
as the CUDA kernel is checked against `ramanujan_series.py`. Doing it first
means the Phase 2 GPU arm has ground truth waiting for it rather than being
validated retroactively.

**Two real bugs found and fixed during the session, both by testing rather
than review:**

- `four_square_solutions` returned **zero** solutions for `p = 13`. The even
  sweep was `range(-isqrt(p), isqrt(p) + 1, 2)`, which walks *odd* values
  whenever `isqrt(p)` is odd. `p = 5` gave `isqrt = 2` and worked by luck,
  which is why the first test written (p = 5) passed. Fixed by rounding the
  bound down to even before building the range.
- The default `report()` pair was `(5, 11)`, which is illegal: `q` must be
  `1 mod 4` for `sqrt(-1)` to exist and `11 = 3 mod 4`. Corrected to `(5, 13)`,
  the canonical LPS textbook pair — and 13 is the *smallest* legal partner for
  `p = 5`, not merely a convenient one.

**Verified against:** **186 passed / 100.00% coverage** on WSL2 (cudaq 0.15.1,
real RTX 5070 Laptop GPU) with `--cov-fail-under=100`; **158 passed / 28
skipped / 97%** on Windows, the skip count unchanged because the new module is
pure numpy/sympy and needs neither cudaq nor a GPU. `ruff check`,
`ruff format --check`, and `mypy classical` all clean. Spectral results
confirmed by running the module: `PSL(2,13)` 1092 vertices / 18-regular /
λ₂ = 7.850855 ≤ 8.246211, and `PGL(2,13)` 2184 vertices / 6-regular /
λ₂ = 4.249721 ≤ 4.472136 — both Ramanujan, and the bipartite/non-bipartite
split matches `(p|q)` in each case.

**Not done, and not claimed:** no parity-check matrices, no qLDPC code, no
decoder, no CUDA-Q QEC run, no second run file. Phase 2 is started, not
delivered, and every status document says so in those words.

---

## 2026-09-06 — Repository audit and direction assessment

**What changed:** audited the current working tree, including the pre-existing
staged Phase 2 changes and untracked `docs/PATHWAYS.md`. Saved a detailed local
report at `.tmp/q1729-audit-2026-09-06.md` and added this session/changelog record.
No implementation, tests, requirements, generated assets, measured JSON, or
staged index entries were changed. No architectural decision was adopted or
amended; the report recommends a bounded feasibility milestone for later work.

**Why:** the owner requested a whole-repository audit and a candid assessment
of whether to continue q1729 or choose another direction.

**Verified this session:** Windows Python 3.14.6; Ruff lint and format clean
(57 files); mypy clean (13 source files); `pip check` clean; `main.py` succeeds.
The suite collected 186 tests and completed with 157 passed / 29 skipped and
97.19% coverage. The 100% threshold therefore exits unsuccessfully on this host;
the missing paths require CUDA-Q. The live NIM test was deliberately skipped by
removing its key only from the test subprocess environment, explaining the
extra skip relative to the historical 158/28 Windows split. No live NIM request
was made. Windows `nvidia-smi` reports RTX 5070 Laptop GPU, 8151 MiB, driver
616.56. The public CI run `31050071005` has four successful jobs at `f88a926`,
and v0.2.0 is the latest published release; neither verifies the staged graph
work. All 27 archived run rows' summary statistics recompute from their five
retained timing samples.

**Open findings:** the harness can overwrite an existing run; generated findings
incorrectly confirm submillisecond execution and misstate the cheapest
five-digit QAE result; a plateau in the tested phase range is overstated as a
permanent limit. Dispatch and H100 performance claims need profiling. Per-repeat
quantum outcomes, complete software/code provenance, backend/device labeling,
run validation, release enforcement, and stale onboarding text need attention.
The current QAE oracle encodes a known amplitude using pi, so its strongest
defensible framing is a simulator resource-cost/educational experiment.

**Phase 2 exploration:** built the canonical LPS graph on CPU and examined its
1092-by-1092 bipartite parity-check matrix using exact GF(2) elimination: rank
794, classical dimension 298. Its self hypergraph product would have 2,384,928
physical qubits; this is a parameter calculation, not an implemented or decoded
quantum code. The graph spectrum is a numerical verification of an exact
integer construction, not an exact computational spectral proof. Any next code
experiment needs a specified construction and sparse memory/runtime budget.

**Unverified:** WSL2 failed to attach its configured `ext4.vhdx` with
`HCS/ERROR_PATH_NOT_FOUND`, so historical WSL2 100% coverage and real CUDA/QAE
behavior were not reproduced. No runtime repair, package installation, GPU
benchmark, cloud rental, commit, tag, or push was performed. Historical measured
numbers and hypotheses remain intact; the findings above remain open.

## 2026-09-06 — Complete Markdown audit and phased roadmap revision

Read all 26 original authored Markdown files, 3379 lines, including the local
scratch audit. Added `docs/markdown-audit-2026-09-06.md` with original line ranges,
dispositions, evidence limits and unresolved implementation gates. README retains
the three-stage research thread; roadmap Phases 0–6 now have explicit dependencies
and exits. Next code work is P1-R1 archive protection/semantic validation, then
provenance, profiling and a bounded repeat. Phase 2 bridges classical decoding
to feasible qLDPC. Publication may precede the platform if contribution/evidence
gates pass; novelty and arXiv acceptance are unverified. ADR 007 records this decision.

Corrected setup/onboarding, AI-prose guarantees, graph proof language, timing and
utilization interpretation, data transmission scope, coverage and release claims.
Kept measured JSON unchanged and preserved the narrator draft beneath a
supersession note, adding separate reviewed findings. Historical ADR bodies,
session entries and published changelog sections remain intact. Legacy visual
source/renders remain unchanged, with limitations recorded beside them.

Verification: Ruff lint/format and mypy pass; Windows no-key suite 157 passed,
29 skipped, 97.19% coverage (518/533). The unchanged 100% gate exits nonzero on
this host. Coverage table regenerated from JSON. WSL2 retry fails attaching its
configured disk with HCS/ERROR_PATH_NOT_FOUND, so no fresh GPU evidence. Local
document links/anchors, fenced blocks, CI documentation checks, whitespace,
preserved bytes and unchanged staged diff checked before handoff. No code fixes,
package changes, live NIM calls, cloud spending, runtime repair, commit or push.

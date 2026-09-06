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

## 2026-09-06 ? Commit research checkpoint and implement P1-R1

The owner authorized committing current changes on main and beginning roadmap
work in order. Committed the complete graph/documentation checkpoint locally as
`e8b2060` (31 files), preserving measured data and attribution to the human owner.
No tag: v0.2.0 remains the latest release, and new work stays Unreleased.

Implemented P1-R1: standard-library schema-2 validation shared by writer,
plotter, narrator and CI; legacy measured and labeled synthetic inputs retain
explicit read behavior. Validate finite numbers, required values, sample/count
and summary consistency, experiment arms and target/control consistency.
Exclusive creation prevents overwrites and late competing-writer collisions;
paired figures reserve both paths and clean up owned outputs on exceptions.
Makefile runs use UUID names and plot defaults are run-specific. Figure backend
labels now use recorded targets. ADR 008 records compatibility and crash limits.

Verification: 219 passed, 29 skipped with no NIM key; 703 statements / 15 missed,
97.87% coverage. All new/changed evidence modules have 100% statement coverage.
Full --cov-fail-under=100 remains nonzero on Windows; threshold unchanged. Ruff
lint/format and mypy (15 source modules) pass after formatting correction. The
required WSL2 retry fails with HCS/ERROR_PATH_NOT_FOUND attaching its configured
disk. No fresh GPU run, live NIM request or runtime repair. Official Action
release checks return checkout v7.0.1, setup-python v7.0.0, codecov-action v7.0.0,
action-gh-release v3.0.3; existing floating majors remain current.

P1-R1 implementation is locally verified; full Linux/CI verification and release
readiness remain open. Next implementation is P1-R2 provenance/outcome retention.
No push or release was performed. Historical JSON, figures, prior session/ADR
bodies and release notes remain unchanged; updated live docs distinguish the
current implementation from the earlier dated audit findings.

## 2026-09-06 — P1-R2 traceability, human review and release gates

Implemented P1-R2 in roadmap order after 1255c4d. Schema 3 records source
revision/dirty state and execution-source hashes, resolved installed packages,
actual CuPy device PCI identity, GPU UUID, CUDA driver/runtime and CUDA-Q
target/precision. Monitoring follows the selected device; the measured protocol
rejects ambiguous multi-device visibility. Source changes during timing reject
the new archive. Versions 1/2 remain readable and all measured JSON is preserved.

Classical timings retain every partial sum and its derived estimate; no separate
post-timing estimate replaces them. QAE retains every outcome/count distribution,
queried precision and optional per-repeat seed. Ties use stable bitstring order.
Seeds do not establish cross-platform determinism. Seeded tensornet is outside
the currently validated protocol; current CUDA-Q tensor controls were checked
in official documentation rather than treating old API limitations as current.

New findings require human review sidecars for every paragraph, bound to exact
source/draft hashes. No approvals were invented. CI checks new findings and
preserves two historical pre-sidecar documents at fixed hashes. Release preflight
checks tag/version/notes/checkout/main ancestry, then a reusable CI run gates the
write-permission publish job. Release scripts join coverage/mypy. Removed the
non-kernel TYPE_CHECKING exclusion without changing JIT circuit operations.

Verification: 269 passed, 29 skipped; 942/945 statements, 99.68%. Every new or
changed module has 100% statement coverage. Fake-backend wrapper coverage is
distinct from real JIT/GPU integration. The full 100% command still fails on
Windows because quantum/backend diagnostic paths are unavailable. Ruff/mypy,
legacy run validation, findings-archive checks and doc checks pass. WSL2 retry
fails with HCS/ERROR_PATH_NOT_FOUND; no fresh GPU or seeded run, live NIM call,
reviewer approval, cloud spending, runtime repair, tag or push occurred.

Official Action versions checked: checkout v7.0.1, setup-python v7.0.0,
codecov-action v7.0.0 and action-gh-release v3.0.3; floating majors unchanged.
ADR 009 records decisions and limitations. P1-R2 implementation is locally
verified; P1-R3 protocol/profiling and fresh runtime evidence are next.

## 2026-09-06 — Independent re-verification of P1-R2 and commit

Picked up P1-R2 where the previous session stopped mid-verification: the
implementation and documentation were complete in the working tree but nothing
was committed, and the final format/test gate had not been re-run after the last
edits to `benchmarks/run_file.py` and `quantum/qae.py`.

Re-ran every gate on this Windows host rather than carrying the previous
session's numbers forward. `ruff format --check` failed on those two files —
trailing whitespace introduced by the last edits — and was corrected with
`ruff format`; no logic changed. Ruff lint, `ruff format --check` and mypy
(19 source modules, now including `scripts`) then pass.

Full suite with the NIM key removed: **269 passed, 29 skipped**, 945 statements,
3 missed, **99.68%**. The three uncovered lines are `quantum/backend.py:80-92`,
the CUDA-Q backend diagnostic, unavailable without cudaq — the documented
Windows shortfall, not a new gap. Every other module including all P1-R2
additions (`benchmarks/provenance.py`, `analysis/review.py`,
`scripts/release_check.py`) is at 100%. The `--cov-fail-under=100` command still
exits nonzero here; the gate is unchanged and CI remains authoritative.
Note: pytest's `tmp_path` needs an explicit writable `--basetemp` under this
session's sandbox, otherwise 96 fixture errors mask the real result.

Also verified independently: legacy archive validation
(`python -m benchmarks.run_file`), the findings-review archive check
(`python -m analysis.review --archive benchmarks/runs`), `git diff --check`,
both workflow YAML files parse with the expected jobs (`ci`: lint/typecheck/
tests/docs; `release`: preflight/quality/release), `ci.yml`'s `push`/
`pull_request` triggers survived the `workflow_call` addition, and
`scripts.release_check v0.2.0` fails closed as designed because HEAD is not the
tagged commit, writing no `release_notes.md`.

WSL2 was retried and fails identically:
`Wsl/Service/CreateInstance/MountDisk/HCS/ERROR_PATH_NOT_FOUND`. The cause is
now pinned down — `%LOCALAPPDATA%\wsl\` is empty, so the registered `Ubuntu`
distro points at a deleted `ext4.vhdx`. This is a machine-level break needing
the owner's decision (re-create the distro and reinstall the cudaq venv); it is
not a repo defect. CUDA-Q coverage, GPU measurement and any seeded reproduction
therefore remain unverified, as P1-R2's roadmap entry already states.

No new measured run, live NIM call, tag or push. Next task is P1-R3.

## 2026-09-06 — P1-R3 measurement protocol, phase timing and analytic QAE reference

Continued in roadmap order after committing P1-R2 as `500a153`. Implemented
every P1-R3 item that does not require a GPU, and left the two that do
explicitly open rather than marking the gate complete.

Committed the protocol as code. `benchmarks/protocol.py` declares timing
boundaries, warm-up policy, exclusion rule, stopping rule and uncertainty
method as module constants, so changing any of them is a reviewable diff.
Schema 4 carries the declaration and its SHA-256. The digest is recomputed from
the declaration the file itself carries, never from the current module —
otherwise every past run would fail validation the moment the protocol changed,
which is backwards. Summaries gained standard error and a two-sided 95%
Student's t interval from a small table (no scipy: the core requirements file
must stay CPU-installable). Between tabulated degrees of freedom it falls back
to the nearest lower entry, overstating the interval rather than understating.

Separated the timing phases. `classical.cuda_kernel.time_phases` measures
kernel-handle acquisition, allocation, device execution, transfer and host
reduction, using CUDA events for the device phase and perf_counter for the
host phases, and reports the leftover as `unattributed_s` instead of scaling
the parts up to the whole. `partial_sum` was deliberately left unchanged:
altering it would break comparability with the only archive this repo has, so
phase attribution is a new measurement beside the old one. Noted for P1-R4:
`_load_kernel()` builds a `RawModule` on every call inside the timed region,
which is a plausible explanation for the audit's 2.714 ms two-term mean — but
that is a hypothesis, recorded as one, not a finding.

Derived the QAE quantization instead of asserting it. `quantum/quantization.py`
is closed-form, CPU-only, no cudaq import, nothing timed. It computes the ideal
outcome, absolute and relative error floor, the plateau bounds and the exact
two-peak distribution (Grover's eigenphases theta and 1-theta, averaged
Dirichlet kernels, normalizing to 1.0 to 1e-14). Strongest available check: all
15 archived QAE rows agree with theory to 1e-12, and 8 of them landed on the
conjugate peak 2^m - y, which recovers an identical estimate — so agreement is
asserted on the recovered estimate, never the raw integer. The plateau comes
out as the finite range m = 10..17, confirming the correction P1-R2 made to the
earlier "improves no further" wording. `harness.quantization_report` attaches
this comparison to every measured QAE row.

Verification on this Windows host: 316 passed, 29 skipped; 1130 statements, 3
missed, 99.73%. Every module is at 100% except `quantum/backend.py:80-92`, the
CUDA-Q diagnostic, which needs cudaq. No `# pragma: no cover` was added — the
five that exist are all CUDA-Q kernel bodies. Ruff lint/format, mypy (21 source
modules), legacy archive validation, the findings-review archive check and
`git diff --check` all pass. The schema bump to 4 kept the only measured
archive readable, asserted by a test.

Not done, and blocked rather than deferred: profiling representative cases
needs a GPU, and re-establishing the Linux/WSL2 runtime is machine maintenance
on the owner's box — `%LOCALAPPDATA%\wsl\` is empty, so the registered Ubuntu
distro points at a deleted ext4.vhdx and must be re-created with the cudaq venv
reinstalled. Both P1-R3 checkboxes stay unticked. No dispatch-bottleneck or
arithmetic-bound claim is made anywhere, `time_phases` has never executed on
real hardware, and no new measured run, tag or push was produced.

Tag question raised by the owner and answered: no tag yet. `scripts.release_check`
verifies main ancestry against `origin/main`, and all four commits are unpushed,
so a tag would fail its own preflight; CI has never run on this work; and P1-R3's
exit criteria require fresh integration evidence that does not exist. The
sequence is push main, let CI verify, finish P1-R3/R4, then tag v0.3.0 with the
version and CHANGELOG bump in one commit.

## 2026-09-06 — Rebuild the WSL2 runtime and close P1-R3 with real profiling

The owner asked me to fix the WSL2 blocker before pushing. Diagnosed it
properly first rather than reinstalling blind: both `Ubuntu` and `Ubuntu-22.04`
registrations pointed into `%LOCALAPPDATA%\wsl\`, which was empty, and no
`ext4.vhdx` existed anywhere on C: for either. The other three distros
(docker-desktop, podman, NVIDIA-Workbench) were intact elsewhere, and WSL
2.7.12.0 itself booted fine. So this was data loss, not a detached disk, and
the `~/q1729-cudaq` venv was gone. No restart was needed.

My first proposal was wrong and the owner corrected it: I suggested installing
a differently-named `Ubuntu-24.04` alongside the dead registration, because the
auto-mode classifier blocked `wsl --unregister`. He said "dont create multiple
distros - lets fix it correctly." He is right — a parallel distro would leave a
phantom entry and split the documented workflow. Recorded as a durable
preference. He then ran the unregister and reinstall himself.

`wsl --install -d Ubuntu` now yields **Ubuntu 26.04 "resolute" with Python
3.14**, which cudaq cannot use. Re-verified against PyPI rather than trusting
the docs: `cuda-quantum-cu13` 0.15.1 still publishes cp311/cp312/cp313 only, no
cp314. Ubuntu 26.04 packages no python3.12 or python3.13 at all, so the venv is
a uv-managed CPython 3.13.15 (`apt install pipx`, `pipx install uv`, `uv python
install 3.13`, `uv venv --python 3.13 ~/q1729-cudaq`). Note `uv venv` seeds no
pip, so installs go through `uv pip install --python ~/q1729-cudaq/bin/python`.

Second cudaq-imposed cap discovered and documented: `cuda-quantum-cu13` requires
`cupy-cuda13x~=13.6.0`. cupy-cuda13x 14.2.0 exists and installs cleanly on its
own, so a future session following the tech-currency rule would try to bump it
and break cudaq. AGENTS.md now records this alongside the Python cap.

Verified on the restored host: cudaq 0.15.1 selects the `nvidia` target, cupy
13.6.0 binds PCI 0000:01:00.0, CUDA runtime 13000 / driver 13040, NVIDIA driver
616.56, RTX 5070 Laptop GPU 7.93 GiB, compute capability 12.0. Full suite:
**344 passed, 1 skipped, 100.00% coverage** — every module at 100%. This is the
first time the 100% gate has actually been met; Windows structurally cannot.
The single skip is the live NIM test with no API key.

With the GPU available I closed P1-R3's last two boxes by actually profiling
rather than deferring. `time_phases` on the classical arm, reproduced twice at 7
repeats, in milliseconds: n=2 end-to-end 4.05 of which kernel_handle 3.08 and
device execute 0.030; n=64 3.58 / 3.09 / 0.087; n=1024 6.53 / 3.39 / 2.50;
n=16384 69.96 / 3.62 / 65.85. kernel_handle is per-call RawModule construction
and is constant at ~3.1-3.9 ms regardless of n, so it is ~92% of the two-term
measurement and ~1% is arithmetic.

That settles the audit's disagreement in both directions instead of picking a
side: the device really is sub-millisecond at small n (~30 microseconds) and
the archived 2.714 ms end-to-end really is milliseconds — they were measuring
different things, which is precisely the failure the committed protocol exists
to prevent. Below roughly n = 1024 the classical arm's wall time measures
Python, not the GPU, and the crossover figure must be read that way.

Limits held deliberately: the profiling ran at an unrecorded power profile and
wrote no archive, so it is a diagnostic and not evidence. The quantum arm was
not profiled at all, so no per-gate dispatch claim is licensed anywhere. No run
file, tag or push was produced by this entry. Next is P1-R4, the first archived
run under the committed protocol with a declared power profile.

## 2026-09-06 — First CI run on the unreleased work, and the bug it caught

Pushed the four unreleased commits to `main`; this was the first time CI had
seen any of the P1-R1/R2/R3 work. Lint, mypy and docs passed, coverage reached
100.00% on CI as well — and one integration test failed:
`test_reported_circuit_shape_matches_the_analytic_prediction`,
`assert 16384 == (8 * (2 ** 10))`.

A genuine bug, not a flake. P1-R2 made `quantum.qae.statevector_bytes`
precision-aware, so a complex amplitude is 8 bytes on an fp32 target and 16 on
fp64. The integration test still hardcoded the fp32 factor. It therefore passed
on the RTX 5070, which selects `nvidia` (fp32), and failed on CI, which runs
`qpp-cpu` (fp64). The Windows host skips integration tests entirely, so no local
host could have caught it — the three-way split in ADR 005 is exactly what
surfaced it, and pushing before tagging is what made that split useful.

Fixed by deriving the expected size from the result's own reported precision
rather than assuming a target. Verified both paths on the GPU host by forcing
`CUDAQ_DEFAULT_SIMULATOR`: `nvidia` and `qpp-cpu` each pass. Full suite on the
GPU host remains 344 passed, 1 skipped, 100.00%.

Sequencing note: the P1-R4 archived run was deliberately held until CI is green,
so the run's recorded source revision is a verified commit rather than one later
amended. The owner switched the laptop to the Turbo power profile for that run
(verified: scheme GUID 6fecc5ae, GPU idle at 57 C on AC), matching the
2026-08-05 archive so the two are comparable.

## 2026-09-06 — P1-R4: first archived run under the committed protocol

CI went green on `0543373` (all four jobs), which was the precondition I had set
for collecting evidence, so the run's recorded revision is a verified commit.

Two preconditions were fixed before measuring rather than after. The tree showed
one modified file (an uncommitted `docs/setup.md` edit), so that was committed
first as `15c0da6` — docs only, cannot affect a measurement. And WSL git had
reported a false dirty source: 41 tracked files appeared modified purely because
the checkout is shared with Windows, whose system config sets
`core.autocrlf=true`, while a fresh Linux git leaves it unset. Setting it in the
distro brought `provenance.source()["dirty"]` to `False`. Without that every
archive would have claimed a dirty source identical to its own commit.

The owner switched the laptop to Turbo and I verified it (scheme GUID 6fecc5ae,
GPU idle 50 C on AC) before starting, so the run is comparable to the
2026-08-05 archive rather than confounded by power profile.

Collected `benchmarks/runs/2026-09-06-1286200412954fb4a59cac02c27a06df.json`: schema 4,
protocol digest 24d1d3af702a, clean source 15c0da6, target nvidia/fp32, driver
616.56, turbo, 4000 shots, 5 repeats, 27 rows, 2m18s. Figures written to a
run-specific directory. The old archive was not touched and both validate.

Comparison, like-for-like on profile and shots. The classical arm reproduces
within +/-12% across all 12 term counts, with the large-n points closest
(16384 terms 68.997 -> 67.584 ms) and saturation unchanged at 16.00 correct
digits. QAE timing shifted systematically with register size: m=2 is ~25%
faster and m=15/16 are ~7-10% slower, crossing near m=14. Small-m cost is
dominated by fixed per-call overhead and large-m by statevector work, so a
driver change could plausibly move them in opposite directions — but this run
did not isolate that and thermal drift across the sweep is not excluded, so it
is recorded as an observation and explicitly not as an explanation.

The strongest check: all 15 QAE rows reproduce the archive's pi estimate to
1e-12, every row agrees with closed-form theory, and each sampled distribution
sits below its own sampling tolerance. Quantization is deterministic, so that is
the expected outcome — and it is what makes the timing comparison meaningful,
since both runs demonstrably computed the same thing. Nothing was selected
across runs; this was the first run under the protocol and it is archived
whatever it showed.

P1-R4 is **not** closed. The findings document needs a human review record and
agents must not approve on a reviewer's behalf, so no tag is cut. A findings
draft plus a pending review template is being prepared for the owner; adding a
findings Markdown file to the archive before its review record is complete would
fail CI by design.

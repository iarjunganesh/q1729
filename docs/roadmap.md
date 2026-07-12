# Q1729 — Vision & Roadmap

> **Vision:** Build Q1729 into the most trusted open-source computational
> research platform for studying the boundary between classical, accelerated,
> and emerging computational paradigms.

> This is the single source of truth for where Q1729 is going. Every idea from
> the original Blueprint v1.0 survives here — what changes is **order**: each
> layer of architecture is earned by a real result before it is built, never
> imposed ahead of one.

The **README** remains authoritative for *what the project is today* and its
three-stage research thread. This document is authoritative for *how the project
grows* — the North Star it serves and the sequence in which it earns its
architecture. The two are kept consistent: the README's Stage 1 is this
roadmap's Phase 1; the README's Stage 3 is this roadmap's Phase 2.

---

# North Star

Q1729 is **not** a benchmark repository.

Q1729 is a **research platform**.

Principles:

1. **Reproducibility over convenience.**
2. **Measured data over anecdotes.**
3. **Architecture over feature accumulation.**
4. **Extensibility over hard-coding.**
5. **Education alongside engineering.**
6. **AI explains results; it never invents them.**

These six principles are adopted in Phase 0 and upheld through every phase that
follows. Principle 6 is enforced in code today by ADR-003: the NIM/Nemotron
narrator narrates run-file numbers and never simulates.

---

# Roadmap Philosophy

Every phase exists to earn the right to build the next one.

Q1729 deliberately evolves from evidence to abstraction:

```
Working Result
  → Repeated Result
    → Recognized Pattern
      → Shared Abstraction
        → Extensible Platform
```

At no point is architecture introduced solely because it appears desirable.
Every abstraction must be justified by real experimental evidence and must
reduce the cost of future research.

Each phase answers three questions:

- **Why now?** What evidence makes this the correct time to begin?
- **Why not earlier?** What speculative design is intentionally being avoided?
- **What becomes possible afterwards?** What new capabilities does this phase unlock?

Every phase must produce something independently valuable even if no later phase
is ever completed.

---

## Where the repo actually is (v0.1.0)

Honest baseline, so every phase below is measured against reality:

- Excellent engineering hygiene already exists: 3 ADRs, CI, coverage gated at 95%, CONTRIBUTING, SECURITY, a working NIM narrator, backend-selection logic.
- `classical/ramanujan_series.py` is exact SymPy — the **ground truth**, not the CUDA kernel.
- **No `.cu` kernel exists yet.** The repo is 97.4% Python.
- `data/sample_run.json` is **synthetic**. No real benchmark has been run.

The core result the whole project exists to produce has not been produced once.
That single fact sets the order of everything below.

---

## Phase sequence at a glance

| Phase | Name | Exit artifact |
|---|---|---|
| **0** | Constitution (lightweight) | Principles + research-standards committed |
| **1** | The First Real Result | One measured crossover run + writeup |
| **2** | The Second Experiment | qLDPC/graphs run reusing Phase 1 by hand |
| **3** | Extract the Experiment Engine | Abstraction refactored *from* real code |
| **4** | Backend Independence | 2nd backend behind the same interface |
| **5** | Research Intelligence | Stats + regression + publication figures |
| **6** | Ecosystem & Governance | RFC process, docs site, release automation |

---

# Engineering Principles

Beyond the project's North Star principles, the roadmap itself follows these engineering rules:

- Prefer evolutionary architecture over revolutionary rewrites.
- Abstractions are extracted from working systems, never imposed on empty scaffolding.
- Optimize only after measurement.
- Documentation explains intent; code explains implementation.
- Every architectural abstraction should reduce the effort required to build the next experiment.
- New contributors should understand *why* the architecture exists before learning *how* it works.

---

# Anti-Roadmap

Q1729 deliberately refuses to:

- Optimize before measuring.
- Introduce abstractions without multiple concrete implementations.
- Publish benchmarks that cannot be independently reproduced.
- Add AI features that generate unsupported conclusions.
- Chase every accelerator, framework, or research trend without a concrete experimental need.
- Introduce governance before multiple maintainers actually exist.
- Build infrastructure that has no immediate research value.

This section serves as the project's non-goals. Anything on this list requires an ADR to overturn.

---

## Phase 0 — Constitution (lightweight)

**Why now?** These documents cost hours, not weeks, and they shape every run that follows. Delaying them means running the first experiment without a contract for what makes it valid.

**Why not earlier?** Nothing precedes this phase.

**What becomes possible afterwards?** Every future run has a defined standard of evidence; every future design decision has principles to be evaluated against.

**Do now:**
- `docs/handbook/principles.md` — the six North Star principles above, one page.
- `docs/handbook/research-standards.md` — the required contract every experiment must define before it runs. The canonical contract is [Research Standards](#research-standards) below: **question, hypothesis, variables, controls, hardware, software versions, statistical treatment, raw data, limitations.**
- The **Anti-Roadmap** section above serves as the non-goals document — link it from the handbook.
- Link the handbook from the README and from `docs/adr/README.md`.

**Explicitly deferred to later phases:** architecture handbook, glossary, contributor expectations. They are written when there is architecture and contributors to describe — Phases 3 and 6.

**Independently valuable because:** even if nothing else ships, the repo gains a public, citable standard of evidence — rare in benchmark projects.

**Exit criteria:** principles and research-standards are committed, and the next run cannot begin without filling in the research-standards contract.

---

## Phase 1 — The First Real Result

**Why now?** The entire repo exists to produce this result, and it does not exist yet. Everything else in the Blueprint is in service of it.

**Why not earlier?** N/A — this is as early as it can be. The premature design being avoided: building any engine, plugin API, or multi-backend layer before a single measured number exists.

**What becomes possible afterwards?** Publication, community benchmark submissions against real data, and — after one more experiment — honest abstraction.

**Build, in order:**
1. **The CUDA kernel.** `classical/` gets a real hand-written CUDA C++ kernel: one Ramanujan term per thread, parallel reduction to the partial sum. Validated against the existing exact SymPy ground truth so any float drift surfaces immediately.
2. **The QAE path on real silicon.** Run the CUDA-Q Quantum Amplitude Estimation circuit on the `nvidia` (cuStateVec) backend in WSL2 on the RTX 5070 — the verified target from ADR-002.
3. **The real run file.** Replace `data/sample_run.json` with **measured** data: timing, VRAM, qubit ceiling, digit count, and the `hardware` field. This run file must satisfy the Phase 0 research-standards contract.
4. **One crossover plot.** Time (and VRAM) vs digit count / qubit count, classical vs quantum, on a single figure. Save under `benchmarks/`.
5. **The narrator writes it up.** Feed the real run file to the existing NIM narrator to draft the findings, under the ADR-003 guardrail (numbers in, prose out — never invented).
6. **The datacenter axis (optional within this phase).** Repeat the QAE path once on a rented H100 (`nvidia-mgpu`) to get the second point on the crossover curve. If time-boxed out, this rolls to the start of Phase 2 — it does not block publication of the RTX result.

**Independently valuable because:** a reproducible RTX-5070 crossover analysis is a publishable, portfolio-grade result on its own — even if the platform vision never materializes.

**Exit criteria:** a reproducible, measured crossover result exists in the repo with a narrator-drafted writeup, all conforming to the research-standards contract. `sample_run.json` is no longer the only data in the repo.

**Why this is the hinge:** until this exists, no abstraction has anything to abstract over. This phase converts the repo from "well-scaffolded skeleton" into "answers one specific question with real evidence" — which is the whole differentiator.

---

## Phase 2 — The Second Experiment

**Why now?** One working result exists (Phase 1). A second, structurally similar experiment is the minimum evidence base for recognizing a genuine pattern.

**Why not earlier?** Running it before Phase 1 published would split focus across two unfinished experiments. The premature design being avoided: generalizing the runner/collector flow off a single data point.

**What becomes possible afterwards?** Honest abstraction — the shared shape of two real experiments becomes visible through use, not guesswork.

**Do:**
- Implement the **Stage 3 thread from the README** as the second experiment: Ramanujan expander graphs → quantum LDPC codes, simulated/decoded with CUDA-Q QEC (CUDA-QX) plus custom kernels.
- Deliberately **copy-paste and adapt** the Phase 1 runner/collector/plot flow rather than prematurely generalizing it. The duplication is intentional — it is the data that will drive Phase 3.
- Produce a second real run file + writeup under the same research-standards contract.
- **Community starts here but stays minimal:** invite benchmark submissions of the Phase 1 run on other GPUs (the run-file schema is already hardware-agnostic). Add the benchmark-submission issue template *now* because there is finally real data worth submitting against. Governance still deferred.

**Independently valuable because:** the qLDPC experiment stands alone as an open, reproducible QEC lab — the README's Stage 3 promise, delivered.

**Exit criteria:** two real experiments exist in the repo, each with measured data, and the duplication between them is obvious and slightly painful. That pain is the signal to begin Phase 3.

---

## Phase 3 — Extract the Experiment Engine

**Why now?** Two working experiments share visible, felt duplication. The Recognized Pattern step of the philosophy ladder has been reached with evidence.

**Why not earlier?** Designing the engine off zero or one experiment would encode guesses. The premature design being avoided: the full ten-package `src/q1729/` layout built as empty scaffolding.

**What becomes possible afterwards?** Experiment #3 becomes cheaper than #2 was — the only honest justification an abstraction has.

**Do:**
- Introduce the Blueprint's pipeline as a refactor, not a rewrite:
  `Research Question → Hypothesis → Experiment → Runner → Collector → Statistics → Report → Archive`.
- Migrate to the [`src/q1729/` layout](#repository-target-layout) **incrementally**, adding a package only when a real experiment already needs it:
  - `core/`, `experiments/`, `runners/`, `reporting/` first — because Phases 1–2 already exercise these.
  - `statistics/`, `visualization/` when Phase 4/5 need them.
  - `plugins/`, `cli/` last.
- Write the **architecture handbook** and **glossary** deferred from Phase 0 — there is now real architecture to document.
- Add the metadata schema, result model, and JSON/CSV/Parquet outputs from the Blueprint's Experiment Engine — driven by what the two experiments actually emitted.

**Independently valuable because:** even frozen here, the repo would be two rigorous experiments running through one clean, documented engine.

**Exit criteria:** both existing experiments run through one shared engine with no externally observable behavior change and no loss of the exact-ground-truth validation.

---

## Phase 4 — Backend Independence

**Why now?** A stable engine exists (Phase 3), and a real experiment demands a second backend — the forcing function that proves the interface.

**Why not earlier?** Abstracting across backends before one produced a number is speculative generality. The premature design being avoided: a plugin API shaped by imagined ROCm/SYCL/JAX needs rather than one concrete integration.

**What becomes possible afterwards?** Community benchmark submissions from non-NVIDIA hardware; the crossover analysis gains new axes.

**Do:**
- Formalize the plugin/backend API around the backends **already in use**: CUDA, CUDA-Q, CPU (`qpp-cpu`). The interface is extracted from the existing `quantum/backend.py` selection logic, which already does `nvidia → tensornet → qpp-cpu`.
- Add exactly **one** new backend from the Blueprint's future list (ROCm, SYCL, Triton, JAX, OpenMP) — chosen because a real experiment needs it.
- Do not add the remaining backends until an experiment demands each. Each one is a pull, never a push.

**Independently valuable because:** a proven two-backend interface is itself a reference design for accelerator-portable benchmarking.

**Exit criteria:** the same experiment runs unmodified across at least two genuinely different backends behind one interface.

---

## Phase 5 — Research Intelligence

**Why now?** An archive of real runs exists across experiments and hardware — statistics finally has a population, not a sample of one.

**Why not earlier?** Confidence intervals over one run are decoration. The premature design being avoided: building analysis infrastructure before there is data to analyze.

**What becomes possible afterwards?** Statistically defensible publications and automatic detection of regressions across releases.

**Do:**
- Statistical analysis + confidence intervals over repeated runs.
- Regression detection: flag when a new run is meaningfully slower/heavier than the archived baseline for the same hardware.
- Evolve the narrator from single-run drafter into the tiered analyst: research-assistant mode (question-grounded), then lab-notebook accumulation across runs — still under the ADR-003 never-invent guardrail.
- Publication-quality figure generation in `visualization/`.

**Independently valuable because:** the run archive + regression detection is useful to every contributor from the day it lands.

**Exit criteria:** the project can produce a statistically defensible, explainable writeup from its run archive without manual plotting.

---

## Phase 6 — Ecosystem & Governance

**Why now?** External interest actually exists — forks, submitted benchmarks, contributors. There are now people to govern and readers to teach.

**Why not earlier?** Per the Anti-Roadmap: no governance before multiple maintainers exist. An RFC process for a solo repo is costume, not process.

**What becomes possible afterwards?** The [Definition of Success](#definition-of-success), in full.

**Do:**
- Documentation site, tutorials, contributor expectations (deferred all the way from Phase 0 — written when there are contributors to expect things of).
- RFC process and governance — introduced when there is more than one decision-maker, so it is real process rather than costume.
- Release automation; milestones v0.2 → v1.0 (see [GitHub Strategy](#github-strategy)).

**Independently valuable because:** each ecosystem piece (docs site, tutorials, automation) reduces maintenance load immediately upon landing.

**Exit criteria:** the [Definition of Success](#definition-of-success) is reachable — researchers reproduce every result, engineers extend without touching core, every decision is documented, every release reproducible — and it was earned one real result at a time.

---

# Roadmap Governance

This roadmap is treated as architecture rather than a TODO list.

Until Phase 6, major sequencing or architectural changes to this roadmap are recorded as **ADRs** in `docs/adr/` — the decision system the repo already uses. This keeps changes intentional, stable, and historically understandable without installing a solo-maintainer RFC process the Anti-Roadmap forbids.

The **RFC process arrives in Phase 6**, when there is more than one decision-maker and roadmap changes genuinely require proposal and review. From that point, major changes go through RFC before implementation.

---
---

# Reference — the platform being earned

Everything below is the durable target the phases above build **toward**. It is
reference material, not a to-do list: nothing here is scaffolded ahead of the
real experiment that needs it (see the Anti-Roadmap). This is where Blueprint
v1.0's architecture, standards, and definition of success now live in full.

## Repository Target Layout

The destination layout, extracted incrementally in Phase 3+ (annotations show the
earliest phase that justifies each package — none is created before then):

```text
src/q1729/
    core/            # Phase 3 — result model, metadata schema, config
    experiments/     # Phase 3 — Ramanujan π (P1), qLDPC (P2)
    runners/         # Phase 3 — run orchestration + collection
    backends/        # Phase 4 — CUDA, CUDA-Q, CPU behind one interface
    statistics/      # Phase 5 — confidence intervals, regression detection
    visualization/   # Phase 5 — publication-quality figures
    reporting/       # Phase 3 — JSON/CSV/Parquet outputs, writeups
    ai/              # Phase 5 — narrator as tiered analyst (ADR-003 guardrail)
    plugins/         # Phase 4+ — third-party backends/experiments
    cli/             # Phase 3+ — unified command-line entry point

docs/
    handbook/        # Phase 0 principles + research-standards; Phase 3 architecture + glossary
    adr/             # in use today — architecture decision records
    rfc/             # Phase 6 — proposals once >1 decision-maker exists
    tutorials/       # Phase 6
    architecture/    # Phase 3
    roadmap/         # this document

benchmarks/          # Phase 1 — real run files + crossover plots
papers/              # published writeups
results/             # archived run files across hardware
examples/
notebooks/
```

## Engineering Standards

Every PR should include, where applicable:

- **Tests** — new modules ship with tests that cover them fully (near-100% coverage is the standard; CI gates at 95%).
- **Documentation** — intent-level docs for anything a contributor would otherwise have to reverse-engineer.
- **ADR (or, from Phase 6, RFC) reference** if the change is architectural.
- **Benchmark impact** if the change touches a measured path.
- **Changelog entry** — CHANGELOG.md follows Keep a Changelog; the release workflow extracts the tagged version's notes from it.

## Research Standards

Every experiment must define, before it runs — this is the Phase 0 contract, enforced from the first real run in Phase 1:

- **Question** — the specific question the run answers.
- **Hypothesis** — the expected outcome and why.
- **Variables** — what is being varied (e.g. digit count, qubit count).
- **Controls** — what is held fixed.
- **Hardware** — the exact silicon (recorded in the run file's `hardware` field).
- **Software versions** — CUDA, CUDA-Q, driver, Python, package versions.
- **Statistical treatment** — repetitions, confidence intervals, how outliers are handled.
- **Raw data** — the run file itself, archived, reproducible.
- **Limitations** — what the run does *not* establish.

## GitHub Strategy

- **Project:** Roadmap (this document, tracked as issues once Phase 3's architecture defines them — per the Blueprint, issues are created only after the architecture they touch is defined).
- **Milestones:** v0.2 → v0.3 → v0.4 → v0.5 → v1.0 (the repo is at v0.1.0 today).
- **Epics:** Foundation · Experiment Engine · Plugin System · Benchmarking · AI · Visualization · Documentation · Governance — each maps onto a phase above.

## Definition of Success

A 10/10 Q1729 repository is one where:

- Researchers can **reproduce every published result**.
- Engineers can **extend it without modifying the core**.
- Educators can **teach from it**.
- AI **augments analysis without fabricating evidence**.
- **Every architectural decision is documented.**
- **Every benchmark is statistically defensible.**
- **Every release is reproducible.**
- The project is **respected for engineering rigor rather than feature count**.

## Final Goal

Become the reference implementation for modern computational research
engineering — not merely for CUDA or quantum computing, but for how rigorous
computational experiments should be designed, executed, analyzed, documented,
and shared.

---

## Provenance

This document supersedes and absorbs **Blueprint v1.0** in full — its Vision,
North Star, 24-month roadmap, repository target layout, engineering and research
standards, GitHub strategy, and definition of success all live here. Nothing was
dropped; the 24-month platform vision is intact, re-sequenced so each layer is
shaped by evidence from the layer beneath it, and so the project always has a
sharp, specific identity while it grows into the general one.

*Author: Arjun Ganesh — github.com/iarjunganesh/q1729*

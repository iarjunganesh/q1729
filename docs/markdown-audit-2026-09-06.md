# Markdown audit — 2026-09-06

## Scope and method

Read all **26 original authored Markdown files, 3379 lines**, including the
ignored local audit note, from first line to last. Excluded dependency/tool
caches, `.git`, virtual environments and generated audit backups. This is an
audit of prose, commands and research claims against the code and available
evidence, not a claim that every historical statement was freshly rerun.

The inventory below uses **original line numbers**, before these edits.
The local `.tmp/markdown-audit-before-2026-09-06.json` records starting line
counts and SHA-256 hashes. Historical ADR bodies, session history and published
changelog sections are preserved. Measured JSON is unchanged. Existing staged
work is retained and the index is untouched. This revision changes documentation;
implementation defects below remain open.

## Main findings and resolution

| Original location | Finding | Resolution / remaining gate |
| --- | --- | --- |
| README 56–88; findings 1–32 | Universal no-crossover, 2-term timing mismatch, utilization paired across different rows, causal dispatch/H100 predictions | Corrected live interpretation; preserved original draft; profiling remains P1-R3 |
| README 98–107, 135–140; principles 60–70 | AI prose described as incapable of inventing claims; diagram conflated series/QAE and verified cloud execution | Explicit unchecked-draft boundary and accurate inline diagram; legacy source/renders still need correction |
| AGENTS 31–55; roadmap 75 onward | Delivered archive conflated with readiness; graph numerical spectrum called proof | Honest baseline and reopened Phase 1 gates; Phase 2 graph-only status |
| research standards 3–4, 31–39; AGENTS 210–225 | Key checks called contract enforcement; hypothesis constant called proof of pre-run commitment | Requirements/gaps separated; archive labeled exploratory; P1-R1/R2 open |
| setup 8, 97–120; onboarding 103–108 | Kernel/harness/QAE wrongly described as absent | Replaced with actual implemented/planned inventory |
| README 181–197; setup 130–139 | Copying `.env` implied configuration; reproduction omitted archive shots and reused output names | Document process environment and unique paths; atomic writer protection still P1-R1 |
| SECURITY 5–17 | Full JSON payload understated; nonexistent release quality job; render toolchains conflated | Corrected current policy |
| CONTRIBUTING 29–46; AGENTS 81–87 | Historical live-key/WSL counts conflated with current Windows or CI | Coverage regenerated; current no-key result and unavailable WSL2 stated |
| research standards 41–65, 78–81 | Warmup treated as isolation; device memory treated as peak; standard deviation used as disagreement threshold | Timing/memory/uncertainty boundaries corrected; statistical design mandatory now |
| PATHWAYS 1–198; roadmap 1–434 | Competing stages and speculative platform/publishing commitments | One execution roadmap with conditional publication and explicit phase exits |
| ADR 005 65–69 | CPU CUDA-Q integration conflated with skipped GPU integration | Dated correction; old body preserved |
| ADR 006 1–176 | Potential source portability and dispatch explanation overstated | Dated qualifications; actual ROCm study remains conditional Phase 4 |
| CLAUDE 1–12 | More than the required one-line import | Exact `@AGENTS.md` |

## Complete original-file disposition

| Original file | Lines read | Disposition |
| --- | --- | --- |
| `.tmp/q1729-audit-2026-09-06.md` (local scratch) | 1–167 | Preserved dated exploratory audit; open findings mapped to roadmap gates. |
| [AGENTS.md](../AGENTS.md) | 1–406 | Corrected phase status, host evidence, graph proof language, contract/provenance gaps and release claims. |
| [CHANGELOG.md](../CHANGELOG.md) | 1–116 | Updated Unreleased; preserved all published release sections. |
| [CLAUDE.md](../CLAUDE.md) | 1–12 | Reduced to the required one-line import. |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 1–57 | Regenerated per-module Windows coverage; separated current, historical and CI evidence. |
| [README.md](../README.md) | 1–224 | Corrected experiment scope, selected-row timings, AI claims, phase status, setup and hardware interpretation. |
| [SECURITY.md](../SECURITY.md) | 1–21 | Corrected full-JSON external payload, runtime/CI credentials and actual release/render tooling. |
| [assets/architecture/README.md](../assets/architecture/README.md) | 1–58 | Added legacy-illustration caveats; source and both SVG corrections remain a later asset task. |
| [assets/brand/README.md](../assets/brand/README.md) | 1–61 | Added simulation/branding caveat and palette scope; source/renders preserved. |
| [benchmarks/README.md](../benchmarks/README.md) | 1–66 | Corrected result interpretation and documented unique run/figure invocation with remaining writer risk. |
| [benchmarks/runs/2026-08-05-rtx5070-turbo-findings.md](../benchmarks/runs/2026-08-05-rtx5070-turbo-findings.md) | 1–32 | Preserved original draft body; prepended supersession link to a separate reviewed interpretation. |
| [docs/PATHWAYS.md](../docs/PATHWAYS.md) | 1–198 | Replaced competing stages with a short orientation subordinate to README/roadmap. |
| [docs/adr/001-cuda-q-over-pennylane.md](../docs/adr/001-cuda-q-over-pennylane.md) | 1–39 | Preserved body; appended support-status and QEC-scope clarification. |
| [docs/adr/002-wsl2-runtime.md](../docs/adr/002-wsl2-runtime.md) | 1–31 | Preserved body; appended runtime availability and separate-environment clarification. |
| [docs/adr/003-hybrid-cloud-nim.md](../docs/adr/003-hybrid-cloud-nim.md) | 1–39 | Preserved body; appended unchecked-prose, full-payload and schema clarification. |
| [docs/adr/004-repo-hygiene-and-agent-sync.md](../docs/adr/004-repo-hygiene-and-agent-sync.md) | 1–117 | Preserved body; appended import, coverage and release-enforcement clarification. |
| [docs/adr/005-cuda-kernel-via-nvrtc.md](../docs/adr/005-cuda-kernel-via-nvrtc.md) | 1–99 | Preserved body; corrected CI CPU simulator vs GPU tests and timing interpretation by amendment. |
| [docs/adr/006-rocm-as-phase-4-second-backend.md](../docs/adr/006-rocm-as-phase-4-second-backend.md) | 1–176 | Preserved body; appended unverified-port/cost and causal-claim qualifications. |
| [docs/adr/README.md](../docs/adr/README.md) | 1–46 | Added ADR 007 and clarified historical support/portability summaries. |
| [docs/handbook/principles.md](../docs/handbook/principles.md) | 1–80 | Separated requirements from enforcement; corrected cloud, deterministic-output and AI guarantees. |
| [docs/handbook/research-standards.md](../docs/handbook/research-standards.md) | 1–85 | Mapped contract requirements to current gaps; corrected preregistration, timing, memory and uncertainty rules. |
| [docs/nvidia-access.md](../docs/nvidia-access.md) | 1–125 | Removed obsolete price/quota assurances; corrected runtime, key configuration and memory estimates. |
| [docs/onboarding.md](../docs/onboarding.md) | 1–125 | Replaced obsolete scaffold status and demo transcript with implemented/planned inventory. |
| [docs/roadmap.md](../docs/roadmap.md) | 1–434 | Replaced speculative plan with baseline, dependencies, measurable gates, publication path and reassessment rules. |
| [docs/sessions.md](../docs/sessions.md) | 1–406 | Preserved prior entries; appended this audit and verification limits. |
| [docs/setup.md](../docs/setup.md) | 1–159 | Replaced obsolete no-harness claims, stale transcripts and ineffective dotenv guidance; separated host environments. |

New public documents: this audit, ADR 007 and the reviewed findings. They were
also read and checked after creation; they are not included in the original count.
Every source line was reviewed, but unaffected history is retained rather than
annotating thousands of unchanged lines individually.

## What remains open

1. **P1-R1:** overwrite protection and semantic validation at actual entry points.
2. **P1-R2:** complete provenance/outcomes, truthful backend labels, narration
   review process, non-kernel coverage exclusions and release checks.
3. **P1-R3/R4:** restored runtime availability, profiling, prospective protocol,
   meaningful integration checks and one fresh bounded repeat.
4. **P2-A–D:** contribution/literature review, specified classical matrix/decoder,
   controlled CPU/GPU study, then a budgeted validated qLDPC experiment.
5. **Visual source follow-up:** legacy architecture/banner wording needs source
   edits and both-theme regeneration before reusing it as current explanation.

The exploratory full-graph parity-matrix/product parameter calculation is a
feasibility warning, not an implemented quantum code. Literature novelty and
publication readiness are still unverified. The roadmap's publication checklist
is a gate, not a promise of an arXiv paper or acceptance.

## Verification

Ruff lint/format and mypy passed (13 typed source modules). The no-key Windows
suite executed 186 tests: 157 passed, 29 skipped. Coverage is 518/533 statements,
**97.19%**; `--cov-fail-under=100` exited nonzero. This is not a full-gate pass,
and the 100% requirement is unchanged. Coverage table in CONTRIBUTING was
generated from this run's JSON report.

The WSL2 retry, outside the restricted sandbox after its access-denied response,
failed to attach the configured `ext4.vhdx` with `HCS/ERROR_PATH_NOT_FOUND`.
No fresh GPU test/benchmark, live NIM call, cloud rental or runtime repair occurred.
Historical WSL2 results and released-commit CI remain separate evidence.

Local Markdown links/anchors, fenced blocks, current CI documentation checks,
whitespace, preserved artifact bytes and unchanged staged diff are checked before
handoff. No code, workflow, dependency, SVG, measured JSON, tag or release was changed.

# Architecture Decision Records

This directory documents the key decisions made in q1729 and the reasoning behind them.
Each ADR is immutable once merged — superseded decisions get a new ADR. The
[roadmap](../roadmap.md) uses these same ADRs as its change-control mechanism:
until Phase 6, any change to roadmap sequencing or architecture is recorded here.

ADRs record *decisions*. The standards those decisions are evaluated against —
the six principles and the nine-field contract every experiment must satisfy —
live in the [handbook](../handbook/principles.md):
[Principles](../handbook/principles.md) ·
[Research Standards](../handbook/research-standards.md).

---

## Index

| ADR | Title | Status | Summary |
|---|---|---|---|
| [001](./001-cuda-q-over-pennylane.md) | CUDA-Q over PennyLane / Qiskit | Accepted | NVIDIA-native stack gives direct cuStateVec + cuTensorNet access without translation overhead |
| [002](./002-wsl2-runtime.md) | WSL2 as Windows runtime | Accepted | WSL2 is the selected Windows GPU runtime; current availability is checked separately |
| [003](./003-hybrid-cloud-nim.md) | Hybrid cloud + NIM narrator | Accepted | H100 as second hardware axis; Nemotron narrates run files, never simulates |
| [004](./004-repo-hygiene-and-agent-sync.md) | Repo hygiene: AGENTS.md, 100% coverage floor, brand/diagram assets | Accepted | Cross-tool sync discipline, coverage gate raised to literal 100%, theme-aware SVG assets |
| [005](./005-cuda-kernel-via-nvrtc.md) | CUDA kernel compiled via NVRTC, not nvcc | Accepted | The `.cu` file is compiled at runtime by cupy/NVRTC — whole GPU toolchain is pip-installable, no CUDA Toolkit and no build step |
| [006](./006-rocm-as-phase-4-second-backend.md) | ROCm/MI300 is the Phase 4 second backend | Accepted | Classical source stays within a portable subset; runtime port unverified; the quantum arm cannot cross vendors inside CUDA-Q, so an AMD run is a portability result, not a crossover point |
| [007](./007-evidence-first-phase-gates.md) | Evidence-first phase gates and publication path | Accepted | Repair evidence, validate classical decoding then feasible qLDPC, extract shared code after reuse; publication conditional |
| [008](./008-versioned-evidence-validation-and-exclusive-archives.md) | Versioned evidence validation and exclusive archives | Accepted | Shared semantic checks, legacy readers and no-overwrite JSON/SVG creation |
| [009](./009-traceable-outcomes-and-reviewed-releases.md) | Traceable outcomes and reviewed releases | Accepted | Source/device provenance, all timed outcomes, human review sidecars and release quality dependencies |

---

## How to read an ADR

Each ADR contains:
- **Context** — what problem was being solved
- **Decision** — what was chosen
- **Consequences** — what this enables and what it constrains

---

## When to add a new ADR

Open a new ADR when:
- A library or backend is added or replaced
- A data format (run file schema) is changed in a breaking way
- A significant architectural boundary is introduced (e.g. the qLDPC module — README Stage 3 / roadmap Phase 2)
- Roadmap sequencing or architecture changes (per Roadmap Governance in [the roadmap](../roadmap.md), recorded as ADRs until Phase 6)

Template: copy any existing ADR and replace the content.

## 2026-09-06 sequencing revision

[007 — Evidence-first phase gates and publication path](007-evidence-first-phase-gates.md)
is accepted. ADRs 001–006 retain their historical bodies and have dated audit
amendments. WSL2 is the chosen Windows GPU workflow; historical platform-support
and portability statements are not fresh runtime verification.

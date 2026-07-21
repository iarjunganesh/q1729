# Architecture Decision Records

This directory documents the key decisions made in q1729 and the reasoning behind them.
Each ADR is immutable once merged — superseded decisions get a new ADR. The
[roadmap](../roadmap.md) uses these same ADRs as its change-control mechanism:
until Phase 6, any change to roadmap sequencing or architecture is recorded here.

---

## Index

| ADR | Title | Status | Summary |
|---|---|---|---|
| [001](./001-cuda-q-over-pennylane.md) | CUDA-Q over PennyLane / Qiskit | Accepted | NVIDIA-native stack gives direct cuStateVec + cuTensorNet access without translation overhead |
| [002](./002-wsl2-runtime.md) | WSL2 as Windows runtime | Accepted | CUDA-Q is Linux-only; WSL2 gives full GPU passthrough without dual-boot |
| [003](./003-hybrid-cloud-nim.md) | Hybrid cloud + NIM narrator | Accepted | H100 as second hardware axis; Nemotron narrates run files, never simulates |
| [004](./004-repo-hygiene-and-agent-sync.md) | Repo hygiene: AGENTS.md, 100% coverage floor, brand/diagram assets | Accepted | Cross-tool sync discipline, coverage gate raised to literal 100%, theme-aware SVG assets |

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

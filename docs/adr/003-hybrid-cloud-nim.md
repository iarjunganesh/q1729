# ADR 003 — Hybrid cloud: NIM/Nemotron analysis layer + cloud-GPU benchmark axis

**Status:** Accepted — July 2026

## Context

The owner wants q1729 to make wide, realistic use of NVIDIA's cloud stack
(NIM, Nemotron) rather than reading as a purely local-hardware project. But
NIM is an *inference* microservice layer — it serves LLMs, not quantum
circuit simulators. Swapping the CUDA-Q core for NIM would turn q1729 into
another LLM app and erase its differentiator (the consumer-GPU crossover
question). The sibling-repo principle applies: an integration must have a
real job, not decorate a checklist.

## Decision

Adopt the cloud stack in the two places it genuinely earns:

1. **NIM/Nemotron is the analysis layer, never the simulator.**
   `analysis/narrator.py` sends benchmark run data to a Nemotron model via
   the NIM chat-completions API and gets back a findings draft. The LLM's
   job is narration and anomaly-spotting; **every number comes from the run
   file, never from the model**. The layer is optional and degrades exactly
   like cudaq does: no `NVIDIA_API_KEY`, no narrator — nothing else breaks.
2. **Cloud GPUs are a second benchmark axis, not a replacement.** The same
   CUDA-Q code that selects `nvidia` on the RTX 5070 runs unchanged on a
   rented H100/multi-GPU box; benchmark run files carry a `hardware` field
   so consumer-vs-datacenter crossover curves land in the same analysis.

## Consequences

- The repo gains its first secret: `NVIDIA_API_KEY` (`.env` gitignored,
  `.env.example` documents it; SECURITY.md updated)
- Narrator calls go through `httpx` at the module boundary — unit tests mock
  there; a live integration test runs only when the key is present
- The README's identity widens from "one consumer GPU" to "one CUDA-Q
  codebase, consumer to datacenter — with an AI layer that writes up what
  the numbers show"
- Stage-1 deliverable now includes the cloud-GPU comparison run

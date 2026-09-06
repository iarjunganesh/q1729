# Principles

The six commitments q1729 is built on. Adopted in
[roadmap Phase 0](../roadmap.md#phase-0--constitution-lightweight); every phase
after it is held to them.

These are adopted requirements. Each names supporting mechanisms; the audit
found incomplete enforcement, tracked in Phase 1. A written rule is not proof
that every artifact satisfies it.

---

## 1. Reproducibility over convenience

A number nobody else can regenerate is not a result. Every measured claim ships
with the run file that produced it, and every run file carries the machine, the
software versions, and the controls that were held fixed
([research standards](research-standards.md)).

*Enforced by:* `benchmarks/harness.py` writes the environment block
automatically rather than relying on anyone to remember it; the CUDA kernel sums
block partials on the host instead of using `atomicAdd`, avoiding nondeterministic atomic reduction order. Cross-hardware/toolchain
bit identity and complete provenance are not guaranteed.

## 2. Measured data over anecdotes

"Faster", "should scale", and "roughly" are not findings. Claims in this repo
are either accompanied by measurements or explicitly labeled as unverified.

*Enforced by:* `data/sample_run.json` is labeled synthetic in the file itself and
`benchmarks/plot.py` refuses to plot it; `AGENTS.md` requires every session to
re-verify the dated claims it is responsible for rather than carrying them
forward from memory.

## 3. Architecture over feature accumulation

Abstractions are extracted from working code, never imposed on empty scaffolding.
A package is created when a real experiment already needs it, not when it seems
likely to be needed later.

*Enforced by:* the [Anti-Roadmap](../roadmap.md#anti-roadmap) — overturning it
requires an ADR — and the phase ordering, which puts the experiment engine
(Phase 3) after two real experiments exist to extract it from.

## 4. Extensibility over hard-coding

Where behavior varies by machine, the variation belongs in data, not in branches.
Cloud and consumer execution are intended to share code; no cloud run exists.

*Enforced by:* run files carry a `hardware_id` and an environment block instead of
the code forking per machine; `quantum/backend.py` selects a target by preference
order rather than by hostname.

## 5. Education alongside engineering

Someone should be able to learn the mathematics and the method from this repo, not
just run it. Comments explain *why* a construction is the way it is, particularly
where it is subtle.

*Enforced by:* `classical/ramanujan_kernel.cu` explains why the term is built as an
interleaved running product rather than a factorial; `quantum/qae.py` explains the
global-phase correction and states plainly what the circuit does *not* prove.

## 6. AI explains results; it never invents them

The narrator receives numbers from a run file and writes prose about them. It must never
generate, estimate, or fill in a measurement, and no classical or quantum
computation is ever routed through a language model.

*Enforced by:* [ADR 003](../adr/003-hybrid-cloud-nim.md), restated as a
non-negotiable constraint in `AGENTS.md`, and by the narrator's shape — it takes a
run file as input and returns prose, with no path by which a model output can
re-enter the numerical pipeline. This does not validate the prose: the model
can produce unsupported statements, so reviewed findings must check each claim.

---

## Non-goals

The things q1729 deliberately refuses to do live in the
[Anti-Roadmap](../roadmap.md#anti-roadmap). Anything on that list requires an ADR
to overturn — it is a standing decision, not a default.

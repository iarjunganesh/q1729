# ADR 011 — Aborted runs are archived; the time budget is a declared control

Date: 2026-09-23
Status: Accepted
Supersedes: nothing. Extends [ADR 008](008-versioned-evidence-validation-and-exclusive-archives.md)
and [ADR 010](010-committed-measurement-protocol.md).

## Context

Protocol version 1 (ADR 010) already declared the right rule: a configuration
that exceeds its wall-clock budget aborts the run, and the completed
configurations are archived with the abort recorded. Nothing enforced it. The
2026-09-23 audit confirmed two consequences in the harness:

- It wrote only after both arms had finished, so any exception late in the
  quantum sweep — a driver fault, an out-of-memory, an operator's Ctrl-C —
  discarded every completed configuration, including hours of GPU time.
- No budget existed to exceed. The stopping rule could not be followed, and
  a run that stopped early could not be told apart from one never started.

A lost partial run is itself a selection effect: only runs that happened to
finish would ever be archived.

## Decision

1. **The budget is a declared control.** `--time-budget-s` is required, like
   `--power-profile`, and is recorded as `controls.time_budget_s`. It is one
   total wall-clock budget for both arms, checked before every warm-up and
   every timed call. A call already in flight is never interrupted, so elapsed
   time may exceed the budget by at most one call; the check sits at the finest
   boundary that keeps every recorded sample whole.
2. **Every stop after measurement begins writes an archive.** Budget
   exhaustion, an exception from either arm and `KeyboardInterrupt` all produce
   a record with `status.state = "aborted"`, the reason (`budget`, `error`,
   `interrupted`), the exception type and message, the planned sweep and the
   completed configurations. The unfinished configuration keeps its raw samples
   and outcomes (count distributions included) and is never summarized.
3. **Schema `q1729/run-file/5`.** It adds the `status` block to schema 4 and is
   the only schema written. Schemas 1–4 remain read-only; both measured
   archives are unchanged and still validate. The validator checks that the
   completed sweep is a prefix of the planned one, the classical arm finished
   before the quantum arm started, the stopped configuration is the next
   planned one, a budget abort happened after the budget elapsed, and a
   complete run covers its whole plan.
4. **An aborted record is an audit record, not a result.** `run_file.load`
   refuses it unless `allow_incomplete=True`. The CI archive check and the
   writer pass that flag; the plotter, NIM narrator and findings review do not.
5. **Ctrl-C is deferred to the next call boundary.** CUDA-Q installs its own
   C-level SIGINT handler when it is imported. On cudaq 0.16.0.post1 (RTX 5070,
   2026-09-23) that handler ended the process with no Python exception and no
   archive, and in the harness it left the process hung. Restoring Python's
   raising handler is not enough either: a Ctrl-C landing during CUDA-Q's JIT
   compilation aborted the compile ("compilation interrupted by Python
   signal") and hung the process. After target selection the harness therefore
   installs a handler that only records the request; the budget check raises
   `KeyboardInterrupt` at the next warm-up or timed call, and the previous
   handler is restored afterwards. A second Ctrl-C raises immediately, as an
   escape hatch for a call that never returns. A real SIGINT on the RTX 5070
   then archived 23 completed configurations plus the unfinished one's sample.
6. **Exit status stays honest.** A budget stop returns exit code 3 after
   archiving. An error or interrupt is re-raised after archiving so its
   traceback is not lost. If the abort archive itself cannot be written — a
   competing file, a source change, a validation failure — the write error is
   raised with the original stop as its cause; nothing is overwritten.
7. **Protocol version 2.** The stopping and exclusion rules now describe the
   enforced mechanism. Runs under protocol 1 and 2 have different digests and
   must not be pooled, as ADR 010 requires.

The classical arm's timed loop moved from `cuda_kernel.time_partial_sum` into
the harness so the budget is checked between repeats. The timing boundary is
unchanged: one discarded warm-up, then `time.perf_counter` around each
`partial_sum` call. `time_partial_sum` remains for diagnostics.

## Consequences

- A stop costs at most the configuration in progress, and even its samples
  are kept. The archive now records every run that started measuring.
- `make benchmark` requires `TIME_BUDGET_S` alongside `POWER_PROFILE`.
- A stop between the last measurement and the write (source changed, invalid
  payload) still writes nothing. That is deliberate: such a record could not be
  trusted.
- Abrupt process death (power loss, `SIGKILL`) still leaves no archive;
  incremental on-disk writing would need a journal format and is not adopted.

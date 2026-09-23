# ADR 010 — A committed measurement protocol and an analytic QAE reference

Date: 2026-09-06
Status: Accepted
Supersedes: nothing. Extends [ADR 008](008-versioned-evidence-validation-and-exclusive-archives.md)
and [ADR 009](009-traceable-outcomes-and-reviewed-releases.md).

## Context

ADR 008 made evidence structurally valid and archives exclusive. ADR 009 made
every recorded number traceable to a source revision, a device and a repeat.
Both establish that a number was recorded faithfully. Neither establishes
**what the number is a measurement of**.

The 2026-09-06 audit found the gap concretely. Published findings claimed
sub-millisecond classical execution against an archived two-term mean of
2.714 ms, and inferred a per-gate dispatch bottleneck from sampled GPU
utilization. The timings themselves were sound — all 27 rows recompute
correctly from their raw samples. What was missing was a committed statement
of the timing boundary, so prose could describe the number as whatever seemed
plausible later.

Two further gaps followed from the same root:

- The sweep, repeats, exclusions and stopping rule existed only as argparse
  defaults and habit. Nothing prevented extending a sweep or re-running a
  configuration after seeing its result.
- Summaries reported mean, min and standard deviation with no interval, so
  "the arms differ" had no stated uncertainty behind it.

Separately, the QAE arm's error floor was asserted in a docstring rather than
derived, and the earlier wording ("from m = 10 upward the estimate stops
improving") overstated a finite effect as an unbounded one.

## Decision

**Commit the protocol as code, and hash it into every run file.**
`benchmarks/protocol.py` declares the timing boundaries, warm-up policy,
exclusion rule, stopping rule and uncertainty method as module constants.
Changing any of them is a reviewable diff. Run files carry the full
declaration plus its SHA-256 as schema `q1729/run-file/4`.

Validation recomputes the digest from the declaration **the file itself
carries**, never from the current module. An archived run must stay valid
after the protocol changes; the check establishes only that a declaration and
its digest were not altered independently, so a run cannot claim a protocol it
did not follow. Runs whose digests differ must not be pooled.

**Report uncertainty, not just spread.** Every configuration gains standard
error and a two-sided 95% Student's *t* interval. The table of critical values
falls back to the nearest lower degrees of freedom, overstating the interval
rather than understating it. `harness.summarize` delegates to
`protocol.uncertainty` so the reported treatment is literally the declared one.

**Measure the phases; do not redefine the old number.**
`classical.cuda_kernel.time_phases` separates kernel-handle acquisition,
allocation, device execution (CUDA events), transfer and host reduction.
`partial_sum` is left byte-for-byte unchanged, because altering it would break
comparability with the existing archive — a phase-attributed sweep is a new
measurement alongside the old one, not a reinterpretation of it. The gap
between the phase sum and the enclosing end-to-end time is reported as
`unattributed_s` rather than absorbed.

**Derive the QAE floor instead of asserting it.**
`quantum/quantization.py` computes the ideal outcome, the error floor, the
plateau bounds and the exact two-peak outcome distribution in closed form,
with no cudaq import and nothing timed. `harness.quantization_report` attaches
that comparison to every measured QAE row.

## Consequences and limits

`classical` must not import `benchmarks` — the measured module cannot depend on
the harness that measures it — so `PHASE_NAMES` is duplicated as a plain tuple
and its agreement with `TIMING_BOUNDARIES` is asserted by a test rather than by
an import. That duplication is deliberate and must stay tested.

The analytic reference is strong evidence but not a simulator check: it
confirms that all 15 archived QAE outcomes match closed-form theory to 1e-12,
with 8 landing on the conjugate peak `2^m - y`, which carries equal weight and
recovers an identical estimate. Agreement is therefore checked on the
recovered estimate, never the raw integer. It says nothing about hardware
noise, and it cannot detect a simulator and a theory that are wrong in the
same way.

`total_variation` against `sampling_tolerance` is a diagnostic, not a
hypothesis test. Finite shots always leave a positive distance.

The confidence interval covers repeated timings on one host under one power
profile. Timing samples are not independent across thermal drift, so it is a
**lower bound** on real uncertainty.

**This ADR defines and validates a measurement; it does not perform one.**
`time_phases` requires a real GPU and has never run on one — the WSL2 distro
points at a deleted `ext4.vhdx`. No profiling was performed, so no
dispatch-bottleneck or arithmetic-bound claim is licensed by this change; the
`_load_kernel`-per-call observation is a hypothesis until measured. Collecting
the first phase-attributed run under this protocol is P1-R4.

## 2026-09-23 amendment — derived QAE fields are recomputed, conjugate rule corrected

The `quantization` block in each QAE row was written but never validated, so
a malformed or hand-edited diagnostic passed. It is now produced by one
function, `quantum.quantization.report`, shared by the writer and
`run_file.validate_quantization`. For schema 4 and later, the validator
recomputes every field from the row's own `counting_qubits`, `outcome`,
`counts` and `shots`. Integers and booleans must match exactly and floats to
1e-9 relative, the field set must match, and the outcome must be an integer.

`landed_on_conjugate` was `outcome != ideal`, which also labelled a wrong
outcome as a conjugate landing. It is now true only when the outcome is the
conjugate peak and that peak differs from the ideal one; a wrong outcome shows
up as `agrees_with_theory = false`. All 15 QAE rows of the only schema-4
archive (2026-09-06) recompute exactly, and all agree with the corrected rule,
so no archived record changes.

(The Status paragraph above predates the 2026-09-06 runtime restoration;
`time_phases` has since run on the RTX 5070, see `docs/measurement-protocol.md`.)

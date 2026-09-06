# Measurement protocol

The committed answer to *what will be measured, and how the numbers will be
treated* — fixed before data is collected, so it cannot be chosen afterwards
once the results are visible. Roadmap gate
[P1-R3](roadmap.md#p1-r3--define-and-verify-the-measurement).

The declaration lives in [`benchmarks/protocol.py`](../benchmarks/protocol.py)
as module constants, not in this file. Prose goes stale; a constant that every
run file hashes does not. This page explains the reasoning.

## Why it exists

The [2026-09-06 audit](markdown-audit-2026-09-06.md) found published findings
that disagreed with the data they described — a "sub-millisecond" classical
claim against an archived two-term mean of **2.714 ms**, and a causal claim
about dispatch overhead that sampled GPU utilization cannot support.

Neither was a measurement error. The timings were internally consistent; all
27 rows recompute correctly from their raw samples. The problem was that
nothing recorded *what the number was a measurement of*, so prose was free to
describe it as whatever seemed reasonable later.

## Timing boundaries

The archived stage-1 run timed one thing: host wall time around the whole
Python call. That is a real and useful quantity — it is what a caller actually
waits for — but it is not device execution time, and it cannot support a claim
about arithmetic throughput or launch overhead.

`partial_sum` does all of this inside that one timer:

| Phase | What it is |
| --- | --- |
| `kernel_handle` | NVRTC source load and module construction |
| `allocate` | device buffer for the block partial sums |
| `execute` | kernel launch to completion — **the only device time** |
| `transfer` | device-to-host copy of the partials |
| `host_reduce` | `math.fsum` over the partials on the host |

[`classical.cuda_kernel.time_phases`](../classical/cuda_kernel.py) measures
these separately: `execute` with CUDA events on the device, everything else
with `time.perf_counter` on the host. Their sum is slightly below the
enclosing end-to-end figure, and the difference is reported as
`unattributed_s` rather than absorbed by scaling the parts up to the whole.

`partial_sum` itself is deliberately unchanged. Altering it would break
comparability with the existing archive, so `time_phases` measures the same
sequence of operations rather than replacing it. A phase-attributed sweep is
therefore a **separate** measurement, not a reinterpretation of the old one.

One consequence is already visible in the source and should be measured before
it is asserted: `_load_kernel()` constructs a `RawModule` on every call, inside
the timed region. cupy caches compiled modules by source, so this is wrapper
cost rather than recompilation — but "wrapper cost" is a hypothesis about the
2.714 ms until `time_phases` runs on real hardware. **It has not run.**

## Warm-up, exclusions, stopping

- **Warm-up** — exactly one untimed call per configuration, discarded, to
  absorb NVRTC/JIT compilation and context creation. Warm-up does *not* remove
  per-call wrapper work, which is why that work is now measured rather than
  assumed negligible.
- **Exclusions** — none. No outlier rejection, trimming or winsorizing. Every
  timed repeat enters the summary and is retained raw. A configuration that
  raised is recorded as failed, never partially summarized.
- **Stopping rule** — the sweep and repeat count are fixed before the run and
  are not extended, truncated or re-run based on the values observed. A
  configuration exceeding its wall-clock budget aborts the run with the abort
  recorded. Re-running after a change writes a **new** archive alongside the
  old one; results are never selected across runs.

The stopping rule is the anti-p-hacking clause. It is the one most easily
violated by accident — "that run looked odd, let me try again" is exactly the
behaviour it forbids without a recorded reason.

## Uncertainty

Per configuration: mean, minimum, sample standard deviation, standard error of
the mean, and a two-sided 95% confidence interval from Student's *t* with
*n*−1 degrees of freedom. Critical values come from a short table in
`protocol.py`; between tabulated points it falls back to the nearest lower
`df`, which **overstates** the interval rather than understating it.

The interval describes the mean of repeated timings on this host under this
power profile. It is not a claim about other hardware, and timing samples are
not independent across thermal drift — so it is a **lower bound** on real
uncertainty, not a complete account of it.

## The protocol digest

Every run file carries the full declaration and its SHA-256:

```json
"protocol": { "declaration": { ... }, "digest": "<64 hex>" }
```

Validation recomputes the digest from the declaration **the file itself
carries**, never from the current `protocol.py`. An archived run must stay
valid after the protocol changes; what the check establishes is that the
declaration and its digest were not altered independently of one another, so a
run cannot claim a protocol it did not follow.

**Two runs whose protocol digests differ were not measured the same way and
must not be pooled.**

## What this does not do

It fixes *what* will be measured and how the numbers will be treated. It
cannot make a timing boundary meaningful, and it does not establish that the
declared sweep is wide enough to answer the question. Those judgements belong
in the run file's `limitations`.

It also is not profiling. Attributing cost to a named phase is not the same as
establishing *why* that phase is expensive — that needs a profiler, and until
one runs, dispatch-bottleneck language stays out of the findings.

## Status

Committed and unit-tested on CPU. **No phase-attributed measurement has been
collected**: `time_phases` needs a real GPU, and the WSL2 runtime is
unavailable (its registered distro points at a deleted `ext4.vhdx`). The
protocol is the gate; the run behind it is [P1-R4](roadmap.md#p1-r4--repeat-and-review).

See also [run-file.md](run-file.md) for the schema and
[research-standards.md](handbook/research-standards.md) for the nine-field
contract this sits inside.

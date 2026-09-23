# ADR 009 — Traceable outcomes and reviewed releases

Date: 2026-09-06

Status: Accepted

## Context

P1-R2 requires every point to be traceable to its source, selected execution
device, runtime and individual outcomes. Schema 2 only preserves final outcomes
beside timing arrays. Backend labels assume precision, narration is unchecked,
and release publication previously had no dependency on the quality suite.

## Decision

Write schema 3 with source revision/dirty state and execution-source SHA-256
manifest, resolved installed distributions, actual CuPy device PCI identity,
GPU UUID, CUDA driver/runtime, and queried CUDA-Q target/precision. Query GPU
monitoring by that selected device. Reject changed source during measurement.
Record explicit configuration, relevant runtime controls and seed policy.

Preserve every timed classical partial sum and derived estimate, and every QAE
outcome/count distribution. Row summaries describe the last timed outcome;
timing statistics still summarize all repeats. Resolve equal QAE count peaks by
lexicographic bitstring order. Optional positive 32-bit seeds follow a recorded
per-repeat schedule. The current protocol rejects seeded tensornet runs until
its additional determinism controls are validated; this is a protocol restriction,
not a claim that CUDA-Q lacks all tensor-network seed functionality.

Require one visible CUDA device for this comparison's unambiguous device mapping.
The general backend diagnostic keeps its existing target order; multi-GPU
experiments require a separate mapping/protocol before the harness accepts them.
CPU quantum fallback stays explicitly labeled. Read schemas 1 and 2 unchanged.

New findings require a named human's paragraph-by-paragraph review sidecar,
bound to source/draft hashes. CI checks these records. The two pre-sidecar
historical findings documents are accepted only at their existing text hashes.
Mechanical validation does not certify the reviewer's identity or scientific judgment.

Release tags must match project version, have unique nonempty changelog notes,
refer to the checked-out commit and be reachable from fetched main. The release
workflow depends on a fresh run of the reusable CI suite for that tag. Add
`scripts` to coverage/type checks rather than leaving release logic untested.
Remove the non-kernel TYPE_CHECKING coverage exclusion; gate-name annotations
are scoped to actual JIT gate references, with real circuit integration retained.

## Consequences and limits

Dirty-source hashes identify files but do not embed or reconstruct them; preserve
matching source separately or run from a clean committed checkout. Package lists
identify versions but are not a portable environment lock. Seeds do not guarantee
cross-platform bit identity. Equivalent statevector bytes are analytical storage,
not measured allocation, especially on tensor-network backends.

CPU boundary tests can verify structure, preservation and failure paths without
establishing GPU numerical behavior. WSL2's missing disk still blocks fresh
device verification. No new measurement, reviewer approval, release or cloud
execution is created by implementing these gates.

References: [CUDA-Q target/precision/seed API](https://nvidia.github.io/cuda-quantum/latest/api/languages/python_api.html),
[tensor-network controls](https://nvidia.github.io/cuda-quantum/latest/using/backends/sims/tnsims.html),
[CuPy device identity](https://docs.cupy.dev/en/stable/reference/generated/cupy.cuda.Device.html).

## 2026-09-23 amendment — a review binds every archive its draft cites

Schema `q1729/findings-review/1` hashed only one run file, but the approved
2026-09-06 findings compare against the 2026-08-05 archive as well; altering
that second archive left the approval standing. `analysis/review.py` now
writes `q1729/findings-review/2`, whose `sources` array holds the name and
normalized SHA-256 of every source. A template is refused unless every
adjacent run JSON named in the draft is bound (`--run` repeats per citation).
Changing any bound source, or citing a new archive, makes the review stale.

Schema 1 stays readable. Its one multi-source case is handled without a new
approval: `LEGACY_CITED_SOURCES` pins the 2026-08-05 archive's hash as it was
when the 2026-09-06 review was approved. That file is unchanged since its only
commit (`f88a926`, 2026-08-05). The pin adds a way to invalidate the
approval; it approves nothing. Any other schema-1 review whose draft cites an
unbound archive fails. The findings were not revised, so no new human review
was required.

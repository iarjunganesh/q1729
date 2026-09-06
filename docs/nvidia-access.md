# NVIDIA runtime and access

Status reviewed 2026-09-06. Local Windows reports an RTX 5070 Laptop GPU,
8151 MiB and driver 616.56. The archived 2026-08-05 run records driver 610.88.
The driver-supported CUDA version is not proof of an installed toolkit version.
WSL2 currently cannot attach its configured virtual disk; no fresh CUDA/QAE
runtime verification or NIM API request was completed in this audit.

## Local GPU first

Use the separate environment in [setup](setup.md). A working Linux/WSL2
runtime, real-backend tests, evidence repairs and profiling precede new
performance claims. A newer Windows CuPy wheel does not establish that this
repository's complete native-Windows GPU path has been tested.

## NIM

The narrator uses `NVIDIA_API_KEY` from the process environment. `.env` is
ignored by Git but is not loaded automatically. Set the key privately and do
not print it. WSL2 may need separate configuration; if sharing via `WSLENV`,
preserve its existing entries. Key presence only confirms configuration,
not authentication, quota, service availability or successful inference.

The whole supplied run object is sent to the service, including environment
metadata. Generated prose needs review. Current pricing, credits, availability
and limits must be checked with the provider when access is actually needed;
this guide makes no continuing free-credit or price guarantee.

## Optional H100 axis

No H100 or multi-GPU run exists. Before renting anything, specify the research
question, profiling evidence, controls, expected memory/runtime, maximum cost
and stop condition. Cost is not the only blocker: the archive and runtime
repair gates in [Phase 1](roadmap.md#phase-1--the-first-real-result) are still open.
Cloud access is not required for CPU Phase 2 design or a local decoding study.

A single H100 follows the single-GPU path. Multi-GPU success has not been
verified; selection depends on visible devices and a working MPI/plugin setup.
Record the actual selected target, precision and device identity before using
timings. Do not infer working multi-GPU execution from a fallback test.

## Statevector budget

Bare fp32 complex state storage is `8 * 2**qubits` bytes: 4 GiB at 29 qubits,
8 GiB at 30 and 64 GiB at 33. Simulator workspace and other allocations reduce
usable capacity. These are estimates, not tested qubit ceilings. The archived
largest circuit has 19 total qubits and a 4 MiB bare state. Utilization readings
alone do not predict whether H100 improves its timing.

ROCm stays a conditional Phase 4 portability study under
[ADR 006](adr/006-rocm-as-phase-4-second-backend.md). No AMD runtime was tested.

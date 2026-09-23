# NVIDIA runtime and access

Status reviewed 2026-09-23. `nvidia-smi` reports an RTX 5070 Laptop GPU,
8151 MiB and driver 616.92. The archived 2026-08-05 run records driver 610.88.
The driver-supported CUDA version is not proof of an installed toolkit version.
WSL2 GPU verification passed on 2026-09-23 (distro `Ubuntu`, Python 3.14.7,
CUDA-Q 0.16.0.post1 on `nvidia`, CuPy 14.2.0, CUDA runtime 13020): 386 passed,
1 skipped, 100.00% coverage. No NIM API request was made.

## Local GPU first

Use the separate environment in [setup](setup.md). A working Linux/WSL2
runtime, real-backend tests, evidence repairs and declared-profile profiling
precede new performance claims. A newer Windows CuPy wheel does not establish
that this repository's complete native-Windows GPU path has been tested.

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

No H100 or multi-GPU run exists. The current π sweep reaches 19 circuit qubits:
its bare fp32 state is only 4 MiB. An 80 GB H100's capacity does not answer a
memory question at that size, and sampled utilization cannot predict a speedup.
Cloud access is unnecessary for P2-A protocol design, a CPU reference decoder
or the first local GPU decoding controls.

Use these gates before any rental:

1. Keep the local GPU runtime passing real CUDA and CUDA-Q tests with the
   intended dependency set (done 2026-09-23); late-failure preservation and a
   declared time budget exist (ADR 011). Archive a declared-profile phase study
   before an expensive run.
2. Write one falsifiable H100 question and controls. Examples: a circuit size
   that exceeds the local GPU's measured safe memory ceiling, or a matched
   decoder workload whose local profile identifies device compute or memory
   as the limiter. Keep precision, code revision, instances, shot/repeat counts
   and timing boundaries fixed or record their differences explicitly.
3. Estimate bare state size (`8 * 2**qubits` bytes for fp32 complex), simulator
   workspace, host RAM, runtime and storage. Set a maximum spend and a short
   smoke-test stop condition. Check the provider's current GPU type, pricing,
   billing, disk and network charges immediately before provisioning.
4. Begin with one H100. Verify the actual device/target/precision and run the
   small correctness control before the full sweep. Archive every outcome,
   including failures. Stop at the preset budget or failed control. Compare
   matched accuracy and end-to-end time; keep device-only time separate.

For a preliminary ceiling, multiply the provider's current hourly rate by
planned provisioned hours, then add storage and transfers. A multi-GPU rental
requires a separate scaling question and MPI/plugin validation; it is not the
default next step.

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

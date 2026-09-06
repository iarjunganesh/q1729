# Start here

q1729 is a research repository growing toward a reusable platform. Read the
[README](../README.md) for the research thread, [PATHWAYS](PATHWAYS.md) for
orientation and [roadmap](roadmap.md) for phase gates. The next code milestone
is P1-R3 protocol/profiling work; P1-R1 and P1-R2 are implemented and locally tested.

## What you can run today

| Component | Implemented | Verification boundary |
| --- | --- | --- |
| Exact Ramanujan series | Yes, SymPy CPU reference | CPU tests |
| LPS graph construction | Yes, graph module and tests committed in e8b2060 | Exact modular construction; numerical spectrum |
| CUDA series kernel | Yes | Real GPU tests require available Linux/WSL2 runtime |
| Canonical QAE | Yes, known amplitude π/4 | CPU simulator CI and historical GPU evidence |
| Harness and plots | Yes; one measured archive | Schema-3 provenance/outcomes and archive protection implemented; real GPU verification pending |
| NIM narrator | Yes, optional external service | Generated prose needs human review |
| Classical decoder / qLDPC study | No | Phase 2 work |
| Shared research engine / ROCm | No | Later phases, conditional on evidence |

Follow [setup](setup.md) for separate Windows and Linux environments. Run
`python main.py` for status and `pytest tests/unit` for CPU development checks.
The WSL2 disk was unavailable in the 2026-09-06 audit; old successful GPU
transcripts are historical, not a present setup guarantee.

Read the [reviewed result](../benchmarks/runs/2026-08-05-rtx5070-turbo-reviewed.md)
before repeating the experiment. QAE encodes a known amplitude; the run does
not demonstrate quantum advantage. Use the [benchmark guide](../benchmarks/README.md)
to avoid reusing output paths. A NIM response to synthetic sample data is never
evidence of a measured run.

Before changing code, read [AGENTS.md](../AGENTS.md), the
[research standards](handbook/research-standards.md) and relevant
[ADRs](adr/README.md). Record new evidence in a dated session entry and keep
current-facing status separate from historical results.

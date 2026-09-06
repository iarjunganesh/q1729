# Contributing

Issues, reproduction feedback and benchmark ideas are welcome. q1729 is a
maintainer-led research project; review capacity is limited. The
[README](README.md) defines its research thread and [roadmap](docs/roadmap.md)
orders work. Read relevant [ADRs](docs/adr/README.md) before proposing a change.

## Development

Follow [setup](docs/setup.md) for separate Windows CPU and Linux/WSL2 GPU
environments. Install core requirements first and GPU requirements only in the
appropriate environment. Run `python main.py`, unit tests, Ruff and mypy.
New code must satisfy the unchanged 100% CI coverage gate; do not add exclusions
outside JIT kernel bodies. Real integration evidence is distinct from line coverage.

## Measured Windows coverage

2026-09-06, Python 3.14.6, NIM key removed: 157 passed, 29 skipped.
Generated from `pytest tests --cov --cov-report=json --cov-fail-under=100`:

| Module | Statements | Missed | Windows coverage |
| --- | --- | --- | --- |
| `analysis/narrator.py` | 35 | 0 | 100.00% |
| `benchmarks/environment.py` | 77 | 0 | 100.00% |
| `benchmarks/harness.py` | 75 | 0 | 100.00% |
| `benchmarks/plot.py` | 60 | 0 | 100.00% |
| `classical/cuda_kernel.py` | 74 | 0 | 100.00% |
| `classical/ramanujan_graph.py` | 110 | 0 | 100.00% |
| `classical/ramanujan_series.py` | 21 | 0 | 100.00% |
| `quantum/backend.py` | 38 | 3 | 92.11% |
| `quantum/qae.py` | 43 | 12 | 72.09% |

Total: **97.19%**, 533 statements, 15 missed. The command exits nonzero because
it does not meet 100%. Missing CUDA-Q runtime paths are expected on this Windows
environment; the CI threshold is not lowered. CUDA wrapper line coverage comes
from mocks and does not substitute for GPU numerical integration tests.

Historical WSL2 evidence recorded 186 passed / 100% on 2026-08-05; this audit
could not reproduce it because the configured virtual disk could not attach.
CI runs real CUDA-Q integration on `qpp-cpu`; CUDA-kernel GPU tests skip there.
Released-commit CI does not validate the staged graph work automatically.

Preserve measured files and use the [research contract](docs/handbook/research-standards.md).
Submit source/configuration and raw outcomes alongside claims. Never use
synthetic examples or unchecked narration as performance evidence.

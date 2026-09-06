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

2026-09-06, Python 3.14.6, NIM key removed: 219 passed, 29 skipped.
Generated from `pytest tests --cov --cov-report=json --cov-fail-under=100`:

| Module | Statements | Missed | Windows coverage |
| --- | --- | --- | --- |
| `analysis/narrator.py` | 31 | 0 | 100.00% |
| `benchmarks/archive.py` | 20 | 0 | 100.00% |
| `benchmarks/environment.py` | 77 | 0 | 100.00% |
| `benchmarks/harness.py` | 84 | 0 | 100.00% |
| `benchmarks/plot.py` | 61 | 0 | 100.00% |
| `benchmarks/run_file.py` | 144 | 0 | 100.00% |
| `classical/cuda_kernel.py` | 74 | 0 | 100.00% |
| `classical/ramanujan_graph.py` | 110 | 0 | 100.00% |
| `classical/ramanujan_series.py` | 21 | 0 | 100.00% |
| `quantum/backend.py` | 38 | 3 | 92.11% |
| `quantum/qae.py` | 43 | 12 | 72.09% |

Total: **97.87%**, 703 statements, 15 missed. All new/changed evidence modules
have 100% statement coverage. The full command exits nonzero because missing
CUDA-Q runtime paths prevent this Windows host from meeting 100%; the gate
is unchanged. Mocked CUDA wrapper coverage is not GPU numerical verification.

Historical WSL2 evidence recorded 186 passed / 100% on 2026-08-05; this audit
could not reproduce it because the configured virtual disk could not attach.
CI runs real CUDA-Q integration on `qpp-cpu`; CUDA-kernel GPU tests skip there.
Released-commit CI does not validate the unreleased graph/evidence changes automatically.

Preserve measured files and use the [research contract](docs/handbook/research-standards.md).
Submit source/configuration and raw outcomes alongside claims. Never use
synthetic examples or unchecked narration as performance evidence.

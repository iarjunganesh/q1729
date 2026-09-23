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

2026-09-23, Python 3.14.6, NIM key removed: 382 passed, 29 skipped.
Recorded with `pytest tests -q --cov --cov-report=term-missing`:

| Module | Statements | Missed | Windows coverage |
| --- | --- | --- | --- |
| `analysis/narrator.py` | 31 | 0 | 100.00% |
| `analysis/review.py` | 85 | 0 | 100.00% |
| `benchmarks/archive.py` | 20 | 0 | 100.00% |
| `benchmarks/environment.py` | 78 | 0 | 100.00% |
| `benchmarks/harness.py` | 202 | 0 | 100.00% |
| `benchmarks/plot.py` | 65 | 0 | 100.00% |
| `benchmarks/protocol.py` | 37 | 0 | 100.00% |
| `benchmarks/provenance.py` | 30 | 0 | 100.00% |
| `benchmarks/run_file.py` | 333 | 0 | 100.00% |
| `classical/cuda_kernel.py` | 114 | 0 | 100.00% |
| `classical/ramanujan_graph.py` | 110 | 0 | 100.00% |
| `classical/ramanujan_series.py` | 21 | 0 | 100.00% |
| `quantum/backend.py` | 38 | 3 | 92.11% |
| `quantum/qae.py` | 53 | 0 | 100.00% |
| `quantum/quantization.py` | 82 | 0 | 100.00% |
| `scripts/release_check.py` | 34 | 0 | 100.00% |

Total: **99.77%**, 1333 statements, 3 missed. New/changed modules reach 100%
statement coverage, including CUDA-Q wrapper paths tested with a fake backend.
Real JIT circuit integration remains separate and was skipped on Windows.
The full 100% command exits nonzero because CUDA-Q's backend diagnostic cannot
run here; the threshold is unchanged. Coverage now includes release scripts.

WSL2 (distro `Ubuntu`, Python 3.14.7, CUDA-Q 0.16.0.post1, CuPy 14.2.0)
recorded **410 passed, 1 skipped, 100.00% coverage** on the RTX 5070 on
2026-09-23. CI's 100% gate and the Windows table are separate.
CI runs real CUDA-Q integration on `qpp-cpu`; CUDA-kernel GPU tests skip there.
Released-commit CI does not validate newer unreleased changes automatically.

Preserve measured files and use the [research contract](docs/handbook/research-standards.md).
Submit source/configuration and raw outcomes alongside claims. Never use
synthetic examples or unchecked narration as performance evidence.

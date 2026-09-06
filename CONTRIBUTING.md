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

2026-09-06, Python 3.14.6, NIM key removed: 316 passed, 29 skipped.
Generated from `pytest tests --cov --cov-report=json --cov-fail-under=100`:

| Module | Statements | Missed | Windows coverage |
| --- | --- | --- | --- |
| `analysis/narrator.py` | 31 | 0 | 100.00% |
| `analysis/review.py` | 57 | 0 | 100.00% |
| `benchmarks/archive.py` | 20 | 0 | 100.00% |
| `benchmarks/environment.py` | 78 | 0 | 100.00% |
| `benchmarks/harness.py` | 115 | 0 | 100.00% |
| `benchmarks/plot.py` | 65 | 0 | 100.00% |
| `benchmarks/protocol.py` | 37 | 0 | 100.00% |
| `benchmarks/provenance.py` | 30 | 0 | 100.00% |
| `benchmarks/run_file.py` | 251 | 0 | 100.00% |
| `classical/cuda_kernel.py` | 114 | 0 | 100.00% |
| `classical/ramanujan_graph.py` | 110 | 0 | 100.00% |
| `classical/ramanujan_series.py` | 21 | 0 | 100.00% |
| `quantum/backend.py` | 38 | 3 | 92.11% |
| `quantum/qae.py` | 53 | 0 | 100.00% |
| `quantum/quantization.py` | 76 | 0 | 100.00% |
| `scripts/release_check.py` | 34 | 0 | 100.00% |

Total: **99.73%**, 1130 statements, 3 missed. New/changed modules reach 100%
statement coverage, including CUDA-Q wrapper paths tested with a fake backend.
Real JIT circuit integration remains separate and was skipped on Windows.
The full 100% command exits nonzero because CUDA-Q's backend diagnostic cannot
run here; the threshold is unchanged. Coverage now includes release scripts.

WSL2 was rebuilt on 2026-09-06 after its virtual disk was found deleted, and
now records **344 passed, 1 skipped, 100.00% coverage** on the RTX 5070 — every
module at 100%, the gate met for the first time. That, not the Windows table
above, is the authoritative coverage measurement.
CI runs real CUDA-Q integration on `qpp-cpu`; CUDA-kernel GPU tests skip there.
Released-commit CI does not validate the unreleased graph/evidence changes automatically.

Preserve measured files and use the [research contract](docs/handbook/research-standards.md).
Submit source/configuration and raw outcomes alongside claims. Never use
synthetic examples or unchecked narration as performance evidence.

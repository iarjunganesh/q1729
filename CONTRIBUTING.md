# Contributing

q1729 is a solo research project until stage 2 of the README roadmap, which opens it up properly (published results, benchmark submissions from other GPUs). Until then: issues and benchmark-idea discussions are welcome; PRs may sit.

## Local development

```bash
git clone https://github.com/iarjunganesh/q1729.git
cd q1729
pip install -r requirements.txt   # CPU-safe on any host
make test                         # integration tests skip without cudaq
```

CUDA-Q work needs Linux — on Windows, WSL2:

```bash
pip install -r requirements-gpu.txt
python -m quantum.backend         # diagnostic: which target initialized
```

## Ground rules

- The README roadmap is authoritative; check `docs/adr/` before proposing a direction change — several "why not X" questions are answered there as deliberate decisions
- 100% test coverage, no buffer: new code ships with its tests (CI gate is a literal `--cov-fail-under=100`, see [ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md))
- `requirements.txt` must stay installable on a CPU-only host

## Test coverage

Measured directly with `pytest tests --cov --cov-report=term-missing` (verified 2026-07-22):

| Host                        | analysis/narrator.py | classical/ramanujan_series.py | quantum/backend.py                                 | Total |
|-----------------------------|----------------------|-------------------------------|----------------------------------------------------|-------|
| Windows (no cudaq)          | 100%                 | 100%                          | 92% (missing 80–92: bell_counts, needs real cudaq) | 97%   |
| WSL2 (cudaq 0.15, RTX 5070) | 100%                 | 100%                          | 100%                                               | 100%  |

The Windows shortfall is expected and documented, not a gap to fix: `bell_counts()`
imports `cudaq` and runs a JIT-compiled kernel, so it can only execute where
cudaq is actually installed. `tests/integration/test_cudaq_smoke.py` exercises
it for real in WSL2/CI. CI (`.github/workflows/ci.yml`) installs the CPU
`cudaq` wheel and gates on a literal `--cov-fail-under=100` — no buffer, since
WSL2/CI measure the real 100% ([ADR 004](docs/adr/004-repo-hygiene-and-agent-sync.md)).

```bash
# Unit tests only (any host, no GPU, no key needed)
pytest tests/unit -v

# Full suite with coverage (run in WSL2 for the true number)
make coverage
```

Coverage report is a terminal `term-missing` table (`Makefile`'s `coverage`
target) — no HTML report is generated locally.

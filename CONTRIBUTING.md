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
- Near-100% test coverage: new code ships with its tests (CI gate is 95%)
- `requirements.txt` must stay installable on a CPU-only host

# Security Policy

## Scope

q1729 is an open benchmarking/research project. It ships no network services and processes no user data — the code computes mathematical series, runs local quantum-circuit simulations, and (optionally) calls the NVIDIA NIM API to draft findings from benchmark data.

## Secrets handling

- The only secret is `NVIDIA_API_KEY` (the NIM findings narrator, ADR 003). `.env` is gitignored; only `.env.example` (placeholder values) is committed
- The key is read from the environment at call time (`analysis/narrator.py`) and never hardcoded or logged
- Benchmark run files sent to NIM contain only synthetic or measured performance numbers — no personal or system-identifying data beyond GPU model names

## Reporting a vulnerability

If you find a security issue (e.g., a credential accidentally committed, or a malicious-input vector in a benchmark harness), please open a private security advisory on GitHub rather than a public issue. This is a solo research project, so response times are best-effort.

# Security Policy

## Scope

q1729 is an open benchmarking/research project. It ships no network services and processes no user data — the code computes mathematical series, runs local quantum-circuit simulations, and (optionally) calls the NVIDIA NIM API to draft findings from benchmark data.

## Secrets handling

- The only secret is `NVIDIA_API_KEY` (the NIM findings narrator, ADR 003). `.env` is gitignored; only `.env.example` (placeholder values) is committed
- The key is read from the environment at call time (`analysis/narrator.py`) and never hardcoded or logged
- Benchmark run files sent to NIM contain only synthetic or measured performance numbers — no personal or system-identifying data beyond GPU model names

## CI and build-time dependencies

- `.github/workflows/ci.yml` runs with `permissions: contents: read` at the workflow level — no job can write to the repo or push tags. `.github/workflows/release.yml` scopes `contents: write` only to the job that creates a GitHub Release, run only on a pushed `v*` tag; its quality-gate job stays read-only.
- GitHub Actions and dependency floors (`requirements.txt`, `requirements-gpu.txt`) are kept at their current latest verified release per `AGENTS.md`'s tech-stack-currency policy — deliberately, since stale pins are a common supply-chain exposure, not just a freshness nit.
- Regenerating `assets/architecture/` and `assets/brand/` locally pulls in Node.js + `@mermaid-js/mermaid-cli` (which bundles Puppeteer/Chromium) via `npx`. This is a **local developer tool only** — it never runs in CI and never touches a secret; the checked-in SVG outputs are what CI and the README actually use.

## Reporting a vulnerability

If you find a security issue (e.g., a credential accidentally committed, or a malicious-input vector in a benchmark harness), please open a private security advisory on GitHub rather than a public issue. This is a solo research project, so response times are best-effort.

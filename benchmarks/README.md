# benchmarks/

This directory is a placeholder. It holds the **real, measured** run files
and crossover plots that roadmap [Phase 1](../docs/roadmap.md#phase-1--the-first-real-result)
produces — not synthetic data.

Nothing has been placed here yet: no `.cu` kernel exists, the QAE circuit
hasn't been run on real silicon, and no crossover has been measured. See
`docs/roadmap.md`'s "Where the repo actually is" section for the current,
honest state of the repo, and `AGENTS.md` for the discipline that keeps that
section accurate.

Until then, `data/sample_run.json` — explicitly labeled synthetic in the file
itself — is the only run file in the repo, and it demonstrates the run-file
schema, not a result.

## What lands here (Phase 1 exit criteria)

- A real run file per hardware target (`hardware` field: `rtx-5070-8gb`,
  optionally `h100-80gb`), satisfying the research-standards contract in
  `docs/roadmap.md` (question, hypothesis, variables, controls, hardware,
  software versions, statistical treatment, raw data, limitations).
- One crossover plot: time (and VRAM) vs. digit count / qubit count,
  classical vs. quantum.

Once real files exist here, update this README to describe them instead of
their absence — see `AGENTS.md`'s status-bearing-document sweep.

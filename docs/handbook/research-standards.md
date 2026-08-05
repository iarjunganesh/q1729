# Research Standards

The contract every q1729 experiment must satisfy **before it runs**. Adopted in
[roadmap Phase 0](../roadmap.md#phase-0--constitution-lightweight) and enforced
from the first real run in Phase 1.

This exists because the failure mode of benchmark projects is not fabricated
data — it is data that was real, and became meaningless because nobody wrote
down what was varied, what was held fixed, or what machine it came from.

---

## The nine required fields

Every experiment declares all nine. A run file that omits one is not a result
yet.

| Field | What it means | Where it lives in a run file |
| --- | --- | --- |
| **Question** | The specific question this run answers — narrow enough that the data can actually settle it. | `question` |
| **Hypothesis** | The expected outcome *and the reasoning*, written before the run. | `hypothesis` |
| **Variables** | What is deliberately varied, per arm of the experiment. | `variables` |
| **Controls** | What is held fixed. Includes environment factors that silently change results — on a laptop, the vendor power/thermal profile. | `controls` |
| **Hardware** | The exact silicon, captured automatically. | `environment.gpu`, `hardware_id` |
| **Software versions** | Driver, CUDA runtime, CUDA-Q, cupy, numpy, sympy, Python. | `environment.packages`, `environment.gpu.driver_version` |
| **Statistical treatment** | Repeats, warm-up handling, what is summarized and how, and how outliers are treated. | `statistical_treatment` |
| **Raw data** | Every individual timing sample, not just summaries. | `runs[].samples_s` |
| **Limitations** | What the run does *not* establish. Written by the person who knows best, at the time they know it. | `limitations` |

## Why hypothesis-before-run

Writing the hypothesis after seeing the data turns any outcome into a
confirmation. In this repo the hypothesis text lives in `benchmarks/harness.py`
as a module constant, so it is committed to version control before the run that
tests it — and changing it is a visible diff, not a silent edit to a JSON file.

## Warm-up and timing

Both benchmark arms discard one warm-up call per configuration before timing.
This is not massaging the numbers: the first call pays NVRTC compilation, CUDA
context creation, and CUDA-Q JIT costs, which are one-time setup, not the
per-run cost the experiment is asking about. The warm-up is declared in
`statistical_treatment` so a reader can disagree with the choice.

Every timed repeat is recorded individually. Summaries (mean, min, sample
standard deviation) are derived; the samples are never replaced by them.

## Controls that are easy to forget

- **Power / thermal profile.** A GPU at 1710 MHz under a "silent" vendor profile
  and the same GPU at 3090 MHz are, for benchmarking purposes, two machines. The
  harness requires `--power-profile` explicitly and records current and max clock
  plus temperature so a reader can see throttling rather than take it on trust.
- **Precision.** The classical arm is fp64 in-kernel; the CUDA-Q `nvidia` target
  defaults to fp32. These are not comparable per-amplitude and the run file says
  so.
- **Other GPU tenants.** VRAM is sampled from `nvidia-smi`, which reports the
  whole device. The recorded figure is an upper bound and is labeled as one.

## Synthetic data

`data/sample_run.json` is synthetic demonstration data for the narrator. It is
labeled synthetic in the file itself, carries `"synthetic": true`, and
`benchmarks/plot.py` raises rather than plotting it. Synthetic data must stay
labeled even once real run files exist alongside it.

## Reproducing a run

A run file should be enough to re-run the experiment. In practice:

```bash
# read the contract and the environment the original run declared
python -c "import json;d=json.load(open('benchmarks/runs/<file>.json'));print(d['question']);print(d['controls']);print(d['environment'])"

# re-run under the same declared controls
python -m benchmarks.harness --power-profile <same profile> --out benchmarks/runs/<new>.json
```

If the numbers disagree beyond the recorded standard deviation, that disagreement
is itself a result — record it rather than re-running until it agrees.

---

*See also: [Principles](principles.md) · [Roadmap](../roadmap.md) ·
[Anti-Roadmap](../roadmap.md#anti-roadmap)*

# benchmarks/

The π case-study harness, environment capture and plotter exist, with one
[measured RTX 5070 Laptop GPU archive](runs/2026-08-05-rtx5070-turbo.json).
Read the [reviewed interpretation](runs/2026-08-05-rtx5070-turbo-reviewed.md)
instead of relying on the preserved narrator draft. No H100 or decoding run exists.

| Path | Role |
| --- | --- |
| `harness.py` | Times CUDA and known-amplitude QAE; writes JSON |
| `environment.py` | Captures selected package versions and sampled GPU metadata |
| `plot.py` | Produces light/dark figures; rejects labeled synthetic input |
| `runs/` | Measured archives and reviewed/historical findings |
| `plots/` | Generated figures; change source code, not SVGs |

The archive has five repeats per configuration, 4000 QAE shots and turbo power
profile. No crossing was observed within its sweep. QAE estimates a known
amplitude; sampled utilization cannot establish a causal bottleneck.

## Reproducing

Install both requirements files in a separate Linux/WSL2 environment per
[setup](../docs/setup.md). Read the source archive's configuration first.
The commands below specify the archived shot count but do not repair missing
provenance or guarantee identical stochastic outcomes.

```bash
# Unique output avoids the current Makefile's same-day filename collision.
run_id=$(python -c 'import uuid; print(uuid.uuid4().hex)')
run_path="benchmarks/runs/${run_id}.json"
test ! -e "$run_path" && python -m benchmarks.harness --power-profile turbo --shots 4000 --out "$run_path"
python -m benchmarks.plot "$run_path" --out-dir "benchmarks/plots/${run_id}"
```

The shell precheck is not atomic overwrite protection. The harness currently
overwrites an existing `--out`; `make benchmark` uses `<date>-run.json` and
defaults to 2000 shots. `make plot` reuses fixed figure names. Enforced archive
protection and semantic validation are open [P1-R1](../docs/roadmap.md#p1-r1--protect-and-validate-evidence)
tasks. Never overwrite an existing measured run or hand-edit its numbers.

Preserve disagreements and analyze uncertainty under a declared protocol;
one recorded standard deviation is not a significance threshold.
`data/sample_run.json` remains synthetic and unplottable.

For another device, record the actual hardware and backend configuration.
Use the [benchmark submission template](../.github/ISSUE_TEMPLATE/benchmark_submission.yml).
The current schema has provenance gaps; a hardware label alone is insufficient
to establish comparable controls. An AMD GPU vs CPU quantum fallback is not
a same-GPU comparison.

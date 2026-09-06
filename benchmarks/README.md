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
missing provenance into an old record or guarantee identical stochastic outcomes.

```bash
# Explicit unique name; the writer also enforces no-overwrite protection.
run_id=$(python -c 'import uuid; print(uuid.uuid4().hex)')
run_path="benchmarks/runs/${run_id}.json"
test ! -e "$run_path" && python -m benchmarks.harness --power-profile turbo --shots 4000 --out "$run_path"
python -m benchmarks.plot "$run_path" --out-dir "benchmarks/plots/${run_id}"
```

The writer validates schema-3 records and exclusively creates the output file;
existing files are rejected, including competing-writer collisions. `make
benchmark` generates a date-plus-UUID name and defaults to 2000 shots. `make
plot` defaults to a run-specific subdirectory; both theme paths must be unused.
Use a new directory/stem to render again. See [schema and legacy rules](../docs/run-file.md).
Schema 3 captures source hashes, installed distributions, selected device, target/precision
and every timed outcome/count distribution. New findings need a [human review record](../docs/findings-review.md).

Preserve disagreements and analyze uncertainty under a declared protocol;
one recorded standard deviation is not a significance threshold.
`data/sample_run.json` remains synthetic and unplottable.

For another device, record the actual hardware and backend configuration.
Use the [benchmark submission template](../.github/ISSUE_TEMPLATE/benchmark_submission.yml).
The hardware label defaults to the selected GPU UUID. Only one CUDA device may
be visible for the current measured protocol; choose visibility before starting
Python. A hardware label alone does not establish comparable controls. An AMD GPU vs CPU quantum fallback is not
a same-GPU comparison.

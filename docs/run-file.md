# Run-file validation and archive behavior

The executable contract is [benchmarks/run_file.py](../benchmarks/run_file.py),
shared by the writer, plotter, narrator and CI. This covers the π experiment;
a future decoding study needs an explicitly specified schema extension.

| Format | Accepted use |
| --- | --- |
| `q1729/run-file/3` | Current measured output with source/device provenance and per-repeat outcomes |
| `q1729/run-file/2` | Legacy read-only input with control/row target consistency |
| `q1729/run-file/1`, measured | Legacy read-only input; existing archive stays unchanged |
| `q1729/run-file/1`, synthetic | Explicitly labeled narrator example only |
| Unknown version or implicit/coerced synthetic flag | Rejected |

Measured records require a nonempty question, hypothesis, variables, controls,
UTC timestamp, hardware identifier, environment/software metadata, statistical
treatment, limitations and both experiment arms. Strings are not coerced to
numbers; booleans are not accepted as integer counts. Nonfinite values anywhere
in the payload are rejected.

Rows require valid method/configuration, positive timing samples, matching repeat
counts and internally consistent mean/minimum/sample standard deviation. π error
and relative-error digit summaries must agree with the recorded estimate.
Quantum rows require a supported target and shots/domain/total-qubit/Grover-count
consistency. Duplicate configurations and mixed targets are rejected. Versions
2 and 3 require the control target to match the rows. Extra metadata is preserved.

## Schema 3 traceability

- `provenance` contains Git revision, dirty state and hashes of execution source,
  including untracked source files. The writer rejects source changes during a
  run. Dirty-source hashes do not reconstruct modified files: preserve matching
  source separately or prefer a clean committed checkout.
- `environment.packages` records all resolved installed distributions. This
  identifies versions but does not provide a portable environment lock.
- `execution` records the selected CuPy device ordinal/PCI identity, GPU UUID,
  CUDA runtime/driver, queried CUDA-Q target/precision and relevant runtime
  controls. Monitoring queries that device. The current measured protocol
  requires one visible CUDA device; multi-device mapping needs a separate protocol.
- `configuration` records actual sweeps, timing boundary, compiler options,
  seed schedule and the meaning of row summaries. CPU fallback labels are explicit.
- `runs[].outcomes` retains each timed classical partial sum/estimate or QAE
  count distribution and derived result. Counts must sum to shots; each result
  must agree with its selected count peak. The top-level row describes the last
  timed outcome; timing summaries still use every repeat.

Optional `--seed N` uses `N + counting_qubits * repeats + repeat_index`, with
unseeded warmup. Invalid schedules are rejected; seeded tensornet is excluded
from this currently validated protocol. QAE ties select the lexicographically
smallest bitstring. Seeds cannot guarantee identical outcomes across targets,
versions or hardware. Statevector bytes use queried precision and describe an
analytical equivalent, not measured allocation on a tensor-network backend.

The historical synthetic example has its own deliberately smaller contract and
must retain a note identifying it as synthetic. Relabeling that example as
measured fails the measured contract. Validation does not prove that observations
were collected, validate every scientific claim, or infer missing provenance.

```bash
python -m benchmarks.run_file benchmarks/runs/2026-08-05-rtx5070-turbo.json
```

JSON writes use exclusive creation after validation and reject existing paths
before expensive work. A competing writer appearing later is also protected.
Plots default to `benchmarks/plots/<run-file-stem>/` and reserve both theme paths
exclusively. Use a new directory/stem for a revised rendering. On an ordinary
write/render exception, only files created by that operation are removed.
Abrupt process termination can leave an incomplete file; validation will reject
incomplete JSON, and a reserved output is never silently overwritten on retry.

See [ADR 008](adr/008-versioned-evidence-validation-and-exclusive-archives.md),
[ADR 009](adr/009-traceable-outcomes-and-reviewed-releases.md),
[research standards](handbook/research-standards.md), [findings review](findings-review.md)
and [benchmark commands](../benchmarks/README.md).

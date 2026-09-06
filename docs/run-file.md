# Run-file validation and archive behavior

The executable contract is [benchmarks/run_file.py](../benchmarks/run_file.py),
shared by the writer, plotter, narrator and CI. This covers the π experiment;
a future decoding study needs an explicitly specified schema extension.

| Format | Accepted use |
| --- | --- |
| `q1729/run-file/2` | Current measured output, including `controls.quantum_target` |
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
consistency. Duplicate configurations and mixed targets are rejected. Version 2
also requires the control target to match the rows. Extra metadata is preserved.

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
[research standards](handbook/research-standards.md) and [benchmark commands](../benchmarks/README.md).

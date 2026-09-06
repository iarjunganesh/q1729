# Research Standards

The contract every new q1729 experiment must satisfy, adopted in
[Phase 0](../roadmap.md#phase-0--constitution-lightweight). These are requirements,
not a claim of complete enforcement. The 2026-09-06 audit found key-presence
checks, incomplete provenance and final-outcome-only rows. Phase 1 tracks repairs.

## Nine required fields

| Field | Requirement | Current location / gap |
| --- | --- | --- |
| Question | Narrow enough to answer with this run | `question` |
| Hypothesis | Reasoned prediction committed before collection | `hypothesis`; constant alone does not prove timing |
| Variables | Explicit per-arm sweep | `variables` |
| Controls | Power mode, precision, noise, shots, seeds and timing boundary as applicable | `controls`; actual backend labels need repair |
| Hardware | Actual selected device identity and execution context | `hardware_id`, `environment.gpu`; selected UUID missing |
| Software | Source revision/dirty state, runtime, resolved dependencies | `environment`; capture is incomplete |
| Statistical treatment | Repeats, warmup, uncertainty, exclusions, stopping rule | `statistical_treatment`; richer analysis remains needed |
| Raw data | Every repeat's timing and numerical outcome/counts | `runs[].samples_s`; final outcome alone is insufficient |
| Limitations | Explicit scope, confounds and unverified claims | `limitations` |

Semantic validation must reject absent, empty, mistyped or inconsistent values;
mere JSON key presence is insufficient. Version schema changes and preserve
old archives under explicit legacy handling. Never silently rewrite measured data.

## Prospective and exploratory work

Commit the question/protocol before collecting a prospective run, recording its
revision in the artifact. A module constant first appearing with the result
does not substantiate preregistration. The first π archive is exploratory;
that is useful evidence when labeled accurately. Do not rewrite its hypothesis.

## Timing and statistical treatment

Both arms currently discard a warmup. This reduces initial setup effects but
does not isolate device time: wrapper construction, allocation, transfers and
other overhead remain. Declare what is timed; profile before assigning causes.

Retain samples and outcomes, derive summaries, and quantify uncertainty appropriate
to the question. A recorded standard deviation is not a significance threshold.
For decoding, report failure-rate uncertainty and stopping criteria as well as
timing. Preserve negative results and disagreements; do not rerun until favorable.

## Controls and metrics

- Require an explicit power/thermal profile and record competing device activity.
- Record actual target/precision, not an assumed cuStateVec label after fallback.
- Distinguish relative-error digits against `math.pi` from absolute-error digits
  against exact references. Zero floating-point error does not prove exact π.
- Whole-device memory before/after a run is not process-specific peak allocation.
- Sampled utilization describes activity during a sampling interval; it does not
  prove arithmetic saturation or a dispatch bottleneck without profiling.
- Host-side deterministic reduction does not guarantee cross-toolchain bit identity.

## Synthetic data and narration

`data/sample_run.json` remains labeled synthetic and the plotter rejects it.
NIM receives the full supplied run object and drafts unchecked prose. Source
data must remain separate from model output; review quantitative and causal
claims before publishing findings. Never use narration to fill missing data.

## Reproduction

Follow [benchmark instructions](../../benchmarks/README.md#reproducing), preserving
unique run/figure paths. The current writer can overwrite an existing path;
enforcement is open P1-R1 work. Reproduce configuration and resolved environment,
then analyze differences with a declared uncertainty method. Statistics are
required now; Phase 5 only adds reusable cross-run tooling.

See [Principles](principles.md) and the [roadmap](../roadmap.md).

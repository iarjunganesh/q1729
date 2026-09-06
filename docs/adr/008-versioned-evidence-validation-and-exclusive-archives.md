# ADR 008 — Versioned evidence validation and exclusive archives

Date: 2026-09-06

Status: Accepted

## Context

P1-R1 found that existing output paths could be overwritten and JSON key checks
accepted incomplete or contradictory evidence. The archive and synthetic example
already use schema 1 and must remain readable without rewriting history.

## Decision

Use the CPU-safe, standard-library `benchmarks/run_file.py` validator at the
harness writer, plotter, narrator and CI archive check. Current writers emit
`q1729/run-file/2`, including `controls.quantum_target`; version 1 remains a
read-only legacy format. Only the narrator allows explicitly labeled legacy
synthetic examples. Unknown schemas and inconsistent measured records fail closed.

Use exclusive file creation for JSON and both SVG outputs. Reject existing JSON
before GPU initialization, and enforce exclusivity again at write time to close
the competing-writer race. Reserve both figure paths before drawing; remove only
newly created files on ordinary exceptions. Use unique Makefile run names and
run-specific default plot directories.

## Consequences

Malformed records previously accepted by shallow checks are now rejected. Valid
archived data is returned unchanged. Validation checks internal consistency; it
does not authenticate measurements, prove claims or supply missing provenance.
P1-R2 still owns source/device provenance and per-repeat outcomes.

Existing figures cannot be regenerated in place: use a new output directory or
stem. A killed process or machine failure can leave incomplete output, so readers
must validate records; this change does not claim crash-atomic paired publication.
GPU/CI verification remains separate from CPU boundary tests and line coverage.

"""Versioned validation of the pi experiment's evidence, without rewriting it.

Versions 1 to 3 are read-only legacy formats (including the version-1 demo).
Version 4 is emitted by current writers and adds the committed measurement
protocol (roadmap P1-R3) alongside version 3's traceability. Validation
establishes structural and internal consistency, not that a measurement
happened or a hypothesis is true.
"""

import argparse
import json
import math
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_SCHEMA = "q1729/run-file/4"
TRACEABLE_SCHEMA = "q1729/run-file/3"
PREVIOUS_SCHEMA = "q1729/run-file/2"
LEGACY_SCHEMA = "q1729/run-file/1"

#: Every schema this module will read. Only CURRENT_SCHEMA is ever written.
READABLE_SCHEMAS = (CURRENT_SCHEMA, TRACEABLE_SCHEMA, PREVIOUS_SCHEMA, LEGACY_SCHEMA)

#: Schemas carrying the version-3 provenance/traceability block.
PROVENANCE_SCHEMAS = (CURRENT_SCHEMA, TRACEABLE_SCHEMA)


def require(condition: bool, message: str) -> None:
    """Raise a data error rather than relying on optimization-sensitive asserts."""
    if not condition:
        raise ValueError(message)


def text(value: Any, field: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be nonempty text")


def integer(value: Any, field: str, minimum: int = 1) -> None:
    require(type(value) is int and value >= minimum, f"{field} must be an integer >= {minimum}")


def number(value: Any, field: str, minimum: float = -math.inf) -> None:
    require(type(value) in (int, float), f"{field} must be a number")
    require(math.isfinite(value) and value >= minimum, f"{field} must be finite and >= {minimum}")


def finite_tree(value: Any) -> None:
    """Reject nonfinite numbers even inside optional metadata or unknown fields."""
    if isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)
    elif type(value) in (int, float):
        number(value, "numeric value")


def validate(payload: Any, *, allow_synthetic: bool = False, allow_legacy: bool = True) -> dict[str, Any]:
    """Validate and return the original object; never coerce or fill missing data."""
    require(isinstance(payload, dict), "run file must be an object")
    require(type(payload.get("synthetic")) is bool, "synthetic must be an explicit boolean")
    synthetic = payload["synthetic"]
    require(allow_synthetic or not synthetic, "synthetic demo data cannot be used as measured evidence")
    schema = payload.get("schema")
    require(schema in READABLE_SCHEMAS, "unknown run-file schema")
    require(allow_legacy or schema == CURRENT_SCHEMA, "legacy schema is read-only")
    finite_tree(payload)
    for key in ("hardware_id", "series", "question"):
        text(payload.get(key), key)
    require(payload["series"] == "ramanujan-1914", "unsupported experiment series")
    controls = payload.get("controls")
    require(isinstance(controls, dict), "controls must be an object")
    for key in ("shots", "domain_qubits"):
        integer(controls.get(key), f"controls.{key}")
    text(controls.get("power_profile"), "controls.power_profile")
    rows = payload.get("runs")
    require(isinstance(rows, list) and bool(rows), "runs must be a nonempty array")
    if synthetic:
        require(schema == LEGACY_SCHEMA, "synthetic examples use the legacy demo schema")
        text(payload.get("note"), "synthetic note")
        require("synthetic" in payload["note"].lower(), "note must identify synthetic data")
    else:
        for key in ("hypothesis", "statistical_treatment", "recorded_utc"):
            text(payload.get(key), key)
        stamp = payload["recorded_utc"]
        require(stamp.endswith("Z"), "recorded_utc must use UTC Z notation")
        datetime.fromisoformat(stamp)
        variables = payload.get("variables")
        require(isinstance(variables, dict), "variables must be an object")
        for key in ("classical", "quantum"):
            text(variables.get(key), f"variables.{key}")
        limitations = payload.get("limitations")
        require(isinstance(limitations, list) and bool(limitations), "limitations must be a nonempty array")
        for item in limitations:
            text(item, "limitation")
        if schema not in PROVENANCE_SCHEMAS:
            text(controls.get("precision"), "controls.precision")
        integer(controls.get("threads_per_block"), "controls.threads_per_block")
        env = payload.get("environment")
        require(isinstance(env, dict), "environment must be an object")
        for key in ("python", "platform", "power_profile"):
            text(env.get(key), f"environment.{key}")
        require(env["power_profile"] == controls["power_profile"], "power profile mismatch")
        packages = env.get("packages")
        require(isinstance(packages, dict) and bool(packages), "environment.packages must be nonempty")
        for key, version in packages.items():
            text(key, "package name")
            text(version, "package version")
        gpu = env.get("gpu")
        require(isinstance(gpu, dict), "classical CUDA evidence requires GPU metadata")
        for key in ("name", "driver_version"):
            text(gpu.get(key), f"environment.gpu.{key}")

    methods = set()
    configurations = set()
    targets = set()
    for row in rows:
        require(isinstance(row, dict), "each run row must be an object")
        method = row.get("method")
        require(method in ("classical-cuda", "qae-cudaq"), "unsupported method")
        methods.add(method)
        parameter = "n_terms" if method == "classical-cuda" else "counting_qubits"
        integer(row.get(parameter), parameter)
        identity = (method, row[parameter])
        require(identity not in configurations, "duplicate configuration")
        configurations.add(identity)
        number(row.get("mean_s"), "mean_s", 0)
        require(row["mean_s"] > 0, "mean_s must be positive for log plots")
        number(row.get("correct_digits"), "correct_digits")
        if method == "qae-cudaq":
            m = row[parameter]
            integer(row.get("grover_applications"), "grover_applications")
            g = row["grover_applications"]
            require(g.bit_length() == m and g & (g + 1) == 0, "Grover count mismatch")
        if synthetic:
            continue
        integer(row.get("repeats"), "repeats")
        samples = row.get("samples_s")
        require(isinstance(samples, list) and len(samples) == row["repeats"], "repeat/sample count mismatch")
        for sample in samples:
            number(sample, "sample", 0)
            require(sample > 0, "timing samples must be positive")
        expected = {
            "mean_s": statistics.fmean(samples),
            "min_s": min(samples),
            "stdev_s": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        }
        for key, result in expected.items():
            number(row.get(key), key, 0)
            require(math.isclose(row[key], result, rel_tol=1e-9, abs_tol=1e-15), f"{key} disagrees with samples")
        number(row.get("pi_estimate"), "pi_estimate")
        number(row.get("abs_error"), "abs_error", 0)
        error = abs(row["pi_estimate"] - math.pi)
        require(math.isclose(row["abs_error"], error, rel_tol=1e-9, abs_tol=1e-15), "abs_error mismatch")
        digits = 16.0 if error == 0 else -math.log10(error / math.pi)
        require(math.isclose(row["correct_digits"], digits, rel_tol=1e-9, abs_tol=1e-12), "correct_digits mismatch")
        if method == "qae-cudaq":
            text(row.get("target"), "target")
            require(row["target"] in ("nvidia", "nvidia-mgpu", "tensornet", "qpp-cpu"), "unsupported target")
            targets.add(row["target"])
            for key in ("shots", "domain_qubits"):
                integer(row.get(key), key)
                require(row[key] == controls[key], f"{key} disagrees with controls")
            integer(row.get("total_qubits"), "total_qubits")
            require(row["total_qubits"] == m + controls["domain_qubits"] + 1, "total_qubits mismatch")
    require(methods == {"classical-cuda", "qae-cudaq"}, "both experiment arms are required")
    if not synthetic:
        require(len(targets) == 1, "mixed quantum targets require separate run files")
        if schema != LEGACY_SCHEMA:
            require(controls.get("quantum_target") in tuple(targets), "controls.quantum_target mismatch")
        if schema in PROVENANCE_SCHEMAS:
            validate_provenance(payload)
        if schema == CURRENT_SCHEMA:
            validate_protocol(payload)
    return payload


def validate_provenance(payload: dict[str, Any]) -> None:
    """Validate traceability and per-repeat result/count relationships in v3."""
    import re

    source: Any = payload.get("provenance")
    require(isinstance(source, dict), "provenance must be an object")
    require(
        isinstance(source.get("revision"), str) and bool(re.fullmatch(r"[0-9a-f]{40}", source["revision"])),
        "source revision must be a Git SHA",
    )
    require(type(source.get("dirty")) is bool, "dirty must be boolean")
    files = source.get("files_sha256")
    require(isinstance(files, dict) and bool(files), "source file hashes required")
    for name, digest in files.items():
        text(name, "source path")
        require(isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "invalid source hash")
    execution: Any = payload.get("execution")
    require(isinstance(execution, dict), "execution metadata required")
    classical, quantum = execution.get("classical"), execution.get("quantum")
    require(isinstance(classical, dict) and isinstance(quantum, dict), "both execution arms required")
    for key in ("uuid", "pci_bus_id", "backend"):
        text(classical.get(key), f"classical.{key}")
    for key in ("cuda_runtime", "cuda_driver"):
        integer(classical.get(key), key)
    require(classical.get("precision") == "fp64", "classical precision mismatch")
    require(quantum.get("target") == payload["controls"]["quantum_target"], "execution target mismatch")
    require(quantum.get("precision") in ("fp32", "fp64"), "quantum precision required")
    require(
        payload["controls"]["precision"] == {"classical": "fp64", "quantum": quantum["precision"]},
        "precision controls mismatch",
    )
    cpu = quantum["target"] == "qpp-cpu"
    require(quantum.get("processor") == ("cpu" if cpu else "gpu"), "processor mismatch")
    require(quantum.get("uuid") == (None if cpu else classical["uuid"]), "quantum device mismatch")
    require(quantum.get("pci_bus_id") == (None if cpu else classical["pci_bus_id"]), "quantum PCI mapping mismatch")
    require(payload["environment"]["gpu"].get("uuid") == classical["uuid"], "environment device mismatch")
    config: Any = payload.get("configuration")
    require(isinstance(config, dict), "configuration required")
    for key in ("seed_schedule", "outcome_summary", "timing_boundary"):
        text(config.get(key), key)
    for key, method, parameter in (
        ("classical_term_counts", "classical-cuda", "n_terms"),
        ("counting_qubits", "qae-cudaq", "counting_qubits"),
    ):
        require(
            config.get(key) == [row[parameter] for row in payload["runs"] if row["method"] == method],
            "configuration sweep mismatch",
        )
    seed = config.get("seed")
    if seed is not None:
        integer(seed, "seed")
    for row in payload["runs"]:
        outcomes = row.get("outcomes")
        require(isinstance(outcomes, list) and len(outcomes) == row["repeats"], "outcome/repeat count mismatch")
        for i, outcome in enumerate(outcomes):
            require(isinstance(outcome, dict), "outcome must be an object")
            for key in ("pi_estimate", "abs_error", "correct_digits"):
                number(outcome.get(key), key)
            error = abs(outcome["pi_estimate"] - math.pi)
            require(math.isclose(outcome["abs_error"], error, rel_tol=1e-9, abs_tol=1e-15), "outcome error mismatch")
            digits = 16.0 if error == 0 else -math.log10(error / math.pi)
            require(
                math.isclose(outcome["correct_digits"], digits, rel_tol=1e-9, abs_tol=1e-12), "outcome digits mismatch"
            )
            if row["method"] == "classical-cuda":
                number(outcome.get("partial_sum"), "partial_sum", 0)
                require(outcome["partial_sum"] > 0, "partial sum must be positive")
                estimate = 1 / ((2 * math.sqrt(2) / 9801) * outcome["partial_sum"])
                require(math.isclose(estimate, outcome["pi_estimate"], rel_tol=1e-12), "partial sum estimate mismatch")
            else:
                require(
                    outcome.get("target") == quantum["target"] and outcome.get("precision") == quantum["precision"],
                    "outcome backend mismatch",
                )
                m = row["counting_qubits"]
                for key in ("counting_qubits", "domain_qubits", "shots", "total_qubits", "grover_applications"):
                    require(outcome.get(key) == row[key], "outcome configuration mismatch")
                counts = outcome.get("counts")
                require(isinstance(counts, dict) and bool(counts), "QAE counts required")
                for bits, count in counts.items():
                    require(
                        isinstance(bits, str) and len(bits) == m and set(bits) <= {"0", "1"}, "invalid count bitstring"
                    )
                    integer(count, "count", 0)
                require(sum(counts.values()) == row["shots"], "count total differs from shots")
                best = min(counts, key=lambda bits: (-counts[bits], bits))
                require(outcome.get("outcome") == int(best, 2), "selected outcome mismatch")
                require(outcome.get("peak_probability") == counts[best] / row["shots"], "peak probability mismatch")
                estimate = 4 * math.sin(math.pi * int(best, 2) / 2**m) ** 2
                require(math.isclose(estimate, outcome["pi_estimate"], abs_tol=1e-14), "QAE estimate/count mismatch")
                require(
                    outcome.get("seed") == (None if seed is None else seed + m * row["repeats"] + i),
                    "repeat seed mismatch",
                )
                text(outcome.get("seed_policy"), "seed policy")
                text(outcome.get("reproducibility_limit"), "reproducibility limit")
        for key in ("pi_estimate", "abs_error", "correct_digits"):
            require(row[key] == outcomes[-1][key], "row must summarize the last timed outcome")
        if row["method"] == "qae-cudaq":
            for key in ("counts", "outcome", "seed", "precision", "peak_probability"):
                require(row.get(key) == outcomes[-1][key], "QAE row differs from final timed outcome")


def validate_protocol(payload: dict[str, Any]) -> None:
    """Validate the committed measurement protocol and uncertainty block (v4).

    The digest is recomputed from the declaration the file itself carries, not
    from the current :mod:`benchmarks.protocol`. An archived run must stay
    valid after the protocol changes — what the check establishes is that the
    declaration and its digest were not altered independently of each other,
    so a run cannot claim a protocol it did not follow.
    """
    from benchmarks import protocol

    block: Any = payload.get("protocol")
    require(isinstance(block, dict), "protocol block required")
    declared = block.get("declaration")
    require(isinstance(declared, dict), "protocol.declaration must be an object")
    integer(declared.get("protocol_version"), "protocol_version")
    for key in ("warmup_policy", "exclusion_rule", "stopping_rule", "uncertainty_method"):
        text(declared.get(key), f"protocol.{key}")
    boundaries = declared.get("timing_boundaries")
    require(isinstance(boundaries, dict) and bool(boundaries), "timing boundaries required")
    for name, description in boundaries.items():
        text(name, "timing boundary name")
        text(description, "timing boundary description")
    require(block.get("digest") == protocol.digest_of(declared), "protocol digest disagrees with its declaration")

    for row in payload["runs"]:
        samples = row["samples_s"]
        expected = protocol.uncertainty(samples)
        for key in ("sem_s", "ci95_low_s", "ci95_high_s", "relative_stdev"):
            number(row.get(key), key)
            require(math.isclose(row[key], expected[key], rel_tol=1e-9, abs_tol=1e-15), f"{key} disagrees with samples")
        require(row["ci95_low_s"] <= row["mean_s"] <= row["ci95_high_s"], "mean must lie inside its own interval")


def load(path: str | Path, *, allow_synthetic: bool = False) -> dict[str, Any]:
    """Load validated measured or explicitly allowed legacy synthetic data."""
    return validate(json.loads(Path(path).read_text(encoding="utf-8")), allow_synthetic=allow_synthetic)


#: Sidecars that live beside run files, share the ``.json`` suffix, and are
#: validated by their own module. CI expands ``benchmarks/runs/*.json``, so a
#: shell glob hands them to this validator; each schema is owned by exactly one
#: validator, and ``analysis.review`` owns this one.
SIDECAR_SUFFIX = ".review.json"


def main(argv: list[str] | None = None) -> int:
    """Validate explicit archive paths in CI, failing on any invalid record."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        if path.name.endswith(SIDECAR_SUFFIX):
            print(f"skipped {path} (findings review sidecar; see analysis.review)")
            continue
        load(path)
        print(f"validated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

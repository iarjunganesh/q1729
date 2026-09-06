"""Versioned validation of the pi experiment's evidence, without rewriting it.

Version 1 is a read-only legacy format (including the labeled synthetic demo).
Version 2 is emitted by current writers. Validation establishes structural and
internal consistency, not that a measurement happened or a hypothesis is true.
"""

import argparse
import json
import math
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_SCHEMA = "q1729/run-file/2"
LEGACY_SCHEMA = "q1729/run-file/1"


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
    require(schema in (CURRENT_SCHEMA, LEGACY_SCHEMA), "unknown run-file schema")
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
        if schema == CURRENT_SCHEMA:
            require(controls.get("quantum_target") in tuple(targets), "controls.quantum_target mismatch")
    return payload


def load(path: str | Path, *, allow_synthetic: bool = False) -> dict[str, Any]:
    """Load validated measured or explicitly allowed legacy synthetic data."""
    return validate(json.loads(Path(path).read_text(encoding="utf-8")), allow_synthetic=allow_synthetic)


def main(argv: list[str] | None = None) -> int:
    """Validate explicit archive paths in CI, failing on any invalid record."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        load(path)
        print(f"validated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

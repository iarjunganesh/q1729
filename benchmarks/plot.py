"""Crossover plot from a measured run file.

    python -m benchmarks.plot benchmarks/runs/<name>.json --out-dir benchmarks/plots

Writes a light and a dark SVG together, matching the repo's theme-aware asset
convention (``assets/architecture/``, ``assets/brand/``) so the figure is
readable in either GitHub theme. Edit this module, never the generated SVGs.

The left panel is the crossover itself — wall time against correct digits of
pi, both arms on one pair of axes, log time. The right panel is why: the
quantum arm's Grover count against its precision, which is the exponential
that the left panel is a shadow of.
"""

import argparse
from pathlib import Path
from typing import Any

from benchmarks import archive, run_file

#: Light and dark render settings. Only colors differ — identical geometry, so
#: the two files stay comparable side by side.
THEMES: dict[str, dict[str, str]] = {
    "light": {
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#ffffff",
        "axes.edgecolor": "#374151",
        "axes.labelcolor": "#111827",
        "text.color": "#111827",
        "xtick.color": "#374151",
        "ytick.color": "#374151",
        "grid.color": "#d1d5db",
    },
    "dark": {
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#0d1117",
        "axes.edgecolor": "#8b949e",
        "axes.labelcolor": "#e6edf3",
        "text.color": "#e6edf3",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "grid.color": "#30363d",
    },
}

#: NVIDIA green for the classical CUDA arm, violet for the quantum arm —
#: the same two-role palette the architecture diagram uses.
CLASSICAL_COLOR = "#76b900"
QUANTUM_COLOR = "#a371f7"


def load_runs(run_file_path: Path) -> dict[str, Any]:
    """Read a run file, refusing synthetic data.

    ``data/sample_run.json`` exists to demonstrate the schema and is labeled
    synthetic; plotting it would produce a figure indistinguishable from a
    real result, which is precisely the failure this project is built to avoid.
    """
    return run_file.load(run_file_path)


def split_arms(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Partition a run file's rows into the classical and quantum arms."""
    classical = [row for row in payload["runs"] if row["method"] == "classical-cuda"]
    quantum = [row for row in payload["runs"] if row["method"] == "qae-cudaq"]
    return classical, quantum


def render(payload: dict[str, Any], out_dir: Path, stem: str = "crossover") -> list[Path]:
    """Render both themes; returns the paths written."""
    run_file.validate(payload)
    if not stem or Path(stem).name != stem or stem in (".", ".."):
        raise ValueError("stem must be a filename, not a path")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    classical, quantum = split_arms(payload)
    gpu = (payload.get("environment", {}).get("gpu") or {}).get("name", "unknown GPU")
    profile = payload.get("controls", {}).get("power_profile", "unknown")

    out_dir.mkdir(parents=True, exist_ok=True)
    written = [out_dir / f"{stem}-{theme}.svg" for theme in THEMES]

    with archive.create_outputs(written) as streams:
        for (_theme, style), stream in zip(THEMES.items(), streams, strict=True):
            # rc_context is typed with a Literal key union covering every rcParam;
            # a plain dict[str, str] cannot satisfy it without enumerating them.
            with plt.rc_context(style):  # type: ignore[arg-type]
                fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5))

                left.plot(
                    [row["correct_digits"] for row in classical],
                    [row["mean_s"] for row in classical],
                    "o-",
                    color=CLASSICAL_COLOR,
                    label="classical — hand-written CUDA kernel",
                )
                left.plot(
                    [row["correct_digits"] for row in quantum],
                    [row["mean_s"] for row in quantum],
                    "s-",
                    color=QUANTUM_COLOR,
                    label="quantum — QAE on cuStateVec",
                )
                left.set_yscale("log")
                left.set_xlabel("correct digits of $\\pi$")
                left.set_ylabel("wall time (s, log scale)")
                left.set_title("Cost of a digit")
                left.grid(True, alpha=0.4)
                left.legend(loc="best", framealpha=0.0)

                right.plot(
                    [row["counting_qubits"] for row in quantum],
                    [row["grover_applications"] for row in quantum],
                    "s-",
                    color=QUANTUM_COLOR,
                )
                right.set_yscale("log")
                right.set_xlabel("counting qubits $m$ (precision bits)")
                right.set_ylabel("Grover operators applied (log scale)")
                right.set_title("Why: $2^m - 1$ per estimate")
                right.grid(True, alpha=0.4)

                fig.suptitle(f"Ramanujan 1/$\\pi$ crossover — {gpu} (power profile: {profile})")
                fig.tight_layout()

                try:
                    fig.savefig(stream, format="svg")
                finally:
                    plt.close(fig)

    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Command-line interface for the plotter."""
    parser = argparse.ArgumentParser(description="Render the crossover plot from a measured run file")
    parser.add_argument("run_file", type=Path, help="measured run file emitted by benchmarks.harness")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--stem", default="crossover", help="output filename stem")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Render both themes for the given run file. Returns a process exit code."""
    args = parse_args(argv)
    out_dir = args.out_dir or Path("benchmarks/plots") / args.run_file.stem
    for path in render(load_runs(args.run_file), out_dir, args.stem):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Nemotron-via-NIM findings narrator (ADR 003).

Turns a benchmark run file (JSON) into a findings draft in markdown. The
LLM's job is narration and anomaly-spotting — every number comes from the
run file, never from the model. Degrades like `quantum.backend`: without
``NVIDIA_API_KEY`` the module imports fine and reports unavailability.

Run ``python -m analysis.narrator data/sample_run.json`` to try it.
"""

import json
import os
from pathlib import Path

import httpx

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
# NIM retires model ids over time, and /v1/models lists entries that 404 on
# invoke — probe with `make narrate` before trusting a new default.
# Verified invocable 2026-07-10 on this account.
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"

SYSTEM_PROMPT = (
    "You are the findings narrator for q1729, a benchmarking study of computing pi "
    "with Ramanujan's 1914 series: a hand-written CUDA kernel vs Quantum Amplitude "
    "Estimation simulated with CUDA-Q. Draft a concise findings section in markdown "
    "from the run data you are given. Use ONLY the numbers in the data — never invent "
    "measurements. Call out anomalies, the classical/quantum gap, and hardware "
    "differences when multiple hardware entries are present."
)


def nim_configured() -> bool:
    """True when an NVIDIA API key is present in the environment."""
    return bool(os.getenv("NVIDIA_API_KEY"))


def load_run(path: str | Path) -> dict:
    """Load and minimally validate a benchmark run file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [key for key in ("hardware", "runs") if key not in data]
    if missing:
        raise ValueError(f"run file {path} is missing required keys: {missing}")
    return data


def build_prompt(run: dict) -> str:
    """Deterministic user prompt — the run data verbatim, plus the ask."""
    return (
        "Benchmark run data (JSON):\n\n"
        f"{json.dumps(run, indent=2)}\n\n"
        "Draft the findings section for these results."
    )


def narrate(path: str | Path, timeout: float = 60.0) -> str:
    """Return a markdown findings draft for the run file at ``path``."""
    if not nim_configured():
        raise RuntimeError("NVIDIA_API_KEY is not set — see .env.example (ADR 003)")

    run = load_run(path)
    response = httpx.post(
        f"{os.getenv('NIM_BASE_URL', DEFAULT_BASE_URL)}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}"},
        json={
            "model": os.getenv("NIM_MODEL", DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(run)},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def report() -> dict[str, object]:
    """Environment diagnostic used by main.py — mirrors quantum.backend.report."""
    info: dict[str, object] = {"nim_configured": nim_configured()}
    if nim_configured():
        info["model"] = os.getenv("NIM_MODEL", DEFAULT_MODEL)
    else:
        info["hint"] = "set NVIDIA_API_KEY to enable the findings narrator (ADR 003)"
    return info


if __name__ == "__main__":
    import sys

    # Windows consoles default to cp1252, which can't print the model's
    # typography (e.g. narrow no-break spaces)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(narrate(sys.argv[1] if len(sys.argv) > 1 else "data/sample_run.json"))

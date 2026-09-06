"""Use real archive structure for evidence-boundary tests; never publish fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def measured_run():
    return json.loads(Path("benchmarks/runs/2026-08-05-rtx5070-turbo.json").read_text(encoding="utf-8"))

"""Real CUDA-Q smoke test — runs only where cudaq is installed (WSL2 / CI).

Mirrors the sibling-repo pattern (continuum's live-cluster integration tests):
unit tests mock the boundary; this file proves the real backend simulates.
"""

import pytest

from quantum import backend

pytestmark = pytest.mark.skipif(
    not backend.cudaq_available(),
    reason="cudaq not installed (Linux/WSL2 only — see docs/adr/002-wsl2-runtime.md)",
)


def test_a_target_initializes():
    assert backend.select_target() in backend.PREFERRED_TARGETS


def test_bell_pair_simulates_on_selected_target():
    backend.select_target()
    counts = backend.bell_counts(shots=1000)

    # A Bell pair collapses to correlated bits only
    assert set(counts) <= {"00", "11"}
    assert sum(counts.values()) == 1000
    # ... in roughly equal proportion (loose bound; 1000 shots)
    assert 350 <= counts.get("00", 0) <= 650

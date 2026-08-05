"""Real CUDA kernel tests — run only where a GPU and NVRTC are present.

This is what proves ``classical/ramanujan_kernel.cu`` compiles and computes the
right numbers. Unit tests mock cupy at the boundary and can only prove the
launch geometry; correctness lives here, checked against the exact SymPy
ground truth rather than against another floating-point approximation.
"""

import math

import pytest

from classical import cuda_kernel, ramanujan_series

pytestmark = pytest.mark.skipif(
    not cuda_kernel.cuda_available(),
    reason="needs cupy and a visible CUDA device (WSL2 — see docs/adr/002-wsl2-runtime.md)",
)


@pytest.mark.parametrize("n_terms", [1, 2, 3, 5, 10, 64])
def test_kernel_matches_the_exact_sympy_ground_truth(n_terms):
    """The drift check the whole classical arm exists to make.

    Any float error in the kernel — a bad reduction, a lost factor, a
    precision regression — surfaces here as disagreement with exact rationals.
    """
    gpu = cuda_kernel.partial_sum(n_terms)
    exact = float(ramanujan_series.partial_sum(n_terms))
    assert gpu == pytest.approx(exact, rel=1e-15)


def test_kernel_recovers_pi_to_double_precision():
    assert cuda_kernel.pi_approximation(3) == pytest.approx(math.pi, abs=1e-15)


def test_first_term_is_exactly_1103():
    """k=0 has no product loop at all, so it isolates the term formula."""
    assert cuda_kernel.partial_sum(1) == pytest.approx(1103.0, abs=1e-9)


def test_result_is_reproducible_across_runs():
    """Host-side fsum over block partials instead of atomicAdd — see the .cu header."""
    first = cuda_kernel.partial_sum(4096)
    assert all(cuda_kernel.partial_sum(4096) == first for _ in range(3))


@pytest.mark.parametrize("threads", [32, 64, 128, 256, 512])
def test_result_is_independent_of_block_size(threads):
    """Block geometry changes the reduction tree but must not change the sum."""
    assert cuda_kernel.partial_sum(1000, threads_per_block=threads) == pytest.approx(
        cuda_kernel.partial_sum(1000, threads_per_block=256), rel=1e-15
    )


def test_terms_beyond_saturation_do_not_corrupt_the_sum():
    """Terms underflow to zero rather than overflowing — (4k)! would blow up past k=43."""
    assert cuda_kernel.partial_sum(4096) == pytest.approx(cuda_kernel.partial_sum(64), rel=1e-15)


def test_time_partial_sum_returns_usable_measurements():
    timing = cuda_kernel.time_partial_sum(1024, repeats=3)
    assert len(timing["samples_s"]) == 3
    assert timing["min_s"] > 0
    assert timing["mean_s"] >= timing["min_s"]


def test_device_info_describes_a_real_gpu():
    info = cuda_kernel.device_info()
    assert info["vram_gb"] > 0
    assert info["gpu"]
    assert info["cuda_runtime"] > 0

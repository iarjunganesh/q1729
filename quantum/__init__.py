"""Quantum side: CUDA-Q kernels and backend selection.

CUDA-Q is Linux-only — this package must always degrade gracefully on the
Windows host (see docs/adr/002-wsl2-runtime.md).
"""

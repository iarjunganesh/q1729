# Environment setup

The CUDA kernel, QAE circuit and benchmark harness exist. The 2026-09-06 audit
verified the CPU-safe Windows environment; WSL2 could not attach its configured
virtual disk (`HCS/ERROR_PATH_NOT_FOUND`). Historical GPU success does not
establish current runtime availability. No cloud setup/run was tested.

## Windows CPU workflow

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
pytest tests/unit
```

Use the existing environment if already installed. `main.py` is a status check,
not the benchmark. Optional CUDA-Q/CuPy imports must degrade gracefully.
The audit's no-key full-suite result is 219 passed, 29 skipped, 97.87% coverage.
GPU/CUDA-Q runtime paths were not verified on native Windows.

## WSL2/Linux GPU workflow

Use a separate Linux environment; never replace the Windows `.venv` in a shared
checkout. From WSL2 with the checkout at `/mnt/c/ws/q1729`:

```bash
nvidia-smi
python3.12 -m venv ~/q1729-cudaq
source ~/q1729-cudaq/bin/activate
cd /mnt/c/ws/q1729
pip install -r requirements.txt
pip install -r requirements-gpu.txt
python -m quantum.backend
python -m classical.cuda_kernel
pytest tests --cov --cov-report=term-missing --cov-fail-under=100
```

These are the intended commands, not a fresh successful GPU transcript.
Use a Python version supported by published CUDA-Q wheels; CI uses 3.13.
The repository's target order is `nvidia-mgpu` → `nvidia` → `tensornet` →
`qpp-cpu`, guarded by visible GPU count. A single GPU normally selects `nvidia`;
multi-GPU success remains unverified. `nvidia-smi`'s CUDA field describes driver
compatibility, not the installed toolkit/runtime version.

The missing WSL2 disk needs separate diagnosis before these commands can run
on this machine. Do not reinstall/delete a distribution as a documentation step.

## Benchmark

Follow [archive-safe invocation guidance](../benchmarks/README.md#reproducing).
The writer now enforces validation and exclusive creation. Complete provenance
is still missing; new
publication-quality measurements depend on the roadmap's Phase 1 repair gates.

## Optional NIM narrator

Set `NVIDIA_API_KEY` privately in the current process environment. Copying
`.env.example` to `.env` alone does not configure the process: the application
does not load dotenv files. Do not print the key or put it in shell history.

```bash
python -m analysis.narrator data/sample_run.json
```

This sends synthetic example JSON to an external API and returns a draft,
not a measured result. The narrator sends the full supplied run object, including
environment metadata. Review payload and generated claims. No live call was made
in this audit. Configure the variable separately in WSL2 or preserve existing
`WSLENV` entries when adding a sharing rule; do not replace that setting blindly.

## CI and cloud

CI has lint, typecheck, tests and docs jobs. CPU CUDA-Q integration uses
`qpp-cpu`; CUDA-kernel GPU integration skips without a GPU. The 100% coverage
gate remains mandatory and is distinct from real-device numerical verification.
Public CI on the released commit does not verify the unreleased graph/evidence changes.

Cloud follows the same two requirements files and backend diagnostics, with
an explicitly recorded device and environment. H100/multi-GPU execution is
unverified and conditional on a budgeted research question; see
[NVIDIA access](nvidia-access.md).

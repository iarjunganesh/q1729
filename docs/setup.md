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
The audit's no-key full-suite result is 316 passed, 29 skipped, 99.73% coverage.
GPU/CUDA-Q runtime paths were not verified on native Windows.

## WSL2/Linux GPU workflow

Use a separate Linux environment; never replace the Windows `.venv` in a shared
checkout. From WSL2 with the checkout at `/mnt/c/ws/q1729`:

Ubuntu 26.04 ships Python 3.14 and packages no 3.12/3.13, but cudaq publishes
no 3.14 wheel — so the venv uses a uv-managed 3.13. Verified 2026-09-06:

```bash
nvidia-smi
sudo apt-get install -y pipx
pipx install uv
uv python install 3.13
uv venv --python 3.13 ~/q1729-cudaq
cd /mnt/c/ws/q1729
uv pip install --python ~/q1729-cudaq/bin/python -r requirements.txt -r requirements-gpu.txt
~/q1729-cudaq/bin/python -m quantum.backend
~/q1729-cudaq/bin/python -m classical.cuda_kernel
~/q1729-cudaq/bin/python -m pytest tests --cov --cov-report=term-missing --cov-fail-under=100
```

`uv venv` does not seed pip, so install through `uv pip --python <venv python>`
rather than `python -m pip`.

**Set `core.autocrlf` in WSL, or every run file will claim a dirty source.**
The checkout is shared with Windows, whose system git config sets
`core.autocrlf=true`, so the working tree holds CRLF while the index holds LF.
A fresh Linux git has `autocrlf` unset and therefore reports all 41 tracked
text files as modified — `benchmarks/provenance.py` then records
`"dirty": true` on an archive whose source is in fact identical to the commit:

```bash
git config --global core.autocrlf true   # in WSL, matches the Windows checkout
```

Verify with `git status --porcelain | wc -l`, which must print `0`, and with
`python -c "from benchmarks import provenance; print(provenance.source()['dirty'])"`,
which must print `False`, before collecting any measured run.

Output on 2026-09-06:

```
cudaq_available: True
target: nvidia
cuda_available: True
gpu: NVIDIA GeForce RTX 5070 Laptop GPU
vram_gb: 7.93
compute_capability: 12.0
cuda_runtime: 13000
cupy: 13.6.0
344 passed, 1 skipped
Required test coverage of 100% reached. Total coverage: 100.00%
```

The one skip is the live NIM test, which needs `NVIDIA_API_KEY`.
Use a Python version supported by published CUDA-Q wheels; CI uses 3.13.
The repository's target order is `nvidia-mgpu` → `nvidia` → `tensornet` →
`qpp-cpu`, guarded by visible GPU count. A single GPU normally selects `nvidia`;
multi-GPU success remains unverified. `nvidia-smi`'s CUDA field describes driver
compatibility, not the installed toolkit/runtime version.

The missing WSL2 disk needs separate diagnosis before these commands can run
on this machine. Do not reinstall/delete a distribution as a documentation step.

## Benchmark

Follow [archive-safe invocation guidance](../benchmarks/README.md#reproducing).
The writer enforces validation and exclusive creation. Schema 3 captures source,
software/device metadata and per-repeat outcomes; new
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

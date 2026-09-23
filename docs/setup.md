# Environment setup

The CUDA kernel, QAE circuit and benchmark harness exist. On 2026-09-23 both
the CPU-safe Windows environment and the WSL2 GPU environment were verified,
each on Python 3.14 — the only supported interpreter. No cloud setup/run was
tested.

## Windows CPU workflow

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
pytest tests/unit
```

Use the existing environment if already installed. `main.py` is a status check,
not the benchmark. Optional CUDA-Q/CuPy imports must degrade gracefully.
The 2026-09-23 no-key full-suite result is 358 passed, 29 skipped, 99.77% coverage.
GPU/CUDA-Q runtime paths were not verified on native Windows.

## WSL2/Linux GPU workflow

Use a separate Linux environment; never replace the Windows `.venv` in a shared
checkout. From WSL2 with the checkout at `/mnt/c/ws/research/q1729`:

**Name the distro.** This machine's repository distro is registered as
`Ubuntu` (Ubuntu 26.04 "resolute"). The default distro is a stale
`Ubuntu-22.04` registration whose `ext4.vhdx` no longer exists, left behind
when WSL2 was rebuilt on 2026-09-06. A bare `wsl` or `wsl -e` therefore fails
with `HCS/ERROR_PATH_NOT_FOUND` even though the real distro is healthy. Enter
it with `wsl -d Ubuntu`.

The venv at `~/q1729-cudaq` was rebuilt on 2026-09-23 with uv-managed Python
3.14.7:

```bash
nvidia-smi
uv python install 3.14
uv venv --python 3.14 ~/q1729-cudaq
cd /mnt/c/ws/research/q1729
uv pip install --python ~/q1729-cudaq/bin/python -r requirements.txt -r requirements-gpu.txt
~/q1729-cudaq/bin/python -m quantum.backend
~/q1729-cudaq/bin/python -m classical.cuda_kernel
~/q1729-cudaq/bin/python -m pytest tests --cov --cov-report=term-missing --cov-fail-under=100
```

The previous Python 3.13.15 venv is parked at `~/q1729-cudaq-py313-old` as a
rollback; delete it once the 3.14 environment has carried a measured run.

`uv venv` does not seed pip, so install through `uv pip --python <venv python>`
rather than `python -m pip`.

**Set `core.autocrlf` in WSL, or every run file will claim a dirty source.**
The checkout is shared with Windows, whose system git config sets
`core.autocrlf=true`, so the working tree holds CRLF while the index holds LF.
A fresh Linux git has `autocrlf` unset and can report tracked text files as
modified — `benchmarks/provenance.py` then records
`"dirty": true` on an archive whose source is in fact identical to the commit:

```bash
git config --global core.autocrlf true   # in WSL, matches the Windows checkout
```

Verify with `git status --porcelain | wc -l`, which must print `0`, and with
`python -c "from benchmarks import provenance; print(provenance.source()['dirty'])"`,
which must print `False`, before collecting any measured run.

Output on 2026-09-23 (Python 3.14.7, cudaq 0.16.0.post1, NVIDIA driver 616.92):

```
cudaq_available: True
target: nvidia
cuda_available: True
gpu: NVIDIA GeForce RTX 5070 Laptop GPU
vram_gb: 7.93
compute_capability: 12.0
cuda_runtime: 13020
cupy: 14.2.0
Required test coverage of 100% reached. Total coverage: 100.00%
386 passed, 1 skipped
```

The one skip is the live NIM test, which needs `NVIDIA_API_KEY`.
Python 3.14 is the only supported interpreter, on every host and in CI.
The repository's target order is `nvidia-mgpu` → `nvidia` → `tensornet` →
`qpp-cpu`, guarded by visible GPU count. A single GPU normally selects `nvidia`;
multi-GPU success remains unverified. `nvidia-smi`'s CUDA field describes driver
compatibility, not the installed toolkit/runtime version.

Do not reinstall, unregister or delete a distribution as a documentation step;
removing the stale `Ubuntu-22.04` registration is the owner's call.

## Benchmark

Follow [archive-safe invocation guidance](../benchmarks/README.md#reproducing).
The writer enforces validation and exclusive creation. Schema 3 captures source,
software/device metadata and per-repeat outcomes; new
publication-quality measurements depend on the roadmap's open evidence repairs.

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
Public CI on a released commit does not verify newer unreleased changes.

Cloud follows the same two requirements files and backend diagnostics, with
an explicitly recorded device and environment. H100/multi-GPU execution is
unverified and conditional on a budgeted research question; see
[NVIDIA access](nvidia-access.md).

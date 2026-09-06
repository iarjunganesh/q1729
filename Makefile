.PHONY: install install-gpu run gpu-check cuda-check narrate benchmark plot test lint format typecheck coverage

install:
	pip install -r requirements.txt

# WSL2 only — no native Windows wheels (docs/adr/002-wsl2-runtime.md)
install-gpu:
	pip install -r requirements-gpu.txt

run:
	python main.py

gpu-check:
	python -m quantum.backend

cuda-check:
	python -m classical.cuda_kernel

# NIM findings narrator on the synthetic sample run (needs NVIDIA_API_KEY, ADR 003)
narrate:
	python -m analysis.narrator data/sample_run.json

# Stage-1 crossover benchmark. POWER_PROFILE is required, not defaulted: the
# vendor power/thermal mode changes every timing in the output, so it is a
# declared control (docs/handbook/research-standards.md).
POWER_PROFILE ?=
RUN ?=
benchmark:
	@test -n "$(POWER_PROFILE)" || (echo "set POWER_PROFILE=<turbo|performance|silent|...> — it is a recorded control"; exit 1)
	python -m benchmarks.harness --power-profile $(POWER_PROFILE) \
		--out benchmarks/runs/$(shell date +%Y-%m-%d)-$(shell python -c "import uuid; print(uuid.uuid4().hex)").json

plot:
	@test -n "$(RUN)" || (echo "set RUN=benchmarks/runs/<file>.json"; exit 1)
	python -m benchmarks.plot $(RUN)

test:
	pytest tests -v

lint:
	ruff check .
	ruff format --check .

# Apply the formatting `lint` only checks.
format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy classical quantum analysis benchmarks scripts

coverage:
	pytest tests --cov --cov-report=term-missing --cov-fail-under=100

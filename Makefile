.PHONY: install install-gpu run gpu-check narrate test lint coverage

install:
	pip install -r requirements.txt

# WSL2 only — no native Windows wheels (docs/adr/002-wsl2-runtime.md)
install-gpu:
	pip install -r requirements-gpu.txt

run:
	python main.py

gpu-check:
	python -m quantum.backend

# NIM findings narrator on the synthetic sample run (needs NVIDIA_API_KEY, ADR 003)
narrate:
	python -m analysis.narrator data/sample_run.json

test:
	pytest tests -v

lint:
	ruff check .

coverage:
	pytest tests --cov --cov-report=term-missing

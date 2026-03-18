PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
RUFF := $(VENV)/bin/ruff

.PHONY: bootstrap-python verify-python test-python lint-python format-python-check smoke-python smoke-importer smoke-backend ci-python

bootstrap-python:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e backend
	$(PIP) install -e tools/system-design-space-importer
	$(PIP) install ruff

lint-python:
	$(RUFF) check backend tools/system-design-space-importer

format-python-check:
	$(RUFF) format --check backend tools/system-design-space-importer

test-python:
	$(PY) -m unittest discover -s backend/tests -q
	$(PY) -m unittest discover -s tools/system-design-space-importer/tests -q

smoke-importer:
	$(PY) -m unittest discover -s tools/system-design-space-importer/tests -p 'test_smoke_pipeline.py' -q

smoke-backend:
	$(PY) -m unittest discover -s backend/tests -p 'test_smoke_backend_loop.py' -q

smoke-python: smoke-importer smoke-backend

verify-python: lint-python format-python-check test-python

ci-python: verify-python smoke-python

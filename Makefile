BOOTSTRAP_PYTHON ?= python3
PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
RUFF := $(VENV)/bin/ruff

.PHONY: bootstrap-python verify-python test-python lint-python format-python-check

bootstrap-python:
	$(BOOTSTRAP_PYTHON) -m pip install --user virtualenv
	$(BOOTSTRAP_PYTHON) -m virtualenv -p $(PYTHON) $(VENV)
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

verify-python: lint-python format-python-check test-python

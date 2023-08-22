# Variables
PYTHON_VERSION := 3.11
VENV ?= .venv
JOBS ?= 4

CHAINS_FILES=\
	chains

# Targets
.PHONY: test clean lint install venv requirements

clean:
	rm -rf *.pyc __pycache__/ htmlcov/

lint: flake8

flake8:
	$(VENV)/bin/flake8 --jobs $(JOBS) --statistics --show-source $(CHAINS_FILES)

init: venv .create-venv requirements .install-pre-commit

venv:
	$(PYTHON) -m venv .venv

.create-venv:
	test -d $(VENV) || python$(PYTHON_VERSION) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry

.install-pre-commit:
	$(VENV)/bin/poetry run pre-commit install

requirements:
	$(VENV)/bin/poetry install
	. .venv/bin/activate

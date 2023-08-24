# Variables
PYTHON := python
PYTHON_VERSION := 3.11
VENV ?= .venv

THREADS = 4
RE_RUNS = 2
RE_RUN_DELAY = 15
ALLURE_DIR = allure-results
TEST_RUN = $(VENV)/bin/python -m pytest --rootdir . --alluredir=$(ALLURE_DIR) -n $(THREADS) -v --reruns $(RE_RUNS) --reruns-delay $(RE_RUN_DELAY)

CHAINS_FILES=\
	chains

# Targets
.PHONY: test clean lint init venv requirements generate_network_list test-all

clean:
	rm -rf *.pyc __pycache__/ **/__pycache__/

init: venv .create-venv requirements .install-pre-commit

generate_network_list:
	$(VENV)/bin/python ./scripts/generate_network_list.py

generate_dapp_list:
	$(VENV)/bin/python ./scripts/generate_dapps_list.py

generate_test_file:
	$(VENV)/bin/python ./scripts/update_test_data.py

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

test-all: test-nodes-availability test-networks-precision test-network-chain-id test-network-prefix test-eth-availability test-new-assets

test-nodes-availability:
	$(TEST_RUN) "./tests/test_nodes_availability.py"

test-networks-precision:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestPrecision"

test-network-chain-id:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestChainId"

test-network-prefix:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestNetworkPrefix"

test-eth-availability:
	$(TEST_RUN) "./tests/test_eth_nodes_availability.py"

test-new-assets:
	$(TEST_RUN) "./tests/test_check_new_assets.py"

allure:
	allure serve $(ALLURE_DIR)

pr-comment-creation:
	echo "## Changes for $(PR_ENV)" >> $(PR_FILE_NAME)
	$(VENV)/bin/python scripts/print_xcm_changes.py $(PR_ENV) >> $(PR_FILE_NAME)

# Variables
PYTHON := python
PYTHON_VERSION := 3.11
VENV ?= .venv
RUN_PYTHON := . $(VENV)/bin/activate && set -a && . .env && set +a && python

RE_RUNS = 2
RE_RUN_DELAY = 5
ALLURE_DIR = allure-results
TEST_RUN = $(RUN_PYTHON) -m pytest --rootdir . --alluredir=$(ALLURE_DIR) -n auto -v --reruns $(RE_RUNS) --reruns-delay $(RE_RUN_DELAY)
TEST_RUN_JUNIT = $(RUN_PYTHON) -m pytest --rootdir . --junit-xml=test-results.xml -n auto -v --reruns $(RE_RUNS) --reruns-delay $(RE_RUN_DELAY)

CHAINS_FILES=\
	chains

# Targets
.PHONY: test clean lint init venv requirements generate_network_list test-all

clean:
	rm -rf *.pyc __pycache__/ **/__pycache__/

init: venv .create-venv requirements .install-pre-commit generate-env-file

generate_type_files:
	$(RUN_PYTHON) ./scripts/create_type_file.py prod

generate_network_list:
	$(RUN_PYTHON) ./scripts/generate_network_list.py

generate_dapp_list:
	$(RUN_PYTHON) ./scripts/generate_dapps_list.py

generate_test_file:
	$(RUN_PYTHON) ./scripts/update_test_data.py

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

test-core:
	CHAINS_JSON_PATH=$(CHAINS_JSON_PATH) $(TEST_RUN_JUNIT) -m core

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
	XCM_PATH=$(XCM_PATH) CHAINS_PATH=$(CHAINS_PATH) $(RUN_PYTHON) scripts/print_xcm_changes.py $(PR_ENV) >> $(PR_FILE_NAME)

check-chains-file:
	$(VENV)/bin/pre-commit run --files chains/**/*.json

update-xcm-to-prod:
	$(RUN_PYTHON) xcm/update_to_prod.py

generate-env-file:
	@echo "Generating .env file..."
	@{ \
	echo "DEV_CHAINS_JSON_PATH=chains/$$(bash .github/get_actual_json_path.sh chains)/chains_dev.json"; \
	echo "CHAINS_JSON_PATH=chains/$$(bash .github/get_actual_json_path.sh chains)/chains.json"; \
	echo "PREVIOUS_DEV_CHAINS_JSON_PATH=chains/$$(bash .github/get_actual_json_path.sh chains 1)/chains_dev.json"; \
	echo "PREVIOUS_CHAINS_JSON_PATH=chains/$$(bash .github/get_actual_json_path.sh chains 1)/chains.json"; \
	echo "DEV_XCM_JSON_PATH=xcm/$$(bash .github/get_actual_json_path.sh xcm)/transfers_dev.json"; \
	echo "XCM_JSON_PATH=xcm/$$(bash .github/get_actual_json_path.sh xcm)/transfers.json"; \
	echo "PREVIOUS_DEV_XCM_JSON_PATH=xcm/$$(bash .github/get_actual_json_path.sh xcm 1)/transfers_dev.json"; \
	echo "PREVIOUS_XCM_JSON_PATH=xcm/$$(bash .github/get_actual_json_path.sh xcm 1)/transfers.json"; \
	} > .env
	@echo "Generated .env file with environment variables."

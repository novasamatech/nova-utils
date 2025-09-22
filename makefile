# =============================================================================
# Variables
# =============================================================================

# Python environment
PYTHON := python
PYTHON_VERSION := 3.10
VENV ?= .venv

# Test configuration
RE_RUNS := 2
RE_RUN_DELAY := 5
ALLURE_DIR := allure-results

# Test commands
TEST_RUN := PYTHONPATH=. $(VENV)/bin/python -m pytest --rootdir . --alluredir=$(ALLURE_DIR) -n auto -v --reruns $(RE_RUNS) --reruns-delay $(RE_RUN_DELAY)
TEST_RUN_JUNIT := PYTHONPATH=. $(VENV)/bin/python -m pytest --rootdir . --junit-xml=test-results.xml -n auto -v --reruns $(RE_RUNS) --reruns-delay $(RE_RUN_DELAY)

# Chain configuration
CHAINS_FILES := chains

# Python script runner
PYTHON_SCRIPT := PYTHONPATH=. $(VENV)/bin/python

# =============================================================================
# Help
# =============================================================================

.PHONY: help

help: ## Display this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  %-20s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)
	@echo ''

# =============================================================================
# Main targets
# =============================================================================

.PHONY: test clean lint init venv requirements generate_network_list test-all

## Clean build artifacts
clean:
	rm -rf *.pyc __pycache__/ **/__pycache__/

## Initialize development environment
init: venv .create-venv requirements .install-pre-commit

# =============================================================================
# Generation targets
# =============================================================================

## Generate type files
generate_type_files:
	$(PYTHON_SCRIPT) ./scripts/create_type_file.py

## Generate network list
generate_network_list:
	$(PYTHON_SCRIPT) ./scripts/generate_network_list.py

## Generate dapp list
generate_dapp_list:
	$(PYTHON_SCRIPT) ./scripts/generate_dapps_list.py

## Generate test file
generate_test_file:
	$(PYTHON_SCRIPT) ./scripts/update_test_data.py

# =============================================================================
# Environment setup targets
# =============================================================================

## Create virtual environment
venv:
	$(PYTHON) -m venv .venv

## Create and setup virtual environment
.create-venv:
	test -d $(VENV) || python$(PYTHON_VERSION) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry

## Install pre-commit hooks
.install-pre-commit:
	$(VENV)/bin/poetry run pre-commit install

## Install project dependencies
requirements:
	$(VENV)/bin/poetry install
	. .venv/bin/activate

# =============================================================================
# Test targets
# =============================================================================

## Run all tests
test-all: test-nodes-availability test-networks-precision test-network-chain-id \
	test-network-prefix test-eth-availability test-new-assets test-nodes-synced \
	test-calls-availability test-subquery-synced

## Run core tests
test-core:
	CHAINS_JSON_PATH=$(CHAINS_JSON_PATH) $(TEST_RUN_JUNIT) -m core

## Test nodes availability
test-nodes-availability:
	$(TEST_RUN) "./tests/test_nodes_availability.py"

## Test networks precision
test-networks-precision:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestPrecision"

## Test network chain ID
test-network-chain-id:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestChainId"

## Test network prefix
test-network-prefix:
	$(TEST_RUN) "./tests/test_network_parameters.py::TestNetworkPrefix"

## Test ETH nodes availability
test-eth-availability:
	$(TEST_RUN) "./tests/test_eth_nodes_availability.py"

## Test new assets
test-new-assets:
	$(TEST_RUN) "./tests/test_check_new_assets.py"

## Test nodes sync status
test-nodes-synced:
	$(TEST_RUN) "./tests/test_substrate_node_is_synced.py"

## Test RPC methods availability
test-calls-availability:
	$(TEST_RUN) "./tests/test_rpc_methods_availability.py"

## Test subquery sync status
test-subquery-synced:
	$(TEST_RUN) "./tests/test_subquery_is_synced.py"

# =============================================================================
# Reporting and documentation targets
# =============================================================================

## Serve Allure test reports
allure:
	allure serve $(ALLURE_DIR)

## Create PR comment with changes
pr-comment-creation:
	echo "## Changes for $(PR_ENV)" >> $(PR_FILE_NAME)
	XCM_PATH=$(XCM_PATH) CHAINS_PATH=$(CHAINS_PATH) $(VENV)/bin/python scripts/print_xcm_changes.py $(PR_ENV) >> $(PR_FILE_NAME)

# =============================================================================
# Chain management targets
# =============================================================================

## Check chains file format
check-chains-file:
	$(VENV)/bin/pre-commit run --files chains/**/*.json

## Update XCM configuration to production
update-xcm-to-prod:
	$(PYTHON_SCRIPT) xcm/update_to_prod.py

## Update Ledger networks
update-ledger-networks:
	$(PYTHON_SCRIPT) scripts/update_generic_ledger_app_networks.py

## Update chains preconfigured settings
update-chains-preconfigured:
	$(PYTHON_SCRIPT) scripts/polkadotjs_endpoints_to_preconfigured.py

## Check legacyAddressPrefix
check-legacy-address-prefix:
	CHAIN_ADDRESS_PREFIX_FILE_PATH=$(JSON_PATH) $(PYTHON_SCRIPT) scripts/update_chain_address_prefixes.py

# =============================================================================
# XCM configuration targets
# =============================================================================

## Update all XCM configurations
update-xcm-config: update-xcm-preliminary-data update-xcm-dynamic-config update-xcm-clean-up-legacy-config

## Update XCM preliminary data
update-xcm-preliminary-data:
	$(PYTHON_SCRIPT) scripts/xcm_transfers/sync_xcm_preliminary_data.py

## Update XCM dynamic configuration
update-xcm-dynamic-config:
	$(PYTHON_SCRIPT) scripts/xcm_transfers/find_working_directions.py

## Clean up legacy XCM configuration
update-xcm-clean-up-legacy-config:
	$(PYTHON_SCRIPT) scripts/xcm_transfers/clean_up_legacy_directions.py

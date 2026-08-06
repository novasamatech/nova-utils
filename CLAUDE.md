# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Static JSON configuration (networks, assets, XCM routes, dApps, banners, icons) served over raw GitHub to Nova Wallet clients. Most changes are data edits, not code. The Python in `scripts/` and `tests/` exists to generate, validate and integration-test that data.

## Versioned config directories

`chains/` and `xcm/` keep one directory per config version (`chains/v2`…`chains/v22`, `xcm/v2`…`xcm/v8`). Older versions stay frozen for older client releases.

- Edit only the latest version: **`chains/v22/`** and **`xcm/v8/`**. Do not backport into older `vNN` directories.
- `chains/chains.json`, `chains/chains_dev.json` and `xcm/transfers*.json` at the top level are legacy leftovers (untouched since 2023) — do not edit them.
- The latest version is hardcoded in two places that must be updated when a new version directory is added: `scripts/utils/chain_model.py` (`latest_config_version()`, overridable via the `CHAINS_VERSION` env var) and `scripts/xcm_transfers/config_setup.py` (`XCM_VERSION`, no env override).

## dev → prod flow

Configs come in dev/prod pairs: `chains_dev.json`/`chains.json`, `transfers_dev.json`/`transfers.json`, `dapps_dev.json`/`dapps.json`, `global/config_dev.json`/`global/config.json`.

Changes land in the `*_dev.json` file first, in their own PR, and are promoted to prod separately. Do not edit both halves of a pair in one change unless explicitly asked.

Promotion tools:
- chains: `chains/apply_dev_to_prod.py` — opens `chains.json`/`chains_dev.json` by bare filename, so run it from inside the version directory.
- xcm: `make update-xcm-to-prod` — needs `DEV_XCM_JSON_PATH`, `XCM_JSON_PATH`, `DEV_CHAINS_JSON_PATH`; prompts y/n per change.

## Generated files — never edit by hand

- `chains/README.md` ← `make generate_network_list`
- `dapps/README.md` ← `make generate_dapp_list`
- `chains/types/*.json` ← `make generate_type_files`
- `tests/data/xcm_data.json` ← `make generate_test_file`

## Commands

Run `make init` once to create `.venv`, install dependencies via poetry and install the pre-commit hook. Requires Python 3.10 — poetry pins `>=3.10,<3.11`; the `PYTHON_VERSION := 3.11` line in the Makefile is stale and has no effect.

- `make check-chains-file` — validate chains JSON through pre-commit. This is the check to run after editing config.
- `make help` — list all targets.
- There is no `make test` or `make lint` target, despite the `.PHONY` line naming them. Python is linted by the flake8 pre-commit hook, configured in `.flake8` to report only real defects (`E7,E9,F`) — formatting is deliberately not enforced.

Python scripts must run from the repo root with `PYTHONPATH=.` (the Makefile targets already do): `scripts/utils/work_with_data.py` resolves config paths against the current working directory.

Several scripts do their work at module level rather than under `if __name__ == "__main__"` — importing `scripts/update_test_data.py` or `scripts/xcm_transfers/clean_up_legacy_directions.py` rewrites config files as a side effect. Never import a script to inspect it; read it instead. A few scripts also import their siblings as top-level modules (`from utils.work_with_data import ...`), so they only resolve when run as a script from their own directory, not as `scripts.<name>`.

## Tests

Integration tests connect to live RPC nodes, take a long time, and are CI's job — `.github/workflows/run_integration_tests.yaml` runs them on any `chains/**` change. Do not run `make test-all` locally; use `make check-chains-file` for local verification.

For a single suite, targets like `make test-nodes-availability` exist. `CHAINS_JSON_PATH` selects the config file under test (defaults to the latest version's `chains.json`).

## Repo etiquette

- PRs target `master`.
- Branch names use a type prefix: `fix/`, `feat/`, and similar.
- CI runs pre-commit on every PR and auto-commits its fixes onto your branch, so run pre-commit before pushing to avoid surprise commits.

---
name: check-config
description: Validate changed JSON config files in this repo before opening a PR — checks that edits landed in the latest version directory, that the dev/prod pairing rule was respected, and runs the pre-commit hooks over the changed files. Use after editing anything under chains/, xcm/, dapps/, global/ or banners/.
---

Validate the config changes in the working tree the way CI will.

## 1. Collect the changed files

```bash
git diff --name-only master...HEAD; git diff --name-only; git diff --name-only --cached
```

Deduplicate, then keep the `.json` files under `chains/`, `xcm/`, `dapps/`, `global/`, and `banners/`. If there are none, say so and stop.

## 2. Check the version directory

Changes belong in the latest version directory only — `chains/v22/` and `xcm/v8/` (confirm the latest by listing `chains/` and `xcm/`; do not assume these numbers stay current).

Flag as a problem:
- edits to an older `vNN` directory
- edits to the legacy top-level `chains/chains.json`, `chains/chains_dev.json`, or `xcm/transfers*.json`

## 3. Check the dev/prod pairing

This repo promotes changes dev-first: a change should touch the `*_dev.json` half of a pair, not both halves in one PR.

If both `chains_dev.json` and `chains.json` (or the `transfers`/`dapps`/`global/config` equivalents) are modified, flag it and ask whether this is an intentional promotion PR. Editing only the prod half is also worth flagging — the dev config would then be behind.

## 4. Run the pre-commit hooks

```bash
.venv/bin/pre-commit run --files <changed files>
```

If `.venv` is missing, tell the user to run `make init` rather than installing anything yourself.

These hooks (`check-chains-json`, `check-dapps-json`, `check-json`, `end-of-file-fixer`, `trailing-whitespace`) rewrite files in place. If they modified anything, re-read the file and report what changed — CI runs the same hooks and auto-commits their output onto the branch, so it is better to land those fixes yourself.

## 5. Report

Give a short verdict per check: version directory, dev/prod pairing, pre-commit result. State clearly that integration tests were not run — they hit live RPC nodes and run in CI on `chains/**` changes.

---
name: promote-dev-to-prod
description: Promote config changes from the dev file to the prod file (chains or xcm). Interactive and writes to prod config — user-invoked only.
disable-model-invocation: true
---

Promote dev config into prod. Argument: `$ARGUMENTS` — `chains` or `xcm`. If empty, ask which one.

Both tools rewrite the prod config in place. Before running either, confirm the working tree is clean (`git status --short`) so the promotion diff is reviewable on its own, and confirm with the user which version directory is being promoted.

## chains

`chains/apply_dev_to_prod.py` opens `chains.json` and `chains_dev.json` by bare filename, so it must run from inside the version directory:

```bash
cd chains/v22 && PYTHONPATH=../.. ../../.venv/bin/python ../apply_dev_to_prod.py
```

Replace `v22` with the actual latest version directory — list `chains/` to confirm.

It copies every dev entry whose `chainId` already exists in prod, non-interactively. Chains present only in dev are not added. It rewrites the whole file with `indent=4`, so review the diff for unintended reformatting.

## xcm

```bash
DEV_XCM_JSON_PATH=xcm/v8/transfers_dev.json \
XCM_JSON_PATH=xcm/v8/transfers.json \
DEV_CHAINS_JSON_PATH=chains/v22/chains_dev.json \
make update-xcm-to-prod
```

Replace the version numbers with the actual latest directories. This script prompts `y/n` for each new chain, asset, destination and reserve change — relay each prompt to the user and pass their answer through; do not answer on their behalf.

## After promotion

1. Show `git diff --stat` and walk the user through the substantive changes.
2. Run the pre-commit hooks over the touched files (`.venv/bin/pre-commit run --files <files>`).
3. Remind the user that promotion goes in its own PR against `master`, separate from the dev change.

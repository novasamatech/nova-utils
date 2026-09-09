"""Check that every entry of a default assets config resolves in its sibling chains file.

A typo here does not fail loudly anywhere else: the clients simply do not find the asset and
silently start a wallet with a shorter curated list than intended, so it is worth a CI gate.

Run over one or more default_assets*.json paths:

    PYTHONPATH=. python3 scripts/check_default_assets.py chains/v22/default_assets.json
"""

import json
import sys
from pathlib import Path


def chains_file_for(default_assets_path: Path) -> Path:
    """default_assets_dev.json is checked against chains_dev.json, prod against prod."""
    suffix = "_dev" if default_assets_path.stem.endswith("_dev") else ""

    return default_assets_path.with_name(f"chains{suffix}.json")


def check(default_assets_path: Path) -> list[str]:
    chains_path = chains_file_for(default_assets_path)
    if not chains_path.exists():
        return [f"{default_assets_path}: no sibling {chains_path.name} to check against"]

    config = json.loads(default_assets_path.read_text())
    chains = json.loads(chains_path.read_text())

    assets_by_chain = {
        chain["chainId"]: {asset["assetId"] for asset in chain.get("assets", [])}
        for chain in chains
    }

    errors = []
    seen = set()

    for entry in config.get("defaultAssets", []):
        chain_id, asset_id = entry["chainId"], entry["assetId"]
        key = (chain_id, asset_id)

        if key in seen:
            errors.append(f"{default_assets_path}: duplicate entry {chain_id}/{asset_id}")
        seen.add(key)

        if chain_id not in assets_by_chain:
            errors.append(f"{default_assets_path}: unknown chain {chain_id} (not in {chains_path.name})")
        elif asset_id not in assets_by_chain[chain_id]:
            errors.append(f"{default_assets_path}: chain {chain_id} has no asset {asset_id}")

    if not config.get("defaultAssets"):
        errors.append(f"{default_assets_path}: the list is empty, which clients read as no curation at all")

    return errors


def main(paths: list[str]) -> int:
    errors = [error for path in paths for error in check(Path(path))]

    for error in errors:
        print(error, file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

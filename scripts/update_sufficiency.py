import os
import sys
from pathlib import Path
from typing import List

from scalecodec import ScaleBytes
from substrateinterface import SubstrateInterface
from substrateinterface.storage import StorageKey

from scripts.utils.chain_model import Chain
from scripts.utils.json_utils import load_json_file, save_json_file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", '../chains/v21/chains_dev.json'))


def update_sufficiency(chains, data):
    for chain in chains:
        process_single_chain(chain, data)


def get_statemine_assets(chain: Chain) -> List:
    return [asset for asset in chain.assets if asset.get("type") == "statemine"]


def process_single_chain(chain: Chain, chain_data):
    statemine_assets = get_statemine_assets(chain)
    if len(statemine_assets) == 0:
        return

    try:
        with chain.create_connection() as connection:
            if connection:
                handle_connection(connection, statemine_assets, chain_data)
    except Exception as e:
        print(f"Error creating connection for chain {chain.name}: {e}")


def create_asset_storage_key(connection: SubstrateInterface, asset: dict) -> StorageKey:
    pallet_name = asset["typeExtras"].get("palletName", "Assets")
    asset_id = parse_asset_id(asset["typeExtras"]["assetId"])
    return connection.create_storage_key(pallet_name, "Asset", [asset_id])


def parse_asset_id(assetId: str):
    if assetId.startswith("0x"):
        return ScaleBytes(assetId)
    else:
        return int(assetId)


def stringify_asset_id(assetIdArg):
    match assetIdArg:
        case ScaleBytes():
            return "0x" + assetIdArg.data.hex()
        case _:
            return str(assetIdArg)


def handle_connection(connection: SubstrateInterface, statemine_assets: List, chain_data):
    storage_keys = [create_asset_storage_key(connection, asset) for asset in statemine_assets]

    result = connection.query_multi(storage_keys)
    sufficiency_by_id = {stringify_asset_id(key.params[0]): scale.value["is_sufficient"] for key, scale in result}

    for asset_data in chain_data["assets"]:
        asset_data_id = asset_data.get("typeExtras", {}).get("assetId", None)
        if asset_data_id is None:
            continue

        is_sufficient = sufficiency_by_id[asset_data_id]

        if is_sufficient:
            asset_data["typeExtras"]["isSufficient"] = True
        else:
            asset_data["typeExtras"].pop("isSufficient", None)


def main():
    existing_data_dev = load_json_file(CHAINS_FILE_PATH_DEV)

    for idx, chain_data in enumerate(existing_data_dev):
        chain = Chain(chain_data)

        print(f"Processing {chain.name} ({idx} / {len(existing_data_dev)})")

        process_single_chain(chain, chain_data)

    save_json_file(CHAINS_FILE_PATH_DEV, existing_data_dev)


if __name__ == "__main__":
    main()

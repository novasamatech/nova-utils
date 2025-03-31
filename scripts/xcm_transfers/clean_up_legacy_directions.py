import dataclasses
import json
from typing import Set, Tuple

from scripts.utils.chain_model import ChainId, ChainAssetId
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles

DirectionId = Tuple[ChainId, ChainAssetId, ChainId]

def get_all_dynamic_directions(config: XCMConfigFiles) -> Set[DirectionId]:
    dynamic_file = get_data_from_file(config.xcm_dynamic_config)
    result = set()

    for chain_config in dynamic_file["chains"]:
        origin_chain_id = chain_config["chainId"]

        for origin_asset_config in chain_config["assets"]:
            origin_asset_id = origin_asset_config["assetId"]

            for transfer_config in origin_asset_config["xcmTransfers"]:
                destination_chain_id = transfer_config["chainId"]
                result.add((origin_chain_id, origin_asset_id, destination_chain_id))

    return result

def clean_up_legacy_directions(config: XCMConfigFiles, all_dynamic_directions: Set[DirectionId]) -> dict:
    all_legacy_directions = get_data_from_file(config.xcm_stable_legacy_config)

    result = all_legacy_directions.copy()
    result_chains = []

    for chain_config in all_legacy_directions["chains"]:
        origin_chain_id = chain_config["chainId"]

        result_chain_config = chain_config.copy()
        result_assets = []

        for origin_asset_config in chain_config["assets"]:
            origin_asset_id = origin_asset_config["assetId"]

            result_origin_asset_config = origin_asset_config.copy()
            result_transfers = []

            for transfer_config in origin_asset_config["xcmTransfers"]:
                destination_chain_id = transfer_config["destination"]["chainId"]

                direction_id = (origin_chain_id, origin_asset_id, destination_chain_id)

                if direction_id not in all_dynamic_directions:
                    result_transfers.append(transfer_config)

            if len(result_transfers) > 0:
                result_origin_asset_config["xcmTransfers"] = result_transfers
                result_assets.append(result_origin_asset_config)

        if len(result_assets) > 0:
            result_chain_config["assets"] = result_assets
            result_chains.append(result_chain_config)

    result["chains"] = result_chains
    return result


config_files = get_xcm_config_files()

all_dynamic_directions = get_all_dynamic_directions(config_files)

filtered_legacy_directions = clean_up_legacy_directions(config_files, all_dynamic_directions)

serialized = json.dumps(filtered_legacy_directions, indent=2)
write_data_to_file(config_files.xcm_legacy_config, serialized)
import json
from collections import defaultdict
from typing import List

from scripts.utils.chain_model import ChainAsset
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles
from scripts.xcm_transfers.xcm.dry_run.dry_run_transfer import TransferDryRunner
from scripts.xcm_transfers.xcm.graph.xcm_connectivity_graph import XcmChainConnectivityGraph
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_polkadot_xcm_registry

config_files = XCMConfigFiles(
    chains="../../chains/v21/chains_dev.json",
    xcm_legacy_config="../../xcm/v7/transfers_dev.json",
    xcm_additional_data="xcm_registry_additional_data.json",
    xcm_dynamic_config="../../xcm/v7/transfers_dynamic_dev.json",
)

registry = build_polkadot_xcm_registry(config_files)
connectivity_graph = XcmChainConnectivityGraph.construct_default(registry)
transfers_runner = TransferDryRunner(registry)

potential_directions = connectivity_graph.construct_potential_directions()

passed = []
failed = []

dynamic_config: dict = get_data_from_file(config_files.xcm_dynamic_config)

transfers_dict: dict[str, dict[int, List[ChainAsset]]] = defaultdict(lambda : defaultdict(list))

dynamic_config.pop("chains", None)

def save_config():
    transfers_in_config_format = []

    for chain_id, chain_transfers in transfers_dict.items():
        assets = []

        for asset_id, destinations in chain_transfers.items():
            asset_transfers = []

            for destination in destinations:
                destination_config = {
                    "chainId": destination.chain.chainId,
                    "assetId": destination.id,
                }
                asset_transfers.append(destination_config)

            asset_config = {
                "assetId": asset_id,
                "xcmTransfers": asset_transfers
            }
            assets.append(asset_config)

        chain_config = {
            "chainId": chain_id,
            "assets": assets
        }

        transfers_in_config_format.append(chain_config)

    dynamic_config["chains"] = transfers_in_config_format
    write_data_to_file(config_files.xcm_dynamic_config, json.dumps(dynamic_config, indent=2))


for idx, potential_direction in enumerate(potential_directions):
    try:
        print(f"{idx+1}/{len(potential_directions)}. Checking {potential_direction}")
        transfers_runner.dry_run_transfer(potential_direction)
        passed.append(potential_direction)

        chain_transfers = transfers_dict[potential_direction.origin_chain.chain.chainId]
        asset_transfers = chain_transfers[potential_direction.origin_asset.id]
        asset_transfers.append(potential_direction.destination_asset)
        save_config()

        print("Result: Success")
    except Exception as exception:
        failed.append(potential_direction)
        print(f"Result: Failure {exception}")



print(f"Passed ({len(passed)}): {passed}")
print(f"Failed ({len(failed)}): {failed}")

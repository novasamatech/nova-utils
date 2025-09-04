import json
from collections import defaultdict
from dataclasses import dataclass
from typing import List

from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.xcm.dry_run.dry_run_transfer import TransferDryRunner, DryRunTransferResult
from scripts.xcm_transfers.xcm.graph.xcm_connectivity_graph import XcmChainConnectivityGraph
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_xcm_registry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection

config_files = get_xcm_config_files()
registry = build_xcm_registry(config_files)
connectivity_graph = XcmChainConnectivityGraph.construct_default(registry)
transfers_runner = TransferDryRunner(registry)

potential_directions = connectivity_graph.construct_potential_directions()

passed = []
failed = []

dynamic_config: dict = get_data_from_file(config_files.xcm_dynamic_config)

@dataclass
class WorkingDirection:
    direction: XcmTransferDirection
    dry_run_result: DryRunTransferResult


transfers_dict: dict[str, dict[int, List[WorkingDirection]]] = defaultdict(lambda: defaultdict(list))

dynamic_config.pop("chains", None)


def save_config():
    transfers_in_config_format = []

    for chain_id, chain_transfers in transfers_dict.items():
        assets = []

        for asset_id, working_directions in chain_transfers.items():
            asset_transfers = []

            for working_direction in working_directions:
                destination_asset = working_direction.direction.destination_asset

                destination_config = {
                    "chainId": destination_asset.chain.chainId,
                    "assetId": destination_asset.id,
                }

                if working_direction.dry_run_result.paid_delivery_fee:
                    destination_config["hasDeliveryFee"] = True

                if working_direction.dry_run_result.supports_xcm_execute:
                    destination_config["supportsXcmExecute"] = True

                # TODO we keep usesTeleport solely for compatibility purposes
                # Remove it when migrating to v8
                if working_direction.dry_run_result.uses_teleport:
                    destination_config["usesTeleport"] = True

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
        print(f"{idx + 1}/{len(potential_directions)}. Checking {potential_direction}")
        result = transfers_runner.dry_run_transfer(potential_direction)
        passed.append(potential_direction)

        working_direction = WorkingDirection(potential_direction, result)

        chain_transfers = transfers_dict[potential_direction.origin_chain.chain.chainId]
        asset_transfers = chain_transfers[potential_direction.origin_asset.id]
        asset_transfers.append(working_direction)
        save_config()

        print("Result: Success")
    except Exception as exception:
        failed.append(potential_direction)
        print(f"Result: Failure {exception}")

print(f"Passed ({len(passed)}): {passed}")
print(f"Failed ({len(failed)}): {failed}")

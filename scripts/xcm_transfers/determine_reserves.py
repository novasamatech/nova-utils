import json
from typing import List

from dry_run_sample import dry_run_sample
from scripts.utils.chain_model import ChainAsset
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.utils.log import disable_debug_log
from scripts.xcm_transfers.xcm.graph.xcm_connectivity_graph import XcmChainConnectivityGraph
from scripts.xcm_transfers.xcm.registry.transfer_type import Teleport
from scripts.xcm_transfers.xcm.registry.xcm_chain import XcmChain
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_xcm_registry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection

RELAY_CHAIN_ID = "b0a8d493285c2df73290dfb7e61f870f17b41801197a149ca93654499ea3dafe"
ASSET_HUB_RESERVE = "KSM-Statemine"
RELAY_RESERVE = None # To avoid redundant KSM entries in overrides


def is_ksm(asset: ChainAsset) -> bool:
    return "KSM" == asset.unified_symbol()

def is_regular_para_and_relay(origin: XcmChain, dest: XcmChain) -> bool:
    return (origin.is_relay() and dest.is_regular_parachain()) or (origin.is_regular_parachain() and dest.is_relay())

def run_dry_run(origin_chain: str, dest_chain: str, origin_token: str, dest_token: str) -> bool:
    """Run dry_run_sample.py as subprocess and return True if successful."""
    try:
        dry_run_sample(origin_chain, dest_chain, origin_token, dest_token)
    except Exception as e:
        print(f"  Error running dry run: {e}")
        return False

    return True


def update_reserve_override(config_data: dict, direction: XcmTransferDirection, reserve_id: str | None) -> bool:
    """Update the reserveIdOverrides in the config data."""
    origin_chain_id = direction.origin_chain.chain.chainId
    origin_asset_id = direction.origin_asset.id

    if "reserveIdOverrides" not in config_data:
        config_data["reserveIdOverrides"] = {}
    reserves = config_data["reserveIdOverrides"]

    if origin_chain_id not in reserves:
        reserves[origin_chain_id] = {}
    chain_reserves = reserves[origin_chain_id]

    if reserve_id is not None:
        chain_reserves[str(origin_asset_id)] = reserve_id
    else:
        if str(origin_asset_id) in chain_reserves:
            del chain_reserves[str(origin_asset_id)]

            if len(chain_reserves) == 0:
                del reserves[origin_chain_id]

success = []
failure = []

def main():
    print("Loading configuration...")
    config_files = get_xcm_config_files()
    registry = build_xcm_registry(config_files)

    # Load dynamic transfers config
    dynamic_config: dict = get_data_from_file(config_files.xcm_dynamic_config)

    print("Building list of KSM directions from dynamic config...")
    ksm_directions: List[XcmTransferDirection] = []

    connectivity_graph = XcmChainConnectivityGraph.construct_default(registry)
    potential_directions = connectivity_graph.construct_potential_directions()

    for direction in potential_directions:
        transfer_type = registry.determine_transfer_type(direction.origin_chain, direction.destination_chain, direction.origin_asset)


        if is_ksm(direction.origin_asset) and not isinstance(transfer_type, Teleport) and not is_regular_para_and_relay(direction.origin_chain, direction.destination_chain):
            if direction.origin_chain.chain.name == "Kusama People" and len(ksm_directions) == 0:
                ksm_directions.append(direction)

    print(f"\nFound {len(ksm_directions)} KSM directions to test: {ksm_directions}\n")

    # Test each direction
    for idx, direction in enumerate(ksm_directions):
        origin_chain, dest_chain, origin_token, dest_token = direction.origin_chain, direction.destination_chain, direction.origin_asset, direction.destination_asset

        print(f"\n[{idx + 1}/{len(ksm_directions)}] Testing: {origin_chain.chain.name} -> {dest_chain.chain.name}")

        if direction.origin_chain.parachain_id is None:
            # If relay is the origin
            first_try = RELAY_RESERVE
            second_try = ASSET_HUB_RESERVE
        else:
            first_try = ASSET_HUB_RESERVE
            second_try = RELAY_RESERVE

        print(f"  Setting reserve to {first_try}...")
        update_reserve_override(dynamic_config, direction, first_try)
        write_data_to_file(config_files.xcm_dynamic_config, json.dumps(dynamic_config, indent=2))

        print("  Running dry run...")
        if run_dry_run(origin_chain.chain.name, dest_chain.chain.name, origin_token.symbol, dest_token.symbol):
            print(f"  ✓ Success with {first_try}")
            success.append(direction)
            continue

        # If failed, try with KSM
        print(f"  Failed with {first_try}, trying {second_try}...")
        update_reserve_override(dynamic_config, direction, second_try)
        write_data_to_file(config_files.xcm_dynamic_config, json.dumps(dynamic_config, indent=2))

        print("  Running dry run...")
        if run_dry_run(origin_chain.chain.name, dest_chain.chain.name, origin_token.symbol, dest_token.symbol):
            print(f"  ✓ Success with {second_try}")
            success.append(direction)
        else:
            print(f"  ✗ Failed with both reserves")
            failure.append(direction)

    print("\n" + "="*80)
    print("Reserve determination complete!")
    print("Success: ", success)
    print("Failure: ", failure)
    print(f"Results saved to: {config_files.xcm_dynamic_config}")


if __name__ == "__main__":
    disable_debug_log()
    main()

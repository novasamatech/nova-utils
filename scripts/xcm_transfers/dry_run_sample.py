from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.utils.log import enable_debug_log
from scripts.xcm_transfers.xcm.dry_run.dry_run_transfer import TransferDryRunner
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_xcm_registry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection

def dry_run_sample(
        origin_chain_name: str,
        destination_chain_name: str,
        origin_token: str,
        destination_token: str,
):
    config_files = get_xcm_config_files()
    registry = build_xcm_registry(config_files)

    origin_chain = registry.get_chain_by_name(origin_chain_name)
    destination_chain = registry.get_chain_by_name(destination_chain_name)
    origin_asset = origin_chain.chain.get_asset_by_symbol(origin_token)
    destination_asset = destination_chain.chain.get_asset_by_symbol(destination_token)

    direction = XcmTransferDirection(origin_chain, origin_asset, destination_chain, destination_asset)

    runner = TransferDryRunner(registry)
    runner.dry_run_transfer(direction)
    print(direction)

if __name__ == "__main__":
    origin_chain_name = "Kusama Relay"
    destination_chain_name = "Encointer"
    origin_token = "KSM"
    destination_token = "KSM"

    enable_debug_log()

    dry_run_sample(origin_chain_name, destination_chain_name, origin_token, destination_token)

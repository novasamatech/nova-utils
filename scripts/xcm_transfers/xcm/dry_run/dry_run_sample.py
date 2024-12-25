from scripts.xcm_transfers.utils.log import enable_debug_log
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles
from scripts.xcm_transfers.xcm.dry_run.dry_run_transfer import TransferDryRunner
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_polkadot_xcm_registry
from scripts.xcm_transfers.xcm.xcm_transfer_direction import XcmTransferDirection

config_files = XCMConfigFiles(
    chains="../../../../chains/v21/chains_dev.json",
    xcm_legacy_config="../../../../xcm/v6/transfers_dev.json",
    xcm_additional_data="../../xcm_registry_additional_data.json",
    xcm_dynamic_config="../../../../xcm/v7/transfers_dynamic_dev.json",
)

registry = build_polkadot_xcm_registry(config_files)

origin_chain_name = "Polkadot"
destination_chain_name = "Bifrost Polkadot"
origin_token = "DOT"
destination_token = "DOT"

origin_chain = registry.get_chain_by_name(origin_chain_name)
destination_chain = registry.get_chain_by_name(destination_chain_name)
origin_asset = origin_chain.chain.get_asset_by_symbol(origin_token)
destination_asset = destination_chain.chain.get_asset_by_symbol(destination_token)

direction = XcmTransferDirection(origin_chain, origin_asset, destination_chain, destination_asset)

enable_debug_log()

runner = TransferDryRunner(registry)
runner.dry_run_transfer(direction)

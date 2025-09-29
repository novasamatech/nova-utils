import json

from scripts.utils.chain_model import Chain, ChainAsset
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.utils.log import warn_log

config_files = get_xcm_config_files()
chains_file = get_data_from_file(config_files.chains)
chains = [Chain(it) for it in chains_file]
chains_by_id = {chain.chainId:chain for chain in chains}

general_config = get_data_from_file(config_files.general_config)
asset_locations_config = general_config["assets"]["assetsLocation"]

for (reserve_id, asset_config) in asset_locations_config.items():
    normalized = ChainAsset.unify_symbol(reserve_id).removesuffix("-Statemine").removesuffix("-Westmint").removesuffix("-Polkadot").removesuffix("-Statemint")
    chain = chains_by_id[asset_config["chainId"]]
    asset = chain.get_asset_by_symbol_or_null(normalized)

    if not asset:
        warn_log("Failed to find asset with symbol {}".format(normalized))
    else:
        asset_config["assetId"] = asset.id

write_data_to_file(config_files.general_config, json.dumps(general_config, indent=2))
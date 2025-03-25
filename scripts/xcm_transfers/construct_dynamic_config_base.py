import json
from collections import defaultdict

from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.config_setup import get_xcm_config_files
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_xcm_registry

config_files = get_xcm_config_files()
config = get_data_from_file(config_files.xcm_legacy_config)

new_config = {"assetsLocation": {}, "reserveIdOverrides": defaultdict(dict)}

for reserve_id, reserve_config in config["assetsLocation"].items():
    reserve_config.pop("reserveFee", None)
    new_config["assetsLocation"][reserve_id] = reserve_config

reserve_overrides = {}

# Step 1 - write all present destinations as overrides so we can construct XcmRegistry
for xcm_chain_config in config["chains"]:
    origin_chain_id = xcm_chain_config["chainId"]

    for origin_asset_config in xcm_chain_config["assets"]:
        origin_asset_id = origin_asset_config["assetId"]
        origin_asset_location = origin_asset_config.get("assetLocation", None)
        if origin_asset_location is not None:
            new_config["reserveIdOverrides"][origin_chain_id][origin_asset_id] = origin_asset_location

# Save temp result of Step 1
write_data_to_file(config_files.xcm_dynamic_config, json.dumps(new_config, indent=2))

# Step 2 - remove redundant overrides by comparing actual reserve with default one
registry = build_xcm_registry(config_files)
reserve_overrides = registry.reserves.dump_overrides()

for chain_id, chain_overrides in list(reserve_overrides.items()):
    chain = registry.get_chain_or_none(chain_id)

    if chain is None:
        del reserve_overrides[chain_id]
        continue

    for asset_id, reserve_id in list(chain_overrides.items()):
        asset = chain.chain.get_asset_by_id(asset_id)
        if asset.symbol == reserve_id:
            del chain_overrides[asset_id]

    if len(chain_overrides) == 0:
        del reserve_overrides[chain_id]

new_config["reserveIdOverrides"] = reserve_overrides

write_data_to_file(config_files.xcm_dynamic_config, json.dumps(new_config, indent=2))

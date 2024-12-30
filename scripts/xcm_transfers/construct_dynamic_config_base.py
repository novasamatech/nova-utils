import json

from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles
from scripts.xcm_transfers.xcm.registry.xcm_registry_builder import build_polkadot_xcm_registry

config_files = XCMConfigFiles(
    chains="../../chains/v21/chains_dev.json",
    xcm_legacy_config="../../xcm/v7/transfers_dev.json",
    xcm_additional_data="xcm_registry_additional_data.json",
    xcm_dynamic_config="../../xcm/v7/transfers_dynamic_dev.json",
)

registry = build_polkadot_xcm_registry(config_files)

config = get_data_from_file(config_files.xcm_legacy_config)

new_config = {"assetsLocation": {}}

for reserve_id, reserve_config in config["assetsLocation"].items():
    reserve_config.pop("reserveFee", None)
    new_config["assetsLocation"][reserve_id] = reserve_config

reserve_overrides = registry.reserves.dump_overrides()

# Remove redundant declarations from overrides
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

write_data_to_file("../../xcm/v7/transfers_dynamic_dev.json", json.dumps(new_config, indent=2))

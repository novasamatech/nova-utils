import os

from scripts.utils.chain_model import Chain
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles

def get_xcm_config_files() -> XCMConfigFiles:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
    CHAINS_VERSION = Chain.latest_config_version()

    if ENVIRONMENT == "PROD":
        print("Running in production mode")
        return XCMConfigFiles(
            chains=f"chains/{CHAINS_VERSION}/chains.json",
            xcm_legacy_config=f"xcm/v7/transfers.json",
            xcm_stable_legacy_config=f"xcm/v6/transfers.json",
            xcm_additional_data="scripts/xcm_transfers/xcm_registry_additional_data.json",
            xcm_dynamic_config=f"xcm/v7/transfers_dynamic.json",
        )
    else:
        print("Running in development mode")
        return XCMConfigFiles(
            chains=f"chains/{CHAINS_VERSION}/chains_dev.json",
            xcm_legacy_config=f"xcm/v7/transfers_dev.json",
            xcm_stable_legacy_config=f"xcm/v6/transfers_dev.json",
            xcm_additional_data="scripts/xcm_transfers/xcm_registry_additional_data.json",
            xcm_dynamic_config=f"xcm/v7/transfers_dynamic_dev.json",
        )

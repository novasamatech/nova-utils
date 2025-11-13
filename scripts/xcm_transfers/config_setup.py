import argparse
import os
from scripts.xcm_transfers.utils.xcm_config_files import XCMConfigFiles

def get_xcm_config_files() -> XCMConfigFiles:
    parser = argparse.ArgumentParser(description="Process the 'production' argument")
    parser.add_argument('--production', action='store_true', default=False,
                        help="Specify if the environment is production")
    args = parser.parse_args()

    if args.production:
        print("Running in production mode")
        return XCMConfigFiles(
            chains="../../chains/v21/chains.json",
            xcm_legacy_config="../../xcm/v7/transfers.json",
            xcm_stable_legacy_config="../../xcm/v6/transfers.json",
            xcm_additional_data="xcm_registry_additional_data.json",
            xcm_dynamic_config="../../xcm/v7/transfers_dynamic.json",
        )
    else:
        print("Running in development mode")
        return XCMConfigFiles(
            chains="../../chains/v21/chains_dev.json",
            xcm_legacy_config="../../xcm/v7/transfers_dev.json",
            xcm_stable_legacy_config="../../xcm/v6/transfers_dev.json",
            xcm_additional_data="xcm_registry_additional_data.json",
            xcm_dynamic_config="../../xcm/v7/transfers_dynamic_dev.json",
        )

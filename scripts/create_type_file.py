#!/usr/bin/env python3
"""That script is used for creating type files in chains/**/types/ directory."""

from pathlib import Path
import os
import sys
import json

# add parent directory to evade import problems across different modules
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from scripts.utils.metadata_interaction import get_metadata_param, get_properties
from scripts.utils.work_with_data import get_data_from_file, write_data_to_file
from scripts.utils.substrate_interface import create_connection_by_url
from scripts.utils.chain_model import Chain


def compare_type_files_for_all_networks(chains_file):
    """This function compare type files with runtime metadata for all networks provided by chain_files
    all changes will be written in particular type file.

    Args:
        chains_file (obj): Json object with all chains from chains/**/chains*.json
    """

    index = 0
    for chain in chains_file:
        index += 1
        print(
            f"Generating has started for: {chain['name']}. {index}/{len(chains_file)}")
        chain_options = chain.get('options')
        skip_options = {'ethereumBased', 'noSubstrateRuntime'}

        if chain_options is not None:
            if skip_options.intersection(chain_options):
                # TODO need to implement creation type file for EVM networks
                print(f"Temporary can't generate type files for EVM networks, {chain['name']} was skipped")
                continue

        actual_types_file_path = chain['types']['url'].split('master/')[1]
        actual_types_file = get_data_from_file(actual_types_file_path)
        chain_object = Chain(chain)
        chain_object.create_connection()

        types_from_runtime = get_metadata_param(chain_object.substrate)
        if types_from_runtime is None:
            continue
        actual_runtime_dispatch_info = actual_types_file['types'].get('RuntimeDispatchInfo')
        if actual_runtime_dispatch_info:
            types_from_runtime.__dict__['types']['RuntimeDispatchInfo'] = actual_runtime_dispatch_info
        write_data_to_file(actual_types_file_path,
                           json.dumps(types_from_runtime.__dict__, indent=2))
        chain_object.close_substrate_connection()
        print(f"Generating has successfuly finished: {chain['name']} 🎉")


def create_new_type_file(url):
    substrate = create_connection_by_url(url)
    json_metadata = get_metadata_param(substrate)
    json_property = get_properties(substrate)
    write_data_to_file(
        json_property.name +
        "_types.json", json.dumps(json_metadata.__dict__, indent=2)
    )
    write_data_to_file(
        json_property.name +
        "_property.json", json.dumps(json_property.__dict__, indent=2)
    )
    print("Success! \ncheck " + json_property.name + "_* files")


def main(argv):
    """Main function for create or update type files.

    Args:
        argv (str): ["dev", "prod", None]
            if "dev" - type files will be created for all networks from chains/**/chains_dev.json
            if "prod" - type files will be created for all networks from chains/**/chains.json
            if None - type file will be created for network provided by url
    """

    if 'dev' in argv:
        chains_path = os.getenv("DEV_CHAINS_JSON_PATH")
        chains_file = get_data_from_file(chains_path)
        compare_type_files_for_all_networks(chains_file)
    elif 'prod' in argv:
        chains_path = os.getenv("CHAINS_JSON_PATH")
        chains_file = get_data_from_file(chains_path)
        compare_type_files_for_all_networks(chains_file)
    else:
        user_input = input(
            "Enter a url for collect data, url should start with wss:\n")
        url = user_input.strip()
        print("Data collecting in process and will write to file in current directory.")
        create_new_type_file(url)


if __name__ == "__main__":
    main(sys.argv[1:])

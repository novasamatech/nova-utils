import os
import sys
import json

from utils.metadata_interaction import get_metadata_param, get_properties, write_data_to_file
from utils.network_interaction import create_connection_by_url
from print_xcm_changes import get_data_from_file
from utils.chain_model import Chain


def compare_type_files_for_all_networks(chains_file):
    index = 0
    for chain in chains_file:
        index += 1
        print(
            f"Generating has started for: {chain['name']}. {index}/{len(chains_file)}")
        if chain['name'] in ['Moonbeam', 'Moonriver', 'Moonbase']:
            # TODO need to implement creation type file for EVM networks
            print(
                f"Temporary can't generate type files for EVM networks, {chain['name']} was skipped")
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
                           json.dumps(types_from_runtime.__dict__, indent=4))
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
    if 'dev' in argv:
        url = "wss://quartz.api.onfinality.io/public-ws"
        create_new_type_file(url)
    elif 'prod' in argv:
        chains_path = os.getenv("CHAINS_JSON_PATH", "chains/v6/chains.json")
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

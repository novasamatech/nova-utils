import json
import os
import requests
from pathlib import Path
from collections import OrderedDict

CHAINS_FILE_PATH = Path(os.getenv("CHAINS_JSON_PATH", 'chains/v20/chains.json'))
CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))
MAPPING_FILE_PATH = Path('scripts/data/check_metadata_hash_mapping.json')
FETCH_METADATA_URL = 'https://dashboards.data.paritytech.io/data/metadata000000000000.jsonl'

def fetch_metadata():
    response = requests.get(FETCH_METADATA_URL)
    response.raise_for_status()
    return [json.loads(line) for line in response.text.splitlines()]

def find_networks_with_check_metadata_hash(metadata):
    return [
        {
            'name': item['chain'].lower(),
            'chain': item['relay_chain']
        }
        for item in metadata if item.get('CheckMetadataHash') == 'yes'
    ]

def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    return []

def update_networks_with_mapping(networks, mapping_data):
    updated_networks = []
    for new_network in networks:
        existing_network = next((network for network in mapping_data if network['name'] == new_network['name']), None)
        if existing_network:
            existing_network.update(new_network)
        else:
            new_network['chainId'] = ''
            updated_networks.append(new_network)
    mapping_data.extend(updated_networks)

    with open(MAPPING_FILE_PATH, 'w') as f:
        json.dump(mapping_data, f, indent=4)

def find_new_networks(existing_data, networks):
    existing_networks = {
        network['name'].lower().replace(' ', '')
        for network in existing_data
        if 'additional' in network and 'supportsGenericLedgerApp' in network['additional']
    }
    return [network for network in networks if network['name'] not in existing_networks]

def update_existing_data_with_new_networks(existing_data, new_networks):
    for new_network in new_networks:
        if not new_network['chainId']:
            print(f"Skipping network with no chainId: {new_network}")
            continue

        matching_network = next((network for network in existing_data if network['chainId'] == new_network['chainId']), None)
        if matching_network:
            if 'additional' not in matching_network:
                matching_network['additional'] = {}
            matching_network['additional']['supportsGenericLedgerApp'] = True

def process_file(chains_file_path):
    metadata = fetch_metadata()
    networks = find_networks_with_check_metadata_hash(metadata)

    existing_data = load_json_file(chains_file_path)
    mapping_data = load_json_file(MAPPING_FILE_PATH)

    if mapping_data:
        update_networks_with_mapping(networks, mapping_data)

    new_networks = find_new_networks(existing_data, mapping_data)

    if new_networks:
        update_existing_data_with_new_networks(existing_data, new_networks)
        with open(chains_file_path, 'w') as f:
            json.dump(existing_data, f, indent=4)

def main():
    process_file(CHAINS_FILE_PATH)
    process_file(CHAINS_FILE_PATH_DEV)

if __name__ == "__main__":
    main()

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from tests.data.setting_data import get_substrate_chains

CHAINS_FILE_PATH = Path(os.getenv("CHAINS_JSON_PATH", 'chains/v20/chains.json'))
CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))

def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')

def update_existing_data_with_new_networks(existing_data, new_networks):
    for new_network in new_networks:
        existing_network = next((network for network in existing_data if network['chainId'] == new_network['chainId']), None)
        if existing_network:
            if 'additional' not in existing_network:
                existing_network['additional'] = {}
            existing_network['additional']['supportsGenericLedgerApp'] = True

def check_metadata_exists(connection):
    try:
        metadata = connection.get_block_metadata()
        if metadata:
            for version in ['V14', 'V15']:
                if version in metadata.value_serialized[1]:
                    extrinsic = metadata.value_serialized[1][version]['extrinsic']
                    if 'signed_extensions' in extrinsic and len(extrinsic['signed_extensions']) > 9:
                        return True
        return False
    except:
        return False

def process_files(chains_file_path, chains_file_path_dev):
    existing_data = load_json_file(chains_file_path)
    existing_data_dev = load_json_file(chains_file_path_dev)

    substrate_chains = get_substrate_chains()
    new_networks = []

    for chain in substrate_chains:
        print(chain.name)
        try:
            connection = chain.create_connection()
            if connection and check_metadata_exists(connection):
                new_networks.append({
                    'name': chain.name,
                    'chainId': chain.chainId
                })
            chain.close_substrate_connection()
        except Exception as e:
            print(f"Error creating connection for chain {chain.name}: {e}")

    update_existing_data_with_new_networks(existing_data, new_networks)
    update_existing_data_with_new_networks(existing_data_dev, new_networks)

    save_json_file(chains_file_path, existing_data)
    save_json_file(chains_file_path_dev, existing_data_dev)

if __name__ == "__main__":
    process_files(CHAINS_FILE_PATH, CHAINS_FILE_PATH_DEV)

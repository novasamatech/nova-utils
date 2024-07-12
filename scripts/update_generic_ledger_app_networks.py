import json
import os
import sys
from pathlib import Path
from substrateinterface import SubstrateInterface

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.data.setting_data import get_substrate_chains

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
            existing_network.setdefault('additional', {})['supportsGenericLedgerApp'] = True

def check_metadata_hash_exist(connection: SubstrateInterface):
    try:
        metadata = connection.get_block_metadata()
        if metadata:
            for version in ['V15']:
                extrinsic = metadata.value_serialized[1].get(version, {}).get('extrinsic', {})
                signed_extensions = extrinsic.get('signed_extensions', [])
                if any(extension.get('identifier') == 'CheckMetadataHash' for extension in signed_extensions):
                    return True
        return False
    except:
        return False

def main():
    existing_data_dev = load_json_file(CHAINS_FILE_PATH_DEV)

    substrate_chains = get_substrate_chains()
    networks_with_metadata_hash = []

    for chain in substrate_chains:
        print(f'Checking {chain.name}')
        try:
            connection = chain.create_connection()
            if connection and check_metadata_hash_exist(connection):
                networks_with_metadata_hash.append({
                    'name': chain.name,
                    'chainId': chain.chainId
                })
            chain.close_substrate_connection()
        except Exception as e:
            print(f"Error creating connection for chain {chain.name}: {e}")

    update_existing_data_with_new_networks(existing_data_dev, networks_with_metadata_hash)

    save_json_file(CHAINS_FILE_PATH_DEV, existing_data_dev)

if __name__ == "__main__":
    main()

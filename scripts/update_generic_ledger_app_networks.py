import json
import os
import sys
from pathlib import Path
from substrateinterface import SubstrateInterface
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.data.setting_data import get_substrate_chains

CHAINS_FILE_PATH_DEV = Path(os.getenv("DEV_CHAINS_JSON_PATH", 'chains/v20/chains_dev.json'))

class BlacklistedChains(Enum):
    NOVASAMA_TESTNET = '3dbb473ae9b2b77ecf077c03546f0f8670c020e453dddb457da155e6cc7cba42'
    KUSAMA_PEOPLE = 'c1af4cb4eb3918e5db15086c0cc5ec17fb334f728b7c65dd44bfe1e174ff8b3f' # TODO: Remove when Kusama People is supported


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
        existing_network = find_existing_network(
            existing_data, new_network['chainId'])
        if existing_network:
            update_network_data(existing_network)


def find_existing_network(existing_data, chain_id):
    return next((network for network in existing_data if network['chainId'] == chain_id), None)


def update_network_data(network):
    additional = network.setdefault('additional', {})
    additional['supportsGenericLedgerApp'] = True
    additional.pop('disabledCheckMetadataHash', None)


def remove_generic_ledger_app_support(existing_data, chain_id):
    existing_network = find_existing_network(existing_data, chain_id)
    if existing_network:
        additional = existing_network.get('additional', {})
        if 'supportsGenericLedgerApp' in additional:
            del additional['supportsGenericLedgerApp']
            print(f"Removed supportsGenericLedgerApp for chain {chain_id}")


def check_metadata_hash_exist(connection: SubstrateInterface) -> bool:
    try:
        metadata = connection.get_block_metadata()
        if not metadata:
            return False

        extrinsic = metadata.value_serialized[1].get(
            'V14', {}).get('extrinsic', {})
        signed_extensions = extrinsic.get('signed_extensions', [])

        if not any(extension.get('identifier') == 'CheckMetadataHash' for extension in signed_extensions):
            return False

        versions_result = connection.rpc_request(
            "state_call", ["Metadata_metadata_versions", "0x"])
        if not versions_result or 'result' not in versions_result:
            return False

        versions = connection.decode_scale(
            "vec<u32>", versions_result['result'])
        return 15 in versions

    except Exception as e:
        print(
            f"Error checking metadata hash for chain {connection.chain}: {e}")
        return False


def process_chains(chains, existing_data):
    networks_with_metadata_hash = []
    for chain in chains:
        if chain.chainId not in [c.value for c in BlacklistedChains]:
            print(f'Checking {chain.name}')
            process_single_chain(chain, existing_data, networks_with_metadata_hash)
        else:
            print(f'Skipping blacklisted chain: {chain.name} (chainId: {chain.chainId})')
    return networks_with_metadata_hash


def process_single_chain(chain, existing_data, networks_with_metadata_hash):
    try:
        with chain.create_connection() as connection:
            if connection:
                handle_connection(connection, chain,existing_data, networks_with_metadata_hash)
    except Exception as e:
        print(f"Error creating connection for chain {chain.name}: {e}")


def handle_connection(connection, chain, existing_data, networks_with_metadata_hash):
    has_metadata_hash = check_metadata_hash_exist(connection)
    if has_metadata_hash:
        networks_with_metadata_hash.append({
            'name': chain.name,
            'chainId': chain.chainId
        })
    else:
        remove_generic_ledger_app_support(existing_data, chain.chainId)


def main():
    existing_data_dev = load_json_file(CHAINS_FILE_PATH_DEV)
    substrate_chains = get_substrate_chains(path=CHAINS_FILE_PATH_DEV.__str__())
    networks_with_metadata_hash = process_chains(substrate_chains, existing_data_dev)
    update_existing_data_with_new_networks(existing_data_dev, networks_with_metadata_hash)
    save_json_file(CHAINS_FILE_PATH_DEV, existing_data_dev)


if __name__ == "__main__":
    main()

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.chain_model import Chain
from scripts.utils.json_utils import load_json_file, save_json_file
from tests.data.setting_data import get_substrate_chains

CHAINS_FILE_PATH_DEV = Path(os.getenv("CHAIN_ADDRESS_PREFIX_FILE_PATH", 'chains/v21/chains_dev.json'))

def update_network_address_prefix(network, new_prefix):
    if network['legacyAddressPrefix'] is not None:
        return False

    current_prefix = network['addressPrefix']
    if current_prefix != new_prefix:
        if current_prefix is not None and 'legacyAddressPrefix' not in network:
            network['legacyAddressPrefix'] = current_prefix

        network['addressPrefix'] = new_prefix
        print(f"Updated address prefix for chain {network.get('name')}: {current_prefix} -> {new_prefix}")
        return True
    return False

def process_single_chain(chain: Chain, existing_data):
    try:
        print(f'Checking {chain.name}')
        network = next((network for network in existing_data if network['chainId'] == chain.chainId), None)
        if not network:
            return False

        with chain.create_connection() as connection:
            if connection:
                properties = connection.properties
                if properties and 'ss58Format' in properties:
                    return update_network_address_prefix(network, properties['ss58Format'])
        return False
    except Exception as e:
        print(f"Error processing chain {chain.name}: {e}")
        return False

def process_chains_parallel(chains, existing_data, max_workers=5):
    updated = False
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chain = {executor.submit(process_single_chain, chain, existing_data): chain for chain in chains}
        for future in as_completed(future_to_chain):
            if future.result():
                updated = True
    return updated

def main():
    existing_data_dev = load_json_file(CHAINS_FILE_PATH_DEV)
    substrate_chains = get_substrate_chains(path=str(CHAINS_FILE_PATH_DEV))

    updated = process_chains_parallel(substrate_chains, existing_data_dev)

    if updated:
        save_json_file(CHAINS_FILE_PATH_DEV, existing_data_dev)
        print("Chain address prefixes updated successfully")
    else:
        print("No changes were made to address prefixes")

if __name__ == "__main__":
    main()

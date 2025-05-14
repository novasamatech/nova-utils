"""
Script to update address prefixes in the chains configuration file.

This script connects to Substrate chains, retrieves their SS58 address format from the properties,
and updates the corresponding chain configuration in the CHAINS_FILE_PATH file.
It preserves the old address prefix as legacyAddressPrefix when making updates.
"""

import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.chain_model import Chain
from scripts.utils.json_utils import load_json_file, save_json_file
from tests.data.setting_data import get_substrate_chains

CHAINS_FILE_PATH = Path(os.getenv("CHAIN_ADDRESS_PREFIX_FILE_PATH", 'chains/v21/chains.json'))

def update_network_address_prefix(network: Chain, prefix_from_prop: int) -> bool:
    """
    Update the address prefix for a network if needed.

    Args:
        network: Chain object
        prefix_from_prop: Address prefix from the properties

    Returns:
        bool: True if the prefix was updated, False otherwise
    """
    current_prefix = network['addressPrefix']
    if current_prefix != prefix_from_prop:
        if current_prefix is not None and 'legacyAddressPrefix' not in network:
            network['legacyAddressPrefix'] = current_prefix

        network['addressPrefix'] = prefix_from_prop
        print(f"Updated address prefix for chain {network.get('name')}: {current_prefix} -> {prefix_from_prop}")
        return True
    return False

def process_single_chain(chain: Chain, existing_data: list[dict[str, any]]) -> bool:
    """
    Process a single chain to update its address prefix.

    Args:
        chain: Chain object to process
        existing_data: List of existing network configurations

    Returns:
        bool: True if the chain was updated, False otherwise
    """
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

def main() -> None:
    existing_data = load_json_file(CHAINS_FILE_PATH)
    substrate_chains = get_substrate_chains(path=str(CHAINS_FILE_PATH))

    updated = False
    for chain in substrate_chains:
        if process_single_chain(chain, existing_data):
            updated = True

    if updated:
        save_json_file(CHAINS_FILE_PATH, existing_data)
        print("Chain address prefixes updated successfully")
    else:
        print("No changes were made to address prefixes")

if __name__ == "__main__":
    main()

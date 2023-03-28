"""
This script compares the dev and prod transfers.json files, finds the difference and asks which changes to apply, then updates the prod file.
"""

import json
import os

def ask_to_update():
    update = input("Would you like to update that data? (y/n)")
    if update.lower() == 'y':
        return True
    return False

def update_networks(dev_chains, prod_chains, meta_dict):
    for dev_chain_id, dev_chain in dev_chains.items():
        if dev_chain_id not in prod_chains:
            print(f"Added new chain - {meta_dict[dev_chain_id]['name']}")
            if ask_to_update():
                prod_chains[dev_chain_id] = dev_chain

    return prod_chains

def update_network_base_weight(dev_file, prod_file, meta_dict):
    for dev_chain_id, dev_weight in dev_file['networkBaseWeight'].items():
        if dev_chain_id not in prod_file['networkBaseWeight']:
            print(f"Added new base weight in chain: {meta_dict[dev_chain_id]['name']}")
            if ask_to_update():
                prod_file['networkBaseWeight'][dev_chain_id] = dev_weight

    return prod_file['networkBaseWeight']


def update_reserves(dev_file, prod_file):
    for dev_asset_location, dev_asset in dev_file['assetsLocation'].items():
        if dev_asset_location not in prod_file['assetsLocation']:
            print(f"Added new asset: {dev_asset_location}")
            if ask_to_update():
                prod_file['assetsLocation'][dev_asset_location] = dev_asset

    return prod_file['assetsLocation']


def update_assets(dev_chains, prod_chains, meta_dict):
    for prod_chain_id, _ in prod_chains.items():
        for dev_asset_location, dev_asset in dev_chains[prod_chain_id]['assets'].items():
            if dev_asset_location not in prod_chains[prod_chain_id]['assets']:
                print(f"Added new asset {dev_asset_location} in chain: {meta_dict[prod_chain_id]['name']}")
                if ask_to_update():
                    prod_chains[prod_chain_id]['assets'][dev_asset_location] = dev_asset

    return prod_chains


def update_destinations(dev_chains, prod_chains, meta_dict):
    for prod_chain_id, prod_chain in prod_chains.items():
        for prod_asset_location, prod_asset in prod_chain['assets'].items():

            for dev_destination_id, dev_destination \
                in dev_chains[prod_chain_id]['assets'][prod_asset_location]['xcmTransfers'].items():

                if dev_destination_id not in prod_asset['xcmTransfers']:
                    print(f"Added new destination in {meta_dict[prod_chain_id]['name']} \
                          \nfor asset: {prod_asset_location} \
                          \nto network: {meta_dict[dev_destination_id]['name']} ")
                    if ask_to_update():
                        prod_chains[prod_chain_id]['assets'][prod_asset_location]['xcmTransfers'][dev_destination_id] = dev_destination

    return prod_chains


def convert_chains_to_dict(chains_obj):
    chains_dict = {chain['chainId']: chain for chain in chains_obj}
    for chain_id, chain in chains_dict.items():
        assets_dict = {}
        for asset in chain['assets']:
            destinations_dict = {destination['destination']['chainId']: destination for destination in asset['xcmTransfers']}
            assets_dict[asset['assetLocation']] = asset
            assets_dict[asset['assetLocation']]['xcmTransfers'] = destinations_dict
        chains_dict[chain_id]['assets'] = assets_dict

    return chains_dict

def convert_chain_dict_to_array_back(chains_dict):
    temp_chains = []
    for _, chain in chains_dict.items():
        temp_assets = []
        for _, asset in chain['assets'].items():
            temp_destinations = []
            for _, destination in asset['xcmTransfers'].items():
                temp_destinations.append(destination)
            asset['xcmTransfers'] = temp_destinations
            temp_assets.append(asset)
        chain['assets'] = temp_assets
        temp_chains.append(chain)

    return temp_chains



def promote_updates_to_prod(dev_file, prod_file, meta_data):

    # meta_dict is used to get a human-readable network name
    meta_dict = {chain['chainId']: chain for chain in meta_data}

    dev_chains_dict = convert_chains_to_dict(dev_file['chains'])
    prod_chains_data = convert_chains_to_dict(prod_file['chains'])

    updated_prod = update_networks(dev_chains_dict, prod_chains_data, meta_dict)
    updated_prod = update_assets(dev_chains_dict, updated_prod, meta_dict)
    updated_prod = update_destinations(dev_chains_dict, updated_prod, meta_dict)

    updated_chains = convert_chain_dict_to_array_back(updated_prod)

    updated_base_weight = update_network_base_weight(dev_file, prod_file, meta_dict)

    updated_reserves = update_reserves(dev_file, prod_file)

    prod_file['networkBaseWeight'] = updated_base_weight
    prod_file['assetsLocation'] = updated_reserves
    prod_file['chains'] = updated_chains

    return prod_file


if __name__ == "__main__":
    xcm_dev_file_path = os.getenv('DEV_XCM_JSON_PATH')
    xcm_file_path = os.getenv('XCM_JSON_PATH')
    chains_dev_path = os.getenv('DEV_CHAINS_JSON_PATH')
    print(f"The following files are used:\n{xcm_dev_file_path}\n{xcm_file_path}\n{chains_dev_path}")
    # Read data from files
    with open(xcm_dev_file_path) as f:
        data1 = json.load(f)
    with open(xcm_file_path) as f:
        data2 = json.load(f)
    with open(chains_dev_path) as f:
        meta_data = json.load(f)


    updated_obj = promote_updates_to_prod(dev_file=data1, prod_file=data2, meta_data=meta_data)

    with open(xcm_file_path, 'w') as f:
        json.dump(updated_obj, f, indent=2)
        print(f"Data updated in {xcm_file_path}")

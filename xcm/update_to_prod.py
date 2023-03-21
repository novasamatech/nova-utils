import json

def ask_to_update():
    update = input("Would you like to update that data? (y/n)")
    if update.lower() == 'y':
        return True
    return False

def update_networks(dev, prod, meta_dict):
    for key, value in dev.items():
        if key not in prod:
            print(f"Was added new chain - {meta_dict[key]['name']}")
            if ask_to_update():
                prod[key] = value

    return prod

def update_network_base_weight(dev_file, prod_file, meta_dict):
    for chain_id, weight in dev_file['networkBaseWeight'].items():
        if chain_id not in prod_file['networkBaseWeight']:
            print(f"Was added new base weight in chain: {meta_dict[chain_id]['name']}")
            if ask_to_update():
                prod_file['networkBaseWeight'][chain_id] = weight

    return prod_file['networkBaseWeight']


def update_reserves(dev_file, prod_file):
    for asset_location, asset in dev_file['assetsLocation'].items():
        if asset_location not in prod_file['assetsLocation']:
            print(f"Was added new asset: {asset_location}")
            if ask_to_update():
                prod_file['assetsLocation'][asset_location] = asset

    return prod_file['assetsLocation']


def update_assets(dev, prod, meta_dict):
    for chain_id, _ in prod.items():
        for asset_location, asset in dev[chain_id]['assets'].items():
            if asset_location \
                not in prod[chain_id]['assets']:
                print(f"Was added new asset {asset_location} in chain: {meta_dict[chain_id]['name']}")
                if ask_to_update():
                    prod[chain_id]['assets'][asset_location] = asset

    return prod


def update_destinations(dev, prod, meta_dict):
    for chain_id, chain in prod.items():
        for asset_location, asset in chain['assets'].items():
            for destination_id, destination in dev[chain_id]['assets'][asset_location]['xcmTransfers'].items():
                if destination_id not in asset['xcmTransfers']:
                    print(f"Was added new destination in {meta_dict[chain_id]['name']} \
                          \nfor asset: {asset_location} \
                          \nto network: {meta_dict[destination_id]['name']} ")
                    if ask_to_update():
                        prod[chain_id]['assets'][asset_location]['xcmTransfers'][destination_id] = destination

    return prod


def conver_chains_to_dict(chains_obj):
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
    meta_dict = {chain['chainId']: chain for chain in meta_data}

    dev_chains_dict = conver_chains_to_dict(dev_file['chains'])
    prod_chains_data = conver_chains_to_dict(prod_file['chains'])

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
    # Read data from files
    with open('xcm/v2/transfers_dev.json') as f:
        data1 = json.load(f)
    with open('xcm/v2/transfers.json') as f:
        data2 = json.load(f)
    with open('chains/v8/chains_dev.json') as f:
        meta_data = json.load(f)


    updated_obj = promote_updates_to_prod(dev_file=data1, prod_file=data2, meta_data=meta_data)

    with open('xcm/v2/transfers.json', 'w') as f:
        json.dump(updated_obj, f, indent=2)
        print("Data updated in xcm/v2/transfers.json")
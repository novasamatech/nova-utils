#!/usr/bin/python
"""
This script compare transfers.json from endpoint and local file, then print changed fee.
"""
import sys
import os
import json
from collections import defaultdict
import requests


def get_data_from_file(file_path):
    with open(file_path, encoding='UTF-8') as fin:
        return json.load(fin)


def get_request(url) -> json:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as request_error:
        raise SystemExit(request_error)


def deep_search_an_elemnt_by_key(obj, key):
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            item = deep_search_an_elemnt_by_key(v, key)
            if item is not None:
                return item
        if isinstance(v, list):
            for element in v:
                if isinstance(element, dict):
                    tuple_item = deep_search_an_elemnt_by_key(element, key)
                    if tuple_item is not None:
                        return tuple_item


def compare_reserve_fee(object_accumulator, production_assets_location, changed_assets_location):
    for assets, assets_data in production_assets_location.items():
        new_value = deep_search_an_elemnt_by_key(
            changed_assets_location[assets], 'value')
        old_value = deep_search_an_elemnt_by_key(assets_data, 'value')
        if new_value != old_value:
            object_accumulator['reserveFee'][assets] = {
                'old_value': old_value, 'new_value': new_value}


def compare_destinations(object_accumulator, prod_chain_dict, new_chain_dict, chains_json_dict):
    for chain_id, chain_data in prod_chain_dict.items():
        chain_name = chains_json_dict[chain_id].get('name')
        for assets_id, chain_asset in enumerate(chain_data.get('assets')):
            try:
                new_asset = new_chain_dict[chain_id].get('assets')[assets_id]
            except:
                object_accumulator['chains'][chain_name][chain_asset.get(
                    'assetLocation')] = 'That asset was removed'
                continue
            for destination_id, destination_value in enumerate(chain_asset.get('xcmTransfers')):
                destination_name = chains_json_dict[destination_value.get(
                    'destination').get('chainId')].get('name')
                try:
                    new_destination = new_asset.get('xcmTransfers')[
                        destination_id]
                except:
                    object_accumulator['chains'][chain_name][chain_asset.get(
                        'assetLocation')][destination_name] = 'That destination was removed'
                    continue
                new_destination_value = deep_search_an_elemnt_by_key(
                    new_destination, 'value')
                old_destination_value = deep_search_an_elemnt_by_key(
                    destination_value, 'value')
                if new_destination_value != old_destination_value:
                    object_accumulator['chains'][chain_name][chain_asset.get('assetLocation')][destination_name] = {
                        'old_value': old_destination_value, 'new_value': new_destination_value}


def compare_files(prod_json, new_json, chains_json):
    changed_values = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: {})))
    prod_assets_location = prod_json.get('assetsLocation')
    new_assets_location = new_json.get('assetsLocation')

    prod_chain_dict = {
        chain.get('chainId'): chain for chain in prod_json.get('chains')}
    new_chain_dict = {
        chain.get('chainId'): chain for chain in new_json.get('chains')}

    chains_json_dict = {chain.get('chainId'): chain for chain in chains_json}

    compare_reserve_fee(
        changed_values, prod_assets_location, new_assets_location)

    compare_destinations(changed_values, prod_chain_dict,
                         new_chain_dict, chains_json_dict)

    return changed_values


def main(argv):
    nova_utils_url = "https://raw.githubusercontent.com/nova-wallet/nova-utils/master/"

    if 'dev' in argv:
        transfers_file = os.getenv("DEV_XCM_JSON_PATH", "xcm/v2/transfers_dev.json")
        chains_url = nova_utils_url + os.getenv("DEV_CHAINS_JSON_PATH", "chains/v5/chains_dev.json")
    elif 'prod' in argv:
        transfers_file = os.getenv("XCM_JSON_PATH", "xcm/v2/transfers.json")
        chains_url = nova_utils_url + os.getenv("CHAINS_JSON_PATH", "chains/v5/chains.json")
    else:
        raise Exception('Provide a string `dev` or `prod` as parameter for the script')

    transfers_file_url = nova_utils_url + transfers_file
    transfers_from_file = get_data_from_file(transfers_file)
    transfers_from_prod = get_request(transfers_file_url)
    chains_from_prod = get_request(chains_url)
    result = compare_files(transfers_from_prod,
                           transfers_from_file, chains_from_prod)
    if len(result) == 0:
        print('🤖 There is no any significant changes in XCMs')
    else:
        print('🤖 The XCM fee has been changed in this PR: \n```json\n',
              json.dumps(result, indent=2), '\n```')


if __name__ == '__main__':
    main(sys.argv[1:])

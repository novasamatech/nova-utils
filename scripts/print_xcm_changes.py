#!/usr/bin/python
"""
This script compare transfers.json from endpoint and local file, then print changes.
"""
import sys
import os
import json
from collections import defaultdict

from scripts.utils.chain_model import Chain
from utils.work_with_data import get_data_from_file, get_request_via_https


def deep_search_an_elemnt_by_key(obj, key):
    """Search an element in object by key and return it's value

    Args:
        obj (dict | list): Object to search
        key (str): key to search

    Returns:
        obj: Value of first found element
    """

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


def compare_reserve_fee(object_accumulator, actual_assets_location, changed_assets_location):
    """Compare reserve fee between production and changed assets location

    Args:
        object_accumulator (obj): This object accumulate all changes
        actual_assets_location (dict): Dictinary with actual assets location
        changed_assets_location (dict): Dictinary with changed assets location
    """

    for assets, assets_data in actual_assets_location.items():
        try:
            new_value = deep_search_an_elemnt_by_key(
                changed_assets_location[assets], 'value')
            old_value = deep_search_an_elemnt_by_key(assets_data, 'value')
            if new_value != old_value:
                object_accumulator['reserveFee'][assets] = {
                    'old_value': old_value, 'new_value': new_value}
        except:
            object_accumulator['reserveFee'][assets] = "That asset was removed"


def compare_transfer_metadata(destination_in_new_chain_dict, destination, object_accumulator, chain_name, asset_symbol, destination_name):
    """Compare transfer metadata (instructions and type) between destinations

    Args:
        destination_in_new_chain_dict (dict): Destination from new chain dictionary
        destination (dict): Destination from actual chain dictionary
        object_accumulator (dict): Object to accumulate changes
        chain_name (str): Name of the chain
        asset_symbol (str): Symbol of the asset
        destination_name (str): Name of the destination
    """
    new_instructions = destination_in_new_chain_dict.get('fee', {}).get('instructions')
    old_instructions = destination.get('fee', {}).get('instructions')
    if new_instructions != old_instructions:
        if chain_name not in object_accumulator['chains']:
            object_accumulator['chains'][chain_name] = {}
        if asset_symbol not in object_accumulator['chains'][chain_name]:
            object_accumulator['chains'][chain_name][asset_symbol] = {}
        if destination_name not in object_accumulator['chains'][chain_name][asset_symbol]:
            object_accumulator['chains'][chain_name][asset_symbol][destination_name] = {}

        object_accumulator['chains'][chain_name][asset_symbol][destination_name]['instructions'] = {
            'old_value': old_instructions,
            'new_value': new_instructions
        }

    new_type = destination_in_new_chain_dict.get('type')
    old_type = destination.get('type')
    if new_type != old_type:
        if chain_name not in object_accumulator['chains']:
            object_accumulator['chains'][chain_name] = {}
        if asset_symbol not in object_accumulator['chains'][chain_name]:
            object_accumulator['chains'][chain_name][asset_symbol] = {}
        if destination_name not in object_accumulator['chains'][chain_name][asset_symbol]:
            object_accumulator['chains'][chain_name][asset_symbol][destination_name] = {}

        object_accumulator['chains'][chain_name][asset_symbol][destination_name]['type'] = {
            'old_value': old_type,
            'new_value': new_type
        }


def find_new_destinations(object_accumulator, actual_chain_dict, new_cahin_dict, chain_json_dict):
    for chain_id, chain_data in new_cahin_dict.items():
        chain_name = chain_json_dict[chain_id].get('name')
        for chain_asset in chain_data.get('assets'):
            asset_in_actual_chain_dict = {}
            asset_symbol = chain_asset['assetLocation']
            try:
                asset_in_actual_chain_dict = next(
                    asset for asset in actual_chain_dict[chain_id]['assets'] if asset['assetLocation'] == asset_symbol)
            except (StopIteration, KeyError):
                pass
            for destination in chain_asset.get('xcmTransfers'):
                destination_value = destination.get('destination')
                destination_chain_id = destination_value.get('chainId')
                destination_name = chain_json_dict[destination_chain_id].get(
                    'name')
                actual_destinations = asset_in_actual_chain_dict.get(
                    'xcmTransfers')
                try:
                    destination_in_generated_chain_file = next(
                        new_destination for new_destination in actual_destinations if new_destination.get('destination').get('chainId') == destination_chain_id)
                except (StopIteration, KeyError, TypeError):
                    object_accumulator['chains'][chain_name][asset_symbol][destination_name] = 'That destination was added'
                    continue


def compare_destinations(object_accumulator, actual_chain_dict, new_chain_dict, chains_json_dict):
    """Compare destinations between production and changed assets location

    Args:
        object_accumulator (dict): This object accumulate all changes
        actual_chain_dict (dict): Dictinary with production chains
        new_chain_dict (dict): Dictinary with changed chains
        chains_json_dict (dict): Dictinary with chains.json
    """

    find_new_destinations(object_accumulator, actual_chain_dict, new_chain_dict, chains_json_dict)

    for chain_id, chain_data in actual_chain_dict.items():
        chain_name = chains_json_dict[chain_id].get('name')
        for chain_asset in chain_data.get('assets'):
            asset_symbol = chain_asset['assetLocation']
            try:
                asset_in_new_chain_dict = next(
                    asset for asset in new_chain_dict[chain_id]['assets'] if asset['assetLocation'] == asset_symbol)
            except (StopIteration, KeyError):
                object_accumulator['chains'][chain_name][asset_symbol] = 'That asset was removed'
                continue
            for destination in chain_asset.get('xcmTransfers'):
                destination_value = destination.get('destination')
                destination_chain_id = destination_value.get('chainId')
                destination_name = chains_json_dict[destination_chain_id].get('name')
                new_destinations = asset_in_new_chain_dict.get('xcmTransfers')
                try:
                    destination_in_new_chain_dict = next(
                        destination for destination in new_destinations if destination.get('destination').get('chainId') == destination_chain_id)
                except StopIteration:
                    object_accumulator['chains'][chain_name][asset_symbol][destination_name] = 'That destination was removed'
                    continue
                new_destination_value = deep_search_an_elemnt_by_key(
                    destination_in_new_chain_dict, 'value')
                old_destination_value = deep_search_an_elemnt_by_key(
                    destination_value, 'value')
                if new_destination_value != old_destination_value:
                    object_accumulator['chains'][chain_name][asset_symbol][destination_name] = {
                        'old_value': old_destination_value, 'new_value': new_destination_value}

                compare_transfer_metadata(
                    destination_in_new_chain_dict,
                    destination,
                    object_accumulator,
                    chain_name,
                    asset_symbol,
                    destination_name
                )


def compare_files(actual_json, new_json, chains_json):
    """
    This function compare two json files and return dictinary with changes.
    Currently it compare reserve fee and destinations

    Args:
        actual_json (_type_): This is actual XCM json from master branch
        new_json (_type_): This is changed XCM json
        chains_json (_type_): This file contains all addition info for chains, from chains/${version}/chains.json

    Returns:
        changed_values (json): This json contains all changes.
        Example:
        {
            "reserveFee": {"DOT": {"old_value": 0.1, "new_value": 0.2}},
            "chains": {"Kusama": {"KSM": {"Karura": {"old_value": 0.1, "new_value": 0.2}}}}
        }
    """

    changed_values = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: {})))
    actual_assets_location = actual_json.get('assetsLocation')
    new_assets_location = new_json.get('assetsLocation')

    prod_chain_dict = {
        chain.get('chainId'): chain for chain in actual_json.get('chains')}
    new_chain_dict = {
        chain.get('chainId'): chain for chain in new_json.get('chains')}

    chains_json_dict = {chain.get('chainId'): chain for chain in chains_json}

    compare_reserve_fee(
        changed_values, actual_assets_location, new_assets_location)

    compare_destinations(changed_values, prod_chain_dict,
                         new_chain_dict, chains_json_dict)

    compare_network_delivery_fee(
        changed_values,
        actual_json.get('networkDeliveryFee', {}),
        new_json.get('networkDeliveryFee', {}),
        chains_json_dict
    )

    return changed_values


def compare_network_delivery_fee(object_accumulator, actual_network_delivery_fee, new_network_delivery_fee, chains_json_dict):
    """Compare network delivery fee between production and changed json

    Args:
        object_accumulator (dict): This object accumulate all changes
        actual_network_delivery_fee (dict): Dictionary with actual network delivery fee
        new_network_delivery_fee (dict): Dictionary with changed network delivery fee
        chains_json_dict (dict): Dictionary with chains.json
    """
    for chain_id, fee_data in new_network_delivery_fee.items():
        chain_name = chains_json_dict[chain_id].get('name', chain_id)
        if chain_id not in actual_network_delivery_fee:
            object_accumulator['networkDeliveryFee'][chain_name] = 'Added'
        else:
            if fee_data != actual_network_delivery_fee[chain_id]:
                object_accumulator['networkDeliveryFee'][chain_name] = {
                    'old_value': actual_network_delivery_fee[chain_id],
                    'new_value': fee_data
                }

    for chain_id in actual_network_delivery_fee:
        chain_name = chains_json_dict[chain_id].get('name', chain_id)
        if chain_id not in new_network_delivery_fee:
            object_accumulator['networkDeliveryFee'][chain_name] = 'Removed'


def main(argv):
    """It will compare transfers.json from endpoint and local file, then print changes. Depends on parametrs it will print changes for dev or prod environment. Also it prepared as to run locally with default parameters, as to run in CI/CD pipeline with parameters from environment variables.

    Args:
        argv (array): Array of script arguments

    Raises:
        Exception: If script arguments are not valid
    """

    nova_utils_url = "https://raw.githubusercontent.com/novasamatech/nova-utils/master/"
    github_base = os.getenv('GITHUB_BASE')
    if github_base:
        nova_utils_url = f"https://raw.githubusercontent.com/novasamatech/nova-utils/{github_base}/"

    transfers_file = os.getenv("XCM_PATH", "xcm/v4/transfers_dev.json")
    chains_version = Chain.latest_config_version()
    chains_url = nova_utils_url + os.getenv("CHAINS_PATH", f"chains/{chains_version}/chains_dev.json")

    transfers_file_url = nova_utils_url + transfers_file
    transfers_from_file = get_data_from_file(transfers_file)
    transfers_json_from_master = get_request_via_https(transfers_file_url)
    chains_json_from_master = get_request_via_https(chains_url)
    result = compare_files(transfers_json_from_master,
                           transfers_from_file, chains_json_from_master)
    if len(result) == 0:
        print('🤖 There is no any significant changes in XCMs')
    else:
        print('🤖 The XCM fee has been changed in this PR: \n```json\n',
              json.dumps(result, indent=2), '\n```')


if __name__ == '__main__':
    main(sys.argv[1:])

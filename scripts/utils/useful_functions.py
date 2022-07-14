import json

from substrateinterface import SubstrateInterface
from utils.data_model.chain_json_model import Chain, ChainAsset


def parse_json_file(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        raise


def find_element_in_array_by_condition(array, key, value):
    return next(filter(lambda x: x.get(key) == value,  array), None)


def write_new_file(json_file, path):
    with open(path, "w") as f:
        f.write(json_file)


def find_asset_in_chain(chain: Chain, asset_name) -> ChainAsset:
    processed_name = asset_name.split('-', 1)[0]
    for asset in chain.assets:
        if (processed_name in asset.symbol):
            return asset


def find_chain(chains_json, chain_name) -> Chain:
    for chain_json in chains_json:
        searched_chain = Chain(**chain_json)
        if (searched_chain.name == chain_name):
            return searched_chain
    return None


def create_connection_by_url(url):
    try:
        substrate = SubstrateInterface(url=url, use_remote_preset=True)
    except:
        print("⚠️ Can't connect by %s, check it is available?" % (url))
        return None

    return substrate


def deep_search_in_object(obj, key, value):
    if key in obj:
        if (obj[key] == value):
            return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            item = deep_search_in_object(v, key, value)
            if item is not None:
                return item
        if isinstance(v, tuple):
            for element in v:
                if isinstance(element, dict):
                    tuple_item = deep_search_in_object(element, key, value)
                    if tuple_item is not None:
                        return tuple_item


def find_assetsLocation(base_parameters, xcm_object):
    for asset in xcm_object.assetsLocation:
        processed_name = asset.split('-', 1)[0]
        if (processed_name == base_parameters.asset):
            return xcm_object.assetsLocation[asset]

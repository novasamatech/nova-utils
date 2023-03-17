import requests
import json
import os

from collections import defaultdict
from typing import Dict, Tuple

from utils.work_with_data import write_data_to_file

CHAINS_VERISON = os.getenv('CHAINS_VERSION', default = "v8")

with open(f"chains/{CHAINS_VERISON}/chains_dev.json") as fin:
    dev_chains = json.load(fin)

with open("assets/evm/v2/assets_dev.json") as fin:
    evm_assets = json.load(fin)


def request_data_from_metamask():
    response = requests.get("https://raw.githubusercontent.com/MetaMask/slip44/main/slip44.json")
    data = response.json()
    return data

def create_slip44_array(first_dict, second_dict):
    slip44_array = []
    for _, value in second_dict.items():
        if value['symbol'] in first_dict:
            slip44_array.append({ "index": value["index"], "symbol": value["symbol"] })
    return slip44_array

def collect_all_assets_in_nova(chains_file, assets_file) -> Tuple[Dict[str, list], Dict[str, list]]:
    chain_assets = defaultdict(list)
    for chain in chains_file:
        for asset in chain['assets']:
            chain_assets[asset['symbol']].append(chain['chainId'])

    evm_assets = defaultdict(list)
    for evm_asset in assets_file:
        for evm_instance in evm_asset['instances']:
            evm_assets[evm_asset['symbol']].append(evm_instance['chainId'])

    print(f"In {CHAINS_VERISON} chains.json file was found - {len(chain_assets)} assets")
    print(f"In evm assets.json file was found - {len(evm_assets)} assets")

    return chain_assets, evm_assets


def create_slip44_token_list(chains_file, assets_file):
    chain_assets, evm_assets = collect_all_assets_in_nova(chains_file, assets_file)
    metamask_data = request_data_from_metamask()
    merged_dict = {**chain_assets, **evm_assets}
    slip44_array = create_slip44_array(merged_dict, metamask_data)
    print(f"Slip44 array has {len(slip44_array)} elements")

    return slip44_array


if __name__ == '__main__':
    slip44_array = create_slip44_token_list(chains_file=dev_chains, assets_file=evm_assets)
    write_data_to_file('assets/slip44.json', json.dumps(slip44_array, indent=4))

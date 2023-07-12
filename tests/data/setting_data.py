import os

from typing import List
from scripts.utils.work_with_data import get_network_list
from scripts.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v10/chains.json")
skipped_networks = ['Edgeware', 'Efinity']
# Efinity issue: https://app.clickup.com/t/24368000/85ztevf2j
network_list = get_network_list('/' + network_file_path)


def get_substrate_chains():
    substrate_chains = []
    for data in network_list:
        if data.get('name') in skipped_networks:
            continue
        options = data.get('options')

        if options is None:
            substrate_chains.append(Chain(data))
        elif 'noSubstrateRuntime' not in options:
            substrate_chains.append(Chain(data))
        else:
            continue

    return substrate_chains


def get_ethereum_chains():
    eth_chains = []
    for data in network_list:
        options = data.get('options')
        if options is not None and 'ethereumBased' in options:
            eth_chains.append(Chain(data))

    return eth_chains


def collect_nodes_for_chains(networks: List[Chain]):
    result = []
    for network in networks:
        for node in network.nodes:
            result.append(
                {"url": node.get("url"), "name": network.name})

    return result


def collect_rpc_nodes_for_chains(networks: List[Chain]):
    result = []
    for network in networks:
        for node in network.nodes:
            if 'https' in node.get("url"):
                result.append(
                    {"url": node.get("url"), "name": network.name}
                )

    return result

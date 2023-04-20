import os

from typing import List
from scripts.utils.work_with_data import get_network_list
from scripts.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v10/chains.json")
skipped_networks = ['Edgeware', 'Ethereum']
network_list = get_network_list('/' + network_file_path)

chains = [Chain(data) for data in network_list if data.get(
    'name') not in skipped_networks]


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

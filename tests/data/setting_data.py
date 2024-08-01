import os

from typing import List
from scripts.utils.work_with_data import get_network_list
from scripts.utils.chain_model import Chain

network_file_path = os.getenv('CHAINS_JSON_PATH', "chains/v20/chains.json")
skipped_networks = ['Edgeware']


def get_substrate_chains(path: str = network_file_path) -> list[Chain]:
    substrate_chains = []
    network_list = get_network_list('/' + path)
    for data in network_list:
        if data.get('name') in skipped_networks or 'PAUSED' in data.get('name'):
            continue
        options = data.get('options')

        if options is None:
            substrate_chains.append(Chain(data))
        elif 'noSubstrateRuntime' not in options:
            substrate_chains.append(Chain(data))
        else:
            continue

    return substrate_chains


def get_ethereum_chain(path: str = network_file_path):
    eth_chains = []
    network_list = get_network_list('/' + path)
    for data in network_list:
        if data.get('chainId') == 'eip155:1':
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
